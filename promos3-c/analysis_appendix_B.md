# ═══════════════════════════════════════════════════════════════
# APPENDIX B — FUNCTION RECOVERY (SQL / config / receive-path session)
# ═══════════════════════════════════════════════════════════════

**Scope.** This appendix adds 30 functions named/analysed in the follow-up Ghidra session,
covering four clusters: (1) the SQL source/tool lookup path, (2) the alarm-insert path and
the dual-driver SQL abstraction, (3) offline-mode + Ethernet configuration + the settings
dialog, and (4) the **MC3_ command registry**, the CAN receive dispatch, and packet
validation. It also folds in three concrete data-format findings that came out of these
functions and **closes the group-2 field-layout open item** from Part 13.

Confidence uses the report's existing scale: ✅ VERIFIED (matched against INI/DB/runtime or
proven by the function's own literal tag string), 🔶 GHIDRA (code-derived, reliable),
⚠️ INFERRED (reasoned). Percentages are the analyst's per-function estimate.

> **Method note.** Most names below are *self-proving*: the function constructs a QString tag
> (a `Promos3MutexLocker` name, an `ErrorManager` log tag, or a class-qualified label such as
> `"Promos3CanInterface::receive"`) that states its own identity. Those are marked
> **[tag-proven]**. Where the name is structural only, it is marked **[structural]**.

---

## B.1 Master rename table

### B.1.1 SQL — source/tool ID lookup
| Address | Name | Conf. | Evidence |
|---|---|---|---|
| FUN_00601040 | `SqlDb_getNCToolID` | 99% ✅ | [tag-proven] `"getNCToolID"`. `SELECT … FROM NCTool WHERE Name='%1'` → int ID / −1 / 0. |
| FUN_006061d0 | `SqlDb_findeSourcesFromWerkzeug` | 99% ✅ | [tag-proven] `"FindeSourcesFromWerkzeug"`. `SELECT DISTINCT ID FROM Source WHERE Channel_Num=%1` + tool/NCTool clause. |
| FUN_005e1c90 | `SqlDbMgr_findeAlleIDsFromWerkzeug` | 88% 🔶 | [structural] Resolves connection by key (`this+0x6c`), calls the two above, merges via `SqlDb_findeAlleIDsFromSource`. |

### B.1.2 SQL — alarm insert + dialect abstraction
| Address | Name | Conf. | Evidence |
|---|---|---|---|
| FUN_005e9930 | `SqlDb_fuegeAlarmsHinzu` | 97% ✅ | [tag-proven] `"FuegeAlarmsHinzu"`. Lazy-creates + INSERTs one alarm row. Column order → §B.4. |
| FUN_00525530 | `SqlDb_getVerbindung` | 92% ✅ | [tag-proven] `"GetVerbindung"`. Copies the 10-QString connection struct at `this+0x40`. |
| FUN_00524480 | `Verbindung_copyCtor` | 86% 🔶 | [structural] Copy-constructs 10 QStrings (`0x00…0x24`) + int `+0x28`. |
| FUN_00446bc0 | `Verbindung_ctorNull` | 85% 🔶 | [structural] Null-inits the 10-QString struct. |
| FUN_00446c90 | `Verbindung_dtor` | 88% 🔶 | [structural] Releases members `[9]…[0]`. |
| FUN_00556680 | `SqlBuild_insertColumnPrefix` | 86% 🔶 | [structural] `INSERT INTO <t> (` + `"( ID , "` vs ODBC variant. |
| FUN_005565e0 | `SqlBuild_valuesPrefix` | 86% 🔶 | [structural] `"VALUES ( NULL,"` (non-ODBC) vs `"VALUES ("` (ODBC). |
| FUN_00557670 | `SqlDialect_ensureMap` | 87% 🔶 | [structural] Lazy-inits dialect singleton `DAT_00a1cb88`. |
| FUN_00557610 | `SqlDialect_ctor` | 84% 🔶 | [structural] Null-inits then builds the map. |
| FUN_00556f50 | `SqlDialect_buildTokenMap` | 83% 🔶 | [structural] Fills per-driver keyword map (→ §B.5). |

### B.1.3 Offline mode / Ethernet config / settings dialog / bootstrap
| Address | Name | Conf. | Evidence |
|---|---|---|---|
| FUN_0041c090 | `Interface_setOfflineMode` | 95% ✅ | [tag-proven] `"SetOfflineMode"`. Toggles offline; tears down / rebuilds CAN + ETH threads; writes INI `Offline`. |
| FUN_004fbae0 | `EthThread_initFromIni` | 90% 🔶 | [tag-proven] `"Promos3EthAbstract::initFromIni"`. Streaming variant (has `StreamingPort`/`ResendON`). INI map → §B.6. |
| FUN_00500390 | `EthThread2_initFromIni` | 78% 🔶 | [tag-proven] same tag; leaner sibling (no `StreamingPort`/`ResendON`; reads `m_broadcastPort`). Which-is-which pending caller xref. |
| FUN_006dcab0 | `EthSettingsDlg_loadFromIni` | 88% ✅ | [structural] Loads dialog from INI. Defaults verified vs `PROVISsettings.ini` (§B.6). |
| FUN_006dba10 | `EthSettingsDlg_saveToIni` | 83% 🔶 | [structural] Writes dialog IP/port fields back to `[Ethernet]`. |
| FUN_006d99a0 | `EthSettingsDlg_setupUi` | 85% 🔶 | [structural] Builds combos/masks/ranges; wires `On…Changed` slots. |
| FUN_00402030 | `Promos3Interface_ctor` | 90% 🔶 | [tag-proven] `"Promos3Interface"`. Acquires all core singletons, `startInterface`, spins up dispatcher + `EthThread2`. |
| FUN_00555580 | `Promos3TcpSocket_ctor` | 93% ✅ | [structural] Sets `Promos3TcpSocket::vftable`; reads timeouts; wires `readyRead→OnReadyRead`. |
| FUN_00442b60 | `Interface_onUnitConnected` | 80% 🔶 | [structural] Wires `DataReceived`/`UnitDisconnected`; persists `LastUsedPort`; starts poll timer. |

### B.1.4 MC3_ registry / receive path / packet validation
| Address | Name | Conf. | Evidence |
|---|---|---|---|
| FUN_0042b1f0 | `MsgCreator_buildMC3Registry` | 95% ✅ | [structural] Builds MC3_ name↔code map + per-command field-descriptor map. Registry → §B.2, layout → §B.3. |
| FUN_00508a80 | `CanInterface_receive` | 95% ✅ | [tag-proven] `"Promos3CanInterface::receive"`. Reassemble → dispatch / abort / restart-streaming. |
| FUN_00411960 | `DatenInstanz_closeDevices` | 93% ✅ | [tag-proven] `"Promos3DatenInstanz::CloseDevices"`. Closes each unit's DB, stops streaming, frees timers. |
| FUN_004c1090 | `Provis3Geraet_sendKom07_SetStreaming` | 95% ✅ | [tag-proven] `"…Sende_Kom_07_MC3_SET_STREAMING"`. Independently confirms cmd 7 = SET_STREAMING. |
| FUN_0042ec10 | `CanThread_run` | 92% ✅ | [tag-proven] `"Promos3CanThread"`. init → `QThread::exec()` → teardown; logs start/terminate. |
| FUN_00404dc0 | `Packet_checkCommandKnown` | 88% 🔶 | [tag-proven] `"ID_FEHLER_PAKET_KOM_NULL/UNBEKANNT"`. Validates command `+0x28` ∈ 1..0xFF. |
| FUN_00404790 | `Packet_checkExpectedEnAll` | 86% 🔶 | [tag-proven] `"Untersuche_enAll_PaketaufFehler"`. Rejects command not in {1,2}; logs `Expected cmd %1, received %2`. |

**Helper functions referenced (not fully analysed):** `FUN_00427f00` (registry insert),
`FUN_00428000` (field-descriptor insert), `FUN_0042b070` (commit field list),
`FUN_00686430` / `FUN_00682d20` (per-unit reassembly), `FUN_0042d8a0` / `FUN_0042d960`
(enqueue to `KommandoVerteilerThread`), `FUN_004c0370` (per-feature streaming check),
`MsgCreator_getCommandByte`, `MsgCreator_createPaketForCommand`.

---

## B.2 MC3_ command registry (code → name)  ✅

Recovered verbatim from `MsgCreator_buildMC3Registry` (`FUN_0042b1f0`), the message-creator's
own name↔code table (map @ object `+0x14`). This is the **authoritative** naming source —
it is what the binary itself uses, independent of the dispatch switch in Part 3.

| Code | Name | Code | Name |
|---|---|---|---|
| 0x00 | MC3_UNKNOWN | 0x12 | MC3_DEVICE_DESCRPTION *(sic)* |
| 0x01 | MC3_GIVESTATUS | 0x13 | MC3_EXTRACYCLE_INFO |
| 0x02 | MC3_GIVEGTYPE | 0x14 | MC3_EXTRALIMIT_INFO |
| 0x03 | MC3_GET_CB_VERSION | 0x15 | MC3_EXTRA_SENSOR_VFAKT |
| 0x04 | MC3_SENSOR_INFO | 0x16 | MC3_EXTRA_FEATURE_INFO |
| 0x05 | MC3_FEATURE_INFO | 0x18 | MC3_SYSTEM_MODE |
| 0x06 | MC3_DEVICEREC | 0x19 | MC3_LICENSE_INFO |
| 0x07 | MC3_SET_STREAMING | 0x1a | MC3_PATTERN_INFO |
| 0x08 | MC3_LIMIT_INFO | 0x1b | MC3_SET_OUTPUTS |
| 0x09 | MC3_CYCLE_INFO | 0x1c | MC3_ETH_MAC_ADDRESS |
| 0x0a | MC3_PLC_SETTINGS | 0x3a | DownloadHexFile |
| 0x0b | MC3_SENSOR_VFAKT | 0x99 | MC3_DOWNLOAD_IDENTIFIER |
| 0x0c | MC3_FEATURE_INCYCLE_SETTINGS | | |
| 0x0d | MC3_DEVICE_SETTING | | |
| 0x0e | MC3_SYSTEM | | |
| 0x0f | MC3_ALARM | | |
| 0x10 | MC3_EVENT | | |
| 0x11 | MC3_LAST_SIGNAL | | |

### B.2.1 Corrections to Part 3 (§3.2)
Two labels in the group-2 handler table should be updated against this registry:

1. **0x11 is `MC3_LAST_SIGNAL`, not `MC3_SENSOR_VFAKT`.** §3.2 lists 0x11 as
   `MC3_SENSOR_VFAKT (stub)`. The binary's own registry puts **`MC3_SENSOR_VFAKT` at 0x0b**
   and **`MC3_LAST_SIGNAL` at 0x11**. The handler `FUN_0040c5e0` at dispatch-index 0x11 may
   simply be a shared/stub worker, but the *name* attached to 0x11 in §3.2 is wrong. The
   "no runtime scaling" conclusion is unaffected (the VFAKT worker `FUN_004acf40` is still a
   `return p!=0` stub) — only the code↔name mapping is corrected.
2. **German handler labels are English aliases in the registry.** §3.2 `MC3_MERKMAL_INFO`
   (0x05) and `MC3_GERAETEREC` (0x06) are the same commands the registry names
   `MC3_FEATURE_INFO` and `MC3_DEVICEREC`. (Merkmal = feature, Gerät = device.)

Otherwise the registry and §3.2 agree: 0x03, 0x04, 0x07, 0x08, 0x09, 0x0f, 0x10, 0x18,
0x1a, 0x1b all match.

---

## B.3 MC3_ per-command field-descriptor table  🔶 — *closes the Part 13 open item (group 2)*

The second map built by `MsgCreator_buildMC3Registry` (object `+0x18`) is keyed by command
code and holds a **per-command list of field descriptors**. Each descriptor is inserted by
`FUN_00428000(list, key, &field_tag, &{cmd, A, B})` and the completed list is committed per
command by `FUN_0042b070`. The descriptor is three consecutive dwords:

```
field_tag  (map key, e.g. 1,2,3,4,8,0x10,0x11,0x12,0x13 …)   — the field identifier/slot
cmd        — command code (redundant; equals the outer key)
A          — attribute A  (constant 4 for most fields; larger for the first/lead field)
B          — attribute B  (small enum: 2,3,4,5,6,7,0xb,0x10,0x11,0x12,0x14,0x21,0x2c … )
```

Interpretation (⚠️ INFERRED, pending one capture to bind): `B` behaves like a **data-type /
element code** and `A` like a **size/field-length**, with the lead field of each command
carrying a larger `A` (a base offset or header length). Binding `A`↔offset vs `A`↔length
needs one raw frame — obtainable with `LogCANMessage=1` exactly as Part 13 describes.

Representative decoded lists (raw `{tag: A,B}` triples straight from the binary):

| Cmd | Name | Field descriptors `{tag: A,B}` |
|---|---|---|
| 0x04 | MC3_SENSOR_INFO | `{1:0x1d,3} {2:4,0x10} {3:4,5} {4:4,3} {8:4,2}` |
| 0x05 | MC3_FEATURE_INFO | `{1:0x2e,3} {2:4,0x31} {3:4,3} {4:4,3} {9:4,5} {8:4,3}` |
| 0x08 | MC3_LIMIT_INFO | `{1:0xe,5} {2:4,0x14} {3:4,6} {8:4,4}` |
| 0x09 | MC3_CYCLE_INFO | `{1:0x37,5} {2:4,0x37} {3:4,0xb} {8:4,4} {0xb:4,6} {0x12:4,5} {0x11:4,5}` |
| 0x0f | MC3_ALARM | `{1:0x24,5} {0xa:4,6}` |
| 0x10 | MC3_EVENT | `{1:0xf,5}` |
| 0x0e | MC3_SYSTEM | `{1:0xc,3} {5:0,3} {6:7,3} {7:4,7} {0xf:4,5} {0x13:4,2} {8:4,2}` |
| 0x99 | MC3_DOWNLOAD_IDENTIFIER | `{1:4,3} {2:4,5} {6:4,5} {3:4,0xd} {8:4,0xb}` |

The complete set (all ~30 commands) is present in `FUN_0042b1f0` and can be dumped
mechanically; the eight above are the ones cross-referenced to already-decoded records
(SENSOR_INFO §4.3, EVENT §4.4, ALARM §4.2). This gives, for group 2, the field-level layout
the report previously listed as the only outstanding wire item.

---

## B.4 Alarms table — column order  ✅

From `SqlDb_fuegeAlarmsHinzu` (`FUN_005e9930`), the exact INSERT column order for the Alarms
table (complements the measurement-DB schema in Part 6):

```
Date, ProgRef, ChannelNr, CycleNr, FeatureNr, LimitNr, Ack, Ack_Date, Signal, TimeOffset
```

On failure the app logs `"writing in table %1 from database %2 failed. Error %3 %4"`. The
source record (`param_1`) field offsets, ⚠️ INFERRED (to confirm against a live row):
`+0x04` Date(text), `+0x0c` ProgRef, `+0x18` ChannelNr, `+0x1c/+0x20` Cycle (composite),
`+0x24` FeatureNr, `+0x28` LimitNr, `+0x2c` Ack, `+0x30` TimeOffset, `+0x34` Signal(text).

---

## B.5 Dual-driver SQL abstraction (SQLite ⇄ ODBC/SQL-Server)  🔶

`SqlDialect_buildTokenMap` (`FUN_00556f50`) proves the app carries a **driver-abstraction
layer** keyed by Qt driver name (`QSQLITE` vs `QODBC`). Token pairs recovered:

| Token | QSQLITE | QODBC |
|---|---|---|
| create-table | `create table ` | `CREATE TABLE ` |
| insert | `INSERT INTO` | `INSERT INTO` |
| primary-key | `primary key` | `PRIMARY KEY` |
| not-null | *(schema-specific)* | ` NOT NULL` |
| identity | *(NULL autoincrement)* | `IDENTITY(1,1) ` |

`SqlBuild_insertColumnPrefix` / `SqlBuild_valuesPrefix` consume this: for non-ODBC they emit
`( ID , … ) VALUES ( NULL, …)` (explicit NULL autoincrement), for ODBC they omit the ID
column (server `IDENTITY`). **Implication for the reader:** the reference install is SQLite
(Part 1), but the same binary targets SQL-Server via ODBC; any schema assumptions should hold
for both back-ends.

---

## B.6 `[Ethernet]` INI → struct offset map  ✅ (defaults verified vs PROVISsettings.ini)

From `EthThread_initFromIni` (`FUN_004fbae0`). Defaults confirmed byte-for-byte against the
reference `PROVISsettings.ini`.

| INI key (`[Ethernet]`) | Default | Struct off. | Note |
|---|---|---|---|
| Active | — | (gate) | `<1` → aborts init; also aborts if offline |
| FirstDevice | 1 | +0x08 (u16) | |
| LastDevice | 1 | +0x0a (u16) | |
| BroadcastPort | 4711 (0x1267) | +0x1c (u16) | `EthThread2` reads it as `m_broadcastPort` (key typo in sibling) |
| FirstPort | 1789 (0x6fd) | +0x20 (u16) | ✅ matches gateway port |
| LastPort | 1789 (0x6fd) | +0x22 (u16) | |
| StreamingPort | 2789 (0xae5) | +0x50 (i32) | ✅ matches `[Ethernet]StreamingPort` |
| LastUsedPort | 1789 (0x6fd) | +0x1e (u16) | live value on ref box = **1793**; also written by `Interface_onUnitConnected` |
| SelectedInterface | "" | (QString) | |
| unitAnswerTimeout | 500 | +0x10 (i32) | floored to 500 |
| ScanTimeout | 1000 | +0x0c (i32) | floored to 1000 |
| ResendON `[Internal]` | 1 | +0x54 (i32) | streaming-variant only |
| MaxResend | 5 | +0x24 (i32) | |
| LogETHMessage `[ErrorManager]` | 0 | +0x48 (i32) | ETH-side capture toggle (mirror of `LogCANMessage`) |

`EthSettingsDlg_loadFromIni` (`FUN_006dcab0`) additionally binds `[CAN]` keys to the dialog:
`PCANGateway`, `BaudrateRegister` (default 22), `BaseCanIDTransfer` (default 1280) — all ✅
matching `[CAN]` in the reference INI.

---

## B.7 Receive-path & lifecycle additions

These slot into the Part 1.3 receive path and Part 1.5 concurrency model:

- **`CanThread_run` (FUN_0042ec10)** — the worker thread body: sets object name
  `Promos3CanThread`, initialises, emits ready, `QThread::exec()`, then closes the socket and
  logs `"terminated with %1"`.
- **`CanInterface_receive` (FUN_00508a80)** — per-unit reassembly + branch: status `1`
  complete → enqueue to `KommandoVerteilerThread`; status `2` abort → log `"enAbort"`, drop
  unit; status `3` restart → send `MC3_SET_STREAMING`, `qDebug("* * * Streaming ON at
  StartUp")`. Packet fields used: command `+0x28`, priority `FUN_00442410`, processed-flag
  `+0x4c`, stream streaming-byte `+0x12`.
- **`DatenInstanz_closeDevices` (FUN_00411960)** — orderly shutdown: per unit, close DB via
  the SQL manager (type 1 `FUN_0044d0e0` / type 2 `FUN_0044d290`), send streaming-off for
  streaming units, disconnect+delete the per-unit timer, erase from the buffer map; logs
  `"Closing succeed for %1 devices"`.
- **`Provis3Geraet_sendKom07_SetStreaming` (FUN_004c1090)** — the streaming on/off sender;
  writes the flag at stream `+0x12` and appends it as a payload byte. Confirms cmd 7.
- **`Promos3Interface_ctor` (FUN_00402030)** — the bootstrap that wires GlobaleDaten,
  ErrorManager, Translator, DatenInstanz, SqlDatenbankManager, NcComm, MessageCreator,
  `KommandoVerteilerThread`, and `EthThread2`, then starts the ETH thread iff
  `[Ethernet]Active>0`.

---

## B.8 Minor bug flagged (not a decode error)

In `SqlDb_findeSourcesFromWerkzeug` (`FUN_006061d0`) the failure-log format string
`"Finding IDs from Tool %1 and Channel %2 …"` binds `%1`←`param_2` and `%2`←`param_1`, i.e.
the **channel and tool arguments are swapped relative to the WHERE clause** (`Channel_Num=%1`
uses `param_1`). Cosmetic (log text only), but note it if matching log lines to queries.

---

## B.9 Glossary additions

- **Verbindung** — (DB) connection / connection-parameter struct (10 QStrings + int).
- **Werkzeug** — tool; **NCTool** — the NC-side tool table (name → ID).
- **fuege … hinzu** — add / append (here: insert an alarm row).
- **Untersuche … auf Fehler** — examine … for errors (packet validators).
- **Kommandokennung** — command identifier (the `+0x28` command field).
- **enAll / enAbort / enKom** — packet/return status enum values used in the CAN receive
  branch (`CanInterface_receive`): complete / abort / command-level.
- **QSQLITE / QODBC** — Qt SQL driver names selecting the dialect token set (§B.5).
- **LastUsedPort** — live UDP port persisted per connection (struct +0x1e); ref box = 1793.

---

*End of Appendix B.*
