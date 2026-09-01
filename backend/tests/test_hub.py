"""LiveHub testleri: SSE cerceve akisi (baglanis paketi, degisim, son-durum-kazanir)."""

import asyncio
import json
import time

import pytest

from app.hub import DATA_STALE_AFTER_S, LiveHub, sse_frame
from app.promos3.messages import identify_answer
from tests.capture import decode_cap


def parse_frame(raw):
    lines = raw.strip().split("\n")
    assert lines[0].startswith("event: ") and lines[1].startswith("data: ")
    return lines[0].removeprefix("event: "), json.loads(lines[1].removeprefix("data: "))


TIME = "2026-08-03T10:00:00+00:00"


def test_sse_frame_tek_satir_json():
    raw = sse_frame("state", {"a": "ç"})  # ensure_ascii=False: Turkce oldugu gibi
    assert raw == 'event: state\ndata: {"a": "ç"}\n\n'


@pytest.mark.anyio
async def test_baglanista_status_ve_state_gelir():
    hub = LiveHub()
    gen = hub.sse_frames()
    name1, data1 = parse_frame(await asyncio.wait_for(anext(gen), 1))
    assert name1 == "status"
    # sources: kaynak basina durum (henuz hicbir adaptor bildirmedi -> bos).
    assert data1 == {"source": "promos3", "connected": False, "sources": {}}
    name2, data2 = parse_frame(await asyncio.wait_for(anext(gen), 1))
    assert name2 == "state"
    st = data2["state"]
    # exclude_none: bos opsiyoneller (cycle, workpiece, wire...) telde YOK.
    assert "cycle" not in st and "wire" not in st
    # Onceden tanimli grafik yok: ozellikler telden gelir.
    assert st["features"] == []
    await gen.aclose()


@pytest.mark.anyio
async def test_degisim_yeni_state_cercevesi_uretir_ve_son_durum_kazanir():
    """Abone beklerken arka arkaya iki mesaj: TEK cerceve, SON durum gelir."""
    hub = LiveHub()
    msgs, _ = decode_cap("sim_stream.cap")
    gen = hub.sse_frames()
    await asyncio.wait_for(anext(gen), 1)  # status
    await asyncio.wait_for(anext(gen), 1)  # state (bos)

    for msg in msgs[:4]:
        hub.apply_promos3_message(msg, TIME)

    name, data = parse_frame(await asyncio.wait_for(anext(gen), 1))
    assert name == "state"
    st = data["state"]
    assert st["units"][0]["konfigVersion"] == 229
    # Tel teshisi her mesajda guncellenir.
    assert st["wire"]["parsed"] == 4
    assert st["wire"]["unparsed"] == 0
    await gen.aclose()


@pytest.mark.anyio
async def test_kaynak_durumu_degisince_status_cercevesi():
    hub = LiveHub()
    gen = hub.sse_frames()
    await asyncio.wait_for(anext(gen), 1)
    await asyncio.wait_for(anext(gen), 1)
    hub.set_source_status("promos3", True)
    name, data = parse_frame(await asyncio.wait_for(anext(gen), 1))
    assert name == "status"
    assert data["connected"] is True
    assert data["sources"] == {"promos3": True}
    await gen.aclose()


@pytest.mark.anyio
async def test_kimliksiz_mesaj_sayaci_artirir_ama_durumu_bozmaz():
    """"Veri gelmiyor" ile "geliyor ama cozulmuyor" ayri gorunmeli."""
    hub = LiveHub()
    gen = hub.sse_frames()
    await asyncio.wait_for(anext(gen), 1)
    await asyncio.wait_for(anext(gen), 1)

    hub.apply_promos3_message(identify_answer(1, b"\x00" * 40), TIME)
    _name, data = parse_frame(await asyncio.wait_for(anext(gen), 1))
    wire = data["state"]["wire"]
    assert wire["unparsed"] == 1
    assert wire["parsed"] == 0
    assert wire["lastUnparsedHex"]  # ham baytlar ekrana tasindi
    await gen.aclose()


@pytest.mark.anyio
async def test_degismeyen_tel_sayaclari_aboneyi_uyandirmaz():
    """Sessiz telde her saniye cerceve yayinlamak tum istemcileri uyandirirdi.

    ILK cagri yine de yayinlanir: WireStats'i var eder, yani ekran "adaptor
    ayakta, henuz veri yok" ile "adaptor hic yok"u ayirt edebilir. Bastirilan
    yalniz TEKRARLARDIR.
    """
    hub = LiveHub()
    gen = hub.sse_frames()
    await asyncio.wait_for(anext(gen), 1)
    await asyncio.wait_for(anext(gen), 1)

    hub.set_wire_counters(datagrams=0, can_frames=0, out_of_range=0, overflow=0)
    _name, data = parse_frame(await asyncio.wait_for(anext(gen), 1))
    assert data["state"]["wire"]["datagrams"] == 0  # teshis blogu artik var

    # Ayni sayaclar yeniden: degisiklik yok, abone uyandirilmaz.
    hub.set_wire_counters(datagrams=0, can_frames=0, out_of_range=0, overflow=0)
    with pytest.raises(asyncio.TimeoutError):
        await asyncio.wait_for(anext(gen), 0.2)
    await gen.aclose()


def test_frames_uygulanan_yuk_basina_artar():
    """`frames` KAYNAKTAN BAGIMSIZ canlilik olcusudur.

    `wire.parsed` yalnizca Promos3 tasimasini sayar; CSV tezgahinin teli
    olmadigi icin orada hep 0 kalir ve ust bar kusursuz akan bir tezgahta
    "Veri Yok" yazardi. Bu sayac o soruyu her kaynak icin cevaplar.
    """
    hub = LiveHub()
    assert hub.frames == 0
    hub.apply_promos3_message(identify_answer(1, b"\x00" * 40), TIME)
    assert hub.frames == 1
    hub.apply_promos3_message(identify_answer(1, b"\x00" * 40), TIME)
    assert hub.frames == 2


@pytest.mark.anyio
async def test_state_cercevesi_frames_tasir():
    hub = LiveHub()
    gen = hub.sse_frames()
    await gen.__anext__()  # status
    cerceve = await gen.__anext__()  # state
    assert '"frames": 0' in cerceve

    hub.apply_promos3_message(identify_answer(1, b"\x00" * 40), TIME)
    cerceve = await gen.__anext__()
    assert '"frames": 1' in cerceve


# --- Tazelik: "hic geldi mi" ile "SU AN geliyor mu" ayri sorulardir ---------


def test_veri_gelmeden_yas_YOKTUR_ve_taze_degildir():
    """Soket bagli ama tek bayt gelmemis hal.

    Eskiden ekran icin tek olcut "bagli"ydi ve bu hal YESIL gorunuyordu
    (PROMOS3_BIND=127.0.0.1 olan bu makinede A/1 kalici olarak boyle).
    """
    hub = LiveHub()
    hub.set_source_status("provis", True)
    assert hub.upstream_connected is True
    assert hub.data_age_s is None
    assert hub.data_fresh is False


def test_promos3_yuku_tazelik_damgasi_atar():
    hub = LiveHub()
    hub.apply_promos3_message(identify_answer(1, b"\x00" * 40), TIME)
    assert hub.data_age_s is not None
    assert hub.data_age_s < 1.0
    assert hub.data_fresh is True


def test_csv_olcumu_de_tazelik_damgasi_atar():
    """Damga IKI adaptorde de atilir; yalniz birinde atmak otekini bayat
    gosterirdi (CSV tezgahi kusursuz akarken "Veri Yok" derdi)."""
    from datetime import datetime

    from app.sim.csv_reader import FeatureValue, MeasurementRecord

    hub = LiveHub(source_name="csv")
    rec = MeasurementRecord(
        unit_no=10660,
        source_time=datetime(2026, 8, 10, 11, 23, 2),
        channel_nr=1,
        tool_nr=11,
        program_nr=0,
        cut_nr=0,
        workpiece=None,
        alarm=None,
        alarm_limit=None,
        source_file="000_01_00011_000_260810_112302.csv",
        features=[FeatureValue(slot=1, name="SPINDEL", value=115.0, work_value=87.0)],
        limits=[],
    )
    hub.apply_measurement(rec, TIME)
    assert hub.frames == 1
    assert hub.data_fresh is True


def test_susan_kaynak_esikten_sonra_TAZE_DEGIL_ama_frames_kalir():
    """`frames` geri saymaz; tazeligi soyleyen odur diye dusunmek hataydi."""
    hub = LiveHub()
    hub.apply_promos3_message(identify_answer(1, b"\x00" * 40), TIME)
    # Kaynak sustu: son yukun uzerinden esikten fazlasi gecti.
    hub.last_frame_at = time.monotonic() - DATA_STALE_AFTER_S - 1.0
    assert hub.frames == 1  # "hic geldi mi" -> evet
    assert hub.data_fresh is False  # "su an geliyor mu" -> hayir
    assert hub.data_age_s > DATA_STALE_AFTER_S


def test_esigin_TAM_uzerinde_hala_taze():
    """Sinir dahildir: saglikli ama yavas bir kaynak esikte dusurulmez."""
    hub = LiveHub()
    hub.apply_promos3_message(identify_answer(1, b"\x00" * 40), TIME)
    hub.last_frame_at = time.monotonic() - DATA_STALE_AFTER_S + 0.5
    assert hub.data_fresh is True


@pytest.mark.anyio
async def test_state_cercevesi_yas_ve_esik_tasir():
    hub = LiveHub()
    gen = hub.sse_frames()
    await asyncio.wait_for(anext(gen), 1)  # status
    _name, data = parse_frame(await asyncio.wait_for(anext(gen), 1))
    # Hic veri gelmemisken yas YOK (null); "0 saniye once" demek yalan olurdu.
    assert data["dataAgeS"] is None
    # Esik telde gider: sayinin tek sahibi backend'dir.
    assert data["stalenessS"] == DATA_STALE_AFTER_S

    hub.apply_promos3_message(identify_answer(1, b"\x00" * 40), TIME)
    _name, data = parse_frame(await asyncio.wait_for(anext(gen), 1))
    assert data["dataAgeS"] is not None and data["dataAgeS"] < 1.0
    await gen.aclose()


@pytest.mark.anyio
async def test_nabiz_tazeligi_TASIR(monkeypatch):
    """Kaynak sustugunda "state" cercevesi HIC dogmaz.

    Yas yalniz state zarfinda gitseydi istemci son gordugu yasla kalir ve
    "Veri Akisi Aktif" kalicilasirdi. Nabiz zaten sessizlikte atiyor; yasi
    ona bindirmek yeni bir zamanlayici gerektirmez.
    """
    monkeypatch.setattr("app.hub.PING_INTERVAL_S", 0.05)
    hub = LiveHub()
    hub.apply_promos3_message(identify_answer(1, b"\x00" * 40), TIME)
    gen = hub.sse_frames()
    await asyncio.wait_for(anext(gen), 1)  # status
    await asyncio.wait_for(anext(gen), 1)  # state

    name, data = parse_frame(await asyncio.wait_for(anext(gen), 1))
    assert name == "ping"
    assert data["dataAgeS"] is not None
    assert "tMs" in data
    await gen.aclose()
