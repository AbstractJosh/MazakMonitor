"""Tam kosum kaydi — CSV korpusunun TAMAMI.

conftest SIM_CSV_DIR'i depodaki `veri/`ye sabitler, o yuzden buradaki
sayilar (131 an, 7 seri) HARFI iddialardir; test_csv_reader.py ve
test_replay.py ile ayni gerekce.
"""

import pytest
from fastapi.testclient import TestClient

from app.config import Settings, settings
from app.csv_live import csv_feature_id
from app.kosum import build_kosum
from app.machines import build_catalog
from app.main import app
from app.sim.baselines import compute_baselines
from app.sim.csv_reader import read_moments

# Lifespan BILEREK kosturulmaz (test_api.py ile ayni gerekce): `with
# TestClient(app)` asagidaki CSV katalogu ile birlikte gercek bir CSV ingest
# gorevi baslatir ve gecici DB'ye yazmaya koyulurdu. Bu ucun lifespan'e
# ihtiyaci yok — katalogu okur, hub'a hic dokunmaz.
client = TestClient(app)


@pytest.fixture
def csv_katalog(monkeypatch):
    """CSV kaynakli bir katalog takar (conftest UC KAYNAGI DA kapatir).

    monkeypatch.setattr: `CATALOG` modul duzeyinde bir kez hesaplanir ve
    test sonunda oldugu gibi geri doner — kalici bir atama, katalogun
    kaynaklari hakkinda iddia tasiyan test_api/test_machines testlerine
    sizardi.
    """
    monkeypatch.setattr(
        "app.main.CATALOG",
        build_catalog(
            Settings(
                csv_replay_enabled=True, promos3_enabled=False, promos3_sim_enabled=False
            )
        ),
    )


def test_kosum_butun_anlari_kapsar_ve_canli_pencereden_UZUNDUR():
    """Bu ucun VAROLMA SEBEBI: kosum canli pencereye SIGMAZ.

    Canli ekran live.WINDOW ornek gosterir; kosumda 131 an vardir. Ikisi
    esitlenirse (ya da pencere buyurse) bu uc gereksizlesir — o gun bunu
    bilerek silmek icin sayiyi burada karsilastiriyoruz.
    """
    from app.live import WINDOW

    kosum = build_kosum(settings.csv_dir())

    assert kosum.count == 131
    assert len(kosum.rows) == 131
    assert kosum.count > WINDOW


def test_kosum_bos_yuva_seri_uretmez():
    """10665/VIBRATION 131/131 bostur: 2 unite x 4 yuva = 8 DEGIL 7 seri.

    csv_live.py ve baselines.py ile ayni kural.
    """
    kosum = build_kosum(settings.csv_dir())

    assert [s.name for s in kosum.series] == [
        "SPINDEL",
        "X AXIS",
        "Y AXIS",
        "Z AXIS",
        "M131 DEBI",
        "M131BASINC",
        "M08 DEBI",
    ]
    assert "VIBRATION" not in {s.name for s in kosum.series}
    # Sira SABIT: once unite, sonra yuva. Grafik renkleri seri sirasina bagli.
    assert [(s.unit_no, s.slot) for s in kosum.series] == [
        (10660, 1),
        (10660, 2),
        (10660, 3),
        (10660, 4),
        (10665, 2),
        (10665, 3),
        (10665, 4),
    ]


def test_kosum_kimligi_canli_yolla_AYNIDIR():
    """Ayni sinyal iki ekranda ayni adla anilir (csv_live.csv_feature_id)."""
    kosum = build_kosum(settings.csv_dir())

    assert {s.id for s in kosum.series} == {
        csv_feature_id(s.unit_no, s.slot) for s in kosum.series
    }
    assert kosum.series[0].id == "csv:10660:1"


def test_kosum_tabani_baselines_ile_AYNI_SAYIYI_verir():
    """Taban TEK GECISTE cikar ama tanimi baselines.py'ninkiyle aynidir.

    Ayrilsalardi canli esik ile kosum grafiginin altindaki ortalama ayni
    veriden iki farkli sayi gosterirdi.
    """
    kosum = build_kosum(settings.csv_dir())
    beklenen = compute_baselines(read_moments(settings.csv_dir()))

    assert {(s.unit_no, s.slot): s.baseline for s in kosum.series} == beklenen


def test_kosum_zamani_AN_DEGIL_gun_ve_saat_tasir():
    """Telde naif ISO an YOK: gun `YYYY-MM-DD`, saat `HH:MM:SS`.

    An gonderilseydi arayuz onu tarayici diliminde cozer, tasarim sisteminin
    formatDateTime'i Istanbul'a cevirir ve iki dilim tutmayan her makinede
    kosum saatleri kayardi.
    """
    kosum = build_kosum(settings.csv_dir())

    assert kosum.start_day == "2026-08-10"
    assert kosum.start_time == "11:23:02"
    assert kosum.end_day == "2026-08-10"
    assert kosum.end_time == "12:36:47"
    # Bu korpus TEK GUNDUR; ekran tarih araligini buna bakarak yazar.
    assert {r.day for r in kosum.rows} == {"2026-08-10"}


def test_kosum_okunmayan_yuva_ANAHTARSIZDIR():
    """Bos yuva 0 ile doldurulmaz: sifir olculmus gibi cizilirdi."""
    kosum = build_kosum(settings.csv_dir())

    vibration = csv_feature_id(10665, 1)
    assert all(vibration not in r.values for r in kosum.rows)
    # Kalan yedi yuva bu korpusta HER anda doludur.
    assert all(len(r.values) == 7 for r in kosum.rows)
    assert all(s.count == kosum.count for s in kosum.series)


def test_kosum_ucu_kaynagi_CSV_OLMAYAN_tezgahta_404(csv_katalog):
    """Kosum kaydi CSV KAYNAGININ ozelligidir, her tezgahin degil.

    A/1'in kaynagi bu katalogda hic yok, A/2'ninki de CSV degil; ikisi de
    ayni sebeple 404 alir. Kaynaklarindan biri acik olsaydi bile cevap
    degismezdi — sart kaynagin CSV OLMASIDIR, var olmasi degil.
    """
    r = client.get("/api/kosum", params={"tezgah": "tesis-a/tezgah-1"})
    assert r.status_code == 404
    # Ciplak degil yol gosteren 404 (_hub_for ile ayni idiom).
    assert "/api/machines" in r.json()["detail"]

    assert client.get("/api/kosum", params={"tezgah": "yok/boyle"}).status_code == 404


def test_kosum_ucu_KAYNAK_OKUNAMAZSA_404_DEGIL_503(csv_katalog, monkeypatch, tmp_path):
    """Katalog CSV VAAT ETTI ama korpus yerinde degil: 404 DEGIL 503.

    Iki cevabin ayri kalmasi sart. 404 "bu tezgahin kayitli kosumu yok"
    demektir ve YAPILANDIRMADIR (kaynagi CSV olmayan tezgah); 503 "olmasi
    gereken kayit okunamadi" demektir ve ARIZADIR. Ikisi ayni koda dusseydi
    `veri/`si eksik deploy edilmis bir kurulum ekranda "bu tezgahin koşumu
    yok" derdi — dogru olmayan, ustelik kimseyi dosyalara bakmaya
    gondermeyen bir cumle.

    Cevap NEYIN okunamadigini da soyler: arayuz hatayi backend'e degil
    kaynaga yazabilsin diye (domain/kosum.ts, `cevapVerdi`).

    Kok `_kosum_kaydi`ye ARGUMAN gectigi icin onbellek bu testte yalan
    soyleyemez: yeni kok = yeni anahtar, gercek korpusun sonucu geri gelmez.
    """
    monkeypatch.setattr(Settings, "csv_dir", lambda self: tmp_path / "olmayan-kok")

    r = client.get("/api/kosum", params={"tezgah": "tesis-a/tezgah-3"})

    assert r.status_code == 503
    assert "CSV kaynagi okunamadi" in r.json()["detail"]


def test_kosum_ucu_CSV_tezgahinda_tam_kosumu_doner(csv_katalog):
    govde = client.get("/api/kosum", params={"tezgah": "tesis-a/tezgah-3"}).json()

    assert govde["count"] == 131
    assert len(govde["rows"]) == 131
    # Tel bicimi camelCase (mevcut uclarla ayni).
    assert govde["startDay"] == "2026-08-10"
    assert govde["startTime"] == "11:23:02"
    assert govde["series"][0]["unitNo"] == 10660
    assert govde["rows"][0]["values"]["csv:10660:1"] == 115.0
