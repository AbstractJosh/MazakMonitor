"""Simulator yakalama dosyasi (.cap) okuyucu — testlerin GERCEK tel kaynagi.

Bicim (promos3_sim.c SECTION 6):
    "P3CAP1\\0\\0" sonra tekrarlayan [u32 le t_ms][u32 le uzunluk][uzunluk bayt]

NEDEN ONEMLI: bu dosyalar elle yazilmadi, promos3-c/done/promos3_sim.exe
tarafindan uretildi. Testler boylece BIZIM varsayimlarimizi degil, bagimsiz
bir kodlayicinin urettigi baytlari cozer. (Eski backend/tools/mock_gateway.py
tam tersini yapiyordu: cozucunun bekledigi bicimi URETIYORDU, yani "N cozuldu"
sonucu dairesel bir kanittti.)

Yeniden uretmek icin (belirlenimci — --seed sabit):
    promos3_sim.exe --out tests/data/sim_stream.cap --stream 127.0.0.1:9 \\
        --cycles 2 --rows 3 --seed 7 --quiet
"""

import struct
from pathlib import Path

from app.live import apply_promos3_message, initial_live_state
from app.domain import LiveState
from app.promos3.messages import Promos3Message, identify_answer
from app.promos3.transport import AnswerReassembler, split_datagram

CAP_MAGIC = b"P3CAP1\x00\x00"
DATA_DIR = Path(__file__).parent / "data"


def read_cap(name: str) -> list[bytes]:
    """Yakalama dosyasindaki UDP datagramlarini sirayla dondurur."""
    raw = (DATA_DIR / name).read_bytes()
    if raw[:8] != CAP_MAGIC:
        raise ValueError(f"{name}: P3CAP1 imzasi yok")
    out: list[bytes] = []
    off = 8
    while off + 8 <= len(raw):
        _t, size = struct.unpack_from("<II", raw, off)
        off += 8
        out.append(raw[off : off + size])
        off += size
    return out


def decode_cap(name: str) -> tuple[list[Promos3Message], AnswerReassembler]:
    """Yakalamayi mesajlara cozer (tasima + kimliklendirme)."""
    reasm = AnswerReassembler()
    msgs: list[Promos3Message] = []
    for datagram in read_cap(name):
        for frame in split_datagram(datagram):
            answer = reasm.feed(frame)
            if answer is not None:
                msgs.append(identify_answer(answer.unit, answer.stripped, frames=answer.frames))
    return msgs, reasm


def replay_cap(name: str, time_iso: str = "2026-08-03T10:00:00+00:00") -> LiveState:
    """Yakalamayi bastan sona canli duruma isler."""
    state = initial_live_state()
    msgs, _ = decode_cap(name)
    for msg in msgs:
        state = apply_promos3_message(state, msg, time_iso)
    return state


def first(msgs: list[Promos3Message], command: int) -> Promos3Message:
    """Yakalamadaki ilk <command> mesaji (yoksa AssertionError)."""
    for msg in msgs:
        if msg.command == command:
            return msg
    raise AssertionError(f"yakalamada 0x{command:02X} yok")
