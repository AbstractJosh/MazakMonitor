"""API uclari testleri. PROMOS3_ENABLED=false (conftest) — lifespan adaptor baslatmaz."""

from fastapi.testclient import TestClient

from app.main import app

# Modul duzeyinde paylasilan istemci: tezgah-basli uclarin 404 testleri
# lifespan'e ihtiyac duymaz (kaynaksiz kurulumda HUBS zaten bostur).
client = TestClient(app)


def test_health():
    with TestClient(app) as client:
        assert client.get("/api/health").json() == {"status": "ok"}


def test_live_kaynaksiz_kurulumda_404_doner():
    """conftest uc bayragi da kapatir: hicbir tezgahin hub'i yoktur.

    Eskiden bu test tekil hub'in bos durumunu okuyordu; hub artik tezgaha
    aittir ve kaynaksiz tezgahin hub'i HIC kurulmaz.
    """
    r = client.get("/api/live", params={"tezgah": "tesis-a/tezgah-1"})
    assert r.status_code == 404


def test_events_ve_alarms_kaynaksiz_tezgahta_404_doner():
    """Hub'lar tezgaha bagli: kaynaksiz tezgah icin olay/alarm ucu da 404 verir."""
    with TestClient(app) as client:
        assert client.get("/api/events", params={"tezgah": "tesis-a/tezgah-1"}).status_code == 404
        assert client.get("/api/alarms", params={"tezgah": "tesis-a/tezgah-1"}).status_code == 404


def test_measurements_bos_db(db_bos):
    with TestClient(app) as client:
        assert client.get("/api/measurements").json() == {"total": 0, "measurements": []}


def test_measurements_unite_suzgeci_ve_ic_ice_alanlar(db_bos):
    from datetime import datetime

    from app.config import settings
    from app.db import SessionLocal
    from app.sim.csv_reader import read_moments
    from app.sim.replay import write_moment

    anlar = read_moments(settings.csv_dir())
    with SessionLocal() as s:
        write_moment(s, anlar[0], datetime(2026, 8, 11, 9, 0, 0))

    with TestClient(app) as client:
        govde = client.get("/api/measurements?unit=10665").json()
        # total SUZGECE uyan TUM satir sayisidir; iki unite yazildi, biri suzuldu.
        assert govde["total"] == 1
        m = govde["measurements"][0]
        # Tel bicimi camelCase (mevcut uclarla ayni).
        assert m["unitNo"] == 10665
        assert m["toolNr"] == 11
        assert m["sourceFile"] == "000_01_00011_000_260810_112302.csv"
        assert [f["name"] for f in m["features"]] == [
            "VIBRATION",
            "M131 DEBI",
            "M131BASINC",
            "M08 DEBI",
        ]
        # Bagli olmayan sensor null gelir, 0 gelmez.
        assert m["features"][0]["value"] is None
        assert m["features"][1]["workValue"] == 100.0
        assert [lv["limitNr"] for lv in m["limits"]] == [1, 2, 3, 4]


def test_measurements_en_yeni_basta(db_bos):
    from datetime import datetime

    from app.config import settings
    from app.db import SessionLocal
    from app.sim.csv_reader import read_moments
    from app.sim.replay import write_moment

    anlar = read_moments(settings.csv_dir())
    with SessionLocal() as s:
        write_moment(s, anlar[0], datetime(2026, 8, 11, 9, 0, 0))
        write_moment(s, anlar[1], datetime(2026, 8, 11, 9, 0, 1))

    with TestClient(app) as client:
        govde = client.get("/api/measurements?unit=10660&limit=2").json()
        assert govde["total"] == 2
        assert govde["measurements"][0]["toolNr"] == 12
        assert govde["measurements"][1]["toolNr"] == 11


def test_measurements_tablolar_yoksa_503_ve_ne_yapilacagi(db_bos):
    """Ciplak 500 yerine ne yapilacagini soyleyen 503.

    `.\\basla.bat` artik HER kosumda alembic'i kosturur, ama elle baslatilan
    backend (`uv run uvicorn ...`, migration'siz) ya da semasi eski kalmis
    bir DB hala tablosuz kalabilir; o durumda bu uca bakan biri sebepsiz bir
    "Internal Server Error" goruyordu. replay.py ayni durumda cikis kodu 2 +
    "alembic upgrade head" diyor; uc ise ayni bilgiye sahipken susuyordu.
    """
    from app.db import engine
    from app.models import Base

    Base.metadata.drop_all(engine)
    with TestClient(app) as client:
        cevap = client.get("/api/measurements")
        assert cevap.status_code == 503
        assert "alembic upgrade head" in cevap.json()["detail"]


def test_measurements_limit_kirpilir():
    """Ust sinir olmadan `limit=999999` butun tabloyu bellege alirdi."""
    from app.measurements import MAX_LIMIT, _clamp_limit

    assert _clamp_limit(999999) == MAX_LIMIT
    assert _clamp_limit(0) == 1
    assert _clamp_limit(-5) == 1
    assert _clamp_limit(50) == 50


def test_stream_bilinmeyen_tezgahta_404():
    """`/api/stream` SSE dondurur ama 404 dalinda _hub_for daha govde
    kurulmadan fırlar: normal JSON hata govdesi doner, istek asilmaz.
    """
    r = client.get("/api/stream", params={"tezgah": "tesis-z/tezgah-9"})
    assert r.status_code == 404
    assert "api/machines" in r.json()["detail"]


def test_stream_kaynaksiz_tezgahta_404():
    """Kaynaksiz tezgah bos bir akis DEGIL, 404 verir.

    Frontend o tezgah icin akisi HIC kurmaz (bos durum verir); bu uc
    yalnizca elle/teshis amacli cagrilar icin bir bekcidir.
    """
    r = client.get("/api/stream", params={"tezgah": "tesis-d/tezgah-4"})
    assert r.status_code == 404


def test_live_bilinmeyen_tezgahta_404():
    """`/api/stream`'in bilinmeyen-tezgah 404'una esdeger `/api/live` kapsami."""
    r = client.get("/api/live", params={"tezgah": "tesis-z/tezgah-9"})
    assert r.status_code == 404
    assert "api/machines" in r.json()["detail"]


def test_machines_ucu_katalogu_doner():
    body = client.get("/api/machines").json()
    assert len(body["facilities"]) == 4
    assert all(len(f["machines"]) == 4 for f in body["facilities"])
    # conftest uc bayragi da kapatir -> hicbir tezgahin kaynagi yok.
    hepsi = [m for f in body["facilities"] for m in f["machines"]]
    assert all(m["source"] is None for m in hepsi)
    assert all(m["connected"] is False for m in hepsi)
    # Kaynak yoksa yas da yoktur; "0 saniye once" uydurulmaz.
    assert all(m["dataAgeS"] is None for m in hepsi)


def test_machines_ucu_BAGLI_ama_sessiz_kaynagi_yesil_gostermez(monkeypatch):
    """/api/machines'in sozunu UCTAN UCA dogrular.

    Soketi baglanmis ama tek bayt almamis bir hub: `connected` True, ama
    `dataAgeS` None. Karsilama ekraninin yesil rozeti ikincisine bakar —
    bakmasaydi bu makinede A/1 (PROMOS3_BIND=127.0.0.1) sonsuza dek "Canli"
    gorunurdu.
    """
    from app import main
    from app.hub import DATA_STALE_AFTER_S, LiveHub

    hub = LiveHub(source_name="provis")
    hub.set_source_status("provis", True)
    monkeypatch.setitem(main.HUBS, "tesis-a/tezgah-1", hub)

    body = client.get("/api/machines").json()
    assert body["stalenessS"] == DATA_STALE_AFTER_S
    tezgahlar = {m["id"]: m for f in body["facilities"] for m in f["machines"]}
    a1 = tezgahlar["tesis-a/tezgah-1"]
    assert a1["connected"] is True
    assert a1["dataAgeS"] is None

    # Veri gelince yas dogar ve esigin altinda kalir.
    from app.promos3.messages import identify_answer

    hub.apply_promos3_message(identify_answer(1, b"\x00" * 40), "2026-08-03T10:00:00+00:00")
    tezgahlar = {
        m["id"]: m
        for f in client.get("/api/machines").json()["facilities"]
        for m in f["machines"]
    }
    assert tezgahlar["tesis-a/tezgah-1"]["dataAgeS"] < DATA_STALE_AFTER_S


def test_uclar_atanan_hubun_durumunu_okur_basari_yolu(monkeypatch):
    """`_hub_for`'un BASARI dalini uctan uca dogrular.

    conftest uc kaynagi da kapattigindan `HUBS` butun suit boyunca bostur;
    yukaridaki testler bu yuzden hep 404'te kaliyordu ve `live()`/`events()`/
    `alarms()` govdelerindeki "yanlis anahtar" turu bir hata bu suitten
    kacabilirdi. Burada TEK bir tezgaha gercek bir `LiveHub` elle takilir
    (monkeypatch.setitem: test sonunda `HUBS` oldugu gibi geri doner) ve uc
    ucun da KENDI hub'ini okudugu -- rastgele/eski bir tekil hub degil --
    ayirt edici kimliklerle kanitlanir.
    """
    from app import main
    from app.domain import Alarm, EventRow
    from app.hub import LiveHub

    TIME = "2026-08-03T10:00:00+00:00"
    hub = LiveHub()
    hub.state = hub.state.model_copy(
        update={
            "events": [EventRow(id="olay-1", time=TIME)],
            "alarms": [Alarm(id="alarm-1", time=TIME)],
        }
    )
    monkeypatch.setitem(main.HUBS, "tesis-a/tezgah-1", hub)

    r = client.get("/api/live", params={"tezgah": "tesis-a/tezgah-1"})
    assert r.status_code == 200
    body = r.json()
    assert set(body) == {"status", "state"}
    assert body["state"]["events"][0]["id"] == "olay-1"
    assert body["state"]["alarms"][0]["id"] == "alarm-1"

    r_events = client.get("/api/events", params={"tezgah": "tesis-a/tezgah-1"})
    assert r_events.status_code == 200
    assert r_events.json()[0]["id"] == "olay-1"

    r_alarms = client.get("/api/alarms", params={"tezgah": "tesis-a/tezgah-1"})
    assert r_alarms.status_code == 200
    assert r_alarms.json()[0]["id"] == "alarm-1"
