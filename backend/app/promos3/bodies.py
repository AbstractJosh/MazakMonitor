"""Govde cozuculeri — rapor Part 4 + promos3-c/done/promos3_sim.c SECTION 4.

Tum coklu bayt degerler KUCUK ENDIAN (Promos3 uygulama yuku; tasima katmani
buyuk endian'di, bkz. transport). Ofsetler GOVDE BASINA goredir.

Govde = mc.identify'in dogruladigi YUK (saglama bayti HARIC).
"""

from dataclasses import dataclass

from app.promos3.le import i16 as _i16
from app.promos3.le import u16 as _u16
from app.promos3.messages import Promos3Message
from app.promos3.records import ChannelRecord, parse_channel_record

# --- 0x16 MC_GIVESAMMELMERKMALE — canli olcum blogu ----------------------
# Bu kutunun ASIL canli verisi budur: her poll cevabinda birkac olcum satiri,
# her satirda ozellik basina bir (durum, genlik) ikilisi.
#
# Ikilinin SIRASI dogrulanmadi. Rapor hem "lo == 0xFF bir kacistir" hem
# "lo & 0x04 = alarm" diyor; bu ikisi ancak lo DURUM, hi DEGER ise birlikte
# anlamlidir. Simulator de bu sozlesmeyi uygular (MERKMAL_VALUE_IS_HI).
# Tek bir gercek yakalama bunu kesinlestirir; o gun DEGISECEK TEK YER burasi.
MERKMAL_STATUS_FIRST = True

# Durum bayti 0xFF ise satir bir OLCUM DEGIL, bir IMDIR (kacis): deger bayti
# imin kodudur ve IZLEYEN satir imin parametresini tasir.
MARKER_ESCAPE = 0xFF
MARKER_WORKPIECE = 0xFE  # yeni is parcasi kimligi (parametre = kimlik BOYU)
MARKER_NEW_CYCLE = 0x00  # yeni cevrim (parametre = cevrim indeksi)
MARKER_RESET = 0xFB  # ozellik basina sifirlama

# Durum bayti bayraklari.
#
# Rapor bu bitleri "lo" ve "hi" arasinda bolusturuyor gorunse de, besinin ayni
# BAYRAK BAYTINDA durmasi tek tutarli okumadir (promos3_view.c ayni sonuca
# variyor) — ve veriyi ureten kod da 0x04/0x10'u durum baytina yaziyor. Ham
# ikili yine de disari verilir ki gercek yakalama geldiginde karar veriyle
# verilebilsin.
STATUS_TEACH = 0x01
STATUS_ALARM = 0x04
STATUS_FLAG08 = 0x08
STATUS_START_STOP = 0x10
STATUS_TOOL_CHANGE = 0x40

# Satir sonundaki 2 bayt raporda hicbir yerde tanimli degil; oldugu gibi
# tasinir ("bilinmeyen" olarak), anlam UYDURULMAZ.
MERKMAL_TRAILER = 2

# SIGNALVERLAUF ornek sayisi (dongu 0x7d) — rapor 4.1.
# Ornekler HAM SAYIMDIR (0..255) — olcek carpani yok (rapor Part 5); ekranda
# "%" degeri ozelligin limit Level'ina goredir.
SV_SAMPLES = 125

# decodeSignalTrace_B govde uzunluk kapisi: > 0xFB (251) bayt.
SV_MIN_BODY = 0xFB


@dataclass(slots=True)
class MerkmalRow:
    """Tek olcum satiri: ozellik basina (durum, genlik).

    values HAM SAYIMDIR (0..254; 255 kacis degeri olarak ayrilmistir).
    """

    statuses: list[int]
    values: list[int]
    trailer: bytes

    @property
    def alarm(self) -> bool:
        return any(s & STATUS_ALARM for s in self.statuses)

    @property
    def start_stop(self) -> bool:
        return any(s & STATUS_START_STOP for s in self.statuses)

    @property
    def teach(self) -> bool:
        return any(s & STATUS_TEACH for s in self.statuses)

    @property
    def tool_change(self) -> bool:
        return any(s & STATUS_TOOL_CHANGE for s in self.statuses)


@dataclass(slots=True)
class MerkmalMarker:
    """Olcum akisina gomulu im (kacis satiri) ve parametresi."""

    row: int
    code: int
    param: int | None = None

    @property
    def is_workpiece(self) -> bool:
        """Yeni is parcasi. DIKKAT: parametre kimligin KENDISI degil, BOYUDUR
        ([WorkpieceID] IDsize) — sayaci artiran olay budur, deger degil.
        """
        return self.code == MARKER_WORKPIECE

    @property
    def is_new_cycle(self) -> bool:
        return self.code == MARKER_NEW_CYCLE

    @property
    def is_reset(self) -> bool:
        return self.code == MARKER_RESET


@dataclass(slots=True)
class MerkmalBlock:
    """0x16 cevabinin tamami: satir sayisi, ozellik sayisi ve satirlar."""

    rows: int
    stride: int
    features: int
    samples: list[MerkmalRow]
    markers: list[MerkmalMarker]
    truncated: bool


def decode_merkmale(msg: Promos3Message) -> MerkmalBlock | None:
    """Canli olcum blogunu cozer (cmd 0x16).

    Govde: [satir sayisi] sonra satir basina
    [ozellik x (durum, deger)][2 bayt bilinmeyen kuyruk].

    rows/stride/features mc.identify tarafindan VERIDEN turetilmistir
    (yapilandirmadan beklenmez); burada yalnizca satirlar okunur.
    """
    b = msg.body
    if not b or msg.stride is None or msg.features is None:
        return None
    rows = b[0]
    stride, features = msg.stride, msg.features
    if rows < 1 or features < 1:
        return None

    samples: list[MerkmalRow] = []
    markers: list[MerkmalMarker] = []
    truncated = False
    # Bir imi izleyen satir onun PARAMETRESIDIR; olcum sayilmaz.
    pending: MerkmalMarker | None = None

    for r in range(rows):
        off = 1 + r * stride
        if off + stride > len(b):
            truncated = True
            break

        statuses: list[int] = []
        values: list[int] = []
        for f in range(features):
            p = off + f * 2
            first, second = b[p], b[p + 1]
            status, value = (first, second) if MERKMAL_STATUS_FIRST else (second, first)
            statuses.append(status)
            values.append(value)

        if pending is not None:
            # Im parametresi: durum bayti parametreyi tasir (deger 0'dir).
            pending.param = statuses[0]
            pending = None
            continue

        if statuses[0] == MARKER_ESCAPE:
            pending = MerkmalMarker(row=r, code=values[0])
            markers.append(pending)
            continue

        samples.append(
            MerkmalRow(
                statuses=statuses,
                values=values,
                trailer=bytes(b[off + features * 2 : off + stride]),
            )
        )

    return MerkmalBlock(
        rows=rows,
        stride=stride,
        features=features,
        samples=samples,
        markers=markers,
        truncated=truncated,
    )


@dataclass(slots=True)
class SignalTrace:
    """Canli genlik izi — cizilen degerler (rapor 4.1).

    samples HAM sayimlardir (0..255); olcekleme YOKTUR. Bu iz yalniz TEL
    uzerinde vardir (DB yalnizca zarflanmis gecmisi tutar, rapor Part 10) —
    yani gercek zamanli dalga formunun tek kaynagi budur.
    """

    tool_key: int
    channel_key: int
    param_a: int
    flag: int
    mode: int
    # Ornekler ve sinirlari TEK SEFERDE kurulur (sonradan doldurulmaz): vmin/vmax
    # ile samples'in birbirinden kaymasi boylece yapisal olarak imkansiz olur.
    samples: list[int]
    vmin: int
    vmax: int
    # Govde beklenen uzunluga ulasmadiysa (kisa/kirpik cerceve) isaretlenir:
    # veri gosterilir ama "tam olmayan iz" oldugu bilinir.
    truncated: bool


def decode_signalverlauf(msg: Promos3Message) -> SignalTrace | None:
    """MC_GIVESIGNALVERLAUF govdesini cozer (cmd 0x1B).

    Govde: toolKey, channelKey, paramA, flag, mode, sonra 125 x int16 LE ornek
    ve bir kuyruk etiketi (toplam 257 bayt). mode==1 varyant A'ya
    (decodeSignalTrace_A) gider; ornek yerlesimi ayni oldugu icin ikisini de
    ayni sekilde okuruz, fark mode alaninda gorunur kalir.
    """
    b = msg.body
    if len(b) < 5 + 2:  # en az baslik + tek ornek
        return None

    samples: list[int] = []
    off = 5
    limit = len(b) - 1  # son tek bayt ornek olusturmaz
    while len(samples) < SV_SAMPLES and off < limit:
        samples.append(_i16(b, off))
        off += 2

    if not samples:
        return None

    return SignalTrace(
        tool_key=b[0],
        channel_key=b[1],
        param_a=b[2],
        flag=b[3],
        mode=b[4],
        samples=samples,
        vmin=min(samples),
        vmax=max(samples),
        truncated=len(b) <= SV_MIN_BODY,
    )


@dataclass(slots=True)
class Konfig:
    """MC_GIVEKONFIG ozeti — cihaz yapilandirmasi (rapor 3.1).

    Log satiri "Version 229 Channels 1 Sensors 4" basar; govde tam olarak bu
    ucludur (3 bayt).
    """

    version: int
    channels: int
    sensors: int


def decode_konfig(msg: Promos3Message) -> Konfig | None:
    """KONFIG ozetini cozer: [surum][kanal][sensor], her biri tek bayt.

    (Onceki surum surumu u16 okuyup 4 bayt bekliyordu — govde 3 bayttir ve
    okuma bir bayt kayardi.)
    """
    b = msg.body
    if len(b) < 3:
        return None
    return Konfig(version=b[0], channels=b[1], sensors=b[2])


@dataclass(slots=True)
class Status:
    """MC_GIVESTATUS ozeti (cmd 0x01) — yerlesim CIKARIMDIR.

    Simulator: [alarm bayragi][cevrim][is parcasi kimligi u16 LE].
    """

    alarm: bool
    cycle: int
    workpiece: int


def decode_status(msg: Promos3Message) -> Status | None:
    b = msg.body
    if len(b) < 4:
        return None
    return Status(alarm=bool(b[0]), cycle=b[1], workpiece=_u16(b, 2))


@dataclass(slots=True)
class PlcValues:
    """MC_GIVEPLCVALUES (cmd 0x08) — giris/cikis bit haritalari."""

    inputs: int
    outputs: int


def decode_plc(msg: Promos3Message) -> PlcValues | None:
    b = msg.body
    if len(b) < 2:
        return None
    return PlcValues(inputs=b[0], outputs=b[1])


@dataclass(slots=True)
class GType:
    """MC_GIVEGTYPE (cmd 0x02) — cihaz kimligi; boyut tablosu catismali."""

    g_type: int
    g_sub_type: int
    channels: int
    sensors: int
    serial: int
    version: int


def decode_gtype(msg: Promos3Message) -> GType | None:
    b = msg.body
    if len(b) < 7:
        return None
    return GType(
        g_type=b[0],
        g_sub_type=b[1],
        channels=b[2],
        sensors=b[3],
        serial=_u16(b, 4),
        version=b[6],
    )


def decode_kanal(msg: Promos3Message) -> ChannelRecord | None:
    """MC_GIVEKANAL (cmd 0x0E) — SKanalRecV40, 144 bayt. ✅ DOGRULANMIS.

    OZELLIK ADLARI BURADAN GELIR (+0x4D'de 4 yuva). Yani adlar artik TELDEN
    okunur; yapilandirmadaki PROMOS3_FEATURE_NAMES yalnizca yedektir.
    """
    return parse_channel_record(msg.body)


@dataclass(slots=True)
class AlarmRecord:
    """MC_GIVEALARM (cmd 0x12) — 34 bayt; yerlesim CIKARIMDIR.

    Simulator: [alt komut][etkin][.][alarm no][.][cevrim] ... [+0x21 kanal].
    Bu komut poll dongusunde YOKTUR (yalniz istek uzerine gelir), bu yuzden
    salt-dinleyici kipte pratikte gorulmez.
    """

    sub_command: int
    active: bool
    alarm_number: int
    cycle: int
    channel_key: int


def decode_alarm(msg: Promos3Message) -> AlarmRecord | None:
    b = msg.body
    if len(b) < 0x22:
        return None
    return AlarmRecord(
        sub_command=b[0x00],
        active=bool(b[0x01]),
        alarm_number=b[0x03],
        cycle=b[0x05],
        channel_key=b[0x21],
    )
