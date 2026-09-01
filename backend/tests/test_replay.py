"""Tekrar oynatma testleri. conftest DATABASE_URL'i gecici dosyaya sabitler."""

from datetime import datetime, timedelta

import pytest
from sqlalchemy import func, select
from sqlalchemy.exc import OperationalError

from app.config import settings
from app.db import SessionLocal
from app.models import Measurement, MeasurementFeature, MeasurementLimit
from app.sim import replay
from app.sim.csv_reader import read_moments
from app.sim.replay import prune, run, write_moment


def _sayilar(s) -> tuple[int, int, int]:
    return (
        s.scalar(select(func.count()).select_from(Measurement)),
        s.scalar(select(func.count()).select_from(MeasurementFeature)),
        s.scalar(select(func.count()).select_from(MeasurementLimit)),
    )


def test_bir_an_18_satir_yazar(db_bos):
    """2 olcum + 8 ozellik + 8 limit = 18."""
    anlar = read_moments(settings.csv_dir())
    with SessionLocal() as s:
        assert write_moment(s, anlar[0], datetime(2026, 8, 11, 9, 0, 0)) == 2
        assert _sayilar(s) == (2, 8, 8)


def test_yazilan_satir_alanlari(db_bos):
    anlar = read_moments(settings.csv_dir())
    simdi = datetime(2026, 8, 11, 9, 0, 0)
    with SessionLocal() as s:
        write_moment(s, anlar[0], simdi)
        m = s.scalars(select(Measurement).where(Measurement.unit_no == 10665)).one()
        # recorded_at SIMDI, source_time CSV'nin kendi zamani.
        # NOT: brief'teki deger (192000) 10660'in ayni anina aitti (bkz.
        # test_csv_reader.py); 10665'in GERCEK dosyasinda Start date .230'dur.
        assert m.recorded_at == simdi
        assert m.source_time == datetime(2026, 8, 10, 11, 23, 2, 230000)
        assert m.tool_nr == 11
        assert m.source_file == "000_01_00011_000_260810_112302.csv"
        assert [f.name for f in m.features] == [
            "VIBRATION",
            "M131 DEBI",
            "M131BASINC",
            "M08 DEBI",
        ]
        assert m.features[0].value is None
        assert [lv.limit_nr for lv in m.limits] == [1, 2, 3, 4]


def test_ayni_an_iki_kez_yazilabilir(db_bos):
    """Dongu basa donunce cakisma OLMAMALI: recorded_at farklidir."""
    anlar = read_moments(settings.csv_dir())
    with SessionLocal() as s:
        write_moment(s, anlar[0], datetime(2026, 8, 11, 9, 0, 0))
        write_moment(s, anlar[0], datetime(2026, 8, 11, 9, 0, 1))
        assert _sayilar(s) == (4, 16, 16)


def test_budama_cocuklari_da_siler(db_bos):
    """FK cascade SQLite'ta YALNIZ foreign_keys=ON ile calisir (db.py pragma).

    Pragma unutulursa bu test cocuk satirlarini yetim bulur ve DUSER — sessiz
    sizintiya karsi tek korumamiz budur.
    """
    anlar = read_moments(settings.csv_dir())
    eski = datetime(2026, 8, 11, 9, 0, 0)
    yeni = eski + timedelta(minutes=90)
    with SessionLocal() as s:
        write_moment(s, anlar[0], eski)
        write_moment(s, anlar[1], yeni)
        assert _sayilar(s) == (4, 16, 16)
        assert prune(s, older_than=eski + timedelta(minutes=60)) == 2
        assert _sayilar(s) == (2, 8, 8)


def test_tek_gecis_tum_anlari_yazar(db_bos):
    """--once: 131 an x 2 unite = 262 olcum, 1048 cocuk satir."""
    assert run(settings.csv_dir(), period_ms=0, retention_min=60, once=True) == 0
    with SessionLocal() as s:
        assert _sayilar(s) == (262, 262 * 4, 262 * 4)


def test_tablo_yoksa_acik_hata_kodu(db_bos):
    """Tablolar dusuruldugunde sim patlamaz, ne yapilacagini soyler."""
    from app.db import engine
    from app.models import Base

    Base.metadata.drop_all(engine)
    assert run(settings.csv_dir(), period_ms=0, retention_min=60, once=True) == 2


def test_bos_unite_klasorlerinde_dongu_hic_baslamaz(db_bos, tmp_path):
    """`--csv-dir <bos-uniteler>` sonsuz doner degil, acikca duser.

    An listesi bosken run()'in TEK bekleme noktasi (an-basi uyku, ic dongude)
    hic calismiyordu ve `while True` tur basina bir DELETE+COMMIT ile serbest
    kosuyordu - --period-ms ne verilirse verilsin. read_moments artik bu hali
    de FileNotFoundError ile kapatiyor, yani dongu HIC baslamiyor.
    """
    (tmp_path / "10660").mkdir()
    (tmp_path / "10665").mkdir()
    with pytest.raises(FileNotFoundError):
        run(tmp_path, period_ms=1000, retention_min=60, once=False)


def _kilitli_hata() -> OperationalError:
    return OperationalError("stmt", {}, Exception("database is locked"))


def _kilit_disi_hata() -> OperationalError:
    return OperationalError("stmt", {}, Exception("no such column: xyz"))


def test_yeniden_deneme_gecici_kilitten_sonra_basarili(db_bos, monkeypatch):
    """Ilk deneme "locked" ile patlar, ikincisi write_moment'i gercekten cagirir."""
    gercek_write_moment = write_moment
    cagri_sayaci = {"n": 0}

    def sahte(session, moment, now):
        cagri_sayaci["n"] += 1
        if cagri_sayaci["n"] == 1:
            raise _kilitli_hata()
        return gercek_write_moment(session, moment, now)

    monkeypatch.setattr(replay, "write_moment", sahte)
    monkeypatch.setattr(replay.time, "sleep", lambda saniye: None)
    anlar = read_moments(settings.csv_dir())
    with SessionLocal() as s:
        assert replay._write_with_retry(s, anlar[0], datetime(2026, 8, 11, 9, 0, 0)) == 2
    assert cagri_sayaci["n"] == 2


def test_yeniden_deneme_kilit_hic_acilmazsa_sifir_doner(db_bos, monkeypatch):
    """Butun LOCK_RETRIES deneme de "locked" ile biterse sessizce 0 doner (patlamaz)."""

    def hep_kilitli(session, moment, now):
        raise _kilitli_hata()

    monkeypatch.setattr(replay, "write_moment", hep_kilitli)
    monkeypatch.setattr(replay.time, "sleep", lambda saniye: None)
    anlar = read_moments(settings.csv_dir())
    with SessionLocal() as s:
        assert replay._write_with_retry(s, anlar[0], datetime(2026, 8, 11, 9, 0, 0)) == 0


def test_kilit_disi_operational_error_yeniden_firlatilir(db_bos, monkeypatch):
    """"locked" olmayan bir OperationalError yutulmaz, oldugu gibi firlatilir.

    Kalici bir DB arizasi (tablo/kolon uyusmazligi, disk I/O, izin hatasi)
    sessizce loglanip 0 donen bir tura donusmemeli.
    """

    def bozuk(session, moment, now):
        raise _kilit_disi_hata()

    monkeypatch.setattr(replay, "write_moment", bozuk)
    anlar = read_moments(settings.csv_dir())
    with SessionLocal() as s:
        with pytest.raises(OperationalError):
            replay._write_with_retry(s, anlar[0], datetime(2026, 8, 11, 9, 0, 0))


def test_budama_kilitliyken_yeniden_denenir(db_bos, monkeypatch):
    """Budama da yazma ile ayni geri-cekilme yolundan gecer.

    Spec 11'in "locked -> geri cekil ve 3 kez dene" satiri budamayi AYIRMAZ;
    ustelik budama turun en buyuk yazma islemidir. Eskiden prune() yeniden
    deneme yolunun DISINDAYDI ve tek bir "locked" sureci olduruyordu.
    """
    cagri_sayaci = {"n": 0}
    gercek_prune = prune

    def sahte(session, older_than):
        cagri_sayaci["n"] += 1
        if cagri_sayaci["n"] == 1:
            raise _kilitli_hata()
        return gercek_prune(session, older_than)

    monkeypatch.setattr(replay, "prune", sahte)
    monkeypatch.setattr(replay.time, "sleep", lambda saniye: None)
    anlar = read_moments(settings.csv_dir())
    with SessionLocal() as s:
        write_moment(s, anlar[0], datetime(2026, 8, 11, 9, 0, 0))
        assert replay._prune_with_retry(s, older_than=datetime(2026, 8, 11, 10, 0, 0)) == 2
    assert cagri_sayaci["n"] == 2


def test_budama_kalici_hatasi_run_i_belirgin_kodla_durdurur(db_bos, monkeypatch):
    """Budamadaki "locked" DISI bir hata da run()'i acik bir kodla durdurur.

    Eskiden prune cagrisi try/except blogunun disindaydi: ayni hata
    yakalanmamis bir traceback'le pencereye dusuyordu.
    """

    def bozuk(session, older_than):
        raise _kilit_disi_hata()

    monkeypatch.setattr(replay, "prune", bozuk)
    assert run(settings.csv_dir(), period_ms=0, retention_min=60, once=True) == 3


def test_kalici_db_hatasi_run_i_belirgin_kodla_durdurur(db_bos, monkeypatch):
    """run(), locked-disi bir OperationalError'i yutup sifir satir turu loglamaz;
    belirgin bir cikis koduyla (3) durur."""

    def bozuk(session, moment, now):
        raise _kilit_disi_hata()

    monkeypatch.setattr(replay, "write_moment", bozuk)
    assert run(settings.csv_dir(), period_ms=0, retention_min=60, once=True) == 3
