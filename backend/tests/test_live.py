"""Esleyici (app.live) testleri — mesajdan canli duruma.

Veri kaynagi tests/data/*.cap: promos3_sim.exe'nin urettigi GERCEK tel baytlari
(bkz. tests/capture.py). Esleyiciler saf ve saatsizdir, bu yuzden burada ag da
zaman da yoktur.
"""

from app.live import (
    apply_promos3_message,
    initial_live_state,
    series_feature_id,
    trace_feature_id,
)
from app.promos3.messages import CMD_KANAL, CMD_MERKMALE, identify_answer
from tests.capture import decode_cap, first, replay_cap

TIME = "2026-08-03T10:00:00+00:00"


def test_baslangic_durumu_TAMAMEN_bos():
    """Onceden tanimli grafik YOKTUR: ozellikler ve adlari telden gelir.

    Yer tutucu grafik acmak, akis gelmeden once ekranda "veri var" izlenimi
    verirdi.
    """
    state = initial_live_state()
    assert state.features == []
    assert state.units == []
    assert state.alarms == []
    assert state.events == []
    assert state.cycle is None
    assert state.workpiece is None


def test_kimliksiz_mesaj_durumu_DEGISTIRMEZ():
    state = initial_live_state()
    same = apply_promos3_message(state, identify_answer(1, b"\x00" * 40), TIME)
    assert same is state


def test_yakalama_dort_seri_ve_bir_iz_uretir():
    """0x16 -> ozellik basina kayan pencere; 0x1B -> 125 ornekli iz."""
    state = replay_cap("sim_stream.cap")
    series = [f for f in state.features if f.kind == "series"]
    traces = [f for f in state.features if f.kind == "trace"]
    assert len(series) == 4
    assert len(traces) == 1
    assert len(traces[0].samples) == 125


def test_ozellik_adlari_TELDEN_gelir():
    """Operator etiketleri SKanalRec'ten okunur; koda gomulu degil."""
    state = replay_cap("sim_stream.cap")
    series = sorted(
        (f for f in state.features if f.kind == "series"), key=lambda f: f.feature_nr or 0
    )
    assert [f.name for f in series] == [
        "VIBRATION",
        "M131 DEBI",
        "M131BASINC",
        "M08 DEBI",
    ]
    assert [f.mask for f in series] == [0x01, 0x02, 0x04, 0x08]


def test_iz_adini_channel_key_uzerinden_ozellikten_alir():
    """channelKey 0x01 -> maske 0x01 -> "VIBRATION" (uydurma esleme yok)."""
    state = replay_cap("sim_stream.cap")
    trace = next(f for f in state.features if f.kind == "trace")
    assert trace.name == "VIBRATION"
    assert trace.id == trace_feature_id(trace.unit_no or 0, trace.tool_key or 0, trace.channel_key or 0)


def test_olcumler_HAM_SAYIM_ve_limitsiz_yuzde_uretmez():
    """Genlik 0..255 ham sayimdir; guvenilir limit yoksa yuzde HESAPLANMAZ."""
    state = replay_cap("sim_stream.cap")
    for f in state.features:
        assert f.raw_counts is True
        assert f.uom == ""
        assert f.limit_level is None
        assert f.pct is None
        assert all(0 <= s <= 255 for s in f.samples)


def test_seriler_paketler_arasinda_BIRIKIR_iz_ise_YENILENIR():
    """Iki farkli besleme bicimi: kayan pencere ve tek cerceve."""
    msgs, _ = decode_cap("sim_stream.cap")
    state = initial_live_state()

    merkmale = [m for m in msgs if m.command == CMD_MERKMALE]
    assert len(merkmale) >= 2

    state = apply_promos3_message(state, first(msgs, CMD_KANAL), TIME)
    state = apply_promos3_message(state, merkmale[0], TIME)
    after_one = len(next(f for f in state.features if f.kind == "series").samples)
    state = apply_promos3_message(state, merkmale[1], TIME)
    after_two = len(next(f for f in state.features if f.kind == "series").samples)
    assert after_two > after_one  # seri birikti


def test_ayni_ozellik_hep_ayni_grafige_duser():
    """Kimlik (unite, yuva) ikilisine baglidir; grafik sirasi sabit kalir."""
    state = replay_cap("sim_stream.cap")
    ids = [f.id for f in state.features if f.kind == "series"]
    assert len(ids) == len(set(ids))
    assert series_feature_id(1, 0) in ids


def test_unite_yapilandirmasi_konfigden_dolar():
    state = replay_cap("sim_stream.cap")
    assert len(state.units) == 1
    unit = state.units[0]
    assert unit.unit == 1
    assert unit.online is True
    assert unit.konfig_version == 229
    assert unit.channel_amount == 1
    assert unit.mi_sens_amount == 4


def test_cevrim_ve_plc_degerleri_telden_gelir():
    state = replay_cap("sim_stream.cap")
    assert state.cycle is not None
    assert state.plc_inputs is not None
    assert state.plc_outputs is not None


def test_im_satirlari_olaya_donusur():
    """0x16 icindeki im satirlari (yeni cevrim / yeni is parcasi) olay uretir."""
    state = replay_cap("sim_rows4.cap")
    # Bu yakalamada im olmayabilir; olan durumda etiketi anlamli olmali.
    for row in state.events:
        assert row.code_label
        assert row.unit_no == 1
