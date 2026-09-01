"""MC_ cevap kodegi — komut tablosu, kanonik istek, saglama toplami, KIMLIKLENDIRME.

Kaynak: promos3-c/done/promos3_sim.c ve promos3_view.c (SECTION 2/3). Bu modul
o iki programla BAYT BAYT AYNI olmak zorundadir; ayrisirsa cozme sessizce
bozulur.

NEDEN BU KATMAN VAR — telin en can alici ozelligi:

    Bir MC_ CEVABI TEL UZERINDE ANONIMDIR. Ne grup, ne komut, ne uzunluk
    tasir; yalnizca [seq][7 yuk bayti] cerceveleri ve sonda tek bir saglama
    baytidir. Cevabi "hangi komuta ait" diye taniyabilen tek taraf, istegi
    GONDEREN taraftir.

Backend ise SALT DINLEYICIDIR (ADR-0004): istegi o gondermez. Eski cozum
telin basinda [group][command][len] diye bir onek oldugunu VARSAYIYORDU; boyle
bir onek yok. O varsayim yalniz backend/tools/mock_gateway.py ile "calisiyor"
gorunuyordu, cunku o arac ayni varsayimi URETIYORDU — daire.

Buradaki cikis yolu daireyi kirar:

  1. Istek KANONIKTIR. Poll dongusu bir komut icin hep ayni baytlari gonderir
     ([cmd][station][0 dolgu][ck]), yani dinleyici de onu YENIDEN URETEBILIR.
  2. Saglama toplami ISTEGIN baytlarini icerir:
         ck = -(unit + SUM(istek, kendi ck'si haric) + SUM(cevap yuku))
     Her komutun istek bayt toplami farklidir (0x01->1, 0x06->7, 0x08->9,
     0x0e->15, 0x16->23, 0x1b->28), dolayisiyla saglama komuta gore DEGISIR.
  3. Beklenen yuk uzunluklari da birbirinden ayriktir (2/3/4/14/34/144/257 ve
     0x16 icin satir kurali).

Sonuc: (yuk uzunlugu + saglama toplami) ikilisi komutu GERI VERIR. Saglama
tuttugunda bu bir TAHMIN DEGIL, DOGRULAMADIR — hem komut kimligi hem veri
butunlugu ayni anda kanitlanir. Dinleyici akisa ortadan katilsa bile dogru
etiketler; poll dongusundeki konuma guvenmek zorunda kalmaz.
"""

from dataclasses import dataclass
from enum import IntEnum

# --- Tel sabitleri (promos3_sim.c SECTION 2 ile ayni) --------------------
CAN_MAX_DATA = 8
# DATA[0] sira numarasi tasir; kalan 7 bayt yuktur.
PAY_PER_FRAME = 7

# Cihaz hata cercevesi: [seq=0][0x01], len 2 (promos3_sim.c faults_apply).
DEVICE_ERROR_BYTE = 0x01

# Poll dongusunun station parametresi. Sim ve view ayni degeri kullanir
# (mc_canonical_request cagrilari station=1 ile yapilir).
DEFAULT_STATION = 1


class SizeRule(IntEnum):
    """Cevap yukunun uzunlugu nasil belirlenir."""

    FIXED = 0  # sabit bayt sayisi
    ROWS = 1  # satir kurali: rows*stride + 1 (ilk bayt satir sayisi)


class Layout(IntEnum):
    """GOVDE YERLESIMINE ne kadar guvenilir.

    DIKKAT — bu, komut KIMLIGINDEN ayri bir sorudur. Saglama toplami tuttugunda
    komutun hangisi oldugu KANITLIDIR; ama o komutun govdesindeki alanlarin
    nerede durdugu ayri bir bilgi kaynagindan gelir ve hepsi ayni olcude
    dogrulanmis degildir.
    """

    ASSUMED = 0  # yerlesim cikarim; deger uretilir ama ON GORUNUMDUR
    TABLE = 1  # boyut tablosundan; catisma bilinir
    VERIFIED = 2  # ham yakalama/PMD ile bayt bayt dogrulandi


@dataclass(frozen=True, slots=True)
class CmdDesc:
    cmd: int
    name: str
    # [cmd][params..][ck] — istegin TEL uzerindeki toplam bayt sayisi.
    req_len: int
    rule: SizeRule
    # rule FIXED iken beklenen cevap yuku uzunlugu; ROWS iken kullanilmaz.
    size: int
    layout: Layout
    note: str


# MC_ kutusunun salt-okunur komut kumesi. req_len 0x08 icin uygulamanin kendi
# log satirindan BAYT DOGRULANMISTIR: "requested 0x08, 0x01, 0xf6".
CMD_TAB: dict[int, CmdDesc] = {
    0x01: CmdDesc(
        0x01, "MC_GIVESTATUS", 2, SizeRule.FIXED, 4, Layout.ASSUMED,
        "gonderen setRecvSize cagirmiyor; boyut tahmin",
    ),
    0x02: CmdDesc(
        0x02, "MC_GIVEGTYPE", 2, SizeRule.FIXED, 14, Layout.TABLE,
        "boyut tablosu 14 diyor ama SGrenzRec olarak etiketliyor — bilinen catisma",
    ),
    0x06: CmdDesc(
        0x06, "MC_GIVEKONFIG", 3, SizeRule.FIXED, 3, Layout.ASSUMED,
        "govde E5 01 04 = surum / kanal / sensor (log satiriyla capalandi)",
    ),
    0x08: CmdDesc(
        0x08, "MC_GIVEPLCVALUES", 3, SizeRule.FIXED, 2, Layout.ASSUMED,
        "gercek boyut Geraet+0x4e6'dan calisma aninda hesaplaniyor (acik ucu D4)",
    ),
    0x0E: CmdDesc(
        0x0E, "MC_GIVEKANAL", 3, SizeRule.FIXED, 144, Layout.VERIFIED,
        "SKanalRecV40; boyut cagri yerinde dogrulandi, ozellik adlari +0x4D",
    ),
    0x12: CmdDesc(
        0x12, "MC_GIVEALARM", 3, SizeRule.FIXED, 34, Layout.ASSUMED,
        "boyut tablosundaki giris aslinda 0x11 ALARMGESEHEN'e ait",
    ),
    0x16: CmdDesc(
        0x16, "MC_GIVESAMMELMERKMALE", 4, SizeRule.ROWS, 0, Layout.VERIFIED,
        "rows*(features*2+2)+1; ilk yuk bayti satir sayisi — CANLI OLCUM BLOGU",
    ),
    0x1B: CmdDesc(
        0x1B, "MC_GIVESIGNALVERLAUF", 6, SizeRule.FIXED, 257, Layout.ASSUMED,
        "5 baslik + 125*int16 LE + 2 kuyruk; gercek cozucu Data+0x10'dan okuyor "
        "olabilir, yani 5 baytlik baslik hic olmayabilir — ON GORUNUM",
    ),
}

# Poll dongusunun sirasi (promos3_sim.c:917 POLL[] ve promos3_view.c'nin
# varsayilan assume-cycle'i ile AYNI). Kimliklendirme buna BAGLI DEGILDIR;
# yalnizca ender bir esitlikte tercih ipucu olarak kullanilir.
POLL_CYCLE: tuple[int, ...] = (0x06, 0x0E, 0x16, 0x08, 0x01, 0x1B)

# 0x16 satir kurali icin makul stride sinirlari. stride = features*2 + 2, yani
# en az 1 ozellik (4) ve NFEAT_MAX=4'un cok uzerinde bir tavan (32 -> 15 ozellik).
_MIN_STRIDE = 4
_MAX_STRIDE = 32


def cmd_name(cmd: int | None) -> str | None:
    """Komutun okunur adi; bilinmeyen komut numarasiyla gorunur."""
    if cmd is None:
        return None
    desc = CMD_TAB.get(cmd)
    return desc.name if desc else f"MC_0x{cmd:02X}"


def request_checksum(unit: int, msg: bytes) -> int:
    """GONDERILECEK istegin saglama toplami (kendi ck'si haric butun baytlar)."""
    return (-(unit + sum(msg))) & 0xFF


def canonical_request(cmd: int, unit: int, station: int = DEFAULT_STATION) -> bytes:
    """Poll dongusunun bu komut icin urettigi ISTEK baytlari.

    promos3_sim.c mc_canonical_request ile birebir: [cmd], (req_len > 2 ise)
    [station], req_len-1'e kadar sifir dolgu, sonra saglama bayti.

    Dinleyici bu baytlari hic gondermez; cevabin saglamasini DOGRULAYABILMEK
    icin yeniden uretir (bkz. modul basligi).
    """
    desc = CMD_TAB.get(cmd)
    want = desc.req_len if desc else 3
    out = bytearray()
    out.append(cmd & 0xFF)
    if want > 2:
        out.append(station & 0xFF)
    while len(out) < want - 1:
        out.append(0x00)
    out.append(request_checksum(unit, bytes(out)))
    return bytes(out)


def answer_checksum(unit: int, request: bytes, payload: bytes) -> int:
    """Cevabin beklenen saglama toplami.

        ck = -(unit + SUM(istek, kendi ck'si HARIC) + SUM(cevap yuku))

    Bayt dogrulanmis: unit 1, istek {08,01} -> -(1+9) = -10 = 0xF6.
    """
    return (-(unit + sum(request[:-1]) + sum(payload))) & 0xFF


def frame_count(payload_len: int) -> int:
    """Bir yukun kac cerceveye bolunecegi (mc_frame_answer ile ayni).

    Tam dolu son cerceveden sonra saglama kendi cercevesini ister; bu yuzden
    payload_len % 7 == 0 iken bir cerceve daha eklenir (0 uzunluklu cevap dahil).
    """
    n = payload_len
    cnt = (n + PAY_PER_FRAME - 1) // PAY_PER_FRAME
    if n % PAY_PER_FRAME == 0:
        cnt += 1
    return cnt


def total_wire_len(payload_len: int) -> int:
    """Sira baytlari SOYULDUKTAN sonra telde tasinan bayt sayisi = yuk + saglama.

    Cerceve dagilimi ne olursa olsun saglama HER ZAMAN tam bir bayttir, bu
    yuzden bu her durumda payload_len + 1'dir.
    """
    return payload_len + 1


def is_device_error(stripped: bytes) -> bool:
    """Cihaz hata cevabi mi: tek cerceve [00][01] (yuk yok, tek bayt 0x01).

    Sim bunu --fault deverr ile uretir; gercek kutu da komutu yerine
    getiremediginde ayni kisa cevabi verir.
    """
    return len(stripped) == 1 and stripped[0] == DEVICE_ERROR_BYTE


@dataclass(frozen=True, slots=True)
class Identified:
    """Saglamasi TUTAN, yani komutu KANITLANMIS bir cevap."""

    cmd: int
    name: str
    payload: bytes
    checksum: int
    layout: Layout
    rule: SizeRule
    # Yalniz satir kuralinda (0x16) dolar — veriden TURETILIR, varsayilmaz.
    rows: int | None = None
    stride: int | None = None
    features: int | None = None


def _rows_candidate(payload: bytes) -> tuple[int, int, int] | None:
    """0x16 satir kuralini yukun KENDISINDEN cozer: (rows, stride, features).

    n = rows*stride + 1 ve rows yukun ilk baytidir; dolayisiyla stride veriden
    turetilir. Ozellik sayisini yapilandirmadan BEKLEMEK gerekmez — blok kendi
    kendini tarif eder. (Bu onemli: poll dongusunde 0x16, KONFIG'den once
    gelebilir ve dinleyici akisa ortadan katilabilir.)
    """
    n = len(payload)
    if n < 2:
        return None
    rows = payload[0]
    if rows < 1:
        return None
    rest = n - 1
    if rest % rows:
        return None
    stride = rest // rows
    # stride = features*2 + 2 -> cift olmali ve makul araliktA durmali.
    if stride % 2 or not (_MIN_STRIDE <= stride <= _MAX_STRIDE):
        return None
    return rows, stride, (stride - 2) // 2


def identify(
    unit: int, stripped: bytes, prefer: int | None = None, station: int = DEFAULT_STATION
) -> Identified | None:
    """Anonim bir cevabi (uzunluk + saglama) ikilisinden komutuna baglar.

    `stripped`: sira baytlari soyulmus akis — yuk + son bayt saglama.

    Saglamasi tutan her aday toplanir. Beklenen yuk uzunluklari zaten ayrik
    oldugu icin pratikte en fazla bir aday kalir; yine de coklu esitlikte
    `prefer` (poll dongusundeki sirasi) ipucu kullanilir, o da yoksa komut
    numarasi kucuk olan secilir (belirlenimci davranis).

    Hicbir aday tutmuyorsa None doner — mesaj SESSIZCE DUSURULMEZ, cagiran ham
    baytlari yuzeye cikarir.
    """
    if len(stripped) < 1:
        return None
    payload, checksum = stripped[:-1], stripped[-1]

    found: list[Identified] = []
    for desc in CMD_TAB.values():
        rows = stride = features = None
        if desc.rule is SizeRule.FIXED:
            if desc.size != len(payload):
                continue
        else:
            parsed = _rows_candidate(payload)
            if parsed is None:
                continue
            rows, stride, features = parsed

        expected = answer_checksum(unit, canonical_request(desc.cmd, unit, station), payload)
        if expected != checksum:
            continue

        found.append(
            Identified(
                cmd=desc.cmd,
                name=desc.name,
                payload=payload,
                checksum=checksum,
                layout=desc.layout,
                rule=desc.rule,
                rows=rows,
                stride=stride,
                features=features,
            )
        )

    if not found:
        return None
    if len(found) > 1 and prefer is not None:
        for cand in found:
            if cand.cmd == prefer:
                return cand
    return min(found, key=lambda c: c.cmd)
