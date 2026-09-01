# PROVIS3 / Prometec Monitoring — Complete Reverse-Engineering Report (v2)

**Target:** PROVIS3 HMI application (Sandvik / Prometec CNC tool-monitoring), 32-bit Qt4 binary
(branded for Mazak, app version **3.1.44.4 / "V3.1.44 HF4"**, DB schema 10).
**Goal:** Recover the device↔HMI communication protocol and data formats so a modern
(64-bit) application can read live sensor telemetry, alarms, configuration and history
**without** the original software, the PEAK/PCAN hardware, or the 32-bit dependency.
**Method:** Ghidra static analysis of the binary + cross-referencing the application's own
exported files (SQLite databases, PMD hex dumps, INI files) + the app's own runtime log.
No Wireshark was required.

> **v2 changelog (this session).** Command dispatch fully resolved (two-level: message
> group + command, ~70 handlers mapped). Runtime log proves **this installation is a
> Provis2 / legacy `MC_` device** (group 1), so the reader must implement the `MC_`
> handlers, not `MC3_`. **Scaling resolved: there is no scaling factor** — amplitude is
> raw 0–255 counts (verified across the measurement DB). Feature names/masks are
> **per-install** (this box: VIBRATION / M131 DEBI / M131BASINC / M08 DEBI), not the
> `SPINDEL/X/Y/Z` example in v1. Added config-derived decoder rings, the dispatcher's
> threading model, and the full measurement-DB schema. Config records re-verified
> byte-for-byte against `1974.txt`.

---

# ═══════════════════════════════════════════════════════════════
# PART 0 — EXECUTIVE SUMMARY (read this first)
# ═══════════════════════════════════════════════════════════════

## 0.1 What was achieved

The **entire receive path** from the monitoring device to decoded values was recovered,
and in v2 both remaining open items (dispatch offset, scaling) were closed:

```
Device → UDP :1789 → 36-byte CAN records → unit routing → per-unit reassembly
       → dispatcher thread → command dispatch (group, command) → payload decode → GUI / SQLite
```

Every stage is tied to a specific, named function in the binary. All configuration record
formats and the historical database schema were decoded and re-verified against the app's
own exported files — a deterministic, proof-grade method that needed no disassembly. The
active protocol generation and the no-scaling result were confirmed from the app's own
runtime log and measurement database.

## 0.2 The single most important structural facts

1. **Transport = CAN-over-UDP through a gateway** at `192.168.222.17:1789`
   (`PROVISsettings.ini [CAN] PCANGateway=1`). Each UDP datagram is a batch of fixed
   **36-byte records**, each carrying one CAN frame (CAN-ID + 8 data bytes). CAN-ID
   selects a unit (`unit = CAN_ID − BaseCanId(1280)`), and the 8-byte payload fragments
   are reassembled per unit into a full Promos3 message.
2. **Endianness:** the CAN transport layer is **BIG-ENDIAN**; the reassembled Promos3
   application payload is **LITTLE-ENDIAN**. Both verified.
3. **Dispatch is two-level.** After reassembly the message object is dispatched by
   `(group, command)`: `group = *(uint32*)(msg+0x00)` and `command = *(uint32*)(msg+0x28)`.
   Group selects the protocol family: **0 = handshake, 1 = `MC_` (legacy Provis2),
   2 = `MC3_` (modern Promos3)**.
4. **This installation is a Provis2 / `MC_` box** (group 1). Proven at runtime — the device
   object is `Promos3DatenProvis2Geraet` and config arrives as `MC_GIVEKONFIG`.
5. **No amplitude scaling factor exists** for this generation. Live samples, stored maxima,
   and limit thresholds all live in one unit: **raw 0–255 counts**.

## 0.3 Confidence levels

- ✅ **VERIFIED** — proven by matching raw hex/DB/runtime, byte-for-byte or value-for-value.
- 🔶 **GHIDRA** — recovered from disassembly; reliable but code-derived.
- ⚠️ **INFERRED** — reasoned from context, not yet byte-confirmed.

## 0.4 Status table (v2)

| Layer | Status | Confidence |
|---|---|---|
| Configuration records (device/channel/cycle/limit) | Complete | ✅ VERIFIED (re-checked vs 1974.txt) |
| Historical config DB schema | Complete | ✅ VERIFIED |
| Measurement DB schema (trend/WP/alarms/log) | Complete | ✅ VERIFIED |
| Gateway/CAN transport framing | Complete | 🔶 GHIDRA (~95%) |
| CAN → message reassembly | Complete | 🔶 GHIDRA (~90%) |
| Command dispatch (group, command → handler) | **Complete** | ✅/🔶 (map recovered; wire offsets pending) |
| Active protocol generation (this box = `MC_`) | **Confirmed** | ✅ VERIFIED (runtime log) |
| Payload body decoders (trace/alarm/event/sensor) | Complete | 🔶 GHIDRA / ✅ |
| Code-meaning tables ("rings") + config rings | Complete | 🔶 GHIDRA / ✅ |
| Scaling (raw→physical) | **Resolved: no factor** | ✅ VERIFIED (DB) |
| Exact message-header wire offsets | Open (non-blocking) | ⚠️ INFERRED |

## 0.5 What remains (small, non-blocking)

1. **Exact wire byte-offsets** of the `[group]`/`[command]`/`[length]` fields in the raw
   reassembled message. The *object* offsets are known (group @+0x00, command @+0x28) and
   the full handler map is recovered; only the raw on-wire positions are unconfirmed.
   Obtain with the app's own capture (`[ErrorManager] LogCANMessage=1`) — **no Wireshark
   needed** — or one UDP capture.
2. **Exact model string** for `(GType 0x44, GSubType 5)` — cosmetic; resolve via
   `[MonitorTypes]` index base against a known unit.

Neither blocks building the reader. All payload formats needed for a read-only telemetry
viewer are in hand.

---

# ═══════════════════════════════════════════════════════════════
# PART 1 — SYSTEM ARCHITECTURE
# ═══════════════════════════════════════════════════════════════

## 1.1 The two communication channels

```
┌──────────────────────┐         CAN-over-UDP          ┌──────────────────────┐
│  Prometec device      │   gateway 192.168.222.17:1789 │                       │
│  (MSL-16 family, 0x44) │◄─────────────────────────────►│    PROVIS3  HMI       │
│  4× PROCUR-S sensors  │        (THIS REPORT)          │    (Promos3 app)      │
└──────────────────────┘                                │                       │
┌──────────────────────┐            TCP 57400           │                       │
│  Mazak NC control     │◄──────  via NTIFDLL.dll  ─────►│                       │
│  (program, tool, part)│      (separate channel)        │                       │
└──────────────────────┘                                └──────────────────────┘
```

- **Prometec / CAN-over-UDP** — sensor telemetry, alarms, config. Covered in full here.
- **Mazak NC** — running program / tool / part count over TCP via the NTIF API
  (`NTIFDLL.dll`, 32-bit). Separate channel; register map in `NCaccess.ini`
  (`Port=57400`, `RegPNameSet=8508-1`, etc.), credentials in `mazak.lic`. Noted for
  completeness, not the focus of this report.

## 1.2 The reference installation (verified from log + DB)

Two monitor units on one Mazak, offline LAN, over the UDP gateway:

```
Unit 1:  SNr 10659   Type 68 (0x44)  SubType 5   PLC inputs 4, outputs 1
Unit 2:  SNr 10663   Type 68 (0x44)  SubType 5   PLC inputs 4, outputs 1
Device class (runtime): Promos3DatenProvis2Geraet   ← Provis2 / MC_ generation
Firmware: Rtm_V14.5.H86 (RTM v14.5, Intel-HEX)
Gateway:  192.168.222.17:1789  (PCANGateway=1, BaseCanIDTransfer=1280, BusID=512)
Ethernet streaming: [Ethernet] Active=0 (disabled; would-be streaming port 2789)
```

## 1.3 The complete receive path (device → decoded values)

```
 (1) UDP datagram arrives on port 1789  (batch of fixed 36-byte records)
        ▼
 (2) Scan4CANmsg [FUN_00507760] 🔶
        split into 36-byte records (trim remainder from FRONT); each = ONE CAN frame:
          +0x15     LEN (0..8);  +0x1A..1B CAN-ID (uint16 BIG-ENDIAN hi,lo)
          +0x1C..23 8 DATA bytes;  +0x00..14 gateway header (discarded)
        ▼
 (3) Unit routing 🔶       unit = CAN_ID − BaseCanId(1280); ID below base → dropped
        ▼
 (4) unitBuffer_appendCanData [FUN_006823b0] 🔶
        append 8 data bytes; two sub-streams (+0x08 header/len, +0x0c data);
        first frame restarts a timeout timer
        ▼
 (5) unitBuffer_hasCompleteMessage [FUN_00682830] 🔶
        read length field from buffer header; complete when received ≥ expected
        ▼
 (6) Completed message enqueued to the dispatcher thread (see 1.5)
        Promos3 payload is LITTLE-ENDIAN
        ▼
 (7) Command_Dispatch_Switch [FUN_004125d0] 🔶 (this = Promos3DatenInstanz singleton)
        group   = *(uint32*)(msg+0x00)   (via FUN_00436470)
        command = *(uint32*)(msg+0x28)
        switch(group){ 0:handshake  1:MC_  2:MC3_ } → switch(command) → handler
        ▼
 (8) bearbeite_Kom_NN → resolveTarget → decode body → emit signals → GUI / SQLite 🔶/✅
```

**Alternate source, identical downstream:** `CanInterface_pollMessages` (`FUN_005083e0`)
branches on transport mode — UDP gateway (above) vs real PEAK-CAN hardware (`CAN_Read`
from `CanApi2.dll`). Both feed the SAME unit buffers and completion logic. On this machine
`PCANGateway=1`, so the gateway path is used; the equivalence proves the gateway decode
matches hardware behavior.

## 1.4 GUI-side signal graph (how data reaches the screen)

From `Promos3MainWindow_setupUi` (`FUN_0043dc70`), key wiring:

| Emitter | Signal | → MainWindow slot |
|---|---|---|
| `Promos3DatenInstanz` (`FUN_00408a60`) | `NewMonitor(QString)` | `ConnectMonitorSignals` |
| `Promos3DatenInstanz` | `CurrentMonDisconnected()` | `OnMonitorDisconnected` |
| `Promos3DatenInstanz` | `selectedMonitorChanged(...)` | `updateAlarmBox` |
| NC comm (`FUN_00433a40`) | `showNCmsg(QString)` | `showMsgFromNC` |
| Button bar (`FUN_004f5fc0`) | `ButtonClicked(int)` | `On_PushButtonClicked` |

The Ethernet interface (`Promos3EthInterface`, `FUN_004fb1c0`) wires streaming/handshake
signals; disabled on this machine (`[Ethernet] Active=0`).

## 1.5 Concurrency model (dispatcher thread) 🔶

Dispatch runs on a dedicated worker thread, **not** the socket thread:

- **`Promos3KommandoVerteilerThread`** ("command distributor thread"). Its `run()` is
  `FUN_0042db50` (`setObjectName("KommandoThread")`).
- The thread drains two queues under a mutex + wait-condition
  (mutex @+0x14, wake flag @+0x1e, stop flag @+0x1f, `QWaitCondition` @+0x24):
  - **Queue A @+0x0c** — completed messages; each dispatched via `FUN_004152c0` →
    `Command_Dispatch_Switch_004125d0(Promos3DatenInstanz, msg)`.
  - **Queue B @+0x08** — a secondary stream → `FUN_00415370` (not needed for a reader).
- **Ownership:** the dispatch switch frees each message (`operator_delete`) after handling.
  The producer (receive/reassembly) hands off ownership by enqueuing.

For a clean reader you need not replicate this threading — you can dispatch inline — but it
explains the mutex ("Vorverarbeitung_Kom") taken inside `resolveTarget`.

---

# ═══════════════════════════════════════════════════════════════
# PART 2 — THE WIRE PROTOCOL (transport)
# ═══════════════════════════════════════════════════════════════

## 2.1 Endianness (verified)

- **CAN transport = BIG-ENDIAN.** CAN-ID read as `(buf[0x1A]<<8) | buf[0x1B]`
  (`CONCAT11(hi,lo)` in the decompiler). ✅🔶
- **Promos3 application payload = LITTLE-ENDIAN.** Proven by config record:
  `ReduzLim = 6612 = 0x19D4` stored on disk as bytes `D4 19`. ✅ (re-confirmed in 1974.txt)

## 2.2 The 36-byte gateway record

```c
#pragma pack(push,1)
typedef struct {                 // one CAN frame as delivered over UDP
    uint8_t  gw_header[0x15];    // +0x00  gateway timestamp/status (discarded)
    uint8_t  len;                // +0x15  CAN data length (0..8)
    uint8_t  gap[4];             // +0x16
    uint8_t  can_id_hi;          // +0x1A  CAN ID high byte  (BIG-ENDIAN)
    uint8_t  can_id_lo;          // +0x1B  CAN ID low byte
    uint8_t  data[8];            // +0x1C  the 8 CAN data bytes (payload fragment)
} GatewayCanRecord;              // 0x24 = 36 bytes
#pragma pack(pop)
// unit = ((can_id_hi<<8)|can_id_lo) - 1280
```

## 2.3 Reassembled CAN message (14-byte internal form = PEAK TPCANMsg)

```c
typedef struct { uint32_t ID; uint8_t MSGTYPE; uint8_t LEN; uint8_t DATA[8]; } TPCANMsg;
// gateway buf[0x1A:0x1B](BE)→ID; buf[0x15]→LEN; buf[0x1C:0x23]→DATA[0:8]
```

## 2.4 Reassembly and the Promos3 message — DISPATCH MODEL (resolved in v2)

Per-unit buffer accumulates `DATA[]` fragments in arrival order; a length field in the
header governs completion (`unitBuffer_hasCompleteMessage`). The completed message becomes
a parsed message object that the dispatcher routes on **two** fields:

```
group   = *(uint32_t*)(msg + 0x00)      // via FUN_00436470 (returns *msg)
command = *(uint32_t*)(msg + 0x28)      // the value switched on
```

- `group` selects the protocol family: **0 = handshake, 1 = `MC_` (legacy Provis2),
  2 = `MC3_` (modern Promos3)**.
- The same command number means different things per group (e.g. command `0x1B` =
  `MC_GIVESIGNALVERLAUF` in group 1 but `MC3_SET_OUTPUTS` in group 2).
- These are **object** offsets (fields set by the message parser upstream). The exact
  **wire** byte positions are the one remaining ⚠️ item (§0.5); obtain via
  `LogCANMessage=1` or a capture.

**Leaf routing pattern (uniform across handlers):**
```
handler(msg):
    packet_getStation(msg)                 // sender unit key
    unit = resolveTarget(FUN_00409ca0)     // look up unit object (mutex "Vorverarbeitung_Kom")
    if unit && getTargetType(FUN_0047fde0)==GEN:   // GEN==1 for MC_, ==2 for MC3_
        worker(msg)                        // the actual byte-parser
```
`getTargetType` returns the unit's generation (`*(uint32*)(unit+0x0c)`): **1 = Provis2/`MC_`,
2 = Promos3/`MC3_`**. On this box it is **1**.

## 2.5 Reference network setup (this machine)

```
Devices 10659 / 10663:  GType 0x44 (MSL-16 family), 1 channel, 4× PROCUR-S sensors
Gateway:  192.168.222.17:1789  PCANGateway=1  BaseCanIDTransfer=1280  BusID=512
Ethernet streaming: Active=0 (disabled), would-be port 2789
Mazak NC: TCP 57400 via NTIFDLL
```

---

# ═══════════════════════════════════════════════════════════════
# PART 3 — COMMAND DISPATCH (the full map)   🔶/✅
# ═══════════════════════════════════════════════════════════════

German terms: `Kom`=Kommando (command); `bearbeite`=process/parse; `Sende`=send;
`Geraet`=device; `Merkmal`=feature; `Zyklus`=cycle; `Signalverlauf`=signal trace;
`Grenz`=limit; `Konfig`=configuration. `MC_*`=Provis2 generation; `MC3_*`=Promos3 generation.

Dispatch table entry format below: `command (hex) → handler FUN_ → name/notes`.
`Command_Dispatch_Switch` = `FUN_004125d0`.

## 3.1 THIS BOX USES GROUP 1 (`MC_`) — implement these

Switch on `msg+0x28` when `group==1` / `getTargetType==1`. Confirmed live: cmd `0x06`
logged `bearbeite_Kom_06_MC_GIVEKONFIG: Version 229 Channels 1 Sensors 4`. Names known
from strings/log/xref; the rest are located wrappers whose worker holds the format.

| cmd | handler | name / notes |
|---|---|---|
| 0x01 | FUN_0040ab10 | |
| 0x02 | FUN_00412290 | (shared with group-0 cmd 2) |
| 0x04 | FUN_0040acb0 | |
| 0x05 | FUN_0040ad00 | |
| **0x06** | **FUN_0040a8f0** | **MC_GIVEKONFIG** — device config; logs "Version N Channels C Sensors S" ✅ |
| 0x08 | FUN_0040a950 | |
| 0x0a | FUN_0040a9a0 | |
| 0x0c, 0x32 | FUN_0040a9f0 | (shared) |
| 0x0d | FUN_0040aa40 | sets selected monitor if station unknown |
| 0x0e | FUN_0040ab70 | |
| 0x0f | FUN_0040abc0 | |
| 0x12 | FUN_0040ac60 | |
| 0x14 | FUN_0040b0c0 | |
| 0x15 | (qDebug only) | **MC_PRESSEDKEYS** — logs, no decode |
| 0x16 | FUN_0040ad50 | |
| 0x18 | FUN_0040ada0 | |
| 0x1a | FUN_0040aee0 | |
| **0x1b** | **FUN_0040af30** | **MC_GIVESIGNALVERLAUF** → bearbeite_Kom_27 (FUN_004d1b70) → decodeSignalTrace_B. THE live amplitude trace ✅ |
| 0x1c | FUN_0040adf0 | |
| 0x1f | FUN_0040ae40 | |
| 0x21 | FUN_0040ae90 | |
| 0x23 | FUN_0040af80 | |
| 0x24 | FUN_0040afd0 | |
| 0x25 | FUN_0040ac10 | |
| 0x27 | FUN_0040b020 | |
| 0x28 | FUN_0040b070 | |
| 0x29 | FUN_0040b110 | (worker FUN_004dc3e0: parse record, timestamp, store, GUI update) |
| 0x2a | FUN_0040b160 | |
| 0x2b | FUN_0040b1b0 | |
| 0x2c | FUN_0040b200 | |
| 0x2d | FUN_0040b250 | |
| 0x30 | FUN_0040b2a0 | |
| 0x33 | FUN_0040b2f0 | |
| 0x34 | FUN_0040b340 | |
| 0x35 | FUN_0040b390 | |
| 0x36 | FUN_0040b3e0 | |
| 0x37, 0x39 | FUN_0040b480 | (shared) |
| 0x38 | FUN_0040b430 | |
| 0x3c | FUN_0040b4d0 | |
| default | drop | |

## 3.2 GROUP 2 (`MC3_`) — for completeness (NOT used by this box)

Switch on `msg+0x28` when `group==2`. Command numbers match the v1 NN table; anchor proof:
cmd `0x0F → FUN_0040c400` = the alarm dispatcher (`bearbeite_Kom_15`).

| cmd | handler | name / notes |
|---|---|---|
| 0x03 | FUN_0040b830 | MC3_GET_CB_VERSION |
| 0x04 | FUN_0040b880 | MC3_SENSOR_INFO → bearbeite_Kom_04 (FUN_004bc090) |
| 0x05 | FUN_0040b8d0 | MC3_MERKMAL_INFO |
| 0x06 | FUN_0040b920 | MC3_GERAETEREC |
| 0x07 | FUN_0040b9e0 | MC3_SET_STREAMING |
| 0x08 | FUN_0040c1d0(msg,0) | MC3_LIMIT_INFO |
| 0x09 | FUN_0040c220(msg,0) | MC3_CYCLE_INFO |
| 0x0a | FUN_0040c270 | |
| 0x0b | FUN_0040c2c0 | (= 0x15) |
| 0x0c | FUN_0040c310 | (= 0x16) |
| 0x0d | FUN_0040c360 | |
| 0x0e | FUN_0040c3b0 | |
| **0x0f** | **FUN_0040c400** | **MC3_ALARM** → bearbeite_Kom_15 (FUN_004b5ba0) — anchor |
| **0x10** | **FUN_0040c450** | **MC3_EVENT** → bearbeite_Kom_16 (FUN_004b6580) — decoded, §4.4 |
| **0x11** | **FUN_0040c5e0** | **MC3_SENSOR_VFAKT — STUB** (worker FUN_004acf40 = `return p!=0`); no runtime scaling |
| 0x13 | FUN_0040c220(msg,1) | CYCLE_INFO variant |
| 0x14 | FUN_0040c1d0(msg,1) | LIMIT_INFO variant |
| 0x15 | FUN_0040c2c0 | (= 0x0b) |
| 0x16 | FUN_0040c310 | (= 0x0c) |
| 0x18 | FUN_0040c4a0 | MC3_SYSTEM_MODE |
| 0x1a | FUN_0040c4f0 | MC3_PATTERN_INFO |
| **0x1b** | **FUN_0040c540** | **MC3_SET_OUTPUTS** → bearbeite_Kom_27 (FUN_004b9150); "Outputs successfully set" — NOT a trace |
| 0x1c | FUN_0040c590 | |
| 0x3a | FUN_0040c680 | |
| 0x99 | FUN_0040c630 | |
| default | drop | |

**Flag-paired workers** (bool selects a variant): `0x08↔0x14` (FUN_0040c1d0),
`0x09↔0x13` (FUN_0040c220).

## 3.3 GROUP 0 — handshake / new unit

Switch on `msg+0x28` when `group==0`.
- cmd 1: **MC_GIVEGTYPE** — device-type handshake (if station unknown, the app *sends* a
  `MC_GIVEGTYPE` request).
- cmd 2: → FUN_00412290 (shared with group 1 cmd 2).

## 3.4 Why you don't decode every handler

Every case is the same 4-line routing wrapper (§2.4); it carries **no format information** —
only the *worker* it calls does. And you only need a worker if your reader consumes that
feature. A read-only telemetry viewer needs a handful (config, signal trace, alarm, and —
if desired — event); the rest are control-writes or config already in SQLite.

---

# ═══════════════════════════════════════════════════════════════
# PART 4 — DECODED PAYLOAD BODIES
# ═══════════════════════════════════════════════════════════════

All offsets relative to the START OF THE BODY (after the message header).
All multi-byte values LITTLE-ENDIAN. 🔶 GHIDRA except where marked ✅.

## 4.1 SIGNALVERLAUF — live amplitude trace (THE plotted bars)

This box: group-1 cmd `0x1B` `MC_GIVESIGNALVERLAUF` (`FUN_0040af30` → `bearbeite_Kom_27`
`FUN_004d1b70` → `decodeSignalTrace_B` `FUN_00497d30`). Header read at body start:

```c
#pragma pack(push,1)
typedef struct {
    uint8_t  toolKey;      // +0x00  routing: which tool/sensor (map key1)
    uint8_t  channelKey;   // +0x01  routing: which feature/channel (map key2)
    uint8_t  paramA;       // +0x02
    uint8_t  flag;         // +0x03
    uint8_t  mode;         // +0x04  (1 → variant A decodeSignalTrace_A, else B)
    int16_t  samples[125]; // +0x05  ← 125 × int16 LE  ← THE PLOTTED VALUES (raw 0..255)
    uint16_t trailer;      // +0xFF  tag/count
} SignalVerlaufPacket;     // body ≈ 255 bytes
#pragma pack(pop)
```

- Sample count **125** (loop `0x7d`); guard: body length must be `> 0xFB` (251).
- Samples are RAW COUNTS in 0..255. **No scaling** (see Part 5). Display axis 0..300 is
  headroom; "%" is raw relative to the feature's limit Level (Part 5).
- Endianness verified by loopback (LE ramp read back 0..248; BE produced garbage).
- The DB stores only enveloped history (Part 10), so the live waveform exists **only on the
  wire** — this decoder is the sole source for real-time traces.

## 4.2 ALARM — status / alarm track

`MC3_ALARM`: group-2 cmd `0x0F` (`bearbeite_Kom_15` `FUN_004b5ba0`). The `MC_` box uses the
group-1 alarm path; the record semantics (feature + limit + status) are the same and match
the stored `Alarms` table (Part 10).

```
sub-command byte first:  1 = alarm data, 8 = state marker, 0x0A = quit/acknowledge
then: u16 alarmId        (0xFFFF = clear all)
then repeating entries, each: u16 alarmNumber, then a 31-byte record:
    rec+0x00 u16 entryId
    rec+0x02 u16 status      ← low byte = ToolStatus code (Part 6.1)
    rec+0x1D u8  channelKey  (0xFF = none)
```
qDebug tag: `" Received Alarm: %d Status: %d"`. Stored form → `Alarms` table columns
`ChannelNr, CycleNr, FeatureNr, LimitNr, Ack, TimeOffset`.

## 4.3 SENSOR_INFO — sensor descriptor (MC3_)

`MC3_SENSOR_INFO`: group-2 cmd `0x04` (`bearbeite_Kom_04` `FUN_004bc090`), record via
`stream_readRecord` (0x1F = 31 bytes):

```c
#pragma pack(push,1)
typedef struct {
    uint8_t  reserved0[4];  uint16_t sensorId;    // +0x04 map key "ID: 0x%04X"
    uint8_t  serialC1, serialC2; uint32_t serialNum;
    uint8_t  gap0C[4];
    uint8_t  sensChannels;  uint8_t  featureCount;
    uint8_t  featureChannel; uint8_t formulaCount;
    uint32_t formulaAvail;  uint32_t swSerial;
    uint8_t  type;          // +0x1C SensorType (0x80=PROCUR-S) (Part 6.2)
    uint8_t  subType;       uint8_t hwSerial;
} SensorInfoRecord;         // ≈ 31 bytes
#pragma pack(pop)
```
DB columns (`DB_insertSensorRow` FUN_005befb0): Date, Rec_Valid, Status, SensorID, Serial,
AktMod_Ref, SensChannels, FeatureCount, FeatureChannel, FormulaCount, FormulaAvailable,
SWserial, Type, SubType, HWserial, Calibration.

## 4.4 EVENT — event log (MC3_, decoded this session)

`MC3_EVENT`: group-2 cmd `0x10` (`bearbeite_Kom_16` `FUN_004b6580`):

```
subcommand byte:  1 = event data
                  8 = state/end marker (next byte==1 → finalize; else FUN_00642ff0)
                  other → error "Wrong subcommand received: %1"
[optional u16 0xFFFF marker, skipped]
repeat while >=2 bytes remain:
    u16   eventNumber
    10-byte record:
        +0x00..+0x08  9 bytes event payload (EventCode per Part 6.5, params/time)
        +0x09         u8 channelKey (0xFF = none)
    → per-channel map @ this+0xC4 (SAME map as alarms) via FUN_00484ec0
if nothing selected: ack via FUN_004b5830(station, 1, 0xFFFF, 0)
```
(Documented for completeness. This box is `MC_`, so its events arrive via the group-1 path;
the log shows only UI "EventList" navigation, no live event packets during capture.)

---

# ═══════════════════════════════════════════════════════════════
# PART 5 — SCALING (raw → physical)   ✅ RESOLVED: NO FACTOR
# ═══════════════════════════════════════════════════════════════

**There is no per-sensor amplitude scaling factor for this device generation.** Live
samples, stored maxima, and alarm thresholds all live in one unit: **raw 0–255 counts.**
Proven from the databases:

- `Features.Feat_Max` (config DB): raw, max exactly **255** (602/729 rows saturated at 255).
- Measurement DB `Trend_C01_F0x.Max_Val` and `WP_*.Max_S0x` envelopes: global max **255**,
  never higher, across all workpieces.
- `Limits.Level` thresholds: **20..170** — the SAME raw units as the amplitude.
- `Sensors.Calibration`: `'0'` on every row (unused).
- The `MC3_SENSOR_VFAKT` handler (cmd 0x11) is a **stub** — no runtime scaling extraction.
- `SFactors.ini` does **not** exist on this install and the app runs fine without it.

Therefore:
- **Reader rule: plot the raw sample directly (0–255).**
- The on-screen "%" is **raw relative to the feature's limit Level**: `% = raw / limitLevel
  × 100` (e.g., raw 204 vs Level 170 → 120%). No per-sensor constant.
- ⚠️ Do not confuse amplitude with `Trend.Work_Val` (range 0..301): that is a cycle
  position / work-window quantity, not a scaled amplitude — it is what the "0–300 axis" in
  v1 actually referred to.
- `Cycle_Sensors.Gain` (0..126) is the sensor-side **hardware amplifier setting**, a device
  config — the app does not apply it at display time.

---

# ═══════════════════════════════════════════════════════════════
# PART 6 — CODE-MEANING TABLES ("decoder rings")   🔶/✅
# ═══════════════════════════════════════════════════════════════

## 6.1 ToolStatus (status byte 0x00–0x0F) — member this+0x44  🔶
```
0=empty        1=Overload      2=Underload     3=Contact
4=Missing      5=Work Over     6=Work Under    7=Cut start
8=Cut end      9=Dynam. upper  A=Dynam. lower  B=Pattern upper
C=Pattern lower D=ACF contact  E=cutdetect contact  F=Tool wear
```

## 6.2 SensorType — member this+0x4c  🔶
```
01=PA-Box 03=VB-Box 10=PA 111 11=PA 122 S1 13=PA 122 S2 14=PA 211 15=PA 221
16=DU2A211 20=EP 111 24=EP 211 30=VBI 211 31=AE 211 38=VBI RTCM
80=PROCUR-S 81=PROCUR-I 82=PROCUR-B 83=ACFeed 84=ACfeed OVR
90=Position 91=Temperature A0=MI32bit FF=Unknown
```

## 6.3 ChannelStatus (0–7) 🔶
`0=Not 1=OK 2=Wrong 3=Later 5=Reset 6=Suppressed 7=Alarm missing`

## 6.4 AccessLevel 🔶
`00=Operator 04=Setter 05=Administrator 06=Machine manufacturer 63=SERVICE`

## 6.5 EventCode (selected) 🔶
`01=RTC Set 02=Cycle settings change 03=Limit change 04=Cycle mode change
06=List cleared 07=Device renamed 09=Sensor change 14=Reboot FF=Empty`

## 6.6 Config-derived rings (from PROVISsettings.ini)  ✅ VERIFIED (app config)

**Model resolution — `[MonitorTypes]`:** GType picks the family row; GSubType indexes it.
```
0x44 (this box's -16 family):
  [0]MDL5081-16 [1]MDL5082-16 [2]MDL5051-16 [3]MDL5052-16
  [4]MSL5081-16 [5]MSL5082-16 [6]MSL5051-16 [7]MSL5052-16
  [8]MSL5074-16 [9]MSL3031-16 [10]MSL3032-16 [11]MSL3011-16
  [12]MSL3012-16 [13]MDL5031-16 [14]MDL5032-16 [15]MSL5034-16
Provis2 families: 0x30/0x38/0x39/0x40/0x41/0x43/0x48
Promos3 families: 0x70 CompactBox, 0x71 SensorBox, 0x80 XT-Monitor
```
Index base (0- vs 1-based) unpinned: (0x44, SubType 5) → MSL5081-16 (1-based) or
MSL5082-16 (0-based). Cosmetic.

**Alarm slot → label — `[AlarmNames]`** (operator-configurable):
`1=Collision 2=Break 3=Wearout 4=Missing 5=Coolant` (6..8 empty)

**Dynamic sensitivity — `[DynnamicSensibility*]`** (behind ToolStatus 0x09/0x0A):
`Top: L0=12 L1=21 L2=27 L3=36 L4=45   Bottom: L0=9 L1=15 L2=21 L3=27 L4=36`

---

# ═══════════════════════════════════════════════════════════════
# PART 7 — CONFIGURATION RECORDS (at rest)   ✅ VERIFIED
# ═══════════════════════════════════════════════════════════════

Decoded by cross-referencing raw PMD hex (`1974.txt`, `exVL2-*.txt`) against the SQLite
config DBs (`Provis-10659`, `Provis-10663`) column-by-column. Re-verified this session
against `1974.txt` — every [VERIFIED] field's hex byte equals the database value.

## 7.1 SGeraetRec — device record (66 bytes) — table: Devices

Verified from `1974.txt` (`44 05 01 04 …`):

| Offset | Field | Value | Verified |
|---|---|---|---|
| +0x00 | GType | 0x44 (68, MSL-16 family) | ✅ |
| +0x01 | GSubType | 5 | ✅ |
| +0x02 | Channel_Amount | 1 | ✅ |
| +0x03 | MiSens_Amount | 4 | ✅ |
| +0x1A..0x21 | MiSensType[8] | 0x80 (PROCUR-S) each | ✅ |
| +0x22 | SampleDiv | 1 | ✅ |
| +0x26..0x27 | ReduzLim | 0x19D4 = 6612 (LE: D4 19) | ✅ |

```c
#pragma pack(push,1)
typedef struct {
    uint8_t  GType, GSubType, Channel_Amount, MiSens_Amount; // +0x00 VERIFIED
    uint8_t  flags04[16];   // +0x04 INFERRED (CDR/Setup/PLC_Konf/Sync/Polarity/ZaSensorType..)
    uint16_t date_or_crc;   // +0x14 INFERRED (1974.txt: 29 A7)
    uint8_t  za_mi_area[4]; // +0x16 INFERRED (1974.txt: 30 14 14 14)
    uint8_t  MiSensType[8]; // +0x1A VERIFIED (0x80)
    uint8_t  SampleDiv;     // +0x22 VERIFIED
    uint8_t  pad23[3];      // +0x23
    uint16_t ReduzLim;      // +0x26 VERIFIED
    uint8_t  tail[66-0x28];
} SGeraetRec;               // 66 bytes
#pragma pack(pop)
```

## 7.2 SKanalRecV40 — channel record (144 bytes) — table: Channels

Verified from `1974.txt`:

| Offset | Field | Value | Verified |
|---|---|---|---|
| +0x00 | PLC_Type | 0x10 (16) | ✅ |
| +0x01 | PLC_Version | 0x20 (32) | ✅ |
| +0x02 | Channel_Num | 1 | ✅ |
| +0x10..0x13 | CDRLim[4] | 0xAA (170) each | ✅ |
| +0x4D | features[4] | 4× 12-byte slots | ✅ |

### ⚠️ CORRECTION — feature names/masks are PER-INSTALL (read them; don't hardcode)

The feature-name block at +0x4D is 4 fixed 12-byte slots, each `[1 mask byte][11-byte
NUL-terminated ASCII]`. **v1 showed `SPINDEL/X AXIS/Y AXIS/Z AXIS` with masks
`0x81/0x82/0x84/0x88` — that was a different machine's example.** THIS box (`1974.txt`) has:

```
mask 0x01  "VIBRATION"
mask 0x02  "M131 DEBI"      (debi = flow rate)
mask 0x04  "M131BASINC"     (basınç = pressure)
mask 0x08  "M08 DEBI"
```

Reader rules:
- **Read feature names dynamically from SKanalRec** — they are operator-assigned per machine.
- The **low nibble** (`0x01/0x02/0x04/0x08`) is the feature-select bit; the **high `0x80`
  bit is a separate flag** (set in v1's example, clear here). Match on `mask & 0x0F` (or the
  bit position), treat `0x80` as a flag — do NOT key on `mask == 0x81`.

```c
typedef struct { uint8_t mask; char name[11]; } SKanalFeature; // 12 bytes
```

## 7.3 SGrenzRec / SHardwareRec / SZykRecV4802

- **SGrenzRec** (limits, ~14 bytes) — `1974.txt`: `d9 01 04 04 04 00 04 fa fc 07 08 32 08 fa`.
  Maps to table `Limits` (Limtype, Level, Feat_Num, …). Levels seen: 20/35/50/70/115/140/152/170.
- **SHardwareRec** (~46 bytes) — `1974.txt`: `02 01 02 03 04 …`. Table `Hardware`
  (Board_Vers, Del_Date1..4).
- **SZykRecV4802** (cycle, 170 bytes) — 9 records in `1974.txt`; size 170 confirmed. Maps
  to table `Cycles` (Name, Duration, MonIndex, Sensor_Ref1..4, Feature_Ref1..4,
  Limit_Ref1..8, PLCRep_Ref1..8, …) and `Cycle_Sensors` (Sens_Param1..3, Gain, Meantime,
  Komp_Start).

## 7.4 Config DB table catalog (`Provis-10663`)  ✅

`Devices, Channels, Cycles, Cycle_Sensors, Sensors, Sensor_Map, SensorLink, Features,
Limits, Constraints, Hardware, NCProgram, Program, CycleDsp, PLCReport, Version, Source`
plus job-numbered tables (`1970/1971/6136/…`). App version 3.1.44.4, schema 10.

Selected schemas:
- `Devices(GType,GSubType,Channel_Amount,MiSens_Amount,CDR,Setup,PLC_Konf,…,SensorType_1..4,
  MiSensType_1..8,SampleDiv,…,ReduzLim,…,WithACfeed)`
- `Channels(PLC_Type,PLC_Version,…,CDRLim1..4,Sens_Link1..4,MDL_Period,MDL_Time,…)`
- `Sensors(Sensor_Num,SensDat_1..14,Calibration)` — Calibration `'0'` (unused)
- `Features(Feat_Num,Feat_Max,Work_Teach,Work_Start,Work_End)` — Feat_Max raw 0..255
- `Limits(Limtype,Level,Feat_Num,Response_Time,Act_Start,Act_End,Act_Mode,Pattern_Ref)`
- `Cycle_Sensors(Sens_Param1..3,Gain,Meantime,Komp_Start)`

---

# ═══════════════════════════════════════════════════════════════
# PART 8 — FUNCTION REFERENCE (receive/decode path)   🔶
# ═══════════════════════════════════════════════════════════════

Names are analysis labels; verify before committing to a build.

## 8.1 Transport / gateway
| Address | Name | Purpose |
|---|---|---|
| FUN_00507760 | Scan4CANmsg | Split UDP datagram into 36-byte CAN records; extract CAN-ID (BE @+0x1A), LEN (@+0x15), 8 data bytes (@+0x1C); route by unit. |
| FUN_005083e0 | CanInterface_pollMessages | Branches gateway (→Scan4CANmsg) vs PEAK (CAN_Read); identical downstream. |
| FUN_00504ab0 | Promos3CanInterface_init | UDP-gateway mode binds QUdpSocket; else loads CanApi2.dll (PEAK). |

## 8.2 Reassembly (per-unit buffering)
| Address | Name | Purpose |
|---|---|---|
| FUN_006823b0 | unitBuffer_appendCanData | Append 8 data bytes; sub-streams +0x08 header/len, +0x0c data; first frame restarts timeout. |
| FUN_00682830 | unitBuffer_hasCompleteMessage | Complete when received ≥ expected (length field in header). |
| FUN_00506160 | unitBuffer_remove | Disconnect cleanup. |

## 8.3 Dispatch + threading
| Address | Name | Purpose |
|---|---|---|
| FUN_004125d0 | Command_Dispatch_Switch | 2-level dispatch: group=*(msg+0x00), command=*(msg+0x28); frees msg after handling. |
| FUN_00436470 | getMessageGroup | `return *msg` (group at obj+0x00). |
| FUN_004152c0 | dispatch_trampoline | `Command_Dispatch_Switch(Promos3DatenInstanz, msg)`. |
| FUN_0042db50 | KommandoThread_run | Dispatcher thread run() loop; drains queues +0x08/+0x0c under mutex+condvar. |
| FUN_00409ca0 | resolveTarget | Resolve unit object by station (mutex "Vorverarbeitung_Kom"). |
| FUN_0047fde0 | getTargetType | `return *(unit+0x0c)` — unit generation (1=MC_, 2=MC3_). |
| FUN_0040c400 | dispatch_alarmIfType2 | Leaf → bearbeite_Kom_15 (MC3_ALARM). |

## 8.4 Command decoders (workers)
| Address | Name | Purpose |
|---|---|---|
| FUN_0040af30 | (MC_) GIVESIGNALVERLAUF wrapper | → bearbeite_Kom_27. |
| FUN_004d1b70 | bearbeite_Kom_27 | Signal-trace header (5B) → decodeSignalTrace_A/B. |
| FUN_00497d30 | decodeSignalTrace_B | 125×int16 LE amplitude → QList<short>. THE amplitude decoder. |
| FUN_00496920 | decodeSignalTrace_A | Amplitude variant (mode==1). |
| FUN_004bc090 | bearbeite_Kom_04 (MC3_SENSOR_INFO) | 31-byte records keyed by u16 sensorId → sensor map + SQLite. |
| FUN_004b5ba0 | bearbeite_Kom_15 (MC3_ALARM) | Alarm/status; entries [u16 alarmNo][31B rec]; map @+0xC4. |
| FUN_004b6580 | bearbeite_Kom_16 (MC3_EVENT) | Event log (§4.4); map @+0xC4. |
| FUN_004b9150 | bearbeite_Kom_27 (MC3_SET_OUTPUTS) | Output-set ack ("Outputs successfully set"). |
| FUN_004acf40 | (MC3_SENSOR_VFAKT worker) | STUB (`return p!=0`). |
| FUN_004dc3e0 | (MC_ cmd 0x29 worker) | Parse record, timestamp, store, GUI update. |

## 8.5 DB / INI / error subsystems
| Address | Name | Purpose |
|---|---|---|
| FUN_005befb0 | DB_insertSensorRow | INSERT sensor row; column list = SensorInfoRecord layout. |
| FUN_004236f0 | initStatusTables | Build decoder rings (ToolStatus@+0x44, SensorType@+0x4c, …). |
| FUN_00437f50 | ini_readInt | INI integer read (tryLock 3000ms → ErrorManager on timeout). |
| FUN_004041c0 | ErrorManager_log | App-wide log entry (category, level, msg). |
| FUN_00403650 | ErrorManager_initLogFile | Opens <settingsDir><LogFile>; "LOG START at: …". |

## 8.6 Central objects (singletons)
| Global | Object | Ctor |
|---|---|---|
| DAT_00a1a244 | Promos3DatenInstanz (central data hub; dispatch `this`) | FUN_00408440 |
| DAT_00a1a840 | NCcommThread | FUN_00433640 |
| DAT_00a19ffc | Promos3ErrorManager | FUN_004040f0 |
| DAT_00a1a1cc | Promos3IniFile | (Promos3IniFile_ctor) |
| DAT_00a1b1c0 | Promos3LicenseValidator | FUN_004aae70 |

*(The full low-level Qt-container/QString plumbing catalog from v1 is unchanged and omitted
here for brevity; it is name-and-forget and not needed to build the reader.)*

---

# ═══════════════════════════════════════════════════════════════
# PART 9 — KEY CODE SNIPPETS (annotated)   🔶
# ═══════════════════════════════════════════════════════════════

## 9.1 Gateway datagram split — Scan4CANmsg (FUN_00507760)
```c
if (0x23 < datagramSize) {                 // need > 35 bytes
    QByteArray::remove(0, size % 0x24);    // trim leftover from FRONT
    while (remaining > 0x23) {              // each whole 36-byte record
        *puVar7   = CONCAT11(at(0x1A),at(0x1B));  // ID = (hi<<8)|lo ← BIG-ENDIAN
        *(puVar7+5)=at(0x15);                     // LEN
        *(puVar7+6)=*(u32*)(data+0x1C);           // DATA[0:4]
        *(puVar7+10)=*(u32*)(data+0x20);          // DATA[4:8]
        QByteArray::remove(0, 0x24);              // consume 36 bytes
    }
}
```

## 9.2 The dispatch skeleton — Command_Dispatch_Switch (FUN_004125d0)
```c
group = *(u32*)(msg + 0x00);                 // via FUN_00436470
switch (group) {
  case 0: /* handshake: cmd 1 = MC_GIVEGTYPE, cmd 2 = FUN_00412290 */ break;
  case 1: switch (*(u32*)(msg + 0x28)) { /* MC_ table, Part 3.1 */ } break;
  case 2: switch (*(u32*)(msg + 0x28)) { /* MC3_ table, Part 3.2 */ } break;
}
FUN_004428e0(msg); operator_delete(msg);     // dispatcher owns + frees the message
```

## 9.3 Leaf routing wrapper (uniform) — e.g. FUN_0040af30 (MC_ signal trace)
```c
station = packet_getStation(msg);
unit    = resolveTarget(this);               // FUN_00409ca0
if (unit && this->quitFlag==0 && getTargetType(unit)==1)   // ==1: MC_ generation
    bearbeite_Kom_27_MC_GIVESIGNALVERLAUF(unit, msg);       // → decodeSignalTrace_B
```

## 9.4 Dispatcher thread loop — FUN_0042db50 (run())
```c
setObjectName("KommandoThread");
for (;;) {
    if (stopFlag@+0x1f) return;
    while (queueA@+0x0c nonEmpty || queueB@+0x08 nonEmpty) {
        lock(mutex@+0x14);
        msg = dequeue(queueA@+0x0c);
        aux = dequeue(queueB@+0x08);
        unlock(mutex@+0x14);
        if (msg) FUN_004152c0(msg);          // → Command_Dispatch_Switch(DatenInstanz, msg)
        if (aux) FUN_00415370(aux);          // secondary stream (not needed for reader)
    }
    lock(mutex@+0x14);
    if (wakeFlag@+0x1e==0) QWaitCondition::wait(cond@+0x24, mutex, INF);
    wakeFlag@+0x1e = 0; unlock(mutex@+0x14);
}
```

## 9.5 Amplitude sample decode — decodeSignalTrace_B (FUN_00497d30)
```c
if (payload > 0xFB) {                        // need > 251 bytes
    puVar6 = data + 0x10;                    // sample bytes start
    // copy 250 bytes, then read 125 samples:
    for (i = 0x7d; i; i--) { QList_short_append(&list, (u16*)p); p += 2; }
    // samples stored RAW (0..255); no scaling
}
```

## 9.6 Config record proof — SGeraetRec vs Devices (re-verified 1974.txt)
```
RAW HEX:  44 05 01 04 … 80 80 80 80 80 80 80 80 … D4 19
           │  │  │  │     └──── MiSensType[8] ────┘   └ ReduzLim (LE) = 6612
DB row:   68 5 1  4       = 128 each                = 0x19D4
Result:   MATCH MATCH MATCH MATCH  MATCH             MATCH
```

## 9.7 Feature-name decode — SKanalRec (this box, verified 1974.txt)
```
+0x4D: 01 56 49 42 52 41 54 49 4F 4E 00 00  → mask 0x01 "VIBRATION"
       02 4D 31 33 31 20 44 45 42 49 00 00  → mask 0x02 "M131 DEBI"
       04 4D 31 33 31 42 41 53 49 4E 43 00  → mask 0x04 "M131BASINC"
       08 4D 30 38 20 44 45 42 49 00 00 ..  → mask 0x08 "M08 DEBI"
```

---

# ═══════════════════════════════════════════════════════════════
# PART 10 — MEASUREMENT DATABASE (history)   ✅ VERIFIED
# ═══════════════════════════════════════════════════════════════

`ProvisLog-10663` (SQLite, ~8 MB) is the app's working measurement DB. 61 tables:

- **`Log`** (9,637 rows) — cycle/run log: `WorkPiece, ProgNum, Channel, Tool, ProgRef,
  Type, SRate, Data_Ref, Status1..4`.
- **`Alarms`** (65 rows) — `Date, ProgRef, ChannelNr, CycleNr, FeatureNr, LimitNr, Ack,
  Ack_Date, Signal, TimeOffset`. Feature+limit referenced — consistent with Part 4.2 and
  the `Limits` config.
- **`Trend_C01_F01..F04`** — per-feature peak trend: `WorkPiece, Source, Max_Val, Work_Val`.
  `Max_Val` = raw peak (0..255); `Work_Val` = 0..301 (position/window, NOT amplitude).
- **`WP_00001_01 … WP_000NN_01`** (52 tables) — per-workpiece measurement curve stored as a
  **per-sensor min/max envelope**: `Min_S01,Max_S01,…,Min_S04,Max_S04` (one row per sample
  index). This is enveloped/downsampled history, **not** the raw 125-int16 waveform.
- **`Status_C01`** — per-workpiece status: `WorkPiece, Source, Status1..4`.
- **`Statistics`, `Version`**.

**Implication:** for history migration, read `Trend_*`, `WP_*`, `Alarms`, `Log`. For the
**live** waveform there is no DB source — it exists only on the wire via SIGNALVERLAUF
(Part 4.1). This confirms (does not contradict) the protocol model.

---

# ═══════════════════════════════════════════════════════════════
# PART 11 — DATA SOURCES & HOW EACH FACT WAS OBTAINED
# ═══════════════════════════════════════════════════════════════

| Fact | Source | Tool | Confidence |
|---|---|---|---|
| Config record layouts | PMD hex (1974.txt, exVL2-*) ↔ SQLite config DBs | file cross-ref | ✅ |
| Config DB schema | Provis-10659 / -10663 | direct read | ✅ |
| Measurement DB schema + amplitude range | ProvisLog-10663 | direct read | ✅ |
| Scaling = no factor | ProvisLog (Max_Val/WP ≤255), Sensors.Calibration, 0x11 stub | DB + Ghidra | ✅ |
| Field meanings | CDR_DESCRIPT_ENU/DEU.ini + DB | direct read | ✅ |
| Gateway wire format | binary (Scan4CANmsg, CanInterface) | Ghidra | 🔶 |
| CAN reassembly | binary (unitBuffer_*) | Ghidra | 🔶 |
| Command dispatch (group,command → handler) | binary (Command_Dispatch_Switch + workers) | Ghidra | 🔶/✅ |
| Active generation = MC_ | LogFile.txt (Promos3DatenProvis2Geraet, MC_GIVEKONFIG) | runtime log | ✅ |
| Payload bodies | binary (bearbeite_Kom_*) | Ghidra | 🔶 |
| Decoder rings | binary (initStatusTables) + PROVISsettings.ini | Ghidra + config | 🔶/✅ |
| Transport config (ports, PCANGateway) | PROVISsettings.ini | direct read | ✅ |

These files exist because PROVIS3 produces them itself (SQLite working DBs; PMD .txt
Export; ErrorManager logs). Collected by copying, not capture. The only data the app does
NOT save is the LIVE stream — hence Ghidra (or a capture) for the transport.

### Files used this session
- SQLite config: Provis-10659(-250127_1838), Provis-10663
- SQLite measurement: ProvisLog-10663
- PMD hex: 1974.txt
- INI: PROVISsettings.ini, ALT2-NCaccess.ini, CDR_DESCRIPT_ENU.ini
- Runtime: LogFile.txt (+ dated LogFile-260701-* referenced)
- Ghidra decompiles: Command_Dispatch_Switch (004125d0), FUN_00436470, FUN_0042db50,
  FUN_004152c0, FUN_00409ca0, FUN_0047fde0, FUN_004dc3e0, FUN_0040af30, FUN_0040c5e0,
  FUN_004acf40, FUN_0040c540, FUN_004b9150, FUN_0040c450, FUN_004b6580, vftable of
  Promos3KommandoVerteilerThread

### Consistency with prior analysis notes
Independent analysis notes (`eski-provis-analizi.md`, ADRs 0001–0005) were cross-checked and
found **consistent** with these findings: units 10659/10663, GType 0x44, transport config,
the two command generations, record structures, and DB schema all match. Notes were slightly
conservative on capture (they predate the Ghidra recovery; Wireshark is now optional via
`LogCANMessage=1`), and correctly flagged the model-name mapping as needing live confirmation.
ADR-0004 (read-only observer MVP) aligns with why only the receive/decode path was needed.

---

# ═══════════════════════════════════════════════════════════════
# PART 12 — TOOLING PRODUCED
# ═══════════════════════════════════════════════════════════════

- **promos3_listen.c** — UDP listener/decoder (no pcap, no admin). Decodes the packet
  bodies. Caveat: assumes a CLEAN Promos3 body per datagram; the real gateway sends 36-byte
  CAN records that must be split + reassembled first (Part 2), and dispatch is 2-level
  (Part 3) — add a front-end that splits records → extracts 8 data bytes → concatenates per
  unit → dispatches by (group, command).
- **promos3_records.h** — verified packed structs (SGeraetRec, SKanalRecV40, SGrenzRec,
  SHardwareRec, SZykRecV4802). Update the feature-name handling per §7.2 (read names, mask
  `& 0x0F`).
- **promos3_sniff.c** — pcap variant (requires libpcap + admin); superseded by the listener.

---

# ═══════════════════════════════════════════════════════════════
# PART 13 — HOW TO FINISH (what's left)
# ═══════════════════════════════════════════════════════════════

The protocol is functionally complete for a read-only `MC_` reader. Remaining, all
non-blocking:

1. **Exact wire byte-offsets** of `[group]/[command]/[length]` in the raw reassembled
   message. Object offsets (group @+0x00, command @+0x28) and the full handler map are
   known; only the on-wire positions are unconfirmed. Get them with the app's own logger:
   set `PROVISsettings.ini [ErrorManager] LogCANMessage=1`, run against the device for a
   minute — raw CAN frames are written to the log. **No Wireshark, no PEAK card, no admin.**
   (A single UDP capture of `192.168.222.17:1789` would also work and pin everything at once.)
2. **Model string** for (GType 0x44, GSubType 5) — resolve the `[MonitorTypes]` index base
   against a known unit. Cosmetic.

Everything else — transport, dispatch, records, alarm, event, sensor-info, decoder rings,
scaling (no factor), and history schema — is recovered and cross-verified.

---

# ═══════════════════════════════════════════════════════════════
# PART 14 — GLOSSARY
# ═══════════════════════════════════════════════════════════════

- **Kom / Kommando** — command (message type); **bearbeite** — process/parse (device→app);
  **Sende** — send (app→device).
- **Geraet** — device; **GType/GSubType** — device type codes; **Merkmal** — feature;
  **Kanal** — channel; **Zyklus/Zyk** — cycle; **Grenz** — limit; **Konfig** — configuration.
- **Signalverlauf** — signal trace (amplitude series); **VFAKT (Verstärkungsfaktor)** —
  gain/scaling factor (stubbed for this generation).
- **PROCUR-S/I/B** — Prometec sensor types (0x80/0x81/0x82); **MI sensor** —
  measurement-input sensor (MiSensType).
- **TPCANMsg** — PEAK PCAN standard CAN message struct (14 bytes); **BaseCanIDTransfer
  (1280)** — CAN-ID base; unit = CAN_ID − base; **PCANGateway** — flag selecting
  CAN-over-UDP gateway vs local PEAK card.
- **MC_ (Provis2)** — legacy command generation (this box); **MC3_ (Promos3)** — modern
  generation; **getTargetType** — unit generation (1=MC_, 2=MC3_).
- **debi** (TR) — flow rate; **basınç** (TR) — pressure (feature labels on this machine).
- **NC / NTIF** — Mazak numerical-control channel / its DLL API.

---

*End of report (v2).*
