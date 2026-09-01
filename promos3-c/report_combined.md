# PROVIS3 / Prometec Monitoring — Consolidated Reverse-Engineering Report

**Version 3.0 — single consolidated edition (supersedes all prior parts)**

**Target:** PROVIS3 HMI application (Sandvik / Prometec CNC tool-monitoring), 32-bit Qt4
binary, branded for Mazak. App version **3.1.44.4 / "V3.1.44 HF4"**, DB schema **10**.

**Goal:** Recover the device↔HMI communication protocol and data formats completely enough
that a modern 64-bit application can read live sensor telemetry, alarms, configuration and
history **without** the original software, without the PEAK/PCAN hardware, and without the
32-bit dependency chain.

**Method:** Ghidra static analysis of the binary, cross-referenced against the application's
own exported artefacts (SQLite databases, PMD hex dumps, INI files) and its own runtime logs.
No Wireshark, no packet capture, and no live machine access was used at any point.

---

## About this edition

This document merges seven separate analysis artefacts produced across five working sessions
into one authoritative reference:

| Source document | Session | What it contributed |
|---|---|---|
| `analysis_jul_28_1_0_0.md` (report v2) | 1 | Architecture, transport, dispatch map, payload bodies, scaling, config records, measurement DB |
| `analysis_appendix_datamodel.md` (Appendix A) | 2 | `Promos3DataRecord` domain object, SQLite read path |
| `analysis_appendix_B.md` (Appendix B) | 2 | 30 SQL/config/receive functions, MC3_ command registry, field descriptors |
| `analysis_part15_gap_register.md` | 3 | Gap register G1–G13, reader test evidence, master/slave discovery |
| `analysis_part16_mc_answer_protocol.md` | 4 | MC_ answer framing, checksum, completion rule, MC3_ assembler |
| `analysis_part17_session_handoff.md` | 4 | MC_ command table, size table, request side, unit discovery, architecture |
| `analysis_part18_session_report.md` | 5 | Transmit path, poll cycle, CAN-ID resolution, model string, link-layer code |

**Consolidation rules applied.** Nothing has been discarded. Where two documents described
the same thing, they have been merged into one statement of current truth. Where a later
session *overturned* an earlier conclusion, the current truth is stated in the body of the
report and the superseded claim is preserved in the **Correction Ledger (§0.6)** with the
evidence that overturned it — because knowing what was wrong, and why, is what stops it being
re-derived. Every ⚠️ **SUPERSEDED** marker in the body points back to that ledger.

**How to read it.** Part 0 is the summary and the correction ledger. Parts 1–4 are the protocol
proper — the part you implement. Parts 5–10 are the reference tables (dispatch, payloads, decoder
rings, records, databases). Parts 11–15 are the binary-level appendices: the application data
model, the SQL layer, the full function reference, annotated snippets and object layouts. Parts
16–21 are project state: what is left, what to build, what to do next, where every fact came from,
what earlier documents got wrong, and the glossary.

Shortcuts: building the link layer → **Parts 2 and 3** (this box) or **Part 4** (other sites);
looking up a `FUN_` address → **Part 13**; wondering whether something is still open → **Parts 16
and 17**; holding an older document and wondering what changed → **§0.6 and Part 20**.

---

## Confidence scale

Used uniformly throughout. Where a percentage appears next to a function name it is the
analyst's per-function estimate from the session that recovered it.

| Marker | Meaning |
|---|---|
| ✅ **VERIFIED** | Proven against raw hex, a database value, a runtime log line, or the function's own literal tag string. Byte-for-byte or value-for-value. |
| 🔶 **GHIDRA** | Recovered from disassembly. Reliable, code-derived, but not externally cross-checked. |
| ⚠️ **INFERRED** | Reasoned from context. Not yet confirmed by bytes. |
| 🔴 | Flags a trap: something that will silently produce plausible-looking wrong output if ignored. |

Two naming conventions appear in the binary and are used here as the binary uses them:

- **[tag-proven]** — the function builds a QString naming itself (a `Promos3MutexLocker`
  label, an `ErrorManager` tag, or a class-qualified string such as
  `"Promos3CanInterface::receive"`). These names are the binary's own.
- **[structural]** — the name is an analysis label derived from what the code does.
  Verify before committing it to a build.

---

## Table of contents

| Part | Title | Covers |
|---|---|---|
| **0** | Executive summary | what was achieved, the facts that matter, status, what remains |
| **1** | System architecture | the two channels, reference install, receive path, transmit path, object architecture, GUI graph, concurrency, unit discovery + cadence |
| **2** | Transport: the gateway and CAN layer | endianness, the 36-byte RX and TX records, `TPCANMsg`, CAN-ID → unit |
| **3** | The `MC_` link protocol (**this box**) | anonymous answers, frame layout, request layout, checksum, completion rule, size table, retries, poll cycle, send queue |
| **4** | The `MC3_` link protocol (group 2) | a different protocol: framing, 16-bit lengths, its own checksum, streaming, side-by-side |
| **5** | Command dispatch | the dispatch model, the group-1 table, the group-2 table + registry, group 0, `MC3_` field descriptors |
| **6** | Decoded payload bodies | SIGNALVERLAUF, SAMMELMERKMALE, KONFIG, ALARM, SENSOR_INFO, EVENT |
| **7** | Scaling | resolved: no factor, raw 0–255 |
| **8** | Decoder rings | ToolStatus, SensorType, ChannelStatus, AccessLevel, EventCode, model string, alarm names, station names, field labels |
| **9** | Configuration records at rest | `SGeraetRec`, `SKanalRecV40`, `SGrenzRec`, `SHardwareRec`, `SZykRecV4802`, versioning, config DB catalog |
| **10** | Measurement database (history) | the 61-table schema, `Alarms` column order |
| **11** | Application data model & DB read path | `Promos3DataRecord`, the SQL read chain, helpers, implications for tooling |
| **12** | SQL dialect layer, configuration and settings | SQLite⇄ODBC abstraction, `Verbindung`, INI→struct maps, the settings dialog |
| **13** | Complete function reference | every named `FUN_` address, merged and deduplicated |
| **14** | Key code snippets | annotated decompiler extracts, incl. the checksum as portable C |
| **15** | Object layouts | `Promos3Paket`, `UnitComm`, `Promos3CanInterface`, `Interface`, `Geraet`, `Kanal`, RouterObj |
| **16** | Gap register (final state) | G1–G13 with their full progression, plus the two device-state items D3/D4 |
| **17** | Reader implementation guide | passive vs master, the 30-second test, what to change, tooling inventory |
| **18** | Test evidence | the reproduced corruption bug, the 20 passing assertions, the bug the tests found |
| **19** | Data sources & provenance | how every fact was obtained, files used, method notes |
| **20** | **Supersession log** | every claim an older document got wrong, and what replaced it |
| **21** | Glossary | German, Turkish, protocol, hardware and confidence terms |

---

# ═══════════════════════════════════════════════════════════════
# PART 0 — EXECUTIVE SUMMARY
# ═══════════════════════════════════════════════════════════════

## 0.1 What was achieved

The complete bidirectional protocol was recovered — receive path, transmit path, framing,
addressing, checksum, completion rule, discovery and poll cadence — entirely from static
analysis plus the application's own files.

```
Device ⇄ UDP :1789 ⇄ 36-byte gateway records ⇄ CAN frames ⇄ per-unit reassembly
       → command dispatch (group, command) → payload decode → GUI / SQLite
```

Every stage is tied to a specific, named function. All configuration record formats and both
database schemas were decoded and re-verified against the application's own exported files —
a deterministic, proof-grade method that needed no disassembly at all. The active protocol
generation, the no-scaling result, and the checksum algorithm were confirmed against the
application's own runtime log and measurement database.

**The reverse-engineering phase is complete.** Protocol knowledge stands at ~99%. The
remaining ~1% is not in the executable: it is device runtime state (two answer sizes and one
config byte) that only the machine can supply. No further decompilation is warranted.

## 0.2 The structural facts that matter most

1. **Transport is CAN-over-UDP through a gateway** at `192.168.222.17:1789`
   (`PROVISsettings.ini [CAN] PCANGateway=1`). Each UDP datagram is a batch of fixed
   **36-byte records**, each carrying one CAN frame (CAN-ID + up to 8 data bytes).
2. **Addressing: one CAN-ID base.** `CAN-ID = BaseCanIDTransfer(1280) + unit`, units 1–15,
   the same base in both directions. ⚠️ SUPERSEDES the three-base claim — see §0.6 C4.
3. **Endianness is split.** The CAN transport layer is **big-endian**; the reassembled
   Promos3 application payload is **little-endian**. Both verified.
4. **The link is master/slave polled, not push.** One outstanding request per unit, 300 ms
   answer timeout, one resend, a 3 ms polling loop. An idle bus carries nothing.
5. **This installation is a Provis2 / `MC_` box** (dispatch group 1). Proven at runtime — the
   device object is `Promos3DatenProvis2Geraet` and config arrives as `MC_GIVEKONFIG`.
6. 🔴 **On the `MC_` wire, answers carry no command and no group.** Both are inherited from
   the request the answer belongs to. A message is only identifiable in the context of its
   request. This is the single most consequential design fact in the project — it decides
   the entire architecture of any reader. ⚠️ SUPERSEDES the v2 header model — see §0.6 C1.
7. **`MC3_` (group 2) is a different protocol, not a variant.** It shares nothing with `MC_`
   at the framing layer: 8 payload bytes per frame instead of 7, no sequence byte, command
   and length *are* on the wire, a different checksum. Two front-ends, one dispatcher.
8. **The checksum is recovered and byte-verified** against a real logged frame, from two
   independent code sites: an 8-bit two's-complement sum seeded with the unit id, taken over
   the request bytes (minus their own checksum) plus the whole answer payload.
9. **No amplitude scaling factor exists** for this generation. Live samples, stored maxima
   and alarm thresholds all live in one unit: **raw 0–255 counts**.
10. **Feature names, alarm slot names and station names are per-install operator strings.**
    They must be read from the device/INI at runtime. Hardcoding the defaults mislabels them
    plausibly — the most dangerous kind of wrong.

## 0.3 The reference installation

Two monitor units on one Mazak, offline LAN, over the UDP gateway. Verified from the runtime
log, the config databases and `PROVISsettings.ini`.

```
Unit 1:  SNr 10659   GType 68 (0x44)  GSubType 5   1 channel, 4 sensors, PLC in 4 / out 1
Unit 2:  SNr 10663   GType 68 (0x44)  GSubType 5   1 channel, 4 sensors, PLC in 4 / out 1
Model string:        MSL5081-16                    (resolved, §8.7)
Device class:        Promos3DatenProvis2Geraet     → generation 1 = MC_
Firmware:            Rtm_V14.5.H86 (RTM v14.5, Intel-HEX)
Config version:      229 (0xE5)                    ← record layouts are version-selected
Gateway:             192.168.222.17:1789   PCANGateway=1  BaseCanIDTransfer=1280  BusID=512
Unit sweep range:    FirstDevice=1 .. LastDevice=15
Timeouts:            [CAN] unitAnswerTimeout=300   [Comm] unitActiveTimeout=900  MaxResend=1
Ethernet streaming:  [Ethernet] Active=0 (disabled; would-be streaming port 2789)
Features (this box): VIBRATION · M131 DEBI · M131BASINC · M08 DEBI   (operator-assigned)
Alarm slots:         1 Collision · 2 Break · 3 Wearout · 4 Missing · 5 Coolant · 6–8 blank
```

⚠️ `PROVISsettings.ini [DatabasePMD]` additionally references units **10660** and **10665**
(`LastMonDataFile-10660`, `LastMonDataFile-10665`, both `bas?c-setup`). Only 10659 and 10663
are active in the logs and databases. Treat 15 units as the addressable range, not 2.

## 0.4 Status table

| Layer | Status | Confidence |
|---|---|---|
| Gateway / CAN transport framing (RX **and** TX) | Complete, byte-exact | ✅ VERIFIED |
| CAN-ID addressing, unit routing | Complete | ✅ VERIFIED |
| `MC_` request wire format | Complete, byte-exact | ✅ VERIFIED (matches logged frame) |
| `MC_` answer framing + sequence | Complete | 🔶 GHIDRA (93%) |
| Checksum algorithm (both generations) | Complete | ✅ VERIFIED (two code sites + log) |
| Reassembly completion rule | Complete | ✅ VERIFIED (code + tests) |
| Expected-answer-size table | Recovered; 3 entries doubtful | 🔶 / ⚠️ |
| Unit discovery + poll cycle + cadence | Complete | ✅ VERIFIED |
| Command dispatch (group, command → handler) | Complete, ~70 handlers | ✅ / 🔶 |
| `MC_` command names (group 1) | ~35 of 38 named | 🔶 GHIDRA |
| `MC_` payload body layouts | 2 of 38 decoded (`0x1b`, `0x16`) | 🔶 / ⚠️ |
| `MC3_` framing, registry, field descriptors | Complete | ✅ VERIFIED |
| `MC3_` payload bodies (alarm/event/sensor) | Complete | 🔶 GHIDRA |
| Configuration records (device/channel/cycle/limit) | Complete | ✅ VERIFIED vs `1974.txt` |
| Historical config DB schema | Complete | ✅ VERIFIED |
| Measurement DB schema (trend/WP/alarms/log) | Complete | ✅ VERIFIED |
| Application data model + DB read path | Complete | 🔶 / ✅ |
| Code-meaning tables ("decoder rings") | Complete | 🔶 / ✅ |
| Scaling (raw→physical) | **Resolved: no factor** | ✅ VERIFIED (2 databases) |
| Record-layout versioning | Open, low value | ⚠️ INFERRED |

## 0.5 What remains

Two items, both **device runtime state** — not recoverable from the binary at any effort:

1. **D3 — real expected answer sizes for `0x01`, `0x12`, `0x1b`.** The recovered size table
   (§3.7) is authoritative for `0x02` (14) and `0x0e` (144, call-site verified). The values
   in use for `0x01`, `0x12` and `0x1b` are guesses. `0x12` (`GIVEALARM`) was mapped onto the
   table's `0x11` entry, which is `ALARMGESEHEN` — probably wrong. `0x1b`'s 257 comes from a
   *synthetic* test, not from real bytes.
2. **D4 — the `0x08` size branch.** With config version `0xE5`, if `Geraet+0x4e6` is nonzero
   a nibble-sum branch applies and the currently assumed value is wrong. That byte arrives
   from device config at runtime.

Plus a short list of minor open assumptions, all of which **degrade into a timeout rather
than corruption** (§14.4). Neither item blocks building the reader; both are answered by one
30-second live test (§17.1).

## 0.6 Correction Ledger — superseded claims

Every place where a later session overturned an earlier one. The **Now** column is what the
body of this report states. Nothing here is deleted; it is recorded so it is not re-derived.

> This table is the **summary**. **Part 20** carries the same material at full length, with the
> reasoning behind each reversal and a few additional reconciliations that are too long for a
> table row. If you are holding an older copy of any source document, read Part 20.

| # | Topic | Earlier claim (source) | **Now** | What overturned it |
|---|---|---|---|---|
| **C1** | `MC_` message header | `[group]@+0x00 / [command]@+0x28 / [length]`; wire offsets "open, non-blocking" (report v2 §2.4, §0.5, §13) | 🔴 **No header exists on the `MC_` wire.** `group` and `command` are copied from the outstanding request before any answer byte is read. Closed **by deletion**, not by measurement. | `UnitComm_assembleAnswer_MC` (`FUN_00684160`): `newMsg[10] = requestPaket[10]`, read at the top of the function (Part 16 §16.1) |
| **C2** | Where the v2 header model came from | Presented as the general model | It is an accurate description of **`MC3_` only** — and even there `group` is hardcoded in the ctor, not on the wire. Not applicable to this box. | `UnitComm_assembleAnswer_MC3` (`FUN_00685940`) read side-by-side (Part 16 §16.9) |
| **C3** | Reassembly completion | "A frame shorter than 8 bytes ends the message" (reader heuristic) | 🔴 **Provably wrong and silently corrupting.** Real rule: accumulate 7 payload bytes/frame until `accumulated == expectedSize` from the size table. | Live test: a 64-byte message never completes and swallows the next one (Part 15 §15.9 cases B/C) |
| **C4** | CAN-ID bases | **Three** bases `0x500 / 0x580 / 0x600`; "this is the direction discriminator" 🔴 IMPORTANT (Part 17 §5.3) | **One base.** `local_1c = *(int*)(this+0x48) + unit` where `this+0x48` = `BaseCanIDTransfer` = 1280. TX and RX share it. | `Promos3CanInterface::send` (`FUN_00506220`) + the settings dialog exposing exactly one "Base Tx" field (Part 18 §3.3) |
| **C5** | `FUN_005073f0` | `CanInterface_setForSending`; "the next target — likely the frame splitter" (Part 17 §13.1) | `Promos3CanThread::sendCommandToUnit` — a queue enqueue with de-duplication. **The splitter is `FUN_00506220`.** | Part 18 §2 and §7 |
| **C6** | `Paket+0x20` | "QByteArray — the message bytes" (Part 16 §16.5) | **Aux/context `QVector<u8>`, never transmitted.** Wire bytes are reached via `stream_peekCurrent`; `+0x20` is read by `stream_peekU16`. | Part 17 §6 |
| **C7** | `Paket+0x30` | "aux" (Part 16 §16.5) | **Station / device index** (`paket[0xc] = station`) | Part 17 §6 |
| **C8** | `Geraet+0x4BC` | "station count" (Part 17, and the first reader draft) | **Channel count.** Behaviourally identical on this box (1 of each) but the label was wrong. | Loop bound in `FUN_004d1310` (Part 18 §6) |
| **C9** | `FUN_005018f0` | Labelled as the CAN interface | `Promos2EthInterface_setForSending` — Ethernet, not CAN. `Promos3CanInterface` is a plain QObject outside the Eth vtable hierarchy. | Corrected mid-session (Part 17 §11 items 5–6) |
| **C10** | `MC3_` command `0x11` | `MC3_SENSOR_VFAKT` (stub) (report v2 §3.2) | **`MC3_LAST_SIGNAL`.** `MC3_SENSOR_VFAKT` is **`0x0b`**. The "no runtime scaling" conclusion is unaffected — the VFAKT worker is still a `return p!=0` stub. | The binary's own registry in `MsgCreator_buildMC3Registry` (App. B.2.1), independently corroborated by the sender tag `Sende_Kom_11_MC3_SENSOR_VFAKT` (11 dec = 0x0b) |
| **C11** | `MC3_` German handler labels | `MC3_MERKMAL_INFO`, `MC3_GERAETEREC` (report v2 §3.2) | Registry aliases: **`MC3_FEATURE_INFO`**, **`MC3_DEVICEREC`**. Same commands. (Merkmal = feature, Gerät = device.) | App. B.2 |
| **C12** | Feature names / masks | `SPINDEL / X AXIS / Y AXIS / Z AXIS`, masks `0x81/0x82/0x84/0x88` (report v1) | 🔴 **Per-install, operator-assigned.** This box: `VIBRATION / M131 DEBI / M131BASINC / M08 DEBI`, masks `0x01/0x02/0x04/0x08`. Match on `mask & 0x0F`; `0x80` is a separate flag. | `1974.txt` byte-for-byte (report v2 §7.2) |
| **C13** | Amplitude scaling | A scaling factor was assumed to exist; "display axis 0–300" read as amplitude range (report v1) | **No factor.** Raw 0–255 everywhere. The 0–301 range belongs to `Trend.Work_Val`, a cycle-position quantity, **not** amplitude. | `Features.Feat_Max`, `Trend_*`, `WP_*`, `Limits.Level`, `Sensors.Calibration`, and the stubbed VFAKT worker (report v2 Part 5) |
| **C14** | Model string for (0x44, SubType 5) | "Cosmetic; index base 0- or 1-based unknown" (v2 §0.5, Part 15 G10) | **Closed: 1-based → `MSL5081-16`.** `idx = GSubType - 1` | `MonitorTypes_resolveName` (`FUN_004abb20`), Part 18 §5 |
| **C15** | Request `params[0]` | "Probably the channel" (Part 15 §15.0a); left open in Part 16 §16.3 | **Station / traceMap key**, not channel. Reads `0x01` in the logged frames because this box has one station. | Confirmed three ways in Part 16 §16.10 |
| **C16** | `FUN_004c5840` | "The single highest-value function still un-analysed" (Part 15 G2) | Recovered as **`Geraet_expectedRecordSize(komNr)`** — the expected *answer* size table, stamped into `Paket+0x14` at send time. | Part 17 §2.6 + the call site in `Geraet_sendeKom_MC_GIVEKANAL` |
| **C17** | Checksum | "0% — algorithm, position and checksum-only frame shape all unknown"; the `0xF6 = ~(0x08+0x01)` observation flagged as an *untested* hint (Part 15 §15.5) | **Recovered and byte-verified.** The hint was correct. | `promos3_checksum` (`FUN_004425c0`) + inline recompute in `FUN_00506220` + the logged frame |
| **C18** | Capture strategy (G4) | "Blocking; you cannot receive a unicast stream twice; needs a SPAN port and libpcap" (Part 15 §15.4, Part 16 §16.6) | **Closed via master mode.** Request framing, checksum, cadence and discovery are all known, so no capture and no mirror is required. `promos3_sniff.c` is **not** needed. | Part 18 §3, §9 |
| **C19** | `0x16` block stride | `featureCount*2 + 2`, "or +4 when `this+0xC0 == 1`" (Part 17 §8) | Stride = `featureCount*2 + 2`, **+2 when `GeraetTyp == 'H'`** (`0x48`). This box is `'D'` (`0x44`) → **stride 10** for 4 features. | `FUN_004d1310` compares GeraetTyp as an ASCII char (Part 18 §4.1) |
| **C20** | Device-error answer signature | `DATA[0]==0 && DATA[1]==1` | 🔴 **Must also be `LEN == 2`.** Without that constraint the signature is identical to a healthy first data frame whose first payload byte is 1 — which for `0x16` means "one row", the most common case. As originally written, a reader would discard most live measurement data and count it as device errors. | Found by writing and testing the link layer, not by reading code (Part 18 §8.2) |
| **C21** | First probe command | `0x01 MC_GIVESTATUS` implied usable | **Poor probe.** It never calls `Paket_setRecvSize`, so its expected answer size is unknown. Use **`0x08`**, whose exact request bytes are verified from the log. | Part 18 §7.5 |
| **C22** | `FUN_005e1c90` | Two readings: "read records by source+date" (App. A.4.1, slot 0) *vs* `SqlDbMgr_findeAlleIDsFromWerkzeug` (App. B.1.1) | **Both, reconciled:** it is `Promos3ProtokollThread` dispatch slot 0; it resolves the connection by key (`this+0x6c`), calls the tool→ID and source→ID lookups, and merges them via `SqlDb_findeAlleIDsFromSource`, which is itself date-ordered. | Cross-read of App. A and App. B |
| **C23** | `FUN_005206c0` / `FUN_005179c0` | Predicted to reveal the multi-frame request split (Part 17) | **They send nothing over CAN.** SQL→memory config loaders with no protocol content. | Part 18 §7.4 |
| **C24** | `[Ethernet]` INI defaults | Appendix B.6 lists *code defaults* | The reference INI's **actual** values differ on four keys: `ResendON` 0 (default 1), `LogETHMessage` 1 (default 0), `LastPort` 1799 (default 1789), `unitAnswerTimeout` 300 (default 500, floored to 500 in code). Both are correct — one is the default, one is the deployment. | Direct read of `PROVISsettings.ini` |

---

# ═══════════════════════════════════════════════════════════════
# PART 1 — SYSTEM ARCHITECTURE
# ═══════════════════════════════════════════════════════════════

## 1.1 The two communication channels

```
┌────────────────────────┐        CAN-over-UDP           ┌──────────────────────┐
│  Prometec device       │  gateway 192.168.222.17:1789  │                      │
│  (MSL5081-16, GType    │◄─────────────────────────────►│    PROVIS3  HMI      │
│   0x44, 4× PROCUR-S)   │        (THIS REPORT)          │    (Promos3 app)     │
└────────────────────────┘                               │                      │
┌────────────────────────┐            TCP 57400          │                      │
│  Mazak NC control      │◄──────  via NTIFDLL.dll  ─────►│                      │
│  (program, tool, part) │      (separate channel)       │                      │
└────────────────────────┘                               └──────────────────────┘
```

- **Prometec / CAN-over-UDP** — sensor telemetry, alarms, configuration. Covered in full here.
- **Mazak NC** — running program, tool and part count over TCP via the NTIF API
  (`NTIFDLL.dll`, 32-bit). Separate channel; register map in `NCaccess.ini`
  (`Port=57400`, `RegPNameSet=8508-1`, …), credentials in `mazak.lic`. Noted for
  completeness; not the focus of this report. The bridge between them is
  `changePMDfromNC` (`FUN_004341f0`), which is a **write** path (NC program change →
  PMD selection) and therefore outside a read-only reader's scope.

## 1.2 The complete receive path (device → decoded values)

```
 (1) UDP datagram arrives on port 1789   (batch of fixed 36-byte records)
        ▼
 (2) Scan4CANmsg  [FUN_00507760] 🔶
        split into 36-byte records (trim the remainder from the FRONT);
        each record = ONE CAN frame:
          +0x15     LEN (0..8)
          +0x1A..1B CAN-ID (uint16 BIG-ENDIAN hi,lo)
          +0x1C..23 8 DATA bytes
          +0x00..14 gateway header (discarded on RX)
        ▼
 (3) Unit routing 🔶     unit = CAN_ID − BaseCanIDTransfer(1280);  ID below base → dropped
        ▼
 (4) unitBuffer_appendCanData [FUN_006823b0] 🔶
        append the data bytes; two sub-streams (+0x08 header/len, +0x0c data);
        the first frame of an answer restarts the timeout timer
        ▼
 (5) UnitComm_firstReceivedPaket [FUN_00686430] 🔶
        route by the REQUEST's group:  group 0 or 1 → MC_ assembler
                                       group 2      → MC3_ assembler
        ▼
 (6) UnitComm_assembleAnswer_MC  [FUN_00684160]     ← this box   (§3)
     UnitComm_assembleAnswer_MC3 [FUN_00685940]     ← other installs (§4)
        verify sequence · accumulate payload · verify checksum · build the message object
        The message object inherits group and command FROM THE REQUEST (§3.2).
        Promos3 payload is LITTLE-ENDIAN.
        ▼
 (7) CanInterface_receive [FUN_00508a80] ✅
        status 1 complete  → enqueue to KommandoVerteilerThread
        status 2 abort     → log "enAbort", drop the unit
        status 3 restart   → send MC3_SET_STREAMING, "* * * Streaming ON at StartUp"
        ▼
 (8) Command_Dispatch_Switch [FUN_004125d0] 🔶  (this = Promos3DatenInstanz singleton)
        group   = *(uint32*)(msg + 0x00)   (via Paket_getGroup FUN_00436470)
        command = *(uint32*)(msg + 0x28)
        switch(group){ 0:handshake  1:MC_  2:MC3_ } → switch(command) → handler
        ▼
 (9) bearbeite_Kom_NN → resolveTarget → decode body → emit signals → GUI / SQLite 🔶/✅
```

⚠️ **SUPERSEDED (§0.6 C1).** Steps (6) and (8) look like a parse followed by a dispatch on
parsed fields. For `MC_` they are not. The `group` and `command` at message object offsets
`+0x00` and `+0x28` are **copied out of the outstanding request** before a single answer byte
is examined. There is nothing to parse. See §3.2.

**Alternate source, identical downstream.** `CanInterface_pollMessages` (`FUN_005083e0`)
branches on transport mode — UDP gateway (above) versus real PEAK-CAN hardware (`CAN_Read`
from `CanApi2.dll`). Both feed the same unit buffers and the same completion logic. On this
machine `PCANGateway=1`, so the gateway path is used; the equivalence is what proves the
gateway decode matches hardware behaviour.

## 1.3 Internal architecture — routing and threads

```
UI / Geraet senders
   └─ MsgCreator_createPaketForCommand        ← builds the wire buffer
      └─ KommandoVerteiler_enqueuePaket       ← outbound queue (+0x08)
         └─ Promos3KommandoVerteilerThread::run
            ├─ +0x0c inbound  → Router_dispatchInbound → Command_Dispatch_Switch
            └─ +0x08 outbound → Router_routePaketOutbound
                                  ├─ RouterObj.type 2 → Eth thread  (signal SendRequest)
                                  └─ RouterObj.type 3 → CAN thread  (signal SendRequest)
                                       └─ slot sendCommandToUnit → per-unit queue
                                          └─ pumpSendQueues → send → transport
```

**Routing is by transport, not by generation.** `Promos3RouterObj` is `{int type; QString name}`
(8 bytes). `type`: **1 = source tag**, **2 = Ethernet**, **3 = CAN**. The `type 1` objects
constructed in every `Sende_Kom_*` are source tags stored at `Paket+0x0c`, not routing keys —
a distinction that is easy to misread.

**Group 0 means "generation not yet known."** `Router_registerUnit` sends `MC_GIVESTATUS`
as group 0; the dispatcher's group-0 arm then sends `MC_GIVEGTYPE`; `FUN_00412290` decides
the generation, and everything afterwards goes out as group 1 or group 2. Group 0 uses `MC_`
framing — which is why `UnitComm_firstReceivedPaket` routes both `group == 0` and `group == 1`
to the `MC_` assembler.

## 1.4 Concurrency model 🔶

Dispatch runs on a dedicated worker thread, **not** the socket thread.

- **`Promos3KommandoVerteilerThread`** ("command distributor thread"). Its `run()` is
  `FUN_0042db50`, which calls `setObjectName("KommandoThread")`.
- The thread drains two queues under a mutex plus a wait-condition
  (mutex `@+0x14`, wake flag `@+0x1e`, stop flag `@+0x1f`, `QWaitCondition` `@+0x24`):
  - **Queue A `@+0x0c`** — completed inbound messages; each dispatched via `FUN_004152c0` →
    `Command_Dispatch_Switch(Promos3DatenInstanz, msg)`.
  - **Queue B `@+0x08`** — the outbound stream → `Router_routePaketOutbound` (`FUN_00415370`).
- **Ownership:** the dispatch switch frees each inbound message (`operator_delete`) after
  handling. The producer hands off ownership by enqueuing.
- **`Promos3CanThread`** (`FUN_0042ec10`, tag `"Promos3CanThread"`) — sets its object name,
  initialises, emits ready, runs `QThread::exec()`, then closes the socket and logs
  `"terminated with %1"`.
- **`CanThread_onTimerTick`** (`FUN_0042eed0`) — the actual cadence:
  `searchForNewUnits → msleep(3) → pollMessages → receive → QTimer(3 ms)`.
  **A 3 ms polled loop, not signal-driven.** This is the master-mode cadence to replicate.
- **`Promos3ProtokollThread`** (`FUN_00557d10`) — a separate QThread subclass with its own
  wait-condition and mutex, handling delayed/batched DB writes. Distinct from the dispatcher:
  the former persists, the latter routes.

A reader does not need to replicate this threading — dispatch can be inline — but it explains
the mutex named `"Vorverarbeitung_Kom"` taken inside `resolveTarget`.

## 1.5 One-outstanding-request enforcement ✅

`Interface_setLastSentPaket` (`FUN_00444090`) stores the in-flight request in the map at
`iface+0x4c`, keyed by unit, and logs
`"Requesting cmd %1 over pending requested cmd %2"` if one is already outstanding.
`Interface_getUnitSendStatus` (`FUN_00444020`) reads `pending+0x48` as the timeout multiplier.

⚠️ `Promos3TcpSocket_getStatus` auto-raises `unitAnswerTimeout` by 50 ms (capped at 500) on
slow units and **writes the new value back to the INI** — `"Auto adjusting timeout to %1 in
unit %2"`. The 300 ms in `PROVISsettings.ini` is a starting value, not a constant.

Related runtime strings, all consistent with a strict one-at-a-time discipline:
`"Trying to send several Canbus commands before answer is received, last command %1 new
command %2"`, `"-CAN: Received data without request"`, `"answer timedout, received"`,
`add_requestedMessage`, `m_requestedMessages`.

## 1.6 GUI-side signal graph

From `Promos3MainWindow_setupUi` (`FUN_0043dc70`), the key wiring:

| Emitter | Signal | → MainWindow slot |
|---|---|---|
| `Promos3DatenInstanz` (`FUN_00408a60`) | `NewMonitor(QString)` | `ConnectMonitorSignals` |
| `Promos3DatenInstanz` | `CurrentMonDisconnected()` | `OnMonitorDisconnected` |
| `Promos3DatenInstanz` | `selectedMonitorChanged(...)` | `updateAlarmBox` |
| NC comm (`FUN_00433a40`) | `showNCmsg(QString)` | `showMsgFromNC` |
| Button bar (`FUN_004f5fc0`) | `ButtonClicked(int)` | `On_PushButtonClicked` |

The Ethernet interface (`Promos3EthInterface`, `FUN_004fb1c0`) wires streaming and handshake
signals; disabled on this machine (`[Ethernet] Active=0`).

## 1.7 Lifecycle — bootstrap, offline mode, shutdown

- **`Promos3Interface_ctor` (`FUN_00402030`)** [tag-proven `"Promos3Interface"`] — the
  bootstrap. Acquires GlobaleDaten, ErrorManager, Translator, DatenInstanz,
  SqlDatenbankManager, NcComm and MessageCreator; calls `startInterface`; spins up the
  `KommandoVerteilerThread` and the Ethernet thread, starting the latter only if
  `[Ethernet] Active > 0`.
- **`Interface_setOfflineMode` (`FUN_0041c090`)** [tag-proven `"SetOfflineMode"`] — toggles
  offline, tears down and rebuilds the CAN and Ethernet threads, and persists `Offline` to
  the INI. Bound to `Ctrl+O` (`[Shortcuts] Offline`).
- **`Interface_onUnitConnected` (`FUN_00442b60`)** — wires `DataReceived` / `UnitDisconnected`,
  persists `LastUsedPort`, starts the poll timer.
- **`DatenInstanz_closeDevices` (`FUN_00411960`)** [tag-proven
  `"Promos3DatenInstanz::CloseDevices"`] — orderly shutdown. Per unit: close the DB through
  the SQL manager (type 1 `FUN_0044d0e0` / type 2 `FUN_0044d290`), send streaming-off for
  streaming units, disconnect and delete the per-unit timer, erase from the buffer map.
  Logs `"Closing succeed for %1 devices"`.

---

# ═══════════════════════════════════════════════════════════════
# PART 2 — TRANSPORT: THE GATEWAY AND CAN LAYER
# ═══════════════════════════════════════════════════════════════

## 2.1 Endianness ✅

- **CAN transport = BIG-ENDIAN.** The CAN-ID is read as `(buf[0x1A] << 8) | buf[0x1B]`
  (`CONCAT11(hi,lo)` in the decompiler), and written the same way on transmit.
- **Promos3 application payload = LITTLE-ENDIAN.** Proven by a config record:
  `ReduzLim = 6612 = 0x19D4` is stored on disk as the byte pair `D4 19`. Re-confirmed
  byte-for-byte against `1974.txt`.

Both directions of this were also verified by loopback during decoder testing: a
little-endian ramp read back as 0…248; big-endian produced garbage.

## 2.2 The 36-byte gateway record — receive ✅

```c
#pragma pack(push,1)
typedef struct {                 /* one CAN frame as delivered over UDP */
    uint8_t  gw_header[0x15];    /* +0x00  gateway header (see §2.3)     */
    uint8_t  len;                /* +0x15  CAN data length (0..8)        */
    uint8_t  gap[4];             /* +0x16                                */
    uint8_t  can_id_hi;          /* +0x1A  CAN-ID high byte (BIG-ENDIAN) */
    uint8_t  can_id_lo;          /* +0x1B  CAN-ID low byte               */
    uint8_t  data[8];            /* +0x1C  the CAN data bytes            */
} GatewayCanRecord;              /* 0x24 = 36 bytes                      */
#pragma pack(pop)

/* unit = ((can_id_hi << 8) | can_id_lo) - 1280 */
```

A UDP datagram is a **batch** of these. The remainder is trimmed from the **front**, not the
back — `QByteArray::remove(0, size % 0x24)` — which matters if you are re-implementing the
split. See the annotated snippet in §13.1.

## 2.3 The 36-byte gateway record — transmit ✅

Recovered from `CanInterface_writeGatewayRecord` (`FUN_00504290`). This had been called
"the empirical unknown"; it is neither empirical nor unknown.

```
off       value              source
0x00-01   00 24              record length 36, BIG-ENDIAN
0x02-03   00 80              constant (type/flags)
0x04-14   00 …               17 bytes of zero padding
0x15      LEN                TPCANMsg+5, the CAN DLC
0x16-19   00 00 00 00
0x1A      (ID >> 8) & 0xFF   BIG-ENDIAN
0x1B       ID       & 0xFF
0x1C-23   DATA[0..7]         copied as two dwords
```

**The entire header is `00 24 00 80` followed by zeros.** `MSGTYPE` (TPCANMsg+4) is *not*
transmitted. Destination address comes from `this+0x70` (QHostAddress) and port from
`*(u16*)(this+0x18)` — i.e. the INI's `[CAN] GatewayAddress` / `GatewayPort`.

The TX record is structurally identical to the verified RX record, which is worth exploiting:
confirming that *received* records also begin `00 24 00 80` establishes the symmetry for free
and validates the whole framing assumption in one line of a hexdump.

## 2.4 Reassembled CAN message — the internal form ✅

```c
typedef struct { uint32_t ID; uint8_t MSGTYPE; uint8_t LEN; uint8_t DATA[8]; } TPCANMsg;
/* gateway buf[0x1A:0x1B] (BE) → ID;  buf[0x15] → LEN;  buf[0x1C:0x23] → DATA[0:8] */
```

This is the PEAK PCAN standard 14-byte message struct. `LEN` at `+5` and `DATA` at `+6` were
confirmed from code (`canFrame_appendHex`, `FUN_00682010`), not inferred.

## 2.5 CAN-ID addressing ✅ ⚠️ SUPERSEDES §0.6 C4

```c
local_1c = *(int *)((int)this + 0x48) + unit;      /* FUN_00506220 */
```

**One base, both directions:** `CAN-ID = BaseCanIDTransfer + unit`, with
`BaseCanIDTransfer = 1280 = 0x500` from `[CAN]`, and `unit ∈ [FirstDevice, LastDevice] = 1…15`.
Independently confirmed by the settings dialog (`FUN_006da550`), which exposes exactly one
**"Base Tx"** field described as *"CAN transfer base address in hex"*, with First/Last unit
described as **offsets added to Base Tx**.

⚠️ **On the superseded three-base reading.** `Promos3CanInterface`'s constructor does set
three constants:

```c
this+0x48 = 0x500  /* 1280 — the transmit/receive base, confirmed */
this+0x54 = 0x580  /* 1408 — purpose unknown, NOT a transmit base */
this+0x58 = 0x600  /* 1536 — purpose unknown, NOT a transmit base */
this+0x4c = 1      /* first unit */      this+0x50 = 0x0F  /* last unit */
this+0x20 = 8      this+0x22 = 0x200 (BusID)   this+0x24 = 0x16 (BaudrateRegister)
this+0x44 = 0x32   this+0x30 = "ProcessControl"   this+0x34 = "sandvik"
```

The CANopen-shaped reading (`0x600+unit` master→slave, `0x580+unit` slave→master) was an
attractive hypothesis and it was wrong — `FUN_00506220` demonstrably transmits on
`0x48 + unit`. The two other constants exist and are unexplained; they are simply not
transmit bases. This mattered because it was briefly believed to be the direction
discriminator that would unblock passive capture. It is not, and passive capture turned out
not to be needed at all (§0.6 C18).

🔴 **Reader trap.** A reader that computes `unit = can_id - 1280` and drops anything
`>= MAX_UNITS` will map `0x580+n` and `0x600+n` to units 128+ and 256+ and silently discard
them. If those IDs ever appear in real traffic, you want them counted and logged, not
dropped in silence.

## 2.6 Reference network setup

```
Devices 10659 / 10663:  GType 0x44 (MSL5081-16), 1 channel, 4× PROCUR-S sensors
Gateway:                192.168.222.17:1789
                        PCANGateway=1  BaseCanIDTransfer=1280  BusID=512
                        BaudrateRegister=22  CanDeviceType=2  HardWareHandle=16  DriverNo=50
Unit sweep:             FirstDevice=1 … LastDevice=15
Ethernet streaming:     Active=0 (disabled), would-be ports 1789–1799, streaming 2789
Mazak NC:               TCP 57400 via NTIFDLL
```

## 2.7 Transmit retry ladder and gating

From `Promos3CanInterface::send` (`FUN_00506220`):

| status | meaning |
|---|---|
| `0x80` | busy — retry up to `this+0x28` times with `QThread::wait(5)` between attempts |
| `0x200` | CAN library missing, or the `CAN_Write` symbol could not be resolved |
| other | passed to `canApi_resolveAndCall("CanWrite", status)` |

- Gateway mode is selected by `this+0x14 > 0`; the socket must be in state 4 (`BoundState`).
- ⚠️ Stale received frames are flushed **at send time** (`UnitComm_deleteReceivedMessages`),
  not on receive. A reader that flushes on receive will behave subtly differently under loss.

## 2.8 Send queue behaviour

- `Promos3CanThread`'s outgoing queue is at `this+8`, a `QList<Promos3Paket*>`.
- **Cap 400; on overflow the entire queue is deleted**, not trimmed
  (`Promos3CanThread::clearSendQueue`, `FUN_00507360`).
- `routerKeyA` is a QString; the literal `"DOWNLOAD"` is a reserved target that bypasses
  de-duplication.
- Ownership of the `Paket` transfers to the queue; a de-dup hit `delete`s the incoming packet.
- De-duplication (`Promos3CanThread::sendCommandToUnit`, `FUN_005073f0`) applies **only to
  group 1** and **only to commands `0x16`, `0x08`, `0x01`, `0x12`** — exactly the periodically
  re-issued poll set (§3.9). Dedup key = (`routerKeyA`, `Paket+0x30` station,
  `Paket+0x28` command).

---

# ═══════════════════════════════════════════════════════════════
# PART 3 — THE `MC_` LINK LAYER (group 0/1) — **this installation**
# ═══════════════════════════════════════════════════════════════

Primary sources: `UnitComm_assembleAnswer_MC` (`FUN_00684160`), `promos3_checksum`
(`FUN_004425c0`), `Promos3Paket_ctorNull` (`FUN_00442650`), `Geraet_expectedRecordSize`
(`FUN_004c5840`), `UnitComm_firstReceivedPaket` (`FUN_00686430`),
`UnitComm_checkAnswerTimeout` (`FUN_00683e00`), `Promos3CanInterface::send` (`FUN_00506220`),
`CanInterface_searchForNewUnits` (`FUN_00506d10`), `Sende_Kom_MC_GIVESAMMELMERKMALE`
(`FUN_004d1310`).

## 3.1 The model: master/slave, request/answer

The v2 report modelled this as "device → app". It is not. It is **request → answer**, with:

- **one outstanding request per unit** at a time,
- `[CAN] unitAnswerTimeout = 300` ms (auto-raised in 50 ms steps to a cap of 500, §1.5),
- `[Comm] MaxResend = 1`,
- a **3 ms** polling loop driving the whole thing (`CanThread_onTimerTick`).

The runtime logs show the discovery sequence
`searchForNewUnits → registerUnit → bearbeite_Kom_06_MC_GIVEKONFIG` completing in a fixed
20–40 ms window, followed by `"unit N detected as not active, will be removed"` once polling
stops.

🔴 **Consequence for any passive tool: an idle bus carries nothing.** A listener on a machine
where PROVIS3 is not polling will sit silent forever and look broken while working perfectly.

## 3.2 🔴 Answers carry no command and no group ✅ (§0.6 C1)

At the end of `UnitComm_assembleAnswer_MC` the completed message object is built like this:

```c
group   = Paket_getGroup(requestPaket);          /* FUN_00436470 = *(u32*)request */
newMsg  = Promos3Paket_ctor(new(0x50), group, routerA, routerB, &assembledBytes, 0, 0);
newMsg[10] = local_13c;        /* +0x28 = command  <-- copied from the REQUEST */
newMsg[11] = requestPaket[11]; /* +0x2c */
newMsg[12] = requestPaket[12]; /* +0x30 */
```

where `local_13c = requestPaket[10]` — the command of the **request**, read at the top of the
function *before any answer byte is touched*.

> **`group` and `command` at `msg+0x00` / `msg+0x28` are inherited from the outstanding
> request. They are never parsed off the wire. The answer payload is pure record bytes.**

This retires the v2 open item "exact wire byte-offsets of `[group]/[command]/[length]`" —
**those fields do not exist on the `MC_` wire.** It also retires any `parse_message_header()`
in a reader: there is nothing to parse.

**The design consequence is the largest single fact in this project.** A message is only
identifiable in the context of the request it answers. A listener that sees only the
device→app direction sees anonymous byte blobs. This is why:

- a one-directional capture is worthless for this generation;
- even a purely *passive* reader must track requests and pair answers to them — which is most
  of the work of being the master anyway;
- **master mode is the recommended architecture** (§17.3).

## 3.3 Request wire format ✅ — byte-exact, verified twice

```
[command][station][params …][checksum]        ← the Paket byte buffer
 0x08     0x01               0xf6             ← logged, complete, verified
```

| cmd | byte 1 | byte 2 | byte 3 | byte 4 |
|---|---|---|---|---|
| `0x01` GIVESTATUS | — | — | — | — |
| `0x08` GIVEPLCVALUES | station | — | — | — |
| `0x0e` GIVEKANAL | station | — | — | — |
| `0x16` GIVESAMMELMERKMALE | station | `Geraet+0x688 ? 1 : 0` | — | — |
| `0x1b` GIVESIGNALVERLAUF | station | feature | p3 | p4 |
| `0x1c` GIVEOLDWORKPROZ | station | p3 | — | — |
| `0x1f` GIVEMUSTER | station | p3 | `(p4 & 0x0F) \| (p5 << 4)` | 0 |
| `0x23` GIVE_SENSORVALUES | round-robin slot index (`Geraet+0x60`, scanning `Geraet+0x4d0…`; slots 0–3 = features, 4–11 = sensors) | | | |

Qt4 places `QByteArray::Data`'s payload at `+0x10`, so `*(data + 0x11)` is wire byte 1 —
that is how the senders were read.

**`params[0]` is the station / device index (the `traceMap` key), not the channel** — §0.6 C15.
It reads `0x01` in both logged frames because this installation has one station, which is
exactly why the two candidate meanings were numerically indistinguishable. Confirmed three
ways: `bearbeite_Kom_15` reads `payload[0]` as the station and keys `traceMap` with it;
`Geraet_sendeKom_MC_GIVEKANAL` sets `this+0x54 = station`; `bearbeite_Kom_14` reads
`this+0x54` back as the `traceMap` key.

⚠️ **Requests are not always a single CAN frame.** The logged
`0x0c, 0x01, 0x61, 0xff, 0xff, 0xff, 0x00, 0x00` is `MC_SETZYKLUS`, station 1 — and a cycle
record is 170 bytes, so that request is multi-frame. The log dumper caps its output at 8
bytes, which is why the line looks complete. Long `SET…` commands are segmented like answers.
For the read-only poll set this is irrelevant: all of those requests are ≤ 4 payload bytes.

**Reserved feature selectors.** In the `0x1b` trace request, feature `0xFB` selects mode 1 and
`0xFD` selects mode 2. If the requested feature equals the station's current feature *and* a
per-feature node exists (`FUN_0048e500()` true), the sender rewrites the feature to `0xFD` and
takes mode 2. `0xFB` and `0xFD` are **not real feature indices** — a reader must not map them
through a feature-index lookup.

### 3.3.1 How the request buffer is built

`MsgCreator_createPaketForCommand` (`0x0042d190`) ✅:

```c
d = MsgCreator_lookupCmdDescriptor(this, …, group, &cmdByte, subCmd);
append(buf, (char)d[0]);                       /* wire command byte              */
if (group == 2) append(buf, (char)d[1]);       /* MC3_ only: the length byte     */
for (i = d[1]-1; i; i--) append(buf, '\0');    /* zero-fill to length            */
paket = Promos3Paket_ctor(new(0x50), group, srcTag, dstKey, &buf, d[2], param_6);
paket[10] = cmdByte;   /* +0x28 */
paket[11] = subCmd;    /* +0x2c */
```

| group | buffer | total |
|---|---|---|
| 0 / 1 (`MC_`) | `[cmd][00]×(len-1)` | `len` |
| 2 (`MC3_`) | `[cmd][len][00]×(len-1)` | `len + 1` |

Signature: `(this, group, srcTag, dstKey, cmdByte, subCmd, 1)`. Argument 7 is `1` at all 77
call sites. `cmd == 0` logs `"wrong command number for %1"` and returns NULL.

⚠️ **The buffer comes out zero-filled — the checksum is NOT written here.** Senders then poke
station and parameters in with `QByteArray_setByteAt`. The trailing byte is still `0x00` when
it leaves this function. The checksum is appended later, in the CAN interface (§3.5).

Full ctor signature, recovered from `FUN_0040a620`:
`Promos3Paket_ctor(mem, group, srcRouterObj, dstRouterObj, QByteArray, 0, 1)`.
Setting `Paket[10] = 0xFFFFFFFF` marks a raw / no-command packet.

## 3.4 Request framing onto CAN ✅

From `Promos3CanInterface::send` (`FUN_00506220`):

```
first frame:      [00][00][00][ up to 5 payload bytes ]     LEN = 3 + n
continuation N:   [seq][ up to 7 payload bytes        ]     LEN = 1 + chunk
```

The continuation counter pre-increments from 0, so the first continuation carries seq `1` and
the first frame's byte 0 is effectively seq `0` — symmetric with the answer direction.

⚠️ Bytes 1–2 of the first frame are written as zero and never assigned. Purpose unexplained.
The `DOWNLOAD` path reserves **2** bytes instead of 3 and prefixes a computed line count.

**For `MC3_` (group 2, command ≥ 3):** no reserved header, no sequence byte, 8 payload bytes
per frame.

**Worked example — the only request whose bytes are independently known:**

```
MC_GIVEPLCVALUES, unit 1, station 1
  Paket bytes : 08 01 f6                  ← matches LogFile-260701-T1154 exactly
  CAN-ID      : 0x501                     ← 1280 + 1
  DATA        : 00 00 00 08 01 f6         LEN = 6
```

Note how this reconciles two readings that looked contradictory: the log line
`requested 0x08, 0x01, 0xf6` shows the **Paket** bytes (command first), while the **CAN DATA**
field for that same request is `00 00 00 08 01 f6`. Both are correct; they are different
layers.

## 3.5 The checksum ✅ — recovered, byte-verified, confirmed twice

### 3.5.1 The algorithm

`promos3_checksum` (`FUN_004425c0`), signature
`(QByteArray *recv, char seed, QByteArray *sent, int group)`:

```c
signed char promos3_checksum(const uint8_t *recv, int recv_n,
                             signed char seed,              /* = unit id */
                             const uint8_t *sent, int sent_n,
                             int group)
{
    signed char ret = 0;
    if (!sent || (group != 0 && group != 1)) { ret = -1; seed = 0; }   /* invalid/foreign gen */
    if (sent && sent_n > 0) {
        for (int i = 0; i < sent_n - 1; i++) seed += sent[i];   /* ALL BUT THE LAST BYTE */
    } else if (group == 1) seed = 0;
    if (recv) for (int i = 0; i < recv_n; i++) seed += recv[i];
    return ret - seed;                                         /* two's complement */
}
```

In words: **an 8-bit two's-complement sum-check, seeded with the unit id, taken over
(the request bytes minus their own trailing checksum) plus (the whole assembled answer
payload).**

`sent_n - 1` is decisive — it proves **the last byte of a request is that request's own
checksum**, which is why it is excluded from the running sum.

### 3.5.2 Verification against a real logged frame ✅

`LogFile-260701-T1154.txt`:

```
12:08:42.060  waitingForData:  requested  0x08, 0x01, 0xf6,
```

```
seed = unit id = 1
sum of all but last = 0x08 + 0x01 = 0x09
checksum = -(1 + 9) = -10 = 0xF6      ← exactly the logged trailing byte
```

Recomputed for units 1/2/3 gives `0xF6 / 0xF5 / 0xF4`. **Only unit 1 matches**, which
incidentally identifies the unit of that log line. This is the first and (so far) only
byte-level verification of the live protocol in the whole project.

### 3.5.3 Independent second confirmation ✅

`FUN_00506220` computes the checksum inline, in a different form:

```c
seed = (group == 0 || group == 1) ? unit - 1 : 0;
for each payload byte: seed += byte;
checksum = -1 - seed;                    /* one's complement */
append to the byte array
```

Algebraically identical to the `FUN_004425c0` form: `-1 - (unit - 1 + Σ) = -(unit + Σ)`.
Both yield `0xF6` for unit 1. **Two independent code sites plus one real log line.**

⚠️ The checksum is appended **before** framing, so on a long request it lands wherever the
frame split puts it — not at a fixed position within a frame.

⚠️ **Open assumption:** the answer-direction seed is assumed symmetric with the request. It is
verified for requests only.

## 3.6 Answer frame layout ✅

Every answer frame is a `TPCANMsg`. Inside `DATA`:

```
DATA[0]           = sequence number, starts at 0, +1 per frame of this answer
DATA[1 .. LEN-2]  = payload bytes                       (up to 7 per frame)
DATA[LEN-1]       = checksum  — ONLY on the final frame, and only if it fits
```

Straight out of the assembly loop:

```c
uVar17 += (byte)frame[5] - 1;                 /* usable bytes per frame = LEN-1     */
...
local_140++;                                   /* starts at -1 → first expected seq = 0 */
if ((byte)frame[6] != local_140) -> "Unknown answer format received on CAN bus for command %1"
...
avail = frame[5] - 1;
if (avail > expected - accumulated) avail = expected - accumulated;   /* clamp */
for (i = 1; i <= avail; i++) QByteArray::append(&buf, frame[6+i]);    /* DATA[1..avail] */
```

and the terminator:

```c
if (avail == 7) {                              /* frame was full: no room for the checksum */
    frame2 = takeFirst(recvList);
    if (frame2[5] == 2 && frame2[6] != 0) ck = frame2[7];   /* LEN==2 → [seq][checksum] */
    else -> "Error, expected Checksum-only message was not received for command %1"
} else {
    ck = frame[5 + frame[5]];                  /* = DATA[LEN-1], the byte after the payload */
}
```

So **`payloadPerFrame = 7`**, and:

| condition | where the checksum lives |
|---|---|
| `expectedSize % 7 != 0` | last byte of the last data frame (`DATA[LEN-1]`) |
| `expectedSize % 7 == 0` | a **separate 2-byte frame** `[seq][checksum]` |

🔴 A reader that does not know about the checksum-only frame will treat it as a truncated
data message.

**Worked example, `cmd 0x0e` (`GIVEKANAL`, 144 bytes from the size table):**
`⌈144/7⌉ = 21` frames — 20 × `LEN=8` (seq + 7 payload), then `LEN=6` (seq + 4 payload +
checksum). `144 % 7 = 4 ≠ 0`, so no checksum-only frame.

## 3.7 Completion rule and the expected-size table ✅ (§0.6 C3, C16)

```
expected = Paket.recvSize (+0x14)
   ├─ normal:   stamped at SEND time from Geraet_expectedRecordSize(cmd)
   ├─ cmd 0x16: computed from the first frame →  expected = DATA[1] * Paket.recordSize(+0x34) + 1
   └─ cmd 0x14: on checksum failure, retried with expected = 0x24 (36)   ← version fallback
accumulate 7 payload bytes per frame while (accumulated < expected)
then validate the checksum; on mismatch roll the frames back (prepend) and retry, else deliver
```

The missing link that Part 15 was looking for is the call
`Paket_setRecvSize(paket, Geraet_expectedRecordSize(this, 0x0e))` inside the `GIVEKANAL`
sender: **the size table is consulted at send time and stamped into `Paket+0x14`, which is
exactly the `expected` the answer assembler counts down.** The table is therefore *expected
answer size keyed by command*.

### 3.7.1 `Geraet_expectedRecordSize(komNr)` — `FUN_004c5840` ✅

A flat switch keyed by command number; an unknown key logs `"Versionsfehler"` and returns −1.

| cmd | bytes | note |
|---|---|---|
| `0x02`, `0x28` | 14 | `SGrenzRec` ✅ |
| `0x03` | 170 | `SZykRecV4802` ✅ ⚠️ odd for a SET command |
| `0x04` | 4 | |
| `0x05` | 16 | |
| `0x08`, `0x09`, `0x0c` | 1 | one-byte ack — consistent with every `SET…` returning an ack |
| `0x0e` | **144** | `SKanalRecV40` ✅ **call-site verified** |
| `0x0f` | 40 | |
| `0x10` | 46 | `SHardwareRec` ✅ ⚠️ but `GIVEHARDWAREREC` is `0x1a`, not `0x10` |
| `0x11` | 2 | |
| `0x35`, `0x3f` | 20 | |
| `0x36` | 60 | |
| `0x37` | 64 | |
| `0x38` | 160 | |

⚠️ **Three entries do not align with the recovered command names:** `0x03` (`SETANZMODE` →
170, a cycle-record size), `0x10` (→ 46, a hardware-record size, but `GIVEHARDWAREREC` is
`0x1a`), and `0x3f` (→ 20, with no name recovered). The pattern suggests some entries are
keyed by **record type** rather than by command. Unresolved, and worth remembering before
trusting an unverified entry.

⚠️ **`expected == 0`** → the answer is a pure acknowledgement. The device replies with a single
frame whose `DATA[1]` *is* the checksum. Failure text:
`"CheckSum fail for Receive Size zero in command %1, try again"`.

⚠️ **`cmd 0x30` (`CIAB_COMMAND`) with subtype 2 or 4** → segmented transfer. `Paket+0x3c`
(offset) and `Paket+0x40` (total); if `offset < total` the assembler **queues a follow-up
request itself** for the next chunk. This is the download / large-record path.

## 3.8 Error answers, retry ladder, timeouts

**Device error answer** 🔴 — a frame with `DATA[0] == 0 && DATA[1] == 1` **and `LEN == 2`** →
`"Error answer in CAN bus for command %1"`.

> The `LEN == 2` constraint is §0.6 C20 and it is not optional. Without it the signature is
> identical to a healthy first data frame whose first payload byte is 1 — which for `0x16`
> means "one row", the single most common case there is. A reader missing this constraint
> discards most live measurement data and counts it as device errors. This was found by
> *writing and testing* the link layer, not by reading code; the constraint itself is marked
> as an inference to confirm against a real capture.

Anything else unexpected → `"Unknown answer format received on CAN bus for command %1"`.

**Retry ladder** (`UnitComm+0x20` attempts vs `UnitComm+0x34` max, INI `[Comm] MaxResend=1`):
`try again` (status 1 — re-arm the same request with the saved size in `DAT_00a1fc54`) →
`aborting` (status 2 — `UnitComm_clearRequestQueue` drops the request queue and
`UnitComm_deleteReceivedMessages` flushes the frames).

**Status codes** returned by `UnitComm_checkAnswerTimeout` (`FUN_00683e00`): 0 / 1 / 3 / 4,
used as: 1 = retry, 2 = abort, 3 = not active (removal), 4 = incomplete.

The full checksum-failure string family, useful for recognising the behaviour in logs:

```
CheckSum error, ID %1 comm %2 feature %3 Received data %4
Wrong checksum for unit %1 command %2, try again
Wrong checksum after several attempts for unit %1 command %2, aborting
Error, expected Checksum-only message was not received for command %1
Accumulated errors in answer for command %1. Wrong checkSumOK, received %2, expected %3
CheckSum fail for Receive Size zero in command %1, try again
Checksum error! resend from %1                       ← implies resume-from-offset on download
Wrong number of bytes for command %1, copiedBytes: %2 of %3
```

## 3.9 Unit discovery ✅

`CanInterface_searchForNewUnits` (`FUN_00506d10`):

- Rescan gate `DAT_00a17914 = unitAnswerTimeout × 3` = **900 ms**. ⚠️ This is where the INI's
  `[Comm] unitActiveTimeout = 900` comes from — it is **derived**, not an independent setting.
- Sweeps units `this+0x4c … this+0x50` (1–15). Unknown → candidate. Known →
  `UnitComm_checkAnswerTimeout`; status 3 → `"unit %1 detected as not active, will be
  removed"` → `unitBuffer_remove`.
- Probes **one** candidate per pass, round-robin via `DAT_00a1bc2c`, builds `MC_GIVESTATUS`
  with **group 0**, and `QList_prepend`s it — probes jump the queue.
- `Router_registerUnit` (`FUN_004156a0`) then logs `"Unit N registered"`; the group-0 arm of
  the dispatcher sends `MC_GIVEGTYPE`; `FUN_00412290` decides the generation; everything
  after that is group 1 or 2.

Observed in the log exactly as described:

```
11:53:31.775  searchForNewUnits:  unit 2 detected as not active, will be removed
11:53:41.116  searchForNewUnits:  unit 1 detected as not active, will be removed
11:53:43.918  registerUnit:       Unit 1 registered
11:53:43.946  bearbeite_Kom_06_MC_GIVEKONFIG:  Version 229 Channels 1 Sensors 4
11:53:46.624  registerUnit:       Unit 2 registered
```

## 3.10 The poll cycle ✅

`Sende_Kom_MC_GIVESAMMELMERKMALE` (`FUN_004d1310`) does not send one command. It sends the
whole cycle:

```
gate: this+0x28 == 0

for station = 1 .. channelCount:      send 0x16   MC_GIVESAMMELMERKMALE   (priority 2)
for station = 1 .. channelCount:      send 0x08   MC_GIVEPLCVALUES        (via FUN_004cd650)
send 0x01                             MC_GIVESTATUS                       (via FUN_004c65d0)
```

Stations already present in `traceMap` with a live node are skipped for `0x16`.

**Corroborated independently by the de-duplication filter** in
`Promos3CanThread::sendCommandToUnit`, which suppresses duplicate queue entries only for
group 1 and only for these commands — i.e. exactly the periodically re-issued set:

| cmd | name |
|---|---|
| `0x01` | `MC_GIVESTATUS` |
| `0x08` | `MC_GIVEPLCVALUES` |
| `0x12` | `MC_GIVEALARM` |
| `0x16` | `MC_GIVESAMMELMERKMALE` — the live measurement block |

⚠️ `Paket_setPriority(…, 2)` puts an item at the front of the queue. A priority queue exists
and can safely be ignored while only one request is outstanding.

---

# ═══════════════════════════════════════════════════════════════
# PART 4 — THE `MC3_` LINK PROTOCOL (group 2) — a **different** protocol
# ═══════════════════════════════════════════════════════════════

**Not used by this installation.** Documented in full because the same binary serves both
generations, and because the group-2 model is what the earlier `[group][command][length]` header
description was actually describing (Part 20 §20.1).

**Source:** `UnitComm_assembleAnswer_MC3` (`FUN_00685940`, tag-proven `"ReceiveProvis3Paket"`),
read side by side with `FUN_00684160`.

## 4.1 No sequence byte — 8 payload bytes per frame ✅

```c
iVar13 += (byte)frame[5];                              /* LEN, not LEN-1  */
...
for (i = 0; i < take; i++) QByteArray::append(&buf, frame[6 + i]);   /* DATA[0..], not DATA[1..] */
```

`MC_` burns `DATA[0]` on a sequence counter and carries 7 bytes per frame. **`MC3_` carries 8 and
has no sequence number at all** — and therefore no per-frame ordering check, no
rollback-and-retry of individual frames, and no checksum-only frame.

## 4.2 Command and length **are** on the wire ✅

```c
if (this->inProgress /*+0x24*/ == 0) {                 /* first frame of a new answer */
    req = requestQueue.front();
    if (req && (uint)req[0x28] > 2) {
        DAT_00a1fc5c = (byte)frame[6];                 /* DATA[0] = COMMAND */
        DAT_00a1fc58 = (byte)frame[7];                 /* DATA[1] = LENGTH  */
        if (LEN == 0) -> "NULL CAN Answer received for command %1"
        if (req[0x28] != DAT_00a1fc5c) -> "Wrong package received. Requested command: %1"
```

So an `MC3_` message is `[command][length][body …][checksum]`, total = `length + 1` bytes, and the
app cross-checks the answer's command against the request's.

The checksum is the last byte; it is stripped, then `QByteArray::remove(buf, 0, 2)` strips
command + length — **confirming that an `MC3_` decoder body starts at message offset 2**.

⚠️ **Quirk.** The header parse is gated on `req[0x28] > 2`, so `MC3_` commands `0x01`/`0x02`
(`GIVESTATUS`/`GIVEGTYPE`) never take this path and the function returns NULL for them.
Presumably the handshake is serviced elsewhere; confirm before assuming a reader can see `MC3_`
status/gtype answers.

## 4.3 The 16-bit length extension for ALARM / EVENT ✅

```c
if ((cmd == 0x0f || cmd == 0x10) && frame[8] /*DATA[2]*/ == 1) {
    u16 asked = LE16(request.data[0], request.data[1]);
    if (asked == 0xFFFF)
        DAT_00a1fc58 = CONCAT11(frame[9], frame[7]);   /* len16 = (DATA[3] << 8) | DATA[1] */
}
```

Three independent cross-confirmations of the alarm/event body model (§6.4, §6.6) fall out of this
one branch:

- `0x0f` / `0x10` really are ALARM / EVENT;
- `DATA[2] == 1` is the *"subcommand 1 = alarm data"* that was previously inferred;
- `0xFFFF` really is the *"give me everything"* request id.

When the app asks for all entries, the length promotes to a **split 16-bit field** — low byte in
`DATA[1]`, high byte in `DATA[3]`. **A reader that assumes an 8-bit length will truncate every
full alarm or event dump.**

## 4.4 A different checksum ✅

```c
computed = FUN_004425c0(&buf, 0, NULL, 2);     /* seed 0, no sent buffer, group 2 */
```

With `sent == NULL` the shared helper takes its `ret = -1` branch and zeroes the seed, so it
reduces to:

```
checksum = -1 - Σ(message bytes)          i.e. one's complement of the byte sum
⟺  Σ(all bytes including the checksum) == 0xFF
```

Verified numerically. Compare `MC_`: `-(unitId + Σ request[0..n-2] + Σ payload)` — two's
complement, seeded, and spanning *both* directions. **Same helper, two genuinely different
schemes, selected by the `group` argument.**

## 4.5 Streaming (two more framings, both `MC3_`-only)

`UnitComm_receiveMonitoringData` (CAN, queue at `this+0x0c`) and `EthSocket_streamingDataReceived`
(Ethernet). Layout `[cmd][id16][?]` with `len + 4` total, a per-command length table derived from
the live feature count, and the checksum invariant `Σ == 0xFF`.

| streaming cmd | CAN | Ethernet |
|---|---|---|
| 1 | features×4 | features×4 |
| 2 | sub-table (`DATA[5]`) | same |
| 3, 5, 7 | `0x0D` | **`0x0B`** |
| 4, 6 | features×2+1 | same |
| 9 | 4 | 4 |

Both gate on `getTargetType == 2`. **On this `MC_` box the streaming path never produces
anything** — it is dead code here. Delivered as a group-2 Paket with command 7, the real type in
`+0x2c`.

Streaming is turned on and off by `Provis3Geraet_sendKom07_SetStreaming` (`FUN_004c1090`,
tag-proven `"…Sende_Kom_07_MC3_SET_STREAMING"`), which writes the flag at stream `+0x12` and
appends it as a payload byte — independently confirming that command 7 is `SET_STREAMING`.

## 4.6 Side-by-side comparison

| | **`MC_`** (group 0/1) — *this box* | **`MC3_`** (group 2) |
|---|---|---|
| per-frame overhead | `DATA[0]` = sequence number | none |
| payload per frame | **7** | **8** |
| command on the wire | **no** — taken from the request | **yes** — message byte 0 |
| length on the wire | **no** — from `Geraet_expectedRecordSize()` | **yes** — byte 1 (16-bit for `0x0f`/`0x10`) |
| total size | `expectedSize` from the table | `lengthByte + 1` |
| checksum position | last payload byte, or a separate `[seq][ck]` frame | last message byte |
| checksum algorithm | `-(unit + Σ sent[0..n-2] + Σ payload)` | `-1 - Σ msgBytes` |
| body starts at | offset 0 (payload is a pure record) | offset 2 |
| ordering check | sequence continuity, with rollback + retry | none |
| identifiable passively? | **no** | **yes** |
| request framing | `[00][00][00][5B]` then `[seq][7B]` | no reserved header, 8B/frame |
| sub-command | — | senders write it at `data[2]`, payload from `data[3]` |

**Portability verdict:** a reader **cannot** share a framing layer between generations. Two
front-ends, one dispatcher. For this installation only the `MC_` path is required; the `MC3_` path
is now specified well enough to write if another site needs it.

---

# ═══════════════════════════════════════════════════════════════
# PART 5 — COMMAND DISPATCH
# ═══════════════════════════════════════════════════════════════

German terms used throughout: `Kom` = Kommando (command); `bearbeite` = process/parse (device→app);
`Sende` = send (app→device); `Geraet` = device; `Merkmal` = feature; `Kanal` = channel;
`Zyklus` = cycle; `Signalverlauf` = signal trace; `Grenz` = limit; `Konfig` = configuration.
`MC_*` = Provis2 generation; `MC3_*` = Promos3 generation.

`Kom_NN` in the app's own tag strings is **decimal**, so `bearbeite_Kom_27` = command `0x1B`.

## 5.1 The dispatch model 🔶

After assembly, the message object is dispatched by `Command_Dispatch_Switch` (`FUN_004125d0`,
`this` = the `Promos3DatenInstanz` singleton) on **two** fields:

```c
group   = *(u32*)(msg + 0x00);               // via FUN_00436470 (Paket_getGroup)
command = *(u32*)(msg + 0x28);
switch (group) {
  case 0: /* handshake: cmd 1 = MC_GIVEGTYPE, cmd 2 = FUN_00412290 */ break;
  case 1: switch (command) { /* MC_ table, §5.2 */ } break;
  case 2: switch (command) { /* MC3_ table, §5.3 */ } break;
}
FUN_004428e0(msg); operator_delete(msg);     // dispatcher owns + frees the message
```

- `group` selects the protocol family: **0 = handshake, 1 = `MC_` (legacy Provis2),
  2 = `MC3_` (modern Promos3)**.
- The same command number means different things per group — e.g. command `0x1B` is
  `MC_GIVESIGNALVERLAUF` in group 1 but `MC3_SET_OUTPUTS` in group 2.
- These are **object** fields, **inherited from the outstanding request** (Part 3.1), not parsed
  from the wire.

**Leaf routing pattern (uniform across nearly all handlers):**

```c
station = packet_getStation(msg);            // sender unit key
unit    = resolveTarget(this);               // FUN_00409ca0, mutex "Vorverarbeitung_Kom"
if (unit && this->quitFlag == 0 && getTargetType(unit) == GEN)   // GEN==1 for MC_, ==2 for MC3_
    worker(unit, msg);                       // the actual byte-parser
```

`getTargetType` (`FUN_0047fde0`) returns the unit's generation (`*(u32*)(unit+0x0c)`):
**1 = Provis2/`MC_`, 2 = Promos3/`MC3_`**. On this box it is **1**.

**Packet validation** happens before dispatch: `Packet_checkCommandKnown` (`FUN_00404dc0`,
tag-proven `"ID_FEHLER_PAKET_KOM_NULL/UNBEKANNT"`) validates that the command at `+0x28` is in
`1..0xFF`; `Packet_checkExpectedEnAll` (`FUN_00404790`, tag-proven
`"Untersuche_enAll_PaketaufFehler"`) rejects any command not in `{1,2}` and logs
`"Expected cmd %1, received %2"`.

## 5.2 GROUP 1 (`MC_`) — **implement these** ✅/🔶

Switch on `msg+0x28` when `group==1` / `getTargetType==1`. Names were recovered by grepping the
binary's own `Sende_Kom_*` / `bearbeite_Kom_*` tag strings; handler addresses come from the
dispatch switch. **~35 of the 41 dispatch case labels are now named.**

Confirmed live in the runtime log: cmd `0x06` logged
`bearbeite_Kom_06_MC_GIVEKONFIG: Version 229 Channels 1 Sensors 4`.

| cmd | name | receive handler | notes |
|---|---|---|---|
| 0x01 | `MC_GIVESTATUS` | FUN_0040ab10 | sent as **group 0** during discovery; ⚠️ never calls `setRecvSize` |
| 0x02 | `MC_GIVEGTYPE` | FUN_00412290 | shared with group-0 cmd 2; expected size 14 |
| 0x03 | `MC_SETANZMODE` | *(send-only)* | ⚠️ size-table entry 170 does not fit a SET command |
| 0x04 | `MC_GIVEMERKMAL` | FUN_0040acb0 | expected size 4 |
| 0x05 | `MC_GIVEUSEDZYKTAB` | FUN_0040ad00 | expected size 16 |
| **0x06** | **`MC_GIVEKONFIG`** | **FUN_0040a8f0** | device config; worker `FUN_004cd420`; logs "Version N Channels C Sensors S" ✅ |
| 0x08 | `MC_GIVEPLCVALUES` | FUN_0040a950 | in the poll set; sender `FUN_004cd650`; size branch = D4 |
| 0x09 | `MC_SETPLCVALUES` | *(send-only)* | ack (1 byte) |
| 0x0a | `MC_SETGERAET` | FUN_0040a9a0 | |
| 0x0b | `MC_SETKANAL` | *(send-only)* | |
| 0x0c | `MC_SETZYKLUS` | FUN_0040a9f0 | shared handler with 0x32; ack (1 byte); multi-frame request |
| 0x0d | *(unnamed)* | FUN_0040aa40 | sets the selected monitor if the station is unknown |
| 0x0e | `MC_GIVEKANAL` | FUN_0040ab70 | expected **144** = `SKanalRecV40` ✅ call-site verified; sender `FUN_004d0320` |
| 0x0f | `MC_GIVEZYKLUS` | FUN_0040abc0 | expected size 40 |
| 0x11 | `MC_ALARMGESEHEN` | *(send-only)* | expected size 2 |
| **0x12** | **`MC_GIVEALARM`** | **FUN_0040ac60** | in the poll set; ⚠️ true expected size unknown (D3) |
| 0x13 | `MC_QUITALARM` | *(send-only)* | |
| 0x14 | *(unnamed)* | FUN_0040b0c0 | ⚠️ on checksum failure retried with expected `0x24` (36) — version fallback |
| 0x15 | `MC_PRESSEDKEYS` | *(qDebug only)* | logs, no decode. Literal `case 0x15: qDebug() << "MC_PRESSEDKEYS"` |
| **0x16** | **`MC_GIVESAMMELMERKMALE`** | **FUN_0040ad50** | "collected features" — **the live measurement block** (§6.2); sender `FUN_004d1310` |
| 0x18 | `MC_GIVETEACHSTATUS` | FUN_0040ada0 | |
| 0x1a | `MC_GIVEHARDWAREREC` | FUN_0040aee0 | sender `FUN_004c6b90`; ⚠️ size table puts 46 (`SHardwareRec`) at 0x10, not 0x1a |
| **0x1b** | **`MC_GIVESIGNALVERLAUF`** | **FUN_0040af30** | → `bearbeite_Kom_27` (FUN_004d1b70) → `decodeSignalTrace_B`. **THE live amplitude trace** ✅; sender `FUN_004d1810` |
| 0x1c | `MC_GIVEOLDWORKPROZ` | FUN_0040adf0 | sender `FUN_004d1de0` |
| 0x1f | `MC_GIVEMUSTER` | FUN_0040ae40 | sender `FUN_004d23d0` (packed-nibble param) |
| 0x21 | `MC_GIVE_CDR_DATA` | FUN_0040ae90 | |
| 0x23 | `MC_GIVE_SENSORVALUES` | FUN_0040af80 | sender `FUN_004ce000`, round-robin sensor index |
| 0x24 | `MC_SET_SENSORVALUES` | FUN_0040afd0 | |
| 0x25 | `MC_GIVE_ACTZYKINDEX` | FUN_0040ac10 | |
| 0x27 | `MC_GIVE_EINZEL_TEACH` | FUN_0040b020 | |
| 0x28 | `MC_GIVE_EINRICHTEN_STATUS` | FUN_0040b070 | expected size 14 (`SGrenzRec`) |
| 0x29 | *(unnamed)* | FUN_0040b110 | worker `FUN_004dc3e0`: parse record, timestamp, store, GUI update |
| 0x2a | *(unnamed)* | FUN_0040b160 | |
| 0x2b | *(unnamed)* | FUN_0040b1b0 | |
| 0x2c | `MC_SET_DSP_GERAET` | FUN_0040b200 | |
| 0x2d | `MC_DSP_STANDARD` | FUN_0040b250 | |
| 0x30 | **`MC_CIAB_COMMAND`** | FUN_0040b2a0 | **segmented transfer** (subtype 2/4); `Paket+0x3c`/`+0x40` = offset/total |
| 0x32 | `MC_SETZYKLUSWITHTIME` | FUN_0040a9f0 | shared handler with 0x0c |
| 0x33 | `MC_GIVEPROGID` | FUN_0040b2f0 | |
| 0x34 | *(unnamed)* | FUN_0040b340 | |
| 0x35 | `MC_GIVE_ACF_INFO` | FUN_0040b390 | expected size 20 |
| 0x36 | `MC_SET_ACF_INFO` | FUN_0040b3e0 | expected size 60 |
| 0x37 | `MC_SET_ACF_INFO_INTERN` | FUN_0040b480 | shared handler with 0x39; expected size 64 |
| 0x38 | `MC_GET_WKS_ID` | FUN_0040b430 | expected size 160 |
| 0x39 | `MC_GET_ACF_DATA` | FUN_0040b480 | shared handler with 0x37 |
| 0x3c | `MC_GET_GERAET_ACF` | FUN_0040b4d0 | sender `FUN_004c7000` |
| default | — | drop | |

**Self-checks that validate the naming:** `0x0c`/`0x32` share a handler because they are
`SETZYKLUS` and `SETZYKLUSWITHTIME`; `0x16 = GIVESAMMELMERKMALE` ("collected features") is exactly
the command with the computed `count × recordSize + 1` length; `0x30 = CIAB_COMMAND` is exactly
the command with segmented transfer; and `Kom 21 = 0x15 = PRESSEDKEYS` appears as a literal in
code.

There is also an **`MC_` name→command-byte registry** in the message creator, reachable as
`MsgCreator_getCommandByte(creator, 1, "MC_GIVEKANAL")`. Dumping its table would give the
authoritative group-1 command list to cross-check the string-derived names above. Not yet dumped.

## 5.3 GROUP 2 (`MC3_`) — for other sites, NOT used by this box

### 5.3.1 The authoritative command registry ✅

Recovered verbatim from `MsgCreator_buildMC3Registry` (`FUN_0042b1f0`), the message-creator's own
name↔code table (map at object `+0x14`). **This is the authoritative naming source** — it is what
the binary itself uses, independent of the dispatch switch.

| Code | Name | Code | Name |
|---|---|---|---|
| 0x00 | `MC3_UNKNOWN` | 0x12 | `MC3_DEVICE_DESCRPTION` *(sic)* |
| 0x01 | `MC3_GIVESTATUS` | 0x13 | `MC3_EXTRACYCLE_INFO` |
| 0x02 | `MC3_GIVEGTYPE` | 0x14 | `MC3_EXTRALIMIT_INFO` |
| 0x03 | `MC3_GET_CB_VERSION` | 0x15 | `MC3_EXTRA_SENSOR_VFAKT` |
| 0x04 | `MC3_SENSOR_INFO` | 0x16 | `MC3_EXTRA_FEATURE_INFO` |
| 0x05 | `MC3_FEATURE_INFO` | 0x18 | `MC3_SYSTEM_MODE` |
| 0x06 | `MC3_DEVICEREC` | 0x19 | `MC3_LICENSE_INFO` |
| 0x07 | `MC3_SET_STREAMING` | 0x1a | `MC3_PATTERN_INFO` |
| 0x08 | `MC3_LIMIT_INFO` | 0x1b | `MC3_SET_OUTPUTS` |
| 0x09 | `MC3_CYCLE_INFO` | 0x1c | `MC3_ETH_MAC_ADDRESS` |
| 0x0a | `MC3_PLC_SETTINGS` | 0x3a | `DownloadHexFile` |
| **0x0b** | **`MC3_SENSOR_VFAKT`** | 0x99 | `MC3_DOWNLOAD_IDENTIFIER` |
| 0x0c | `MC3_FEATURE_INCYCLE_SETTINGS` | | |
| 0x0d | `MC3_DEVICE_SETTING` | | |
| 0x0e | `MC3_SYSTEM` | | |
| 0x0f | `MC3_ALARM` | | |
| 0x10 | `MC3_EVENT` | | |
| **0x11** | **`MC3_LAST_SIGNAL`** | | |

⚠️ **The sender tags are not a reliable second source for `MC3_` code↔name.** Most
`Sende_Kom_NN_MC3_*` tags agree with the registry when `NN` is read as **decimal** — `Kom_10` →
`0x0a` PLC_SETTINGS ✔, `Kom_11` → `0x0b` SENSOR_VFAKT ✔ (which independently corroborates §0.6
C10), `Kom_13` → `0x0d` DEVICE_SETTING ✔, `Kom_14` → `0x0e` SYSTEM ✔, `Kom_15` → `0x0f` ALARM ✔,
`Kom_16` → `0x10` EVENT ✔, `Kom_24` → `0x18` SYSTEM_MODE ✔. But there are two exceptions:

- `Sende_Kom_99_MC3_DOWNLOADFILE` matches `0x99` in **hex**, not `0x63` in decimal.
- `FUN_004b1540`'s tag reads `Sende_Kom_04_MC3_MERKMAL_INFO` (*Merkmal* = feature), while the
  registry puts `MC3_SENSOR_INFO` at `0x04` and `MC3_FEATURE_INFO` at `0x05`.

The numbering convention is therefore inconsistent. 🔴 **Treat the registry as authoritative for
`MC3_` code↔name; treat the sender tags as corroboration only.**

### 5.3.2 The dispatch table

Switch on `msg+0x28` when `group==2`. Anchor proof: cmd `0x0F → FUN_0040c400` = the alarm
dispatcher (`bearbeite_Kom_15`).

| cmd | registry name | handler | notes |
|---|---|---|---|
| 0x03 | `MC3_GET_CB_VERSION` | FUN_0040b830 | sender `FUN_004ace30` |
| 0x04 | `MC3_SENSOR_INFO` | FUN_0040b880 | → `bearbeite_Kom_04` (FUN_004bc090); §6.5. Sender `FUN_004b1540` is tagged `MC3_MERKMAL_INFO` |
| 0x05 | `MC3_FEATURE_INFO` | FUN_0040b8d0 | German alias in handler tags: `MC3_MERKMAL_INFO` |
| 0x06 | `MC3_DEVICEREC` | FUN_0040b920 | German alias in handler tags: `MC3_GERAETEREC`; sender `FUN_004b1da0` |
| 0x07 | `MC3_SET_STREAMING` | FUN_0040b9e0 | confirmed independently by `FUN_004c1090` |
| 0x08 | `MC3_LIMIT_INFO` | FUN_0040c1d0(msg,0) | flag-paired with 0x14; sender `FUN_004b1fd0` |
| 0x09 | `MC3_CYCLE_INFO` | FUN_0040c220(msg,0) | flag-paired with 0x13; sender `FUN_004b26a0` |
| 0x0a | `MC3_PLC_SETTINGS` | FUN_0040c270 | sender `FUN_004b3240` |
| 0x0b | `MC3_SENSOR_VFAKT` | FUN_0040c2c0 | same handler as 0x15; sender `FUN_004b3550` |
| 0x0c | `MC3_FEATURE_INCYCLE_SETTINGS` | FUN_0040c310 | same handler as 0x16 |
| 0x0d | `MC3_DEVICE_SETTING` | FUN_0040c360 | sender `FUN_004b50e0` |
| 0x0e | `MC3_SYSTEM` | FUN_0040c3b0 | sender `FUN_004b5490` |
| **0x0f** | **`MC3_ALARM`** | **FUN_0040c400** | → `bearbeite_Kom_15` (FUN_004b5ba0) — the anchor; §6.4. Sender `FUN_004b5830` |
| **0x10** | **`MC3_EVENT`** | **FUN_0040c450** | → `bearbeite_Kom_16` (FUN_004b6580); §6.6. Sender `FUN_004b6380` |
| **0x11** | **`MC3_LAST_SIGNAL`** | **FUN_0040c5e0** | worker `FUN_004acf40` = `return p != 0` — a **STUB** |
| 0x13 | `MC3_EXTRACYCLE_INFO` | FUN_0040c220(msg,1) | CYCLE_INFO variant |
| 0x14 | `MC3_EXTRALIMIT_INFO` | FUN_0040c1d0(msg,1) | LIMIT_INFO variant |
| 0x15 | `MC3_EXTRA_SENSOR_VFAKT` | FUN_0040c2c0 | same handler as 0x0b |
| 0x16 | `MC3_EXTRA_FEATURE_INFO` | FUN_0040c310 | same handler as 0x0c |
| 0x18 | `MC3_SYSTEM_MODE` | FUN_0040c4a0 | sender `FUN_004b6ac0` |
| 0x1a | `MC3_PATTERN_INFO` | FUN_0040c4f0 | |
| **0x1b** | **`MC3_SET_OUTPUTS`** | **FUN_0040c540** | → `bearbeite_Kom_27` (FUN_004b9150); "Outputs successfully set" — **NOT a trace** |
| 0x1c | `MC3_ETH_MAC_ADDRESS` | FUN_0040c590 | |
| 0x3a | `DownloadHexFile` | FUN_0040c680 | |
| 0x99 | `MC3_DOWNLOAD_IDENTIFIER` | FUN_0040c630 | sender `FUN_004af1e0` / `FUN_004ba490` |
| default | — | drop | |

**Flag-paired workers** (a bool selects the variant): `0x08 ↔ 0x14` (FUN_0040c1d0),
`0x09 ↔ 0x13` (FUN_0040c220).

`MC3_` senders write the sub-command at `data[2]` and the payload from `data[3]`.

## 5.4 GROUP 0 — handshake / new unit

Switch on `msg+0x28` when `group==0`. Group 0 means **"generation not yet known"** and uses
`MC_` framing.

- cmd 1: **`MC_GIVESTATUS`** — sent by `Router_registerUnit` as the discovery probe.
- cmd 1 also covers **`MC_GIVEGTYPE`** device-type handshake: if the station is unknown, the app
  *sends* a `MC_GIVEGTYPE` request.
- cmd 2: → `FUN_00412290` (`DatenInstanz_handleGTypeAnswer`, shared with group 1 cmd 2) — this is
  the function that **decides the generation**. Everything after it goes out as group 1 or 2.

## 5.5 `MC3_` per-command field-descriptor table 🔶

The second map built by `MsgCreator_buildMC3Registry` (object `+0x18`) is keyed by command code
and holds a **per-command list of field descriptors**. Each descriptor is inserted by
`FUN_00428000(list, key, &field_tag, &{cmd, A, B})` and the completed list is committed per
command by `FUN_0042b070`. The descriptor is three consecutive dwords:

```
field_tag  (map key, e.g. 1,2,3,4,8,0x10,0x11,0x12,0x13 …)   — the field identifier/slot
cmd        — command code (redundant; equals the outer key)
A          — attribute A  (constant 4 for most fields; larger for the first/lead field)
B          — attribute B  (small enum: 2,3,4,5,6,7,0xb,0x10,0x11,0x12,0x14,0x21,0x2c … )
```

**Interpretation (⚠️ INFERRED, one capture from being bound):** `B` behaves like a **data-type /
element code** and `A` like a **size / field-length**, with the lead field of each command
carrying a larger `A` (a base offset or header length). Binding `A`↔offset vs `A`↔length needs
one raw frame.

Representative decoded lists (raw `{tag: A,B}` triples straight from the binary):

| Cmd | Name | Field descriptors `{tag: A,B}` |
|---|---|---|
| 0x04 | `MC3_SENSOR_INFO` | `{1:0x1d,3} {2:4,0x10} {3:4,5} {4:4,3} {8:4,2}` |
| 0x05 | `MC3_FEATURE_INFO` | `{1:0x2e,3} {2:4,0x31} {3:4,3} {4:4,3} {9:4,5} {8:4,3}` |
| 0x08 | `MC3_LIMIT_INFO` | `{1:0xe,5} {2:4,0x14} {3:4,6} {8:4,4}` |
| 0x09 | `MC3_CYCLE_INFO` | `{1:0x37,5} {2:4,0x37} {3:4,0xb} {8:4,4} {0xb:4,6} {0x12:4,5} {0x11:4,5}` |
| 0x0f | `MC3_ALARM` | `{1:0x24,5} {0xa:4,6}` |
| 0x10 | `MC3_EVENT` | `{1:0xf,5}` |
| 0x0e | `MC3_SYSTEM` | `{1:0xc,3} {5:0,3} {6:7,3} {7:4,7} {0xf:4,5} {0x13:4,2} {8:4,2}` |
| 0x99 | `MC3_DOWNLOAD_IDENTIFIER` | `{1:4,3} {2:4,5} {6:4,5} {3:4,0xd} {8:4,0xb}` |

The complete set (all ~30 commands) is present in `FUN_0042b1f0` and can be dumped mechanically;
the eight above are the ones cross-referenced to already-decoded records. **This gives, for
group 2, the field-level layout that was once the only outstanding wire item.**

## 5.6 Why you don't decode every handler

Almost every dispatch case is the same 4-line routing wrapper (§5.1); it carries **no format
information** — only the *worker* it calls does. And you only need a worker if your reader
consumes that feature. A read-only telemetry viewer needs a handful: config (`0x06`), the live
measurement block (`0x16`), the signal trace (`0x1B`), alarms (`0x12`), and — if desired — events.
The rest are control-writes, or configuration that is already in SQLite.

---

# ═══════════════════════════════════════════════════════════════
# PART 6 — DECODED PAYLOAD BODIES
# ═══════════════════════════════════════════════════════════════

All offsets are relative to the **start of the record payload**. For `MC_` that is offset 0 of the
assembled answer (the payload is a pure record); for `MC3_` it is message offset 2 (after
`[command][length]`). All multi-byte values are LITTLE-ENDIAN. 🔶 GHIDRA except where marked ✅.

## 6.1 SIGNALVERLAUF — the live amplitude trace (THE plotted bars)

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
- Samples are RAW COUNTS in 0..255. **No scaling** (Part 7). The display axis 0..300 is headroom;
  the on-screen "%" is raw relative to the feature's limit Level.
- Endianness verified by loopback (an LE ramp read back 0..248; BE produced garbage).
- The database stores only an enveloped history (Part 10), so the live waveform exists **only on
  the wire** — this decoder is the sole source for real-time traces.
- The request that produces it carries `{station, feature, p3, p4}` and a mode byte; feature
  values `0xFB`/`0xFD` are **reserved selectors**, not indices (§3.3).
- ⚠️ The `mode` field, and the aux context vector at `Paket+0x20` that the request stuffed with
  `{station, featureKey, p3, p4, mode}`, are what tell `bearbeite_Kom_27` **which feature it asked
  for**. That vector never touches the wire. A passive listener must reconstruct it from the
  request bytes; a master gets it for free.
- ⚠️ The exact encoding of `channelKey` is still open (G9, §16.2). Three encodings are plausible —
  a feature mask (`1/2/4/8`), a flagged mask (`0x81/0x82/…`), or a plain index (`0..3`) — and it
  resolves on the first real trace.
- ⚠️ The `expectedSize` currently used for `0x1b` (257) comes from a *synthetic* test, not real
  bytes (D3).

## 6.2 SAMMELMERKMALE — the live measurement block (cmd `0x16`) ✅

`Kanal_addMerkmalData` (`FUN_004a7ec0`). `this` is a **channel** object (`+0x16` channel number,
`+0xa8` target RouterObj, `+0xb0` version). This is the block the app polls continuously, and it
is the primary source of live per-feature values.

```
data[0]  = row count
stride   = featureCount*2 + 2          (+2 more when GeraetTyp == 'H'; this box is 'D')
row r, feature f: lo = data[base + r*stride + f*2]
                  hi = data[base + r*stride + f*2 + 1]
```

**On this box: 4 features → stride 10, total answer size = `rows × 10 + 1`.**

`lo == 0xFF` is an **escape**; `hi` selects the marker, and the *following* row carries the
parameter:

| `hi` | meaning |
|---|---|
| `0x00` | **new cycle** — the next row's byte is the new cycle index |
| `0xFB` | per-feature reset across all features |
| `0xFE` | **workpiece ID** — the next byte is the ID size, cross-checked against `[WorkpieceID] IDsize` |

**Flag bits in `hi`** (gated on `version > 0xD8`; this box is `0xE5`, so all are active):

| bit | meaning |
|---|---|
| `0x01` | teach |
| `0x10` | start/stop |
| `0x40` | tool change (logs `"m_bToolChange set"`) |
| `0x08` | sets bit 7 of the derived status |

`lo & 0x04` = alarm → timestamps the row and fires the tool-wear path.

**Double buffering — do not ignore this.** On a mid-block cycle boundary, the remaining samples go
to shadow maps (`+0xC8`/`+0xD0`) and swap into the live ones (`+0xC4`/`+0xCC`) at the boundary.
Ignoring it attributes post-boundary samples to the **wrong cycle**.

**Cross-check:** the answer assembler's `expected = DATA[1] × Paket+0x34 + 1` is the same formula
— `DATA[1]` = row count, `+0x34` = stride, `+1` = the count byte itself. Two independent
derivations agree.

⚠️ The decompiler shows rows starting at `Data+0x10`, which is the same byte as the count; the
`+1` in the size formula says rows start *after* it. Assume `base = 0x11` and confirm on the first
real block.

⚠️ `Geraet+0x688` — the flag that becomes request byte 2 of `0x16` — is sent as 0 and its meaning
is unknown.

## 6.3 KONFIG — device configuration (cmd `0x06`) ✅

`Geraet_bearbeite_Kom_06_MC_GIVEKONFIG` (`FUN_004cd420`). Verified live in the runtime log:

```
bearbeite_Kom_06_MC_GIVEKONFIG: Version 229 Channels 1 Sensors 4
```

The body is the `SGeraetRec` device record (Part 9.1), which the app copies wholesale into the
Geraet object at `+0x4BA`:

| off | field | cross-check |
|---|---|---|
| `+0x4BA` | GeraetTyp | literal `== 0x48` test (`'H'`) |
| `+0x4BB` | GSubType | passed to `MonitorTypes_resolveName` |
| `+0x4BC` | **channel count** | loop bound in the poll cycle `FUN_004d1310` |
| `+0x4BD` | **sensor count** | `1974.txt`: `44 05 01 04` ✓ |

`MiSensType[]` is copied only for the first `sensorCount` entries — the array is 8 long, only 4
are meaningful here. **A PMD parser should do the same.**

This is the single richest answer for a reader to request first: it establishes version, channel
count, sensor count and device type in one shot, and its expected answer size is well constrained.

## 6.4 ALARM — status / alarm track

`MC3_ALARM`: group-2 cmd `0x0F` (`bearbeite_Kom_15` `FUN_004b5ba0`). The `MC_` box uses the
group-1 alarm path (`0x12 MC_GIVEALARM`); the record semantics (feature + limit + status) are the
same and match the stored `Alarms` table (Part 10).

```
sub-command byte first:  1 = alarm data, 8 = state marker, 0x0A = quit/acknowledge
then: u16 alarmId        (0xFFFF = clear all / "give me everything")
then repeating entries, each: u16 alarmNumber, then a 31-byte record:
    rec+0x00 u16 entryId
    rec+0x02 u16 status      ← low byte = ToolStatus code (§8.1)
    rec+0x1D u8  channelKey  (0xFF = none)
```

qDebug tag: `" Received Alarm: %d Status: %d"`. Stored form → `Alarms` table columns
`ChannelNr, CycleNr, FeatureNr, LimitNr, Ack, TimeOffset`.

✅ **Confirmed for `MC3_`** by the 16-bit length branch (§4.3): the subcommand really is at body
offset 0, `DATA[2]==1` really is "alarm data", and `0xFFFF` really is "give me everything".

⚠️ **For the `MC_` box this layout is `MC3_`-derived and must be treated as PROVISIONAL** — a
reader should hexdump group-1 alarms rather than present them as decoded alarms until an `MC_`
alarm body is seen. `bearbeite_Kom_15` reads `payload[0]` as the **station**, which is the piece
that *is* confirmed for both.

⚠️ **Device-side timestamps.** The app reads a `QDateTime` out of the alarm record
(`FUN_00626960`) and stores `Alarms.TimeOffset` relative to cycle start. A reader that stamps rows
with its own clock at print time will misorder events against the machine's own log under load.

## 6.5 SENSOR_INFO — sensor descriptor (`MC3_`)

`MC3_SENSOR_INFO`: group-2 cmd `0x04` (`bearbeite_Kom_04` `FUN_004bc090`), record read via
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
    uint8_t  type;          // +0x1C SensorType (0x80=PROCUR-S) (§8.2)
    uint8_t  subType;       uint8_t hwSerial;
} SensorInfoRecord;         // ≈ 31 bytes
#pragma pack(pop)
```

DB columns (`DB_insertSensorRow` `FUN_005befb0`): `Date, Rec_Valid, Status, SensorID, Serial,
AktMod_Ref, SensChannels, FeatureCount, FeatureChannel, FormulaCount, FormulaAvailable, SWserial,
Type, SubType, HWserial, Calibration`.

## 6.6 EVENT — event log (`MC3_`)

`MC3_EVENT`: group-2 cmd `0x10` (`bearbeite_Kom_16` `FUN_004b6580`):

```
subcommand byte:  1 = event data
                  8 = state/end marker (next byte==1 → finalize; else FUN_00642ff0)
                  other → error "Wrong subcommand received: %1"
[optional u16 0xFFFF marker, skipped]
repeat while >=2 bytes remain:
    u16   eventNumber
    10-byte record:
        +0x00..+0x08  9 bytes event payload (EventCode per §8.5, params/time)
        +0x09         u8 channelKey (0xFF = none)
    → per-channel map @ this+0xC4 (the SAME map as alarms) via FUN_00484ec0
if nothing selected: ack via FUN_004b5830(station, 1, 0xFFFF, 0)
```

Documented for completeness. This box is `MC_`, so its events arrive via the group-1 path; the
runtime logs show only UI "EventList" navigation, no live event packets during the capture window.

---

# ═══════════════════════════════════════════════════════════════
# PART 7 — SCALING (raw → physical)   ✅ RESOLVED: NO FACTOR
# ═══════════════════════════════════════════════════════════════

**There is no per-sensor amplitude scaling factor for this device generation.** Live samples,
stored maxima and alarm thresholds all live in one unit: **raw 0–255 counts.** Proven from the
databases and the binary together:

- `Features.Feat_Max` (config DB): raw, maximum exactly **255** (602 of 729 rows saturated at 255).
- Measurement DB `Trend_C01_F0x.Max_Val` and `WP_*.Max_S0x` envelopes: global maximum **255**,
  never higher, across all workpieces.
- `Limits.Level` thresholds: **20..170** — the SAME raw units as the amplitude.
- `Sensors.Calibration`: `'0'` on every row (unused).
- The `MC3_SENSOR_VFAKT` worker (`FUN_004acf40`) is a **stub** (`return p != 0`) — there is no
  runtime scaling extraction.
- `SFactors.ini` does **not** exist on this install and the app runs fine without it.

Therefore:

- **Reader rule: plot the raw sample directly (0–255).**
- The on-screen "%" is **raw relative to the feature's limit Level**:
  `% = raw / limitLevel × 100` (e.g. raw 204 against Level 170 → 120%). There is no per-sensor
  constant involved.
- ⚠️ Do not confuse amplitude with `Trend.Work_Val` (range 0..301): that is a cycle position /
  work-window quantity, **not** a scaled amplitude. It is what an early "0–300 axis" reading
  actually referred to.
- `Cycle_Sensors.Gain` (0..126) is the sensor-side **hardware amplifier setting**, a device
  configuration value — the app does **not** apply it at display time.

---

# ═══════════════════════════════════════════════════════════════
# PART 8 — CODE-MEANING TABLES ("decoder rings")   🔶/✅
# ═══════════════════════════════════════════════════════════════

Built at startup by `initStatusTables` (`FUN_004236f0`), which populates the member tables listed
below, plus the config-derived rings read from `PROVISsettings.ini`.

## 8.1 ToolStatus (status byte 0x00–0x0F) — member `this+0x44` 🔶

```
0=empty        1=Overload      2=Underload     3=Contact
4=Missing      5=Work Over     6=Work Under    7=Cut start
8=Cut end      9=Dynam. upper  A=Dynam. lower  B=Pattern upper
C=Pattern lower D=ACF contact  E=cutdetect contact  F=Tool wear
```

## 8.2 SensorType — member `this+0x4c` 🔶

```
01=PA-Box 03=VB-Box 10=PA 111 11=PA 122 S1 13=PA 122 S2 14=PA 211 15=PA 221
16=DU2A211 20=EP 111 24=EP 211 30=VBI 211 31=AE 211 38=VBI RTCM
80=PROCUR-S 81=PROCUR-I 82=PROCUR-B 83=ACFeed 84=ACfeed OVR
90=Position 91=Temperature A0=MI32bit FF=Unknown
```

This box's four sensors are all `0x80` = **PROCUR-S**.

## 8.3 ChannelStatus (0–7) 🔶

`0=Not 1=OK 2=Wrong 3=Later 5=Reset 6=Suppressed 7=Alarm missing`

## 8.4 AccessLevel 🔶

`00=Operator 04=Setter 05=Administrator 06=Machine manufacturer 63=SERVICE`

## 8.5 EventCode (selected) 🔶

`01=RTC Set 02=Cycle settings change 03=Limit change 04=Cycle mode change
06=List cleared 07=Device renamed 09=Sensor change 14=Reboot FF=Empty`

## 8.6 Model resolution — `[MonitorTypes]` ✅ **RESOLVED**

`MonitorTypes_resolveName` (`FUN_004abb20`):

```c
key   = "0x" + hex(GType);          /* falls back to bare hex on miss */
value = ini["MonitorTypes"][key];
list  = value.split(",");
idx   = GSubType - 1;               /* <<<< 1-BASED */
name  = (0 <= idx < list.size()) ? list[idx] : "Unknown";
```

**The index is 1-based**, i.e. `listIndex = GSubType − 1`. The `0x44` family list, shown in the
order it appears in the INI (0-based list positions, as `QStringList::split` produces them):

```
0x44 (this box's -16 family):
  [0]MDL5081-16 [1]MDL5082-16 [2]MDL5051-16 [3]MDL5052-16
  [4]MSL5081-16 [5]MSL5082-16 [6]MSL5051-16 [7]MSL5052-16
  [8]MSL5074-16 [9]MSL3031-16 [10]MSL3032-16 [11]MSL3011-16
  [12]MSL3012-16 [13]MDL5031-16 [14]MDL5032-16 [15]MSL5034-16
Provis2 families: 0x30 / 0x38 / 0x39 / 0x40 / 0x41 / 0x43 / 0x48
Promos3 families: 0x70 CompactBox, 0x71 SensorBox, 0x80 XT-Monitor
```

**GType 0x44, GSubType 5 → list index `5 − 1 = 4` → `MSL5081-16`.** ✅

(Earlier documents listed both `MSL5081-16` and `MSL5082-16` as candidates because the index base
was unknown. `FUN_004abb20` settles it — see Part 20 §20.3.)

## 8.7 Alarm slot → label — `[AlarmNames]` ✅ (operator-configurable)

`GlobaleDaten_loadIniTables` (`FUN_00421e10`) reads `[AlarmNames]` keyed `AlarmName<N>`,
translating known keywords and falling back to `"Alarm <N>"` when blank. Built-in keywords:
`collision`, `Break`, `Wearout`, `Missing`, `Contact`.

**This box's actual table:**

```
1 = Collision   2 = Break   3 = Wearout   4 = Missing   5 = Coolant   6..8 = blank -> "Alarm 6/7/8"
```

⚠️ **Slot 5 is `Coolant`, not the built-in default `Contact`.** It is operator-assigned. Hardcoding
the defaults mislabels it — the same trap as the feature names (§9.2).

## 8.8 Dynamic sensitivity — `[DynnamicSensibility*]` ✅

Behind ToolStatus `0x09` / `0x0A` (Dynam. upper / lower):

```
Top:    L0=12 L1=21 L2=27 L3=36 L4=45
Bottom: L0=9  L1=15 L2=21 L3=27 L4=36
```

## 8.9 Station names — `[StationNames]` ✅

Format `Station-<Serial>.<Channel> = Name`. **Empty on this box** → fall back to `SNr.Ch`.

## 8.10 Field labels — the app's own dictionary ✅

`UnitConfigWidget_setupUi` (`FUN_00715220`) is the application's own label dictionary, and it maps
almost field-for-field onto `SKanalRecV40`. Useful for a reader that wants UI parity:

| internal key | displayed label |
|---|---|
| `Unit_SamplePointLength` | "PROVIS Sampling rate" |
| `Unit_WorkingRange` | "Measuring range" |
| `Unit_SignalFallTime` | "Signal drop time TD" |
| `Unit_OscillationTime` | "Oscillation time TRS" |
| `Unit_AxisActiveOFFDelay` | (axis-active off delay) |
| `Unit_SpindleActiveONDelay` | (spindle-active on delay) |
| `Unit_ChannelInactive` | (channel inactive) |

…plus the filter / offset / compensation set.

---

# ═══════════════════════════════════════════════════════════════
# PART 9 — CONFIGURATION RECORDS (at rest)   ✅ VERIFIED
# ═══════════════════════════════════════════════════════════════

Decoded by cross-referencing raw PMD hex (`1974.txt`, `exVL2-*.txt`) against the SQLite config
databases (`Provis-10659`, `Provis-10663`) column by column. Re-verified against `1974.txt` —
every field marked ✅ has a hex byte equal to the database value.

These are the same records that arrive over the wire: `MC_GIVEKONFIG` (`0x06`) delivers
`SGeraetRec`, `MC_GIVEKANAL` (`0x0e`) delivers `SKanalRecV40` (144 bytes — matching the size
table exactly), and so on. **The at-rest format and the on-wire format are the same bytes.**

## 9.1 `SGeraetRec` — device record (66 bytes) — table `Devices`

Verified from `1974.txt` (`44 05 01 04 …`):

| Offset | Field | Value | Verified |
|---|---|---|---|
| +0x00 | GType | 0x44 (68, MSL-16 family) | ✅ |
| +0x01 | GSubType | 5 | ✅ |
| +0x02 | Channel_Amount | 1 | ✅ |
| +0x03 | MiSens_Amount | 4 | ✅ |
| +0x1A..0x21 | MiSensType[8] | 0x80 (PROCUR-S) each | ✅ |
| +0x22 | SampleDiv | 1 | ✅ |
| +0x26..0x27 | ReduzLim | 0x19D4 = 6612 (LE: `D4 19`) | ✅ |

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

**In-memory home:** copied wholesale into the Geraet object at `+0x4BA` (see §6.3), so
`Geraet+0x4BA..+0x4BD` = GeraetTyp / GSubType / **channel count** / **sensor count**.

⚠️ **`+0x4BC` is the CHANNEL count, not a station count.** (Corrected — see Part 20 §20.6.)
Behaviourally identical on this box, which has one of each, but the label was wrong.

⚠️ `MiSensType[]` is copied only for the first `sensorCount` entries. The array is 8 long; only 4
are meaningful here. A PMD parser should do the same.

## 9.2 `SKanalRecV40` — channel record (144 bytes) — table `Channels`

Verified from `1974.txt`. The 144-byte size matches the size table's `0x0e` entry exactly.

| Offset | Field | Value | Verified |
|---|---|---|---|
| +0x00 | PLC_Type | 0x10 (16) | ✅ |
| +0x01 | PLC_Version | 0x20 (32) | ✅ |
| +0x02 | Channel_Num | 1 | ✅ |
| +0x10..0x13 | CDRLim[4] | 0xAA (170) each | ✅ |
| +0x4D | features[4] | 4 × 12-byte slots | ✅ |

### ⚠️ Feature names and masks are PER-INSTALL — read them, never hardcode

The feature-name block at `+0x4D` is 4 fixed 12-byte slots, each `[1 mask byte][11-byte
NUL-terminated ASCII]`.

> An early version of this analysis showed `SPINDEL / X AXIS / Y AXIS / Z AXIS` with masks
> `0x81 / 0x82 / 0x84 / 0x88`. **That was a different machine's example.** See Part 20 §20.7.

**THIS box (`1974.txt`) has:**

```
+0x4D: 01 56 49 42 52 41 54 49 4F 4E 00 00  → mask 0x01 "VIBRATION"
       02 4D 31 33 31 20 44 45 42 49 00 00  → mask 0x02 "M131 DEBI"      (debi = flow rate)
       04 4D 31 33 31 42 41 53 49 4E 43 00  → mask 0x04 "M131BASINC"     (basınç = pressure)
       08 4D 30 38 20 44 45 42 49 00 00 ..  → mask 0x08 "M08 DEBI"
```

```c
typedef struct { uint8_t mask; char name[11]; } SKanalFeature; // 12 bytes
```

**Reader rules:**

- **Read feature names dynamically from `SKanalRec`** — they are operator-assigned per machine,
  and on this box they are Turkish/German shop-floor labels. A wrong label will look plausible.
- The **low nibble** (`0x01 / 0x02 / 0x04 / 0x08`) is the feature-select bit; the **high `0x80`
  bit is a separate flag** (set in the other machine's example, clear here). Match on
  `mask & 0x0F` (or the bit position) and treat `0x80` as a flag — do **not** key on
  `mask == 0x81`.

## 9.3 `SGrenzRec` / `SHardwareRec` / `SZykRecV4802`

- **`SGrenzRec`** (limits, ~14 bytes) — `1974.txt`:
  `d9 01 04 04 04 00 04 fa fc 07 08 32 08 fa`. Maps to table `Limits` (`Limtype`, `Level`,
  `Feat_Num`, …). Levels seen on this box: 20 / 35 / 50 / 70 / 115 / 140 / 152 / 170. Size 14
  matches the size-table entries for commands `0x02` and `0x28`. ✅
- **`SHardwareRec`** (~46 bytes) — `1974.txt`: `02 01 02 03 04 …`. Table `Hardware`
  (`Board_Vers`, `Del_Date1..4`). Size 46 matches the size-table entry for `0x10`
  (⚠️ though `GIVEHARDWAREREC` is command `0x1a` — see §3.5.2).
- **`SZykRecV4802`** (cycle, 170 bytes) — 9 records present in `1974.txt`; size 170 confirmed.
  Maps to table `Cycles` (`Name`, `Duration`, `MonIndex`, `Sensor_Ref1..4`, `Feature_Ref1..4`,
  `Limit_Ref1..8`, `PLCRep_Ref1..8`, …) and `Cycle_Sensors` (`Sens_Param1..3`, `Gain`, `Meantime`,
  `Komp_Start`). Size 170 matches the size-table entry for `0x03`.

## 9.4 ⚠️ Record-layout versioning

Every handler calls `Geraet_getRecordVersion` (`FUN_004c5c70`) **before** parsing and passes the
version into the record parsers. Record type names are version-stamped — `SKanalRec**V40**`,
`SZykRec**V4802**` — and this box reports **Version 229 (0xE5)**.

**So the layouts are version-selected.** Everything in this Part is correct *for firmware
`Rtm_V14.5.H86` / record version 229*. A reader that hardcodes one variant is correct only for
that firmware. `FUN_004c5c70` and the version→layout switch remain unread (G6, §16.2) — judged low
value while only one firmware is in scope.

## 9.5 Config DB table catalog (`Provis-10663`) ✅

```
Devices, Channels, Cycles, Cycle_Sensors, Sensors, Sensor_Map, SensorLink, Features,
Limits, Constraints, Hardware, NCProgram, Program, CycleDsp, PLCReport, Version, Source
```

plus job-numbered tables (`1970` / `1971` / `6136` / …). App version 3.1.44.4, schema 10.

Selected schemas:

- `Devices(GType, GSubType, Channel_Amount, MiSens_Amount, CDR, Setup, PLC_Konf, …,
  SensorType_1..4, MiSensType_1..8, SampleDiv, …, ReduzLim, …, WithACfeed)`
- `Channels(PLC_Type, PLC_Version, …, CDRLim1..4, Sens_Link1..4, MDL_Period, MDL_Time, …)`
- `Sensors(Sensor_Num, SensDat_1..14, Calibration)` — `Calibration` is `'0'` (unused)
- `Features(Feat_Num, Feat_Max, Work_Teach, Work_Start, Work_End)` — `Feat_Max` raw 0..255
- `Limits(Limtype, Level, Feat_Num, Response_Time, Act_Start, Act_End, Act_Mode, Pattern_Ref)`
- `Cycle_Sensors(Sens_Param1..3, Gain, Meantime, Komp_Start)`

## 9.6 PMD file loading (no wire traffic)

Two functions load a PMD configuration into memory. Both were once expected to reveal the
multi-frame request split; **they do not send anything over CAN** and contain no protocol content
(Part 20 §20.8):

| Address | Name | Role |
|---|---|---|
| FUN_005206c0 | `Lade_Alles_aus_PMD_File` | SQL → memory, whole device |
| FUN_005179c0 | `Lade_Kanal_aus_PMD_File` | SQL → memory, one channel |
| FUN_00426100 | `GetCurrentPMD` | resolves the per-unit PMD name |
| FUN_004341f0 | `changePMDfromNC` | Mazak↔PMD bridge (**write** path) |

---

# ═══════════════════════════════════════════════════════════════
# PART 10 — MEASUREMENT DATABASE (history)   ✅ VERIFIED
# ═══════════════════════════════════════════════════════════════

`ProvisLog-10663` (SQLite, ~8 MB) is the app's working measurement database. 61 tables:

- **`Log`** (9,637 rows) — cycle/run log: `WorkPiece, ProgNum, Channel, Tool, ProgRef, Type,
  SRate, Data_Ref, Status1..4`.
- **`Alarms`** (65 rows) — `Date, ProgRef, ChannelNr, CycleNr, FeatureNr, LimitNr, Ack, Ack_Date,
  Signal, TimeOffset`. Feature and limit are referenced — consistent with §6.4 and the `Limits`
  config table.
- **`Trend_C01_F01..F04`** — per-feature peak trend: `WorkPiece, Source, Max_Val, Work_Val`.
  `Max_Val` = raw peak (0..255); `Work_Val` = 0..301 (position/window, **NOT** amplitude).
- **`WP_00001_01 … WP_000NN_01`** (52 tables) — per-workpiece measurement curve stored as a
  **per-sensor min/max envelope**: `Min_S01, Max_S01, …, Min_S04, Max_S04` (one row per sample
  index). This is enveloped / downsampled history, **not** the raw 125-int16 waveform.
- **`Status_C01`** — per-workpiece status: `WorkPiece, Source, Status1..4`.
- **`Statistics`**, **`Version`**.

**Implication:** for history migration, read `Trend_*`, `WP_*`, `Alarms` and `Log`. For the
**live** waveform there is no DB source — it exists only on the wire via SIGNALVERLAUF (§6.1).
This confirms, and does not contradict, the protocol model.

## 10.1 `Alarms` — exact INSERT column order ✅

From `SqlDb_fuegeAlarmsHinzu` (`FUN_005e9930`, tag-proven `"FuegeAlarmsHinzu"`):

```
Date, ProgRef, ChannelNr, CycleNr, FeatureNr, LimitNr, Ack, Ack_Date, Signal, TimeOffset
```

On failure the app logs `"writing in table %1 from database %2 failed. Error %3 %4"`.

The source record (`param_1`) field offsets, ⚠️ INFERRED (to confirm against a live row):

```
+0x04  Date (text)      +0x0c  ProgRef        +0x18  ChannelNr
+0x1c / +0x20  Cycle (composite)              +0x24  FeatureNr
+0x28  LimitNr          +0x2c  Ack            +0x30  TimeOffset
+0x34  Signal (text)
```

---

# ═══════════════════════════════════════════════════════════════
# PART 11 — APPLICATION DATA MODEL & DATABASE READ PATH
# ═══════════════════════════════════════════════════════════════

*(Formerly Appendix A.)*

**Scope.** Where the rest of this report follows bytes from the device to the decoder, this Part
documents the complementary *application-internal* layer: the in-memory domain object that live
and historical measurements are loaded into, and the SQLite/ODBC read path that reconstructs a
workpiece's full history from disk. It was produced by Ghidra static analysis working outward from
Qt container teardown code into the DB layer, using the application's own German method-name
strings (mutex-locker labels, log messages) as ground truth for naming.

**Relationship to the rest of the report.** Where the receive path ends at "decode body → emit
signals → GUI / SQLite", this Part picks up the SQLite side: the schema in Part 10 is the
*storage*; the functions below are the *reader* that turns those tables back into a populated
record for the statistics / event-log / print UI.

## 11.1 Summary

- The central domain object is **`Promos3DataRecord`** (0xF8 = 248 bytes) 🔶 — one instance per
  workpiece cycle. It aggregates the cycle header, a timestamp→sample index, the raw
  multi-channel signal traces, and alarm/feature sub-records. Its field layout was recovered from
  its copy-constructor and destructor.
- The **read path is fully mapped end to end** 🔶/✅:
  `buildWorkpieceRecords` → per workpiece `GetWorkPieceData` → `{ GetWorkPieceCycle,
  GetSignalData, alarms }` → one populated `Promos3DataRecord` → UI.
- Every SQL entry point carries a German mutex-locker string that names it directly:
  `OpenDatabase`, `CloseDatabase`, `UeberpruefeTabelle` (check table), `Zeilenanzahl` (row count),
  `GetAlarmsList`, `FindeAlleIDsFromSource`, `GetWorkPiecesFomProgRef`, `GetWorkPieceCycle`,
  `GetSignalData`, `GetWorkPieceData`. ✅
- The **SQL database manager** (`Promos3SqlDatenbankManager`) is a singleton supporting both
  **QSQLITE** and **QODBC** (SQL Server) back-ends, with its own logging worker thread
  (`Promos3ProtokollThread`) for delayed/batched writes. 🔶
- This layer is consistent with the measurement DB schema in Part 10: `Log`, `Alarms`, `Trend_*`
  and `WP_*` are exactly the tables these readers target.

## 11.2 The central domain object — `Promos3DataRecord`

One `Promos3DataRecord` represents a single monitored cycle / workpiece run. It is heap allocated
(`operator_new(0xF8)`), deep-copied through a copy-constructor (`FUN_00560340`), and destroyed
through `FUN_0055fbc0`. A global instance counter (`g_dataRecordCount`, `_DAT_00a1cd04`) tracks
live instances. Records nest: several fields hold `QList<Promos3DataRecord*>` of sub-records,
deep-copied recursively.

### 11.2.1 Verified field map (0xF8 bytes) 🔶

| Offset | Type | Meaning |
|---|---|---|
| +0x04..+0x24 | int ×9 | scalar header fields (flags/counts) |
| +0x18 | int | **ProgRef** (program reference) |
| +0x1C | int | **CycleNr** |
| +0x28 | QString | cycle label / workpiece name (see `formatCycleId`, §11.4) |
| +0x2C | QString | second label string |
| +0x38 | int | **start row ID** (into signal table) |
| +0x3C | int | stop / count flag |
| +0x40 | int | type-2 ID (from cycle row type 2) |
| +0x44 | int | type-3 ID (from cycle row type 3) |
| +0x4D.. (stride 0xC ×4) | struct[4] | **channel descriptor table**; low nibble @+0 = active-feature mask |
| +0x54 | int | extra scalar |
| +0x74 | QByteArray | raw payload blob |
| +0x7C | QDateTime | cycle timestamp |
| +0x80..+0x98 | QVector<short> ×N | fixed-size sample vectors |
| +0xA0 | QMap<int, QVector<short>*> | **signal channels** — the raw sample traces |
| +0xA4, +0xBC, +0xC0 | QList<int64*> | boxed 64-bit accumulators (per-group sums) |
| +0xA8 | QMap<int, {sub-record}> | typed sub-entries |
| +0xAC | ptr | parent/context reference (copied by value, not owned) |
| +0xB4, +0x90, +0x94 | QMap<int,int> | cycle/index maps |
| +0xB8 | QMap<QDateTime,int> | **timestamp → sample index** |
| +0xCC, +0xD8, +0xF0 | QStringList | label/category lists |
| +0xE4, +0xE8, +0xEC, +0xF4, +0xC4, +0x9C | QList<Record*> / QList<QVector*> | **nested sub-records** |

> **Note on the signal channels.** The `+0xA0` map's value vectors are element-size 2
> (`QVector<short>`), matching the raw 0–255 amplitude counts documented in Part 7 (no scaling
> factor). Each channel index maps to one trace vector; the `+0xB8` timestamp map indexes samples
> by time. Note that the channel-descriptor stride and offset (`+0x4D`, stride 0xC, ×4) are the
> same shape as `SKanalRecV40`'s feature slots (§9.2) — the in-memory record mirrors the on-wire
> record.

### 11.2.2 Interpretation

The record is the in-memory mirror of the storage schema: header fields (`ProgRef`, `CycleNr`,
timestamp) correspond to `Log` / `WP_*` key columns; the `+0xA0` channel map holds what `WP_*`
stores as a min/max envelope; the alarm sub-records correspond to `Alarms` rows. The nested
`QList<Record*>` fields let one workpiece own its per-feature children.

## 11.3 The database read path 🔶/✅

### 11.3.1 Call chain

```
ProtokollThread_buildWorkpieceRecords            (slot 3 of Promos3ProtokollThread)
   │  GetWorkPiecesFomProgRef  ──► QList<int> workpiece IDs (filtered, sorted)   ✅
   ▼
   for each workpiece ID:
      GetWorkPieceData(this, wpID, progRef, mode, &record)                       ✅
         ├─ GetConnectionForKey        (resolve QODBC/QSQLITE connection)        🔶
         ├─ GetWorkPieceCycle          (cycle header + timestamp index)          ✅
         │     type 1 → main row: ProgRef, CycleNr, startID, timestamp, +0xB8 map
         │     type 2 → +0x40   type 3 → +0x44   type 5 → adjust startID
         ├─ GetSignalData              (raw per-channel sample traces → +0xA0)   ✅
         │     pre-grows N channel vectors, writes (value,extra) shorts per row
         ├─ (alarms / feature sub-records)                                       🔶
         └─ formatCycleId              (build "PP.CCCCC" display label)          🔶
      append record to output QList<Record*>
```

### 11.3.2 Named SQL entry points (all ✅ via mutex strings)

| Function | Rename | Query / behaviour |
|---|---|---|
| FUN_00525700 | `SqlDb_openDatabase` | `"OpenDatabase"` — QSQLITE or QODBC (`DRIVER={SQL SERVER};…`); sets host/name/user/pw/port |
| FUN_005253d0 | `SqlDb_closeDatabase` | `"CloseDatabase"` — close, delete query+db, removeDatabase |
| FUN_005241e0 | `SqlDb_setDatabaseClosing` | `"SetDatabaseClosing:\t%1, SN:%2"` — closing-flag setter under mutex |
| FUN_00526d10 | `SqlDb_checkTableExists` | `"UeberpruefeTabelle"` — `SELECT name FROM sqlite_master …` |
| FUN_005270c0 | `SqlDb_getMaxRowId` | `"Zeilenanzahl"` — `SELECT MAX(ID)` as a cheap row count |
| FUN_005ea6c0 | `SqlDb_getAlarmsList` | `"GetAlarmsList"` — parse rows → 11-field alarm records, dedup-append |
| FUN_005f8820 | `SqlDb_findeAlleIDsFromSource` | `"FindeAlleIDsFromSource"` — `SELECT ID,Date … WHERE Source_Ref=… ORDER BY Date DESC` |
| FUN_0059b240 | `SqlDb_getWorkPiecesFromProgRef` | `"GetWorkPiecesFomProgRef"` — workpiece IDs by program ref, bit-filtered, sorted |
| FUN_00590e50 | `SqlDb_getWorkPieceCycle` | `"GetWorkPieceCycle"` — cycle header rows (type 1/2/3/5) into record |
| FUN_005efdc0 | `SqlDb_getSignalData` | `"GetSignalData"` — raw multi-channel sample traces into +0xA0 |
| FUN_005dfa50 | `SqlDb_getWorkPieceData` | `"GetWorkPieceData"` — orchestrates the three loaders above |
| FUN_00601040 | `SqlDb_getNCToolID` | `"getNCToolID"` — `SELECT … FROM NCTool WHERE Name='%1'` → int ID / −1 / 0 |
| FUN_006061d0 | `SqlDb_findeSourcesFromWerkzeug` | `"FindeSourcesFromWerkzeug"` — `SELECT DISTINCT ID FROM Source WHERE Channel_Num=%1` + tool/NCTool clause |
| FUN_005e1c90 | `SqlDbMgr_findeAlleIDsFromWerkzeug` | resolves connection by key (`this+0x6c`), calls the two above, merges via `SqlDb_findeAlleIDsFromSource` |
| FUN_005e9930 | `SqlDb_fuegeAlarmsHinzu` | `"FuegeAlarmsHinzu"` — lazy-creates + INSERTs one alarm row (column order §10.1) |
| FUN_005dfed0 | `SqlDb_updateFromOldVersion` | schema migration |
| FUN_00463fb0 | `SqlDbManager_upgradeWPtoTrend` | `WP_*` → `Trend_*` migration |

### 11.3.3 `GetWorkPiecesFromProgRef` detail ✅

`SELECT * FROM <workpieces> WHERE <progRef> ORDER BY ID DESC`. Two modes: normal mode reads the ID
plus two status bytes per row and filters on bit masks (`& 0x500`, `& 4`, `& 0x200` — a
"valid/complete workpiece" test), building a deduplicated ID list and erasing incomplete trailing
entries; alt mode collects all IDs. The list is sorted ascending (`std::sort<int*>`, introsort)
before return. The table-name literal is labelled `g_workpiecesTableName` (`param_1_00a1d320`).

### 11.3.4 `GetWorkPieceCycle` detail ✅

`SELECT * FROM <cycle> WHERE WorkPiece=<id>`. Each row carries a **type** field:

- type 1 — main cycle row: fills `+0x04 / +0x0C / +0x18 (ProgRef) / +0x1C (CycleNr) /
  +0x38 (startID) / +0x54 / +0x7C (QDateTime)` and inserts a dated entry into the `+0xB8`
  `QMap<QDateTime,int>`.
- type 2 → `+0x40`; type 3 → `+0x44`; type 5 → adjusts the `+0x38` start offset.
- `+0x3C` is used as a stop flag.

### 11.3.5 `GetSignalData` detail ✅

`SELECT * FROM <signalTable> WHERE ID >= <start> AND ID <= <max>`. Pre-grows N channel
`QVector<short>` in the `+0xA0` map (channel count from a helper), then per result row writes
paired `(value, extra)` shorts into each channel's vector at a rolling byte offset. This is the
raw sensor/signal trace — the per-sample amplitude curve(s) for a workpiece cycle, consistent with
the wire-side SIGNALVERLAUF format and the no-scaling result.

## 11.4 Supporting application helpers 🔶

| Function | Rename | Meaning |
|---|---|---|
| FUN_00560340 | `Promos3DataRecord_copyCtor` | deep copy of the 0xF8 record (recurses into sub-records) |
| FUN_0055fbc0 | `Promos3DataRecord_dtor` | destructor freeing all ~40 members |
| FUN_005ebf20 | `formatCycleId` | builds the `"PP.CCCCC"` label (2-digit prog, 5-digit cycle, separator) |
| FUN_004a0dd0 | `Record_collectActiveChannels` | walks 4 channel descriptors (stride 0xC @+0x4D), low-nibble flag → channel-index list |
| FUN_0055b630 | `TwoStringRecord_assign` | copy 4 ints + 2 QStrings (a lookup-record value type) |
| FUN_0055d840 | `DataRecord_setChannelList` | assign the `QList` at +0xF4 |
| FUN_00455d00 | `SqlDbManager_getConnectionForKey` | `"GetP2DatPmd"` — `QMap<QString,DbConn*>` lookup |
| FUN_004546c0 | `SqlDbManager_reapClosedConnections` | closes flagged connections; logs "N delayed databases have been closed" |
| FUN_0044cdc0 | `Promos3SqlDatenbankManager_ctor` | 0x4C-byte singleton ctor; QTimer `OnSimpTimer()` @ 5 min; reads INI |
| FUN_0044d070 | `Promos3SqlDatenbankManager_instance` | lazy singleton (`g_sqlDbManager`, `DAT_00a1ab04`) |
| FUN_00557d10 | `Promos3ProtokollThread_ctor` | QThread subclass; wait-condition + mutex; DB-logging worker |

### 11.4.1 `Promos3ProtokollThread` public interface (moc dispatch)

Recovered from `qt_static_metacall` (`FUN_00798020`) — the thread's method indices:

| idx | function | role |
|---|---|---|
| 0 | FUN_005e1c90 | read records by source + date |
| 1 | FUN_005e1f50 | `AddAlarms` — batch-persist alarms with cycle/feature context ✅ |
| 3 | FUN_005e2af0 | `buildWorkpieceRecords` — the read entry point |
| 2, 4, 5, 6 | FUN_005df950 / FUN_005e2af0 / FUN_005df970 / FUN_005e2ed0 / FUN_005e1930 | sibling batch add/read handlers |

## 11.5 Newly labelled globals

| Symbol | Rename |
|---|---|
| DAT_00a1ab04 | `g_sqlDbManager` (Promos3SqlDatenbankManager singleton) |
| DAT_00a1cd04 | `g_dataRecordCount` (live Promos3DataRecord counter) |
| DAT_00a1cb8c | `g_protokollThreadCount` |
| param_1_00a1d320 | `g_workpiecesTableName` |
| (alarms table literal) | `g_alarmsTableName` |

## 11.6 Consistency with the protocol side

Everything in this Part corroborates and extends the wire findings without contradiction:

- The tables these readers hit (`Log`, `Alarms`, `Trend_*`, `WP_*`) are exactly the verified
  measurement schema (Part 10).
- The `+0xA0` `QVector<short>` channel traces confirm the amplitude representation is raw 0–255
  counts — the "no scaling factor" result — from the storage side as well as the wire.
- The `GetSignalData` layout mirrors the on-wire SIGNALVERLAUF body: same per-channel sample
  series, same units.
- `Promos3ProtokollThread` (DB persistence) and `Promos3KommandoVerteilerThread` (command
  dispatch, §1.7) are distinct workers with distinct jobs.

## 11.7 Implications for reader tooling

- **Live path** — decode SIGNALVERLAUF (§6.1) and the SAMMELMERKMALE block (§6.2) off the wire.
- **History path** — there is **no need to reverse a binary DB format**: the working database is
  plain SQLite with the schema in Part 10. A migration/read tool can query `Log`, `WP_*`,
  `Trend_*` and `Alarms` directly and reconstruct the equivalent of a `Promos3DataRecord` per
  workpiece, using §11.3.4–11.3.5 as the field-population recipe.
- The `formatCycleId` rule (`"PP.CCCCC"`) reproduces the app's cycle labels exactly for UI parity.

## 11.8 What remains in this layer (non-blocking)

- A few Qt container variants and small getters remain unnamed; they are mechanical
  (QMap/QVector/QListData detach/insert/free by signature) and carry no domain meaning.
- The exact semantics of the `+0xA8` typed sub-record map and a couple of the `+0xE4`-family
  nested lists are structurally understood but not individually field-labelled; not required for
  read-only history reconstruction.

---

# ═══════════════════════════════════════════════════════════════
# PART 12 — SQL DIALECT LAYER, CONFIGURATION AND SETTINGS
# ═══════════════════════════════════════════════════════════════

## 12.1 Dual-driver SQL abstraction (SQLite ⇄ ODBC / SQL Server) 🔶

`SqlDialect_buildTokenMap` (`FUN_00556f50`) proves the app carries a **driver-abstraction layer**
keyed by Qt driver name (`QSQLITE` vs `QODBC`). Token pairs recovered:

| Token | QSQLITE | QODBC |
|---|---|---|
| create-table | `create table ` | `CREATE TABLE ` |
| insert | `INSERT INTO` | `INSERT INTO` |
| primary-key | `primary key` | `PRIMARY KEY` |
| not-null | *(schema-specific)* | ` NOT NULL` |
| identity | *(NULL autoincrement)* | `IDENTITY(1,1) ` |

`SqlBuild_insertColumnPrefix` (`FUN_00556680`) / `SqlBuild_valuesPrefix` (`FUN_005565e0`) consume
this: for non-ODBC they emit `( ID , … ) VALUES ( NULL, …)` (explicit NULL autoincrement); for
ODBC they omit the `ID` column entirely and let the server's `IDENTITY` fill it.

Supporting objects: `SqlDialect_ensureMap` (`FUN_00557670`) lazily initialises the dialect
singleton `DAT_00a1cb88`; `SqlDialect_ctor` (`FUN_00557610`) null-inits then builds the map.

**Implication for the reader:** the reference install is SQLite, but the same binary targets
SQL Server via ODBC. Any schema assumption should hold for both back-ends.

## 12.2 The connection struct (`Verbindung`)

`SqlDb_getVerbindung` (`FUN_00525530`, tag-proven `"GetVerbindung"`) copies the **10-QString
connection struct** at `this+0x40`, plus an int at `+0x28`:

| Address | Name | Role |
|---|---|---|
| FUN_00524480 | `Verbindung_copyCtor` | copy-constructs 10 QStrings (`0x00…0x24`) + int `+0x28` |
| FUN_00446bc0 | `Verbindung_ctorNull` | null-inits the 10-QString struct |
| FUN_00446c90 | `Verbindung_dtor` | releases members `[9]…[0]` |

## 12.3 ⚠️ A minor bug worth knowing about (log text only)

In `SqlDb_findeSourcesFromWerkzeug` (`FUN_006061d0`) the failure-log format string
`"Finding IDs from Tool %1 and Channel %2 …"` binds `%1`←`param_2` and `%2`←`param_1` — i.e. the
**channel and tool arguments are swapped relative to the WHERE clause** (`Channel_Num=%1` uses
`param_1`). Cosmetic, affecting only the log text, but note it when matching log lines to queries.

## 12.4 `[Ethernet]` INI → struct offset map ✅

From `EthThread_initFromIni` (`FUN_004fbae0`, tag-proven `"Promos3EthAbstract::initFromIni"`).

⚠️ **Two different things are tabulated here and they must not be confused:** the **code default**
(what `initFromIni` substitutes when the key is absent) and the **reference INI value** (what this
deployment actually sets). They agree on most keys and differ on four — see the ⚠️ rows and
§0.6 C24.

| INI key (`[Ethernet]`) | Code default | Reference INI | Struct off. | Note |
|---|---|---|---|---|
| Active | — | **0** | (gate) | `<1` → aborts init; also aborts if offline. Ethernet is **disabled** on this box |
| FirstDevice | 1 | 1 | +0x08 (u16) | |
| LastDevice | 1 | 1 | +0x0a (u16) | |
| BroadcastPort | 4711 (0x1267) | 4711 | +0x1c (u16) | `EthThread2` reads it as `m_broadcastPort` (key typo in the sibling) |
| FirstPort | 1789 (0x6fd) | 1789 | +0x20 (u16) | ✅ matches the gateway port |
| LastPort | 1789 (0x6fd) | ⚠️ **1799** | +0x22 (u16) | the deployment widens the range |
| StreamingPort | 2789 (0xae5) | 2789 | +0x50 (i32) | |
| LastUsedPort | 1789 (0x6fd) | **1793** | +0x1e (u16) | a live value, written by `Interface_onUnitConnected` |
| SelectedInterface | "" | "" | (QString) | |
| unitAnswerTimeout | 500 | ⚠️ **300** | +0x10 (i32) | **floored to 500 in code**, so the INI's 300 has no effect here. `[Ethernet]`-side — distinct from `[CAN] unitAnswerTimeout` |
| ScanTimeout | 1000 | 1000 | +0x0c (i32) | floored to 1000 |
| ResendON `[Internal]` | 1 | ⚠️ **0** | +0x54 (i32) | streaming-variant only; **off** on this box |
| MaxResend | 5 | (unset) | +0x24 (i32) | `[Ethernet]`-side; the CAN link uses `[Comm] MaxResend = 1` |
| LogETHMessage `[ErrorManager]` | 0 | ⚠️ **1** | +0x48 (i32) | ETH-side capture toggle (mirror of `LogCANMessage`). **Already enabled** on this box — but Ethernet is inactive, so it produces nothing |

There are **two `initFromIni` siblings** carrying the same tag string:

| Address | Name | Distinguishing feature |
|---|---|---|
| FUN_004fbae0 | `EthThread_initFromIni` | streaming variant — has `StreamingPort` / `ResendON` |
| FUN_00500390 | `EthThread2_initFromIni` | leaner sibling — no `StreamingPort` / `ResendON`; reads `m_broadcastPort` |

⚠️ Which is which by caller is still pending an xref check. Non-blocking.

## 12.5 The settings dialog and `[CAN]` keys ✅

`EthSettingsDlg_loadFromIni` (`FUN_006dcab0`) additionally binds `[CAN]` keys to the dialog:
`PCANGateway`, `BaudrateRegister` (default 22), `BaseCanIDTransfer` (default 1280) — all ✅
matching `[CAN]` in the reference INI. `EthSettingsDlg_saveToIni` (`FUN_006dba10`) writes the
dialog's IP/port fields back to `[Ethernet]`; `EthSettingsDlg_setupUi` (`FUN_006d99a0`) builds the
combos, masks and ranges and wires the `On…Changed` slots.

The CAN settings dialog builder (`FUN_006da550`) exposes exactly **one** "Base Tx" field —
*"CAN transfer base address in hex"* — with First/Last unit described as **offsets added to Base
Tx**. This is the independent confirmation that there is one CAN-ID base (§2.5).

## 12.6 Other configuration facts used by the reader

Transcribed directly from the reference `PROVISsettings.ini`, section by section:

```
[Internal]       ResendON = 0
[ErrorManager]   LogCANMessage = 0      ← set to 1 to capture raw CAN frames to the log
                 LogETHMessage = 1      ← already on (but [Ethernet] is inactive)
[User Interface] PlotRefreshTime = 100   PlotInterval = 2000    (display-side hints)
[StationNames]   Station-<Serial>.<Channel> = Name   — EMPTY on this box   (§8.9)
[AlarmNames]     AlarmName1..8                                            (§8.7)
[Comm]           unitActiveTimeout = 900   ← DERIVED, mirrors unitAnswerTimeout × 3
                 MaxResend = 1
[CAN]            Active = 1
                 PCANGateway = 1
                 GatewayPort = 1789
                 GatewayAddress = 192.168.222.17
                 BaudrateRegister = 22
                 BaseCanIDTransfer = 1280
                 BusID = 512
                 unitAnswerTimeout = 300
[Ethernet]       Active = 0             ← Ethernet path disabled on this box
                 FirstPort = 1789   LastPort = 1799   StreamingPort = 2789
                 LastUsedPort = 1793
                 unitAnswerTimeout = 300   (floored to 500 in code — no effect)
[DynnamicSensibilityTop] / [DynnamicSensibilityBottom]                     (§8.8)
[MonitorTypes]   0x30 0x38 0x39 0x40 0x41 0x43 0x44 0x48 0x70 0x71 0x80    (§8.6)
[DatabasePMD] / [DatabaseLog]   Log_Active = 1
[WorkpieceID]    IDsize                (cross-checked by the 0x16 escape handler, §6.2)
```

⚠️ **`unitActiveTimeout` lives in `[Comm]`, not `[CAN]`**, and it is derived rather than
independent: `DAT_00a17914 = unitAnswerTimeout × 3 = 900 ms` is the unit-rescan gate, and the INI
value simply mirrors it (§3.9).

⚠️ **`unitAnswerTimeout` appears twice** — once under `[CAN]` (300 ms, the value that governs this
box's CAN link) and once under `[Ethernet]` (300 ms, but floored to 500 in code). Do not conflate
them. The same applies to `MaxResend`: `[Comm] MaxResend = 1` governs the CAN link; the
`[Ethernet]` side has its own code default of 5.

Reading INI values goes through `ini_readInt` (`FUN_00437f50`), which `tryLock`s for 3000 ms and
raises an `ErrorManager` entry on timeout.

---

# ═══════════════════════════════════════════════════════════════
# PART 13 — COMPLETE FUNCTION REFERENCE
# ═══════════════════════════════════════════════════════════════

All names in this Part are **analysis labels**. Where a name is **[tag-proven]** the function
constructs a QString tag — a `Promos3MutexLocker` name, an `ErrorManager` log tag, or a
class-qualified label such as `"Promos3CanInterface::receive"` — that states its own identity;
those are as good as symbols. Where a name is **[structural]** it was derived from behaviour
alone. Percentages are the analyst's per-function confidence estimate.

This is the merged reference; every function named in any of the seven source documents appears
here exactly once.

## 13.1 Transport — gateway and CAN interface

| Address | Name | Conf. | Purpose |
|---|---|---|---|
| FUN_00504ab0 | `Promos3CanInterface_init` | 🔶 | UDP-gateway mode binds a QUdpSocket; otherwise loads `CanApi2.dll` (PEAK) |
| FUN_00505b00 / FUN_00505c60 | `Promos3CanInterface_ctor` / `_dtor` | 96% ✅ | ctor holds the base CAN-ID, unit range and the `"ProcessControl"` / `"sandvik"` literals (§2.5) |
| FUN_00507760 | `Scan4CANmsg` | 🔶 | Split a UDP datagram into 36-byte CAN records; extract CAN-ID (BE @+0x1A), LEN (@+0x15), 8 data bytes (@+0x1C); route by unit |
| FUN_005083e0 | `CanInterface_pollMessages` | 🔶 | Branches gateway (→`Scan4CANmsg`) vs PEAK (`CAN_Read`); identical downstream |
| FUN_00508a80 | `CanInterface_receive` | 95% ✅ | [tag-proven] `"Promos3CanInterface::receive"`. Reassemble → dispatch / abort / restart-streaming |
| **FUN_00506220** | **`Promos3CanInterface::send`** | ✅ | ⭐ **the transmit tail** — appends the checksum, splits into `[00 00 00 + 5B]` then `[seq + 7B]` frames, picks CAN-ID = base + unit |
| **FUN_00504290** | **`CanInterface_writeGatewayRecord`** | ✅ | ⭐ builds the 36-byte TX record (`00 24 00 80` + zeros) and sends the datagram |
| FUN_00506d10 | `CanInterface_searchForNewUnits` | 96% ✅ | unit discovery sweep 1–15, one probe per pass (§3.9) |
| FUN_005073f0 | `Promos3CanThread::sendCommandToUnit` | ✅ | send-queue enqueue **with de-duplication** — ⚠️ *not* the frame splitter (Part 20 §20.9) |
| FUN_00507360 | `Promos3CanThread::clearSendQueue` | ✅ | drop-all on queue overflow (cap 400) |
| FUN_00508210 | `CanInterface_hasPendingSend` | 75% ⚠️ | returns bool; metacall slot 3 |
| FUN_00506160 | `unitBuffer_remove` | 🔶 | disconnect cleanup |
| FUN_00686770 / FUN_006867f0 | `CanInterface_qt_static_metacall` / `_qt_metacall` | 92% 🔶 | ⚠️ `Promos3CanInterface` is a **plain QObject**, not part of the Eth vtable hierarchy; its 11-entry vtable is all boilerplate and its real entry points are metacall slots 0–3 |
| FUN_0042ec10 | `CanThread_run` | 92% ✅ | [tag-proven] `"Promos3CanThread"`. init → `QThread::exec()` → teardown; logs start/terminate |
| FUN_0042eed0 | `CanThread_onTimerTick` | 92% ✅ | the **3 ms polled loop**: searchForNewUnits → msleep(3) → pollMessages → receive → QTimer(3 ms) |
| FUN_0042e780 | `Promos3CanThread_instance(create)` | 85% 🔶 | |
| FUN_0042f070 | `CanThread_postPaket` | 86% 🔶 | emit toward the CAN thread |

## 13.2 Reassembly, unit communication and framing

| Address | Name | Conf. | Purpose |
|---|---|---|---|
| FUN_006823b0 | `unitBuffer_appendCanData` | 🔶 | Append data bytes; sub-streams `+0x08` header/len and `+0x0c` data; first frame restarts the timeout |
| FUN_00682830 | `unitBuffer_hasCompleteMessage` | 🔶 | Complete when received ≥ expected |
| FUN_00686430 | `UnitComm_firstReceivedPaket` | 90% ✅ | routes `group == 0 \|\| group == 1` → MC_ assembler; group 2 → MC3_ assembler |
| **FUN_00684160** | **`UnitComm_assembleAnswer_MC`** | 93% 🔶 | ⭐ the MC_ answer assembler: sequence check, 7B/frame, expected countdown, checksum, rollback + retry |
| **FUN_00685940** | **`UnitComm_assembleAnswer_MC3`** | 95% ✅ | [tag-proven] `"ReceiveProvis3Paket"`. 8B/frame, no seq, command+length on the wire |
| FUN_00683e00 | `UnitComm_checkAnswerTimeout` | 88% 🔶 | returns status 0/1/3/4 |
| FUN_006823f0 | `UnitComm_deleteReceivedMessages` | 95% ✅ | flush received frames (called at **send** time) |
| FUN_00684030 | `UnitComm_clearRequestQueue` | 90% 🔶 | drop the request queue on abort |
| FUN_00682d20 | `UnitComm_receiveMonitoringData` | 90% 🔶 | CAN streaming path (MC3_ only), queue at `this+0x0c` |
| FUN_00681f30 | `UnitComm_updateFeatureInfo` | 80% 🔶 | |
| **FUN_004425c0** | **`promos3_checksum`** | **96% ✅** | ⭐ byte-verified against a real logged request (§3.4) |
| FUN_00682010 | `canFrame_appendHex` | 95% ✅ | proves `TPCANMsg` LEN @+5, DATA @+6 |

## 13.3 Dispatch, routing and threads

| Address | Name | Conf. | Purpose |
|---|---|---|---|
| 0x004125d0 | `Command_Dispatch_Switch` | 95% ✅ | 2-level dispatch: group=*(msg+0x00), command=*(msg+0x28); frees the msg after handling |
| FUN_00436470 | `Paket_getGroup` / `getMessageGroup` | 95% ✅ | `return *msg` (group at obj+0x00) |
| FUN_004152c0 | `Router_dispatchInbound` | 95% ✅ | `Command_Dispatch_Switch(Promos3DatenInstanz, msg)` |
| FUN_00415370 | `Router_routePaketOutbound` | 92% 🔶 | outbound arm: RouterObj.type 2 → Eth, 3 → CAN |
| FUN_00415600 | `Promos3Router_instance` | 88% 🔶 | |
| FUN_004156a0 | `Router_registerUnit` | 96% ✅ | sends `MC_GIVESTATUS` as **group 0** |
| FUN_0046a310 | `Promos3RouterObj_ctor(this, name, type)` | 85% 🔶 | `{int type; QString name}` — 1 = source tag, 2 = Ethernet, 3 = CAN |
| FUN_0046a460 | `Promos3RouterObj::operator!=` | ✅ | confirms the 8-byte `{int type; QString name}` layout |
| FUN_0042db50 | `KommandoThread_run` / `Promos3KommandoVerteilerThread_run` | 95% ✅ | dispatcher loop; drains `+0x0c` inbound and `+0x08` outbound under mutex + condvar |
| FUN_0042d960 | `KommandoVerteiler_enqueuePaket` | 90% ✅ | outbound enqueue |
| FUN_0042d8a0 | *(enqueue helper)* | — | sibling of the above |
| FUN_00409ca0 | `resolveTarget` | 🔶 | resolve unit object by station (mutex `"Vorverarbeitung_Kom"`) |
| FUN_0047fde0 | `getTargetType` | 🔶 | `return *(unit+0x0c)` — unit generation (1 = MC_, 2 = MC3_) |
| FUN_00412290 | `DatenInstanz_handleGTypeAnswer` | 75% ⚠️ | group-0/1 cmd 2 — **decides the generation** |
| FUN_00411960 | `DatenInstanz_closeDevices` | 93% ✅ | [tag-proven] `"Promos3DatenInstanz::CloseDevices"` |
| FUN_0040c400 | `dispatch_alarmIfType2` | 🔶 | leaf → `bearbeite_Kom_15` (MC3_ALARM) |
| FUN_00404dc0 | `Packet_checkCommandKnown` | 88% 🔶 | [tag-proven] `"ID_FEHLER_PAKET_KOM_NULL/UNBEKANNT"`; validates command `+0x28` ∈ 1..0xFF |
| FUN_00404790 | `Packet_checkExpectedEnAll` | 86% 🔶 | [tag-proven] `"Untersuche_enAll_PaketaufFehler"`; rejects a command not in {1,2} |
| FUN_00402030 | `Promos3Interface_ctor` | 90% 🔶 | [tag-proven] `"Promos3Interface"`; the bootstrap |
| FUN_0041c090 | `Interface_setOfflineMode` | 95% ✅ | [tag-proven] `"SetOfflineMode"` |
| FUN_00442b60 | `Interface_onUnitConnected` | 80% 🔶 | wires `DataReceived`/`UnitDisconnected`; persists `LastUsedPort`; starts the poll timer |

## 13.4 Paket and message creator

| Address | Name | Conf. | Purpose |
|---|---|---|---|
| 0x0042d190 | `MsgCreator_createPaketForCommand` | 96% ✅ | builds and **zero-fills** the wire buffer; does **not** write the checksum |
| — | `MsgCreator_lookupCmdDescriptor` | *(unread)* | the `{wireCmd, length, flags}` descriptor table for both generations |
| — | `MsgCreator_getCommandByte` | — | name→command-byte registry, per generation |
| FUN_0042b1f0 | `MsgCreator_buildMC3Registry` | 95% ✅ | builds the MC3_ name↔code map (`+0x14`) and the per-command field-descriptor map (`+0x18`) |
| FUN_00427f00 | *(registry insert helper)* | — | |
| FUN_00428000 | *(field-descriptor insert helper)* | — | |
| FUN_0042b070 | *(commit field list helper)* | — | |
| FUN_00442650 | `Promos3Paket_ctorNull` | 92% 🔶 | 0x50-byte null ctor |
| FUN_00442430 | `Paket_getRouterKeyA` | 88% 🔶 | `= p+4` |
| FUN_006796c0 / FUN_004423f0 | `Paket_getRecvSize` / `Paket_setRecvSize` | 92% 🔶 | `+0x14`, the expected answer size |
| FUN_00442450 | `Paket_getRecordSize` | 85% 🔶 | `+0x34`, used by the `0x16` length formula |
| FUN_004429f0 | `Paket_setByteArray` | 88% 🔶 | writes the **aux context** vector at `+0x20`, *not* the wire buffer |
| FUN_004315e0 | `QByteArray_assign` | 88% 🔶 | |
| FUN_00442470 | `Paket_appendDataHex(str, maxBytes)` | 93% 🔶 | the log dumper — **caps at 8 bytes**, which is why logged requests look single-frame |
| FUN_00442410 / FUN_00442400 | `Paket_getPriority` / `Paket_setPriority` | 85% 🔶 | priority 2 = front of queue |
| — | `stream_peekCurrent` | — | returns the **wire** `QByteArray::Data` (payload at Qt4's `+0x10`) |
| — | `stream_peekU16` | — | reads the `+0x20` aux context vector |

## 13.5 Device (`Geraet`) and channel layer

| Address | Name | Conf. | Purpose |
|---|---|---|---|
| FUN_004cd420 | `Geraet_bearbeite_Kom_06_MC_GIVEKONFIG` | 97% ✅ | logs "Version N Channels C Sensors S" |
| FUN_004c5840 | `Geraet_expectedRecordSize(komNr)` | 97% ✅ | the expected-**answer**-size table (§3.5.2) |
| FUN_004c56a0 | `Geraet_getGeraetTyp` | 96% ✅ | returns `this+0x4ba`; compared as an **ASCII char** (`'D'`=0x44, `'H'`=0x48) |
| FUN_004c5c70 | `Geraet_getRecordVersion` | 40% ⚠️ | **unread** — the version→layout selector (G6) |
| FUN_004a7ec0 | `Kanal_addMerkmalData(featureCount, stream, &status)` | 92% ✅ | the live measurement block decoder (§6.2) |
| FUN_004e1190 | `Kanal_getFlagWord(idx, sel)` | 60% ⚠️ | |
| FUN_004b9640 | `GetMerkmalInZykAnz` | 95% ✅ | features-in-cycle count |
| FUN_00482090 | `getCurrentFeatureInCycleCount` | 95% ✅ | |
| FUN_004adb90 | `GetPLCrec` | 95% ✅ | |
| FUN_0047ee10 / FUN_0047ac60 / FUN_0047a7a0 | `Provis3Zyklus_assign` / `_dtor` / `_clear` | 90% 🔶 | |
| FUN_004abb20 | **`MonitorTypes_resolveName`** | ✅ | ⭐ resolves the model string; **1-based** GSubType index (§8.6) |
| FUN_00654eb0 / FUN_00654ee0 | `Promos3DatenProvis2Error_ctor` | 85% 🔶 | |

## 13.6 `MC_` senders (app → device)

| Address | Name | Conf. |
|---|---|---|
| FUN_004c65d0 | `Sende_Kom_01_MC_GIVESTATUS` — no parameters, **no `setRecvSize`** | ✅ |
| FUN_004acd20 | `Geraet_sendeKom_02_MC_GIVEGTYPE` | 95% ✅ |
| FUN_004cd650 | `Sende_Kom_08_MC_GIVEPLCVALUES` — station param + the D4 size branch | ✅ |
| FUN_004c6b90 | `Geraet_sendeKom_MC_GIVEHARDWAREREC` | 96% ✅ |
| FUN_004d0320 | `Geraet_sendeKom_MC_GIVEKANAL` (cmd 0x0e) | 96% ✅ |
| **FUN_004d1310** | **`Sende_Kom_MC_GIVESAMMELMERKMALE` (cmd 0x16)** — ⭐ **the whole poll cycle** | ✅ |
| **FUN_004d1810** | **`Sende_Kom_27_MC_GIVESIGNALVERLAUF` (cmd 0x1b)** — 4 params + mode magic | 96% ✅ |
| FUN_004d1de0 | `Sende_Kom_28_MC_GIVEOLDWORKPROZ` (cmd 0x1c) | ✅ |
| FUN_004d23d0 | `Sende_Kom_31_MC_GIVEMUSTER` (cmd 0x1f) — packed nibble param | ✅ |
| FUN_004ce000 | `Sende_Kom_35_MC_GIVE_SENSORVALUES` (cmd 0x23) — round-robin sensor index | ✅ |
| FUN_004c7000 | `Sende_Kom_60_MC_GET_GERAET_ACF` (cmd 0x3c) | ✅ |
| FUN_004c6ca0 | `Geraet_sendeKom_MC_GIVEDYNVALUES` | 95% ✅ |
| FUN_0040d2c0 | `Daten_sendeKom_GIVEKANAL_forTarget` | 90% 🔶 |
| FUN_0040a620 | `Sende_Kom_P2_DOWNLOAD` — reveals the full Paket ctor signature | ✅ |

## 13.7 `MC3_` senders (app → device)

All 95% ✅, tag-proven. `MC3_` senders write the sub-command at `data[2]` and the payload from
`data[3]`.

| Address | Name |
|---|---|
| FUN_004ace30 | `Geraet3_sendeKom_03_MC3_GET_CB_VERSION` |
| FUN_004b1540 | `Geraet3_sendeKom_04_MC3_MERKMAL_INFO` |
| FUN_004b1da0 | `Geraet3_sendeKom_06_MC3_GERAETEREC` |
| FUN_004c1090 | `Provis3Geraet_sendKom07_SetStreaming` — [tag-proven] `"…Sende_Kom_07_MC3_SET_STREAMING"` |
| FUN_004b1fd0 | `Geraet3_sendeKom_08_MC3_LIMIT_INFO` |
| FUN_004b26a0 | `Geraet3_sendeKom_09_MC3_CYCLE_INFO` |
| FUN_004b3240 | `Geraet3_sendeKom_10_MC3_PLC_SETTINGS` |
| FUN_004b3550 | `Geraet3_sendeKom_11_MC3_SENSOR_VFAKT` |
| FUN_004b50e0 | `Geraet3_sendeKom_13_MC3_GERAETE_SETTING` |
| FUN_004b5490 | `Geraet3_sendeKom_14_MC3_SYSTEM` |
| FUN_004b5830 | `Geraet3_sendeKom_15_MC3_ALARM` |
| FUN_004b6380 | `Geraet3_sendeKom_16_MC3_EVENT` |
| FUN_004b6ac0 | `Geraet3_sendeKom_24_MC3_SYSTEM_MODE` |
| FUN_004af1e0 | `Geraet3_sendeKom_99_MC3_DOWNLOADFILE` |
| FUN_004ba490 | `Sende_Kom_99_MC3_DOWNLOAD` — group 2, N/A here |

## 13.8 Command workers / body decoders

| Address | Name | Purpose |
|---|---|---|
| FUN_0040af30 | `(MC_) GIVESIGNALVERLAUF` dispatch wrapper | → `bearbeite_Kom_27` |
| FUN_004d1b70 | `bearbeite_Kom_27` (MC_) | signal-trace header (5B) → `decodeSignalTrace_A/B` |
| FUN_00497d30 | `decodeSignalTrace_B` | 125 × int16 LE amplitude → `QList<short>`. **THE amplitude decoder** |
| FUN_00496920 | `decodeSignalTrace_A` | amplitude variant (mode == 1) |
| FUN_004bc090 | `bearbeite_Kom_04` (MC3_SENSOR_INFO) | 31-byte records keyed by u16 sensorId → sensor map + SQLite |
| FUN_004b5ba0 | `bearbeite_Kom_15` (MC3_ALARM) | alarm/status; entries `[u16 alarmNo][31B rec]`; map @+0xC4; reads `payload[0]` as the station |
| FUN_004b6580 | `bearbeite_Kom_16` (MC3_EVENT) | event log (§6.6); map @+0xC4 |
| FUN_004b9150 | `bearbeite_Kom_27` (MC3_SET_OUTPUTS) | output-set ack ("Outputs successfully set") |
| FUN_004acf40 | `(MC3_ 0x11 worker)` | **STUB** — `return p != 0`; no runtime scaling extraction |
| FUN_004dc3e0 | `(MC_ cmd 0x29 worker)` | parse record, timestamp, store, GUI update |
| FUN_004be820 | `bearbeite_Kom_12_MC3_…` | wrong generation for this box |
| FUN_00484ec0 | *(per-channel map insert)* | used by alarm and event decoders |
| FUN_00626960 | *(alarm `QDateTime` reader)* | source of `Alarms.TimeOffset` |
| FUN_00642ff0 | *(event state-marker helper)* | |
| FUN_0048e500 | *(per-feature node predicate)* | used by the `0x1b` mode selection |

## 13.9 Ethernet interface / TCP socket

| Address | Name | Conf. |
|---|---|---|
| FUN_004fb1c0 | `Promos3EthInterface` (ctor / wiring) | 🔶 |
| FUN_00443150 | `EthAbstract_setForSending_stub` (vtable idx 12 marker) | 96% ✅ |
| FUN_004fef00 | `EthInterface_setForSending` | 95% ✅ |
| FUN_004ff2c0 | `Promos3EthInterface_send` | 96% ✅ |
| FUN_005018f0 | `Promos2EthInterface_setForSending` ⚠️ *(was mislabelled as the CAN interface — Part 20 §20.10)* | 95% ✅ |
| FUN_00501e10 | `Promos2EthInterface_send` | 96% ✅ |
| FUN_00500970 | `EthInterface2_receiveData` | 92% ✅ |
| FUN_004fc540 | `EthInterface_onReadyRead` | 85% 🔶 |
| FUN_004fd3a0 | `EthSocket_streamingDataReceived` | 94% ✅ |
| FUN_004fbae0 | `EthThread_initFromIni` (streaming variant) | 90% 🔶 |
| FUN_00500390 | `EthThread2_initFromIni` (lean sibling) | 78% 🔶 |
| FUN_0042e3b0 | `Promos3EthThread_instance(create)` | 94% ✅ |
| FUN_0042ddc0 | `Promos3EthThread_initInterface` | 92% ✅ |
| FUN_0042e230 | `EthThread_postPaket` (emit) | 86% 🔶 |
| FUN_00446910 | `Interface_pumpSendQueues` (virtual +0x38) | 92% ✅ |
| FUN_00444860 | `Interface_clearSendQueues` | 88% 🔶 |
| FUN_00444090 | `Interface_setLastSentPaket` | 95% ✅ |
| FUN_00444020 | `Interface_getUnitSendStatus` | 88% 🔶 |
| FUN_00444910 | `Interface_getSendQueueForUnit` | 90% 🔶 |
| FUN_00556030 | `Promos3EthAbstract_qt_metacall` | 90% 🔶 |
| FUN_00555580 | `Promos3TcpSocket_ctor` | 93% ✅ |
| FUN_005559b0 | `Promos3TcpSocket_sendToUnit` | 96% ✅ |
| FUN_00554e30 | `Promos3TcpSocket_getStatus` — auto-raises `unitAnswerTimeout` and writes it back to the INI | 96% ✅ |
| FUN_00554630 | `socketStateToString` | 95% ✅ |
| FUN_00554590 | `TcpSocket_readAllInto` | 90% 🔶 |
| FUN_00554d10 | `TcpSocket_resetTimer` | 85% 🔶 |
| FUN_00553310 | `SocketMap_getForUnit` | 90% 🔶 |
| FUN_006dcab0 | `EthSettingsDlg_loadFromIni` | 88% ✅ |
| FUN_006dba10 | `EthSettingsDlg_saveToIni` | 83% 🔶 |
| FUN_006d99a0 | `EthSettingsDlg_setupUi` | 85% 🔶 |
| FUN_006da550 | *(CAN settings-dialog builder)* — confirms a single "Base Tx" | ✅ |

## 13.10 SQL / database

See also Part 11 §11.3.2 and §11.4, which list the read-path SQL entry points with their queries.

| Address | Name | Conf. |
|---|---|---|
| FUN_005befb0 | `DB_insertSensorRow` | 🔶 |
| FUN_00525530 | `SqlDb_getVerbindung` | 92% ✅ |
| FUN_00524480 / FUN_00446bc0 / FUN_00446c90 | `Verbindung_copyCtor` / `_ctorNull` / `_dtor` | 85–88% 🔶 |
| FUN_00556680 | `SqlBuild_insertColumnPrefix` | 86% 🔶 |
| FUN_005565e0 | `SqlBuild_valuesPrefix` | 86% 🔶 |
| FUN_00557670 | `SqlDialect_ensureMap` | 87% 🔶 |
| FUN_00557610 | `SqlDialect_ctor` | 84% 🔶 |
| FUN_00556f50 | `SqlDialect_buildTokenMap` | 83% 🔶 |
| FUN_0044d0e0 / FUN_0044d290 | *(per-unit DB close, type 1 / type 2)* | 🔶 |

## 13.11 Application, INI, error subsystem and UI

| Address | Name | Conf. |
|---|---|---|
| FUN_004236f0 | `initStatusTables` — builds the decoder rings (ToolStatus @+0x44, SensorType @+0x4c, …) | 🔶 |
| FUN_00437f50 | `ini_readInt` — INI integer read (`tryLock` 3000 ms → ErrorManager on timeout) | 🔶 |
| FUN_004041c0 | `ErrorManager_log` — app-wide log entry (category, level, msg) | 🔶 |
| FUN_00403650 | `ErrorManager_initLogFile` — opens `<settingsDir><LogFile>`; "LOG START at: …" | 🔶 |
| FUN_00421e10 | `GlobaleDaten_loadIniTables` — reads `[AlarmNames]` etc. | 88% 🔶 |
| FUN_0041b800 | `GlobaleDaten_isDownloadMode` | 88% 🔶 |
| FUN_00423370 | `MainWindow_setDownloadMode` | 80% 🔶 |
| FUN_0043dc70 | `Promos3MainWindow_setupUi` — the GUI signal graph (§1.6) | 🔶 |
| FUN_00715220 | `UnitConfigWidget_setupUi` — the app's own field-label dictionary (§8.10) | 95% ✅ |
| FUN_004f5fc0 | *(button bar)* | 🔶 |
| FUN_00433a40 | *(NC comm)* | 🔶 |
| FUN_006e0920 | `Promos2Download_onPushButton5Clicked` | 95% ✅ |
| FUN_005206c0 | `Lade_Alles_aus_PMD_File` — SQL→memory, **no wire traffic** | ✅ |
| FUN_005179c0 | `Lade_Kanal_aus_PMD_File` — SQL→memory, **no wire traffic** | ✅ |
| FUN_00426100 | `GetCurrentPMD` — per-unit PMD name | ✅ |
| FUN_004341f0 | `changePMDfromNC` — Mazak↔PMD bridge (write path) | ✅ |
| FUN_00798020 | `Promos3ProtokollThread::qt_static_metacall` | 🔶 |

## 13.12 Helpers

| Address | Name | Conf. |
|---|---|---|
| FUN_00411650 | `QByteArray_setByteAt(idx, &val)` | 90% 🔶 |
| FUN_00490410 | `QByteArray_resize(n)` | 85% 🔶 |
| FUN_004315e0 | `QByteArray_assign` | 88% 🔶 |
| FUN_0042d800 | `QList_prepend` | 95% ✅ |
| FUN_00454930 | `QList_takeFirstPtr` | 90% 🔶 |
| FUN_00444830 | `QList_firstPtrRef` | 88% 🔶 |
| FUN_00611020 | `SKonfigRec_copy` / `memcpy3` | 65% ⚠️ |
| FUN_004428e0 | *(message teardown before `operator_delete`)* | 🔶 |
| FUN_004c0370 | *(per-feature streaming check)* | — |

## 13.13 Central objects (singletons)

| Global | Object | Ctor |
|---|---|---|
| DAT_00a1a244 | `Promos3DatenInstanz` (central data hub; the dispatch `this`) | FUN_00408440 |
| DAT_00a1a840 | `NCcommThread` | FUN_00433640 |
| DAT_00a19ffc | `Promos3ErrorManager` | FUN_004040f0 |
| DAT_00a1a1cc | `Promos3IniFile` | `Promos3IniFile_ctor` |
| DAT_00a1b1c0 | `Promos3LicenseValidator` | FUN_004aae70 |
| DAT_00a1ab04 | `Promos3SqlDatenbankManager` | FUN_0044cdc0 / instance FUN_0044d070 |
| — | `Promos3DatenInstanz::NewMonitor` emitter | FUN_00408a60 |

## 13.14 Globals

| Address | Name |
|---|---|
| DAT_00a1fc54 | `g_savedRecvSize` (MC_ retry) |
| DAT_00a1fc5c / DAT_00a1fc58 | `g_mc3_answerCommand` / `g_mc3_answerLength` |
| DAT_00a1fc50 | `g_featureInCycleCount` |
| DAT_00a1fc48 / DAT_00a1fc44 | `g_streamCommand` / `g_streamHighNibble` |
| DAT_00a1fc40 / DAT_00a1fc3c / DAT_00a1fc4c | `g_streamExpectedLen` / `g_streamErrorCount` / `g_streamPendingFrames` |
| DAT_00a17914 | `g_unitRescanInterval` (= `unitAnswerTimeout × 3` = 900 ms) |
| DAT_00a1bc2c | `g_lastProbedUnit` |
| _DAT_00a1ac1c | `g_routerObjInstanceCount` |
| DAT_00a1cb88 | *(SQL dialect singleton)* |
| DAT_00a1ab04 | `g_sqlDbManager` |
| DAT_00a1cd04 | `g_dataRecordCount` |
| DAT_00a1cb8c | `g_protokollThreadCount` |
| param_1_00a1d320 | `g_workpiecesTableName` |
| *(alarms table literal)* | `g_alarmsTableName` |

## 13.15 Ignore list — Qt template guts

Named only so nobody re-analyses them. They carry no domain meaning:

```
FUN_005429d0 · FUN_00407d40 · FUN_00406d30 · FUN_00406cf0 · FUN_00408910 ·
FUN_00407c00 · FUN_00406bc0 · FUN_00541e90 · FUN_00541d20 · FUN_005ace00 ·
FUN_0042db20 · FUN_00443710 · FUN_00444350 · FUN_00443f50
```

…plus all `QListData::*` wrappers and the QMap/QVector detach/insert/free family, which are
identifiable by signature alone. The full low-level Qt-container / QString plumbing catalog from
the earliest version of this analysis is unchanged and omitted here for brevity; it is
name-and-forget and not needed to build the reader.

---

# ═══════════════════════════════════════════════════════════════
# PART 14 — KEY CODE SNIPPETS (annotated)   🔶
# ═══════════════════════════════════════════════════════════════

## 14.1 Gateway datagram split — `Scan4CANmsg` (FUN_00507760)

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

## 14.2 The dispatch skeleton — `Command_Dispatch_Switch` (FUN_004125d0)

```c
group = *(u32*)(msg + 0x00);                 // via FUN_00436470
switch (group) {
  case 0: /* handshake: cmd 1 = MC_GIVESTATUS/GIVEGTYPE, cmd 2 = FUN_00412290 */ break;
  case 1: switch (*(u32*)(msg + 0x28)) { /* MC_ table, §5.2 */ } break;
  case 2: switch (*(u32*)(msg + 0x28)) { /* MC3_ table, §5.3 */ } break;
}
FUN_004428e0(msg); operator_delete(msg);     // dispatcher owns + frees the message
```

## 14.3 Leaf routing wrapper (uniform) — e.g. FUN_0040af30 (MC_ signal trace)

```c
station = packet_getStation(msg);
unit    = resolveTarget(this);               // FUN_00409ca0
if (unit && this->quitFlag==0 && getTargetType(unit)==1)   // ==1: MC_ generation
    bearbeite_Kom_27_MC_GIVESIGNALVERLAUF(unit, msg);      // → decodeSignalTrace_B
```

## 14.4 Dispatcher thread loop — FUN_0042db50 (`run()`)

```c
setObjectName("KommandoThread");
for (;;) {
    if (stopFlag@+0x1f) return;
    while (queueA@+0x0c nonEmpty || queueB@+0x08 nonEmpty) {
        lock(mutex@+0x14);
        msg = dequeue(queueA@+0x0c);         // inbound
        aux = dequeue(queueB@+0x08);         // outbound
        unlock(mutex@+0x14);
        if (msg) FUN_004152c0(msg);          // → Command_Dispatch_Switch(DatenInstanz, msg)
        if (aux) FUN_00415370(aux);          // → Router_routePaketOutbound
    }
    lock(mutex@+0x14);
    if (wakeFlag@+0x1e==0) QWaitCondition::wait(cond@+0x24, mutex, INF);
    wakeFlag@+0x1e = 0; unlock(mutex@+0x14);
}
```

## 14.5 Amplitude sample decode — `decodeSignalTrace_B` (FUN_00497d30)

```c
if (payload > 0xFB) {                        // need > 251 bytes
    puVar6 = data + 0x10;                    // sample bytes start
    // copy 250 bytes, then read 125 samples:
    for (i = 0x7d; i; i--) { QList_short_append(&list, (u16*)p); p += 2; }
    // samples stored RAW (0..255); no scaling
}
```

## 14.6 The MC_ answer inheritance — `UnitComm_assembleAnswer_MC` (FUN_00684160) tail

```c
group   = Paket_getGroup(requestPaket);          // FUN_00436470 = *(u32*)request
newMsg  = Promos3Paket_ctor(new(0x50), group, routerA, routerB, &assembledBytes, 0, 0);
newMsg[10] = local_13c;        // +0x28 = command  <-- copied from the REQUEST
newMsg[11] = requestPaket[11]; // +0x2c
newMsg[12] = requestPaket[12]; // +0x30
FUN_004429f0(newMsg, stream_peekU16(request));   // aux context copied request -> answer
```

## 14.7 Request construction — `MsgCreator_createPaketForCommand` (0x0042d190)

```c
d = MsgCreator_lookupCmdDescriptor(this, ..., group, &cmdByte, subCmd);
append(buf, (char)d[0]);                       /* wire command byte */
if (group == 2) append(buf, (char)d[1]);       /* MC3_ only: length byte */
for (i = d[1]-1; i; i--) append(buf, '\0');    /* zero-fill */
paket = Promos3Paket_ctor(new(0x50), group, srcTag, dstKey, &buf, d[2], param_6);
paket[10] = cmdByte;   /* +0x28 */
paket[11] = subCmd;    /* +0x2c */
```

| group | buffer | total |
|---|---|---|
| 0/1 (MC_) | `[cmd][00]×(len-1)` | `len` |
| 2 (MC3_) | `[cmd][len][00]×(len-1)` | `len + 1` |

Signature: `(this, group, srcTag, dstKey, cmdByte, subCmd, 1)`. Argument 7 is `1` at all **77**
call sites. `cmd == 0` → `"wrong command number for %1"`, returns NULL.

The full Paket ctor signature, recovered from `Sende_Kom_P2_DOWNLOAD` (`FUN_0040a620`):

```c
Promos3Paket_ctor(mem, group, srcRouterObj, dstRouterObj, QByteArray, 0, 1)
// setting Paket[10] = 0xFFFFFFFF marks a raw / no-command packet
```

## 14.8 Config record proof — `SGeraetRec` vs `Devices` (re-verified against `1974.txt`)

```
RAW HEX:  44 05 01 04 … 80 80 80 80 80 80 80 80 … D4 19
           │  │  │  │     └──── MiSensType[8] ────┘   └ ReduzLim (LE) = 6612
DB row:   68 5 1  4       = 128 each                = 0x19D4
Result:   MATCH MATCH MATCH MATCH  MATCH             MATCH
```

## 14.9 Feature-name decode — `SKanalRec` (this box, verified against `1974.txt`)

```
+0x4D: 01 56 49 42 52 41 54 49 4F 4E 00 00  → mask 0x01 "VIBRATION"
       02 4D 31 33 31 20 44 45 42 49 00 00  → mask 0x02 "M131 DEBI"
       04 4D 31 33 31 42 41 53 49 4E 43 00  → mask 0x04 "M131BASINC"
       08 4D 30 38 20 44 45 42 49 00 00 ..  → mask 0x08 "M08 DEBI"
```

## 14.10 The checksum, as a portable C function

```c
/* Recovered from FUN_004425c0 (receive side) and cross-confirmed by the inline
 * computation in FUN_00506220 (transmit side). Byte-verified against a real log line. */
signed char promos3_checksum(const uint8_t *recv, int recv_n,
                             signed char seed,              /* = unit id */
                             const uint8_t *sent, int sent_n,
                             int group)
{
    signed char ret = 0;
    if (!sent || (group != 0 && group != 1)) { ret = -1; seed = 0; }
    if (sent && sent_n > 0) {
        for (int i = 0; i < sent_n - 1; i++) seed += sent[i];   /* ALL BUT THE LAST BYTE */
    } else if (group == 1) seed = 0;
    if (recv) for (int i = 0; i < recv_n; i++) seed += recv[i];
    return ret - seed;
}

/* group 0/1 (MC_)  : checksum = -(unitId + Σ sent[0..n-2] + Σ payload)
 * group 2  (MC3_)  : checksum = -1 - Σ msgBytes   ⟺  Σ(all bytes incl. checksum) == 0xFF
 */
```

---

# ═══════════════════════════════════════════════════════════════
# PART 15 — OBJECT LAYOUTS
# ═══════════════════════════════════════════════════════════════

## 15.1 `Promos3Paket` — 0x50 (80) bytes

| off | field | accessor |
|---|---|---|
| +0x00 | group / generation | `Paket_getGroup` (FUN_00436470) |
| +0x04 | routing key A (unit id, stored as **text** → `toInt`) | `Paket_getRouterKeyA` (= p+4) |
| +0x0c | **source tag** (RouterObj) | `param1_+_0xc` |
| +0x12 | streaming byte | used by `SetStreaming` / `CanInterface_receive` |
| +0x14 | **expected receive size** | `Paket_getRecvSize` / `Paket_setRecvSize` |
| +0x20 | **aux context `QVector<u8>`** — never sent on the wire | `Paket_setByteArray` / read by `stream_peekU16` |
| +0x28 | **command** | direct `p[10]` |
| +0x2c | **sub-command / variant** | direct `p[11]` |
| +0x30 | **station / device index** | direct `p[12]` |
| +0x34 | record size (used by the cmd `0x16` length formula) | `Paket_getRecordSize` |
| +0x3c / +0x40 | chunk offset / total (cmd `0x30` segmented transfer) | direct |
| +0x48 | timeout multiplier (init 1) | used by `UnitComm_checkAnswerTimeout` |
| +0x4c | processed flag | used by `CanInterface_receive` |
| — | **the wire buffer** | `stream_peekCurrent` |

⚠️ **Two distinct byte arrays.** `stream_peekCurrent` returns the **wire** bytes;
`stream_peekU16` returns the `+0x20` **aux context**. (An earlier reading had `+0x20` as the
message bytes and `+0x30` as "aux" — both wrong; Part 20 §20.11.)

**Why the aux vector matters.** `Geraet_sendeKom_27` packs `{station, featureKey, p3, p4, mode}`
into `+0x20`, and `UnitComm_assembleAnswer_MC` copies it from the request into the answer.
**That is how `bearbeite_Kom_27` knows which feature it asked for.** It never touches the wire —
so a passive listener must reconstruct it from the request bytes, while a master-mode reader gets
it for free by keeping its own request record. Another point in favour of master mode.

## 15.2 `UnitComm`

```
+0x00  request queue
+0x08  received-frame list
+0x0c  streaming frame list
+0x14  unit RouterObj
+0x1c  QTime
+0x20  attempt counter
+0x24  progress / in-progress marker
+0x28 / +0x2c  timeouts
+0x34  max attempts
+0x40  streaming sequence
+0x44  last-seen frame count
```

## 15.3 `Promos3CanInterface` constructor constants

```c
this+0x14 = gateway-mode flag (> 0 means gateway)
this+0x18 = gateway port (u16)
this+0x20 = 8         this+0x22 = 0x200 (BusID 512)   this+0x24 = 0x16 (BaudrateRegister 22)
this+0x30 = "ProcessControl"    this+0x34 = "sandvik"
this+0x44 = 0x32
this+0x48 = 0x500  /* 1280 — THE BaseCanIDTransfer */
this+0x4c = 1      /* first unit */
this+0x50 = 0x0F   /* last unit  */
this+0x54 = 0x580  /* 1408 — not a transmit base; purpose unknown */
this+0x58 = 0x600  /* 1536 — not a transmit base; purpose unknown */
this+0x70 = gateway QHostAddress
```

## 15.4 `Interface` (Ethernet hierarchy)

```
+0x10  QTimer
+0x18  socket map
+0x40  per-unit send queues
+0x44  per-unit "buffer full" flags
+0x48  log level
+0x4c  last-sent-paket map (keyed by unit — enforces one outstanding request)
```

## 15.5 Ethernet vtable index map

Stable across `Promos3EthAbstract` / `Promos3EthInterface` / `Promos2EthInterface`:

```
11 init · 12 SetForSending · 13 ? · 14 send · 15 receiveData ·
16 ? · 17 onUnitConnected · 18 ? · 19 ? · 20 initFromIni · 21 ?
```

⚠️ **`Promos3CanInterface` is NOT part of this hierarchy.** It is a plain QObject whose 11-entry
vtable is entirely boilerplate; its real entry points are metacall slots:

```
case 0: FUN_00686740
case 1: CanInterface_searchForNewUnits
case 2: FUN_005073f0   <- takes Paket*, the send entry
case 3: FUN_00508210   <- returns bool
```

## 15.6 `Promos3RouterObj` — 8 bytes

`{int type; QString name}`. type **1** = source tag, **2** = Ethernet, **3** = CAN.

## 15.7 `Geraet` — relevant offsets

```
+0x54   station (set by GIVEKANAL sender, read back as the traceMap key)
+0x60   round-robin sensor slot index (used by cmd 0x23)
+0x480  recvSize scratch for cmd 0x16
+0x4BA  SGeraetRec begins (66 bytes, copied wholesale)
+0x4BA  GeraetTyp        +0x4BB  GSubType
+0x4BC  CHANNEL count    +0x4BD  sensor count
+0x4d0  sensor/feature slot table (slots 0–3 features, 4–11 sensors)
+0x4e6  the byte that selects the cmd 0x08 size branch  ← D4, runtime state
+0x688  the flag sent as request byte 2 of cmd 0x16     ← meaning unknown
```

## 15.8 `Kanal` (channel object) — relevant offsets

```
+0x16   channel number
+0xa8   target RouterObj
+0xb0   version
+0xC0   the flag that selects the "+4" stride variant  (== the 'H' GeraetTyp branch)
+0xC4 / +0xCC   live maps
+0xC8 / +0xD0   shadow maps (double buffering across a cycle boundary)
```

## 15.9 `Promos3DataRecord` — 0xF8 (248) bytes

See Part 11 §11.2.1 for the full field map.

---

# ═══════════════════════════════════════════════════════════════
# PART 16 — GAP REGISTER (final state)
# ═══════════════════════════════════════════════════════════════

**Question this Part answers:** *what is still missing before a reader can talk to the device and
display its data correctly, 100% of the time?*

The gap register was opened when protocol knowledge stood at ~78% and a trustworthy reader at
~45%. Each gap carries a **completion %** — how much of that item is in hand, where 100% means
nothing is left to do. The **Progress** column shows how each gap moved across the investigation,
so that a reader of an older document can see where their copy sits.

## 16.1 Scoreboard

| # | Gap | Progress | Now | Blocks live reading? |
|---|---|---|---|---|
| G1 | Message header wire layout | 20% → 95% → **100%** ✅ | **closed by deletion** — no header exists | no |
| G2 | Completion rule + expected-length table | 30% → 90% → **100%** ✅ | seq + 7B/frame + size table + checksum; verified in code **and** in tests | no |
| G3 | Request side / master role | 0% → 35% → 75% → **100%** ✅ | framing, checksum, poll cycle, cadence, discovery all known | no |
| G4 | Capture strategy / CAN-ID base | 0% → 0% → 35% → **100%** ✅ | **one** base; master mode needs no capture at all | no |
| G5 | Checksum | 0% → 90% → **100%** ✅ | two independent code sites + one log line | no |
| G6 | Record-layout versioning (`Geraet_getRecordVersion`) | 20% → **20%** | `FUN_004c5c70` still unread — judged low value | no |
| G7 | `MC_` (group-1) body layouts | ~15% → ~60% → **~65%** | ~35/38 named; `0x1B` and `0x16` decoded; most other bodies not | no |
| G8 | Limits loaded + the "%" display | 60% → 70% → **70%** | alarm, station and field names recovered; limits still not loaded by the reader | no |
| G9 | `channelKey` → feature index encoding | 60% → **60%** | falls out of the first real trace | no |
| G10 | Unit ↔ serial ↔ model string | 70% → **100%** ✅ | 1-based index → `MSL5081-16` | no |
| G11 | Device-side timestamps | 50% → **50%** | app reads a `QDateTime` from the alarm record; reader still uses host clock | no |
| G12 | Reader robustness (timeouts, counters, xlsx durability, record/replay) | 60% → **80%** | link layer written and tested; no `--record` / `--replay` yet | no |
| G13 | *(what is NOT missing)* | — | see §16.4 | — |
| **D3** | Real expected answer sizes for `0x01`, `0x12`, `0x1B` | — | **device state — not in the binary** | measurement needed |
| **D4** | The `0x08` size branch (`Geraet+0x4e6`) | — | **device state — not in the binary** | measurement needed |

**Aggregate**

| Measure | Then | Now |
|---|---|---|
| Protocol *knowledge* (transport + framing + config + DB + dispatch) | ≈78% | **≈99%** |
| Live *reader* that is correct and trustworthy end to end | ≈45% | **≈75%** |
| Group-1 commands named | 3 / 38 | **~35 / 38** |

## 16.2 The gaps that remain open, in detail

### `<!> G6 — Record-layout versioning` — **20%**

Every handler calls `Geraet_getRecordVersion` (`FUN_004c5c70`) **before** parsing and passes the
version into the record parsers. Record names are version-stamped (`SKanalRec**V40**`,
`SZykRec**V4802**`) and this box reports **Version 229**. So layouts are version-selected and any
reader that hardcodes one variant is correct *only* for firmware `Rtm_V14.5.H86` / Version 229.

**Needed:** decompile `FUN_004c5c70` plus the version→layout switch. **Judged low value** while
only one firmware is in scope.

### `<!> G7 — `MC_` (group-1) body layouts` — **~65%**

38 group-1 commands are located and ~35 are now named (§5.2). **Two bodies are decoded**: `0x1B`
(the signal trace) and `0x16` (the live measurement block, including its exact stride).

The alarm layout in §6.4 is **`MC3_`-derived** and must stay flagged PROVISIONAL — meaning a
faithful reader will show group-1 alarms as a hexdump, not as alarms. For a display that matches
the app you minimally need the `MC_` variants of **alarm/status**, **cycle start/end**, and
whatever carries the tool/cycle context (candidates: `0x0c`, `0x0d`, `0x29`).

### `<!> G8 — Limits and the "%" display` — **70%**

The on-screen "%" is `raw / limitLevel × 100` (Part 7). The limit levels are parsed by the PMD
parser, but the reader's `reader_apply_pmd()` only loads `SGeraetRec` and `SKanalRecV40`;
cycles and limits are never loaded into `reader_state_t`, and nothing computes the percentage.
**The bar chart can be drawn; the limit line and the alarm colour cannot.**

Recovered since: alarm slot names (§8.7), station names (§8.9), the model string (§8.6) and the
app's own field-label dictionary (§8.10) — everything the display needs *except* the limit load
itself. Estimated ~1 day of work.

### `<!> G9 — Trace → feature mapping (`channelKey` encoding)` — **60%**

The reader's `key_to_index()` accepts *three* encodings — a feature mask (`1/2/4/8`), a flagged
mask (`0x81/0x82/…`) and a plain index (`0..3`) — because it is unknown which one `channelKey`
actually uses. The ambiguity resolves itself on the first real trace, but until then a wrong guess
mislabels every plotted bar, and this box's labels are operator-assigned Turkish/German shop
labels (`VIBRATION / M131 DEBI / M131BASINC / M08 DEBI`), so **a wrong label looks entirely
plausible**.

⚠️ One hint exists but is from the **wrong generation**: `MC3_` packs the cycle in the low 12 bits
and the channel in the high 4. Do not apply it to `MC_` without confirmation.

Also remember `0xFB` / `0xFD` are reserved feature selectors and must never go through
`key_to_index()` (§3.3).

### `<!> G11 — Device-side timestamps` — **50%**

The reader stamps rows with *its own* clock at print time. The app reads a `QDateTime` out of the
alarm record (`FUN_00626960`) and stores `Alarms.TimeOffset` relative to cycle start. Under load,
host-clock stamping will misorder events against the machine's own log. Best closed together with
G7.

### `<!> G12 — Operational robustness of the reader itself` — **80%**

| Item | State | Fix |
|---|---|---|
| Reassembly timeout | **was absent** → now in the link layer | per-unit deadline; flush + count on expiry (as the app does) |
| Lost-frame recovery | **was absent** → now resyncs on sequence | after a sequence break, resync on the next first frame |
| Counters (dropped / bad-checksum / unparsed) | now counted | print on exit |
| xlsx durability | all rows held in RAM, written **only** on clean exit | flush periodically, or append CSV and convert later |
| xlsx memory | unbounded growth on a long run | same fix |
| **Offline replay** | **still absent** | see below |

> **The highest-value missing tool: record & replay.** There is still no way to save raw datagrams
> and re-run the decoder against them. Every calibration attempt therefore needs the live machine.
> Add `--record FILE` (dump raw datagrams + timestamps) and `--replay FILE` (feed them back
> through the same path). This turns every remaining measurement question from "book a machine
> window" into "iterate at a desk", and it is **~50 lines of code**.

### `<!> D3 — Real expected answer sizes for `0x01`, `0x12`, `0x1B`` — device state

The size table (§3.5.2) is authoritative for `0x02` (14) and `0x0e` (144, call-site verified). The
values currently used for `0x01`, `0x12` and `0x1B` are **guesses**:

- `0x01 MC_GIVESTATUS` never calls `Paket_setRecvSize` at all — its expected size comes from
  `createPaketForCommand` defaults and is unknown. **A poor first probe.**
- `0x12 GIVEALARM` was mapped onto the table's `0x11` entry, which is `ALARMGESEHEN`, not
  `GIVEALARM` — probably wrong.
- `0x1B`'s value of 257 comes from a *synthetic* test, not real bytes.

### `<!> D4 — The `0x08` size branch` — device state

```c
if (version < 0xD6 || Geraet[0x4e6] == 0)
     n = base + (GType=='D'||'H' ? 1 : 0) + (traceMapNode(station)==4 ? 1 : 0);
else n = (Geraet[0x4e6] >> 4) + (Geraet[0x4e6] & 0x0F);
```

Version is `0xE5`, so **if `Geraet+0x4e6` is nonzero the nibble branch applies** and any statically
chosen value is wrong. That byte arrives from device configuration at runtime. It is not in the
executable.

## 16.3 Minor open assumptions

- The **answer-direction checksum seed** is assumed symmetric with the request direction; it is
  verified for requests only.
- The device-error `LEN == 2` constraint (§3.2) is inference, added because the documented
  signature alone is ambiguous.
- `Geraet+0x688` — the flag that becomes request byte 2 of `0x16` — is sent as 0; meaning unknown.
- The 3 reserved bytes at the head of the first request frame — purpose unexplained.
- `Paket_setPriority(…, 2)` — a priority queue exists and is currently ignored; harmless while
  only one request is outstanding.
- Requests longer than 7 payload bytes need splitting; irrelevant for the read-only poll set
  (all ≤ 4 bytes).
- The `MC3_` field-descriptor attributes `A` and `B` (§5.5) are interpreted as size and type
  respectively; binding them needs one raw frame.
- Which of `EthThread_initFromIni` / `EthThread2_initFromIni` is called from where (§12.4).
- ⚠️ Size-table entries `0x03`, `0x10` and `0x3f` do not align with the recovered command names,
  which suggests the switch may be keyed by record type for some entries (§3.5.2).

**Every size doubt degrades into a timeout, not corruption.** The request tracker catches it, the
counters record it, and nothing reaches the output as a plausible-looking lie. That is exactly
what the `CONF_*` confidence gating was built for.

## 16.4 `<!> G13 — What is NOT missing` (so nobody re-does it)

✅ Gateway record split, CAN-ID big-endian, `unit = ID − 1280` — verified, and the reader
implements the front-trim exactly as `Scan4CANmsg` does.
✅ The 36-byte **transmit** record — byte-exact (`00 24 00 80` + zeros).
✅ Payload little-endian; **no scaling factor** (raw 0–255) — verified against two databases.
✅ The checksum algorithm — recovered from two independent code sites and byte-verified against a
real log line.
✅ `MC_` answer framing — sequence byte, 7 payload bytes per frame, checksum position including
the checksum-only frame case.
✅ `MC_` request framing and splitting — byte-exact and verified twice.
✅ The completion rule and the expected-size table (with the three doubtful entries flagged).
✅ Unit discovery, the 3 ms cadence, the one-outstanding-request rule and the retry ladder.
✅ Config records (`SGeraetRec`, `SKanalRecV40`, `SZykRecV4802`, `SGrenzRec`, `SHardwareRec`) and
the PMD parser — byte-for-byte against `1974.txt`; the `--config-unit` path works.
✅ Decoder rings (ToolStatus, SensorType, ChannelStatus, AccessLevel, EventCode, alarm slot names)
and both DB schemas.
✅ The model string — `MSL5081-16`.
✅ Dispatch map (~70 handlers across both groups), the `MC3_` command registry, and the `MC3_`
per-command field descriptors.
✅ The `MC3_` framing, its 16-bit length extension, and its separate checksum scheme.
✅ The reader's **honesty design** — `CONF_UNKNOWN / NAMED / PROVISIONAL / CONFIRMED` gating means
it hexdumps anything it cannot prove. **Keep this.** It is the reason the early header mistake was
mostly loud rather than silent.

## 16.5 The capture that used to be the whole plan

```ini
; PROVISsettings.ini
[ErrorManager]
LogCANMessage = 1        ; currently 0
```

Run PROVIS3 against the machine for 60 seconds with the monitoring screen open, then take the log.
Raw CAN frames are written to it. **No Wireshark, no PEAK card, no admin rights.**

⚠️ **Its role has changed from discovery to validation.** When the gap register was opened, this
single artefact was going to close G1 (header offsets, anchored on `E5 01 04` from the KONFIG
answer), G2 (where the length lives), G5 (checksum shape) and part of G4. All of those are now
closed by static analysis instead. What the capture is still good for:

- confirming the sequence/checksum framing against real bytes;
- resolving the `channelKey` encoding (G9);
- checking a **unit-2** request, to double-confirm that request byte 1 is the station;
- confirming that received gateway records also start `00 24 00 80` (free symmetry check).

---

# ═══════════════════════════════════════════════════════════════
# PART 17 — READER IMPLEMENTATION GUIDE
# ═══════════════════════════════════════════════════════════════

## 17.1 The decision that shapes everything: passive or master?

**Recommendation: master mode.**

| Deployment | Works? | What it needs |
|---|---|---|
| PROVIS3 runs and polls; reader listens passively | data flows | **a both-direction port mirror** (see below) |
| PROVIS3 stopped; reader listens passively | **silent forever** | nothing on the bus to hear |
| Reader replaces PROVIS3 (master) | works standalone | request framing, discovery, poll loop — **all now known** |

**Why passive is hard.** `MC_` answers are anonymous (§3.1), so decoding *anything* requires
observing **both** app→gateway requests and gateway→app answers and pairing them per unit. That
removes "bind :1789 and listen" from the table entirely:

- The gateway traffic is **unicast UDP** between the PROVIS3 host and `192.168.222.17:1789`, and
  the app **binds the port itself** (`"UDP Gateway Socket bound"` / `"UDP Gateway Socket Not bound
  at: %1"`). On the same host, with PROVIS3 running, **one of the two processes gets the datagrams
  — not both**; `SO_REUSEADDR` does not duplicate unicast delivery.
- Remaining passive options: a **switch-port mirror / SPAN** to a second NIC read promiscuously
  (which brings libpcap back into scope), or asking the gateway to also send to a second endpoint
  (undocumented; unknown whether it can).
- On a mirror you also see the app's **requests**, which are *also* 36-byte records with valid
  CAN-IDs. Fed into the same per-unit buffer they will **corrupt reassembly**. A passive reader
  therefore needs `if (src_ip != GatewayAddress) skip;` plus a request/answer discriminator.
- And even then, the aux context vector (`Paket+0x20`) that tells a handler which feature it asked
  for never appears on the wire — a passive reader must reconstruct it from the request bytes.

**Why master is now tractable.** The request format is byte-exact and verified, the checksum is
recovered and verified, `[CAN] unitAnswerTimeout=300`, `[Comm] MaxResend=1`, the discovery
sequence is known, and the cadence is a 3 ms polled loop. A master needs no capture infrastructure
at all.

⚠️ **The one cost of master mode: do not poll a unit that PROVIS3 is also polling.** Stop PROVIS3,
or aim at a different unit. The collision symptom is the log line
`"Trying to send several Canbus commands before answer is received"`.

## 17.2 The one 30-second test

Form this request and send it to `192.168.222.17:1789`:

```
36-byte record:
  00 24 00 80 00 00 00 00 00 00 00 00 00 00 00 00
  00 00 00 00 00 06 00 00 00 00 05 01 00 00 00 08
  01 f6 00 00
                 ^ dlc 6      ^ CAN-ID 0x501   ^ DATA
```

This is `MC_GIVEPLCVALUES`, unit 1, station 1 — the one request whose exact bytes are independently
verified against the runtime log. **If anything comes back, everything else follows. If nothing
does, that is a real result no decompiler was going to give.**

## 17.3 Then measure the sizes

For each of `0x01`, `0x02`, `0x06`, `0x08`, `0x0e`, `0x12`, `0x16`: send the request, accept frames
until the bus is quiet for 300 ms, and record the total payload byte count. That is **the real
size table, measured**. It closes D3 and D4 together and validates the answer-direction checksum
as a side effect.

## 17.4 If machine access is not available

Then the priority inverts and none of §17.2–17.3 applies. Build instead:

1. **`--replay`** against synthetic datagrams, so the decode path can be developed at a desk;
2. **the confirmed constants wired in**, so the tool is ready on the day access happens;
3. **this document**, handed to whoever does have access.

## 17.5 Changes required in the existing reader

The reader's transport layer still implements rules that are now known to be wrong. All of this is
desk work; no machine is needed.

```
DELETE  parse_message_header()                      — no such thing exists for MC_
DELETE  the "short frame ends the message" heuristic — provably corrupts (§18.1)
DELETE  reasm_expected_len()'s fallback              — replaced by the size table

ADD     per-unit request tracker: {command, expectedSize, sentBytes, deadline, attempts}
ADD     frame layer: seq = DATA[0]; payload = DATA[1..LEN-2]; verify sequence continuity
ADD     completion: accumulated == expectedSize (size table, or the 0x16 formula)
ADD     promos3_checksum() verbatim (§14.10)
ADD     checksum-only frame handling when expectedSize % 7 == 0
ADD     status codes 1 = retry / 2 = abort / 4 = incomplete, mirroring UnitComm_assembleAnswer_MC
ADD     device-error detection: DATA[0]==0 && DATA[1]==1 && LEN==2   ← the LEN==2 part matters
ADD     --record / --replay (~50 lines) — the highest-value tooling item

PATCH   gw_build_record(): header = 00 24 00 80, rest zero
PATCH   request framing: [00][00][00][5 payload] then [seq][7 payload]
PATCH   single CAN-ID base; delete any 3-base probe dimension
PATCH   feature-name loading: read from SKanalRec, match on mask & 0x0F
WIRE    the master link layer into main.c as a --master mode

KEEP    the CONF_* honesty gating — it is still what stops guessed layouts printing as fact
```

`promos3_msg_t` loses `group` / `command` as **parsed** fields and gains them as **attributed**
fields, plus a `bool attributed` that is false whenever no request was observed.

## 17.6 Tooling inventory

| File | Contents | State |
|---|---|---|
| `promos3.h` | shared types, transport constants, decoder-ring enums, `CONF_*` gating | present; header comment still describes the two retired "CALIBRATE" items |
| `promos3_transport.c` | 36-byte record split, CAN-ID routing, per-unit reassembly | present; **needs the §17.5 rewrite** |
| `promos3_decode.c` | header parse + body decoders + printing | present; `parse_message_header()` **to be deleted** |
| `promos3_proto.c` | command-name and enum lookups | present; group-1 names can be upgraded from §5.2 |
| `promos3_config.c` / `.h` | PMD config-record parser (`SGeraetRec`, `SKanalRecV40`, cycles, limits) | present and working (`--config-unit`) |
| `promos3_state.c` / `.h` | reader state | present; **does not yet load cycles/limits** (G8) |
| `span.h`, `xlsx.c` / `.h` | byte-span helper; xlsx writer | present; xlsx flushes only on clean exit (G12) |
| `main.c` | UDP listener + modes (`--raw`, `--decode`, `--config-unit`) | present; binds `INADDR_ANY:1789`; **no source-address or direction filter** |
| `promos3_master.h` / `.c` | `MC_` master link layer: checksum, request builder, frame layer, completion rule, per-unit request tracker, poll cycle, retry ladder, counters, RX record split | **written and tested** — ⚠️ *not present in the current project tree; retrieve it or rewrite from Part 3* |
| `test_master.c` | 20 assertions, all passing (§18.2) | **written** — ⚠️ *same caveat* |
| `promos3_learn.c` | probe / measure harness | **largely obsolete** now that the transmit path is byte-exact |
| `promos3_listen.c` | early UDP listener/decoder (no pcap, no admin) | superseded — assumed a clean Promos3 body per datagram |
| `promos3_records.h` | verified packed structs | superseded by `promos3_config.*`; feature-name handling must follow §9.2 |
| `promos3_sniff.c` | pcap variant (needs libpcap + admin) | retired — ⚠️ **may need to come back** if passive mode with a port mirror is chosen (§17.1) |

Build lines in use:

```
gcc -std=c11 -Wall -Wextra -O2 -Isrc (src\*.c) -o promos3_reader.exe -lws2_32
gcc -std=c11 -Wall -Wextra -O2 -Isrc tools\pmd.c src\promos3_config.c src\promos3_proto.c -o promos3_pmd.exe

.\promos3_reader.exe --raw
.\promos3_reader.exe --decode --config-unit 1=test\exVL2-1.txt --config-unit 2=test\exVL2-1.txt
```

## 17.7 Stop reading Ghidra

Protocol knowledge is ~99%. The transmit path is byte-exact. The remaining 1% is device runtime
state. In the final analysis session, eleven functions moved *knowledge* from 92% → 99% while the
*reader* moved 45% → 75% — and the 75% came from **writing code, not from reading functions**.

Two functions were once on the "read next" list and are now judged not worth it:

1. `Geraet_getRecordVersion` (`FUN_004c5c70`) — only matters if a second firmware version comes
   into scope (G6).
2. `MsgCreator_lookupCmdDescriptor` — would give the authoritative `{wireCmd, length, flags}`
   table for both generations and verify every request length. Genuinely useful, but not blocking.

Also unread and optional: `MsgCreator_getCommandByte`'s `MC_` name→byte table (§5.2), which would
cross-check the string-derived group-1 command names.

**The next byte of useful information has to come from the machine.**

---

# ═══════════════════════════════════════════════════════════════
# PART 18 — TEST EVIDENCE
# ═══════════════════════════════════════════════════════════════

## 18.1 The corruption bug in the original transport — reproduced and then fixed

Synthetic gateway datagrams fed through `gw_parse_record → reasm_feed → parse_message_header →
print_message`, using the original "a frame shorter than 8 bytes ends the message" heuristic:

```
A: 261-byte message (33 frames, last = 5B)
   -> completed=1 parsed=1 cmd=0x1B body_len=257
   Unit 1   | MC_GIVESIGNALVERLAUF | len 257 | confirmed
            | M131 DEBI | 125 samples raw 0..248        <-- happy path OK

B: 64-byte message (an exact multiple of 8)
   -> completed=0                                       <-- NEVER completes

C: next 20-byte message on the same unit
   -> completed=1 raw_len=84 cmd=0x06                   <-- ate B's bytes,
                                                            reported B's command

D: CAN-ID 1000  -> unit=-280 (dropped, correct)
   CAN-ID 1480  -> unit=200  (dropped, correct)
```

Cases B and C are the important ones. A message whose total length is an exact multiple of 8
**never completes** (≈12.5% of all lengths), and the stuck buffer then **swallows the next
message** and reports it with the *previous* message's command and a wrong length. Silent,
plausible-looking garbage — the worst failure mode a reader can have.

The pipeline was sound; the **rules** it was fed were not. Compiled clean at `-Wall -Wextra`.

## 18.2 The rewritten link layer — 20 assertions, all passing

After replacing the heuristic with the real rules from Part 3, the master link layer
(`promos3_master.c` + `test_master.c`) proves:

- the checksum reproduces `0xF6` / `0xF5` / `0xF4` for units 1/2/3 — **the only real protocol bytes
  on hand**;
- `mc_build_request()` emits `08 01 f6`, byte-identical to the log line;
- the **64-byte message that silently corrupted the old transport** (cases B/C above) now
  completes exactly and does not consume the following message;
- both checksum placements work — the tail byte, and the lone `[seq][ck]` frame when
  `expected % 7 == 0`;
- the poll cycle emits `0x16, 0x16, 0x08, 0x08, 0x01` for a 2-channel unit;
- a bad sequence and a bad checksum are **counted, not swallowed**;
- the timeout ladder fires one resend at 300 ms and aborts at 600 ms.

All compiled clean at `-Wall -Wextra`.

## 18.3 A real bug the code found that the reverse-engineering did not

The documented device-error signature `DATA[0] == 0 && DATA[1] == 1` is **identical to a healthy
first data frame whose first payload byte is 1** — which, for command `0x16`, means "one row", the
single most common case there is. As originally written, the reader would have discarded most live
measurement data and counted it as device errors.

The fix constrains it to `f->len == 2` (sequence + status and nothing else), and that constraint is
marked in the source as an assumption to confirm against a real capture.

**This is the argument for writing code early:** static analysis produced a correct-sounding rule
that a running test immediately showed to be unusable.

---

# ═══════════════════════════════════════════════════════════════
# PART 19 — DATA SOURCES & HOW EACH FACT WAS OBTAINED
# ═══════════════════════════════════════════════════════════════

## 19.1 Provenance table

| Fact | Source | Tool | Confidence |
|---|---|---|---|
| Config record layouts | PMD hex (`1974.txt`, `exVL2-*`) ↔ SQLite config DBs | file cross-reference | ✅ |
| Config DB schema | `Provis-10659` / `Provis-10663` | direct read | ✅ |
| Measurement DB schema + amplitude range | `ProvisLog-10663` | direct read | ✅ |
| Scaling = no factor | `ProvisLog` (`Max_Val`/`WP` ≤ 255), `Sensors.Calibration`, the VFAKT stub | DB + Ghidra | ✅ |
| Field meanings | `CDR_DESCRIPT_ENU.ini` / `_DEU.ini` + DB | direct read | ✅ |
| Gateway RX wire format | binary (`Scan4CANmsg`, `CanInterface_pollMessages`) | Ghidra | 🔶 |
| Gateway TX wire format | binary (`CanInterface_writeGatewayRecord`) | Ghidra | ✅ |
| CAN reassembly | binary (`unitBuffer_*`, `UnitComm_*`) | Ghidra | 🔶 |
| `MC_` answer framing (seq, 7B, checksum position) | binary (`UnitComm_assembleAnswer_MC`) | Ghidra | ✅ |
| `MC_` request framing + splitting | binary (`Promos3CanInterface::send`) | Ghidra | ✅ |
| Checksum algorithm | binary (`promos3_checksum` **and** the inline form in `send`) | Ghidra ×2 | ✅ |
| Checksum **value** | `LogFile-260701-T1154.txt` (`08 01 f6`) | runtime log | ✅ byte-verified |
| Request bytes for `0x08` | same log line + the sender's own code | log + Ghidra | ✅ |
| Expected-size table | binary (`Geraet_expectedRecordSize`) + the `GIVEKANAL` call site | Ghidra | ✅ |
| Poll cycle + cadence | binary (`Sende_Kom_MC_GIVESAMMELMERKMALE`, `CanThread_onTimerTick`) + the dedup filter | Ghidra ×2 | ✅ |
| Unit discovery | binary (`CanInterface_searchForNewUnits`, `Router_registerUnit`) + logs | Ghidra + log | ✅ |
| Command dispatch (group, command → handler) | binary (`Command_Dispatch_Switch` + workers) | Ghidra | 🔶/✅ |
| `MC_` command names | `Sende_Kom_*` / `bearbeite_Kom_*` tag strings | string grep | ✅ |
| `MC3_` command registry + field descriptors | binary (`MsgCreator_buildMC3Registry`) | Ghidra | ✅ |
| Active generation = `MC_` | `LogFile.txt` (`Promos3DatenProvis2Geraet`, `MC_GIVEKONFIG`) | runtime log | ✅ |
| Payload bodies | binary (`bearbeite_Kom_*`, `Kanal_addMerkmalData`) | Ghidra | 🔶 |
| Decoder rings | binary (`initStatusTables`) + `PROVISsettings.ini` | Ghidra + config | 🔶/✅ |
| Model string | binary (`MonitorTypes_resolveName`) + `[MonitorTypes]` | Ghidra + config | ✅ |
| Alarm slot names | binary (`GlobaleDaten_loadIniTables`) + `[AlarmNames]` | Ghidra + config | ✅ |
| Transport config (ports, `PCANGateway`) | `PROVISsettings.ini` | direct read | ✅ |
| Application data model + DB read path | binary (Qt teardown → SQL layer, German mutex tags) | Ghidra | 🔶/✅ |
| Reader failure modes | compiling and running the reader against synthetic datagrams | test | ✅ |

**These files exist because PROVIS3 produces them itself** — SQLite working databases, PMD `.txt`
exports, ErrorManager logs. They were collected by copying, not by capture. The only data the app
does **not** save is the live stream, which is why the transport needed Ghidra.

## 19.2 Files used

```
SQLite config:       Provis-10659 (-250127_1838), Provis-10663
SQLite measurement:  ProvisLog-10663
PMD hex exports:     1974.txt, exVL2-1.txt, exVL2-2.txt
INI:                 PROVISsettings.ini, PROVISsecurity.ini (+ OLD-),
                     NCaccess.ini (+ OLD-, ALT2-), CDR_DESCRIPT_ENU.ini
Runtime logs:        LogFile.txt,
                     LogFile-260701-T0545.txt, -T0749.txt, -T0952.txt, -T1154.txt
String dump:         mazak_strings.txt
Reader source:       main.c, promos3_{transport,decode,proto,state,config}.c/.h,
                     promos3.h, span.h, xlsx.c/.h, run_commands.txt
```

**Ghidra decompiles referenced across the investigation** (not exhaustive — see Part 13 for the
full naming table):

```
Command_Dispatch_Switch (004125d0) · FUN_00436470 · FUN_0042db50 · FUN_004152c0 ·
FUN_00409ca0 · FUN_0047fde0 · FUN_004dc3e0 · FUN_0040af30 · FUN_0040c5e0 · FUN_004acf40 ·
FUN_0040c540 · FUN_004b9150 · FUN_0040c450 · FUN_004b6580 ·
vftable of Promos3KommandoVerteilerThread ·
FUN_0042b1f0 · FUN_00508a80 · FUN_00411960 · FUN_004c1090 · FUN_0042ec10 · FUN_00404dc0 ·
FUN_00404790 · FUN_005e9930 · FUN_00556f50 · FUN_004fbae0 · FUN_006dcab0 · FUN_0041c090 ·
FUN_00684160 · FUN_00685940 · FUN_004425c0 · FUN_00442650 · FUN_004c5840 · FUN_00686430 ·
FUN_00683e00 · FUN_004d0320 · FUN_004d1810 · 0x0042d190 · FUN_00506d10 · FUN_0042eed0 ·
FUN_00506220 · FUN_00504290 · FUN_004d1310 · FUN_005073f0 · FUN_00507360 · FUN_0046a460 ·
FUN_004c65d0 · FUN_004cd650 · FUN_004ce000 · FUN_004d1de0 · FUN_004d23d0 · FUN_004c7000 ·
FUN_0040a620 · FUN_004ba490 · FUN_004abb20 · FUN_004341f0 · FUN_005206c0 · FUN_005179c0 ·
FUN_00426100 · FUN_006da550 · FUN_004be820 · FUN_004a7ec0 · FUN_00715220 · FUN_00421e10
```

## 19.3 Method notes

- **No Wireshark, no packet capture, no PEAK hardware, and no admin rights** were used at any
  point. Every wire fact came from the binary, from the application's own logs, or from its own
  exported files.
- **Tag strings are the backbone of the naming.** The application constructs QString tags for
  mutex lockers, error-manager entries and class-qualified labels; a function that builds the
  string `"Promos3CanInterface::receive"` is telling you its own name. Names derived that way are
  marked **[tag-proven]** in Part 13 and treated as near-symbol quality.
- **German method names are ground truth**, not noise: `FuegeAlarmsHinzu`, `UeberpruefeTabelle`,
  `Zeilenanzahl`, `FindeSourcesFromWerkzeug`, `Vorverarbeitung_Kom`, `Versionsfehler`.
- **Cross-confirmation was sought wherever possible.** The checksum was recovered twice from
  independent code sites and then matched to a log line; the `0x16` stride was derived twice from
  different functions; the CAN-ID base was confirmed by the settings dialog; the `MC3_` command
  names come from the binary's own registry rather than from the dispatch switch.
- **Every source was re-read at each stage.** The gap register (Part 16) was produced by
  re-reading the entire corpus — reports, appendices, reader source, INI, all five runtime logs,
  the PMD exports and the string dump — and then *compiling and running the reader* against
  synthetic datagrams to see which failures were real rather than theoretical.
- **The runtime logs had not been mined for wire bytes** in the early passes. They turned out to
  contain real request frames (`waitingForData` prints the frame the app sent when an answer times
  out), which is what made byte-level verification possible at all.

## 19.4 Consistency with prior independent analysis

Independent analysis notes (`eski-provis-analizi.md`, ADRs 0001–0005) were cross-checked and found
**consistent** with these findings: units 10659/10663, GType 0x44, the transport configuration,
the two command generations, the record structures and the DB schema all match.

Those notes were slightly conservative on capture — they predate the Ghidra recovery, and a
Wireshark capture is now entirely optional — and they correctly flagged the model-name mapping as
needing confirmation (now resolved, §8.6). **ADR-0004 (read-only observer MVP)** aligns with why
only the receive/decode path was needed initially; note, however, that §17.1 now argues the
observer role is *harder* than the master role for this protocol generation, which is a genuine
revision of that decision's premises.

---

# ═══════════════════════════════════════════════════════════════
# PART 20 — SUPERSESSION LOG
# ═══════════════════════════════════════════════════════════════

Every claim in the seven source documents that a later finding **overturned, narrowed or
reconciled**. If you are holding an older copy of any of those documents, this is the list of
statements in it to stop believing.

> §0.6 is the one-line-per-item summary of this Part (entries **C1–C24**). This Part is the long
> form: the same reversals with the evidence and the reasoning, plus reconciliations that did not
> fit a table row. Where a `C`-number and a `20.x` number cover the same item they do not conflict
> — they are the short and long descriptions of one finding.

Entries marked **CORRECTION** reverse an earlier claim. Entries marked **RECONCILIATION** merge two
descriptions that were both partly right. Entries marked **RESOLUTION** close something that was
previously recorded as open or uncertain.

## 20.0 Index

| # | Subject | Type |
|---|---|---|
| 20.1 | The `[group][command][length]` message header | CORRECTION |
| 20.2 | "Exact wire byte-offsets" as the headline open item | RESOLUTION |
| 20.3 | Model string for (GType 0x44, GSubType 5) | RESOLUTION |
| 20.4 | Three CAN-ID bases | CORRECTION |
| 20.5 | "A request is a single CAN frame" | CORRECTION |
| 20.6 | `Geraet+0x4BC` = station count | CORRECTION |
| 20.7 | Feature names `SPINDEL / X / Y / Z` and masks `0x81…` | CORRECTION |
| 20.8 | PMD loaders would reveal the multi-frame split | CORRECTION |
| 20.9 | `FUN_005073f0` is the frame splitter | CORRECTION |
| 20.10 | `FUN_005018f0` is the CAN interface | CORRECTION |
| 20.11 | `Paket+0x20` is the wire buffer; `+0x30` is "aux" | CORRECTION |
| 20.12 | `MC3_` `0x11` = `MC3_SENSOR_VFAKT` | CORRECTION |
| 20.13 | `MC3_MERKMAL_INFO` / `MC3_GERAETEREC` vs registry names | RECONCILIATION |
| 20.14 | The reassembly completion rule | CORRECTION |
| 20.15 | The checksum "untested hint" | RESOLUTION |
| 20.16 | "There is no group byte on the wire" (inferred) | RESOLUTION |
| 20.17 | G4 — the capture-strategy assessment | RECONCILIATION |
| 20.18 | `Promos3CanInterface` in the Eth vtable hierarchy | CORRECTION |
| 20.19 | `0x01 MC_GIVESTATUS` as a first probe | CORRECTION |
| 20.20 | The `0x16` "+4 stride variant" | RESOLUTION |
| 20.21 | The "0–300 display axis" as a scaled amplitude | CORRECTION |
| 20.22 | The role of `LogCANMessage=1` | RECONCILIATION |
| 20.23 | The device-error signature | CORRECTION |
| 20.24 | The alarm body layout's applicability | RECONCILIATION |
| 20.25 | `unitActiveTimeout=900` as an independent setting | RESOLUTION |
| 20.26 | Which open item Appendix B.3 closed | RECONCILIATION |
| 20.27 | Expected answer sizes for `0x01`, `0x12`, `0x1B` | CORRECTION |
| 20.28 | Completion-percentage headlines | RECONCILIATION |
| 20.29 | `RouterObj` type 1 = "Provis2/`MC_` generation" | CORRECTION |
| 20.30 | Where `promos3_sniff.c` stands | RECONCILIATION |

---

## 20.1 The `[group][command][length]` message header — **CORRECTION**

**Was** (main report v2, §2.4 and Part 13, and the reader's `parse_message_header()`): the
reassembled message begins with a header carrying group, command and length, whose exact wire
offsets were the one remaining unknown.

**Is:** for **`MC_` (this box) there is no header at all.** `group` and `command` are copied from
the outstanding request before any answer byte is read; the answer payload is pure record bytes,
and its length comes from the expected-size table rather than the wire (§3.1).

The `[group][command][length]` model turned out to be a *nearly* correct description of **`MC3_`**
— except that even there the group is not on the wire, it is hardcoded to 2 in the constructor
call. `MC3_` messages really are `[command][length][body][checksum]` with the body starting at
offset 2 (§4.2).

**Action:** delete `parse_message_header()` rather than fixing it. `promos3_msg_t` should carry
`group`/`command` as **attributed** fields with a `bool attributed` flag.

## 20.2 "Exact wire byte-offsets" as the headline open item — **RESOLUTION**

**Was** (v2 §0.5 item 1, Part 13 item 1): the single remaining wire unknown, to be closed with
`LogCANMessage=1` or one UDP capture.

**Is:** closed **by deletion**, not by measurement — those fields do not exist on the `MC_` wire
(§20.1). The capture is still useful, but for validation rather than discovery (§16.5).

## 20.3 Model string for (GType 0x44, GSubType 5) — **RESOLUTION**

**Was** (v2 §0.5 item 2 and §6.6): "cosmetic; index base 0- vs 1-based unpinned — either
`MSL5081-16` (1-based) or `MSL5082-16` (0-based)." An intermediate document recorded this as "50%
closed".

**Is:** `MonitorTypes_resolveName` (`FUN_004abb20`) computes `idx = GSubType - 1`. **The index is
1-based**, so GSubType 5 → list position 4 → **`MSL5081-16`** ✅ (§8.6).

## 20.4 Three CAN-ID bases — **CORRECTION**

**Was** (session handoff, §5.3 and §11 item 7): "There are three CAN-ID bases (`0x500`, `0x580`,
`0x600`), not one" — flagged 🔴 IMPORTANT, read as CANopen-shaped direction discrimination, and
described as the discriminator that gap G4 needed. The reader was said to be silently discarding
an entire direction.

**Is:** **one** base. `Promos3CanInterface::send` computes `CAN-ID = *(this+0x48) + unit`, and
`this+0x48` is `BaseCanIDTransfer = 1280`. Transmit and receive use the same base, confirmed
independently by the settings dialog exposing a single "Base Tx" field with First/Last unit as
offsets from it (§2.5).

`0x580` and `0x600` are stored in the constructor but are **not transmit bases**; their purpose is
unknown. **G4 closed as a consequence.**

## 20.5 "A request is a single CAN frame" — **CORRECTION**

**Was** (gap register §15.0(a)): from the two logged `waitingForData` frames — "Frame length is
variable, 3–8 bytes — a request is a *single* CAN frame."

**Is:** requests are split exactly like answers. The logged `0x0c, 0x01, 0x61, 0xff, …` is
`MC_SETZYKLUS` carrying a **170-byte cycle record**, which cannot fit in one frame. The log line
looks short only because the dumper (`Paket_appendDataHex`) **caps its output at 8 bytes**
(§3.3.1).

Short *read* requests (`0x08`, `0x0e`, `0x1b`, …) genuinely do fit in one frame, which is why the
first reading was plausible.

## 20.6 `Geraet+0x4BC` = station count — **CORRECTION**

**Was** (session handoff, and the first draft of the reader): `Geraet+0x4BC` is a **station**
count.

**Is:** it is the **channel** count — it is the loop bound in `Sende_Kom_MC_GIVESAMMELMERKMALE`
over channels. Behaviourally identical on this box (1 of each), but the label was wrong and would
mislead on a multi-channel unit (§6.3, §9.1).

## 20.7 Feature names `SPINDEL / X AXIS / Y AXIS / Z AXIS` — **CORRECTION**

**Was** (report v1): the `SKanalRec` feature block contains `SPINDEL / X AXIS / Y AXIS / Z AXIS`
with masks `0x81 / 0x82 / 0x84 / 0x88`.

**Is:** **that was a different machine's example.** Feature names and masks are **per-install and
operator-assigned**. This box has `VIBRATION / M131 DEBI / M131BASINC / M08 DEBI` with masks
`0x01 / 0x02 / 0x04 / 0x08`. The **low nibble** is the feature-select bit and the **high `0x80` bit
is a separate flag** — match on `mask & 0x0F`, never on `mask == 0x81` (§9.2).

The same trap applies to **alarm slot names**: slot 5 on this box is `Coolant`, not the built-in
default `Contact` (§8.7).

## 20.8 The PMD loaders would reveal the multi-frame request split — **CORRECTION**

**Was** (predicted during the session): `Lade_Alles_aus_PMD_File` (`FUN_005206c0`) and
`Lade_Kanal_aus_PMD_File` (`FUN_005179c0`) were expected to show how a long request is split.

**Is:** they **send nothing over CAN**. Both are SQL→memory configuration loaders with no protocol
content (§9.6). The splitter is `Promos3CanInterface::send` (`FUN_00506220`).

## 20.9 `FUN_005073f0` is the frame splitter — **CORRECTION**

**Was** (session handoff, §13.1): `FUN_005073f0` named `CanInterface_setForSending` and flagged as
the **next target**, expected to contain the checksum fill, the frame split and the CAN-ID base
choice.

**Is:** `FUN_005073f0` is **`Promos3CanThread::sendCommandToUnit`** — a send-queue enqueue with
de-duplication (§3.9). The frame splitter, checksum writer and CAN-ID selector is
**`FUN_00506220`** (`Promos3CanInterface::send`, §3.4).

The elimination reasoning that located it is preserved in §3.8 because it also rules out four
other plausible-looking sites.

## 20.10 `FUN_005018f0` is the CAN interface — **CORRECTION**

**Was:** labelled as a CAN-interface function.

**Is:** `Promos2EthInterface_setForSending` — an **Ethernet** hierarchy function. Corrected
mid-session (§13.9).

## 20.11 `Paket+0x20` is the wire buffer; `+0x30` is "aux" — **CORRECTION**

**Was** (Part 16 §16.5 object layout table):

| field | claimed |
|---|---|
| `Paket+0x20` | "QByteArray — the message bytes" |
| `Paket+0x30` | "aux" |

**Is:**

| field | actual |
|---|---|
| `Paket+0x20` | **aux/context `QVector<u8>`**, written by `Paket_setByteArray`, read by `stream_peekU16`. **Never sent on the wire.** |
| `Paket+0x30` | **station / device index** (`paket[0xc] = station`) |
| — | the **wire bytes** live elsewhere and are reached via `stream_peekCurrent` |

This matters more than a label fix: `+0x20` is where the trace sender packs
`{station, featureKey, p3, p4, mode}`, and the answer assembler copies it from request into
answer. **That vector is how `bearbeite_Kom_27` knows which feature it asked for**, and it is
invisible to a passive listener (§15.1).

## 20.12 `MC3_` `0x11` = `MC3_SENSOR_VFAKT` — **CORRECTION**

**Was** (v2 §3.2): command `0x11` labelled `MC3_SENSOR_VFAKT — STUB`.

**Is:** the binary's own registry puts **`MC3_SENSOR_VFAKT` at `0x0b`** and **`MC3_LAST_SIGNAL` at
`0x11`** (§5.3.1). The handler at dispatch index `0x11` may still be a shared/stub worker, and the
worker `FUN_004acf40` is indeed `return p != 0` — so **the "no runtime scaling" conclusion is
unaffected**. Only the code↔name mapping was wrong.

## 20.13 `MC3_MERKMAL_INFO` / `MC3_GERAETEREC` — **RECONCILIATION**

The handler-side German labels `MC3_MERKMAL_INFO` (0x05) and `MC3_GERAETEREC` (0x06) and the
registry's English names `MC3_FEATURE_INFO` and `MC3_DEVICEREC` are **the same commands**
(Merkmal = feature, Gerät = device). Both naming sets appear in the binary; the registry is
authoritative (§5.3).

## 20.14 The reassembly completion rule — **CORRECTION**

**Was** (v2 §2.4 / §8.2): "a length field in the buffer header governs completion; complete when
received ≥ expected." In the reader this became *"a frame shorter than 8 bytes ends the message"*
because `reasm_expected_len()` returned 0.

**Is provably wrong** — and it was proven by running it (§18.1): a message whose total length is a
multiple of 8 **never completes**, and the stuck buffer then **swallows the next message** and
reports it under the previous message's command.

**The real rule** (§3.5): `expected` comes from `Geraet_expectedRecordSize(cmd)` stamped into
`Paket+0x14` at send time; frames carry a sequence byte plus **7** payload bytes; accumulate until
`accumulated == expected`; then validate the checksum, rolling frames back and retrying on
mismatch.

## 20.15 The checksum "untested hint" — **RESOLUTION**

**Was** (gap register §15.5): "*Weak hint:* in the 3-byte request `08 01 F6`, `0xF6 = ~(0x08+0x01)`
— a one's-complement byte sum fits that one sample but **not** the 8-byte sample, so treat it as
untested, not as a finding."

**Is:** the hint was **correct**, and the reason it did not fit the 8-byte sample is that the
8-byte sample was a *truncated* multi-frame request (§20.5), not a complete one. The full algorithm
is seeded with the unit id and spans both directions (§3.4). Verified against the same log line and
against a second, independent code site.

## 20.16 "There is no group byte on the wire" — **RESOLUTION**

**Was** (gap register §15.0(a)): ⚠️ INFERRED from the logged request frames — "there is no `group`
byte on the wire; `group` at msg+0x00 is set by the parser from the unit's registered generation."

**Is:** ✅ confirmed in code (§3.1). The inference was right, and stronger than stated: neither
group *nor* command is on the `MC_` wire.

## 20.17 G4 — the capture-strategy assessment — **RECONCILIATION**

This gap's assessment moved three times, and all three readings are partly true. The final
position:

| Stage | Assessment | Status |
|---|---|---|
| Gap register | "0%, blocker — you cannot receive a unicast stream twice" | **true for passive mode** |
| `MC_` protocol part | "0% *and now mandatory* — a one-directional capture is worthless, so it got *worse*" | **true for passive mode** |
| Session handoff | "35% — three ID bases found, that's the direction discriminator" | **false premise** (§20.4) |
| Session report | "100% — one base; master mode needs no capture" | **true for master mode** |

**Reconciled:** for a **master-mode** reader, G4 does not exist — it sends its own requests and
receives its own answers, no capture infrastructure required. For a **passive** reader, the
original objection stands in full: unicast delivery cannot be duplicated on the same host, a
both-direction port mirror is required, and the reader additionally needs a source-address filter
and a request/answer discriminator or it will feed the app's own requests into its reassembly
buffers and corrupt them (§17.1). This is the strongest argument for choosing master mode.

## 20.18 `Promos3CanInterface` in the Eth vtable hierarchy — **CORRECTION**

**Was:** assumed to follow the same vtable index pattern as the Ethernet interfaces
(index 12 = SetForSending, 14 = send, …).

**Is:** it is a **plain QObject**. Its vtable has only 11 entries, all boilerplate, with no
index-12/14 pattern; its real entry points are metacall slots 0–3 (§15.5).

## 20.19 `0x01 MC_GIVESTATUS` as a first probe — **CORRECTION**

**Was:** implied by the discovery sequence — `MC_GIVESTATUS` is what the app itself sends first, so
it looks like the natural first probe.

**Is:** `0x01` **never calls `Paket_setRecvSize`**, so its expected answer size comes from
`createPaketForCommand` defaults and is not known. It is therefore a **poor first probe**. Use
`0x08 MC_GIVEPLCVALUES`, whose exact request bytes are verified against the log (§17.2).

## 20.20 The `0x16` "+4 stride variant" — **RESOLUTION**

**Was:** `stride = featureCount*2 + 2`, "or +4 when `this+0xC0 == 1`" — the condition unexplained.

**Is:** the `+4` case is the **`GeraetTyp == 'H'` branch**: `recvSize` and `recordSize` are both
`featureCount*2 + 2`, and **both** gain `+2` when the device type is `'H'` (0x48). This box is
`'D'` (0x44), so **stride = 10** for 4 features (§3.7, §6.2).

## 20.21 The "0–300 display axis" as a scaled amplitude — **CORRECTION**

**Was** (report v1): the 0–300 display axis implied some amplitude scaling.

**Is:** amplitude is raw 0–255 with **no scaling factor**; the 0–300 axis is display headroom. The
0..301 range that prompted the confusion is `Trend.Work_Val`, a **cycle position / work-window**
quantity, not an amplitude (Part 7).

## 20.22 The role of `LogCANMessage=1` — **RECONCILIATION**

**Was:** "the one action that unblocks the most" — it was going to close G1, G2, G5 and part of G4
in a single 60-second run.

**Is:** all of those closed by static analysis instead. The capture's role is now **validation, not
discovery** (§16.5): confirm the framing against real bytes, resolve `channelKey`, check a unit-2
request, and verify RX/TX record symmetry. Still worth doing, no longer the critical path.

## 20.23 The device-error signature — **CORRECTION**

**Was:** "a frame with `DATA[0]==0 && DATA[1]==1` is a device error answer."

**Is:** that signature is **ambiguous** — it is identical to a healthy first data frame whose first
payload byte is `1`, which for command `0x16` means "one row", the most common case there is. It
must additionally require `LEN == 2` (§3.2, §18.3). ⚠️ The `LEN == 2` constraint is itself
inference and needs confirming against a real capture.

Found by running the code, not by reading it.

## 20.24 The alarm body layout's applicability — **RECONCILIATION**

The alarm layout in §6.4 is **`MC3_`-derived**. Three of its assumptions were later ✅ confirmed for
`MC3_` — the subcommand at body offset 0, `DATA[2]==1` meaning "alarm data", and `0xFFFF` meaning
"give me everything" (§4.3).

**For the `MC_` box it remains PROVISIONAL.** The piece that *is* confirmed for both is that
`bearbeite_Kom_15` reads `payload[0]` as the station. A faithful reader will hexdump group-1
alarms rather than present them as decoded alarms until an `MC_` alarm body is observed (G7).

## 20.25 `unitActiveTimeout=900` as an independent setting — **RESOLUTION**

**Is:** it is **derived**, not independent. `DAT_00a17914 = unitAnswerTimeout × 3 = 900 ms` is the
unit-rescan gate, and the INI value simply mirrors it (§3.9). Changing `unitAnswerTimeout` moves it.

Relatedly: `[CAN] unitAnswerTimeout = 300` and the `[Ethernet]`-side `unitAnswerTimeout` (default
500, floored to 500) are **different settings for different transports** and must not be conflated
(§12.4). The same applies to `[Comm] MaxResend = 1` (CAN) versus the `[Ethernet]` `MaxResend`
default of 5.

## 20.26 Which open item Appendix B.3 closed — **RECONCILIATION**

**Was** (Appendix B, header and §B.3): "closes the Part 13 open item".

**Is:** it closes the **group-2 (`MC3_`) field-layout** question, by supplying the per-command
field-descriptor table (§5.5). It did **not** close the group-1 wire-offset item — that one closed
later and differently, by the discovery that no `MC_` header exists (§20.1). Both are now closed;
the credit just belongs to two different findings.

⚠️ Note that the field-descriptor attributes `A` and `B` are still interpreted rather than proven
(size vs type); binding them needs one raw frame.

## 20.27 Expected answer sizes for `0x01`, `0x12`, `0x1B` — **CORRECTION**

**Was:** these sizes were carried in the reader as if they were table-derived.

**Is:** they are **guesses** (§16.2, D3). `0x12 GIVEALARM` was mapped onto the table's `0x11` entry,
which is `ALARMGESEHEN` — probably wrong. `0x1B`'s 257 comes from a *synthetic* test, not from real
bytes. `0x01` has no table entry at all. The table is authoritative only for `0x02` (14) and `0x0e`
(144).

## 20.28 Completion-percentage headlines — **RECONCILIATION**

The headline numbers moved as follows. They are recorded here so that a percentage quoted from an
older document can be placed correctly:

| Document | Protocol knowledge | Trustworthy live reader |
|---|---|---|
| Gap register | ~78% | ~45% |
| `MC_` protocol part | ~85% (G1/G2/G5 closed at spec level) | ~45% (no code written) |
| Session handoff | ~92% | ~45% |
| Session report | ~99% | ~75% (link layer written + tested) |
| **This report** | **≈99%** | **≈75%** |

The gap register's headline — *"the distance between those two numbers is almost entirely G1, G2,
G3, G4, and three of them were previously recorded as non-blocking; they are blocking"* — was
correct at the time and **all four are now closed**. What remains between 75% and 100% on the
reader line is engineering plus two measurements from a live device, not reverse engineering.

## 20.29 `RouterObj` type 1 = "Provis2/`MC_` generation" — **CORRECTION**

**Was** (`MC_` protocol part, §16.10, in the annotated sender skeleton):

```c
Promos3RouterObj_ctor(tag, "Promos3DatenProvis2Geraet::Sende_Kom_…", 1);   /* type 1 = Provis2/MC_ */
```

**Is:** `Promos3RouterObj` is `{int type; QString name}` and its `type` field selects the
**transport**, not the generation: **1 = source tag, 2 = Ethernet, 3 = CAN**. The `type 1` objects
constructed in every `Sende_Kom_*` are source tags stored at `Paket+0x0c`; they are not routing
keys and say nothing about the protocol generation (§1.4, §15.6). Generation lives in `Paket+0x00`
(group) and in `unit+0x0c` (`getTargetType`).

## 20.30 Where `promos3_sniff.c` stands — **RECONCILIATION**

**Was** (report v2, Part 12): the pcap variant "requires libpcap + admin; **superseded** by the
listener."

**Is:** superseded *for the originally intended use* (binding :1789 on the PROVIS3 host). But if
the **passive** deployment option is chosen, a both-direction port mirror read promiscuously is the
only viable route, and that needs pcap again — so the retired tool **may need to come back**
(§17.1, §17.6). Under the recommended **master** option it stays retired.

## 20.31 A dropped pointer, recorded for completeness

The session handoff's "read next" list named `FUN_005073f0` "and whatever function contains
`0x005090f5`" as the two places the transmit tail might live. Neither was the answer: the transmit
tail is `FUN_00506220` (§20.9). The address `0x005090f5` was never resolved and is no longer
needed; it is recorded here only so that a reader of the older document does not go looking for a
finding that does not exist.

---

# ═══════════════════════════════════════════════════════════════
# PART 21 — GLOSSARY
# ═══════════════════════════════════════════════════════════════

## 21.1 German terms used by the binary

| Term | Meaning |
|---|---|
| **Kom / Kommando** | command (message type) |
| **Kommandokennung** | command identifier — the `+0x28` command field |
| **bearbeite** | process / parse (device → app) |
| **Sende** | send (app → device) |
| **Geraet** | device; **GType / GSubType** — device type codes |
| **Merkmal** | feature |
| **Kanal** | channel |
| **Zyklus / Zyk** | cycle |
| **Grenz** | limit |
| **Konfig** | configuration |
| **Signalverlauf** | signal trace (amplitude series) |
| **Sammelmerkmale** | "collected features" — the live measurement block (cmd `0x16`) |
| **Verstärkungsfaktor (VFAKT)** | gain / scaling factor (stubbed for this generation) |
| **Verbindung** | (DB) connection / connection-parameter struct (10 QStrings + int) |
| **Werkzeug** | tool; **NCTool** — the NC-side tool table (name → ID) |
| **fuege … hinzu** | add / append (here: insert an alarm row) |
| **Untersuche … auf Fehler** | examine … for errors (the packet validators) |
| **Ueberpruefe Tabelle** | check table (does it exist) |
| **Zeilenanzahl** | row count |
| **Finde … aus …** | find … from … (the ID lookup queries) |
| **Vorverarbeitung** | pre-processing (the mutex taken in `resolveTarget`) |
| **Versionsfehler** | version error (unknown command in the size table) |
| **Lade … aus …** | load … from … (the PMD loaders) |
| **Einrichten** | setup / commissioning |
| **Muster** | pattern |
| **Anzeige (Anz)** | display (`SETANZMODE` = set display mode) |

## 21.2 Turkish terms (operator-assigned labels on this machine)

| Term | Meaning |
|---|---|
| **debi** | flow rate — as in `M131 DEBI`, `M08 DEBI` |
| **basınç** | pressure — as in `M131BASINC` |

## 21.3 Protocol and transport terms

| Term | Meaning |
|---|---|
| **`MC_` (Provis2)** | the legacy command generation — **this box**. Dispatch groups 0 and 1 |
| **`MC3_` (Promos3)** | the modern command generation. Dispatch group 2 |
| **group** | the protocol family selector at message `+0x00`: 0 = handshake, 1 = `MC_`, 2 = `MC3_`. **Inherited from the request, never on the `MC_` wire** |
| **getTargetType** | a unit's generation (`unit+0x0c`): 1 = `MC_`, 2 = `MC3_` |
| **station** | the device/traceMap index carried as request byte 1 — **not** the channel |
| **TPCANMsg** | the PEAK PCAN standard CAN message struct (14 bytes): `{u32 ID; u8 MSGTYPE; u8 LEN; u8 DATA[8]}`, LEN @+5, DATA @+6 |
| **BaseCanIDTransfer (1280 / 0x500)** | the CAN-ID base; `unit = CAN_ID − base`. There is exactly one |
| **PCANGateway** | the flag selecting the CAN-over-UDP gateway over a local PEAK card |
| **gateway record** | the fixed 36-byte UDP-borne wrapper around one CAN frame |
| **seq** | the sequence byte at `DATA[0]` of every `MC_` frame; starts at 0, +1 per frame |
| **checksum-only frame** | a 2-byte `[seq][checksum]` frame, sent when `expectedSize % 7 == 0` |
| **expectedSize / recvSize** | the expected **answer** byte count, from `Geraet_expectedRecordSize(cmd)`, stamped into `Paket+0x14` at send time |
| **aux context (`Paket+0x20`)** | an in-process `QVector<u8>` copied request→answer; carries `{station, featureKey, p3, p4, mode}`. **Never on the wire** |
| **enAll / enAbort / enKom** | packet/return status enum values in the CAN receive branch: complete / abort / command-level |
| **priority 2** | a Paket flag that puts the request at the front of the send queue |
| **`0xFB` / `0xFD`** | reserved feature *selectors* in the trace request (they choose modes 1 and 2), not feature indices |
| **`0xFFFF`** | "give me everything" — the all-entries request id for alarms and events |
| **QSQLITE / QODBC** | Qt SQL driver names, which select the dialect token set |
| **LastUsedPort** | the live UDP port persisted per connection (`Interface+0x1e`); 1793 on the reference box |
| **NC / NTIF** | the Mazak numerical-control channel and its DLL API (`NTIFDLL.dll`, TCP 57400) |
| **PMD** | the device's exported parameter/configuration file (hex text, e.g. `1974.txt`) |
| **CIAB** | the segmented-transfer command family (`MC_` cmd `0x30`); used for downloads and large records |

## 21.4 Sensors and hardware

| Term | Meaning |
|---|---|
| **PROCUR-S / -I / -B** | Prometec sensor types (`0x80` / `0x81` / `0x82`); this box has 4× PROCUR-S |
| **MI sensor** | measurement-input sensor (`MiSensType`) |
| **GType 0x44** | the MSL-16 device family; resolved model here = `MSL5081-16` |
| **GeraetTyp as ASCII** | `0x44 = 'D'`, `0x48 = 'H'` — the binary compares it as a character |
| **Gain** (`Cycle_Sensors.Gain`, 0..126) | the sensor-side **hardware** amplifier setting; **not** applied at display time |
| **ReduzLim** | a device record field, `0x19D4` = 6612 on this box |
| **SampleDiv** | sample divider, 1 on this box |
| **CDRLim** | channel record limit array, `0xAA` (170) ×4 on this box |

## 21.5 Confidence and code-quality markers used by the reader

| Marker | Meaning |
|---|---|
| `CONF_UNKNOWN` | no name, no decoder → print id + hexdump |
| `CONF_NAMED` | known name, no decoder → print name + hexdump |
| `CONF_PROVISIONAL` | a decoder exists but its layout is unconfirmed → print name + hexdump |
| `CONF_CONFIRMED` | decoder **and** layout confirmed → print decoded values |

This gating is the reader's honesty mechanism: it never prints a "meaning" whose byte layout is
unproven. It is the reason the early header mistake produced loud `[UNPARSED HEADER]` output rather
than silent lies, and it should be preserved through every rewrite.

---

*End of consolidated report (v3).*

*This document supersedes: `analysis_jul_28_1_0_0.md` (v2), `analysis_appendix_datamodel.md`
(Appendix A), `analysis_appendix_B.md` (Appendix B), `analysis_part15_gap_register.md`,
`analysis_part16_mc_answer_protocol.md`, `analysis_part17_session_handoff.md`, and
`analysis_part18_session_report.md`.*
