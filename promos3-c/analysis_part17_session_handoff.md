# PROVIS3 / Prometec — **PART 17: SESSION HANDOFF**

Everything established in this session, in a form that can be dropped into a fresh context.
Supersedes nothing in the v2 report except where marked ⚠️ **CORRECTION**.

**Target system:** Mazak cell, Prometec PROVIS3, `Promos3DatenProvis2Geraet` (generation **1 = `MC_`**),
firmware Version **229 (0xE5)**, 1 channel, 4 sensors, GeraetTyp **0x44**, units **1–15**,
CAN-over-UDP gateway at **192.168.222.17:1789**.

---

# 1. Status

| Measure | Start of session | Now |
|---|---|---|
| Protocol knowledge | ~78% | **~92%** |
| Trustworthy live reader | ~45% | ~45% *(no code written yet)* |
| Group-1 commands named | 3 / 38 | **~35 / 38** |
| Wire framing (MC_) | unknown | **specified** |
| Checksum | unknown | **recovered + byte-verified** |
| Request format | unknown | **specified** |
| Unit discovery | unknown | **specified** |

The decode side is essentially complete. The blocker is unchanged and is **engineering, not RE**:
the reader's transport layer still implements rules we now know are wrong.

---

# 2. The `MC_` protocol (this box)

## 2.1 Answers carry no command and no group ✅

`UnitComm_assembleAnswer_MC` builds the finished message as:

```c
group   = Paket_getGroup(requestPaket);      /* from the request */
newMsg[10] = requestPaket[10];               /* +0x28 command, from the request */
```

Both are read **before any answer byte is touched**. The answer payload is pure record bytes.
The v2 open item "wire offsets of `[group]/[command]/[length]`" is closed **by deletion** — those
fields do not exist on the MC_ wire.

**Consequence:** an answer is only identifiable in the context of the request it answers. A
one-directional passive capture is worthless for this generation.

## 2.2 CAN answer frame layout ✅

`TPCANMsg` = `{u32 ID; u8 MSGTYPE; u8 LEN; u8 DATA[8]}` (LEN at `+5`, DATA at `+6`).

```
DATA[0]          = sequence number, starts at 0, +1 per frame
DATA[1..LEN-2]   = payload, 7 bytes per frame
DATA[LEN-1]      = checksum — final frame only, and only if it fits
```

| condition | checksum location |
|---|---|
| `expectedSize % 7 != 0` | last byte of the last data frame |
| `expectedSize % 7 == 0` | separate 2-byte frame `[seq][checksum]` |

Sequence mismatch → `"Unknown answer format received on CAN bus for command %1"`.
Device error answer → a frame with `DATA[0]==0 && DATA[1]==1` → `"Error answer in CAN bus"`.

## 2.3 Checksum — verified against real logged bytes ✅

```c
signed char promos3_checksum(const uint8_t *recv, int recv_n,
                             signed char seed,           /* = unit id */
                             const uint8_t *sent, int sent_n,
                             int group)
{
    signed char ret = 0;
    if (!sent || (group != 0 && group != 1)) { ret = -1; seed = 0; }
    if (sent && sent_n > 0)
        for (int i = 0; i < sent_n - 1; i++) seed += sent[i];   /* ALL BUT THE LAST BYTE */
    else if (group == 1) seed = 0;
    if (recv) for (int i = 0; i < recv_n; i++) seed += recv[i];
    return ret - seed;                                          /* two's complement */
}
```

**Verification.** `LogFile-260701-T1154.txt` contains `waitingForData: requested 0x08, 0x01, 0xf6`.
`-(unit 1 + 0x08 + 0x01) = -10 = 0xF6` — exact match. Units 2/3 give `0xF5`/`0xF4`, so that line
was unit 1. First byte-level verification of the live protocol in the project.

`sent_n - 1` proves **the last byte of a request is that request's own checksum**.

## 2.4 Request format ✅

```
[command][station][params …][checksum]
 0x0e      station                        <- MC_GIVEKANAL
 0x1b      station  feature  p3  p4       <- MC_GIVESIGNALVERLAUF
 0x08      0x01              0xf6         <- logged, complete
```

`params[0]` is the **station / traceMap key**, not the channel. Confirmed three ways:
`bearbeite_Kom_15` keys traceMap off `payload[0]`; `Geraet_sendeKom_MC_GIVEKANAL` sets
`this+0x54 = station`; `bearbeite_Kom_14` reads it back as the key.

⚠️ Requests are **not always one CAN frame**. The logged `0x0c 0x01 0x61 ff…` is `MC_SETZYKLUS`,
station 1 — a 170-byte cycle record, so multi-frame. The log dumper caps at 8 bytes.

`0xFB` and `0xFD` are **reserved feature selectors** in the trace request (they select modes 1 and
2), not real feature indices. Do not run them through `key_to_index()`.

## 2.5 Completion rule ✅

```
expected = Paket.recvSize (+0x14)
   ├─ normal: stamped at send time from Geraet_expectedRecordSize(cmd)
   ├─ cmd 0x16: expected = DATA[1] * Paket.recordSize(+0x34) + 1     (variable count)
   └─ cmd 0x14: on checksum failure, retried with expected = 0x24 (36)  (version fallback)
accumulate 7 payload bytes/frame while (accumulated < expected)
then validate checksum; on mismatch roll frames back (prepend) and retry
```

`expected == 0` → pure ack; the single answer frame's `DATA[1]` *is* the checksum.
`cmd 0x30` (CIAB_COMMAND) with subtype 2 or 4 → segmented transfer; `+0x3c`/`+0x40` are
offset/total and the assembler queues its own follow-up request.

Retry ladder: `this+0x20` attempts vs `this+0x34` max (`[Comm] MaxResend=1`) →
`try again` (status 1) → `aborting` (status 2) → drop queue + flush frames.

## 2.6 `Geraet_expectedRecordSize` — the size table ✅

Flat switch keyed by command number; unknown → logs `"Versionsfehler"`, returns −1.
It is **expected ANSWER size**, stamped into `Paket+0x14` at send time.

| cmd | bytes | note |
|---|---|---|
| 0x02, 0x28 | 14 | SGrenzRec ✅ |
| 0x03 | 170 | SZykRecV4802 ✅ ⚠️ odd for a SET command |
| 0x04 | 4 | |
| 0x05 | 16 | |
| 0x08, 0x09, 0x0c | 1 | ack |
| 0x0e | **144** | SKanalRecV40 ✅ (call site verified) |
| 0x0f | 40 | |
| 0x10 | 46 | SHardwareRec ✅ ⚠️ but GIVEHARDWAREREC is 0x1a |
| 0x11 | 2 | |
| 0x35, 0x3f | 20 | |
| 0x36 | 60 · 0x37 | 64 · 0x38 | 160 |

⚠️ Entries 3, 16 and 63 don't align with the recovered command names — possible record-type
keying rather than command keying. Unresolved.

---

# 3. The `MC3_` protocol (group 2) — a **different** protocol

Not a variant. Shares nothing at the framing layer.

| | **MC_** (group 0/1) | **MC3_** (group 2) |
|---|---|---|
| per-frame overhead | `DATA[0]` = sequence | none |
| payload per frame | **7** | **8** |
| command on wire | no — from request | **yes**, msg byte 0 |
| length on wire | no — from size table | **yes**, byte 1 (16-bit for `0x0f`/`0x10`) |
| total size | `expectedSize` | `lengthByte + 1` |
| checksum | `-(unit + Σsent[0..n-2] + Σpayload)` | `-1 - Σ msgBytes` (one's complement) |
| body starts at | offset 0 | offset 2 |
| ordering check | sequence + rollback | none |
| passively identifiable | **no** | yes |

**The v2 report's `[group][command][length]` model was a description of MC3_** — nearly right for
group 2 (group is hardcoded, not on the wire), and simply not applicable to this box.

**16-bit length extension:** for `0x0f`/`0x10` with `DATA[2]==1`, when the request asked for
`0xFFFF`, length promotes to `(DATA[3] << 8) | DATA[1]`. Three §4.2 assumptions confirmed at once:
`0x0f`/`0x10` = ALARM/EVENT, `DATA[2]==1` = "alarm data" subcommand, `0xFFFF` = "give me
everything". An 8-bit length assumption truncates every full alarm/event dump.

⚠️ MC3_ commands ≤ 2 never take the header-parse path (`req[0x28] > 2` gate) — handshake is
serviced elsewhere.

---

# 4. Streaming (two more framings, both MC3_-only)

`UnitComm_receiveMonitoringData` (CAN, queue at `this+0x0c`) and
`EthSocket_streamingDataReceived` (Ethernet). Layout `[cmd][id16][?]` + `len + 4` total,
per-command length table derived from the live feature count, checksum invariant `Σ == 0xFF`.

| streaming cmd | CAN | Ethernet |
|---|---|---|
| 1 | features×4 | features×4 |
| 2 | sub-table (`DATA[5]`) | same |
| 3, 5, 7 | `0x0D` | **`0x0B`** |
| 4, 6 | features×2+1 | same |
| 9 | 4 | 4 |

Both gate on `getTargetType == 2`. **On this MC_ box the streaming path never produces anything** —
dead code here. Delivered as a group-2 Paket with command 7, real type in `+0x2c`.

---

# 5. Architecture

```
UI / Geraet senders
   └─ MsgCreator_createPaketForCommand   <- builds the wire buffer
      └─ KommandoVerteiler_enqueuePaket  <- outbound queue (+0x08)
         └─ KommandoVerteilerThread::run
            ├─ +0x0c inbound  -> Router_dispatchInbound -> Command_Dispatch_Switch
            └─ +0x08 outbound -> Router_routePaketOutbound
                                   ├─ RouterObj.type 2 -> Eth thread   (signal SendRequest)
                                   └─ RouterObj.type 3 -> CAN thread   (signal SendRequest)
                                        └─ slot SetForSending -> per-unit queue
                                           └─ pumpSendQueues -> send -> transport
```

**Routing is by transport, not generation.** `RouterObj.type`: **2 = Ethernet, 3 = CAN**.
The `type 1` objects in every `Sende_Kom_*` are source tags at `Paket+0x0c`, not routing keys.

**Group 0 = "generation not yet known."** `Router_registerUnit` sends `MC_GIVESTATUS` as group 0;
the dispatcher's group-0 arm then sends `MC_GIVEGTYPE`; `FUN_00412290` decides the generation and
everything afterwards goes out as group 1 or 2. Group 0 uses MC_ framing (hence
`UnitComm_firstReceivedPaket` routing `group == 0 || group == 1` to the MC_ assembler).

## 5.1 `MsgCreator_createPaketForCommand` (0x0042d190) ✅

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

Signature: `(this, group, srcTag, dstKey, cmdByte, subCmd, 1)`. Arg 7 is `1` at all 77 call sites.
`cmd == 0` → `"wrong command number for %1"`, returns NULL.

⚠️ **The buffer comes out zero-filled — the checksum is NOT written here.** Senders then poke
station/params in with `QByteArray_setByteAt`. The trailing byte is still `0x00` when it leaves
this function.

## 5.2 Where the checksum is written — narrowed by elimination

- `promos3_checksum` has **exactly 4 call sites** (`0068437f`, `00684ab6`, `00684ce2` in
  `UnitComm_assembleAnswer_MC`; `006860a0` in `_MC3`). **All receive-side.**
- `createPaketForCommand` zero-fills and does not write it.
- `SetForSending` (both Eth variants) only queues.
- `pumpSendQueues` → `send` → `Interface_setLastSentPaket` → `TcpSocket_sendToUnit`:
  **`QIODevice::write` of the raw buffer, nothing touched.**

⟹ It must be written inside the **CAN interface**, which is a separate hierarchy.
**Open next: `FUN_005073f0`, and whatever function contains `0x005090f5`.**

## 5.3 `Promos3CanInterface` — plain QObject, metacall-dispatched ⚠️

Its vtable has only 11 entries (all boilerplate). No index-12/14 pattern. Slots:

```
case 0: FUN_00686740
case 1: CanInterface_searchForNewUnits
case 2: FUN_005073f0   <- takes Paket*, the send entry
case 3: FUN_00508210   <- returns bool
```

### Constructor constants — **three CAN-ID bases** 🔴 IMPORTANT

```c
this+0x48 = 0x500  /* 1280 */     this+0x4c = 1     /* first unit */
this+0x54 = 0x580  /* 1408 */     this+0x50 = 0x0F  /* last unit  */
this+0x58 = 0x600  /* 1536 */
this+0x20 = 8, this+0x22 = 0x200, this+0x24 = 0x16, this+0x44 = 0x32
this+0x30 = "ProcessControl", this+0x34 = "sandvik"
```

The report only ever knew `0x500` (`unit = ID − 1280`). CANopen-shaped: plausibly `0x600+unit`
master→slave, `0x580+unit` slave→master, `0x500+unit` data/streaming. **This is the direction
discriminator G4 needed.** The current reader computes `unit = can_id - 1280` and drops anything
≥ MAX_UNITS — so IDs at `0x580+n` / `0x600+n` map to unit 128+/256+ and are **silently discarded**.
An entire direction may be being thrown away.

## 5.4 Unit discovery ✅

`CanInterface_searchForNewUnits`:
- rescan gate `DAT_00a17914 = unitAnswerTimeout × 3` = **900 ms** (this is where the INI's
  `unitActiveTimeout=900` comes from — derived, not independent)
- sweeps units `+0x4c … +0x50` (1–15); unknown → candidate; known → `UnitComm_checkAnswerTimeout`,
  status 3 → `"unit %1 detected as not active, will be removed"` → `unitBuffer_remove`
- probes **one** candidate per pass, round-robin via `DAT_00a1bc2c`, builds `MC_GIVESTATUS` with
  **group 0**, and `QList_prepend`s it (probes jump the queue)

`CanThread_onTimerTick`: `searchForNewUnits → [msleep(3)] → pollMessages → receive → QTimer(3 ms)`.
**A 3 ms polled loop**, not signal-driven. That is the master-mode cadence.

## 5.5 One-outstanding-request enforcement ✅

`Interface_setLastSentPaket` stores the in-flight request in the map at `iface+0x4c`, keyed by unit,
and logs `"Requesting cmd %1 over pending requested cmd %2"` if one is already outstanding.
`Interface_getUnitSendStatus` reads `pending+0x48` as the timeout multiplier.

`Promos3TcpSocket_getStatus` auto-raises `unitAnswerTimeout` by 50 ms (cap 500) on slow units and
**writes it back to the INI** — `"Auto adjusting timeout to %1 in unit %2"`. 300 ms is not fixed.

---

# 6. Object layouts

### `Promos3Paket` — 0x50 bytes

| off | field | accessor |
|---|---|---|
| +0x00 | group / generation | `Paket_getGroup` |
| +0x04 | routing key A (unit id as **text** → `toInt`) | `Paket_getRouterKeyA` |
| +0x0c | source tag (RouterObj) | `param1_+_0xc` |
| +0x14 | expected receive size | `Paket_getRecvSize` / `Paket_setRecvSize` |
| +0x20 | **aux context `QVector<u8>`** — never sent | `Paket_setByteArray` / read by `stream_peekU16` |
| +0x28 | **command** | direct `p[10]` |
| +0x2c | **sub-command** | direct `p[11]` |
| +0x30 | **station / device index** | direct `p[12]` |
| +0x34 | record size (cmd 0x16 formula) | `Paket_getRecordSize` |
| +0x3c / +0x40 | chunk offset / total (cmd 0x30) | direct |
| +0x48 | timeout multiplier (init 1) | used by `UnitComm_checkAnswerTimeout` |
| — | **wire buffer** | `stream_peekCurrent` |

⚠️ **CORRECTION to Part 16 §16.5:** `+0x20` is *not* the wire bytes. Two distinct byte arrays:
`stream_peekCurrent` = wire, `stream_peekU16` = `+0x20` aux context.

The aux vector matters: `Geraet_sendeKom_27` packs `{station, featureKey, p3, p4, mode}` into it,
and `UnitComm_assembleAnswer_MC` copies it from request into answer. **That is how
`bearbeite_Kom_27` knows which feature it asked for.** It never touches the wire — a passive
listener must reconstruct it from request bytes; a master gets it free.

### `UnitComm`
`+0x00` request queue · `+0x08` received-frame list · `+0x0c` streaming frame list ·
`+0x14` unit RouterObj · `+0x1c` QTime · `+0x20` attempt counter · `+0x24` progress/in-progress ·
`+0x28`/`+0x2c` timeouts · `+0x34` max attempts · `+0x40` streaming seq · `+0x44` last frame count

### Interface (Eth hierarchy)
`+0x18` socket map · `+0x40` per-unit send queues · `+0x44` per-unit "buffer full" flags ·
`+0x48` log level · `+0x4c` last-sent-paket map · `+0x10` QTimer

### Eth vtable index map (stable across `Promos3EthAbstract` / `Promos3EthInterface` / `Promos2EthInterface`)
`11` init · **`12` SetForSending** · `13` ? · **`14` send** · `15` receiveData ·
`16` ? · `17` onUnitConnected · `18` ? · `19` ? · `20` initFromIni · `21` ?

### `Promos3RouterObj` — 8 bytes
`{int type; QString name}`. type **1** = source tag, **2** = Ethernet, **3** = CAN.

---

# 7. The `MC_` command table

`Kom_NN` is decimal, so `Kom_NN` = command `0xNN`. Recovered by grepping `Sende_Kom_*` /
`bearbeite_Kom_*` tag strings. ~35 of 38 group-1 handlers now named.

| cmd | name | cmd | name |
|---|---|---|---|
| 0x01 | GIVESTATUS | 0x21 | GIVE_CDR_DATA |
| 0x02 | GIVEGTYPE | 0x23 | GIVE_SENSORVALUES |
| 0x03 | SETANZMODE | 0x24 | SET_SENSORVALUES |
| 0x04 | GIVEMERKMAL | 0x25 | GIVE_ACTZYKINDEX |
| 0x05 | GIVEUSEDZYKTAB | 0x27 | GIVE_EINZEL_TEACH |
| 0x06 | GIVEKONFIG | 0x28 | GIVE_EINRICHTEN_STATUS |
| 0x08 | GIVEPLCVALUES | 0x29 | *(worker FUN_004dc3e0)* |
| 0x09 | SETPLCVALUES | 0x2c | SET_DSP_GERAET |
| 0x0a | SETGERAET | 0x2d | DSP_STANDARD |
| 0x0b | SETKANAL | 0x30 | **CIAB_COMMAND** (segmented) |
| 0x0c | SETZYKLUS | 0x32 | SETZYKLUSWITHTIME |
| 0x0e | GIVEKANAL | 0x33 | GIVEPROGID |
| 0x0f | GIVEZYKLUS | 0x35 | GIVE_ACF_INFO |
| 0x11 | ALARMGESEHEN | 0x36 | SET_ACF_INFO |
| 0x12 | **GIVEALARM** | 0x37 | SET_ACF_INFO_INTERN |
| 0x13 | QUITALARM | 0x38 | GET_WKS_ID |
| 0x15 | PRESSEDKEYS | 0x39 | GET_ACF_DATA |
| 0x16 | **GIVESAMMELMERKMALE** | 0x3c | GET_GERAET_ACF |
| 0x18 | GIVETEACHSTATUS | 0x1b | GIVESIGNALVERLAUF |
| 0x1a | GIVEHARDWAREREC | 0x1c | GIVEOLDWORKPROZ |
| 0x1f | GIVEMUSTER | | |

Self-checks: `0x0c`/`0x32` share a handler because they're SETZYKLUS and SETZYKLUSWITHTIME;
`0x16 = GIVESAMMELMERKMALE` ("collected features") is exactly the command with the computed
`count × recSize + 1` length; `0x30 = CIAB_COMMAND` is the segmented-transfer command;
`case 0x15: qDebug() << "MC_PRESSEDKEYS"` is a literal in code (Kom 21 = 0x15 ✓).

---

# 8. Live measurement block — `Kanal_addMerkmalData` (cmd 0x16)

`this` = a **channel** object (`+0x16` channel no., `+0xa8` target RouterObj, `+0xb0` version).

```
data[0]  = row count
stride   = featureCount*2 + 2      (or +4 when this+0xC0 == 1)
row r, feature f: lo = data[base + r*stride + f*2]
                  hi = data[base + r*stride + f*2 + 1]
```

`lo == 0xFF` is an **escape**; `hi` selects the marker, the *following* row carries the parameter:

| `hi` | meaning |
|---|---|
| `0x00` | **new cycle** — next row's byte is the new cycle index |
| `0xFB` | per-feature reset across all features |
| `0xFE` | **workpiece ID** — next byte is ID size, cross-checked against `[WorkpieceID] IDsize` |

Flag bits in `hi` (gated on `version > 0xD8`; yours is `0xE5` so all active): `0x01` teach,
`0x10` start/stop, `0x40` tool change (`"m_bToolChange set"`), `0x08` → bit 7 of derived status.
`lo & 0x04` = alarm → timestamps and fires the tool-wear path.

**Double buffering:** on a mid-block cycle boundary, remaining samples go to shadow maps
(`+0xC8`/`+0xD0`) and swap into the live ones (`+0xC4`/`+0xCC`) at the boundary. Ignoring this
attributes post-boundary samples to the wrong cycle.

Cross-check: `FUN_00684160`'s `expected = DATA[1] × Paket+0x34 + 1` is the same formula —
`DATA[1]` = row count, `+0x34` = stride, `+1` = the count byte. Two independent derivations agree.

⚠️ The decompiler shows rows starting at `Data+0x10`, the same byte as the count; the `+1` says
rows start after it. Assume `base = 0x11`, confirm on the first real block.

---

# 9. Display data (for G8)

**Alarm slot names** — `GlobaleDaten_loadIniTables` reads `[AlarmNames]` keyed `AlarmName<N>`,
translating known keywords, falling back to `"Alarm <N>"` when blank. Built-in keywords:
`collision`, `Break`, `Wearout`, `Missing`, `Contact`. **This box's actual table:**

```
1 = Collision   2 = Break   3 = Wearout   4 = Missing   5 = Coolant   6..8 = blank -> "Alarm 6/7/8"
```

⚠️ Slot 5 is **Coolant**, not the built-in `"Contact"` default — operator-assigned. Hardcoding
defaults mislabels it. Same trap as the feature names.

**Station names** — `[StationNames]` format `Station-<Serial>.<Channel> = Name`, empty on this box
→ fall back to `SNr.Ch`.

**Model string** — `[MonitorTypes] 0x44` list, GSubType 5 → `MSL5082-16` (0-based) or
`MSL5081-16` (1-based). Report open item #2 **50% closed**; only the index base is unknown.

**Field labels** — `UnitConfigWidget_setupUi` is the app's own label dictionary and maps almost
field-for-field onto `SKanalRecV40`: `Unit_SamplePointLength` = "PROVIS Sampling rate",
`Unit_WorkingRange` = "Measuring range", `Unit_SignalFallTime` = "Signal drop time TD",
`Unit_OscillationTime` = "Oscillation time TRS", `Unit_AxisActiveOFFDelay`,
`Unit_SpindleActiveONDelay`, `Unit_ChannelInactive`, plus the filter/offset/compensation set.

---

# 10. Complete rename table

### Command handlers / device layer
| Address | Name | Conf. |
|---|---|---|
| FUN_004cd420 | `Geraet_bearbeite_Kom_06_MC_GIVEKONFIG` | 97% ✅ |
| FUN_004c5840 | `Geraet_expectedRecordSize(komNr)` | 97% ✅ |
| FUN_004c56a0 | `Geraet_getGeraetTyp` (returns `this+0x4ba`) | 96% ✅ |
| FUN_004c5c70 | `Geraet_getRecordVersion` *(unread)* | 40% ⚠️ |
| FUN_004a7ec0 | `Kanal_addMerkmalData(featureCount, stream, &status)` | 92% ✅ |
| FUN_004e1190 | `Kanal_getFlagWord(idx, sel)` | 60% ⚠️ |

### MC_ senders
| Address | Name | Conf. |
|---|---|---|
| FUN_004c6b90 | `Geraet_sendeKom_MC_GIVEHARDWAREREC` | 96% ✅ |
| FUN_004d0320 | `Geraet_sendeKom_MC_GIVEKANAL` | 96% ✅ |
| FUN_004d1810 | `Geraet_sendeKom_27_MC_GIVESIGNALVERLAUF` | 96% ✅ |
| FUN_004c6ca0 | `Geraet_sendeKom_MC_GIVEDYNVALUES` | 95% ✅ |
| FUN_004acd20 | `Geraet_sendeKom_02_MC_GIVEGTYPE` | 95% ✅ |
| FUN_0040d2c0 | `Daten_sendeKom_GIVEKANAL_forTarget` | 90% 🔶 |

### MC3_ senders
| Address | Name |
|---|---|
| FUN_004ace30 | `Geraet3_sendeKom_03_MC3_GET_CB_VERSION` |
| FUN_004b1540 | `Geraet3_sendeKom_04_MC3_MERKMAL_INFO` |
| FUN_004b1da0 | `Geraet3_sendeKom_06_MC3_GERAETEREC` |
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

All 95% ✅ (tag-proven). MC3_ senders write sub-command at `data[2]`, payload from `data[3]`.

### Unit comm / framing
| Address | Name | Conf. |
|---|---|---|
| FUN_00686430 | `UnitComm_firstReceivedPaket` | 90% ✅ |
| FUN_00684160 | `UnitComm_assembleAnswer_MC` | 93% 🔶 |
| FUN_00685940 | `UnitComm_assembleAnswer_MC3` | 95% ✅ |
| FUN_00683e00 | `UnitComm_checkAnswerTimeout` (0/1/3/4) | 88% 🔶 |
| FUN_006823f0 | `UnitComm_deleteReceivedMessages` | 95% ✅ |
| FUN_00684030 | `UnitComm_clearRequestQueue` | 90% 🔶 |
| FUN_00682d20 | `UnitComm_receiveMonitoringData` (CAN streaming) | 90% 🔶 |
| FUN_00681f30 | `UnitComm_updateFeatureInfo` | 80% 🔶 |
| **FUN_004425c0** | **`promos3_checksum`** | **96% ✅ byte-verified** |
| FUN_00682010 | `canFrame_appendHex` (LEN@+5, DATA@+6) | 95% ✅ |

### Paket
| Address | Name | Conf. |
|---|---|---|
| 0x0042d190 | `MsgCreator_createPaketForCommand` | 96% ✅ |
| — | `MsgCreator_lookupCmdDescriptor` *(unread)* | — |
| FUN_00442650 | `Promos3Paket_ctorNull` | 92% 🔶 |
| FUN_00436470 | `Paket_getGroup` | 95% ✅ |
| FUN_00442430 | `Paket_getRouterKeyA` (= p+4) | 88% 🔶 |
| FUN_006796c0 / FUN_004423f0 | `Paket_getRecvSize` / `Paket_setRecvSize` | 92% 🔶 |
| FUN_00442450 | `Paket_getRecordSize` (+0x34) | 85% 🔶 |
| FUN_004429f0 | `Paket_setByteArray` (→ +0x20 aux) | 88% 🔶 |
| FUN_00442470 | `Paket_appendDataHex(str, maxBytes)` | 93% 🔶 |
| FUN_00442410 / FUN_00442400 | `Paket_getPriority` / `Paket_setPriority` (2 = front) | 85% 🔶 |

### Routing / threads
| Address | Name | Conf. |
|---|---|---|
| FUN_0042d960 | `KommandoVerteiler_enqueuePaket` | 90% ✅ |
| — | `Promos3KommandoVerteilerThread_run` (+0x0c in, +0x08 out) | 95% ✅ |
| FUN_004152c0 | `Router_dispatchInbound` | 95% ✅ |
| FUN_00415370 | `Router_routePaketOutbound` | 92% 🔶 |
| FUN_00415600 | `Promos3Router_instance` | 88% 🔶 |
| FUN_004156a0 | `Router_registerUnit` | 96% ✅ |
| FUN_0046a310 | `Promos3RouterObj_ctor(this, name, type)` | 85% 🔶 |
| 0x004125d0 | `Command_Dispatch_Switch` | 95% ✅ |
| FUN_00412290 | `DatenInstanz_handleGTypeAnswer` | 75% ⚠️ |
| FUN_0042e3b0 | `Promos3EthThread_instance(create)` | 94% ✅ |
| FUN_0042e780 | `Promos3CanThread_instance(create)` | 85% 🔶 |
| FUN_0042e230 / FUN_0042f070 | `EthThread_postPaket` / `CanThread_postPaket` (emit) | 86% 🔶 |
| FUN_0042ddc0 | `Promos3EthThread_initInterface` | 92% ✅ |

### Interfaces / transport
| Address | Name | Conf. |
|---|---|---|
| FUN_00443150 | `EthAbstract_setForSending_stub` (vtable idx 12 marker) | 96% ✅ |
| FUN_004fef00 | `EthInterface_setForSending` | 95% ✅ |
| FUN_004ff2c0 | `Promos3EthInterface_send` | 96% ✅ |
| FUN_005018f0 | `Promos2EthInterface_setForSending` ⚠️ *(was mislabelled CAN)* | 95% ✅ |
| FUN_00501e10 | `Promos2EthInterface_send` | 96% ✅ |
| FUN_00500970 | `EthInterface2_receiveData` | 92% ✅ |
| FUN_004fc540 | `EthInterface_onReadyRead` | 85% 🔶 |
| FUN_00446910 | `Interface_pumpSendQueues` (virtual +0x38) | 92% ✅ |
| FUN_00444860 | `Interface_clearSendQueues` | 88% 🔶 |
| FUN_00444090 | `Interface_setLastSentPaket` | 95% ✅ |
| FUN_00444020 | `Interface_getUnitSendStatus` | 88% 🔶 |
| FUN_00444910 | `Interface_getSendQueueForUnit` | 90% 🔶 |
| FUN_00556030 | `Promos3EthAbstract_qt_metacall` | 90% 🔶 |
| FUN_005559b0 | `Promos3TcpSocket_sendToUnit` | 96% ✅ |
| FUN_00554e30 | `Promos3TcpSocket_getStatus` | 96% ✅ |
| FUN_00554630 | `socketStateToString` | 95% ✅ |
| FUN_00554590 | `TcpSocket_readAllInto` | 90% 🔶 |
| FUN_00554d10 | `TcpSocket_resetTimer` | 85% 🔶 |
| FUN_00553310 | `SocketMap_getForUnit` | 90% 🔶 |
| FUN_004fd3a0 | `EthSocket_streamingDataReceived` | 94% ✅ |

### CAN interface
| Address | Name | Conf. |
|---|---|---|
| FUN_00505b00 / FUN_00505c60 | `Promos3CanInterface_ctor` / `_dtor` | 96% ✅ |
| FUN_00506d10 | `CanInterface_searchForNewUnits` | 96% ✅ |
| FUN_0042eed0 | `CanThread_onTimerTick` (3 ms loop) | 92% ✅ |
| **FUN_005073f0** | **`CanInterface_setForSending`** *(next target)* | 88% 🔶 |
| FUN_00508210 | `CanInterface_hasPendingSend` | 75% ⚠️ |
| FUN_00686770 / FUN_006867f0 | `CanInterface_qt_static_metacall` / `_qt_metacall` | 92% 🔶 |

### Helpers
| Address | Name | Conf. |
|---|---|---|
| FUN_00411650 | `QByteArray_setByteAt(idx, &val)` | 90% 🔶 |
| FUN_00490410 | `QByteArray_resize(n)` | 85% 🔶 |
| FUN_004315e0 | `QByteArray_assign` | 88% 🔶 |
| FUN_0042d800 | `QList_prepend` | 95% ✅ |
| FUN_00454930 | `QList_takeFirstPtr` | 90% 🔶 |
| FUN_00444830 | `QList_firstPtrRef` | 88% 🔶 |
| FUN_00611020 | `SKonfigRec_copy` / `memcpy3` | 65% ⚠️ |
| FUN_00654eb0 / FUN_00654ee0 | `Promos3DatenProvis2Error_ctor` | 85% 🔶 |

### App / DB / UI (non-protocol, named for completeness)
| Address | Name | Conf. |
|---|---|---|
| FUN_00421e10 | `GlobaleDaten_loadIniTables` | 88% 🔶 |
| FUN_0041b800 | `GlobaleDaten_isDownloadMode` | 88% 🔶 |
| FUN_00423370 | `MainWindow_setDownloadMode` | 80% 🔶 |
| FUN_00715220 | `UnitConfigWidget_setupUi` | 95% ✅ |
| FUN_005dfed0 | `SqlDb_updateFromOldVersion` | 95% ✅ |
| FUN_00463fb0 | `SqlDbManager_upgradeWPtoTrend` | 95% ✅ |
| FUN_006e0920 | `Promos2Download_onPushButton5Clicked` | 95% ✅ |
| FUN_004b9640 | `GetMerkmalInZykAnz` | 95% ✅ |
| FUN_00482090 | `getCurrentFeatureInCycleCount` | 95% ✅ |
| FUN_004adb90 | `GetPLCrec` | 95% ✅ |
| FUN_0047ee10 / FUN_0047ac60 / FUN_0047a7a0 | `Provis3Zyklus_assign` / `_dtor` / `_clear` | 90% 🔶 |

### Globals
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

### Ignore — Qt template guts
`FUN_005429d0` · `FUN_00407d40` · `FUN_00406d30` · `FUN_00406cf0` · `FUN_00408910` ·
`FUN_00407c00` · `FUN_00406bc0` · `FUN_00541e90` · `FUN_00541d20` · `FUN_005ace00` ·
`FUN_0042db20` · `FUN_00443710` · `FUN_00444350` · `FUN_00443f50`

---

# 11. Corrections to earlier report parts

1. ⚠️ **§2 / open item #1** — MC_ answers have no header. Closed by deletion, not by measurement.
2. ⚠️ **The `[group][command][length]` model describes MC3_**, not this box.
3. ⚠️ **`Paket+0x20` is aux context, not the wire buffer** (Part 16 §16.5 said otherwise).
4. ⚠️ **`Paket+0x30` is the station index**, not "aux".
5. ⚠️ **`FUN_005018f0` is Promos2**Eth**Interface, not the CAN interface** — corrected mid-session.
6. ⚠️ **`Promos3CanInterface` is not in the Eth vtable hierarchy** — plain QObject, metacall slots.
7. ⚠️ **There are three CAN-ID bases** (`0x500`, `0x580`, `0x600`), not one.
8. ✅ **§4.2 alarm layout confirmed** for MC3_ (subcommand at body offset 0, `0xFFFF` = all).
9. ✅ **§2.3 TPCANMsg layout confirmed** from code, not inferred.

---

# 12. Gap register status (vs Part 15)

| Gap | was | now | note |
|---|---|---|---|
| G1 header layout | 20% | **95%** ✅ | no header exists |
| G2 completion rule | 30% | **90%** ✅ | seq + 7B/frame + size table + checksum |
| G3 request side / master role | 0% | **75%** | request format, discovery, cadence all known; only the checksum-fill site missing |
| G4 capture strategy | 0% | **35%** | three ID bases found — the direction discriminator |
| G5 checksum | 0% | **90%** ✅ | recovered and byte-verified |
| G6 record versioning | 20% | 20% | `Geraet_getRecordVersion` still unread |
| G7 MC_ body layouts | ~15% | **~60%** | ~35/38 commands named; bodies still mostly undecoded |
| G8 limits / "%" | 60% | **70%** | alarm + station + field names recovered |
| G9 channelKey encoding | 60% | 60% | falls out of the first real capture |
| G10 unit ↔ serial ↔ model | 70% | 70% | |
| G11 device timestamps | 50% | 50% | |
| G12 reader robustness | 60% | 60% | **no code written this session** |

---

# 13. What to do next

## 13.1 Remaining RE — two functions, then stop

1. **`FUN_005073f0`** (`CanInterface_setForSending`) and whatever contains **`0x005090f5`**.
   One of them fills the trailing checksum, splits into `[seq][7 bytes]`, and picks which of the
   three ID bases to transmit on. That last part matters most: **it tells you which IDs to listen to.**
2. *(optional)* **`MsgCreator_lookupCmdDescriptor`** — the authoritative `{wireCmd, length, flags}`
   table for both generations; would verify the whole command list and give every request length.

## 13.2 The actual blocker — unchanged since Part 15

**No reader code has been written this session.** The transport layer still implements rules now
known to be wrong. Desk work, no machine needed:

```
DELETE  parse_message_header()                      — no such thing for MC_
DELETE  the "short frame ends message" heuristic    — provably corrupts (Part 15 §15.9)
ADD     per-unit request tracker {command, expectedSize, sentBytes, deadline, attempts}
ADD     frame layer: seq = DATA[0]; payload = DATA[1..LEN-2]; verify seq continuity
ADD     completion: accumulated == expectedSize (size table / 0x16 formula)
ADD     promos3_checksum() verbatim; checksum-only frame when expectedSize % 7 == 0
ADD     status codes 1=retry / 2=abort / 4=incomplete
FIX     CAN-ID handling: recognise 0x500 / 0x580 / 0x600 bases instead of dropping two of them
ADD     --record / --replay (~50 lines) — the highest-value tooling item
KEEP    the CONF_* honesty gating
```

`promos3_msg_t` loses `group`/`command` as *parsed* fields and gains them as *attributed* fields
plus a `bool attributed` that is false when no request was observed.

## 13.3 The decision still outstanding

**Passive or master?** Master remains the recommendation: MC_ answers are anonymous, so even a
passive reader must track requests and pair them — most of the master's work anyway. Passive
additionally needs a both-direction port mirror and only works while PROVIS3 runs. Master needs no
infra, and the request format, checksum, timeouts, discovery sequence and 3 ms cadence are all now
known. Cost: you must not poll a unit PROVIS3 is also polling.

## 13.4 Validation capture

`[ErrorManager] LogCANMessage = 1`, 60 seconds with the monitoring screen open. Its role has
changed from **discovery** to **validation**: confirm the seq/checksum framing against real bytes,
resolve `channelKey` encoding, and check a unit-2 request to double-confirm the station byte.

*End of Part 17.*
