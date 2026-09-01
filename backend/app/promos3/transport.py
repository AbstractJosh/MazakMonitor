"""Tasima katmani — UDP datagramini 36 baytlik CAN kayitlarina boler, uniteye
yonlendirir, unite basina MC_ cevabini yeniden birlestirir.

Kaynak: rapor Part 2 + 8.1/8.2 + 9.1 ve promos3-c/done/promos3_sim.c SECTION 2.

KAYIT AYRISTIRMA ve CAN-ID/unite yonlendirmesi tam bilinir (Scan4CANmsg ile
birebir). YENIDEN BIRLESTIRME artik tahmin degildir: MC_ cerceve bicimi
[seq][en fazla 7 yuk bayti] olarak bilinir ve mesaj sonu, saglama toplamiyla
KANITLANARAK belirlenir (bkz. mc.identify).
"""

from dataclasses import dataclass, field

from app.promos3 import mc

# PROVISsettings.ini [CAN] degerleri.
# (Dinlenecek port config.promos3_port'tan gelir — burada ikinci bir
# varsayilan tutmak iki degerin sessizce ayrismasi olurdu.)
BASE_CAN_ID = 1280  # BaseCanIDTransfer
GW_RECORD_SIZE = 0x24  # 36 bayt: bir gateway CAN kaydi
CAN_MAX_DATA = mc.CAN_MAX_DATA

# Yeniden birlestirmede tek mesaj icin ust sinir. En buyuk bilinen govde
# SIGNALVERLAUF (257 bayt); 4096 bol bir tavan. Asilirsa mesaj bozuktur
# (kayip cerceve, bozuk sira) — buyumeye devam etmek yerine dusurulur.
REASM_MAX_MSG = 4096

# FirstDevice..LastDevice = 1..15 (PROVISsettings.ini); 0 dahil 16 yuva.
MAX_UNITS = 16


@dataclass(slots=True)
class CanFrame:
    """36 baytlik gateway kaydinin cozulmus hali (PEAK TPCANMsg esdegeri)."""

    can_id: int
    length: int
    data: bytes
    # unit = can_id - BASE_CAN_ID; taban altindaki ID'ler icin NEGATIF olabilir
    # (bu kutunun trafigi degildir, cagiran dusurur).
    unit: int


@dataclass(slots=True)
class RawAnswer:
    """Tamamlanmis MC_ cevabi: sira baytlari SOYULMUS akis (yuk + saglama).

    Kimliklendirme (hangi komut) mc.identify'in isidir; burada yalniz cerceve
    birlestirme yapilir.
    """

    unit: int
    stripped: bytes
    frames: int
    # Tamamlanma nasil karara baglandi — teshis icin.
    #   "short"    : kisa cerceve (len < 8) mesaji bitirdi
    #   "rows"     : dolu cerceveydi ama satir kurali + saglama tamamlandi dedi
    reason: str = "short"


def parse_gateway_record(rec: bytes) -> CanFrame | None:
    """Tek 36 baytlik kaydi CAN cercevesine cevirir (rapor 2.2).

    Yerlesim: +0x15 len, +0x1A..1B CAN-ID (BUYUK ENDIAN), +0x1C..23 8 veri bayti.
    Bastaki 0x15 bayt gateway basligidir (zaman damgasi/durum) ve atilir.

    dlc > 8 OLANAKSIZDIR: kayit hizasi kaymis ya da bozuktur. Boyle bir kayit
    DUSURULUR (None), 8'e KIRPILMAZ — kirpmak, cop baytlari gecerli bir dolu
    cerceveymis gibi mesaja enjekte ederdi. Iki C okuyucu da ayni sekilde
    dusurur (gw_read 0 doner).
    """
    if len(rec) < GW_RECORD_SIZE:
        raise ValueError(f"gateway kaydi kisa: {len(rec)} < {GW_RECORD_SIZE}")
    length = rec[0x15]
    if length > CAN_MAX_DATA:
        return None
    can_id = (rec[0x1A] << 8) | rec[0x1B]  # BUYUK ENDIAN — rapor 2.1
    return CanFrame(
        can_id=can_id,
        length=length,
        data=bytes(rec[0x1C : 0x1C + CAN_MAX_DATA]),
        unit=can_id - BASE_CAN_ID,
    )


def split_datagram(datagram: bytes) -> list[CanFrame]:
    """Bir UDP datagramini CAN cercevelerine boler (rapor 9.1 / Scan4CANmsg).

    Uygulamanin kendisi artan baytlari BASTAN atar (`remove(0, size % 0x24)`);
    ayni davranis birebir korunur — hizalamayi kaydirmak tum kaydi bozar.
    (Bu ayni zamanda simulatorun `--fault junk=N` onekini de dogru yutar:
    N <= 35 iken len % 36 tam olarak o onektir.)
    36 bayttan kisa datagram tumuyle yok sayilir.
    """
    if len(datagram) < GW_RECORD_SIZE:
        return []
    start = len(datagram) % GW_RECORD_SIZE  # bastan kirp (uygulama ile ayni)
    frames: list[CanFrame] = []
    for off in range(start, len(datagram) - GW_RECORD_SIZE + 1, GW_RECORD_SIZE):
        frame = parse_gateway_record(datagram[off : off + GW_RECORD_SIZE])
        if frame is not None:  # dlc > 8: bozuk kayit, sessizce atlanir
            frames.append(frame)
    return frames


@dataclass(slots=True)
class _UnitBuffer:
    buf: bytearray = field(default_factory=bytearray)
    active: bool = False
    frames: int = 0
    # Beklenen sonraki sira numarasi (mod 256). -1 = mesaj yok.
    next_seq: int = -1


class AnswerReassembler:
    """Unite basina MC_ cerceverini birlestirir; cevap tamamlaninca dondurur.

    CERCEVE BICIMI (promos3_sim.c mc_frame_answer):
        cerceve k : [seq=k][en fazla 7 yuk bayti]
      - Saglama bayti, SIGDIYSE son yuk baytindan hemen sonra gelir.
      - Son yuk cercevesi tam doluysa (n %% 7 == 0) saglama KENDI cercevesini
        alir: [seq][ck], len 2. Bu ayni zamanda "yuksuz onay" halidir.

    TAMAMLANMA. Ara cerceveler HER ZAMAN len 8'dir, bu yuzden:
      - len < 8 gelen cerceve mesaji KESIN bitirir.
      - len == 8 gelen cerceve genellikle aradadir. TEK istisna: yuk uzunlugu
        n %% 7 == 6 oldugunda son cerceve de doludur (6 yuk + saglama = 8).
        Sabit boyutlu komutlarin hicbiri bu duruma dusmez (2/3/4/14/34/144/257
        icin son cerceve daima kisadir); yalniz satir kuralli 0x16 belirli
        satir sayilarinda (rows %% 7 == 4 gibi) buraya duser. O yuzden dolu
        cercevede yalnizca satir kurali sinanir ve karar SAGLAMA TOPLAMIYLA
        verilir — uzunluk tahminiyle degil.

    Eski "len < 8 mesaji bitirir" kurali tek basina bu istisnayi kaciriyordu;
    dahasi sira baytlarini yuke KARISTIRIYORDU (data[0] soyulmuyordu).

    Durum tutar (parcalar cercevelere yayilir), bu yuzden ornek basina birdir.
    """

    def __init__(self, max_units: int = MAX_UNITS) -> None:
        self._units: dict[int, _UnitBuffer] = {}
        self._max_units = max_units
        # Teshis sayaclari — "veri geliyor ama cozulmuyor" ile "veri hic
        # gelmiyor" ayrimini ekranda yapabilmek icin.
        self.dropped_out_of_range = 0
        self.dropped_overflow = 0
        # Sira numarasi beklenenden farkli geldi (kayip/yinelenen/bozuk cerceve).
        self.dropped_sequence = 0
        # Mesajin ortasindan katilindi: seq 0 gorulmeden gelen cerceveler.
        self.dropped_orphan = 0
        # Onceki mesaj bitmeden yeni bir seq 0 geldi (eksik kalan mesaj).
        self.dropped_incomplete = 0

    def _reset(self, u: _UnitBuffer) -> None:
        u.buf.clear()
        u.active = False
        u.frames = 0
        u.next_seq = -1

    def _finish(self, unit: int, u: _UnitBuffer, reason: str) -> RawAnswer:
        answer = RawAnswer(unit=unit, stripped=bytes(u.buf), frames=u.frames, reason=reason)
        self._reset(u)
        return answer

    def feed(self, frame: CanFrame) -> RawAnswer | None:
        """Bir CAN cercevesi isler; cevap tamamlandiysa dondurur."""
        if frame.unit < 0 or frame.unit >= self._max_units:
            # Taban altindaki / yabanci CAN-ID: bu kutunun trafigi degil.
            self.dropped_out_of_range += 1
            return None
        if frame.length < 1:
            # Sira bayti bile yok: tasima duzeyinde bozuk cerceve.
            self.dropped_sequence += 1
            return None

        u = self._units.setdefault(frame.unit, _UnitBuffer())
        seq = frame.data[0]
        part = frame.data[1 : frame.length]

        # Devam mi, yeni mesaj mi? Devam sinamasi ONCE gelir: cok uzun bir
        # cevapta sira numarasi 256'da sarar ve seq 0 mesru bir DEVAM olabilir;
        # "seq 0 her zaman yeni mesajdir" demek onu ikiye bolerdi.
        if u.active and seq == u.next_seq:
            u.next_seq = (u.next_seq + 1) & 0xFF
        elif seq == 0:
            if u.active and u.buf:
                # Onceki mesaj tamamlanmadan yenisi basladi: kayip cerceve.
                self.dropped_incomplete += 1
            self._reset(u)
            u.active = True
            u.next_seq = 1
        elif not u.active:
            # Akisa mesajin ortasindan katildik: seq 0 gorene dek bekle.
            self.dropped_orphan += 1
            return None
        else:
            # Sira atladi/yinelendi (drop / dup / badseq): mesaji dusur, bir
            # sonraki seq 0'da yeniden senkron ol.
            self.dropped_sequence += 1
            self._reset(u)
            return None

        u.buf += part
        u.frames += 1

        if len(u.buf) > REASM_MAX_MSG:
            # Tamamlanma hic gelmedi: sonsuza kadar buyumek yerine tamponu bosalt.
            self.dropped_overflow += 1
            self._reset(u)
            return None

        # --- tamamlanma karari ---
        if frame.length < CAN_MAX_DATA:
            # Kisa cerceve: mesaj KESIN bitti (ara cerceveler hep doludur).
            return self._finish(frame.unit, u, "short")

        # Dolu cerceve: yalnizca satir kuralli blok burada bitebilir ve karar
        # uzunluk tahminiyle degil, SAGLAMA TOPLAMIYLA verilir.
        ident = mc.identify(frame.unit, bytes(u.buf))
        if ident is not None and ident.rule is mc.SizeRule.ROWS:
            return self._finish(frame.unit, u, "rows")

        return None
