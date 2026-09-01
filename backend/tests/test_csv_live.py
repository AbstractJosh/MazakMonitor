from datetime import datetime

from app.csv_live import apply_measurement
from app.domain import LiveState
from app.live import ALARM_LIMIT, WINDOW
from app.sim.csv_reader import FeatureValue, LimitValue, MeasurementRecord

TIME = "2026-08-10T11:23:02"


def _rec(**patch) -> MeasurementRecord:
    base = dict(
        unit_no=10660,
        source_time=datetime(2026, 8, 10, 11, 23, 2),
        channel_nr=1,
        tool_nr=11,
        program_nr=0,
        cut_nr=0,
        workpiece=None,
        alarm=None,
        alarm_limit=None,
        source_file="000_01_00011_000_260810_112302.csv",
        features=[
            FeatureValue(slot=1, name="SPINDEL", value=115.0, work_value=87.0),
            FeatureValue(slot=2, name="VIBRATION", value=None, work_value=None),
        ],
        limits=[LimitValue(limit_nr=1, level=230.0, lim_type=2, feature_nr=1)],
    )
    base.update(patch)
    return MeasurementRecord(**base)


def test_unite_online_isaretlenir():
    out = apply_measurement(LiveState(), _rec(), TIME)
    assert [u.unit for u in out.units] == [10660]
    assert out.units[0].online is True
    assert out.units[0].serial_no == "10660"


def test_ozellik_seri_olarak_kurulur():
    out = apply_measurement(LiveState(), _rec(), TIME)
    ozellikler = {f.name: f for f in out.features}
    assert "SPINDEL" in ozellikler
    f = ozellikler["SPINDEL"]
    assert f.id == "csv:10660:1"
    assert f.kind == "series"
    assert f.unit_no == 10660
    assert f.samples == [115.0]
    assert f.current == 115.0
    assert f.raw_counts is True


def test_degeri_olmayan_yuva_ozellik_URETMEZ():
    """VIBRATION kolonu 10665'te 131/131 bostur.

    Hic dolmayacak bir ozellik ekranda kalici bir "—" uretmekten baska ise
    yaramaz (domain.py'nin NC alanlarini kaldirma gerekcesinin aynisi).
    """
    out = apply_measurement(LiveState(), _rec(), TIME)
    assert all(f.name != "VIBRATION" for f in out.features)


def test_ornekler_birikir_ve_pencere_kayar():
    state = LiveState()
    for i in range(WINDOW + 10):
        state = apply_measurement(
            state,
            _rec(features=[FeatureValue(slot=1, name="SPINDEL", value=float(i), work_value=None)]),
            TIME,
        )
    f = next(f for f in state.features if f.name == "SPINDEL")
    assert len(f.samples) == WINDOW
    assert f.samples[-1] == float(WINDOW + 9)
    assert f.current == float(WINDOW + 9)
    assert f.min_value == float(10)
    assert f.max_value == float(WINDOW + 9)


def test_limit_yuzdeyi_besler():
    out = apply_measurement(LiveState(), _rec(), TIME)
    f = next(f for f in out.features if f.name == "SPINDEL")
    assert f.limit_level == 230.0
    assert f.pct == 50.0
    assert [lim.level for lim in f.limits] == [230.0]


def test_limitsiz_ozellikte_yuzde_BOS_kalir():
    """Uydurma esikle yanlis yuzde uretmektense yuzde hic gosterilmez."""
    out = apply_measurement(LiveState(), _rec(limits=[]), TIME)
    f = next(f for f in out.features if f.name == "SPINDEL")
    assert f.limit_level is None
    assert f.pct is None


def test_taban_CSV_LIMITININ_YERINE_gecer():
    """Taban varken tel kavramlari (limitLevel/pct) bos kalir.

    Gerekce baselines.py'de: CSV'nin kendi limiti 10665'te izin dortte biri
    kadardir. Esik tabandan turer ve sapmayi EKRAN uygular, o yuzden burada
    yalnizca ham ortalama tasinir.
    """
    out = apply_measurement(LiveState(), _rec(), TIME, {(10660, 1): 113.4})
    f = next(f for f in out.features if f.name == "SPINDEL")
    assert f.baseline == 113.4
    assert f.limit_level is None
    assert f.pct is None


def test_taban_varken_HAM_CSV_LIMITLERI_listede_kalir():
    """Veridir; esigi kurmuyor olmasi silinmesini gerektirmez."""
    out = apply_measurement(LiveState(), _rec(), TIME, {(10660, 1): 113.4})
    f = next(f for f in out.features if f.name == "SPINDEL")
    assert [lim.level for lim in f.limits] == [230.0]


def test_taban_YALNIZ_kendi_yuvasina_uygulanir():
    """Baska yuvanin tabani bu ozelligi etkilemez; CSV limiti yerinde kalir."""
    out = apply_measurement(LiveState(), _rec(), TIME, {(10660, 9): 500.0})
    f = next(f for f in out.features if f.name == "SPINDEL")
    assert f.baseline is None
    assert f.limit_level == 230.0
    assert f.pct == 50.0


def test_taban_YOKSA_CSV_limiti_oldugu_gibi_kalir():
    """Taban uydurulmaz: elde ne varsa o gosterilir."""
    out = apply_measurement(LiveState(), _rec(), TIME, None)
    f = next(f for f in out.features if f.name == "SPINDEL")
    assert f.baseline is None
    assert f.limit_level == 230.0


def test_alarm_biti_alarm_uretir():
    out = apply_measurement(LiveState(), _rec(alarm=1, alarm_limit=230), TIME)
    assert len(out.alarms) == 1
    a = out.alarms[0]
    assert a.unit_no == 10660
    assert a.channel_nr == 1
    assert a.level == 230.0
    assert a.state == "active"


def test_alarmsiz_satir_alarm_URETMEZ():
    assert apply_measurement(LiveState(), _rec(alarm=0), TIME).alarms == []
    assert apply_measurement(LiveState(), _rec(alarm=None), TIME).alarms == []


def test_alarm_listesi_ALARM_LIMIT_e_kirpilir():
    """CSV tekrari sonsuz donguyle oynar; state_wire() listenin TAMAMINI her
    SSE cercevesine gomer. Kirpma olmazsa bellek ve cerceve boyu sinirsiz
    buyur (live.py'nin ayni kurali: satir 347, 520).
    """
    state = LiveState()
    total = ALARM_LIMIT + 10
    for i in range(total):
        state = apply_measurement(
            state,
            _rec(alarm=1, alarm_limit=230, source_file=f"dosya_{i}.csv"),
            TIME,
        )
    assert len(state.alarms) == ALARM_LIMIT
    # En yeni EN BASTA kalir: sonuncu uretilen alarm ilk sirada.
    assert state.alarms[0].id == f"csv:10660:dosya_{total - 1}.csv"
    # En eski (ilk uretilenler) atilir; sinirin disinda kalanlar YOK, sinirin
    # ICINDEKI en eski ise KALIR.
    kept_ids = {a.id for a in state.alarms}
    assert "csv:10660:dosya_0.csv" not in kept_ids
    oldest_dropped = total - ALARM_LIMIT - 1
    oldest_kept = total - ALARM_LIMIT
    assert f"csv:10660:dosya_{oldest_dropped}.csv" not in kept_ids
    assert f"csv:10660:dosya_{oldest_kept}.csv" in kept_ids


def test_ayni_dosya_TEKRAR_gelince_alarm_COGALMAZ():
    """CSV donguseldir: ayni dosya her turda yeniden okunur.

    Kirpma tek basina yetmiyordu. Sevkiyattaki veride 262 CSV'nin 17'si alarm
    tasir ve bir tur ~131 sn surer; kimlik kaynak DOSYASINDAN turedigi icin
    liste 17 GERCEK olayi ~11'er kopyayla ALARM_LIMIT'e (200) sisiriyordu.
    Sonucu yalniz bellek degildi: React ayni anahtari birden cok kez goruyor,
    "Aktif Alarm" sayaci 17'den 200'e tirmaniyor ve tek bir onay her kopyayi
    ayri ayri isaretlemek zorunda kaliyordu.
    """
    state = LiveState()
    for tur in range(20):
        state = apply_measurement(
            state,
            _rec(alarm=1, alarm_limit=230, cut_nr=tur, source_file="ayni.csv"),
            f"2026-08-10T11:23:{tur:02d}",
        )
    assert len(state.alarms) == 1
    # Kalan kayit EN YENISIDIR: "ayni alarm yeniden goruldu" demek, eski
    # kopyayi degil sonuncuyu tutmak demektir.
    assert state.alarms[0].cycle_nr == 19
    assert state.alarms[0].time == "2026-08-10T11:23:19"


def test_iki_ayri_dosya_iki_ayri_alarm_kalir():
    """Tekilleme KIMLIGE gore yapilir; ayri olaylar birbirini yemez."""
    state = apply_measurement(
        LiveState(), _rec(alarm=1, alarm_limit=230, source_file="a.csv"), TIME
    )
    state = apply_measurement(
        state, _rec(alarm=1, alarm_limit=230, source_file="b.csv"), TIME
    )
    state = apply_measurement(
        state, _rec(alarm=1, alarm_limit=230, source_file="a.csv"), TIME
    )
    assert [a.id for a in state.alarms] == ["csv:10660:a.csv", "csv:10660:b.csv"]


def test_uydurulmayanlar_bos_kalir():
    """CSV'de karsiligi olmayan alan DOLDURULMAZ.

    workpiece: Workpiece ID kolonu 262/262 dosyada bostur.
    wire: CSV'nin teli yoktur (tasima teshisi Promos3'e ozeldir).
    """
    out = apply_measurement(LiveState(), _rec(), TIME)
    assert out.workpiece is None
    assert out.wire is None
    assert out.plc_inputs is None
    assert out.events == []


def test_cevrim_cut_nr_den_gelir():
    out = apply_measurement(LiveState(), _rec(cut_nr=7), TIME)
    assert out.cycle == 7


def test_iki_unite_ayri_ozellik_uretir():
    state = apply_measurement(LiveState(), _rec(unit_no=10660), TIME)
    state = apply_measurement(state, _rec(unit_no=10665), TIME)
    assert {f.id for f in state.features} == {"csv:10660:1", "csv:10665:1"}
    assert [u.unit for u in state.units] == [10660, 10665]
