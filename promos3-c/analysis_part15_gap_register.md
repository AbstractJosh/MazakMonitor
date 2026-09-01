# PROVIS3 / Prometec — **PART 15: GAP REGISTER** (addendum to report v2 + Appendix A/B)

**Question this part answers:** *what is still missing before the reader can receive UDP
from the gateway and display it correctly, 100% of the time?*

**Method.** Every source in the project tab was re-read: the v2 report, Appendix A
(datamodel) and Appendix B (function recovery), the reader source (`main.c`,
`promos3_{transport,decode,proto,state,config}.c`, `span.h`, `xlsx.c`), `PROVISsettings.ini`,
the five runtime logs, the PMD exports (`1974.txt`, `exVL2-*`), and `mazak_strings.txt`.
The reader was then **compiled and driven with synthetic gateway datagrams** to see which
failures are real rather than theoretical. Results are in §15.9.

Gaps are marked `<!>` and numbered `G1…G13`. Each carries a **completion %** = how much of
that item is already in hand (100% = nothing left to do).

> **Headline.** Protocol *knowledge* is ~78% complete. A *working, trustworthy live reader*
> is ~45% complete. The distance between those two numbers is almost entirely four items:
> **G1, G2, G3, G4** — and three of them were previously recorded as "non-blocking".
> They are blocking.

---

## 15.0 Two new hard facts found this pass (not in v2)

Both come from the runtime logs, which had not been mined for wire bytes:

**(a) Real request frames exist in the logs.** `waitingForData` prints the frame the app
sent when an answer times out. Two samples across the five logs:

```
01.07.26 11:54:38.074  waitingForData:  requested  0x0c, 0x01, 0x61, 0xff, 0xff, 0xff, 0x00, 0x00,
01.07.26 12:08:42.060  waitingForData:  requested  0x08, 0x01, 0xf6,
```

Read against the group-1 dispatch table: **byte 0 = command** (`0x0c` and `0x08` are both
real MC_ commands), **byte 1 = 0x01 in both = channel** (this box has exactly 1 channel),
rest = parameters, `0xFF` = "not specified". Frame length is **variable, 3–8 bytes** — a
request is a *single* CAN frame.

⚠️ Implication: **there is no `group` byte on the wire.** `group` at msg+0x00 is set by the
parser from the unit's registered generation (`getTargetType`), not read from the packet.
This directly contradicts the placeholder layout in `parse_message_header()`.

**(b) The link is master/slave polled, not push.** `[CAN] unitAnswerTimeout=300`,
`[Comm] MaxResend=1`; strings `"Trying to send several Canbus commands before answer is
received, last command %1 new command %2"`, `"-CAN: Received data without request"`,
`"answer timedout, received"`, `add_requestedMessage`, `m_requestedMessages`. The logs show
`searchForNewUnits → registerUnit → bearbeite_Kom_06_MC_GIVEKONFIG` in a fixed 20–40 ms
sequence, then `"unit N detected as not active, will be removed"` when polling stops.

⚠️ Implication: **an idle bus carries nothing.** A passive reader on a machine where PROVIS3
is not polling will sit silent forever and look "broken" when it is working perfectly.

---

# ═══════════════════════════════════════════════════════════
# 15.1 `<!> G1 — Message header wire layout` — **20% · BLOCKER**
# ═══════════════════════════════════════════════════════════

**State.** `promos3_decode.c :: parse_message_header()` assumes
`+0x00 u8 group | +0x01 u8 command | +0x02 u16 len | +0x04 body`. That was an explicit
placeholder ("EDIT ME"), and §15.0(a) now says it is **probably wrong in both fields**.

**What the evidence supports instead** (⚠️ INFERRED, one capture from confirmation):

```c
/* hypothesis H1 — matches the two logged request frames */
+0x00  u8   command        /* 0x06, 0x08, 0x0c, 0x1b … */
+0x01  u8   channel        /* 1-based; 0xFF = none/all  */
+0x02  …    params / body
/* group is NOT on the wire — take it from the unit's generation (1 = MC_ here) */
```

**Why it is a blocker, not cosmetic.** Under the current code a real answer starting
`1B 01 …` fails the sanity gate (`g > GROUP_MC3`) and prints `[UNPARSED HEADER]` — loud and
safe. But answers to commands `0x00/0x01/0x02` **pass** the gate and are decoded as a
different command entirely. Partly-loud, partly-silent corruption.

**How to close.** `PROVISsettings.ini → [ErrorManager] LogCANMessage=1` (currently `0`), run
60 s, read the raw frames out of the log. Anchor: the KONFIG answer must contain
`E5 01 04` (Version 229, Channels 1, Sensors 4) — that single line pins command position,
channel position and body start at once. **Effort: one afternoon, no hardware.**

---

# ═══════════════════════════════════════════════════════════
# 15.2 `<!> G2 — Reassembly completion rule + expected-length table` — **30% · BLOCKER**
# ═══════════════════════════════════════════════════════════

**State.** `reasm_expected_len()` returns 0 and the code falls back to *"a frame shorter than
8 bytes ends the message"*. **This is provably wrong** — see the live test in §15.9:

- a message whose total length is a multiple of 8 **never completes** (≈12.5% of all lengths);
- the stuck buffer then **swallows the next message** and reports it with the *previous*
  message's command and a wrong length. Silent, plausible-looking garbage — the worst failure
  mode a reader can have.

**What is missing.** The app does not trust the wire either — it knows the expected size
**per command, from a table**:

- `FUN_004c5840(this, komNumber)` → expected byte count. Seen in `bearbeite_Kom_14`:
  `iVar6 = FUN_004c5840(this,0xe); if (*(int*)(*piVar7+8) == iVar6) { …decode… } else
  { "Wrong amount of channels in SNr %1" }`.
- String `"Wrong number of bytes for command %1, copiedBytes: %2 of %3"` — same idea, generic.
- `unitBuffer_appendCanData` keeps **two** sub-streams: `+0x08` header/len and `+0x0c` data —
  consistent with **frame 1 = header (cmd, channel, len/params), frames 2..N = data**.

**Deliverables needed:**
1. **`FUN_004c5840` decompiled** → the per-command expected-size table (`MC_` group). *This
   is the single highest-value function still un-analysed.*
2. `unitBuffer_hasCompleteMessage` (`FUN_00682830`) re-read for where the length lives.
3. **A per-unit reassembly timeout** (the app restarts a timer on the first frame; the reader
   has none). Without it a single lost UDP datagram desynchronises that unit *permanently*.

---

# ═══════════════════════════════════════════════════════════
# 15.3 `<!> G3 — Nobody is polling: the request side` — **0% · BLOCKER**
# ═══════════════════════════════════════════════════════════

The report's model is "device → app". §15.0(b) shows it is **request → answer**, one
outstanding command at a time, 300 ms timeout, 1 resend. Consequences:

| Deployment | Works? | What is still missing |
|---|---|---|
| PROVIS3 runs and polls; reader listens | data flows | a way to *see* it → **G4** |
| PROVIS3 stopped; reader listens only | **silent forever** | the whole request side |
| Reader replaces PROVIS3 | needs the full master role | request framing, unit discovery, poll loop |

**Missing pieces for the master role** (if you choose that route):
- request frame format — **partly known**, two real samples in §15.0(a);
- the unit-discovery handshake (`searchForNewUnits` → broadcast/scan of units 1..15 →
  `registerUnit` → `MC_GIVEGTYPE` → `MC_GIVEKONFIG`);
- the poll schedule (which command, how often — `[User Interface] PlotRefreshTime=100`,
  `PlotInterval=2000` are the display-side hints);
- one-outstanding-request discipline + `unitAnswerTimeout=300` + `MaxResend=1`;
- **the checksum**, because a master must validate and re-request → **G5**.

**Decision required before any more code is written.** Passive observer (needs G4) or active
master (needs G3+G5)? The report's ADR-0004 chose *read-only observer* — that choice is only
viable if PROVIS3 keeps running, which makes G4 mandatory.

---

# ═══════════════════════════════════════════════════════════
# 15.4 `<!> G4 — You cannot receive a unicast stream twice` — **0% · BLOCKER**
# ═══════════════════════════════════════════════════════════

The gateway traffic is **unicast UDP** between the PROVIS3 host and `192.168.222.17:1789`,
and the app **binds the port itself** (`"UDP Gateway Socket bound"` /
`"UDP Gateway Socket Not bound at: %1"`). `main.c` binds `INADDR_ANY:1789`. On the same host,
with PROVIS3 running, **one of the two gets the datagrams — not both** (`SO_REUSEADDR` does
not duplicate unicast delivery).

**Options, none of them currently in the code:**
1. **Switch-port mirror / SPAN** to a second NIC, read promiscuously *(needs pcap → the
   report retired `promos3_sniff.c`; it may need to come back)*;
2. **run instead of PROVIS3** (→ G3, master role);
3. ask the gateway to also send to a second endpoint (unknown whether it can — undocumented).

**Also missing in `main.c` regardless of option:**
- **no source-address filter** — anything arriving on :1789 is parsed as gateway data;
- **no direction filter** — on a mirror you see the app's *requests* too. Requests are also
  36-byte records with valid CAN-IDs, so they will be fed into the same per-unit buffer and
  **corrupt reassembly**. Needs `if (src_ip != GatewayAddress) skip;` plus a request/answer
  discriminator (likely the CAN-ID: `base+unit` for one direction, a different offset for the
  other — *unconfirmed, one capture answers it*).

---

# ═══════════════════════════════════════════════════════════
# 15.5 `<!> G5 — The checksum layer is entirely absent` — **0%**
# ═══════════════════════════════════════════════════════════

The reader has no integrity check at all. The binary has a whole subsystem:

```
CheckSum error, ID %1 comm %2 feature %3 Received data %4
Wrong checksum for unit %1 command %2, try again
Wrong checksum after several attempts for unit %1 command %2, aborting
Error, expected Checksum-only message was not received for command %1
Accumulated errors in answer for command %1. Wrong checkSumOK, received %2, expected %3
CheckSum fail for Receive Size zero in command %1, try again
Checksum error! resend from %1
```

Facts these give for free: the checksum is **per command/answer**; there is a
**"checksum-only message"** (a separate frame carrying just the checksum — a reader that does
not know this will treat it as a truncated data message); failures are **retried then
aborted**; `Checksum error! resend from %1` implies **resume-from-offset** on the download
path.

**Missing:** the algorithm (sum? XOR? one's complement?), its position, and the checksum-only
frame's shape. *Weak hint:* in the 3-byte request `08 01 F6`, `0xF6 = ~(0x08+0x01)` — a
one's-complement byte sum fits that one sample but **not** the 8-byte sample, so treat it as
untested, not as a finding.

---

# ═══════════════════════════════════════════════════════════
# 15.6 `<!> G6…G11 — decode & display gaps` (non-blocking, quality)
# ═══════════════════════════════════════════════════════════

### `<!> G6 — Record-layout versioning` — **20%**
Every handler calls `FUN_004c5c70(this, &v)` **before** parsing and passes `v` into the record
parsers. Record names are version-stamped (`SKanalRec**V40**`, `SZykRec**V4802**`) and this
box reports **Version 229**. So layouts are version-selected and the reader hardcodes exactly
one variant. **Needed:** decompile `FUN_004c5c70` + the version→layout switch. Until then the
reader is correct *only* for firmware `Rtm_V14.5.H86 / Version 229`.

### `<!> G7 — MC_ (group-1) body layouts` — **~15%**
38 group-1 commands are located; **3 are named** (`0x06`, `0x15`, `0x1B`) and **1 body is
confirmed** (`0x1B` trace). `promos3_proto.c` labels the other 35 `MC_cmd_NN`. The alarm
layout in Part 4.2 is **MC3_-derived** and correctly flagged `CONF_PROVISIONAL` — meaning the
reader will show alarms as a hexdump, not as alarms. For a display that matches the app you
minimally need the MC_ variants of: **alarm/status**, **cycle start/end**, and whatever
carries the tool/cycle context (candidates: `0x0c`, `0x0d`, `0x29`).

### `<!> G8 — Limits / the "%" display` — **60%**
Part 5 says on-screen % = `raw / limitLevel × 100`. The limit levels are parsed
(`parse_zyklus`, `zyklus_feature_level`) — but **`reader_apply_pmd()` only loads `SGeraetRec`
and `SKanalRecV40`**; cycles/limits are never loaded into `reader_state_t`, and nothing
computes %. The bar chart can be drawn; the limit line and the alarm colour cannot.

### `<!> G9 — Trace → feature mapping` — **60%**
`key_to_index()` accepts *three* encodings (mask `1/2/4/8`, flagged `0x81/0x82/…`, plain index
`0..3`) because it is unknown which one `channelKey` actually uses. That ambiguity resolves
itself on the first real trace — but until then a wrong guess mislabels every plotted bar,
and this box's labels are operator-assigned Turkish/German shop labels
(`VIBRATION / M131 DEBI / M131BASINC / M08 DEBI`), so a wrong label looks plausible.

### `<!> G10 — Unit ↔ serial ↔ model identity` — **70%**
The reader prints `unit 1`. The app prints `Unit 1 Type 68 SubType 5 SNr 10659`. The serial
arrives via the GIVEGTYPE/registerUnit path, which is not decoded. **Model string is now
resolvable from `[MonitorTypes] 0x44`:** GSubType 5 → `MSL5082-16` (0-based) or `MSL5081-16`
(1-based). Report open item #2 is therefore **50% closed — only the index base is unknown.**

### `<!> G11 — Device-side timestamps** — **50%**
The reader stamps rows with *its own* clock at print time. The app reads a `QDateTime` out of
the alarm record (`FUN_00626960`) and stores `Alarms.TimeOffset` relative to cycle start.
Under load, host-clock stamping will misorder events against the machine's own log.

---

# ═══════════════════════════════════════════════════════════
# 15.7 `<!> G12 — Operational robustness of the reader itself` — **60%**
# ═══════════════════════════════════════════════════════════

Found by reading and running the code:

| Item | State | Fix |
|---|---|---|
| Reassembly timeout | **absent** | per-unit deadline; flush + count on expiry (app does this) |
| Lost-frame recovery | **absent** | after G2, resync on the next header frame |
| Counters (dropped / bad-checksum / unparsed) | only `unparsed_count` | add + print on exit |
| xlsx durability | all rows held in RAM, written **only** on clean exit | flush periodically, or append CSV and convert later |
| xlsx memory | unbounded growth on a long run | same |
| **Offline replay** | **absent** | see below |

**`<!> The highest-value missing tool: record & replay.** There is no way to save raw
datagrams and re-run the decoder against them. Every calibration attempt therefore needs the
live machine. Add `--record FILE` (dump raw datagrams + timestamps) and `--replay FILE`
(feed them back through the same path). This turns G1/G2/G5 from "book a machine window"
into "iterate at a desk", and it is ~50 lines.

---

# ═══════════════════════════════════════════════════════════
# 15.8 `<!> G13 — What is NOT missing` (so nobody re-does it)
# ═══════════════════════════════════════════════════════════

✅ Gateway record split, CAN-ID big-endian, `unit = ID − 1280` — verified, and the reader
implements the front-trim exactly as `Scan4CANmsg` does.
✅ Payload little-endian; **no scaling factor** (raw 0–255) — verified against two databases.
✅ Config records (`SGeraetRec`, `SKanalRecV40`, `SZykRecV4802`, `SGrenzRec`) and the PMD
parser — byte-for-byte against `1974.txt`; the `--config-unit` path works.
✅ Decoder rings (ToolStatus, SensorType, alarm slot names) and the DB schemas.
✅ Dispatch map (~70 handlers), MC3_ registry, MC3_ per-command field descriptors (App. B.3).
✅ The reader's **honesty design** — `CONF_UNKNOWN/NAMED/PROVISIONAL/CONFIRMED` gating means
it hexdumps anything it cannot prove. Keep this; it is why G1's damage is mostly loud.

---

# ═══════════════════════════════════════════════════════════
# 15.9 Test evidence (reader compiled and driven, this session)
# ═══════════════════════════════════════════════════════════

Synthetic gateway datagrams fed through `gw_parse_record → reasm_feed → parse_message_header
→ print_message`:

```
A: 261-byte message (33 frames, last=5B)
   -> completed=1 parsed=1 cmd=0x1B body_len=257
   Unit 1   | MC_GIVESIGNALVERLAUF | len 257 | confirmed
            | M131 DEBI | 125 samples raw 0..248        <-- happy path OK

B: 64-byte message (exact multiple of 8)
   -> completed=0                                       <-- NEVER completes  (G2)

C: next 20-byte message on the same unit
   -> completed=1 raw_len=84 cmd=0x06                   <-- ate B's bytes,
                                                             reported B's command (G2)

D: CAN-ID 1000  -> unit=-280 (dropped, correct)
   CAN-ID 1480  -> unit=200  (dropped, correct)
```

Compiles clean at `-Wall -Wextra`. The pipeline is sound; the **rules** it is fed are not.

---

# ═══════════════════════════════════════════════════════════
# 15.10 Scoreboard
# ═══════════════════════════════════════════════════════════

| # | Gap | % done | Blocks live reading? | Effort |
|---|---|---|---|---|
| G1 | Message header wire layout | 20% | **YES** | 1 capture |
| G2 | Completion rule + expected-length table (`FUN_004c5840`) | 30% | **YES** | 1 capture + 1 decompile |
| G3 | Request/answer master role (or a live PROVIS3) | 0% | **YES** | design decision first |
| G4 | Getting a copy of a unicast stream (+ src/direction filter) | 0% | **YES** | infra decision |
| G5 | Checksum + checksum-only frames | 0% | for a master | 1 capture |
| G6 | Record-layout versioning (`FUN_004c5c70`) | 20% | no | 1 decompile |
| G7 | MC_ group-1 body layouts (3/38 named, 1 body confirmed) | ~15% | no | per-command |
| G8 | Limits loaded + "%" computed | 60% | no | ~1 day |
| G9 | `channelKey` → feature index encoding | 60% | no | falls out of G1 |
| G10 | Unit ↔ serial ↔ model string | 70% | no | trivial + index base |
| G11 | Device-side timestamps | 50% | no | with G7 |
| G12 | Timeouts, counters, xlsx durability, **record/replay** | 60% | no | ~1 day |

**Aggregate**

| Measure | % |
|---|---|
| Protocol *knowledge* (transport + config + DB + dispatch) | **≈78%** |
| Live *reader* that is correct and trustworthy end-to-end | **≈45%** |
| Live reader correct for **just** the trace `0x1B` on **this** firmware, given G1+G2 fixed and a working feed | **≈85%** |

---

# ═══════════════════════════════════════════════════════════
# 15.11 The one action that unblocks the most
# ═══════════════════════════════════════════════════════════

```ini
; PROVISsettings.ini
[ErrorManager]
LogCANMessage = 1        ; currently 0
```

Run PROVIS3 against the machine for 60 seconds with the monitoring screen open, then take the
log. That single artefact closes **G1** (header offsets, anchored on `E5 01 04`), **G2**
(where the length lives / whether frame 1 is a header), **G5** (checksum shape and the
checksum-only frame), and gives the answer/request CAN-ID split needed for **G4** — with no
Wireshark, no PEAK card, no admin rights.

Do that **before** writing any more decoder code. Every remaining item is either downstream
of it or independent of it.

*End of Part 15.*
