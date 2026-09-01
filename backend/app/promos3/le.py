"""Kucuk endian okuyucular — Promos3 uygulama yukunun TEK endianlik noktasi.

Rapor 2.1'in en kolay yanlis yapilan bulgusu: TASIMA katmani (CAN) BUYUK
ENDIAN, uygulama yuku (Promos3) KUCUK ENDIAN. Yuk tarafindaki her okuma bu
modulden gecer ki karar tek yerde dursun; buyuk endian olan tek yer
transport.parse_gateway_record'daki CAN-ID'dir ve orada aciklamasiyla
elle yazilir.
"""


def u16(b: bytes, off: int = 0) -> int:
    """Isaretsiz 16 bit, kucuk endian."""
    return int.from_bytes(b[off : off + 2], "little")


def i16(b: bytes, off: int = 0) -> int:
    """Isaretli 16 bit, kucuk endian (genlik ornekleri int16'dir)."""
    return int.from_bytes(b[off : off + 2], "little", signed=True)


def u32(b: bytes, off: int = 0) -> int:
    """Isaretsiz 32 bit, kucuk endian."""
    return int.from_bytes(b[off : off + 4], "little")
