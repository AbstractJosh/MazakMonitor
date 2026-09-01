import asyncio
import contextlib
import time

import pytest

import app.adapters.csv_replay as csv_replay
from app.adapters.csv_replay import _run_in_thread, run_csv_ingest
from app.config import settings
from app.hub import LiveHub
from app.sim.csv_reader import FeatureValue, LimitValue, MeasurementRecord
from datetime import datetime


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


def _rec() -> MeasurementRecord:
    return MeasurementRecord(
        unit_no=10660,
        source_time=datetime(2026, 8, 10, 11, 23, 2),
        channel_nr=1,
        tool_nr=11,
        program_nr=0,
        cut_nr=0,
        workpiece=None,
        alarm=None,
        alarm_limit=None,
        source_file="x.csv",
        features=[FeatureValue(slot=1, name="SPINDEL", value=115.0, work_value=None)],
        limits=[LimitValue(limit_nr=1, level=230.0, lim_type=2, feature_nr=1)],
    )


def test_hub_olcumu_uygular_ve_frames_artirir():
    hub = LiveHub(source_name="csv")
    hub.apply_measurement(_rec(), "2026-08-10T11:23:02")
    assert hub.frames == 1
    assert [f.name for f in hub.state.features] == ["SPINDEL"]
    # Tel istatistigi URETILMEZ: CSV'nin teli yoktur.
    assert hub.wire is None


@pytest.mark.anyio
async def test_ingest_hubi_besler_ve_baglantiyi_bildirir(db_bos):
    """Adaptor gercek veri/ klasorunu okur (conftest SIM_CSV_DIR'i sabitler)."""
    hub = LiveHub(source_name="csv")
    task = asyncio.create_task(
        run_csv_ingest(
            hub,
            csv_dir=settings.csv_dir(),
            period_ms=0,
            retention_min=60,
        )
    )
    # Birkac anin islenmesine izin ver, sonra iptal et.
    for _ in range(200):
        if hub.frames > 0 and hub.upstream_connected:
            break
        await asyncio.sleep(0.01)
    # `task.cancel()` normalde CancelledError'a yol acar, ama gorev bu ani
    # tam gecerken KENDI basina bitmis de olabilir (orn. bu makinedeki AV/DLP
    # taramasi bir dosya acmayi anlik engelleyip "locked" DISI bir
    # OperationalError firlatirsa run_csv_ingest kalici hata sayip doner --
    # bkz. adaptorun kendi except OperationalError dali). O durumda cancel()
    # zaten bitmis gorevde etkisizdir ve await task CancelledError FIRLATMAZ.
    # Testin amaci iptal SOZLESMESI degil, hub'in beslenmesidir; bu yuzden
    # her iki sonucu da kabul ediyoruz (nadir bir ortam kaynakli yaristan
    # kacinilamayan bir kirilganlik uretmemek icin).
    #
    # Yine de gorevin SESSIZCE erken donmedigini (orn. bir kayit
    # islenemedigi icin) dogruluyoruz: normal yolda gorev hala kosuyor
    # olmali, cancel() burada GERCEK bir iptal olmali.
    assert not task.done()
    task.cancel()
    with contextlib.suppress(asyncio.CancelledError):
        await task

    assert hub.frames > 0
    assert hub.upstream_connected is True
    assert hub.state.features, "ozellik uretilmedi"


@pytest.mark.anyio
async def test_csv_koku_yoksa_baglanti_dusuk_bildirilir(tmp_path):
    """Eksik klasor sessizce bos donmez: durum "bagli degil" olur."""
    hub = LiveHub(source_name="csv")
    await run_csv_ingest(hub, csv_dir=tmp_path, period_ms=0, retention_min=60)
    assert hub.upstream_connected is False
    assert hub.frames == 0


@pytest.mark.anyio
async def test_run_in_thread_iptalde_gercek_bitisi_bekler():
    """`_run_in_thread`in GUVENCESI: iptal is parcacigini durdurmaz (Python
    is parcaciklari zorla kesilemez), yalniz BEKLEMEYI keser. Bu fonksiyon
    GERCEK bitisi bekleyip SONRA iptali yeniden yukseltmeli.

    `_run_in_thread` yerine duz `asyncio.to_thread` kullanilsaydi bu test
    FAIL ederdi: is parcacigi hala 0.2sn'lik `time.sleep`teyken cancel()
    CancelledError'i HEMEN dondururdu ve `calisti["bitti"]` henuz False
    olurdu (bu iddia elle denenip dogrulandi - rapora bakiniz).
    """
    calisti = {"bitti": False}

    def is_parcacigi() -> None:
        time.sleep(0.2)
        calisti["bitti"] = True

    async def calistir() -> None:
        await _run_in_thread(is_parcacigi)

    task = asyncio.create_task(calistir())
    await asyncio.sleep(0.02)  # is parcaciginin gercekten baslamis olmasi icin
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task

    assert calisti["bitti"] is True


@pytest.mark.anyio
async def test_beklenmeyen_hata_baglantiyi_dusuk_bildirir_ve_gorevi_oldurmez(db_bos, monkeypatch):
    """OperationalError DISI bir ariza hub'i SESSIZCE "bagli" birakmamali.

    `_prune_with_retry`'i RuntimeError firlatacak sekilde degistiriyoruz: tam
    bir tur (gercek veri/ 131 ani) once basariyla islenip hub baglanir,
    SONRA budama patlar. Adaptor OperationalError'daki gibi olmemeli
    (task.done() olmamali), yalniz durumu dusuk bildirip yeniden denemeli --
    promos3_udp.py'nin deseniyle ayni.
    """

    def _patlayan_budama(*args: object, **kwargs: object) -> int:
        raise RuntimeError("kaboom - OperationalError DEGIL")

    monkeypatch.setattr(csv_replay, "_prune_with_retry", _patlayan_budama)

    hub = LiveHub(source_name="csv")
    task = asyncio.create_task(
        run_csv_ingest(hub, csv_dir=settings.csv_dir(), period_ms=0, retention_min=60)
    )
    # Once baglanmasini (frames>0, upstream_connected=True), SONRA budama
    # patladiginda durumun dusuk bildirilmesini bekle.
    for _ in range(300):
        if hub.frames > 0 and hub.upstream_connected is False:
            break
        await asyncio.sleep(0.01)

    # Gorev OperationalError yolundaki gibi OLMEMELI: hala kosuyor, yeniden
    # deniyor olmali.
    assert not task.done()
    task.cancel()
    with contextlib.suppress(asyncio.CancelledError):
        await task

    assert hub.frames > 0, "ariza ONCESI islenen kayitlar olmali"
    assert hub.upstream_connected is False, "ariza sonrasi durum dusuk bildirilmeli"
