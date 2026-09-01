"""Cevaptan mesaja — kimliklendirme ve GUVEN MERDIVENI.

Kaynak: rapor Part 3 (dagitim haritasi) + promos3-c/done/promos3_view.c.

Buradaki en onemli fikir guven merdivenidir: bir komutun bayt yerlesimini
GERCEKTEN bilmiyorsak, cozulmus "anlam" uretmeyiz — ekran ham baytlari
gosterir. Boylece tahmin edilmis bir ofset asla dogrulanmis veri gibi gorunmez.

ONEMLI AYRIM — iki ayri soru vardir:

  1. "Bu cevap hangi komuta ait?"  Artik KANITLANIR: saglama toplami istegin
     baytlarini icerdigi icin tutan bir saglama komutu dogrular (mc.identify).
     Eskiden bu bir baslik TAHMINIYDI ([group][command][len] onegi) ve telde
     boyle bir onek YOKTU.
  2. "Bu komutun govdesinde alanlar nerede?"  Bu ayri bir bilgi kaynagindan
     gelir ve komuttan komuta degisir (mc.Layout).

Guven, ikisinin BIRLESIMIDIR: saglama tutmuyorsa komut bilinmez (UNKNOWN);
tutuyorsa govde yerlesiminin dogrulanmisligi belirler.
"""

from dataclasses import dataclass
from enum import IntEnum, StrEnum

from app.promos3 import mc


class Group(IntEnum):
    """Dagitim grubu. Bu kutu MC (1) konusur — tel uzerinde grup BAYTI YOKTUR;
    kutunun neslinden bilinir (rapor: getTargetType, MC_ = Provis2 nesli).
    """

    HANDSHAKE = 0
    MC = 1  # legacy Provis2 — BU KUTU
    MC3 = 2  # modern Promos3


class Confidence(StrEnum):
    """Bir komutun alan yerlesimine ne kadar guvendigimiz.

    Ekranin cozulmus deger mi yoksa ham hex mi gosterecegini bu belirler.
    """

    UNKNOWN = "unknown"  # kimlik yok (saglama tutmadi)  -> ham hex
    NAMED = "named"  # ad var, cozucu yok            -> ad + hex
    PROVISIONAL = "provisional"  # cozucu var, yerlesim cikarim  -> ad + hex
    CONFIRMED = "confirmed"  # cozucu + yerlesim dogrulandi  -> cozulmus deger


# Komut numarasi kisayollari (live.py dagitiminda okunurluk icin).
CMD_STATUS = 0x01
CMD_GTYPE = 0x02
CMD_KONFIG = 0x06
CMD_PLCVALUES = 0x08
CMD_KANAL = 0x0E
CMD_ALARM = 0x12
CMD_MERKMALE = 0x16
CMD_SIGNALVERLAUF = 0x1B


def cmd_name(command: int | None) -> str | None:
    """Komutun okunur adi; bilinmeyen komut numarasiyla gorunur."""
    return mc.cmd_name(command)


def _layout_confidence(layout: mc.Layout) -> Confidence:
    """Govde yerlesiminin dogrulanmisligini guven duzeyine cevirir."""
    if layout is mc.Layout.VERIFIED:
        return Confidence.CONFIRMED
    # TABLE ve ASSUMED: deger uretilir ama ON GORUNUMDUR.
    return Confidence.PROVISIONAL


@dataclass(slots=True)
class Promos3Message:
    """Kimliklendirilmis (ya da edilememis) bir MC_ cevabi.

    `raw` HER ZAMAN gecerlidir: kimlik cikmazsa mesaj SESSIZCE DUSURULMEZ,
    cagiran ham baytlari yuzeye cikarir (teshisin tek ipucu bunlardir).
    """

    unit: int
    raw: bytes  # sira baytlari soyulmus akis (yuk + saglama)
    parsed: bool = False
    group: int | None = None
    command: int | None = None
    body: bytes = b""  # yuk (saglama HARIC)
    checksum: int | None = None
    checksum_ok: bool = False
    # Cihaz "yapamiyorum" cevabi verdi ([00][01]) — bozuk veri DEGIL.
    device_error: bool = False
    # Yalniz satir kuralli blokta (0x16) dolar; veriden TURETILIR.
    rows: int | None = None
    stride: int | None = None
    features: int | None = None
    frames: int = 0
    layout: mc.Layout | None = None

    @property
    def name(self) -> str | None:
        return cmd_name(self.command)

    @property
    def confidence(self) -> Confidence:
        if not self.checksum_ok or self.layout is None:
            return Confidence.UNKNOWN
        return _layout_confidence(self.layout)


def identify_answer(
    unit: int, stripped: bytes, frames: int = 0, prefer: int | None = None
) -> Promos3Message:
    """Birlestirilmis bir cevabi mesaja cevirir.

    Kimlik, (yuk uzunlugu + saglama toplami) ikilisinden KANITLANARAK bulunur
    — poll dongusundeki konuma guvenilmez, cunku dinleyici akisa ortadan
    katilmis olabilir. `prefer` yalnizca ender bir esitlikte ipucudur.
    """
    msg = Promos3Message(unit=unit, raw=stripped, frames=frames)

    if mc.is_device_error(stripped):
        # Cihaz komutu yerine getiremedi. Bu bir COZME HATASI DEGILDIR;
        # ayri isaretlenir ki teshiste "bozuk tel" ile karistirilmasin.
        msg.device_error = True
        msg.group = Group.MC
        return msg

    ident = mc.identify(unit, stripped, prefer=prefer)
    if ident is None:
        return msg

    msg.parsed = True
    msg.checksum_ok = True
    msg.group = Group.MC
    msg.command = ident.cmd
    msg.body = ident.payload
    msg.checksum = ident.checksum
    msg.rows = ident.rows
    msg.stride = ident.stride
    msg.features = ident.features
    msg.layout = ident.layout
    return msg
