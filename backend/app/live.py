"""Canli veri katmani — Promos3 mesajlarini alan modeline ceviren SAF esleyiciler.

TEK KAYNAK: Prometec CAN-over-UDP telgrafi (ADR-0002). Kaynak ister atolyedeki
gateway ister promos3-c/done/promos3_sim.exe olsun, tel bicimi AYNIDIR — bu
yuzden burada "simulasyon kipi" diye bir dal yoktur.

Simulasyon yok: tum degerler akistan turer; akis yoksa durum bos kalir.
Esleyiciler saatsizdir (an damgasi cagiranin isidir) ki pytest ile tek basina
test edilebilsinler.

EKRANI BESLEYEN IKI AYRI GRAFIK TURU — ikisi de gercek, ikisi de ayni tel:

  0x16 SAMMELMERKMALE -> "series"  Her cevapta birkac olcum satiri; ozellik
                                   basina KAYAN PENCERE tutulur. Canli ekranin
                                   asil verisi budur (promos3_view.c: "this
                                   block IS the live screen").
  0x1B SIGNALVERLAUF  -> "trace"   Tek cerceve, 125 ornek, her pakette
                                   BUTUNUYLE yenilenir — kayan pencere degil.

Ikisi ayni fiziksel ozelligi farkli gosterir; bu yuzden ayri Feature kayitlari
olarak durur ve tek bir grafige ezilmez.
"""

from typing import Any

from app.domain import (
    Alarm,
    EventRow,
    Feature,
    LiveState,
    UnitInfo,
)
from app.promos3 import bodies, records, rings
from app.promos3.messages import (
    CMD_ALARM,
    CMD_GTYPE,
    CMD_KANAL,
    CMD_KONFIG,
    CMD_MERKMALE,
    CMD_PLCVALUES,
    CMD_SIGNALVERLAUF,
    CMD_STATUS,
    Promos3Message,
)

# Olcum serilerindeki kayan pencere boyu.
WINDOW = 120

# Listelerde tutulan en fazla kayit (en yeniler kalir).
EVENT_LIMIT = 500
ALARM_LIMIT = 200


def initial_live_state() -> LiveState:
    """Bos baslangic durumu.

    ONCEDEN TANIMLI GRAFIK YOKTUR: ozellikler ve adlari TELDEN gelir
    (MC_GIVEKANAL, +0x4D ozellik yuvalari). Uydurma yer tutucu grafik acmak,
    akis gelmeden once ekranda "veri var" izlenimi verirdi.
    """
    return LiveState()


def _upsert_unit(units: list[UnitInfo], unit: int, **patch: Any) -> list[UnitInfo]:
    if any(u.unit == unit for u in units):
        nxt = [u.model_copy(update=patch) if u.unit == unit else u for u in units]
    else:
        nxt = [*units, UnitInfo(unit=unit).model_copy(update=patch)]
    return sorted(nxt, key=lambda u: u.unit)


def _upsert_feature(features: list[Feature], feature: Feature) -> list[Feature]:
    """Ayni kimlikli ozelligi yeniler; yoksa sona ekler (grafik sirasi korunur)."""
    for i, f in enumerate(features):
        if f.id == feature.id:
            nxt = list(features)
            nxt[i] = feature
            return nxt
    return [*features, feature]


# --- Kimlikler -----------------------------------------------------------
# Ayni (unite, yuva) ikilisi HEP AYNI grafige duser; boylece grafik adi ve
# sirasi paketler arasinda sabit kalir.


def series_feature_id(unit: int, slot: int) -> str:
    """0x16 olcum serisi kimligi — ozellik yuvasi sirasina baglidir."""
    return f"u{unit}-f{slot}"


def trace_feature_id(unit: int, tool_key: int, channel_key: int) -> str:
    """0x1B iz kimligi = SIGNALVERLAUF yonlendirme anahtarlari (rapor 4.1)."""
    return f"u{unit}-t{tool_key}-c{channel_key}"


def _slot_features(state: LiveState, unit: int) -> list[Feature]:
    """Bu unitenin 0x16 serileri (yuva sirasina gore)."""
    return [
        f
        for f in state.features
        if f.unit_no == unit and f.kind == "series" and f.feature_nr is not None
    ]


def _config_name(mask: int | None, names: dict[int, str] | None) -> str | None:
    """Yapilandirmadaki elle gecersiz kilma (PROMOS3_FEATURE_NAMES).

    Adlarin DOGRU kaynagi teldir (MC_GIVEKANAL +0x4D). Bu yalnizca yedektir:
    kanal kaydi henuz gelmediyse ya da yuva adsizsa devreye girer.
    """
    if names is None or mask is None:
        return None
    return names.get(mask)


# ---------------------------------------------------------------------------
# 0x0E MC_GIVEKANAL — ozellik yuvalari ve ADLARI (telin kendisinden)
# ---------------------------------------------------------------------------


def _apply_kanal(state: LiveState, msg: Promos3Message, names: dict[int, str] | None) -> LiveState:
    """Kanal kaydini isler: ozellik yuvalarini ve ADLARINI kurar.

    ADLAR ARTIK TELDEN GELIR. Kuruluma ozel operator etiketleri (bu tezgahta
    VIBRATION / M131 DEBI / M131BASINC / M08 DEBI) SKanalRec'in +0x4D'deki 4
    yuvasinda durur ve burada okunur — koda gomulmez, yapilandirmadan
    beklenmez.
    """
    rec = bodies.decode_kanal(msg)
    if rec is None:
        return state

    features = state.features
    for slot in rec.features:
        if not slot.used:
            # Maskesi 0 olan yuva KULLANILMIYOR demektir; bos grafik acilmaz.
            continue
        fid = series_feature_id(msg.unit, slot.index)
        previous = next((f for f in features if f.id == fid), None)
        name = slot.name or _config_name(slot.mask, names) or f"Özellik {slot.index + 1}"
        if previous is not None:
            features = _upsert_feature(
                features,
                previous.model_copy(update={"name": name, "mask": slot.mask}),
            )
            continue
        features = _upsert_feature(
            features,
            Feature(
                id=fid,
                kind="series",
                name=name,
                unit_no=msg.unit,
                feature_nr=slot.index,
                mask=slot.mask,
                # 0..254 ham sayim; olcek carpani YOK (rapor Part 5).
                raw_counts=True,
                uom="",
                samples=[],
                confidence=msg.confidence,
            ),
        )

    return state.model_copy(
        update={
            "features": features,
            "units": _upsert_unit(
                state.units,
                msg.unit,
                online=True,
                channel_amount=rec.channel_num or None,
            ),
        }
    )


# ---------------------------------------------------------------------------
# 0x16 MC_GIVESAMMELMERKMALE — CANLI OLCUM BLOGU (ekranin asil verisi)
# ---------------------------------------------------------------------------


def _merkmale_features(
    state: LiveState, msg: Promos3Message, block: bodies.MerkmalBlock, names: dict[int, str] | None
) -> list[Feature]:
    """Olcum satirlarini ozellik basina kayan pencereye iter."""
    features = state.features
    for slot in range(block.features):
        fid = series_feature_id(msg.unit, slot)
        previous = next((f for f in features if f.id == fid), None)

        # Bu cevaptaki bu ozellige ait tum ornekler (satir sirasiyla).
        fresh = [float(row.values[slot]) for row in block.samples if slot < len(row.values)]
        if not fresh and previous is None:
            continue

        base = previous.samples if previous else []
        samples = [*base, *fresh][-WINDOW:]
        current = samples[-1] if samples else None

        # Durum: bu cevaptaki SON satirin bu ozellige ait durum bayti.
        status_code = None
        for row in reversed(block.samples):
            if slot < len(row.statuses):
                status_code = row.statuses[slot]
                break

        limit_level = previous.limit_level if previous else None
        limits = previous.limits if previous else []
        pct = (
            None
            if current is None or not limit_level
            else round(current / limit_level * 100, 1)
        )
        mask = previous.mask if previous else None
        name = (
            previous.name
            if previous and previous.name
            else (_config_name(mask, names) or f"Özellik {slot + 1}")
        )

        features = _upsert_feature(
            features,
            Feature(
                id=fid,
                kind="series",
                name=name,
                unit_no=msg.unit,
                feature_nr=slot,
                mask=mask,
                raw_counts=True,
                uom="",
                samples=samples,
                current=current,
                min_value=min(samples) if samples else None,
                max_value=max(samples) if samples else None,
                limit_level=limit_level,
                limits=limits,
                pct=pct,
                status_code=status_code,
                status_label=rings.tool_status_name(
                    None if status_code is None else status_code & 0x0F
                ),
                truncated=block.truncated,
                confidence=msg.confidence,
            ),
        )
    return features


def _marker_rows(
    msg: Promos3Message, block: bodies.MerkmalBlock, time_iso: str, workpiece: int | None
) -> tuple[list[EventRow], int | None, int | None]:
    """Im satirlarini olay satirlarina ve (cevrim, is parcasi) degerlerine cevirir."""
    rows: list[EventRow] = []
    cycle: int | None = None
    wp = workpiece

    for marker in block.markers:
        if marker.is_new_cycle:
            cycle = marker.param
            label = "Yeni çevrim"
        elif marker.is_workpiece:
            # Parametre kimligin KENDISI degil BOYUDUR; sayilan olayin
            # kendisidir, bu yuzden sayac artirilir.
            wp = (wp or 0) + 1
            label = "Yeni iş parçası"
        elif marker.is_reset:
            label = "Özellik sıfırlama"
        else:
            label = None

        rows.append(
            EventRow(
                id=f"m-{msg.unit}-{time_iso}-{marker.row}",
                time=time_iso,
                unit_no=msg.unit,
                code=marker.code,
                code_label=label or f"Bilinmeyen im 0x{marker.code:02X}",
                cycle_nr=cycle,
                workpiece=None if wp is None else str(wp),
                confidence=msg.confidence,
            )
        )
    return rows, cycle, wp


def _merkmale_alarms(
    msg: Promos3Message, block: bodies.MerkmalBlock, time_iso: str, serial: str | None
) -> list[Alarm]:
    """Alarm BITINDEN alarm satiri uretir.

    Bu kutuda 0x12 MC_GIVEALARM poll dongusunde YOKTUR (yalniz istek uzerine
    gelir) ve backend salt dinleyicidir — dolayisiyla alarmin tel uzerindeki
    tek gozlenebilir izi olcum satirinin durum baytindaki 0x04 bitidir.
    Uydurma degil, dogrudan okunan bir bittir; yine de kaydin kendisi kadar
    ayrintili degildir (limit/tepe degeri tasimaz) ve bunu confidence soyler.
    """
    rows: list[Alarm] = []
    for idx, row in enumerate(block.samples):
        if not row.alarm:
            continue
        for slot, status in enumerate(row.statuses):
            if not status & bodies.STATUS_ALARM:
                continue
            rows.append(
                Alarm(
                    id=f"a-{msg.unit}-{time_iso}-{idx}-{slot}",
                    time=time_iso,
                    unit_no=msg.unit,
                    device_serial=serial,
                    status_code=status & 0x0F,
                    status_label=rings.tool_status_name(status & 0x0F),
                    feature_nr=slot,
                    state="active",
                    confidence=msg.confidence,
                )
            )
    return rows


def _apply_merkmale(
    state: LiveState, msg: Promos3Message, time_iso: str, names: dict[int, str] | None
) -> LiveState:
    block = bodies.decode_merkmale(msg)
    if block is None:
        return state

    serial = next(
        (u.serial_no for u in state.units if u.unit == msg.unit and u.serial_no), None
    )
    features = _merkmale_features(state, msg, block, names)
    events, cycle, workpiece = _marker_rows(msg, block, time_iso, state.workpiece)
    alarms = _merkmale_alarms(msg, block, time_iso, serial)

    update: dict[str, Any] = {
        "features": features,
        "units": _upsert_unit(state.units, msg.unit, online=True),
    }
    if cycle is not None:
        update["cycle"] = cycle
    if workpiece != state.workpiece:
        update["workpiece"] = workpiece
    if events:
        update["events"] = [*events, *state.events][:EVENT_LIMIT]
    if alarms:
        update["alarms"] = [*alarms, *state.alarms][:ALARM_LIMIT]
    return state.model_copy(update=update)


# ---------------------------------------------------------------------------
# 0x1B MC_GIVESIGNALVERLAUF — canli genlik izi
# ---------------------------------------------------------------------------


def _trace_name(
    state: LiveState, msg: Promos3Message, trace: bodies.SignalTrace, names: dict[int, str] | None
) -> tuple[str, int | None]:
    """Izin adini channelKey'den cozer.

    Rapor channelKey ile SKanalRec maskeleri arasindaki karsiligi kurmadigi
    icin esleme UYDURULMAZ: records.resolve_feature_key ile ayni sirali
    merdiven denenir (maske / maske|0x80 / dogrudan sira). Hicbiri tutmazsa
    anahtarin kendisi gosterilir — yanlis ada sahip bir grafik, adsiz
    grafikten kotudur.
    """
    slots = [
        records.FeatureSlot(index=f.feature_nr or 0, mask=f.mask or 0, name=f.name)
        for f in _slot_features(state, msg.unit)
    ]
    hit = records.resolve_feature_key(trace.channel_key, slots)
    if hit is not None:
        index, _rule = hit
        for f in _slot_features(state, msg.unit):
            if f.feature_nr == index:
                return f.name, f.mask
    from_config = _config_name(trace.channel_key, names)
    if from_config:
        return from_config, trace.channel_key
    return f"Kanal {trace.channel_key}", None


def _apply_trace(
    state: LiveState, msg: Promos3Message, names: dict[int, str] | None
) -> LiveState:
    trace = bodies.decode_signalverlauf(msg)
    if trace is None:
        return state

    fid = trace_feature_id(msg.unit, trace.tool_key, trace.channel_key)
    previous = next((f for f in state.features if f.id == fid), None)
    name, mask = _trace_name(state, msg, trace, names)

    current = float(trace.samples[-1]) if trace.samples else None
    limit_level = previous.limit_level if previous else None
    limits = previous.limits if previous else []
    pct = (
        None if current is None or not limit_level else round(current / limit_level * 100, 1)
    )

    feature = Feature(
        id=fid,
        kind="trace",
        name=name,
        unit_no=msg.unit,
        tool_key=trace.tool_key,
        channel_key=trace.channel_key,
        mask=mask,
        # Ham sayim: olcek carpani YOK (rapor Part 5).
        raw_counts=True,
        uom="",
        samples=[float(v) for v in trace.samples],
        current=current,
        min_value=float(trace.vmin),
        max_value=float(trace.vmax),
        limit_level=limit_level,
        limits=limits,
        pct=pct,
        truncated=trace.truncated,
        confidence=msg.confidence,
    )
    return state.model_copy(
        update={
            "features": _upsert_feature(state.features, feature),
            "units": _upsert_unit(state.units, msg.unit, online=True),
        }
    )


# ---------------------------------------------------------------------------
# Kucuk yapilandirma / durum cevaplari
# ---------------------------------------------------------------------------


def _apply_konfig(state: LiveState, msg: Promos3Message) -> LiveState:
    konfig = bodies.decode_konfig(msg)
    if konfig is None:
        return state
    return state.model_copy(
        update={
            "units": _upsert_unit(
                state.units,
                msg.unit,
                online=True,
                konfig_version=konfig.version,
                channel_amount=konfig.channels,
                mi_sens_amount=konfig.sensors,
            )
        }
    )


def _apply_gtype(state: LiveState, msg: Promos3Message) -> LiveState:
    gtype = bodies.decode_gtype(msg)
    if gtype is None:
        return state
    return state.model_copy(
        update={
            "units": _upsert_unit(
                state.units,
                msg.unit,
                online=True,
                g_type=gtype.g_type,
                g_sub_type=gtype.g_sub_type,
                model=rings.monitor_model(gtype.g_type, gtype.g_sub_type),
                generation=rings.generation_of(gtype.g_type),
                serial_no=str(gtype.serial),
                konfig_version=gtype.version,
            )
        }
    )


def _apply_status(state: LiveState, msg: Promos3Message) -> LiveState:
    status = bodies.decode_status(msg)
    if status is None:
        return state
    return state.model_copy(
        update={
            "cycle": status.cycle,
            "workpiece": status.workpiece,
            "units": _upsert_unit(state.units, msg.unit, online=True),
        }
    )


def _apply_plc(state: LiveState, msg: Promos3Message) -> LiveState:
    plc = bodies.decode_plc(msg)
    if plc is None:
        return state
    return state.model_copy(
        update={"plc_inputs": plc.inputs, "plc_outputs": plc.outputs}
    )


def _apply_alarm(state: LiveState, msg: Promos3Message, time_iso: str) -> LiveState:
    """0x12 alarm kaydi — poll dongusunde YOKTUR, yalniz istek uzerine gelir.

    Salt dinleyici kipte pratikte gorulmez; yine de gelirse dusurulmez.
    """
    rec = bodies.decode_alarm(msg)
    if rec is None or not rec.active:
        return state
    serial = next(
        (u.serial_no for u in state.units if u.unit == msg.unit and u.serial_no), None
    )
    row = Alarm(
        id=f"a-{msg.unit}-{rec.alarm_number}-{time_iso}",
        time=time_iso,
        unit_no=msg.unit,
        device_serial=serial,
        alarm_number=rec.alarm_number,
        channel_nr=None if rec.channel_key == 0xFF else rec.channel_key,
        cycle_nr=rec.cycle,
        slot_name=rings.alarm_slot_name(rec.alarm_number),
        state="active",
        confidence=msg.confidence,
    )
    kept = [a for a in state.alarms if a.id != row.id]
    return state.model_copy(update={"alarms": [row, *kept][:ALARM_LIMIT]})


# ---------------------------------------------------------------------------
# Dagitim
# ---------------------------------------------------------------------------


def apply_promos3_message(
    state: LiveState,
    msg: Promos3Message,
    time_iso: str,
    feature_names: dict[int, str] | None = None,
) -> LiveState:
    """Kimliklendirilmis bir Promos3 cevabini duruma isler.

    Kimliklendirilememis mesaj durumu DEGISTIRMEZ (ayni nesne doner) — ama
    sessizce yok da sayilmaz: hub onu tel istatistiklerine yazar, boylece
    "cerceve akiyor, cozulmuyor" hali ekranda gorunur.
    """
    if not msg.parsed or msg.command is None:
        return state

    if msg.command == CMD_MERKMALE:
        return _apply_merkmale(state, msg, time_iso, feature_names)
    if msg.command == CMD_SIGNALVERLAUF:
        return _apply_trace(state, msg, feature_names)
    if msg.command == CMD_KANAL:
        return _apply_kanal(state, msg, feature_names)
    if msg.command == CMD_KONFIG:
        return _apply_konfig(state, msg)
    if msg.command == CMD_GTYPE:
        return _apply_gtype(state, msg)
    if msg.command == CMD_STATUS:
        return _apply_status(state, msg)
    if msg.command == CMD_PLCVALUES:
        return _apply_plc(state, msg)
    if msg.command == CMD_ALARM:
        return _apply_alarm(state, msg, time_iso)

    return state
