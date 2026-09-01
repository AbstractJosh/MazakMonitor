"""CSV ayristirici testleri — GERCEK veri/ dosyalarina karsi kosar.

Uydurma fixture yerine gercek veriyi kullanmak bilincli bir tercihtir:
biçimi bu 262 dosya tanimlar, bizim varsayimimiz degil.
"""

import pytest

from app.config import settings
from app.sim.csv_reader import Moment, read_measurement, read_moments

VERI = settings.csv_dir()


def test_gercek_dosya_tum_alanlari():
    p = VERI / "10660" / "000_01_00011_000_260810_112302.csv"
    r = read_measurement(p, 10660)
    assert r is not None
    assert r.unit_no == 10660
    assert (r.program_nr, r.channel_nr, r.tool_nr, r.cut_nr) == (0, 1, 11, 0)
    assert r.source_time.isoformat() == "2026-08-10T11:23:02.192000"
    assert r.source_file == "000_01_00011_000_260810_112302.csv"
    assert [f.name for f in r.features] == ["SPINDEL", "X AXIS", "Y AXIS", "Z AXIS"]
    assert [f.slot for f in r.features] == [1, 2, 3, 4]
    assert [f.value for f in r.features] == [115.0, 89.0, 96.0, 96.0]
    assert [f.work_value for f in r.features] == [87.0, 90.0, 85.0, 91.0]


def test_bos_hucre_none_olur_sifir_olmaz():
    """Workpiece ID 262/262 bostur; "" ya da 0 degil None olmali."""
    p = VERI / "10660" / "000_01_00011_000_260810_112302.csv"
    r = read_measurement(p, 10660)
    assert r is not None
    assert r.workpiece is None
    assert r.alarm is None
    assert r.alarm_limit is None


def test_bagli_olmayan_sensor_none_kalir():
    """10665'te VIBRATION 131/131 bostur; 0 yazmak 'sensor 0 olctu' derdi."""
    p = VERI / "10665" / "000_01_00011_000_260810_112302.csv"
    r = read_measurement(p, 10665)
    assert r is not None
    assert [f.name for f in r.features] == [
        "VIBRATION",
        "M131 DEBI",
        "M131BASINC",
        "M08 DEBI",
    ]
    assert r.features[0].value is None
    assert r.features[0].work_value is None
    assert r.features[1].value == 214.0
    assert r.features[1].work_value == 100.0


def test_bos_limit_yuvasi_satir_uretmez():
    """Limit 5..8 262/262 bostur: 8 degil 4 limit gelmeli."""
    p = VERI / "10660" / "000_01_00011_000_260810_112302.csv"
    r = read_measurement(p, 10660)
    assert r is not None
    assert [lv.limit_nr for lv in r.limits] == [1, 2, 3, 4]
    assert [lv.level for lv in r.limits] == [110.0, 110.0, 151.0, 110.0]
    assert [lv.lim_type for lv in r.limits] == [1, 1, 1, 1]
    assert [lv.feature_nr for lv in r.limits] == [1, 2, 3, 4]


def test_alarmli_an_okunur():
    """00043 alarmli bir andir: Alarm=1, Alarm limit=2."""
    p = VERI / "10660" / "000_01_00043_000_260810_114320.csv"
    r = read_measurement(p, 10660)
    assert r is not None
    assert r.alarm == 1
    assert r.alarm_limit == 2


def test_tum_dosyalar_cozulur():
    """262/262 — bir tanesi bile atlanirsa sim o ani sessizce kaybederdi."""
    dosyalar = sorted(VERI.rglob("*.csv"))
    assert len(dosyalar) == 262
    assert all(read_measurement(p, int(p.parent.name)) is not None for p in dosyalar)


def test_cok_kisa_dosya_none_doner(tmp_path):
    bozuk = tmp_path / "kisa.csv"
    bozuk.write_text("Program ; 0\nsadece iki satir\n", encoding="utf-8")
    assert read_measurement(bozuk, 10660) is None


def test_yanlis_kolon_sayisi_none_doner(tmp_path):
    """41 degil 5 kolon: sessizce yanlis kolondan okumaktansa ani ATLA."""
    bozuk = tmp_path / "dar.csv"
    bozuk.write_text(
        "Program ; 0\nChannel ; 1\nTool ; 11\nCut ; 0\n"
        "Start date ; 2026-08-10 11:23:02.192\n"
        "End date ; 2026-08-10 11:23:02.192\n"
        "File version ; 1\n\n"
        "Time (s) ; Date ; Time ; A ; B\n"
        "0 ; 10.08.2026 ; 11:23:02 ; 1 ; 2\n",
        encoding="utf-8",
    )
    assert read_measurement(bozuk, 10660) is None


def test_utf8_disi_dosya_none_doner(tmp_path):
    """cp1254 ile yazilmis bir ozellik adi TUM sim'i oldurmemeli.

    UnicodeDecodeError OSError DEGILDIR; yakalanmadigi surece tek bir
    UTF-8 disi bayt yakalanmamis bir traceback'le replay'i durduruyordu.
    Gercekci giris: ozellik adlari operatorun yazdigi Turkce/Almanca
    etiketlerdir (CONTEXT'teki "M131 BASINC" ASCII'ye indirgenmis halidir).
    """
    kaynak = (VERI / "10660" / "000_01_00011_000_260810_112302.csv").read_text(
        encoding="utf-8"
    )
    bozuk = tmp_path / "cp1254.csv"
    bozuk.write_text(kaynak.replace("SPINDEL", "BASINÇ"), encoding="cp1254")
    assert read_measurement(bozuk, 10660) is None


def test_bilinmeyen_surum_none_doner(tmp_path):
    """File version 2 farkli bir yerlesim demektir; tahmin etmeyiz."""
    kaynak = (VERI / "10660" / "000_01_00011_000_260810_112302.csv").read_text(
        encoding="utf-8"
    )
    bozuk = tmp_path / "surum2.csv"
    bozuk.write_text(kaynak.replace("File version ; 1", "File version ; 2"), encoding="utf-8")
    assert read_measurement(bozuk, 10660) is None


def test_anlar_iki_uniteyi_eslestirir():
    anlar = read_moments(VERI)
    assert len(anlar) == 131
    # 54 ve 99 IKI unitede de eksik, o yuzden her an iki dosya tasir.
    assert all(len(a.files) == 2 for a in anlar)
    assert {u for a in anlar for u, _ in a.files} == {10660, 10665}
    assert isinstance(anlar[0], Moment)


def test_anlar_zaman_sirasinda():
    """Dosya adi ...{YYMMDD}_{HHMMSS} ile bittigi icin alfabetik = zaman sirasi."""
    anlar = read_moments(VERI)
    assert anlar[0].name == "000_01_00011_000_260810_112302.csv"
    assert anlar[-1].name == "000_01_00143_000_260810_123647.csv"


def test_eksik_sira_numaralari_an_uretmez():
    """54 ve 99 iki unitede de yok; olmayan ani uydurmuyoruz."""
    adlar = {a.name for a in read_moments(VERI)}
    assert not any("_00054_" in n or "_00099_" in n for n in adlar)


def test_tek_uniteli_an_da_kabul_edilir(tmp_path):
    """Bir uniteden eksik olan an, DIGER unite icin yine yazilmali."""
    (tmp_path / "10660").mkdir()
    (tmp_path / "10665").mkdir()
    kaynak = VERI / "10660" / "000_01_00011_000_260810_112302.csv"
    (tmp_path / "10660" / kaynak.name).write_bytes(kaynak.read_bytes())
    anlar = read_moments(tmp_path)
    assert len(anlar) == 1
    assert anlar[0].files == [(10660, tmp_path / "10660" / kaynak.name)]


def test_kok_yoksa_acik_hata(tmp_path):
    with pytest.raises(FileNotFoundError):
        read_moments(tmp_path / "olmayan")


def test_unite_klasoru_yoksa_acik_hata(tmp_path):
    with pytest.raises(FileNotFoundError):
        read_moments(tmp_path)


def test_bos_unite_klasorleri_acik_hata(tmp_path):
    """Klasorler var ama CSV yok: bos liste DEGIL, acik hata.

    Bos liste run()'in an-basi uykusunu tamamen atlatiyordu (o uyku ic
    dongudedir): `while True` tur basina bir DELETE+COMMIT ile serbest
    kosuyordu - olculdu, ~3000 tur/sn ve surekli tutulan SQLite yazma kilidi.
    """
    (tmp_path / "10660").mkdir()
    (tmp_path / "10665").mkdir()
    with pytest.raises(FileNotFoundError):
        read_moments(tmp_path)
