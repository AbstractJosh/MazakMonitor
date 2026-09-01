"""Alan modeli — Promos3 TELGRAFININ sekli, frontend/src/domain/types.ts ile birebir.

Bu modeller backend <-> frontend arasindaki VERI SOZLESMESIDIR: tel ustunde
camelCase (frontend tipleriyle ayni ad ve bicim), Python tarafinda snake_case.

Model, promos3-c/analysis_jul_28_1_0_0.md'de cozulen GERCEK veriye gore
sekillendirilmistir; onceki sekil MazakFolly log tekrarindan turemisti ve
tel uzerinde var olmayan alanlar (alt/ust limit bandi, kayan pencere) tasiyordu.
Onemli sonuclar:

- Genlik HAM SAYIMDIR: 0..255, OLCEK CARPANI YOK (rapor Part 5). "%" degeri
  ilgili ozelligin limit Level'ina goredir: pct = current / limitLevel * 100.
- Canli iz TEK BIR CERCEVEDIR: 125 x int16 (rapor 4.1) ve her pakette
  BUTUNUYLE YENILENIR — kayan pencere degil.
- Durum tek bir "izleme/alarm" ikilisi degil, 16 kodlu ToolStatus halkasidir.
- Ozellik ADLARI kuruluma ozeldir (SKanalRec'ten okunur), koda gomulmez.
- Her cozulmus yuk bir GUVEN duzeyi tasir: baslik yerlesimi henuz kalibre
  edilmediginden (rapor §0.5) arayuz "on gorunum" ile "dogrulanmis" veriyi
  ayirt edebilmek zorundadir.
"""

from typing import Literal

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel

# Alarm durumu (CONTEXT: Alarm — aktif / onaylandi).
AlarmState = Literal["active", "acknowledged"]

# Cozulmus bir yuke ne kadar guvenilir (promos3.messages.Confidence ile ayni).
# "confirmed" disindaki her sey ekranda ON GORUNUM olarak isaretlenir.
Confidence = Literal["unknown", "named", "provisional", "confirmed"]

# Grafigin besleme bicimi:
#   "trace"  -> Promos3 SIGNALVERLAUF: 125 ornekli cerceve, her pakette yenilenir
#   "series" -> sayac/olcum zaman serisi: kayan pencere (NC kanali)
FeatureKind = Literal["trace", "series"]


class CamelModel(BaseModel):
    """Tel bicimi camelCase (types.ts ile ayni), Python alanlari snake_case."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


class FeatureLimit(CamelModel):
    """Limit (CONTEXT: Limit) — tek bir esik.

    Promos3'te limit bir ALT+UST BANDI DEGIL, tipli tek esiktir (tablo Limits:
    Limtype, Level, Feat_Num). Level genlikle AYNI ham birimdedir (0..255).
    """

    # Limtype ham kodu (anlam tablosu dogrulanmadi; kod oldugu gibi tasinir).
    lim_type: int | None = None
    # Esik degeri — ham sayim (bu kurulumda gorulen aralik 20..170).
    level: float
    # Okunur etiket (varsa; orn. alarm yuvasi adi).
    label: str | None = None


class Feature(CamelModel):
    """Ozellik (CONTEXT: Ozellik / feature) — kanalda olculen karakteristik.

    Kimlik Promos3 yonlendirme anahtarlaridir: (unitNo, channelKey) + yuva
    sirasi. Ad SKanalRec'ten gelir (kuruluma ozel).
    """

    id: str
    kind: FeatureKind
    name: str

    # --- Promos3 kimligi (NC serilerinde bos) ---
    # Izleme unitesi numarasi (CAN-ID - 1280).
    unit_no: int | None = None
    # SIGNALVERLAUF yonlendirme anahtarlari (rapor 4.1).
    tool_key: int | None = None
    channel_key: int | None = None
    # Ozellik yuvasi / Feat_Num ve SKanalRec maskesi (alt nibble secme biti).
    feature_nr: int | None = None
    mask: int | None = None

    # --- Olcum ---
    # True: degerler HAM SAYIM (0..255), olcek carpani yok (rapor Part 5).
    raw_counts: bool = False
    # Birim etiketi; ham sayimda bos kalir ("" -> ekran birim yazmaz).
    uom: str = ""
    # Cizilen degerler. "trace" icin 125'e kadar ornek (her pakette yenilenir),
    # "series" icin kayan pencere.
    samples: list[float] = []
    # O anki deger (izin son ornegi / serinin son degeri).
    current: float | None = None
    # Bu cercevedeki en kucuk/en buyuk ornek.
    min_value: float | None = None
    max_value: float | None = None

    # --- Limit ve durum ---
    # Yuzde hesabinda kullanilan birincil esik; guvenilir limit kaynagi
    # yoksa BOS kalir (uydurma esikle yanlis yuzde uretmemek icin).
    limit_level: float | None = None
    limits: list[FeatureLimit] = []
    # pct = current / limitLevel * 100 (rapor Part 5); limit yoksa bos.
    pct: float | None = None
    # Bu ozelligin TUM CSV degerlerinin ortalamasi (app/sim/baselines.py);
    # YALNIZ CSV kaynagi doldurur, telde her zaman bostur.
    #
    # HAM ORTALAMADIR, ESIK DEGILDIR. Esik = baseline x (1 + sapma/100) ve
    # sapmayi kullanici secer, o yuzden burada uygulanmaz: hub tek durumu
    # BUTUN abonelere yayinlar, sunucuda tutulan tek bir yuzde bir
    # kullanicinin secimini digerlerinin ekranina yazardi. Backend OLGUYU
    # yollar, esigi ekran kurar (frontend/src/domain/esik.ts).
    #
    # Bu alan doluyken `limit_level` ve `pct` BOS kalir: o ikisi Promos3 tel
    # kavramidir (yukaridaki "rapor Part 5") ve ayni alana kaynaga gore iki
    # ayri anlam yuklemek tel tarafini da bulaniklastirirdi. CSV'nin ham
    # limitleri `limits[]` icinde oldugu gibi durur.
    baseline: float | None = None
    # ToolStatus ham kodu ve etiketi (rapor 6.1).
    status_code: int | None = None
    status_label: str | None = None
    # Govde beklenen uzunluga ulasmadi: iz gosterilir ama tam degil.
    truncated: bool = False
    confidence: Confidence = "unknown"


class SensorInfo(CamelModel):
    """Sensor tanimlayicisi (rapor 4.3) — bu kurulumda 4x PROCUR-S (0x80)."""

    unit_no: int
    sensor_id: int
    serial: str | None = None
    # Ham SensorType kodu + etiketi (rapor 6.2).
    type: int | None = None
    type_label: str | None = None
    sub_type: int | None = None
    hw_serial: int | None = None
    sw_serial: int | None = None
    sens_channels: int | None = None
    feature_count: int | None = None
    confidence: Confidence = "unknown"


class UnitInfo(CamelModel):
    """Izleme unitesi (CONTEXT: Izleme unitesi / device) — Prometec kutusu.

    Bu kurulumda iki unite: SNr 10659 ve 10663, GType 0x44 / SubType 5.
    """

    unit: int
    # Seri no (10659/10663) — kimlik satiri gelene dek bos.
    serial_no: str | None = None
    online: bool = False

    # --- Cihaz kimligi (SGeraetRec / KONFIG) ---
    g_type: int | None = None
    g_sub_type: int | None = None
    # [MonitorTypes] cozumlemesi; indeks tabani sabitlenmedigi icin "(?)" tasir.
    model: str | None = None
    # 1 = Provis2/MC_, 2 = Promos3/MC3_ (getTargetType karsiligi).
    generation: int | None = None
    channel_amount: int | None = None
    mi_sens_amount: int | None = None
    # MiSensType[8] ham kodlari + etiketleri (0x80 = PROCUR-S).
    mi_sens_types: list[int] = []
    mi_sens_type_labels: list[str] = []
    sample_div: int | None = None
    reduz_lim: int | None = None
    # KONFIG ozetindeki surum (log: "Version 229").
    konfig_version: int | None = None
    # Firmware (orn. "Rtm_V14.5.H86") — akista gelirse dolar.
    firmware: str | None = None
    sensors: list[SensorInfo] = []


class Alarm(CamelModel):
    """Alarm (CONTEXT: Alarm) — (kanal, cevrim, ozellik, limit) dortlusune bagli.

    Alanlar hem tel kaydiyla (rapor 4.2) hem sakli `Alarms` tablosuyla ayni:
    ChannelNr, CycleNr, FeatureNr, LimitNr, Ack, TimeOffset.
    """

    id: str
    time: str  # ISO
    unit_no: int | None = None
    device_serial: str | None = None

    # --- Tel kaydi ---
    alarm_number: int | None = None
    entry_id: int | None = None
    # Durum baytinin alt yarisi = ToolStatus kodu (rapor 6.1).
    status_code: int | None = None
    status_label: str | None = None

    # --- Baglam (Alarms tablosu kolonlari) ---
    channel_nr: int | None = None
    cycle_nr: int | None = None
    feature_nr: int | None = None
    limit_nr: int | None = None
    # Ozellik adi (SKanalRec'ten cozulebiliyorsa).
    feature_name: str | None = None
    # [AlarmNames] yuva etiketi (1=Carpisma, 2=Kirilma, ...).
    slot_name: str | None = None
    # Esigi asan tepe deger ve esigin kendisi — ham sayim; kaynak vermiyorsa bos.
    peak: float | None = None
    level: float | None = None
    # Cevrim baslangicina gore konum (Alarms.TimeOffset).
    time_offset: int | None = None

    state: AlarmState = "active"
    confidence: Confidence = "unknown"


class EventRow(CamelModel):
    """Olay (CONTEXT: Olay / event) — izleme sirasinda dusen tek kayit satiri."""

    id: str
    time: str  # ISO
    unit_no: int | None = None

    # --- Promos3 olay kaydi (rapor 4.4) ---
    event_number: int | None = None
    # EventCode ham kodu + etiketi (rapor 6.5).
    code: int | None = None
    code_label: str | None = None
    channel_nr: int | None = None

    # --- Cevrim baglami (0x16 im satirlari) ---
    # Im satirlari cevrim ve is parcasi degisimlerini olay akisina dusurur;
    # NC program adi TELDE YOKTUR (o yalniz MazakFolly log akisinda vardi).
    workpiece: str | None = None
    cycle_nr: int | None = None

    confidence: Confidence = "unknown"


class WireStats(CamelModel):
    """Tasima/cozme teshisi — "veri gelmiyor" ile "geliyor ama cozulmuyor" ayrimi.

    Bu sayaclar telin sagligini ekranda GORUNUR kilar; yoksa arayuz sessizce
    bos durur ve iki cok farkli ariza (kablo yok / cozucu yanlis) ayni goruntuyu
    verir.

    `parsed` artik "saglama toplami TUTTU" demektir: komut kimligi tahmin degil,
    kanittir (bkz. promos3.mc). `unparsed` ise "cerceveler birlesti ama hicbir
    komut saglamayi tutturmadi" — yani ya veri bozuk ya da bilmedigimiz bir
    komut konusuluyor.
    """

    datagrams: int = 0
    can_frames: int = 0
    messages: int = 0
    parsed: int = 0
    unparsed: int = 0
    # CAN-ID tabanin altinda / unite araligi disinda (bu kutunun trafigi degil).
    dropped_out_of_range: int = 0
    # Tamamlanma hic gelmedi, tampon tasti (kayip cerceve / yanlis kural).
    dropped_overflow: int = 0
    # Sira numarasi atladi: kayip, yinelenen ya da bozuk cerceve.
    dropped_sequence: int = 0
    # Mesajin ortasindan katilindi (ilk seq 0 gorulene dek).
    dropped_orphan: int = 0
    # Onceki mesaj bitmeden yeni bir mesaj basladi.
    dropped_incomplete: int = 0
    # Cihaz "bu komutu yapamiyorum" cevabi verdi ([00][01]) — tel saglikli.
    device_errors: int = 0
    # Son kimliklendirilemeyen mesajin bas kismi (hex) — teshisin tek ipucu.
    last_unparsed_hex: str | None = None
    # Son cozulen komutun adi (akisin canliligini gosterir).
    last_command: str | None = None


class LiveState(CamelModel):
    """Akistan turetilen canli durum — types.ts LiveState'in tel karsiligi.

    TEK KAYNAK: Prometec Promos3 telgrafi (ADR-0002). Eskiden burada bir de NC
    kanali vardi (program / register / Provis surumu / NC nabzi); o alanlar
    YALNIZCA MazakFolly log tekrarindan doluyordu ve tel uzerinde karsiliklari
    yok. Kaynak kaldirildiginda alanlarin kendisi de kaldirildi — hicbir zaman
    dolmayacak bir alani tasimak, ekranda kalici bir "—" uretmekten baska ise
    yaramaz.

    Yerlerine telin GERCEKTEN verdikleri kondu: cevrim ve is parcasi sayaci
    (0x16 im satirlari / 0x01 durum) ve PLC giris-cikis haritasi (0x08).
    """

    # --- Cevrim baglami (MC_GIVESTATUS + SAMMELMERKMALE im satirlari) ---
    cycle: float | None = None
    # Is parcasi sayaci — im satiri her yeni parcada artar.
    workpiece: int | None = None

    # --- PLC giris/cikis bit haritalari (MC_GIVEPLCVALUES) ---
    plc_inputs: int | None = None
    plc_outputs: int | None = None

    # --- Prometec kanali ---
    units: list[UnitInfo] = []
    features: list[Feature] = []
    alarms: list[Alarm] = []
    events: list[EventRow] = []
    wire: WireStats | None = None
