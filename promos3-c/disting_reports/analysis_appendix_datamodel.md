# PROVIS3 — Appendix A: Application Data Model & Database Read Path

**Scope of this appendix.** The main report (v2) recovers the *receive path* — how bytes
travel device → UDP gateway → CAN reassembly → command dispatch → payload decode. This
appendix documents the complementary *application-internal* layer: the in-memory domain
object that live and historical measurements are loaded into, and the SQLite/ODBC read path
that reconstructs a workpiece's full history from disk. It was produced by Ghidra static
analysis, working outward from Qt container teardown code into the DB layer, using the
application's own German method-name strings (mutex-locker labels, log messages) as
ground truth for naming.

**Relationship to the main report.** Where the main report ends at "decode body → emit
signals → GUI / SQLite," this appendix picks up the SQLite side: the schema in Part 10 of
the main report is the *storage*; the functions below are the *reader* that turns those
tables back into a populated record for the statistics / event-log / print UI.

Confidence markers follow the main report: ✅ VERIFIED (string/log-confirmed), 🔶 GHIDRA
(disassembly-derived, reliable), ⚠️ INFERRED.

---

## A.1 Executive summary

- The central domain object is **`Promos3DataRecord`** (0xF8 = 248 bytes) 🔶 — one instance
  per workpiece cycle. It aggregates the cycle header, a timestamp→sample index, the raw
  multi-channel signal traces, and alarm/feature sub-records. Its field layout was recovered
  from its copy-constructor and destructor and is given in §A.3.
- The **read path is fully mapped end-to-end** 🔶/✅:
  `buildWorkpieceRecords` → per workpiece `GetWorkPieceData` → `{ GetWorkPieceCycle,
  GetSignalData, alarms }` → one populated `Promos3DataRecord` → UI.
- Every SQL entry point carries a German mutex-locker string that names it directly:
  `OpenDatabase`, `CloseDatabase`, `UeberpruefeTabelle` (check table), `Zeilenanzahl`
  (row count), `GetAlarmsList`, `FindeAlleIDsFromSource`, `GetWorkPiecesFomProgRef`,
  `GetWorkPieceCycle`, `GetSignalData`, `GetWorkPieceData`. ✅
- The **SQL database manager** (`Promos3SqlDatenbankManager`) is a singleton supporting both
  **QSQLITE** and **QODBC** (SQL Server) back-ends, with its own logging worker thread
  (`Promos3ProtokollThread`) for delayed/batched writes. 🔶
- This layer is consistent with the measurement DB schema already verified in the main
  report (Part 10): `Log`, `Alarms`, `Trend_*`, `WP_*` are exactly the tables these readers
  target.

---

## A.2 The central domain object — `Promos3DataRecord`

One `Promos3DataRecord` represents a single monitored cycle/workpiece run. It is heap
allocated (`operator_new(0xF8)`), deep-copied through a copy-constructor (`FUN_00560340`),
and destroyed through `FUN_0055fbc0`. A global instance counter (`g_dataRecordCount`,
`_DAT_00a1cd04`) tracks live instances. Records nest: several fields hold
`QList<Promos3DataRecord*>` of sub-records, deep-copied recursively.

### A.2.1 Verified field map (0xF8 bytes) 🔶

| Offset | Type | Meaning |
|---|---|---|
| +0x04..+0x24 | int ×9 | scalar header fields (flags/counts) |
| +0x18 | int | **ProgRef** (program reference) |
| +0x1C | int | **CycleNr** |
| +0x28 | QString | cycle label / workpiece name (see `formatCycleId`, §A.4) |
| +0x2C | QString | second label string |
| +0x38 | int | **start row ID** (into signal table) |
| +0x3C | int | stop / count flag |
| +0x40 | int | type-2 ID (from cycle row type 2) |
| +0x44 | int | type-3 ID (from cycle row type 3) |
| +0x4D.. (stride 0xC ×4) | struct[4] | **channel descriptor table**; low nibble @+0 = active-feature mask |
| +0x54 | int | extra scalar |
| +0x74 | QByteArray | raw payload blob |
| +0x7C | QDateTime | cycle timestamp |
| +0x80..+0x98 | QVector<short> ×N | (see note) fixed-size sample vectors |
| +0xA0 | QMap<int, QVector<short>*> | **signal channels** — the raw sample traces |
| +0xA4, +0xBC, +0xC0 | QList<int64*> | boxed 64-bit accumulators (per-group sums) |
| +0xA8 | QMap<int, {sub-record}> | typed sub-entries |
| +0xAC | ptr | parent/context reference (copied by value, not owned) |
| +0xB4, +0x90, +0x94 | QMap<int,int> | cycle/index maps |
| +0xB8 | QMap<QDateTime,int> | **timestamp → sample index** |
| +0xCC, +0xD8, +0xF0 | QStringList | label/category lists |
| +0xE4, +0xE8, +0xEC, +0xF4, +0xC4, +0x9C | QList<Record*> / QList<QVector*> | **nested sub-records** |

> Note on the signal channels: the `+0xA0` map's value vectors are element-size 2
> (`QVector<short>`), matching the raw 0–255 amplitude counts documented in the main report
> (no scaling factor). Each channel index maps to one trace vector; the `+0xB8`
> timestamp map indexes samples by time.

### A.2.2 Interpretation

The record is the in-memory mirror of the storage schema: header fields (`ProgRef`,
`CycleNr`, timestamp) correspond to `Log`/`WP_*` key columns; the `+0xA0` channel map holds
what `WP_*` stores as a min/max envelope; the alarm sub-records correspond to `Alarms`
rows. The nested `QList<Record*>` fields let one workpiece own its per-feature children.

---

## A.3 The database read path 🔶/✅

### A.3.1 Call chain

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

### A.3.2 Named SQL entry points (all ✅ via mutex strings)

| Function | Rename | Query / behavior |
|---|---|---|
| FUN_00525700 | `SqlDb_openDatabase` | `"OpenDatabase"` — QSQLITE or QODBC (`DRIVER={SQL SERVER};…`); sets host/name/user/pw/port |
| FUN_005253d0 | `SqlDb_closeDatabase` | `"CloseDatabase"` — close, delete query+db, removeDatabase |
| FUN_005241e0 | `SqlDb_setDatabaseClosing` | `"SetDatabaseClosing:\t%1, SN:%2"` — closing-flag setter under mutex |
| FUN_00526d10 | `SqlDb_checkTableExists` | `"UeberpruefeTabelle"` — `SELECT name FROM sqlite_master …` |
| FUN_005270c0 | `SqlDb_getMaxRowId` | `"Zeilenanzahl"` — `SELECT MAX(ID)` as cheap row-count |
| FUN_005ea6c0 | `SqlDb_getAlarmsList` | `"GetAlarmsList"` — parse rows → 11-field alarm records, dedup-append |
| FUN_005f8820 | `SqlDb_findeAlleIDsFromSource` | `"FindeAlleIDsFromSource"` — `SELECT ID,Date … WHERE Source_Ref=… ORDER BY Date DESC` |
| FUN_0059b240 | `SqlDb_getWorkPiecesFromProgRef` | `"GetWorkPiecesFomProgRef"` — workpiece IDs by program ref, bit-filtered, sorted |
| FUN_00590e50 | `SqlDb_getWorkPieceCycle` | `"GetWorkPieceCycle"` — cycle header rows (type 1/2/3/5) into record |
| FUN_005efdc0 | `SqlDb_getSignalData` | `"GetSignalData"` — raw multi-channel sample traces into +0xA0 |
| FUN_005dfa50 | `SqlDb_getWorkPieceData` | `"GetWorkPieceData"` — orchestrates the three loaders above |

### A.3.3 `GetWorkPiecesFromProgRef` detail ✅

`SELECT * FROM <workpieces> WHERE <progRef> ORDER BY ID DESC`. Two modes: normal mode reads
ID + two status bytes per row and filters on bit masks (`& 0x500`, `& 4`, `& 0x200` — a
"valid/complete workpiece" test), building a deduplicated ID list and erasing incomplete
trailing entries; alt mode collects all IDs. The list is sorted ascending
(`std::sort<int*>`, introsort) before return. Table name literal → label
`g_workpiecesTableName` (`param_1_00a1d320`).

### A.3.4 `GetWorkPieceCycle` detail ✅

`SELECT * FROM <cycle> WHERE WorkPiece=<id>`. Each row carries a **type** field:

- type 1 — main cycle row: fills `+0x04/+0x0C/+0x18(ProgRef)/+0x1C(CycleNr)/+0x38(startID)/
  +0x54/+0x7C(QDateTime)` and inserts a dated entry into the `+0xB8` `QMap<QDateTime,int>`.
- type 2 → `+0x40`; type 3 → `+0x44`; type 5 → adjusts the `+0x38` start offset.
- `+0x3C` is used as a stop flag.

### A.3.5 `GetSignalData` detail ✅

`SELECT * FROM <signalTable> WHERE ID >= <start> AND ID <= <max>`. Pre-grows N channel
`QVector<short>` in the `+0xA0` map (channel count from a helper), then per result row writes
paired `(value, extra)` shorts into each channel's vector at a rolling byte offset. This is
the raw sensor/signal trace — the per-sample amplitude curve(s) for a workpiece cycle,
consistent with the wire-side SIGNALVERLAUF format and the no-scaling result in the main
report.

---

## A.4 Supporting application helpers 🔶

| Function | Rename | Meaning |
|---|---|---|
| FUN_00560340 | `Promos3DataRecord_copyCtor` | deep copy of the 0xF8 record (recurses into sub-records) |
| FUN_0055fbc0 | `Promos3DataRecord_dtor` | destructor freeing all ~40 members |
| FUN_005ebf20 | `formatCycleId` | builds `"PP.CCCCC"` label (2-digit prog, 5-digit cycle, separator) |
| FUN_004a0dd0 | `Record_collectActiveChannels` | walks 4 channel descriptors (stride 0xC @+0x4D), low-nibble flag → channel-index list |
| FUN_0055b630 | `TwoStringRecord_assign` | copy 4 ints + 2 QStrings (a lookup-record value type) |
| FUN_0055d840 | `DataRecord_setChannelList` | assign the `QList` at +0xF4 |
| FUN_00455d00 | `SqlDbManager_getConnectionForKey` | `"GetP2DatPmd"` — QMap<QString,DbConn*> lookup |
| FUN_004546c0 | `SqlDbManager_reapClosedConnections` | closes flagged connections; logs "N delayed databases have been closed" |
| FUN_0044cdc0 | `Promos3SqlDatenbankManager_ctor` | 0x4C-byte singleton ctor; QTimer `OnSimpTimer()` @ 5 min; reads INI |
| FUN_0044d070 | `Promos3SqlDatenbankManager_instance` | lazy singleton (`g_sqlDbManager`, `DAT_00a1ab04`) |
| FUN_00557d10 | `Promos3ProtokollThread_ctor` | QThread subclass; wait-condition + mutex; DB-logging worker |

### A.4.1 `Promos3ProtokollThread` public interface (moc dispatch)

Recovered from `qt_static_metacall` (`FUN_00798020`) — the thread's method indices:

| idx | function | role |
|---|---|---|
| 0 | FUN_005e1c90 | read records by source+date |
| 1 | FUN_005e1f50 | `AddAlarms` — batch-persist alarms with cycle/feature context ✅ |
| 3 | FUN_005e2af0 | `buildWorkpieceRecords` — the read entry point |
| 2,4,5,6 | FUN_005df950 / 005e2af0 / 005df970 / 005e2ed0 / 005e1930 | sibling batch add/read handlers |

---

## A.5 Newly labeled globals

| Symbol | Rename |
|---|---|
| DAT_00a1ab04 | `g_sqlDbManager` (Promos3SqlDatenbankManager singleton) |
| DAT_00a1cd04 | `g_dataRecordCount` (live Promos3DataRecord counter) |
| DAT_00a1cb8c | `g_protokollThreadCount` |
| param_1_00a1d320 | `g_workpiecesTableName` |
| (alarms table literal) | `g_alarmsTableName` |

---

## A.6 Consistency with the main report

Everything here corroborates and extends the main report without contradiction:

- The tables these readers hit (`Log`, `Alarms`, `Trend_*`, `WP_*`) are exactly the verified
  measurement schema (main report Part 10).
- The `+0xA0` `QVector<short>` channel traces confirm the amplitude representation is raw
  0–255 counts — the "no scaling factor" result — from the storage side as well as the wire.
- The `GetSignalData` layout mirrors the on-wire SIGNALVERLAUF body: same per-channel sample
  series, same units.
- `Promos3ProtokollThread` and the dispatcher thread (`Promos3KommandoVerteilerThread`,
  main report §1.5) are distinct workers: the former handles DB persistence, the latter
  command dispatch.

## A.7 Implications for the reader tooling

For a read-only telemetry/history viewer:

- **Live path** — already covered by the main report (decode SIGNALVERLAUF off the wire).
- **History path** — this appendix shows there is no need to reverse a binary DB format:
  the working DB is plain SQLite with the schema in Part 10. A migration/read tool can query
  `Log`, `WP_*`, `Trend_*`, `Alarms` directly and reconstruct the equivalent of a
  `Promos3DataRecord` per workpiece, using §A.3.4–A.3.5 as the field-population recipe.
- The `formatCycleId` rule (`"PP.CCCCC"`) reproduces the app's cycle labels exactly for UI
  parity.

## A.8 What remains in this layer (non-blocking)

- A few Qt container variants and small getters remain unnamed; they are mechanical
  (QMap/QVector/QListData detach/insert/free by signature) and carry no domain meaning.
- The exact semantics of the `+0xA8` typed sub-record map and a couple of `+0xE4`-family
  nested lists are structurally understood but not individually field-labeled; not required
  for read-only history reconstruction.

---

*End of Appendix A.*
