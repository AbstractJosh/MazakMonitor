"""Provis olcum satiri -> canli durum: SAF esleyici.

live.py'nin (Promos3 telgrafi -> LiveState) CSV karsiligidir ve ayni
kurallara uyar: saatsiz (an damgasi cagirandan gelir), saf, tek basina
test edilebilir.

CSV kaynagi neden ayni ekrani besler: veri/ altindaki dosyalar OLCUM
SATIRLARIDIR ve Promos3'un 0x16 SAMMELMERKMALE bloguyla ayni seyi tasir
(ozellik basina deger + limit + alarm biti). Bu yuzden ayni "series"
grafiklerine dusurler ve CSV tezgahi ayri bir ekran turu gerektirmez.

DOLDURULMAYANLAR bilerek bostur: CSV'de karsiligi olmayan alan (is parcasi
sayaci, PLC haritasi, tel istatistikleri, cihaz kimligi) uydurulmaz —
ekranda kalici bir "—" uretmekten baska ise yaramaz.
"""

from app.domain import Alarm, Feature, FeatureLimit, LiveState
from app.live import ALARM_LIMIT, WINDOW, _upsert_feature, _upsert_unit
from app.sim.baselines import Baselines
from app.sim.csv_reader import MeasurementRecord


def csv_feature_id(unit_no: int, slot: int) -> str:
    """CSV kaynakli bir ozelligin kimligi.

    ACIK ADLI (eskiden `_feature_id`): kosum kaydi (app/kosum.py) AYNI
    kimligi uretmek zorunda — canli kutucuk ile kosum grafigi ayni sinyali
    ayni adla anmazsa ikisini yan yana okumak imkansiz olur. Kopyalanmis bir
    f-string bunu sessizce bozabilirdi. live.py'nin `series_feature_id` /
    `trace_feature_id` adlandirmasiyla ayni kalip.
    """
    return f"csv:{unit_no}:{slot}"


def apply_measurement(
    state: LiveState,
    rec: MeasurementRecord,
    time_iso: str,
    baselines: Baselines | None = None,
) -> LiveState:
    """Bir olcum satirini duruma isler ve YENI durumu doner.

    `baselines` verilirse (canli yol her zaman verir) o yuvanin taban
    ortalamasi CSV'NIN KENDI LIMITININ YERINE gecer: `baseline` dolar,
    `limit_level`/`pct` bos kalir. Gerekce baselines.py'de — CSV limitleri
    10665 unitesinde izin dortte biri kadardir ve cizgi grafigin tabanina
    yapisir.

    VERILMEZSE CSV limiti oldugu gibi kalir. Bu bir yedek degil, dogru
    davranis: taban yoksa uydurulmaz ve elde ne varsa o gosterilir (limitsiz
    ozellikte yuzdenin hic basilmamasiyla ayni kural).
    """
    units = _upsert_unit(
        state.units,
        rec.unit_no,
        # Klasor adi (10660/10665) oldugu gibi tasinir. CONTEXT.md telde
        # iki uniteyi 10659/10663 SERI NUMARALARIYLA anar; ikisi ayni sey
        # degildir, o yuzden CAN turevi bir unite indisiymis gibi
        # gosterilmez.
        serial_no=str(rec.unit_no),
        online=True,
    )

    features = state.features
    for fv in rec.features:
        # Degeri olmayan yuva ozellik URETMEZ: 10665'in VIBRATION kolonu
        # 131/131 bostur ve hic dolmayacak bir grafik acmak, ekranda
        # kalici bir "—"den baska bir sey vermez.
        if fv.value is None:
            continue

        fid = csv_feature_id(rec.unit_no, fv.slot)
        previous = next((f for f in features if f.id == fid), None)

        base = previous.samples if previous else []
        samples = [*base, fv.value][-WINDOW:]
        current = samples[-1]

        # Bu yuvaya ait HAM CSV limitleri. Taban varken esigi bunlar
        # kurmaz ama listede kalirlar: veridir, silmek icin sebep yok.
        limits = [
            FeatureLimit(lim_type=lv.lim_type, level=lv.level)
            for lv in rec.limits
            if lv.feature_nr == fv.slot
        ]
        baseline = (baselines or {}).get((rec.unit_no, fv.slot))
        # Taban varsa esik ONDAN turer ve tel kavramlari bos birakilir; yoksa
        # CSV limiti birincil esiktir ve yuzdenin paydasidir.
        limit_level = None if baseline is not None else (limits[0].level if limits else None)
        pct = None if not limit_level else round(current / limit_level * 100, 1)

        features = _upsert_feature(
            features,
            Feature(
                id=fid,
                kind="series",
                # Ad CSV kolon basligindan gelir (kuruluma ozel, koda
                # gomulmez). Baslik bossa live.py ile ayni yedek kullanilir.
                name=fv.name or f"Özellik {fv.slot}",
                unit_no=rec.unit_no,
                feature_nr=fv.slot,
                # Provis degerleri ham sayimdir; olcek carpani yok.
                raw_counts=True,
                uom="",
                samples=samples,
                current=current,
                min_value=min(samples),
                max_value=max(samples),
                limit_level=limit_level,
                limits=limits,
                pct=pct,
                baseline=baseline,
                # Degerler kalibre edilmemis bir baslik yerlesiminden degil,
                # belgelenmis bir Provis disa aktarimindan gelir ve
                # csv_reader kolon hizasini dosya basina dogrular.
                confidence="confirmed",
            ),
        )

    alarms = state.alarms
    if rec.alarm:
        # CSV tekrari SONSUZ donguyle oynar ve state_wire() alarm listesinin
        # TAMAMINI her SSE cercevesine gomer; live.py'nin butun yollarinin
        # yaptigi gibi (_apply_merkmale, _apply_alarm) burada da en yeniyi
        # basa alip ALARM_LIMIT'e kirpiyoruz, yoksa hem bellek hem her
        # cerceve boyu sinirsiz buyur.
        row = Alarm(
            id=f"csv:{rec.unit_no}:{rec.source_file}",
            time=time_iso,
            unit_no=rec.unit_no,
            device_serial=str(rec.unit_no),
            channel_nr=rec.channel_nr,
            cycle_nr=rec.cut_nr,
            alarm_number=rec.alarm,
            level=float(rec.alarm_limit) if rec.alarm_limit is not None else None,
            state="active",
            confidence="confirmed",
        )
        # AYNI KIMLIK IKI KEZ DURMAZ (_apply_alarm ile ayni kural). Alarm
        # kimligi kaynak DOSYASINDAN turer ve dosya her turda yeniden okunur:
        # kirpma tek basina yetmiyordu, liste 17 GERCEK olayi ~11'er kopyayla
        # 200 satira sisiriyordu. Sonuclari sadece bellek degildi — React ayni
        # anahtari birden cok kez goruyor, "Aktif Alarm" sayaci 17'den 200'e
        # tirmaniyor ve tek bir onay her kopyayi ayri ayri isaretlemek zorunda
        # kaliyordu.
        #
        # Yeni satirin BASA alinmasi onay tasimasini da anlamli kilar: ayni
        # kimlik = AYNI ALARM YENIDEN GORULDU, yani istemcideki "goruldu"
        # damgasi (kimlige baglidir, ADR-0004) dogru sekilde ustunde kalir.
        kept = [a for a in alarms if a.id != row.id]
        alarms = [row, *kept][:ALARM_LIMIT]

    return state.model_copy(
        update={
            "units": units,
            "features": features,
            "alarms": alarms,
            # Bu veride Cut 262/262 dosyada 0'dir; yine de GERCEK cevrim
            # numarasidir ve oldugu gibi tasinir.
            "cycle": rec.cut_nr,
        }
    )
