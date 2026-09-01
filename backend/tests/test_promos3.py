"""Promos3 tel katmani testleri — tasima, MC_ kodegi, kimliklendirme, govdeler.

Test verisinin iki kaynagi var ve ikisi de BIZIM KODUMUZDAN BAGIMSIZ:
  1. Raporda BAYT DOGRULANMIS degerler (orn. istek 0x08 -> "08 01 f6", tezgahin
     kendi log satirindan).
  2. promos3-c/done/promos3_sim.exe'nin urettigi gercek yakalama dosyalari
     (tests/data/*.cap) — bkz. tests/capture.py.

Ikinci nokta bilerek boyle: eski tools/mock_gateway.py cozucunun BEKLEDIGI
bicimi uretiyordu, dolayisiyla "cozuldu" demek hicbir sey kanitlamiyordu.
"""

import pytest

from app.promos3 import bodies, mc, records
from app.promos3.messages import (
    CMD_KANAL,
    CMD_KONFIG,
    CMD_MERKMALE,
    CMD_PLCVALUES,
    CMD_SIGNALVERLAUF,
    CMD_STATUS,
    Confidence,
    identify_answer,
)
from app.promos3.transport import (
    BASE_CAN_ID,
    CAN_MAX_DATA,
    GW_RECORD_SIZE,
    AnswerReassembler,
    parse_gateway_record,
    split_datagram,
)
from tests.capture import decode_cap, first, read_cap

# --------------------------------------------------------------------------
# Yardimcilar
# --------------------------------------------------------------------------


def gw_record(can_id: int, data: bytes, length: int | None = None) -> bytes:
    """36 baytlik gateway kaydi kurar (+0x15 len, +0x1A..1B BE id, +0x1C veri)."""
    rec = bytearray(GW_RECORD_SIZE)
    rec[0x00], rec[0x01], rec[0x02], rec[0x03] = 0x00, 0x24, 0x00, 0x80
    rec[0x15] = len(data) if length is None else length
    rec[0x1A] = (can_id >> 8) & 0xFF
    rec[0x1B] = can_id & 0xFF
    rec[0x1C : 0x1C + len(data)] = data
    return bytes(rec)


def frames_for(payload: bytes, unit: int, cmd: int) -> list[bytes]:
    """Bir yuku MC_ cevap cercevelerine boler (promos3_sim.c mc_frame_answer)."""
    ck = mc.answer_checksum(unit, mc.canonical_request(cmd, unit), payload)
    can_id = BASE_CAN_ID + unit
    out: list[bytes] = []
    i = seq = 0
    while i < len(payload):
        chunk = payload[i : i + mc.PAY_PER_FRAME]
        data = bytes([seq]) + chunk
        if len(chunk) < mc.PAY_PER_FRAME:
            data += bytes([ck])
        out.append(gw_record(can_id, data))
        i += len(chunk)
        seq += 1
    if len(payload) % mc.PAY_PER_FRAME == 0:
        out.append(gw_record(can_id, bytes([seq, ck])))
    return out


def _feed_all(reasm: AnswerReassembler, records_: list[bytes]) -> list:
    out = []
    for rec in records_:
        for frame in split_datagram(rec):
            answer = reasm.feed(frame)
            if answer is not None:
                out.append(answer)
    return out


# --------------------------------------------------------------------------
# 1. Tasima: gateway kaydi ve datagram bolme
# --------------------------------------------------------------------------


def test_can_id_buyuk_endian_okunur_ve_unite_verir():
    frame = parse_gateway_record(gw_record(0x0501, b"\x01\x02\x03"))
    assert frame is not None
    assert frame.can_id == 0x0501
    assert frame.unit == 0x0501 - BASE_CAN_ID == 1
    assert frame.length == 3


def test_olanaksiz_dlc_kaydi_dusurur_kirpmaz():
    """dlc > 8 bozuk kayittir; 8'e kirpmak cop baytlari mesaja enjekte ederdi."""
    assert parse_gateway_record(gw_record(0x0501, b"\x01", length=0xFF)) is None
    assert split_datagram(gw_record(0x0501, b"\x01", length=0xFF)) == []


def test_artan_baytlar_BASTAN_kirpilir():
    """Uygulama remove(0, size % 0x24) yapar; hizalamayi kaydirmak her kaydi bozar."""
    rec = gw_record(0x0501, b"\xaa")
    frames = split_datagram(b"\xde\xad\xbe\xef" + rec)
    assert len(frames) == 1
    assert frames[0].data[0] == 0xAA


def test_36_bayttan_kisa_datagram_yok_sayilir():
    assert split_datagram(b"\x00" * 10) == []


# --------------------------------------------------------------------------
# 2. MC_ kodegi: saglama toplami ve kanonik istek
# --------------------------------------------------------------------------


def test_istek_saglama_toplami_bayt_dogrulanmis():
    """Tezgahin kendi log satiri: "requested 0x08, 0x01, 0xf6"."""
    assert mc.canonical_request(0x08, unit=1) == bytes([0x08, 0x01, 0xF6])
    # Ayni istek 2 ve 3. unitelerde f5 / f4 verir (saglama uniteyi icerir).
    assert mc.canonical_request(0x08, unit=2)[-1] == 0xF5
    assert mc.canonical_request(0x08, unit=3)[-1] == 0xF4


@pytest.mark.parametrize(
    ("cmd", "expected"),
    [
        (0x01, "01 fe"),
        (0x02, "02 fd"),
        (0x06, "06 01 f8"),
        (0x08, "08 01 f6"),
        (0x0E, "0e 01 f0"),
        (0x12, "12 01 ec"),
        (0x16, "16 01 00 e8"),
        (0x1B, "1b 01 00 00 00 e3"),
    ],
)
def test_kanonik_istekler_c_okuyucularla_ayni(cmd: int, expected: str):
    """promos3_view.c'nin urettigi baytlarla birebir (unit 1, station 1)."""
    assert mc.canonical_request(cmd, unit=1).hex(" ") == expected


def test_cevap_saglamasi_istegin_baytlarini_icerir():
    """Komut degisince saglama da degisir — kimliklendirmeyi mumkun kilan sey bu."""
    payload = b"\xe5\x01\x04"
    a = mc.answer_checksum(1, mc.canonical_request(0x06, 1), payload)
    b = mc.answer_checksum(1, mc.canonical_request(0x0E, 1), payload)
    assert a != b


def test_cerceve_sayisi_ve_tel_uzunlugu():
    # 7'nin kati olan yuk, saglama icin AYRI bir cerceve ister.
    assert mc.frame_count(14) == 3
    assert mc.frame_count(0) == 1
    assert mc.frame_count(3) == 1
    # Sira baytlari soyulduktan sonra telde tasinan = yuk + saglama.
    assert mc.total_wire_len(144) == 145


# --------------------------------------------------------------------------
# 3. Kimliklendirme: (uzunluk + saglama) -> komut
# --------------------------------------------------------------------------


def test_kimlik_saglamayla_kanitlanir():
    payload = bytes(range(144))
    ck = mc.answer_checksum(1, mc.canonical_request(0x0E, 1), payload)
    ident = mc.identify(1, payload + bytes([ck]))
    assert ident is not None
    assert ident.cmd == 0x0E
    assert ident.payload == payload


def test_bozuk_saglama_kimlik_URETMEZ():
    """Yanlis etiket vermektense hic etiket vermemek yeglenir."""
    payload = bytes(range(144))
    ck = mc.answer_checksum(1, mc.canonical_request(0x0E, 1), payload) ^ 0xFF
    assert mc.identify(1, payload + bytes([ck])) is None


def test_kimlik_UNITEYE_duyarli():
    """Saglama uniteyi de icerir: 1. unitenin cevabi 2. unitede tutmamali."""
    payload = bytes(range(144))
    ck = mc.answer_checksum(1, mc.canonical_request(0x0E, 1), payload)
    assert mc.identify(1, payload + bytes([ck])) is not None
    assert mc.identify(2, payload + bytes([ck])) is None


def test_satir_kurali_stride_i_VERIDEN_turetir():
    """0x16 blogu kendi kendini tarif eder — yapilandirma beklemez."""
    rows, features = 3, 4
    stride = features * 2 + 2
    payload = bytes([rows]) + bytes(rows * stride)
    ck = mc.answer_checksum(1, mc.canonical_request(0x16, 1), payload)
    ident = mc.identify(1, payload + bytes([ck]))
    assert ident is not None
    assert (ident.cmd, ident.rows, ident.stride, ident.features) == (0x16, rows, stride, features)


def test_cihaz_hatasi_ayri_isaretlenir():
    """[00][01] bozuk veri DEGIL: cihaz "yapamiyorum" diyor."""
    msg = identify_answer(1, b"\x01")
    assert msg.device_error is True
    assert msg.parsed is False


# --------------------------------------------------------------------------
# 4. Yeniden birlestirme: sira takibi ve tamamlanma
# --------------------------------------------------------------------------


def test_tek_cerceveli_cevap():
    reasm = AnswerReassembler()
    got = _feed_all(reasm, frames_for(b"\xe5\x01\x04", unit=1, cmd=0x06))
    assert len(got) == 1
    assert identify_answer(1, got[0].stripped).command == CMD_KONFIG


def test_cok_cerceveli_cevap_sira_baytlari_SOYULUR():
    """Eski hata: data[0] (sira numarasi) yuke karistiriliyordu."""
    payload = bytes(range(144))
    reasm = AnswerReassembler()
    got = _feed_all(reasm, frames_for(payload, unit=1, cmd=0x0E))
    assert len(got) == 1
    assert got[0].stripped[:-1] == payload  # son bayt saglama


def test_dolu_cercevede_biten_cevap_yakalanir():
    """yuk % 7 == 6 iken SON cerceve de doludur; "len < 8 bitirir" bunu kacirirdi."""
    rows, stride = 4, 10
    payload = bytes([rows]) + bytes(rows * stride)  # 41 bayt, 41 % 7 == 6
    assert len(payload) % mc.PAY_PER_FRAME == 6
    recs = frames_for(payload, unit=1, cmd=0x16)
    assert all(rec[0x15] == CAN_MAX_DATA for rec in recs)  # hepsi dolu
    got = _feed_all(AnswerReassembler(), recs)
    assert len(got) == 1
    assert got[0].reason == "rows"
    assert identify_answer(1, got[0].stripped).command == CMD_MERKMALE


def test_sira_atlamasi_mesaji_dusurur_ve_sonraki_seq0_da_senkron_olur():
    reasm = AnswerReassembler()
    recs = frames_for(bytes(range(144)), unit=1, cmd=0x0E)
    broken = recs[:1] + recs[2:]  # 1 numarali cerceve kayip
    assert _feed_all(reasm, broken) == []
    assert reasm.dropped_sequence == 1
    # Bir sonraki cevap sorunsuz cozulur: akis kendini toparlar.
    got = _feed_all(reasm, frames_for(b"\xe5\x01\x04", unit=1, cmd=0x06))
    assert len(got) == 1


def test_mesajin_ortasindan_katilma_oksuz_sayilir():
    reasm = AnswerReassembler()
    recs = frames_for(bytes(range(144)), unit=1, cmd=0x0E)
    assert _feed_all(reasm, recs[3:]) == []  # seq 0 hic gorulmedi
    assert reasm.dropped_orphan > 0


def test_uniteler_tamponlari_karistirmaz():
    reasm = AnswerReassembler()
    a = frames_for(b"\xe5\x01\x04", unit=1, cmd=0x06)
    b = frames_for(b"\xe5\x01\x04", unit=2, cmd=0x06)
    got = _feed_all(reasm, [a[0], b[0]])
    assert sorted(x.unit for x in got) == [1, 2]


def test_taban_alti_can_id_bu_kutunun_trafigi_degil():
    reasm = AnswerReassembler()
    frame = parse_gateway_record(gw_record(0x0100, b"\x00\x01"))
    assert frame is not None
    assert reasm.feed(frame) is None
    assert reasm.dropped_out_of_range == 1


# --------------------------------------------------------------------------
# 5. Govde cozuculeri — GERCEK simulator baytlariyla
# --------------------------------------------------------------------------


def test_yakalamadaki_her_cevap_kimliklendirilir():
    """Belirlenimci yakalama: 2 dongu x 6 komut, kayipsiz."""
    msgs, reasm = decode_cap("sim_stream.cap")
    assert len(msgs) == 12
    assert all(m.parsed for m in msgs)
    assert {m.name for m in msgs} == {
        "MC_GIVEKONFIG",
        "MC_GIVEKANAL",
        "MC_GIVESAMMELMERKMALE",
        "MC_GIVEPLCVALUES",
        "MC_GIVESTATUS",
        "MC_GIVESIGNALVERLAUF",
    }
    assert (reasm.dropped_sequence, reasm.dropped_orphan, reasm.dropped_overflow) == (0, 0, 0)


def test_bozuk_saglamali_yakalama_HICBIR_yanlis_etiket_uretmez():
    msgs, _ = decode_cap("sim_faults.cap")
    assert msgs  # cerceveler birlesti
    assert not any(m.parsed for m in msgs)  # ama hicbiri etiketlenmedi


def test_konfig_govdesi():
    msgs, _ = decode_cap("sim_stream.cap")
    konfig = bodies.decode_konfig(first(msgs, CMD_KONFIG))
    assert konfig is not None
    # Tezgahin log satiri: "Version 229 Channels 1 Sensors 4".
    assert (konfig.version, konfig.channels, konfig.sensors) == (229, 1, 4)


def test_kanal_kaydi_OZELLIK_ADLARINI_telden_verir():
    """Adlar koda gomulu degil: SKanalRec +0x4D yuvalarindan okunur."""
    msgs, _ = decode_cap("sim_stream.cap")
    rec = bodies.decode_kanal(first(msgs, CMD_KANAL))
    assert rec is not None
    used = [s for s in rec.features if s.used]
    assert [s.name for s in used] == ["VIBRATION", "M131 DEBI", "M131BASINC", "M08 DEBI"]
    assert [s.mask for s in used] == [0x01, 0x02, 0x04, 0x08]


def test_merkmale_blogu_satirlari_ve_bayraklari():
    msgs, _ = decode_cap("sim_stream.cap")
    block = bodies.decode_merkmale(first(msgs, CMD_MERKMALE))
    assert block is not None
    assert block.features == 4
    assert block.stride == 4 * 2 + 2
    assert not block.truncated
    for row in block.samples:
        assert len(row.values) == 4
        assert all(0 <= v <= 255 for v in row.values)


def test_status_ve_plc_govdeleri():
    msgs, _ = decode_cap("sim_stream.cap")
    status = bodies.decode_status(first(msgs, CMD_STATUS))
    assert status is not None
    assert status.cycle >= 1
    plc = bodies.decode_plc(first(msgs, CMD_PLCVALUES))
    assert plc is not None
    assert 0 <= plc.inputs <= 0xFF


def test_signalverlauf_125_ornek_verir():
    msgs, _ = decode_cap("sim_stream.cap")
    trace = bodies.decode_signalverlauf(first(msgs, CMD_SIGNALVERLAUF))
    assert trace is not None
    assert len(trace.samples) == bodies.SV_SAMPLES == 125
    assert not trace.truncated
    assert trace.vmin == min(trace.samples)
    assert trace.vmax == max(trace.samples)


def test_rows4_yakalamasi_dolu_cercevede_biten_blogu_cozer():
    """Gercek simulator ciktisiyla dolu-cerceve tamamlanma yolu."""
    msgs, _ = decode_cap("sim_rows4.cap")
    block = bodies.decode_merkmale(first(msgs, CMD_MERKMALE))
    assert block is not None
    assert block.rows == 4


# --------------------------------------------------------------------------
# 6. Guven merdiveni — kimlik KANIT, yerlesim AYRI bir sorudur
# --------------------------------------------------------------------------


def test_saglama_tutsa_bile_yerlesimi_cikarim_olan_komut_dogrulanmis_sayilmaz():
    """Bu testin varlik nedeni:

    Saglama toplami komutun HANGISI oldugunu kanitlar. Ama o komutun
    govdesindeki alanlarin NEREDE durdugu ayri bir bilgi kaynagindan gelir ve
    hepsi ayni olcude dogrulanmis degildir. Simulatorle ayni sonucu vermek
    yerlesimi DOGRULAMAZ — simulator de ayni raporu okuyarak yazildi.

    0x1B ozellikle boyle: promos3_view.c "gercek cozucu Data+0x10'dan okuyor
    olabilir, yani 5 baytlik baslik hic olmayabilir" diyor.
    """
    msgs, _ = decode_cap("sim_stream.cap")
    assert first(msgs, CMD_SIGNALVERLAUF).confidence == Confidence.PROVISIONAL
    assert first(msgs, CMD_STATUS).confidence == Confidence.PROVISIONAL
    assert first(msgs, CMD_KONFIG).confidence == Confidence.PROVISIONAL
    # Buna karsilik ham yakalamayla bayt bayt dogrulanmis olanlar:
    assert first(msgs, CMD_KANAL).confidence == Confidence.CONFIRMED
    assert first(msgs, CMD_MERKMALE).confidence == Confidence.CONFIRMED


def test_kimliksiz_mesaj_ham_baytlari_YUZEYE_CIKARIR():
    msg = identify_answer(1, b"\x00" * 40)
    assert msg.parsed is False
    assert msg.confidence == Confidence.UNKNOWN
    assert msg.raw  # sessizce dusurulmedi


# --------------------------------------------------------------------------
# 7. Ozellik anahtari cozumleme
# --------------------------------------------------------------------------


def test_channel_key_cozumleme_merdiveni():
    """Sirali merdiven: once maske, sonra maske|0x80, en son dogrudan sira."""
    slots = [
        records.FeatureSlot(index=0, mask=0x01, name="VIBRATION"),
        records.FeatureSlot(index=1, mask=0x02, name="M131 DEBI"),
    ]
    assert records.resolve_feature_key(0x02, slots) == (1, "mask")
    assert records.resolve_feature_key(0x82, slots) == (1, "mask|0x80")
    assert records.resolve_feature_key(0x40, slots) is None

    # SIRA kurali yalniz maskeler tukendiginde devreye girer. Anahtar 1, ustteki
    # kurulumda hem "maske 0x01" hem "sira 1" olarak okunabilirdi; maske kurali
    # ONCE geldigi icin 0x01 kazanir — bu bilincli bir onceliktir.
    assert records.resolve_feature_key(1, slots) == (0, "mask")

    # Maskelerin kucuk sayilarla cakismadigi bir kurulumda sira kurali gorunur.
    high = [
        records.FeatureSlot(index=0, mask=0x04, name="M131BASINC"),
        records.FeatureSlot(index=1, mask=0x08, name="M08 DEBI"),
    ]
    assert records.resolve_feature_key(1, high) == (1, "index")


def test_yakalama_dosyasi_gercekten_datagram_tasiyor():
    datagrams = read_cap("sim_stream.cap")
    assert datagrams
    assert all(len(d) % GW_RECORD_SIZE == 0 for d in datagrams)
