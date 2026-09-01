"""CSV tekrar-oynatma ingest adaptoru — SUREC ICI.

run_promos3_ingest ile ayni sozlesme: sonsuz async gorev, iptal edilebilir,
kendi durumunu hub'a bildirir.

NEDEN SUREC ICI: bu adaptor hub'i besler, yani ekranin gordugu canli durumu
uretir. Ayri bir surec (eski `python -m app.sim.replay`) bunu ancak IPC ile
yapabilirdi. CLI hala durur ve DB'ye yazmayi surdurur; bu adaptor ayni
yardimcilari cagirir, kopyalamaz.

DB YAZMASI SURUYOR: /api/measurements ve test_replay.py bozulmaz.

IPTAL VE IS PARCACIGI (bkz. `_run_in_thread`): `asyncio.to_thread` iptal
edildiginde arka plandaki GERCEK is parcacigini DURDURMAZ (Python is
parcaciklari zorla kesilemez) — yalniz BEKLEMEYI birakir ve CancelledError'i
hemen yukseltir. Session'a dokunan cagrilar duz `to_thread` ile beklenirse,
lifespan (ya da bir test) gorevi TAM O ANDA iptal ettiginde `with
SessionLocal()` blogu event dongusu is parcacigindan `session.close()`
cagirirken arka plandaki is parcacigi HALA ayni (thread-safe OLMAYAN)
session'i kullaniyor olabilir — IllegalStateChangeError ya da sessiz veri
bozulmasi. Bu yuzden session'a dokunan her cagri `_run_in_thread`den gecer.
"""

import asyncio
import logging
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import TypeVar

from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from app.db import SessionLocal
from app.hub import LiveHub
from app.sim.baselines import compute_baselines
from app.sim.csv_reader import MeasurementRecord, Moment, read_measurement, read_moments
from app.sim.replay import _prune_with_retry, _to_row, _with_lock_retry

log = logging.getLogger("app.adapters.csv_replay")

SOURCE = "csv"

# OperationalError DISI beklenmeyen bir arizadan sonraki bekleme.
# promos3_udp.py'nin yeniden baglanma araligiyla (3.0s) ayni mantik: TIGHT
# SPIN olmadan yeniden dene, log'u da her turda spamlamasin.
UNEXPECTED_ERROR_BACKOFF_S = 3.0

_T = TypeVar("_T")


async def _run_in_thread(func, *args) -> _T:
    """`asyncio.to_thread` sarar; IPTAL GERCEK BITISI BEKLER.

    `asyncio.shield` sayesinde disaridan gelen iptal yalniz BU BEKLEMEYI
    keser, sardigi is parcacigini iptal etmez (zaten edemez). CancelledError
    yukselince is parcacigi hala kosuyor olabilir; `asyncio.wait` ile
    GERCEKTEN bitmesi beklenir, ancak SONRA iptal yeniden yukseltilir. Boylece
    cagiran (`with SessionLocal()`) session'i kapattiginda is parcacigi ona
    kesin dokunmuyor olur.
    """
    task = asyncio.ensure_future(asyncio.to_thread(func, *args))
    try:
        return await asyncio.shield(task)
    except asyncio.CancelledError:
        await asyncio.wait([task])
        raise


def _read_and_write(session: Session, moment: Moment, now: datetime) -> list[MeasurementRecord]:
    """Bir anin kayitlarini okur, DB'ye yazar ve KAYITLARI doner.

    write_moment yalnizca SAYI donuyordu; hub'i beslemek icin kayitlarin
    kendisi gerekiyor. Okuma+yazma tek yerde kaliyor ki dosya iki kez
    okunmasin.
    """
    records: list[MeasurementRecord] = []
    for unit_no, path in moment.files:
        record = read_measurement(path, unit_no)
        if record is None:
            continue  # bozuk dosya TUM ani dusurmez
        session.add(_to_row(record, now))
        records.append(record)
    session.commit()
    return records


async def run_csv_ingest(
    hub: LiveHub, csv_dir: Path, period_ms: int, retention_min: int
) -> None:
    """CSV'leri DONGUSEL okur: DB'ye yazar ve hub'i besler."""
    try:
        moments = await asyncio.to_thread(read_moments, csv_dir)
    except FileNotFoundError as exc:
        # Sessizce bos donmek "calisiyor ama hicbir sey yazmiyor" demekti.
        log.error("CSV kaynagi okunamadi: %s", exc)
        hub.set_source_status(SOURCE, False)
        return

    # Taban ortalamalari BIR KEZ, dongu baslamadan once: 262 kucuk dosya
    # (~0,5 sn) ve sonuc surec boyunca degismez. An basina hesaplamak ayni
    # sayiyi 131 kez yeniden uretirdi.
    baselines = await asyncio.to_thread(compute_baselines, moments)
    hub.set_baselines(baselines)

    log.info("CSV SIM  -  uretilen her satir CSV'DEN gelir, canli olcum DEGILDIR")
    log.info("  kaynak: %s   an sayisi: %d", csv_dir, len(moments))
    log.info("  taban ortalamasi cikarilan ozellik: %d", len(baselines))

    with SessionLocal() as session:
        while True:
            try:
                for moment in moments:
                    now = datetime.now(UTC).replace(tzinfo=None)
                    records = await _run_in_thread(
                        _with_lock_retry,
                        session,
                        moment.name,
                        lambda: _read_and_write(session, moment, now),
                    )
                    # Hub yazmalari OLAY DONGUSUNDE kalir: hub kilitsizdir
                    # ve tek dongu varsayar (bkz. hub.py basligi).
                    for rec in records or []:
                        hub.apply_measurement(rec, now.isoformat())
                    if records:
                        hub.set_source_status(SOURCE, True)
                    if period_ms > 0:
                        await asyncio.sleep(period_ms / 1000)

                await _run_in_thread(
                    _prune_with_retry,
                    session,
                    datetime.now(UTC).replace(tzinfo=None)
                    - timedelta(minutes=retention_min),
                )
            except asyncio.CancelledError:
                # promos3_udp.py ile ayni desen: iptal asagidaki genis
                # except'e ASLA dusmesin diye acikca once burada yakalanip
                # yeniden firlatilir (CancelledError zaten 3.8+'ta
                # Exception'dan turemez, ama niyet boylece acik kalir).
                raise
            except OperationalError as exc:
                # Kalici bir DB arizasi sessizce sifir-satir turlara
                # donusmez; acikca durur ve durumu dusuk bildirir.
                log.error("Kalici veritabani hatasi, CSV ingest duruyor: %s", exc)
                hub.set_source_status(SOURCE, False)
                return
            except Exception:
                # OperationalError DISI bir ariza (orn. IntegrityError) gorevi
                # SESSIZCE oldurup hub'i "bagli" birakmamali: /api/machines
                # o zaman olu bir kaynagi "connected: true" gosterirdi
                # (welcome ekraninin varolma nedeni tam da bunu onlemek).
                # promos3_udp.py'nin deseni: durumu dusuk bildir, logla,
                # TIGHT SPIN olmadan yeniden dene. Session basarisiz bir
                # flush/commit sonrasi "failed transaction" durumunda
                # kalabilir; rollback de is parcacigindan gecmeli (session
                # thread-safe DEGILDIR, bkz. modul basligi).
                log.exception("CSV ingest dongusunde beklenmeyen hata")
                await _run_in_thread(session.rollback)
                hub.set_source_status(SOURCE, False)
                await asyncio.sleep(UNEXPECTED_ERROR_BACKOFF_S)
                continue

            # Tur sonu tabani: `period_ms=0` verildiginde serbest kosmasin.
            await asyncio.sleep(0.2)
