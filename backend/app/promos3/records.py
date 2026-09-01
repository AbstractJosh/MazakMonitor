"""Yapilandirma kayitlari (durgun veri) — rapor Part 7.

Bu bolum raporun EN SAGLAM parcasidir: ham PMD hex (1974.txt) ile SQLite
yapilandirma DB'leri kolon kolon karsilastirilarak DOGRULANDI. Asagida yalniz
[VERIFIED] isaretli alanlar cozulur; dogrulanmamis alanlar icin alan
uretilmez (tahmini ofset, dogrulanmis veri gibi gorunmesin).

Ozellik ADLARI buradan gelir ve KURULUMA OZELDIR — koda gomulmez (rapor 7.2).
"""

from dataclasses import dataclass, field

from app.promos3.le import u16 as _u16

# Kayit boyutlari (rapor 7.1-7.3).
DEVICE_REC_SIZE = 66  # SGeraetRec
CHANNEL_REC_SIZE = 144  # SKanalRecV40
LIMIT_REC_SIZE = 14  # SGrenzRec (~14; alan ofsetleri DOGRULANMADI)
CYCLE_REC_SIZE = 170  # SZykRecV4802

# Ozellik adi bloku: +0x4D'de 4 sabit 12 baytlik yuva.
FEATURE_BLOCK_OFF = 0x4D
FEATURE_SLOT_SIZE = 12
FEATURE_SLOTS = 4
FEATURE_NAME_LEN = 11


@dataclass(slots=True)
class FeatureSlot:
    """SKanalRec'teki tek ozellik yuvasi: [1 maske bayti][11 bayt ASCII ad].

    maske: ALT NIBBLE (0x01/0x02/0x04/0x08) ozellik-secme bitidir; 0x80 AYRI
    bir bayraktir (rapor 7.2 duzeltmesi). Bu yuzden `mask == 0x81` gibi
    karsilastirma YAPILMAZ — bit konumu ile eslesilir.
    """

    index: int  # yuva sirasi (0..3)
    mask: int  # ham maske bayti
    name: str  # operatorun verdigi ad (orn. "M131 DEBI")

    @property
    def select_bit(self) -> int:
        """Ozellik-secme biti (maskenin alt nibble'i)."""
        return self.mask & 0x0F

    @property
    def flag(self) -> bool:
        """Maskedeki 0x80 bayragi (anlami ayri; ad/secim ile ilgisiz)."""
        return bool(self.mask & 0x80)

    @property
    def used(self) -> bool:
        """Yuva dolu mu: adi ve secme biti olan yuva gercek bir ozelliktir."""
        return bool(self.name) and self.select_bit != 0


def _ascii_z(b: bytes) -> str:
    """NUL ile sonlanan ASCII adi cozer; bozuk bayt varsa atlanir."""
    raw = b.split(b"\x00", 1)[0]
    return raw.decode("ascii", errors="ignore").strip()


def parse_feature_slots(channel_rec: bytes) -> list[FeatureSlot]:
    """SKanalRec'ten ozellik yuvalarini okur (rapor 7.2/9.7) — ✅ DOGRULANMIS.

    Bu kurulumda: 0x01 "VIBRATION", 0x02 "M131 DEBI", 0x04 "M131BASINC",
    0x08 "M08 DEBI". BASKA TEZGAHTA FARKLIDIR — bu yuzden okunur, gomulmez.
    """
    slots: list[FeatureSlot] = []
    for i in range(FEATURE_SLOTS):
        off = FEATURE_BLOCK_OFF + i * FEATURE_SLOT_SIZE
        if off + FEATURE_SLOT_SIZE > len(channel_rec):
            break
        slots.append(
            FeatureSlot(
                index=i,
                mask=channel_rec[off],
                name=_ascii_z(channel_rec[off + 1 : off + 1 + FEATURE_NAME_LEN]),
            )
        )
    return slots


def resolve_feature_key(key: int, slots: list[FeatureSlot]) -> tuple[int, str] | None:
    """SIGNALVERLAUF channelKey'ini bir ozellik yuvasina baglar.

    Rapor channelKey ile SKanalRec maske bitleri arasindaki karsiligi ACIKCA
    KURMUYOR, bu yuzden burada tek bir esleme UYDURULMAZ; promos3_view.c ile
    ayni SIRALI merdiven denenir ve HANGI kuralin tuttugu geri verilir:

        1. "mask"        : maske bayti birebir esit
        2. "mask|0x80"   : maske 0x80 bayragiyla birlikte gelmis
        3. "index"       : anahtar dogrudan yuva sirasi (0..n-1)

    Hicbiri tutmazsa None — ekran o zaman anahtarin kendisini gosterir.
    Yanlis ada sahip bir grafik, adsiz grafikten kotudur.
    """
    used = [s for s in slots if s.used]
    for slot in used:
        if slot.mask == key:
            return slot.index, "mask"
    for slot in used:
        if (slot.mask | 0x80) == key:
            return slot.index, "mask|0x80"
    if 0 <= key < len(used):
        return used[key].index, "index"
    return None


@dataclass(slots=True)
class DeviceRecord:
    """SGeraetRec — cihaz kaydi (66 bayt), tablo: Devices. ✅ DOGRULANMIS."""

    g_type: int  # +0x00 (bu kutu 0x44)
    g_sub_type: int  # +0x01 (5)
    channel_amount: int  # +0x02 (1)
    mi_sens_amount: int  # +0x03 (4)
    mi_sens_types: list[int] = field(default_factory=list)  # +0x1A..0x21 (0x80 x4)
    sample_div: int = 0  # +0x22 (1)
    reduz_lim: int = 0  # +0x26 u16 LE (6612)


def parse_device_record(b: bytes) -> DeviceRecord | None:
    """SGeraetRec'i cozer. Yalniz dogrulanmis alanlar (rapor 7.1)."""
    if len(b) < 0x28:  # ReduzLim sonuna kadar gerekli
        return None
    return DeviceRecord(
        g_type=b[0x00],
        g_sub_type=b[0x01],
        channel_amount=b[0x02],
        mi_sens_amount=b[0x03],
        mi_sens_types=list(b[0x1A:0x22]),
        sample_div=b[0x22],
        reduz_lim=_u16(b, 0x26),
    )


@dataclass(slots=True)
class ChannelRecord:
    """SKanalRecV40 — kanal kaydi (144 bayt), tablo: Channels. ✅ DOGRULANMIS."""

    plc_type: int  # +0x00 (0x10)
    plc_version: int  # +0x01 (0x20)
    channel_num: int  # +0x02 (1)
    cdr_lim: list[int] = field(default_factory=list)  # +0x10..0x13 (0xAA x4)
    features: list[FeatureSlot] = field(default_factory=list)  # +0x4D


def parse_channel_record(b: bytes) -> ChannelRecord | None:
    """SKanalRec'i cozer (rapor 7.2)."""
    if len(b) < FEATURE_BLOCK_OFF:
        return None
    return ChannelRecord(
        plc_type=b[0x00],
        plc_version=b[0x01],
        channel_num=b[0x02],
        cdr_lim=list(b[0x10:0x14]),
        features=parse_feature_slots(b),
    )


# --- SGrenzRec (limitler) -------------------------------------------------
# BILINCLI OLARAK ALAN COZUCUSU YOK.
#
# Rapor bu kaydin tablo Limits'e (Limtype, Level, Feat_Num, Response_Time,
# Act_Start, Act_End, Act_Mode, Pattern_Ref) karsilik geldigini ve gorulen
# Level degerlerini (20/35/50/70/115/140/152/170) veriyor, AMA alanlarin bayt
# OFSETLERINI vermiyor. Ofset uydurup "Level" diye sunmak, ekranda dogrulanmis
# bir esik gibi gorunurdu — genlik "%"si buna bolundugu icin sessizce yanlis
# yuzde uretirdi.
#
# Limitler bu yuzden yalniz GUVENILIR bir kaynaktan gelir: yapilandirma
# SQLite'i ya da kalibrasyondan sonra LIMIT_INFO govdesi. O kaynak baglanana
# dek domain.Feature.limit_level BOS kalir ve yuzde HESAPLANMAZ.
