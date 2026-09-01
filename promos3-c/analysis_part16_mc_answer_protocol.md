# PROVIS3 / Prometec — **PART 16: THE `MC_` ANSWER PROTOCOL, RESOLVED** ✅

**Source:** `FUN_00684160` (the `MC_`/group-0,1 answer assembler), plus `FUN_004425c0`
(checksum), `FUN_00442650` (Paket ctor), `FUN_004c5840` (expected-size table),
`FUN_00686430` / `FUN_00683e00` (arbiter/timeout).

**Status change:** Part 15 gaps **G1 (header layout)**, **G2 (completion rule)** and
**G5 (checksum)** are now **closed at the specification level** — but G1 closes by being
*inverted*, and that inversion makes **G3/G4 harder, not easier**. Read §16.6 before writing
code.

---

## 16.1 The headline: **answers carry no command and no group**

At the end of `FUN_00684160`, the completed message object is built like this:

```c
group   = Paket_getGroup(requestPaket);          // FUN_00436470 = *(u32*)request
newMsg  = Promos3Paket_ctor(new(0x50), group, routerA, routerB, &assembledBytes, 0, 0);
newMsg[10] = local_13c;        // +0x28 = command  <-- copied from the REQUEST
newMsg[11] = requestPaket[11]; // +0x2c
newMsg[12] = requestPaket[12]; // +0x30
```

where `local_13c = requestPaket[10]` — i.e. the command of the **request**, read at the top
of the function *before any answer byte is touched*.

> **`group` and `command` at msg+0x00 / msg+0x28 are inherited from the outstanding request.
> They are never parsed off the wire. The answer payload is pure record bytes.**

This retires the v2 open item "exact wire byte-offsets of `[group]/[command]/[length]`" —
**those fields do not exist on the wire.** It also retires `parse_message_header()` in the
reader: there is nothing to parse.

**Consequence:** a message is only identifiable *in the context of the request it answers*.
A listener that sees only the device→app direction sees anonymous byte blobs. This is the
single most important design fact in the whole project.

---

## 16.2 CAN answer frame layout (the real framing) ✅

Every answer frame is a `TPCANMsg` (`{u32 ID; u8 MSGTYPE; u8 LEN; u8 DATA[8]}`; LEN at `+5`,
DATA at `+6` — confirmed in §15 via `FUN_00682010`). Inside `DATA`:

```
DATA[0]           = sequence number, starts at 0, +1 per frame of this answer
DATA[1 .. LEN-2]  = payload bytes                       (up to 7 per frame)
DATA[LEN-1]       = checksum  — ONLY on the final frame, and only if it fits
```

Proof, straight out of the loop:

```c
uVar17 += (byte)frame[5] - 1;                 // usable bytes per frame = LEN-1
...
local_140++;                                   // starts at -1 -> first expected seq = 0
if ((byte)frame[6] != local_140) -> "Unknown answer format received on CAN bus for command %1"
...
avail = frame[5] - 1;
if (avail > expected - accumulated) avail = expected - accumulated;   // clamp
for (i = 1; i <= avail; i++) QByteArray::append(&buf, frame[6+i]);    // DATA[1..avail]
```

and the terminator:

```c
if (avail == 7) {                              // frame was full: no room left for the checksum
    frame2 = takeFirst(recvList);
    if (frame2[5] == 2 && frame2[6] != 0) ck = frame2[7];   // LEN==2 -> [seq][checksum]
    else -> "Error, expected Checksum-only message was not received for command %1"
} else {
    ck = frame[5 + frame[5]];                  // = DATA[LEN-1], the byte after the payload
}
```

So **`payloadPerFrame = 7`**, and:

| condition | where the checksum lives |
|---|---|
| `expectedSize % 7 != 0` | last byte of the last data frame (`DATA[LEN-1]`) |
| `expectedSize % 7 == 0` | a **separate 2-byte frame** `[seq][checksum]` |

Worked example, `cmd 0x0e` (GIVEKANAL, 144 bytes from the §15 table):
`⌈144/7⌉ = 21` frames — 20 × `LEN=8` (seq + 7 payload), then `LEN=6` (seq + 4 payload +
checksum). `144 % 7 = 4 ≠ 0`, so no checksum-only frame.

---

## 16.3 The checksum — **algorithm recovered and verified against real bytes** ✅

`FUN_004425c0(QByteArray *recv, char seed, QByteArray *sent, int group)`:

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
    return ret - seed;                                          /* two's complement */
}
```

In words: **8-bit two's-complement sum-check, seeded with the unit id, taken over
(the request bytes minus their own trailing checksum) + (the whole assembled answer payload).**

`sent_n - 1` is decisive — it says **the last byte of a request is that request's own
checksum**, which is why it is excluded from the running sum.

### Verification against a real logged frame ✅

`LogFile-260701-T1154.txt`:

```
12:08:42.060  waitingForData:  requested  0x08, 0x01, 0xf6,
```

```
seed = unit id = 1
sum of all but last = 0x08 + 0x01 = 0x09
checksum = -(1 + 9) = -10 = 0xF6      <-- exactly the logged trailing byte
```

Recomputed for units 1/2/3 → `0xF6 / 0xF5 / 0xF4`. **Only unit 1 matches**, which also
identifies the unit of that log line. This is the first byte-level verification of the live
protocol in the whole project, and it settles §15.5's "untested hint" as **correct**.

Request layout is therefore confirmed as:

```
[command][params …][checksum]        (single CAN frame, 3..8 bytes)
 0x08     0x01       0xf6
```

⚠️ Still open: whether `params[0]` is the channel. In this sample it is `0x01` on a
1-channel box addressed as unit 1 — the two candidate meanings are numerically identical
here. One capture with unit 2 resolves it.

---

## 16.4 Completion rule — the full picture (closes G2)

```
expected = Paket.recvSize (+0x14)
         ├─ normally preloaded from Geraet_expectedRecordSize(cmd)      [§15 table]
         ├─ cmd 0x16: computed from the first frame -> expected = DATA[1] * Paket.recSize(+0x34) + 1
         └─ cmd 0x14: on checksum failure, retried with expected = 0x24 (36)   ← version fallback
accumulate 7 payload bytes per frame while (accumulated < expected)
then validate checksum; on mismatch: rollback frames (prepend) and retry, else deliver
```

Two special cases matter for a reader:

- **`expected == 0`** → the answer is a pure acknowledgement. The device replies with a
  single frame whose `DATA[1]` *is* the checksum. Failure text:
  `"CheckSum fail for Receive Size zero in command %1, try again"`.
- **`cmd 0x30`** with subtype `2` or `4` → segmented transfer. `Paket+0x3c` (offset) and
  `+0x40` (total); if `offset < total` the assembler **queues a follow-up request itself**
  for the next chunk. This is the download/large-record path.

**Error answer from the device** = a frame with `DATA[0]==0 && DATA[1]==1` →
`"Error answer in CAN bus for command %1"`. Anything else unexpected →
`"Unknown answer format received on CAN bus for command %1"`.

**Retry ladder** (`this+0x20` attempts vs `this+0x34` max, INI `[Comm] MaxResend=1`):
`try again` (status 1, re-arm the same request with the saved size in `DAT_00a1fc54`) →
`aborting` (status 2) → `FUN_00684030` drops the request queue and
`UnitComm_deleteReceivedMessages` flushes the frames.

---

## 16.5 Object layouts recovered

**`Promos3Paket` — 0x50 (80) bytes**, from `FUN_00442650` (null ctor) + accessors:

| off | field | accessor |
|---|---|---|
| +0x00 | group / generation | `FUN_00436470` |
| +0x04 | routing key A (unit id, stored as **text** → `toInt`) | `FUN_00442430` (= p+4) |
| +0x0c | routing key B | `param1_+_0xc` |
| +0x14 | **expected receive size** | get `FUN_006796c0` / set `FUN_004423f0` |
| +0x20 | QByteArray — the message bytes | `FUN_004429f0` → `FUN_004315e0` |
| +0x28 | **command** | direct (`p[10]`) |
| +0x2c | sub-type / variant | direct |
| +0x30 | aux | direct |
| +0x34 | record size (used by the 0x16 length formula) | `FUN_00442450` |
| +0x3c / +0x40 | chunk offset / total (cmd 0x30) | direct |
| +0x48 | timeout multiplier (init 1) | used by `FUN_00683e00` |

**`UnitComm`** (`this` in `FUN_00684160` / `FUN_00686430` / `FUN_00683e00`):
`+0x00` request queue · `+0x08` received-frame list · `+0x14` unit RouterObj ·
`+0x1c` QTime · `+0x20` attempt counter · `+0x24` progress marker ·
`+0x28`/`+0x2c` timeouts · `+0x34` max attempts · `+0x44` last-seen frame count.

**Global:** `DAT_00a1fc54` = saved expected-size for the in-flight retry.

---

## 16.6 What this does to the Part 15 scoreboard

| Gap | was | now | note |
|---|---|---|---|
| G1 header layout | 20% | **95%** ✅ | closed by *deletion* — there is no header |
| G2 completion rule | 30% | **90%** ✅ | seq + 7B/frame + size table + checksum terminator |
| G5 checksum | 0% | **90%** ✅ | algorithm recovered **and byte-verified** |
| G3 request side | 0% | **35%** | request format now known: `[cmd][params][ck]` |
| **G4 capture strategy** | 0% | **0% — and now mandatory** | see below |

### The sting: G4 got worse

Because answers are anonymous (§16.1), **a one-directional capture is worthless**. To decode
anything you must observe **app→gateway requests and gateway→app answers**, and pair them
per unit. That removes "bind :1789 and listen" from the table entirely:

1. **Port mirror / SPAN of both directions** — now the only viable passive option. The
   retired `promos3_sniff.c` (libpcap) is back on the menu.
2. **Be the master** (§15.3) — now much more tractable: request framing is known, the
   checksum is known and verified, `[CAN] unitAnswerTimeout=300`, `MaxResend=1`. This is the
   route I'd take.

Either way the reader's front end must change from *"parse a message"* to
**"track one outstanding request per unit, then attribute the assembled bytes to it."**

---

## 16.7 Concrete changes to the reader

```
DELETE  parse_message_header()                  — no such thing exists
DELETE  the "short frame ends the message" heuristic  — the §15.9 corruption bug goes with it

ADD     per-unit request tracker:  {command, expectedSize, sentBytes, deadline, attempts}
ADD     frame layer:  seq = DATA[0]; payload = DATA[1..LEN-2]; verify seq continuity
ADD     completion:   accumulated == expectedSize  (from the §15 size table / 0x16 formula)
ADD     checksum:     promos3_checksum(payload, unitId, sentRequest, group) == trailing byte
ADD     checksum-only frame handling when expectedSize % 7 == 0
ADD     status codes 1=retry / 2=abort / 4=incomplete, mirroring FUN_00684160
KEEP    the CONF_* honesty gating — it is still what stops guessed layouts printing as fact
```

`promos3_msg_t` loses `group`/`command` as parsed fields and gains them as *attributed*
fields, with a `bool attributed` that is false whenever no request was observed.

---

## 16.8 Naming table (this batch)

| Address | Name | Conf. |
|---|---|---|
| `FUN_00684160` | `UnitComm_assembleAnswer_MC` | 93% 🔶 |
| `FUN_004425c0` | `promos3_checksum` | **96% ✅** byte-verified vs log |
| `FUN_00442650` | `Promos3Paket_ctorNull` | 92% 🔶 |
| `FUN_00684030` | `UnitComm_clearRequestQueue` | 90% 🔶 |
| `FUN_006796c0` / `FUN_004423f0` | `Paket_getRecvSize` / `Paket_setRecvSize` | 92% 🔶 |
| `FUN_00442450` | `Paket_getRecordSize` (+0x34) | 85% 🔶 |
| `FUN_00442430` | `Paket_getRouterKeyA` (= p+4) | 88% 🔶 |
| `FUN_004429f0` / `FUN_004315e0` | `Paket_setByteArray` / `QByteArray_assign` | 88% 🔶 |
| `FUN_0042d800` | `QList_prepend` | 95% ✅ |
| `FUN_00685940` | `UnitComm_assembleAnswer_MC3` | **95% ✅** tag-proven `"ReceiveProvis3Paket"` |

Still Qt boilerplate, ignore: `FUN_004315e0`'s callers aside, all `QListData::*` wrappers.

---

## 16.9 `FUN_00685940` — the `MC3_` assembler: **a different protocol, not a variant** ✅

`UnitComm_assembleAnswer_MC3` (tag-proven: `"ReceiveProvis3Paket"`). Read side by side with
`FUN_00684160`, it shows the two generations share *nothing* at the framing layer.

### No sequence byte — 8 payload bytes per frame

```c
iVar13 += (byte)frame[5];                              /* LEN, not LEN-1  */
...
for (i = 0; i < take; i++) QByteArray::append(&buf, frame[6 + i]);   /* DATA[0..], not DATA[1..] */
```

MC_ burns `DATA[0]` on a sequence counter and carries 7 bytes/frame. **MC3_ carries 8 and has
no sequence number at all** — and therefore no per-frame ordering check, no rollback-and-retry
of individual frames, and no checksum-only frame.

### The command and length ARE on the wire (this is where the v2 model came from)

```c
if (this->inProgress /*+0x24*/ == 0) {                 /* first frame of a new answer */
    req = requestQueue.front();
    if (req && (uint)req[0x28] > 2) {
        DAT_00a1fc5c = (byte)frame[6];                 /* DATA[0] = COMMAND */
        DAT_00a1fc58 = (byte)frame[7];                 /* DATA[1] = LENGTH  */
        if (LEN == 0) -> "NULL CAN Answer received for command %1"
        if (req[0x28] != DAT_00a1fc5c) -> "Wrong package received. Requested command: %1"
```

So an MC3_ message is `[command][length][body …][checksum]`, total = `length + 1` bytes, and
the app cross-checks the answer's command against the request's. **The v2 report's
`[group][command][length]` header model was a description of MC3_** — nearly right for group 2
(there is no group byte; group is hardcoded to `2` in the ctor call), and simply not applicable
to the `MC_` box this installation actually runs.

### 16-bit length extension for ALARM / EVENT

```c
if ((cmd == 0x0f || cmd == 0x10) && frame[8] /*DATA[2]*/ == 1) {
    u16 asked = LE16(request.data[0], request.data[1]);
    if (asked == 0xFFFF)
        DAT_00a1fc58 = CONCAT11(frame[9], frame[7]);   /* len16 = (DATA[3] << 8) | DATA[1] */
}
```

Three independent cross-confirmations of report §4.2 fall out of this one branch:
`0x0f`/`0x10` really are ALARM/EVENT; `DATA[2] == 1` is the *"subcommand 1 = alarm data"* the
report inferred; and `0xFFFF` really is the *"give me everything"* request id. When the app
asks for all entries, the length promotes to a **split 16-bit field** — low byte in `DATA[1]`,
high byte in `DATA[3]`. A reader that assumes an 8-bit length will truncate every full alarm
or event dump.

### A different checksum

```c
computed = FUN_004425c0(&buf, 0, NULL, 2);     /* seed 0, no sent buffer, group 2 */
```

With `sent == NULL` the function takes its `ret = -1` branch and zeroes the seed, so it reduces
to **`checksum = -1 - Σ(message bytes)` = one's complement of the byte sum**, i.e.
`Σ(all bytes including the checksum) == 0xFF`. Verified numerically. Compare MC_:
`-(unitId + Σ request[0..n-2] + Σ payload)` — two's complement, seeded, and spanning *both*
directions. Same helper, two genuinely different schemes selected by the `group` argument.

The checksum is the last byte; it is stripped, then `QByteArray::remove(buf, 0, 2)` strips
command+length — **confirming that an MC3_ decoder body starts at message offset 2**, exactly
as report Part 4 assumed.

### Side-by-side

| | **MC_** (group 0/1) — *this box* | **MC3_** (group 2) |
|---|---|---|
| per-frame overhead | `DATA[0]` = sequence no. | none |
| payload per frame | **7** | **8** |
| command on the wire | **no** — taken from the request | **yes** — message byte 0 |
| length on the wire | **no** — from `Geraet_expectedRecordSize()` | **yes** — byte 1 (16-bit for `0x0f`/`0x10`) |
| total size | `expectedSize` from the table | `lengthByte + 1` |
| checksum position | last payload byte, or a separate `[seq][ck]` frame | last message byte |
| checksum algorithm | `-(unit + Σ sent[0..n-2] + Σ payload)` | `-1 - Σ msgBytes` |
| body starts at | offset 0 (payload is pure record) | offset 2 |
| ordering check | sequence continuity, with rollback + retry | none |
| identifiable passively? | **no** | **yes** |

**Portability verdict:** a reader cannot share a framing layer between generations. Two
front-ends, one dispatcher. For this installation only the MC_ path is required; the MC3_ path
is now specified well enough to write if another site needs it.

### Quirk worth flagging

The header parse is gated on `req[0x28] > 2` — MC3_ commands `0x01`/`0x02` never take this
path and the function returns NULL for them. Presumably the handshake is serviced elsewhere;
worth confirming before assuming a reader can see MC3_ status/gtype answers.

---

## 16.10 The request side — recovered ✅ (closes most of G3)

Two send functions, `Geraet_sendeKom_MC_GIVEKANAL` (`FUN_004d0320`) and
`Geraet_sendeKom_27_MC_GIVESIGNALVERLAUF` (`FUN_004d1810`), give the whole outbound path.

### The common skeleton

```c
Promos3RouterObj_ctor(tag, "Promos3DatenProvis2Geraet::Sende_Kom_…", 1);   /* type 1 = Provis2/MC_ */
cmd    = MsgCreator_getCommandByte(creator, 1 /*generation*/, "MC_GIVEKANAL");
paket  = MsgCreator_createPaketForCommand(creator, 1 /*group*/, tag, dest, cmd, 0, 1);
…fill wire bytes…
Paket_setRecvSize(paket, Geraet_expectedRecordSize(this, cmd));   /* expected ANSWER size */
KommandoVerteiler_enqueuePaket(KommandoVerteilerThread::instance(), paket);
```

`Paket_setRecvSize(paket, Geraet_expectedRecordSize(this, 0x0e))` in the GIVEKANAL sender is
the missing link from §15.2: **the §15 size table is consulted at send time and stamped into
`Paket+0x14`, which is exactly the `expected` the answer assembler counts down.** The table is
therefore *expected answer size keyed by command* — which also explains why every `SET…`
command returns `1` (a one-byte ack): `0x08`, `0x09`, `0x0c` → 1. ⚠️ `Kom 3 (SETANZMODE) → 170`
remains the one entry that doesn't fit the pattern.

There is also an **`MC_` name→command-byte registry**, not just the MC3_ one already known:
`MsgCreator_getCommandByte(creator, 1, "MC_GIVEKANAL")`. Dumping its table would give the
authoritative group-1 command list to cross-check §16.11's string-derived names.

### Wire layout — confirmed

`stream_peekCurrent(paket)` returns the request `QByteArray::Data`; Qt4 puts the bytes at
`+0x10`, so `Data+0x11` is `data[1]`. Both senders write through that:

```c
/* MC_GIVEKANAL  (cmd 0x0e) */
data[1] = station;

/* MC_GIVESIGNALVERLAUF (cmd 0x1b) */
data[1] = station;      /* param_5, the traceMap key      */
data[2] = feature;      /* param_2, or 0xFB / 0xFD (magic) */
data[3] = param_3;
data[4] = param_4;
```

So the request format from §16.3 is confirmed and refined:

```
[command][station][params …][checksum]
```

**`params[0]` is the station/device index (the traceMap key), not the channel** — the open
question at the end of §16.3 is closed. It reads as `0x01` in both logged frames because this
installation has one station. Cross-check: `bearbeite_Kom_15` reads `payload[0]` as the station
and keys `traceMap` with it; `FUN_004d0320` sets `this+0x54 = station` and
`bearbeite_Kom_14` reads `this+0x54` back as the traceMap key.

The logged `0x0c, 0x01, 0x61, 0xff, …` is now readable: **cmd `0x0c` = `MC_SETZYKLUS`,
station 1** — and since a cycle record is 170 bytes, that request must be **multi-frame**,
which is why the log line is truncated (the dumper caps at 8 bytes). Requests are therefore
*not* always a single CAN frame; long `SET…` commands are segmented too.

### Trace request semantics (`0x1b`)

`FUN_004d1810` picks a mode byte before sending: feature `0xFB` → mode 1, feature `0xFD` →
mode 2, and if the requested feature equals the station's current feature *and* a per-feature
node exists with `FUN_0048e500()` true, it rewrites the feature to `0xFD` and takes mode 2.
`0xFB`/`0xFD` are reserved feature selectors, not real feature indices — a reader must not map
them through `key_to_index()`.

### Two corrections to §16.5

| field | was | **is** |
|---|---|---|
| `Paket+0x20` | "QByteArray — the message bytes" | **aux/context `QVector<u8>`**, written by `Paket_setByteArray`, read by `stream_peekU16`. The wire bytes live elsewhere and are reached via `stream_peekCurrent`. |
| `Paket+0x30` | "aux" | **station / device index** (`paket[0xc] = station`) |

`+0x20` matters more than it looks. `FUN_004d1810` packs
`{station, featureKey, param_3, param_4, mode}` into it, and `FUN_00684160` copies it from the
request into the answer (`FUN_004429f0(newMsg, stream_peekU16(request))`). **That vector is how
`bearbeite_Kom_27` knows which feature it asked for.** It is in-process context, never on the
wire — so a passive listener must reconstruct it from the request bytes, while a master-mode
reader gets it for free by keeping its own request record. Another point for master mode.

---

## 16.11 What I would pull next

1. **`MsgCreator_createPaketForCommand`** — the only remaining unknown in the outbound path:
   how big the request `QByteArray` is allocated, that `data[0] = cmd`, and what the trailing
   `(0, 1)` arguments mean.
2. **The transmit tail** — whoever appends the checksum and splits the request into CAN
   frames, i.e. the `KommandoVerteilerThread::run` → CAN-interface send path. Needed for
   multi-frame `SET…` requests.
3. **`MsgCreator_getCommandByte`'s table** — the authoritative `MC_` name→byte registry, to
   cross-check the string-derived command names.
4. *(done)* ~~`FUN_00685940`~~ §16.9 · ~~request builder~~ §16.10.

*End of Part 16.*
