# PROVIS3 / Prometec — **PART 18: SESSION REPORT**

Continues Part 17. Supersedes it where marked ⚠️ **CORRECTION**.

**Target system:** Mazak cell, Prometec PROVIS3, `Promos3DatenProvis2Geraet` (generation **1 = `MC_`**),
firmware Version **229 (0xE5)**, 1 channel, 4 sensors, GeraetTyp **0x44**, units **1–15**,
CAN-over-UDP gateway at **192.168.222.17:1789**.

**Question this part answers:** *what is left before the reader can talk to the device — and is
any of it still in the binary?*

**Headline.** No. The transmit path is now fully recovered, byte for byte. Every remaining
unknown is **device runtime state**, which no amount of decompilation can produce. The RE phase
is over.

---

# 1. Status

| Measure | Start of session | Now |
|---|---|---|
| Protocol knowledge | ~92% | **~99%** |
| Trustworthy live reader | ~45% | **~75%** *(link layer written + tested)* |
| Request wire format | specified | **byte-exact, verified twice** |
| Gateway TX record | unknown | **byte-exact** |
| CAN-ID base | 3 candidates | **settled: one** |
| Functions still worth reading | 2 | **0** |

---

# 2. Functions recovered this session

| Address | Name | Value |
|---|---|---|
| `FUN_00506220` | **`Promos3CanInterface::send`** | ⭐ the transmit tail — framing, checksum, CAN-ID |
| `FUN_00504290` | **`CanInterface_writeGatewayRecord`** | ⭐ the 36-byte TX record |
| `FUN_004d1310` | **`Sende_Kom_MC_GIVESAMMELMERKMALE`** | ⭐ the poll cycle |
| `FUN_005073f0` | `Promos3CanThread::sendCommandToUnit` | send queue + dedup |
| `FUN_00507360` | `Promos3CanThread::clearSendQueue` | drop-all on overflow |
| `FUN_0046a460` | `Promos3RouterObj::operator!=` | `{int type; QString name}` |
| `FUN_004c65d0` | `Sende_Kom_01_MC_GIVESTATUS` | no parameters, no recvSize |
| `FUN_004cd650` | `Sende_Kom_08_MC_GIVEPLCVALUES` | station param + size branch |
| `FUN_004ce000` | `Sende_Kom_35_MC_GIVE_SENSORVALUES` | round-robin sensor index |
| `FUN_004d1810` | `Sende_Kom_27_MC_GIVESIGNALVERLAUF` | 4 params, mode magic |
| `FUN_004d1de0` | `Sende_Kom_28_MC_GIVEOLDWORKPROZ` | |
| `FUN_004d23d0` | `Sende_Kom_31_MC_GIVEMUSTER` | packed nibble param |
| `FUN_004c7000` | `Sende_Kom_60_MC_GET_GERAET_ACF` | |
| `FUN_0040a620` | `Sende_Kom_P2_DOWNLOAD` | Paket ctor signature |
| `FUN_004ba490` | `Sende_Kom_99_MC3_DOWNLOAD` | group 2, N/A |
| `FUN_004abb20` | **`MonitorTypes_resolveName`** | ⭐ closes G10 |
| `FUN_004341f0` | `changePMDfromNC` | Mazak↔PMD bridge (write path) |
| `FUN_005206c0` | `Lade_Alles_aus_PMD_File` | SQL→memory, no wire |
| `FUN_005179c0` | `Lade_Kanal_aus_PMD_File` | SQL→memory, no wire |
| `FUN_00426100` | `GetCurrentPMD` | per-unit PMD name |
| `FUN_006da550` | settings-dialog builder | dead end (GUI) |
| `FUN_004be820` | `bearbeite_Kom_12_MC3_...` | wrong generation |

---

# 3. ⭐ The transmit path — complete

## 3.1 The gateway TX record (`FUN_00504290`) ✅

The one item that had been called "the empirical unknown". It is neither empirical nor unknown:

```
off       value              source
0x00-01   00 24              record length 36, BIG-ENDIAN
0x02-03   00 80              constant (type/flags)
0x04-14   00 ...             17 bytes of zero padding
0x15      LEN                TPCANMsg+5, CAN dlc
0x16-19   00 00 00 00
0x1A      (ID >> 8) & 0xFF   BIG-ENDIAN
0x1B       ID       & 0xFF
0x1C-23   DATA[0..7]         copied as two dwords
```

**The entire header is `00 24 00 80` followed by zeros.** `MSGTYPE` (TPCANMsg+4) is *not*
transmitted. Destination: `this+0x70` (QHostAddress) / `*(u16*)(this+0x18)` (port), i.e. the
INI's `GatewayAddress` / `GatewayPort`.

Structurally identical to the verified RX record — worth cross-checking that received records
also start `00 24 00 80`, which would confirm symmetry for free.

## 3.2 Request frame framing (`FUN_00506220`) ✅

```
first frame:      [00][00][00][ 5 payload bytes ]     LEN = 8
continuation N:   [seq][ up to 7 payload bytes  ]     LEN = 1 + chunk
```

The continuation counter pre-increments from 0, so the first continuation carries seq `1` and
the first frame's byte 0 is effectively seq `0` — symmetric with the answer direction.

⚠️ Bytes 1–2 of the first frame are written as zero and never assigned. Purpose unexplained.
The `DOWNLOAD` path reserves **2** bytes instead of 3 and prefixes a computed line count.

**MC3_ (group 2, command ≥ 3):** no reserved header, no seq, 8 payload bytes per frame.

**Worked example — the only request with independently known bytes:**

```
MC_GIVEPLCVALUES, unit 1, station 1
  Paket bytes : 08 01 f6                  (matches LogFile-260701-T1154)
  CAN-ID      : 0x501                     (1280 + 1)
  DATA        : 00 00 00 08 01 f6         LEN = 6
```

## 3.3 CAN-ID — ⚠️ **CORRECTION to Part 17 §11 item 7**

```c
local_1c = *(int *)((int)this + 0x48) + unit;
```

**One base, not three.** `this+0x48` is `BaseCanIDTransfer = 1280`. Transmit and receive use the
same base. Confirmed independently by the settings dialog (`FUN_006da550`), which exposes exactly
one "Base Tx" field — *"CAN transfer base address in hex"* — with First/Last unit described as
**offsets added to Base Tx**.

**G4 is closed.** Whatever `0x580` / `0x600` are, they are not transmit bases.

## 3.4 Checksum — confirmed a second time, independently ✅

`FUN_00506220` computes it inline, differently from `FUN_004425c0`:

```c
seed = (group == 0 || group == 1) ? unit - 1 : 0;
for each payload byte: seed += byte;
checksum = -1 - seed;                    /* one's complement */
append to the byte array
```

Algebraically identical to the Part 17 form: `-1 - (unit - 1 + Σ) = -(unit + Σ)`. Both yield
`0xF6` for unit 1. **Two independent code sites plus one log line.**

⚠️ The checksum is appended **before** framing, so on a long request it lands wherever the split
puts it — not at a fixed frame position.

## 3.5 Transmit retry ladder

| status | meaning |
|---|---|
| `0x80` | busy — retry up to `this+0x28` times, `QThread::wait(5)` between |
| `0x200` | CAN library or `CAN_Write` symbol missing |
| other | pass to `canApi_resolveAndCall("CanWrite", status)` |

Stale received frames are flushed **at send time** (`UnitComm_deleteReceivedMessages`), not on
receive. Gateway mode is `this+0x14 > 0`; socket must be in state 4 (`BoundState`).

---

# 4. ⭐ The poll cycle (`FUN_004d1310`)

`Sende_Kom_MC_GIVESAMMELMERKMALE` does not send one command. It sends the whole cycle:

```
gate: this+0x28 == 0

for station = 1 .. channelCount:      send 0x16   MC_GIVESAMMELMERKMALE   (priority 2)
for station = 1 .. channelCount:      send 0x08   MC_GIVEPLCVALUES        (via FUN_004cd650)
send 0x01                             MC_GIVESTATUS                       (via FUN_004c65d0)
```

Stations already present in `traceMap` with a live node are skipped for `0x16`.

**Corroborated by the dedup filter** in `Promos3CanThread::sendCommandToUnit`, which suppresses
duplicate queue entries only for group 1 and only for commands **`0x16`, `0x08`, `0x01`, `0x12`** —
i.e. exactly the periodically re-issued set:

| cmd | name |
|---|---|
| `0x01` | `MC_GIVESTATUS` |
| `0x08` | `MC_GIVEPLCVALUES` |
| `0x12` | `MC_GIVEALARM` |
| `0x16` | `MC_GIVESAMMELMERKMALE` — the live measurement block |

Dedup key = (routerKeyA, `Paket+0x30` station, `Paket+0x28` command).

## 4.1 The `0x16` stride — now a constant

```c
recvSize   = featureCount * 2 + 2;          /* Geraet+0x480 */
recordSize = featureCount * 2 + 2;          /* Paket+0x34   */
if (Geraet_getGeraetTyp() == 'H') both += 2;
```

GeraetTyp is compared **as an ASCII char**: `0x44 = 'D'`, `0x48 = 'H'`. This box is `'D'`.

**4 features → stride 10.** Combined with the Part 17 completion rule
(`expected = data[0] * recordSize + 1`), the live block resolves to `rows * 10 + 1`, and the
Part 17 §8 "+4 variant" is identified as the `'H'` branch.

## 4.2 Request byte layouts (six senders, cross-checked)

Qt4 places `QByteArray::Data` payload at `+0x10`, so `*(data + 0x11)` is wire byte 1.

| cmd | byte 1 | byte 2 | byte 3 | byte 4 |
|---|---|---|---|---|
| `0x01` GIVESTATUS | — | — | — | — |
| `0x08` GIVEPLCVALUES | station | — | — | — |
| `0x16` GIVESAMMELMERKMALE | station | `this+0x688 ? 1 : 0` | — | — |
| `0x1b` GIVESIGNALVERLAUF | station | feature | p3 | p4 |
| `0x1c` GIVEOLDWORKPROZ | station | p3 | — | — |
| `0x1f` GIVEMUSTER | station | p3 | `(p4 & 0x0F) \| (p5 << 4)` | 0 |

`0x23` GIVE_SENSORVALUES carries a round-robin slot index (`Geraet+0x60`) scanning
`Geraet+0x4d0..` — slots 0–3 = features, 4–11 = sensors.

## 4.3 Send queue behaviour

- `Promos3CanThread` outgoing queue at `this+8`, `QList<Promos3Paket*>`
- **cap 400; on overflow the entire queue is deleted**, not trimmed
- routerKeyA is a QString; the literal `"DOWNLOAD"` is a reserved target that bypasses dedup
- ownership of the Paket transfers to the queue; a dedup hit `delete`s the incoming packet

---

# 5. ⭐ G10 closed — the model string (`FUN_004abb20`)

```c
key   = "0x" + hex(GType);          /* falls back to bare hex on miss */
value = ini["MonitorTypes"][key];
list  = value.split(",");
idx   = GSubType - 1;               /* <<<< 1-BASED */
name  = (0 <= idx < list.size()) ? list[idx] : "Unknown";
```

**The index is 1-based.** For `[MonitorTypes] 0x44` with GSubType 5 → list index 4 →

> **`MSL5081-16`**

Part 15 listed both candidates; this settles it. Report open item #2 is **closed**.

---

# 6. Object layout confirmations

`SGeraetRec` lives inside the Geraet object at `+0x4BA` (66 bytes, seen copied wholesale in
`FUN_005206c0`):

| off | field | cross-check |
|---|---|---|
| `+0x4BA` | GeraetTyp | literal `== 0x48` test |
| `+0x4BB` | GSubType | passed to `FUN_004abb20` |
| `+0x4BC` | **channel count** | loop bound in `FUN_004d1310` |
| `+0x4BD` | **sensor count** | `1974.txt`: `44 05 01 04` ✓ |

⚠️ **CORRECTION.** Part 17 and the first draft of the reader called `+0x4BC` a *station* count.
It is the **channel** count. Behaviourally identical on this box (1 of each) but the label was wrong.

`MiSensType[]` is copied only for the first `sensorCount` entries — the array is 8 long, only 4
are meaningful here. The PMD parser should do the same.

`Promos3Paket_ctor(mem, group, srcRouterObj, dstRouterObj, QByteArray, 0, 1)` — recovered from
`FUN_0040a620`, closing the Part 16 §16.11 open item on the outbound path. Setting
`Paket[10] = 0xFFFFFFFF` marks a raw/no-command packet.

---

# 7. ⚠️ Corrections to Part 17

1. **`FUN_005073f0` is not the frame splitter.** It is `Promos3CanThread::sendCommandToUnit`, a
   queue enqueue with de-duplication. The splitter is `FUN_00506220`.
2. **There is one CAN-ID base, not three** (§3.3).
3. **`Geraet+0x4BC` is channels, not stations** (§6).
4. **`FUN_005206c0` / `FUN_005179c0` send nothing over CAN.** Predicted to reveal the multi-frame
   request split; they are SQL→memory config loaders with no protocol content.
5. **`0x01 MC_GIVESTATUS` never calls `Paket_setRecvSize`** — its expected answer size comes from
   `createPaketForCommand` defaults and is *not* known. It is therefore a **poor first probe**;
   use `0x08`, whose exact request bytes are verified from the log.

---

# 8. Code written this session

All compiled clean at `-Wall -Wextra`.

| File | Contents |
|---|---|
| `promos3_master.h` / `.c` | MC_ master link layer: checksum, request builder, frame layer, completion rule, per-unit request tracker, poll cycle, retry ladder, counters, RX record split |
| `test_master.c` | 20 assertions, **all passing** |
| `promos3_learn.c` | probe/measure harness — *now largely obsolete, see §10* |

## 8.1 What the tests prove

- checksum reproduces `0xF6` / `0xF5` / `0xF4` for units 1/2/3 — the only real protocol bytes on hand
- `mc_build_request()` emits `08 01 f6`, byte-identical to the log
- the **64-byte message that silently corrupted the old transport** (Part 15 §15.9 cases B/C)
  now completes exactly and does not consume the following message
- both checksum placements work: tail byte, and the lone `[seq][ck]` frame when `expected % 7 == 0`
- poll cycle emits `0x16, 0x16, 0x08, 0x08, 0x01` for a 2-channel unit
- bad sequence and bad checksum are counted, not swallowed
- timeout ladder: one resend at 300 ms, abort at 600 ms

## 8.2 A real bug the code found that the RE did not

The documented device-error signature `DATA[0] == 0 && DATA[1] == 1` is **identical to a healthy
first data frame whose first payload byte is 1** — which for `0x16` means "one row", the most
common case there is. As originally written, the reader would have discarded most live
measurement data and counted it as device errors.

Constrained to `f->len == 2` (seq + status and nothing else). Marked in the source as an
assumption to confirm against a real capture.

## 8.3 Still to change in the reader

```
DELETE  parse_message_header()                   — no such thing for MC_
DELETE  the "short frame ends message" heuristic — provably corrupts
PATCH   gw_build_record(): header = 00 24 00 80, rest zero
PATCH   request framing: [00][00][00][5 payload] then [seq][7]
PATCH   single CAN-ID base; delete the 3-base probe dimension
WIRE    master_* into main.c as a --master mode
ADD     --record / --replay
KEEP    the CONF_* honesty gating
```

---

# 9. Gap register

| Gap | Part 17 | Now | Note |
|---|---|---|---|
| G1 header layout | 95% | **100%** ✅ | no header exists |
| G2 completion rule | 90% | **100%** ✅ | verified in code + tests |
| G3 request side | 75% | **100%** ✅ | framing, checksum, poll cycle, cadence |
| G4 capture strategy / ID base | 35% | **100%** ✅ | one base; master mode needs no capture |
| G5 checksum | 90% | **100%** ✅ | two independent code sites |
| G6 record versioning | 20% | 20% | `Geraet_getRecordVersion` still unread — low value |
| G7 MC_ body layouts | ~60% | ~65% | `0x16` stride now exact |
| G8 limits / "%" | 70% | 70% | |
| G9 channelKey encoding | 60% | 60% | MC3_ packs cycle in low 12 bits, channel in high 4 — *hint only, wrong generation* |
| G10 model string | 70% | **100%** ✅ | 1-based → `MSL5081-16` |
| G11 device timestamps | 50% | 50% | |
| G12 reader robustness | 60% | **80%** | link layer written and tested; no `--record`/`--replay` yet |

---

# 10. What remains — and why Ghidra cannot supply it

Two items. Both are **device runtime state**, not code.

### D3 — real expected answer sizes for `0x01`, `0x12`, `0x1b`

The Part 17 size table is authoritative for `0x02` (14) and `0x0e` (144, call-site verified).
The values currently used for `0x01`, `0x12` and `0x1b` are **guesses**. `0x12` was mapped to the
table's `0x11` entry, which is `ALARMGESEHEN`, not `GIVEALARM` — probably wrong. `0x1b`'s 257
comes from a *synthetic* Part 15 test, not real bytes.

### D4 — the `0x08` size branch

```c
if (version < 0xD6 || Geraet[0x4e6] == 0)
     n = base + (GType=='D'||'H' ? 1 : 0) + (traceMapNode(station)==4 ? 1 : 0);
else n = (Geraet[0x4e6] >> 4) + (Geraet[0x4e6] & 0x0F);
```

Version is `0xE5`, so **if `Geraet+0x4e6` is nonzero the nibble branch applies** and the current
value is wrong. That byte arrives from config at runtime. It is not in the executable.

### Minor open assumptions

- answer-direction checksum seed assumed symmetric with the request (verified for requests only)
- device-error `len == 2` constraint is inference (§8.2)
- `Geraet+0x688` (the `0x16` byte-2 flag) — sent as 0, meaning unknown
- the 3 reserved bytes at the head of the first request frame — purpose unexplained
- `Paket_setPriority(…, 2)` — a priority queue exists and is ignored (harmless with one
  outstanding request)
- requests > 7 payload bytes need splitting; irrelevant for the read-only poll set (all ≤ 4)

**Every size doubt degrades into a timeout, not corruption.** The tracker catches it, the counters
record it, and nothing reaches the xlsx as a plausible-looking lie. That is what the `CONF_*`
gating was for.

---

# 11. What to do next

## 11.1 One 30-second test

Form this request and send it to `192.168.222.17:1789`:

```
36-byte record:
  00 24 00 80 00 00 00 00 00 00 00 00 00 00 00 00
  00 00 00 00 00 06 00 00 00 00 05 01 00 00 00 08
  01 f6 00 00
                 ^ dlc 6      ^ CAN-ID 0x501   ^ DATA
```

If anything comes back, everything else follows. If nothing does, that is a real result no
decompiler was going to give.

## 11.2 Then measure the sizes

For each of `0x01`, `0x02`, `0x06`, `0x08`, `0x0e`, `0x12`, `0x16`: send, accept frames until the
bus is quiet for 300 ms, record the payload byte total. That is the real size table, measured.
Closes D3 and D4 together, and validates the answer-direction checksum as a side effect.

⚠️ **Do not poll a unit PROVIS3 is also polling.** Stop it, or aim at a different unit.
Collision symptom: `"Trying to send several Canbus commands before answer is received"`.

## 11.3 If machine access is not available

Then the priority inverts, and none of §11.1–11.2 applies. Build instead:

1. `--replay` against synthetic datagrams, so the decode path can be developed at a desk
2. the confirmed constants wired in, so the tool is ready the day access happens
3. this document, handed to whoever does have access

## 11.4 Do not read more Ghidra

Protocol knowledge is ~99%. The transmit path is byte-exact. The remaining 1% is device state.
Eleven functions this session moved knowledge 92% → 99% and the *reader* 45% → 75%, and the
75% came from writing code, not from reading functions. The next byte of useful information has
to come from the machine.

*End of Part 18.*
