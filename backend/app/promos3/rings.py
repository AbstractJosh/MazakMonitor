"""Karar halkalari (decoder rings) — kod -> anlam tablolari.

Kaynak: rapor Part 6. Uygulamanin kendi tablolarindan (initStatusTables) ve
PROVISsettings.ini'den turer. Kod->etiket cevirisi BACKEND'de yapilir: frontend
ham kodu da etiketi de gorur, boylece bilinmeyen bir kod ekranda "?" yerine
sayisiyla gorunur (sessizce kaybolmaz).
"""

# --- ToolStatus (durum baytinin alt yarisi, 0x00..0x0F) — rapor 6.1 ---
# Alarm kayitlarindaki status alaninin ALT BAYTI bu halkadan okunur.
TOOL_STATUS: dict[int, str] = {
    0x0: "Boş",
    0x1: "Aşırı yük",
    0x2: "Düşük yük",
    0x3: "Temas",
    0x4: "Takım yok",
    0x5: "Çalışma üstü",
    0x6: "Çalışma altı",
    0x7: "Kesme başlangıcı",
    0x8: "Kesme sonu",
    0x9: "Dinamik üst",
    0xA: "Dinamik alt",
    0xB: "Örüntü üst",
    0xC: "Örüntü alt",
    0xD: "ACF temas",
    0xE: "Kesme algılama teması",
    0xF: "Takım aşınması",
}

# NOT: "hangi kod operatore alarm olarak gosterilir" siniflandirmasi burada
# DEGIL, frontend/src/domain/format.ts statusTone'da durur (bir sunum
# karari; 0x7/0x8 kesme basi/sonu ve 0x3/0xD/0xE temas bildirimleri izlemenin
# normal isaretleridir, kirmiziya boyanmaz). Iki yerde tutulsa sessizce
# ayrisirdi.

# --- SensorType — rapor 6.2 ---
SENSOR_TYPE: dict[int, str] = {
    0x01: "PA-Box",
    0x03: "VB-Box",
    0x10: "PA 111",
    0x11: "PA 122 S1",
    0x13: "PA 122 S2",
    0x14: "PA 211",
    0x15: "PA 221",
    0x16: "DU2A211",
    0x20: "EP 111",
    0x24: "EP 211",
    0x30: "VBI 211",
    0x31: "AE 211",
    0x38: "VBI RTCM",
    0x80: "PROCUR-S",
    0x81: "PROCUR-I",
    0x82: "PROCUR-B",
    0x83: "ACFeed",
    0x84: "ACfeed OVR",
    0x90: "Pozisyon",
    0x91: "Sıcaklık",
    0xA0: "MI32bit",
    0xFF: "Bilinmiyor",
}

# --- ChannelStatus (0..7) — rapor 6.3 ---
CHANNEL_STATUS: dict[int, str] = {
    0: "Yok",
    1: "OK",
    2: "Hatalı",
    3: "Sonra",
    5: "Sıfırlandı",
    6: "Bastırıldı",
    7: "Alarm eksik",
}

# --- AccessLevel — rapor 6.4 ---
ACCESS_LEVEL: dict[int, str] = {
    0x00: "Operatör",
    0x04: "Ayarcı",
    0x05: "Yönetici",
    0x06: "Tezgah üreticisi",
    0x63: "SERVİS",
}

# --- EventCode — rapor 6.5 (secili kodlar) ---
EVENT_CODE: dict[int, str] = {
    0x01: "RTC ayarlandı",
    0x02: "Çevrim ayarı değişti",
    0x03: "Limit değişti",
    0x04: "Çevrim modu değişti",
    0x06: "Liste temizlendi",
    0x07: "Cihaz yeniden adlandırıldı",
    0x09: "Sensör değişti",
    0x14: "Yeniden başlatma",
    0xFF: "Boş",
}

# --- Alarm yuvasi -> etiket ([AlarmNames]) — rapor 6.6 ---
# OPERATORCE YAPILANDIRILABILIR: bu kurulumun PROVISsettings.ini degerleri.
# Baska tezgahta farkli olabilir; ini okunabildiginde oradan gelmeli.
ALARM_SLOT: dict[int, str] = {
    1: "Çarpışma",
    2: "Kırılma",
    3: "Aşınma",
    4: "Eksik",
    5: "Soğutma sıvısı",
}

# --- Model cozumleme ([MonitorTypes]) — rapor 6.6 ---
# GType aileyi, GSubType satiri secer. Bu kutu 0x44 ailesi.
MONITOR_TYPES_0X44: tuple[str, ...] = (
    "MDL5081-16",
    "MDL5082-16",
    "MDL5051-16",
    "MDL5052-16",
    "MSL5081-16",
    "MSL5082-16",
    "MSL5051-16",
    "MSL5052-16",
    "MSL5074-16",
    "MSL3031-16",
    "MSL3032-16",
    "MSL3011-16",
    "MSL3012-16",
    "MDL5031-16",
    "MDL5032-16",
    "MSL5034-16",
)

# Aile -> nesil. Model adi olmayan aileler icin de nesil bilinir.
PROVIS2_FAMILIES: frozenset[int] = frozenset({0x30, 0x38, 0x39, 0x40, 0x41, 0x43, 0x44, 0x48})
PROMOS3_FAMILIES: dict[int, str] = {0x70: "CompactBox", 0x71: "SensorBox", 0x80: "XT-Monitor"}


def _named(table: dict[int, str], code: int | None, unknown: str | None) -> str | None:
    """Kod -> etiket. unknown verilirse bilinmeyen kod SAYISIYLA gorunur.

    unknown=None yalniz operatorce yapilandirilan tablolar icindir (bkz.
    alarm_slot_name): orada "bilinmeyen 0x06" degil, "etiket yok" dogru
    cevaptir.
    """
    if code is None:
        return None
    if unknown is None:
        return table.get(code)
    return table.get(code, f"{unknown} 0x{code:02X}")


def tool_status_name(code: int | None) -> str | None:
    """ToolStatus etiketi; bilinmeyen kod sayisiyla gorunur."""
    return _named(TOOL_STATUS, code, "Bilinmeyen durum")


def sensor_type_name(code: int | None) -> str | None:
    return _named(SENSOR_TYPE, code, "Bilinmeyen tip")


def event_code_name(code: int | None) -> str | None:
    return _named(EVENT_CODE, code, "Bilinmeyen olay")


def alarm_slot_name(slot: int | None) -> str | None:
    # [AlarmNames] operatorce doldurulur; tanimsiz yuvanin adi YOKTUR.
    return _named(ALARM_SLOT, slot, None)


def monitor_model(g_type: int | None, g_sub_type: int | None) -> str | None:
    """(GType, GSubType) -> model adi.

    DIKKAT (rapor §0.5/6.6): 0x44 ailesinde indeks tabani HENUZ SABITLENMEDI;
    (0x44, 5) ya MSL5081-16 ya MSL5082-16'dir. Her iki C okuyucu da (sim ve
    view) 1-TABANLI okur — promos3_sim.c "0x44 / 5 -> MSL5081-16" der,
    promos3_view.c MONTYPE_44[gsubtype-1] kullanir — bu yuzden uc uygulama
    ayni seyi soylesin diye burada da 1-tabanli okunur. Belirsizlik kozmetik
    oldugu icin model adinda "?" ile gorunur, ekranda kesinmis gibi durmasin.
    """
    if g_type is None:
        return None
    if g_type in PROMOS3_FAMILIES:
        return PROMOS3_FAMILIES[g_type]
    if g_type == 0x44 and g_sub_type is not None and 1 <= g_sub_type <= len(MONITOR_TYPES_0X44):
        return f"{MONITOR_TYPES_0X44[g_sub_type - 1]} (?)"
    return f"GType 0x{g_type:02X}" + ("" if g_sub_type is None else f"/{g_sub_type}")


def generation_of(g_type: int | None) -> int | None:
    """Cihaz nesli: 1 = Provis2/MC_, 2 = Promos3/MC3_ (getTargetType karsiligi)."""
    if g_type is None:
        return None
    if g_type in PROMOS3_FAMILIES:
        return 2
    if g_type in PROVIS2_FAMILIES:
        return 1
    return None
