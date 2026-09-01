# PROVIS3 / Prometec Monitoring — Unified Reverse-Engineering, Measurement and Field-Validation Report

**Version 5.0 — the three v4.0 editions merged into one. Nothing discarded.**

**Target:** PROVIS3 HMI application (Sandvik / Prometec CNC tool-monitoring), 32-bit Qt4
binary, branded for Mazak. App version **3.1.44.4 / "V3.1.44 HF4"**, DB schema **10**.

**Goal:** Recover the device↔HMI communication protocol and data formats completely enough
that a modern 64-bit application can read live sensor telemetry, alarms, configuration and
history **without** the original software, without the PEAK/PCAN hardware, and without the
32-bit dependency chain.

---

## 0.0.1 What this document is, and why it exists

Three separate "version 4.0" reports were produced from the same project. They share a common
ancestor (consolidated report v3.0, the static-analysis phase, which is Parts 0–21 here) and
then **diverge**, because each was written against a different subset of the live-capture
evidence and each organises the field phase differently.

| Tag used in this document | Source file | Scope | Field evidence behind it |
|---|---|---|---|
| **⟦CAP1⟧** | `PROVIS3_consolidated_report_v4.md` | v3 + **one** capture. Parts 0–22. | `JULY5_IMP1.pcapng` — 4,039 packets, 21.24 s, 5,622 gateway records, **1,353** attributed exchanges |
| **⟦MEAS⟧** | `PROVIS3_COMPLETE_REPORT_v4.md` | v3 + **three** captures + a distilled normative wire spec + a document archive. Parts 0–26. | 3 captures, ~197,000 gateway records, **90,539** attributed exchanges, 178,370 checksum verifications |
| **⟦FIELD⟧** | `PROVIS3_consolidated_report_v4__1_.md` | v3 (verbatim) + the **whole field campaign**, subject-organised, incl. control-flow ownership and the ODBC back-end. Parts 0–32. | 7 captures + 4 runtime logs + 4 databases + 3 INI revisions + a live master run + a UI screenshot — **219,994** attributed exchanges, **439,988** checksum verifications, ~250,000 decoded rows |

None of the three is a superset of the other two:

- **⟦FIELD⟧** has the largest evidence base and is the most recent (2026-08-07). It alone
  carries Part 27 (who stops the machine), Part 28 (databases and QODBC), Part 29 (live access
  and operating procedure) and the eight-document reconciliation in Part 22.
- **⟦MEAS⟧** alone carries the **normative wire specification** (here Part 36 — the single most
  directly implementable artefact in the corpus), the per-capture narratives with their
  reproduction commands (Parts 34–35), the **restored low-level function catalog** (§13.16) that
  v3 abridged, the early decimal command tables (§5.2.1 ⟦MEAS⟧, §5.2.2 ⟦MEAS⟧), and the document
  lineage archive (Part 37).
- **⟦CAP1⟧** alone carries the decimal-vs-hex numbering trap (§5.2.1 ⟦CAP1⟧), the `MC_`
  trend/streaming family (§5.2.2 ⟦CAP1⟧), supersession entries §20.32–§20.40, and the
  intermediate status text that records **what was known after one capture** — which is the
  only place the reasoning between "one capture" and "seven captures" is visible.

**This edition merges all three.** Every sentence from every one of them is present somewhere in
this document.

---

## 0.0.2 How the merge was performed

1. **Parts 0–21 are common to all three editions and were merged paragraph by paragraph.**
   The three editions inherit the same v3 text; each then annotated it differently. Blocks that
   all three agree on appear once, unmarked. Blocks that only one or two editions carry are kept
   and tagged. Blocks where two editions say *different things about the same point* are kept
   **side by side**, tagged, and — where the disagreement is substantive — listed in the
   Conflict Register below (§0.0.5).
2. **Parts 22–32 are ⟦FIELD⟧'s field campaign, reproduced whole and unrenumbered**, because the
   ~370 internal cross-references inside them are self-consistent.
3. **Parts 33–37 are ⟦MEAS⟧'s field parts, renumbered from 22–26 → 33–37** so they do not
   collide with the above. Every reference to them inside this document has been rewritten to
   match. The letter-numbered sections of the two capture appendices (**§C.x**, **§D.x**) were
   already collision-free and are unchanged, so all 92 §C.x and 22 §D.x references still resolve.
4. **Part 33 is itself a merge**, because ⟦MEAS⟧ and ⟦CAP1⟧ both contain the capture-1 narrative
   with different annotations.
5. **Nothing was rewritten to smooth over a disagreement.** Where the editions differ, both
   readings are present. Where the evidence settles it, the resolution is stated in §0.0.5 and
   the losing claim is left in place with a pointer, exactly as the source documents treat their
   own superseded claims.

### Provenance markers used in Parts 0–21 and Part 33

| Marker | Meaning |
|---|---|
| *(no marker)* | All editions that carry this section agree on this block. |
| **⟦FIELD — added⟧** / **⟦MEAS — added⟧** / **⟦CAP1 — added⟧** | This block exists only in the named edition(s) and **adds** to the shared text. Additive, not contradictory. |
| **⟦… — variant⟧** | This block is one edition's **rewrite** of a passage another edition words differently. Both versions follow, each tagged. Read both. |
| `⟦FIELD⟧` / `⟦MEAS⟧` / `⟦CAP1⟧` **inside a heading** | Two editions used **the same section number for different content**. Both are kept under that number, distinguished by the tag. This happens exactly three times: **§0.7**, **§5.2.1**, **§5.2.2**. A cross-reference inside an edition's own text resolves to that edition's section. |

Parts 22–32 and 34–37 are single-source and carry no markers.

---

## 0.0.3 ⚠️ Four Part-numbering systems are in circulation — read this before following a reference

This is the largest single source of confusion in the corpus, and it now has one more layer.

**Layer 1 — the standalone analysis documents.** The eight field documents (F-a … F-h) and the
capture appendices were written against the *standalone analysis parts*, not against any
consolidated report. A reference like *"Part 17 §5.3"* inside F-b points at
`analysis_part17_session_handoff.md`, **not** at Part 17 of this report.

| Reference inside F-a … F-h, or inside Parts 33–37 | Means | In this report |
|---|---|---|
| "Part 2 §2.3", "Part 2 §1.3" | report v2 (`analysis_jul_28_1_0_0.md`) | Part 2 |
| "Part 9.7", "Part 7.2", "Part 8.1", "Part 8.5" | report v2 sections | Parts 7, 8, 9 |
| "Part 15 §G2", "Part 15 §13.2", "Part 15 §15.x" | `analysis_part15_gap_register.md` | Part 16 / Part 17 |
| "Part 16 §16.1 … §16.10" | `analysis_part16_mc_answer_protocol.md` | Part 3 (`MC_` link layer) |
| "Part 17 §2.x, §5.3, §7, §8, §13.2" | `analysis_part17_session_handoff.md` | Parts 2, 3, 5, 6, 15, 17 |
| "Part 18 §3.1, §3.3, §10, §11.2" | `analysis_part18_session_report.md` | Parts 2, 3, 16 |
| "Part 19 — Live Capture Verification" | `analysis_part19_capture_verification.md` | **Part 33** |
| "Part 25 / Appendix F (The Deployed Configuration)" | an earlier document of that name | Part 12 |

**Layer 2 — the three v4 editions.** Each numbered its field material from 22 upward, and they
mean different things. This is the mapping applied when building this edition:

| ⟦CAP1⟧ | ⟦MEAS⟧ | ⟦FIELD⟧ | **This report** | Content |
|---|---|---|---|---|
| Part 22 | Part 22 | — | **Part 33** | Capture 1 narrative (`JULY5_IMP1.pcapng`) |
| — | Part 23 (Appendix C) | — | **Part 34** | Capture 2, breadth (`ALL_merged__uniq.pcapng`); sections **§C.0–§C.16** unchanged |
| — | Part 24 (Appendix D) | — | **Part 35** | Capture 3, depth (`july_6_packet1.pcapng`); sections **§D.0–§D.11** unchanged |
| — | Part 25 | — | **Part 36** | ⭐ The normative wire specification; sections renumbered §25.x → **§36.x** |
| — | Part 26 | — | **Part 37** | Document lineage & archive; §26.x → **§37.x** |
| — | — | Parts 22–32 | **Parts 22–32** | The field campaign, unchanged |

**Rule of thumb while reading:** inside Parts 22–32, a bare "Part *n*" or "§*n.m*" means this
report's Part *n*. Inside Parts 33–37, it has already been rewritten to mean this report's
numbering — **except** where the text says "Part 15/16/17/18/19" in the sense of Layer 1 above,
which the source documents also did and which the table above decodes.

---

## 0.0.4 Confidence scale — unified

The three editions introduced the "proven on the wire" grade under **two different names**. They
mean the same thing and both are retained, because retagging inherited text would have meant
editing it.

| Marker | Introduced by | Meaning |
|---|---|---|
| 📐 **MEASURED** ≡ ✅ **WIRE** | ⟦MEAS⟧ used 📐; ⟦FIELD⟧ used ✅ WIRE | **Proven against captured network traffic**, as a predicate over a full record set rather than a spot check. The strongest evidence class in the project. Where a count is given — "88,936 / 88,936" — that is the number of independent samples satisfying the rule over the number tested. |
| ✅ **VERIFIED** | v3 | Proven against raw hex, a database value, a runtime log line, or the function's own literal tag string. Byte-for-byte or value-for-value. |
| 🔶 **GHIDRA** | v3 | Recovered from disassembly. Reliable, code-derived, but not externally cross-checked. |
| ⚠️ **INFERRED** | v3 | Reasoned from context. Not yet confirmed by bytes. |
| 🔴 | v3 | Flags a trap: something that will silently produce plausible-looking wrong output if ignored. |
| ⚖️ | *this edition* | Marks a point where the three editions disagree. See §0.0.5. |

⚠️ **A standing rule that survived every phase: a decompiled expression outranks the prose that
summarises it.** Corrections C32/C33 are the only two in this project where the decompiler output
was *right* and the English sentence directly underneath it was *wrong* — `avail = frame[5] − 1`
became "7 payload bytes per frame" because 7 was the value it took in every sample then
available. **When this report quotes a decompiled expression and then paraphrases it, the
expression is the specification and the paraphrase is a convenience.**

Two naming conventions appear in the binary and are used here as the binary uses them:

- **[tag-proven]** — the function builds a QString naming itself (a `Promos3MutexLocker`
  label, an `ErrorManager` tag, or a class-qualified string such as
  `"Promos3CanInterface::receive"`). These names are the binary's own.
- **[structural]** — the name is an analysis label derived from what the code does.
  Verify before committing it to a build.

---

## 0.0.5 ⚖️ CONFLICT REGISTER — where the three editions disagree, and what is correct

Substantive disagreements only. Wording differences and differing levels of detail are left to
the ⟦…⟧ tags in the body. **X1 is the one that will produce wrong output in a working reader; read
it first.**

### ⚖️ X1 🔴 The gateway timestamp word order — ⟦FIELD⟧ is correct, ⟦MEAS⟧'s struct is wrong

| | Claim |
|---|---|
| ⟦MEAS⟧ §36.2.3 | field map row `0x0C 8 timestamp (BE, microseconds)`, and the C struct declares `uint64_t timestamp_be;` at `+0x0C` |
| ⟦FIELD⟧ §23.4 | `0x0C` = timestamp **LOW** dword, `0x10` = timestamp **HIGH** dword, each big-endian, **low first**. *"Reading `0x0C..0x13` as one BE u64 is WRONG."* |

**Resolution: ⟦FIELD⟧ is correct, and ⟦MEAS⟧'s own prose agrees with it — only its struct
declaration does not.**

- ⟦MEAS⟧ §33.2 (capture 1) already says *"a 64-bit big-endian microsecond counter at `0x0C`
  (low dword) / `0x10` (high dword)"* — low first.
- ⟦MEAS⟧ §36.2.4 says *"the low word wraps every 71.6 minutes — visible in capture 2 as the
  high word stepping 382 → 383. Use all 64 bits, not just `+0x0C..0x0F`."* 2³² µs = 4,294.97 s
  = **71.58 min**, which is only true if `+0x0C..0x0F` is the low dword.
- ⟦FIELD⟧ reports the concrete failure: reading it as one BE `u64` produced
  `12,302,785,157,688,983,949 µs` in a real reader, and the high dword is a constant
  `0x0000017F` = 383, giving `383·2³² + ts_low ≈ 19.04 days` — a rate-checkable quantity.

**Implement:** `ts_us = ((uint64_t)be32(rec+0x10) << 32) | be32(rec+0x0C);`
Do **not** use ⟦MEAS⟧'s `uint64_t timestamp_be` field as written. Everything else in that struct
is confirmed by both editions.

### ⚖️ X2 The clock's drift figure — 75 ppm vs +8.5 ppm

⟦FIELD⟧ §23.4.1 and ⟦CAP1⟧ §33.2 quote **≈75 ppm** (ratio 1.000075). ⟦MEAS⟧ §36.2.4 quotes
**+8.5 ppm over 3,836.7 s**, and −23 ppm over a 143 s window.

**Resolution: not a contradiction — different baselines, and ⟦MEAS⟧ already gives the rule.**
The 75 ppm figure is measured over **21.2 seconds**; ⟦MEAS⟧ notes explicitly that *"a 143-second
baseline is too short to pin the sign"*. Take the longest-baseline figure: **≈ +8.5 ppm**. The
operative point, on which all three agree, is that the counter tracks real time to within tens of
ppm and is a far better time base than packet arrival time, because answer frames arrive batched.

### ⚖️ X3 🔴 Passive sniffing vs master mode — ⟦MEAS⟧ says master, ⟦FIELD⟧ reverses it

| | Position |
|---|---|
| v3 §17.1 | **Master mode.** |
| ⟦MEAS⟧ §17.1 (📐 box) | **Master mode, strengthened.** Capture 2 accidentally simulated the passive problem: 146 of 396 exchanges had no request, and attributing them failed. Each unpaired answer admitted **~48 consistent `(command, args)` pairs across 6 commands**; length narrowed but never closed it. A passive reader that drops one mirror packet cannot recover attribution *and cannot detect that it has lost it*. (§C.12) |
| ⟦FIELD⟧ §17.1 (⚠️ FIELD box), §29.1 | **Reversed. Use promiscuous sniffing.** (1) `SIO_RCVALL`/npcap on the PROVIS3 host captures **both directions** without binding a port, without transmitting, and without taking datagrams from PROVIS3 — the "unicast cannot be duplicated" objection applies only to a *bound socket*. (2) Two masters on one bus is a **correctness failure, demonstrated**: one capture contains 7 bad checksums, all 7 inside the 52-second window in which the campaign's reader was polling in master mode, none before, none after. |

**Resolution: both are right about different things, and they combine into one rule.**

⟦MEAS⟧'s §C.12 result is about *unpaired* answers — it proves the checksum is **not** an
attribution oracle, so a capture that has lost the request direction is unrecoverable. ⟦FIELD⟧'s
point is that a promiscuous host-side sniff **does not lose the request direction**, which is
precisely the condition under which §C.12's problem does not arise. ⟦FIELD⟧ additionally shows
master mode is *actively harmful* while PROVIS3 runs.

**Combined recommendation, adopted here:**
`--sniff` (promiscuous, both directions, safe alongside PROVIS3) → `--replay` (offline) →
`--listen` (PROVIS3 stopped) → `--master` (PROVIS3 stopped, exclusive, **never** while capturing
for analysis). And carry ⟦MEAS⟧'s §C.12 forward as the reason a **one-directional** capture can
never be used for body attribution, and why dropped mirror packets must be counted, not tolerated.
See Part 29 §29.1 and §29.4, and Part 34 §C.12.

### ⚖️ X4 G10 — where the unit serial number comes from

| | Claim |
|---|---|
| ⟦MEAS⟧ §36.6 (G10) | ⚠️ **90% — serial source not found.** *"The serials 10659/10663 appear nowhere in this capture in any byte order."* §C.10.5 reads `+0x14` as 10660 (unit 1) / 10665 (unit 2) big-endian, calls the identity ⚠️ INFERRED and concludes the capture *"probably"* comes from **a different cell**. |
| ⟦FIELD⟧ §31.15 (F15), §25.2.1, §30.1 | ✅ **Closed.** `SGeraetRec +0x14` **is `Serial_Num`, read BIG-ENDIAN** — the only mixed-endian field in the protocol (it was mis-typed as `date_or_crc // INFERRED` in §9.1). Four for four: `29 A3`→10659, `29 A7`→10663, `29 A4`→**10660**, `29 A9`→**10665**, all four appearing verbatim in `LogFile.txt` and in database filenames (`pmd_10659`, `pmd_10663`, `ProvisLog-10660`, `ProvisLog-10665`). All four little-endian readings are plausible five-digit numbers corresponding to nothing. |

**Resolution: ⟦FIELD⟧ closes it. ⟦MEAS⟧'s numbers were right and its conclusion was wrong.**
⟦FIELD⟧ §22.5.2 shows the installation carries **four serials in two pairs** — `PROVISsettings.ini
[DatabasePMD]` names all four and pairs them by PMD file (`10659`/`10663` → `1971`;
`10665`/`10660` → `bas?c-setup`). Parts 0–21 worked from the first pair; the campaign's
measurement databases are the second. So 10660/10665 are not evidence of a different cell — they
are the other pair on the same installation.

⚠️ **One thing ⟦MEAS⟧ raised is still open, and ⟦FIELD⟧ agrees:** whether the capture came from a
second *cell* is not settled, and if it did, the `.17`-in-the-INI / `.16`-on-the-wire discrepancy
is a documentation gap rather than a stale file. Filed as ⟦FIELD⟧ open item **F-6** (§30.3), and
answered by reading the gateway's own configuration.

**Practical rule both editions support:** take the serial from the device (`0x0D` at `+0x14`,
big-endian), never from a filename and never from a constant.

### ⚖️ X5 Headline completion percentages

| Quantity | ⟦CAP1⟧ | ⟦MEAS⟧ | ⟦FIELD⟧ |
|---|---|---|---|
| Protocol knowledge | ~99% | **≈99.7%** | **≈99.9%** |
| Working end-to-end reader | ~75%, untested | **≈93%** | **≈95%, proven on live production data** |
| `MC_` answer sizes from real bytes | 3 measured | 16 of 38 | **16 of 38** |
| `MC_` body layouts decoded | 2 of 38 | 9 of 38 (§36.6 G7) | **12 of 38** |
| G11 device timestamps | 80% | ~95% | 85% (§23.4.1) / "closed" (§30.1) |
| G12 reader robustness | 80% | 85% | 80% |

**Resolution: ⟦FIELD⟧'s figures are current** — largest evidence base, latest date. ⟦MEAS⟧'s are
the state after three captures; ⟦CAP1⟧'s after one. They are a progression, not a contradiction,
**except** for the body-layout count (9 vs 12) where the two editions simply counted different
sets, and G11/G12 where the differences are within the noise of a subjective percentage.
⟦FIELD⟧ is also internally inconsistent on G11 — §23.4.1 says "closes G11 to 85%", §30.1 says
"✅ closed". Treat G11 as **closed for ordering and interval work, open for wall-clock dating**,
which is what both texts actually describe.

### ⚖️ X6 The two final gap registers use different ID spaces

⟦MEAS⟧ §36.6 opens **D5–D9**. ⟦FIELD⟧ §30.1 opens **G14–G18** and keeps D3/D4. Neither knows
about the other's IDs. Both registers are reproduced in full. Concordance:

| ⟦MEAS⟧ | ⟦FIELD⟧ | Subject | State |
|---|---|---|---|
| D3 | D3 | Sizes for `0x01`, `0x12`, `0x1B` | ✅ `0x01`=2, `0x12`=17; **`0x1B` open** — agreed |
| D4 | D4 | The `0x08` size branch | ✅ **closed: 5** — agreed |
| **D5** | *(under D3 / §25.5)* | `0x1B GIVESIGNALVERLAUF` size and body | 🔴 **the only structurally unknown message left** — agreed by both, and both name the same fix: an operator opening the signal-trace view |
| **D6** | — | Multi-frame request continuation | open; irrelevant to a read-only reader |
| **D7** | ⟦FIELD⟧ §24.4, §26.4 | Error / retry / abort paths | open — **must be tested by injection, not by capture** |
| **D8** | ⟦FIELD⟧ §26.4.1 | Sequence wrap past 255 | ⟦FIELD⟧ goes further: **unreachable** in practice — the largest possible answer (1,001 B) needs 144 frames |
| **D9** | ⟦FIELD⟧ §24.1, §26.3 | The 250-byte flush boundary | ⚠️ characterised, not explained by either. ⟦FIELD⟧ ties it to the 100-row cap; whether the trigger is a byte buffer or a 25-row block stays undecidable |
| — | **G14–G17** | Limit-write command, cross-install `Limits.ID`, PLC bit→slot map, MACHINE ladder | ⟦FIELD⟧-only; opened by Part 27 |
| — | **G18** | ⭐ Two sensor-type encodings that disagree | ⟦FIELD⟧-only, new and open — the PMD file says `0x80` PROCUR-S ×8, `SGeraetRec +0x16` says `30 14 14 14` for the same unit |

### ⚖️ X7 Payload bytes per frame — the ⟦CAP1⟧ text is superseded in place

⟦CAP1⟧ §33.6 states *"Seven payload bytes per frame, exactly as specified"* and it is **wrong as a
rule** — it was true of capture 1 only, where every frame happened to be `DLC = 8`. Both ⟦MEAS⟧
(§D.2, ledger C32–C34) and ⟦FIELD⟧ (§24.1) correct it to `avail = min(DLC − 1, expected −
accumulated)`, verified **88,936 / 88,936**. The ⟦CAP1⟧ sentence is left in place because it
documents what one capture can make look certain; do not implement it.

Same status for ⟦CAP1⟧'s `expected % 7 == 0` completion rule (11 counter-examples, all 1,001-byte
`0x16` answers) and for the `⌈expected/7⌉` frame-count predicate, which is **withdrawn** — no
closed form exists.

### ⚖️ X8 Minor numeric differences, recorded so nobody re-derives them

| Point | Readings | Resolution |
|---|---|---|
| Max records per answer datagram | ⟦CAP1⟧ 14 / 504 B · ⟦MEAS⟧ 15 / 540 B | 15/540 is the maximum over the larger sample; 14/504 was capture 1's maximum. Size the receive buffer ≥ 1500 either way. |
| `0x33 GIVEPROGID` count in capture 1 | ⟦MEAS⟧ §33.8: **341** · ⟦FIELD⟧ §22.4.3 (quoting F-c's census): **340** | Off-by-one from a capture that begins and ends mid-transaction. ⟦FIELD⟧ shows the same ±1 signature on the `0x08` and `0x16` counts. |
| Gateway records verified | ⟦MEAS⟧ 194,006 · ⟦FIELD⟧ 217,151 | Different capture sets, both 100 % conformant. Not comparable; not contradictory. |
| Checksum verifications | ⟦MEAS⟧ 178,370 · ⟦FIELD⟧ 439,988 | Same. Zero failures in both. |
| `unit` extraction | ⟦MEAS⟧ §36.3.1 `unit = id & 0x7F` · ⟦FIELD⟧ §29.5 `unit = can_id & 0x00F` | Both correct for units 1–15. Prefer ⟦FIELD⟧'s explicit base mask (`base = can_id & 0xF80`) — it fails loudly on an unexpected base instead of silently folding it. |
| `0x0D` command name | ⟦MEAS⟧ *(unnamed — `SGeraetRec`)* · ⟦FIELD⟧ `GIVEGERAETEREC` | Same command. ⟦FIELD⟧'s name comes from the `MC3_` registry; ⟦MEAS⟧ declined to assume the `MC_` name matches. Harmless either way. |
| Feature names per unit | ⟦MEAS⟧ §C.10.3 (from the wire) · ⟦FIELD⟧ §22.5.3 (from the config files + the wire) | **Convergent, independently.** Unit 1 = `SPINDEL / X AXIS / Y AXIS / Z AXIS`, masks `0x81/82/84/88`; unit 2 = `VIBRATION / M131 DEBI / M131BASINC / M08 DEBI`, masks `0x01/02/04/08`. Ledger entry **C12** is therefore a *narrowing*, not a reversal — report v1 was reading unit 1 and report v2 was reading unit 2. ⟦FIELD⟧'s §22.5.3 heading says "reversal" while its body says "narrowing, not a reversal"; the body is right. |
| Reader change-lists | ⟦MEAS⟧ §36.5 · ⟦FIELD⟧ §29.5 | **Complementary, not conflicting** — they agree on every overlapping item. Neither is complete on its own; work from both. ⟦MEAS⟧-only: the 71.6-min timestamp wrap, `DLC==2` disambiguation by `DATA[0]`, the 15-record datagram loop, deadline armed on last frame received, alarm timestamps at body `+0x0A`, `0x0D` as the discovery command. ⟦FIELD⟧-only: `promos3_transport.c:52` copying the sequence byte into the payload, `0x16` request byte 2 = 1, drop polling `0x23`, `--sniff`, the `--raw`/`--port` tool bugs, honour `LEN`, big-endian serial, device-error status codes 1/2/4. |

### What the three editions agree on completely

Worth stating, because it is most of the document: the 36-byte gateway record layout (bar X1),
the two CAN-ID bases (`0x500 + unit` requests, `0x580 + unit` answers), the ephemeral gateway
source port, the gateway being `.16` and not the `.17` in the INI, the request wire format, the
spanning checksum in both directions, the clamped `DLC − 1` completion rule, the **entire
measured answer-size table** (all 17 entries, value for value), the `0x16` length formula
`DATA[1] × (featureCount×2 + 2) + 1`, the `(min, max)` row decode and its `0xFF` escape, the
50 Hz device sample rate, `0x1B` as the last unknown, and the feature-name/mask encoding.
**Two independent consolidations, different capture sets, same numbers.**

---

## 0.0.6 Table of contents

| Part | Title | Source | Covers |
|---|---|---|---|
| **0** | Executive summary | merged | what was achieved, the facts that matter, status, what remains, the correction ledgers |
| **1** | System architecture | merged | the two channels, reference install, receive path, transmit path, object architecture, GUI graph, concurrency, unit discovery + cadence |
| **2** | Transport: the gateway and CAN layer | merged | endianness, the 36-byte RX and TX records, `TPCANMsg`, CAN-ID → unit |
| **3** | The `MC_` link protocol (**this box**) | merged | anonymous answers, frame layout, request layout, checksum, completion rule, size table, retries, poll cycle, send queue |
| **4** | The `MC3_` link protocol (group 2) | merged | a different protocol: framing, 16-bit lengths, its own checksum, streaming, side-by-side |
| **5** | Command dispatch | merged | the dispatch model, the group-1 table (hex **and** decimal), the group-2 registry, group 0, `MC3_` field descriptors, the decimal/hex trap |
| **6** | Decoded payload bodies | merged | SIGNALVERLAUF, SAMMELMERKMALE (incl. the decoded row layout), KONFIG, ALARM, SENSOR_INFO, EVENT, and the index of bodies decoded from the wire |
| **7** | Scaling | merged | resolved: no factor, raw 0–255 |
| **8** | Decoder rings | merged | ToolStatus, SensorType, ChannelStatus, AccessLevel, EventCode, model string, alarm names, station names, field labels |
| **9** | Configuration records at rest | merged | `SGeraetRec`, `SKanalRecV40`, `SGrenzRec`, `SHardwareRec`, `SZykRecV4802`, versioning, config DB catalog |
| **10** | Measurement database (history) | merged | the 61-table schema, `Alarms` column order |
| **11** | Application data model & DB read path | merged | `Promos3DataRecord`, the SQL read chain, helpers, implications for tooling |
| **12** | SQL dialect layer, configuration and settings | merged | SQLite⇄ODBC abstraction, `Verbindung`, INI→struct maps, the settings dialog |
| **13** | Complete function reference | merged | every named `FUN_` address — **including §13.16, the low-level catalog v3 abridged** |
| **14** | Key code snippets | merged | annotated decompiler extracts, incl. the checksum as portable C |
| **15** | Object layouts | merged | `Promos3Paket`, `UnitComm`, `Promos3CanInterface`, `Interface`, `Geraet`, `Kanal`, RouterObj |
| **16** | Gap register (static-phase state) | merged | G1–G13 with their full progression, plus D3/D4 |
| **17** | Reader implementation guide (static-phase) | merged | passive vs master (**see ⚖️ X3**), the 30-second test, what to change, tooling inventory |
| **18** | Test evidence | merged | the reproduced corruption bug, the 20 passing assertions, the bug the tests found |
| **19** | Data sources & provenance | merged | how every fact was obtained, files used, method notes |
| **20** | Supersession log I (static phase) | merged | every claim an older document got wrong, and what replaced it — incl. §20.32–§20.40 from capture 1 |
| **21** | Glossary | merged | German, Turkish, protocol, hardware and confidence terms |
| **22** | **The live-capture campaign** | ⟦FIELD⟧ | evidence base, capture inventory, the eight-document reconciliation, the three contradictions resolved |
| **23** | **Transport, re-established on the wire** | ⟦FIELD⟧ | two CAN-ID bases, the ephemeral source port, the PEAK 36-byte record's real field map, the device clock |
| **24** | **Framing, completion and checksum** | ⟦FIELD⟧ | `DLC−1` not 7, the 250-byte flush, the corrected completion rule, the checksum closed in both directions |
| **25** | **Command bodies decoded from live traffic** | ⟦FIELD⟧ | the `0x16` measurement block, sixteen measured sizes, twelve decoded bodies, feature names from the device, the event list |
| **26** | **Link behaviour, timing and machine state** | ⟦FIELD⟧ | discovery and poll cadence, latency, error paths, 50 Hz, the 100-row cap, cycle detection, sensor health |
| **27** | **Control-flow ownership** | ⟦FIELD⟧ | who compares the limit, who stops the machine, what a second PROVIS3 does, G14–G17 |
| **28** | **Databases, configuration and the QODBC back-end** | ⟦FIELD⟧ | the measurement schema verified, the logging gap, the Qt plugin, four-layer verification, the migration decision |
| **29** | **Live access, tooling and operating procedure** | ⟦FIELD⟧ | the four access modes, what is safe alongside PROVIS3, the reader's own bugs, the recommended procedure |
| **30** | **Gap register v4 and open items** | ⟦FIELD⟧ | G1–G18 final state, D-items, the critical path |
| **31** | **Supersession log II (field phase)** | ⟦FIELD⟧ | F1–F32: every claim the captures overturned, narrowed or reconciled |
| **32** | **Glossary addenda and artefact inventory** | ⟦FIELD⟧ | new terms, every file used, reproduction notes |
| **33** | **Capture 1 — first live verification** | ⟦MEAS⟧+⟦CAP1⟧ | `JULY5_IMP1.pcapng`: the two-base CAN-ID correction, batching, three measured sizes, the 50 Hz rate |
| **34** | **Capture 2 — breadth (Appendix C)** | ⟦MEAS⟧ | `ALL_merged__uniq.pcapng`: the PEAK gateway record and its µs clock, the ephemeral source port, six decoded bodies, 16 measured sizes, **the attribution negative result (§C.12)** |
| **35** | **Capture 3 — depth (Appendix D)** | ⟦MEAS⟧ | `july_6_packet1.pcapng`: `DLC−1` framing, corrected checksum placement, `0x16` as `(min,max)` pairs, the measured poll loop |
| **36** | ⭐ **The normative wire specification** | ⟦MEAS⟧ | the single post-measurement spec, final gap register, final reader checklist, replay corpus — **subject to ⚖️ X1** |
| **37** | Document lineage & archive | ⟦MEAS⟧ | what each source document said, what replaced it, where its unique content now lives |
| **38** | The three source editions' front matter | verbatim | preserved in full so nothing is lost |

### Reading routes

| You want | Go to |
|---|---|
| **To implement a reader, fastest path** | **Part 36** (normative spec) — then **⚖️ X1**, then **§29.5** for the items Part 36 lacks |
| Why your reader receives nothing | **§23.2** (two CAN-ID bases), **§23.3** (ephemeral port), §36.5 |
| Why your messages never complete | **§24.1** (`DLC − 1`, not 7), §36.3.3 |
| To decode the live measurement stream | **§25.1**, §6.2.1, §D.4 |
| Whether to sniff or to master | **⚖️ X3**, then **§29.1** and §C.12 |
| The protocol as reasoned out | Parts 1–4 (`MC_`, this box) or Part 4 (`MC3_`, other sites) |
| Reference tables — dispatch, payloads, rings, records, DBs | Parts 5–10 |
| The application's own data model and SQL layer | Parts 11–12, Part 28 |
| A `FUN_` address | Part 13, incl. §13.16 |
| What can stop the machine | **Part 27** |
| To move the databases to SQL Server | **Part 28** |
| What is still open | **Part 30**, then §36.6 |
| Proof for any wire claim | Parts 22–26 (subject-organised) or Parts 33–35 (per capture) |
| You are holding an older document | §0.6, §0.7, Part 20, Part 31, Part 37 |

---

# ═══════════════════════════════════════════════════════════════
# PART 0 — EXECUTIVE SUMMARY
# ═══════════════════════════════════════════════════════════════


> ⚖️ **X5 — the three editions quote different completion percentages here.** They are a
> progression across evidence bases (1 capture → 3 captures → 7 captures), not a
> contradiction. ⟦FIELD⟧'s figures are current. See the Conflict Register, §0.0.5.
## 0.1 What was achieved

<!--variant-->
**⟦MEAS — variant⟧**

The complete bidirectional protocol was recovered — receive path, transmit path, framing,
addressing, checksum, completion rule, discovery and poll cadence — entirely from static
analysis plus the application's own files, and has since been **verified against three live
packet captures totalling 197,000 gateway records and 90,539 attributed request/answer
exchanges**.

<!--variant-->
**⟦FIELD + CAP1 — variant⟧**

The complete bidirectional protocol was recovered — receive path, transmit path, framing,
addressing, checksum, completion rule, discovery and poll cadence — entirely from static
analysis plus the application's own files.

```
Device ⇄ UDP :1789 ⇄ 36-byte gateway records ⇄ CAN frames ⇄ per-unit reassembly
       → command dispatch (group, command) → payload decode → GUI / SQLite
```

<!--variant-->
**⟦MEAS — variant⟧**

Every stage is tied to a specific, named function. All configuration record formats and both
database schemas were decoded and re-verified against the application's own exported files —
a deterministic, proof-grade method that needed no disassembly at all. The active protocol
generation, the no-scaling result, and the checksum algorithm were confirmed against the
application's own runtime log and measurement database, and then again on the wire.

<!--variant-->
**⟦MEAS — variant⟧**

**The reverse-engineering phase is complete and the verification phase is substantially
complete.** Protocol knowledge stands at **≈99.7%**. A reader built to Part 36 is **≈93%**
correct end to end. What stands between 93% and 100% is one command (`0x1B`, the live
amplitude trace, which requires an operator to open a screen), the error/retry paths (which a
healthy cell never exercises and which must be tested by injection), and engineering.

<!--variant-->
**⟦FIELD + CAP1 — variant⟧**

Every stage is tied to a specific, named function. All configuration record formats and both
database schemas were decoded and re-verified against the application's own exported files —
a deterministic, proof-grade method that needed no disassembly at all. The active protocol
generation, the no-scaling result, and the checksum algorithm were confirmed against the
application's own runtime log and measurement database.

<!--variant-->
**⟦FIELD + CAP1 — variant⟧**

**The reverse-engineering phase is complete.** Protocol knowledge stands at ~99%. The
remaining ~1% is not in the executable: it is device runtime state (two answer sizes and one
config byte) that only the machine can supply. No further decompilation is warranted.

<!--variant-->
**⟦CAP1 — variant⟧**

✅ **This has now been tested against reality.** A 21-second bidirectional capture
(`JULY5_IMP1.pcapng` — 5,622 gateway records, 1,353 complete request/answer transactions across
two units) was taken after the above was written. **The link layer is confirmed, and in most
places byte-exact:** the 36-byte record framing matched on 100% of records in *both* directions,
the request format was byte-identical to the prediction, the sequence rule held for 4,269
consecutive frames with zero errors, and the checksum verified 1,353/1,353 in the request
direction and 1,352/1,352 in the answer direction — including the answer-direction seed that
Parts 3 and 16 had flagged as an *assumption*. Four things were corrected, and the device-state
items D3/D4 were partly measured rather than guessed. See **§0.7** and **Part 33**.

<!--variant-->
**⟦FIELD — variant⟧**

> ### ⚠️ FIELD — this paragraph was right about the binary and wrong about the wire
>
> No further decompilation *was* warranted, and none of consequence was done. But the
> campaign that followed (Parts 22–32) found that three claims elsewhere in this Part were
> wrong, and none of the three was recoverable by reading more code — they were wrong about
> what the *device* does, which only the device could say. Post-campaign figures:
>
> | | v3 (static) | **v4 (measured)** |
> |---|---|---|
> | Protocol knowledge | ≈99% | **≈99.9%** |
> | Working end-to-end reader | ≈75%, untested | **≈95%, proven on live production data** |
> | `MC_` answer sizes from real bytes | 2 of 38 | **16 of 38** |
> | `MC_` body layouts decoded | 2 of 38 | **12 of 38** |
> | Remaining protocol gap | two device-state items | **one: `0x1B`** |
>
> The two device-state items (D3, D4) are **closed** (§25.3). See Part 30 for the current
> register.

### What the captures did to the analysis

> **The reverse engineering was right about the protocol and wrong about the wire.**
>
> Every framing rule recovered from Ghidra — the sequence byte, the checksum algorithm in
> *both* directions, the checksum-only frame, the `0x16` length formula, the request layout,
> the little-endian payload rule — was confirmed exactly, most across every exchange in the
> captures with zero exceptions. That is an unusually clean result for static analysis.
>
> But **three of the four facts a reader needs to receive a single byte were wrong**: the
> answer CAN-ID base, the gateway's UDP source port, and the "17 bytes of zero padding" in the
> gateway record. A reader built strictly to v3 binds the right port and then discards 100% of
> traffic — silently, with no error. All three are fixed in Part 36.
>
> A fourth rule broke only at scale: "7 payload bytes per frame" is `DLC − 1`, and the device
> emits short mid-stream frames at 250-byte flush boundaries. The decompiled code always said
> `DLC − 1`; only the English summary of it said 7.

| Measure | v3 (static only) | After capture 1 | After capture 2 | **After capture 3** |
|---|---|---|---|---|
| Protocol *knowledge* | ≈99% | ≈99.2% | ≈99.5% | **≈99.7%** |
| Live *reader* correct end to end | ≈75% | ≈80% | ≈90% | **≈93%** |
| `MC_` answer sizes known from real bytes | 2 of 38 | 5 of 38 | 16 of 38 | **16 of 38** |
| `MC_` body layouts decoded | 2 of 38 | 2 of 38 | 8 of 38 | **9 of 38** |
| Attributed exchanges verified | 0 | 1,353 | 250 | **88,936** |
| Largest complete answer observed | — | 91 B | 170 B | **1,001 B / 144 frames** |

## 0.2 The structural facts that matter most

<!--variant-->
**⟦MEAS — variant⟧**

*Post-measurement. Facts marked 📐 were re-tested against the captures; where a capture
changed the fact, the old form is kept beneath it so an older document can be placed.*

<!--variant-->
**⟦MEAS — variant⟧**

1. **Transport is CAN-over-UDP through a gateway**, `PROVISsettings.ini [CAN] PCANGateway=1`.
   Each UDP datagram is a batch of fixed **36-byte records**, each carrying one CAN frame
   (CAN-ID + up to 8 data bytes). 📐 194,006 / 194,006 records; every datagram an exact
   multiple of 36.
   🔴 **The gateway is `192.168.222.16`, not the `.17` in the INI** (Part 33 §33.1). The INI
   copy in the project predates a re-address or belongs to a different cell. And the record is,
   field for field, the **standard PEAK PCAN-Ethernet Gateway UDP frame** — a documented,
   off-the-shelf container, not a Prometec invention (Part 34 §C.3.3).
2. 🔴 **Addressing: two CAN-ID bases, split by direction.**
   `requests = 0x500 + unit` (app → gateway), `answers = 0x580 + unit` (gateway → app).
   📐 194,006 records, total split, zero crossovers.
   ⚠️ **SUPERSEDES the one-base claim of v3** (`unit = CAN-ID − 1280` in both directions),
   which itself superseded a three-base claim. See §0.6 C4 and C25, and Part 20 §20.4.
   A reader using the one-base rule computes `unit = 0x581 − 1280 = 129`, fails its range
   check and **drops every answer it will ever receive**, silently.
3. 🔴 **The gateway answers from an ephemeral, session-varying source port** (34686 and 50375
   observed), never 1789. Bind `:1789` **unconnected** and filter on source **host**, never on
   port. 📐 2,513 + 181,309 answer datagrams. A `connect()`ed socket — the natural way to write
   it — makes the kernel drop every reply (Part 34 §C.3.2).
4. **Endianness is split.** The CAN transport container is **big-endian**; the reassembled
   Promos3 application payload is **little-endian**. 📐 `ReduzLim` reads 6612 LE / 54297 BE on
   the wire, and the gateway timestamp is monotonic under BE (8,305/8,549) and not under LE
   (3,032/8,549).
5. **The link is master/slave polled, not push.** One outstanding request per unit, `[CAN]
   unitAnswerTimeout = 300` ms, `[Comm] MaxResend = 1`. An idle bus carries nothing.
   📐 0 violations of the one-outstanding rule in 88,936 exchanges. ⚠️ The cadence is **~1.5 ms
   between requests**, not the 3 ms stated in v3 — a full 8-request cycle over two units takes
   **12.64 ms median**, i.e. 77.6 cycles/s (Part 35 §D.5).
6. **This installation is a Provis2 / `MC_` box** (dispatch group 1). Proven at runtime — the
   device object is `Promos3DatenProvis2Geraet` and config arrives as `MC_GIVEKONFIG` — and
   📐 confirmed on the wire: `GIVEKONFIG` answers `e5 01 04 …` at payload offset 0.
7. 🔴 **On the `MC_` wire, answers carry no command and no group.** Both are inherited from
   the request the answer belongs to. A message is only identifiable in the context of its
   request. This is the single most consequential design fact in the project — it decides
   the entire architecture of any reader. ⚠️ SUPERSEDES the v2 header model — see §0.6 C1.
   📐 **Confirmed the hard way**: 146 answers whose requests were absent from a capture proved
   unidentifiable, and a brute-force attempt to attribute them by checksum produced ~48
   consistent `(command, args)` candidates each, across 6 distinct commands (Part 34 §C.12).
   The answer *is* however less anonymous than once feared — the **unit and the direction are
   both on the wire** in the CAN-ID (fact 2), so a listener can demultiplex units and separate
   request from answer without heuristics. Only the *command* is genuinely absent.
8. 🔴 **Payload bytes per frame is `DLC − 1`, clamped to the bytes still expected — not the
   constant 7.** The device flushes its transmit buffer every 250 payload bytes and emits a
   short mid-stream frame at each boundary. 📐 `sum(DLC−1) == total assembled bytes`,
   88,936/88,936. ⚠️ **SUPERSEDES "7 payload bytes per frame"** in v3 §3.6 and Part 34 §C.2 —
   see §0.6 C32. The decompiled loop always read `avail = frame[5] − 1`; only the prose said 7.
   Consequently the checksum-only frame condition is **`clamped avail == 7`**, not
   `expectedSize % 7 == 0` (§0.6 C33), and **there is no closed form for the frame count**
   (§0.6 C34).
9. **`MC3_` (group 2) is a different protocol, not a variant.** It shares nothing with `MC_`
   at the framing layer: 8 payload bytes per frame, no sequence byte, command
   and length *are* on the wire, a different checksum. Two front-ends, one dispatcher.
   *(Not exercised by this installation; unverified on the wire.)*
10. **The checksum is recovered, byte-verified and now measured in both directions.** An 8-bit
    two's-complement sum seeded with the unit id, taken over the request bytes (minus their own
    checksum) plus the whole answer payload. 📐 **178,370 samples across both directions and all
    three captures, zero failures.** All three plausible alternative seedings score **0/250**.
    v3's last open protocol assumption — that the answer seed is symmetric with the request — is
    closed (§0.6 C30).
11. **No amplitude scaling factor exists** for this generation. Live samples, stored maxima
    and alarm thresholds all live in one unit: **raw 0–255 counts**. 📐 Confirmed from a third,
    independent direction: the `0x16` wire rows are byte-for-byte the `Min_Sxx / Max_Sxx`
    envelope the app stores in `WP_*` (Part 35 §D.4.2).
12. **Feature names, alarm slot names and station names are per-install operator strings.**
    They must be read from the device/INI at runtime. Hardcoding the defaults mislabels them
    plausibly — the most dangerous kind of wrong. 📐 The two units on this cell carry
    *completely different* feature sets in the same firmware: unit 1 `SPINDEL / X AXIS / Y AXIS
    / Z AXIS` at masks `0x81/0x82/0x84/0x88`, unit 2 `VIBRATION / M131 DEBI / M131BASINC /
    M08 DEBI` at masks `0x01/0x02/0x04/0x08`. The mask's low nibble is **one-hot**, so the
    feature index is `log2(mask & 0x0F)`; `0x80` is a separate flag (Part 34 §C.10.3).

<!--variant-->
**⟦CAP1 — variant⟧**

1. **Transport is CAN-over-UDP through a gateway** on port **1789**
   (`PROVISsettings.ini [CAN] PCANGateway=1`). Each UDP datagram is a batch of fixed
   **36-byte records**, each carrying one CAN frame (CAN-ID + up to 8 data bytes).
   🔴 The gateway is at **`192.168.222.16`**, not the `.17` in the INI — measured, §0.7 C25.
   🔴 The batching is **asymmetric**: the app sends exactly one record per datagram; the
   gateway packs a whole multi-frame answer into one datagram (up to 14 records / 504 bytes
   observed). A reader that assumes one record per datagram loses ~64% of the frames — §0.7 C27.
2. **Addressing: two CAN-ID bases, one per direction.** Requests are `0x500 + unit`
   (`BaseCanIDTransfer` = 1280); answers are `0x580 + unit`. ⚠️ This SUPERSEDES **both** the
   original three-base claim (§0.6 C4) **and** v3's single-base correction of it (§0.7 C26).
   Units 1–15. The upshot is better than either: **direction and unit are both on the wire.**
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
9a. **The device samples features at 50 Hz** and the app's `0x16` poll rate floats to match it
   (3–9 rows per answer, 63.7 transactions/second overall). Measured, §33.9 — a real number for
   sizing buffers and for the xlsx writer.
10. **Feature names, alarm slot names and station names are per-install operator strings.**
    They must be read from the device/INI at runtime. Hardcoding the defaults mislabels them
    plausibly — the most dangerous kind of wrong.

<!--variant-->
**⟦FIELD — variant⟧**

1. **Transport is CAN-over-UDP through a gateway** at `192.168.222.17:1789`
   <!-- FIELD -->
   > **⚠️ FIELD — the gateway is at `192.168.222.16`, not `.17`.** The `.17` in
   > `PROVISsettings.ini` appears in **zero** packets across seven captures. All eight field
   > documents agree on `.16`. Do not aim a probe at `.17`. §23.1, and open item **F-6**
   > in §30.3.
   (`PROVISsettings.ini [CAN] PCANGateway=1`). Each UDP datagram is a batch of fixed
   **36-byte records**, each carrying one CAN frame (CAN-ID + up to 8 data bytes).
2. **Addressing: one CAN-ID base.** `CAN-ID = BaseCanIDTransfer(1280) + unit`, units 1–15,
   the same base in both directions. ⚠️ SUPERSEDES the three-base claim — see §0.6 C4.
   <!-- FIELD -->
   > 🔴 **⚠️ FIELD — this is the single most consequential error in v3. There are TWO bases.**
   >
   > ```
   > 0x500 + unit    PC → gateway     REQUEST
   > 0x580 + unit    gateway → PC     ANSWER
   > ```
   >
   > Measured across 194,006 records with zero exceptions. The one-base conclusion came from
   > `Promos3CanInterface::send`, which is evidence about the **transmit path only** — no
   > receive-side function was ever read to check it, and the settings dialog exposes one
   > field because a *sender* only needs one. A reader computing `unit = id − 1280` gets 129
   > or 130 for every answer, drops it as out of range, and **reports no error**. §23.2, and
   > **F1** in §0.7.
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

<!--variant-->
**⟦CAP1 — variant⟧**

```
Unit 1:  SNr 10659   GType 68 (0x44)  GSubType 5   1 channel, 4 sensors, PLC in 4 / out 1
Unit 2:  SNr 10663   GType 68 (0x44)  GSubType 5   1 channel, 4 sensors, PLC in 4 / out 1
Model string:        MSL5081-16                    (resolved, §8.7)
Device class:        Promos3DatenProvis2Geraet     → generation 1 = MC_
Firmware:            Rtm_V14.5.H86 (RTM v14.5, Intel-HEX)
Config version:      229 (0xE5)                    ← record layouts are version-selected
Gateway (INI):       192.168.222.17:1789   PCANGateway=1  BaseCanIDTransfer=1280  BusID=512
Gateway (MEASURED):  192.168.222.16:1789   🔴 the INI is stale — use .16  (§0.7 C25, §33.1)
PROVIS3 host:        192.168.222.24, bound :1789   (gateway replies from an ephemeral src port)
Unit sweep range:    FirstDevice=1 .. LastDevice=15
Timeouts:            [CAN] unitAnswerTimeout=300   [Comm] unitActiveTimeout=900  MaxResend=1
Ethernet streaming:  [Ethernet] Active=0 (disabled; would-be streaming port 2789)
Features (this box): VIBRATION · M131 DEBI · M131BASINC · M08 DEBI   (operator-assigned)
Alarm slots:         1 Collision · 2 Break · 3 Wearout · 4 Missing · 5 Coolant · 6–8 blank
Feature sample rate: 50 Hz (measured: 50.1/s unit 1, 49.8/s unit 2)      §33.9
Gateway uptime:      ~19.04 days at capture start, ~75 ppm clock drift   §33.2
```

<!--variant-->
**⟦FIELD + MEAS — variant⟧**

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

> ### ⚠️ FIELD — the reference box carries **four** serials, in two pairs, and the two units are not alike
>
> `PROVISsettings.ini [DatabasePMD]` names four: `LastMonDataFile-10659` and `-10663` both
> point at PMD **`1971`**; `-10660` and `-10665` both point at **`bas?c-setup`**. The
> runtime log in this project shows only 10659/10663. The field campaign's measurement
> databases are `ProvisLog-10660` and `ProvisLog-10665`, and its `0x0D` answers report
> serials 10660/10665. **Both pairs are real**; the campaign most likely ran against the
> second pair, which would also explain the `.17`→`.16` gateway discrepancy as a
> second cell rather than a stale file. ⚠️ INFERRED — not proven. §22.5.2.
>
> More importantly, the line `Features (this box): VIBRATION · M131 DEBI · M131BASINC · M08
> DEBI` is **half the picture**. Those are **unit 2's** features. Unit 1's are
> `SPINDEL · X AXIS · Y AXIS · Z AXIS`. This is verifiable from files already in this
> project and it reverses ledger entry **C12** — see §22.5.3.

### 0.3.1 What the captures say about *which* box this is 📐

⚠️ **The captured cell is probably a sister cell, not the one the file corpus describes.** This
matters for identifiers and for nothing else.

| | File corpus (INI, DBs, PMD, logs) | Captures 1–3 |
|---|---|---|
| Gateway | `192.168.222.17` | **`192.168.222.16`** |
| PROVIS3 host | — | `192.168.222.24`, bound `:1789` |
| Unit identifiers | SNr 10659 / 10663 | `u16 @ SGeraetRec+0x14` reads **10660 / 10665** |
| Firmware / config version | `0xE5` (229) | `0xE5` ✅ |
| `GType` / `GSubType` | `0x44` / `5` | `0x44` / `5` ✅ |
| `ReduzLim` | 6612 (`d4 19` LE) | 6612 ✅ |
| `CDRLim` | `0xAA` ×4 | `aa aa aa aa` ✅ |
| Sensors | 4 × `0x80` PROCUR-S | 4 × `0x80` ✅ |
| Channels | 1 | 1 ✅ |

Everything structural matches exactly; only the identifiers differ — and 10660/10665 are exactly
the two units the reference INI's `[DatabasePMD]` section already mentions. **Treat identifiers
as installation-specific and structure as general.** Note also that the serials 10659/10663 appear
nowhere in any capture in any byte order, so `GIVEGTYPE` is *not* their source and G10's
"serial arrives via the `GIVEGTYPE`/`registerUnit` path" is unsupported (Part 34 §C.10.5).

Captures 2 and 3 are **the same physical box, ~18 hours apart**: the gateway's uptime counter
reads 19.022 days in one and 19.768 days in the other, never reset — a clean third-party
confirmation both that the counter is continuous and that the two files share a box.

## 0.4 Status table

<!--variant-->
**⟦MEAS — variant⟧**

| Layer | Status | Confidence |
|---|---|---|
| Gateway record layout (RX **and** TX) | Complete — and identified as the **PEAK gateway frame** | 📐 MEASURED 194,006/194,006 |
| Gateway hardware timestamp (`+0x0C`, 64-bit BE µs) | Decoded; drift +8.5 ppm over 64 min | 📐 MEASURED |
| CAN-ID addressing, unit routing | Complete — **two bases**, `0x500` TX / `0x580` RX | 📐 MEASURED, total split |
| UDP endpoint behaviour (ephemeral answer port, batching to 15 records) | Complete | 📐 MEASURED |
| `MC_` request wire format | Complete, byte-exact; `LEN = 3 + min(5, payloadLen)` | 📐 MEASURED 89,186/89,186 |
| `MC_` answer framing + sequence | Complete; payload/frame = `DLC − 1` clamped | 📐 MEASURED 88,936/88,936, 0 seq errors |
| Checksum algorithm, **both directions** | Complete | 📐 MEASURED 178,370 samples, 0 failures |
| Reassembly completion rule + checksum placement | Complete (corrected form) | 📐 MEASURED 88,936/88,936 = 100.0000% |
| Expected-answer-size table | 🔴 **Binary's table refuted** — use the measured table | 📐 16 of 38 measured; the rest unknown |
| Unit discovery + poll cycle + cadence | Complete | 📐 MEASURED, 11,116 identical cycles |
| Command dispatch (group, command → handler) | Complete, ~70 handlers | ✅ / 🔶 |
| `MC_` command names (group 1) | ~35 of 38 named | 🔶 GHIDRA |
| `MC_` payload body layouts | **9 of 38 decoded** (`0x16`, `0x06`, `0x02`, `0x0D`, `0x0E`, `0x12`, `0x08`, `0x23`, `0x1B`†) | 📐 / 🔶 |
| `0x16 SAMMELMERKMALE` — the live measurement block | **Decoded: 4 × (min,max) + 2 status** | 📐 61,764 pairs, 0 inversions |
| `0x1B SIGNALVERLAUF` — the live amplitude trace | Layout 🔶 from code; **never once seen on the wire** | 🔶 GHIDRA — the last real gap |
| `MC3_` framing, registry, field descriptors | Complete | ✅ VERIFIED (binary's own registry) |
| `MC3_` payload bodies (alarm/event/sensor) | Complete | 🔶 GHIDRA — no `MC3_` box captured |
| Configuration records (device/channel/cycle/limit) | Complete | ✅ vs `1974.txt`; 📐 `SGeraetRec`/`SKanalRec` re-confirmed on the wire |
| Historical config DB schema | Complete | ✅ VERIFIED |
| Measurement DB schema (trend/WP/alarms/log) | Complete | ✅ VERIFIED; 📐 `WP_*` envelope matches the `0x16` wire rows exactly |
| Application data model + DB read path | Complete | 🔶 / ✅ |
| Code-meaning tables ("decoder rings") | Complete | 🔶 / ✅ |
| Scaling (raw→physical) | **Resolved: no factor** | ✅ 2 databases + 📐 the wire |
| Device-side timestamps | Alarm D-M-Y h:m:s decoded; gateway µs clock decoded | 📐 MEASURED |
| Error / retry / abort paths | Specified from code; **zero occurrences in 88,936 exchanges** | 🔶 GHIDRA — untestable by capture |
| Record-layout versioning | Open, low value | ⚠️ INFERRED |

<!--variant-->
**⟦MEAS — variant⟧**

† `0x1B`'s body layout is decoded from the decompiler with high confidence, but the command has
never appeared in any capture, so neither its size nor its body has been seen on the wire.

<!--variant-->
**⟦CAP1 — variant⟧**

Two confidence columns are given. **Static** is what the binary, the INI files, the databases
and the runtime logs establish. **Captured** is what the live `JULY5_IMP1.pcapng` artefact
measured on real packets (Part 33). A dash means the capture had nothing to say about that row —
usually because it is a storage-side or configuration-side fact rather than a wire fact.

<!--variant-->
**⟦CAP1 — variant⟧**

| Layer | Status | Static | Captured (Part 33) |
|---|---|---|---|
| Gateway / CAN transport framing (RX **and** TX) | Complete, byte-exact | ✅ VERIFIED | ✅ **5,622/5,622 records, both directions** |
| Datagram batching (records per datagram) | Complete | ⚠️ not modelled | ✅ **measured — asymmetric, §0.7 C27** |
| Gateway header bytes `0x04–0x14` | Complete | 🔶 "discarded" | ✅ **decoded: 64-bit µs clock, §33.2** |
| CAN-ID addressing, unit routing | Complete | ⚠️ **wrong — one base** | ✅ **two bases, split by direction, §0.7 C26** |
| `MC_` request wire format | Complete, byte-exact | ✅ VERIFIED (matches logged frame) | ✅ **1,353/1,353 byte-identical** |
| `MC_` answer framing + sequence | Complete | 🔶 GHIDRA (93%) | ✅ **0 sequence errors in 4,269 frames** |
| Checksum algorithm (both generations) | Complete | ✅ VERIFIED (two code sites + log) | ✅ **1,353/1,353 req · 1,352/1,352 ans** |
| Answer-direction checksum seed | Complete | ⚠️ *assumed* symmetric | ✅ **assumption confirmed, §33.5** |
| Reassembly completion rule | Complete | ✅ VERIFIED (code + tests) | ✅ **363/363 on the `0x16` formula** |
| Expected-answer-size table | Recovered; 3 measured, 3 still doubtful | 🔶 / ⚠️ | ✅ **`0x01`=2 `0x08`=5 `0x33`=2 measured; table said `0x08`=1** |
| Checksum-only frame (`expected % 7 == 0`) | Specified | 🔶 GHIDRA | ⚠️ **never occurred — branch untested** |
| Unit discovery + poll cycle + cadence | Complete | ✅ VERIFIED | ✅ **63.7 tx/s, 0 outstanding-request violations** |
| Command dispatch (group, command → handler) | Complete, ~70 handlers | ✅ / 🔶 | — |
| `MC_` command names (group 1) | ~35 of 38 named | 🔶 GHIDRA | 4 of 38 seen live |
| `MC_` payload body layouts | 2 of 38 decoded (`0x1b`, `0x16`) | 🔶 / ⚠️ | 🔴 **idle machine — no movement to decode** |
| `0x16` row stride (`featureCount×2+2`) | Complete | 🔶 GHIDRA ×2 | ✅ **recordSize = 10 confirmed on 363 messages** |
| `0x16` row *internal* split (which pair is which feature) | Open | ⚠️ INFERRED | ⚠️ **both candidates still parse — §33.9** |
| `MC3_` framing, registry, field descriptors | Complete | ✅ VERIFIED | — (this box is `MC_`) |
| `MC3_` payload bodies (alarm/event/sensor) | Complete | 🔶 GHIDRA | — |
| Configuration records (device/channel/cycle/limit) | Complete | ✅ VERIFIED vs `1974.txt` | — (no config traffic in window) |
| Historical config DB schema | Complete | ✅ VERIFIED | — |
| Measurement DB schema (trend/WP/alarms/log) | Complete | ✅ VERIFIED | — |
| Application data model + DB read path | Complete | 🔶 / ✅ | — |
| Code-meaning tables ("decoder rings") | Complete | 🔶 / ✅ | — |
| Scaling (raw→physical) | **Resolved: no factor** | ✅ VERIFIED (2 databases) | — |
| Device feature sample rate | **Resolved: 50 Hz** | ⚠️ unknown | ✅ **measured, §33.9** |
| Record-layout versioning | Open, low value | ⚠️ INFERRED | — |

<!--variant-->
**⟦FIELD — variant⟧**

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

<!--variant-->
**⟦MEAS — variant⟧**

**D3 and D4 — the two items v3 correctly identified as "device runtime state, not recoverable
from the binary at any effort" — are closed.** Both were measured (Parts 33–34). D4 resolves to
`n = 5`; D3 resolves to `0x01` = 2 and `0x12` = 17. Five new items opened in their place, and
the character of the remaining work changed: it is no longer *decompilation*, and it is no
longer even *capture*. Four of the five need someone at the machine doing something specific.

<!--variant-->
**⟦MEAS — variant⟧**

| # | Item | State | What closes it |
|---|---|---|---|
| **D5** | `0x1B GIVESIGNALVERLAUF` — size and body | 🔴 **open, and now the single highest-value item.** Absent from all three captures and all six sessions behind them. It is **not part of the steady-state poll loop** — the app fetches it only when the operator opens the signal-trace view | **An operator standing at the HMI opening that screen**, with a capture running. Not a longer capture. Cheap, concrete, five minutes |
| **D6** | Multi-frame **request** continuation (`[seq][7 payload]`) | open — no request longer than 8 bytes occurred in 89,186 | Issue one `0x0C SETZYKLUS` (a 170-byte cycle write) with a capture running. ⚠️ That is a **write**; out of scope for a read-only reader, which never needs this rule |
| **D7** | Error / retry / abort paths, and the `LEN == 2` disambiguation | open — **zero** device errors, retries, timeouts, sequence breaks or checksum failures in 88,936 exchanges on a healthy cell | **Fault injection**, not capture. A reader's error handling cannot be validated against any capture that exists |
| **D8** | Sequence wrap past 255 | open — the largest answer seen is 144 frames; a wrap needs ≈1,785 bytes | Nothing on this box produces one. Remains 🔶 GHIDRA (`+1 per frame, wraps at 256`) |
| **D9** | The 250-byte flush boundary | ⚠️ **characterised, not explained** — is the trigger a 250-byte buffer or a 25-row block? Only `0x16` produces answers long enough to tell, and for `0x16` the two coincide exactly | A long answer from a command with a different record stride |
| **G6** | Record-layout versioning (`Geraet_getRecordVersion`) | 20%, unchanged, **judged low value** while only firmware `Rtm_V14.5.H86` / version 229 is in scope | Decompile `FUN_004c5c70` and the version→layout switch |
| **G7** | The remaining 29 `MC_` body layouts | ~80% of what matters — the two live commands and the four config commands are decoded | Mostly config writes already available in SQLite; decode on demand |

<!--variant-->
**⟦MEAS — variant⟧**

Plus the minor open assumptions in §16.3, all of which **degrade into a timeout rather than
corruption**. Nothing on this list blocks building the reader. See Part 36 §36.6 for the full
final register.

<!--variant-->
**⟦CAP1 — variant⟧**

Two items were **device runtime state** — not recoverable from the binary at any effort. The
capture answered most of both:

<!--variant-->
**⟦CAP1 — variant⟧**

1. **D3 — real expected answer sizes.** The recovered size table (§3.7) is authoritative for
   `0x02` (14) and `0x0e` (144, call-site verified). The values in use for `0x01`, `0x12` and
   `0x1b` were guesses.
   ✅ **`0x01` measured = 2** and **`0x33` measured = 2** (Part 33). ⚠️ **`0x12` and `0x1b`
   remain unmeasured** — neither command appeared in the capture window, because no alarm fired
   and no trace was requested while the machine sat idle. `0x12` (`GIVEALARM`) was mapped onto
   the table's `0x11` entry, which is `ALARMGESEHEN` — still probably wrong. `0x1b`'s 257 still
   comes from a *synthetic* test, not from real bytes.
2. **D4 — the `0x08` size branch.** With config version `0xE5`, if `Geraet+0x4e6` is nonzero a
   nibble-sum branch applies and the statically assumed value is wrong.
   ✅ **RESOLVED as a value: 5.** The device sends 5 bytes for `0x08`, against the size table's
   `1`. So `Geraet+0x4e6` is nonzero and its nibbles sum to 5 (§33.7). This is resolved
   *without* knowing which nibble is which — which is all a reader needs.

<!--variant-->
**⟦CAP1 — variant⟧**

**A third item is now the largest remaining unknown, and it is new:**

<!--variant-->
**⟦CAP1 — variant⟧**

3. **G7 body semantics — and only a *busy* machine can supply them.** The capture caught the
   cell **completely idle for all 21 seconds**: every one of unit 2's 1,058 measurement rows was
   all-zero, unit 1's 1,064 rows were near-constant, there was not one `0xFF` escape byte in the
   whole file, and `GIVESTATUS`/`GIVEPROGID` returned `00 00` on every single poll. The link
   layer is fully verified; the **body** layer could not be, because nothing moved. See §33.9.

<!--variant-->
**⟦CAP1 — variant⟧**

Plus a short list of minor open assumptions, all of which **degrade into a timeout rather
than corruption** (§16.3). Neither D-item blocks building the reader. The one action that now
unblocks the most is **a second capture taken while the machine is cutting** (§0.7, §33.11).

<!--variant-->
**⟦FIELD — variant⟧**

Two items, both **device runtime state** — not recoverable from the binary at any effort:

<!--variant-->
**⟦FIELD — variant⟧**

1. **D3 — real expected answer sizes for `0x01`, `0x12`, `0x1b`.** The recovered size table
   (§3.7) is authoritative for `0x02` (14) and `0x0e` (144, call-site verified). The values
   in use for `0x01`, `0x12` and `0x1b` are guesses. `0x12` (`GIVEALARM`) was mapped onto the
   table's `0x11` entry, which is `ALARMGESEHEN` — probably wrong. `0x1b`'s 257 comes from a
   *synthetic* test, not from real bytes.
2. **D4 — the `0x08` size branch.** With config version `0xE5`, if `Geraet+0x4e6` is nonzero
   a nibble-sum branch applies and the currently assumed value is wrong. That byte arrives
   from device config at runtime.

<!--variant-->
**⟦FIELD — variant⟧**

Plus a short list of minor open assumptions, all of which **degrade into a timeout rather
than corruption** (§14.4). Neither item blocks building the reader; both are answered by one
30-second live test (§17.1).

<!--variant-->
**⟦FIELD — variant⟧**

> ### ⚠️ FIELD — both items are closed, and the test was run
>
> **D3 closed for `0x01` and `0x12`, still open for `0x1B`.** Measured: `0x01 GIVESTATUS` =
> **2**, `0x12 GIVEALARM` = **17** (a 16-entry ring). `0x1B GIVESIGNALVERLAUF` was **never
> observed in 219,994 exchanges** and its size remains unknown; the value 257 is withdrawn.
>
> **D4 closed.** `0x08 GIVEPLCVALUES` returns **5** bytes, not the table's 1 —
> `[in1..in4][out1]`, matching the log line *"PLC inputs 4, outputs 1"*. The nibble branch
> `(Geraet[0x4e6] >> 4) + (Geraet[0x4e6] & 0x0F)` therefore evaluates to 5 on this machine.
> A reader hard-coding 1 times out roughly sixteen times a second.
>
> §25.3. The 30-second test itself is superseded by §29.2 — it targets the wrong host and
> would not have received an answer even from the right one (§23.3).


> ⚖️ **Three correction ledgers exist in this document and they do not overlap.** §0.6 (C1–C24,
> static phase) is common to all editions; **§0.6.1** (C25–C35) is ⟦MEAS⟧'s capture-era
> extension; **§0.7 ⟦FIELD⟧** (F1–F32, expanded in Part 31) is the field campaign's. §0.7 ⟦CAP1⟧
> is the one-capture snapshot of the same thing. Read all four for a complete history.
## 0.6 Correction Ledger — superseded claims

Every place where a later session overturned an earlier one. The **Now** column is what the
body of this report states. Nothing here is deleted; it is recorded so it is not re-derived.

> This table is the **summary**. **Part 20** carries the same material at full length, with the
> reasoning behind each reversal and a few additional reconciliations that are too long for a
> table row. If you are holding an older copy of any source document, read Part 20.

<!--variant-->
**⟦CAP1 — variant⟧**

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
| **C25** | Gateway address | `192.168.222.17:1789`, taken from `[CAN] GatewayAddress` (every document up to v3) | 🔴 **`192.168.222.16:1789`.** The port is right; the host is not. The INI copy in the project either predates a re-address or belongs to a different cell. | The capture: the PROVIS3 host `192.168.222.24` exchanges every datagram with `.16` (§33.1) |
| **C26** | CAN-ID bases | **One** base, `0x500 + unit`, "TX and RX share it" (§0.6 C4, §2.5, v3 throughout) | 🔴 **Two bases, split by direction.** Requests `0x500 + unit`, answers **`0x580 + unit`**. C4 was right that `0x580` is not a *transmit* base — and wrong to conclude it was therefore not a base. It is the **answer** base. | The capture: exactly four IDs appear (`0x501 0x502 0x581 0x582`), cleanly split by direction (§33.3) |
| **C27** | Datagram → record ratio | Implicit "a datagram is a batch"; never quantified, and the reader's split loop was the only thing that depended on it | **Asymmetric and worth stating explicitly.** App → gateway: **exactly one record per datagram, 1,353/1,353.** Gateway → app: **the whole multi-frame answer batched into one datagram**, up to **14 records (504 bytes)** observed. A one-record-per-datagram reader loses ~64% of frames. | The capture (§33.2) |
| **C28** | Gateway header `0x04–0x14` | "timestamp/status (discarded)" (§2.2, Part 2.2) | **Correct, and now decodable.** On RX it carries a **64-bit big-endian microsecond counter** — low dword at `+0x0C`, high dword at `+0x10`, `+0x14` zero. ~75 ppm drift against pcap wall time; ~19.04 days of gateway uptime at capture start. Better than arrival time for jitter analysis, because answer frames arrive batched. On TX it is all zero, as `FUN_00504290` builds it. | The capture (§33.2) |
| **C29** | `0x08` expected answer size | **1** — from `Geraet_expectedRecordSize`'s `{0x08, 0x09, 0x0c} → 1` entry, "every SET returns a 1-byte ack" (§3.7.1) | 🔴 **5.** The device sends five. This is the D4 nibble branch firing, and it is fatal in practice: a reader hardcoding 1 times out on every poll, ~16 times a second. | The capture, 342 `0x08` transactions (§33.7) |
| **C30** | `0x16` request byte 2 | "`Geraet+0x688 ? 1 : 0`… sent as 0 and its meaning is unknown" (§3.3, §6.2, §16.3) | **Sent as `0x01` on this box.** The live request is `00 00 00 16 01 01 e7` — station `0x01`, then flag `0x01`. So `Geraet+0x688` is **nonzero** here. The meaning is still unknown, but the value is not 0 and a reader must not send 0 and expect parity. | The capture, 363 `0x16` requests (§33.4) |
| **C31** | The poll set | `0x16 → 0x08 → 0x01` per §3.10, and the dedup filter's set `{0x01, 0x08, 0x12, 0x16}` (§2.8) | **Observed cycle is `0x16 → 0x08 → 0x01 → 0x33`**, interleaved between units — one `0x16` per unit (not two), **plus `0x33 MC_GIVEPROGID`**, which no static analysis had placed in the poll set. `0x12 GIVEALARM` did **not** appear at all in 21 s of idle running. | The capture, 1,353 transactions (§33.8) |
| **C32** | `params[0]` = station | Concluded from `FUN_004d0320` and confirmed "three ways" (§0.6 C15) — but all three were code-internal, and this box has one station, so station and channel were numerically indistinguishable | ✅ **Confirmed on the wire, and from the one angle the code could not give.** Unit **2** is addressed as CAN-ID `0x502` and *still* sends `params[0] = 0x01`. The parameter does not track the unit. It is the station. | The capture (§33.4) |
| **C33** | Answer-direction checksum seed | "⚠️ Open assumption: the answer-direction seed is assumed symmetric with the request. Verified for requests only." (§3.5.3, §16.3) | ✅ **Assumption correct, now measured: 1,352/1,352.** And the proof is structural — the answer checksum *cannot* be validated without the request bytes, which independently confirms that the two directions are one transaction (§3.2). | The capture (§33.5) |

<!--variant-->
**⟦FIELD + MEAS — variant⟧**

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

### 0.6.1 Capture-era corrections (C25–C35) 📐

Everything below was produced by measurement rather than by reading code. These are the entries
that matter most to an implementer, because C25–C27 are each individually sufficient to make a
reader receive **nothing at all**, with no error.

| # | Item | Previously | **Now** | Evidence |
|---|---|---|---|---|
| **C25** | Answer CAN-ID base | **CORRECTION.** v3 §0.2 fact 2 / §2.5 / ledger C4 / §20.4: "One base… transmit and receive use the same base"; `0x580` purpose unknown; G4 closed as a consequence | **Two bases.** Requests `0x500 + unit`, answers `0x580 + unit`. `0x580` **is** the answer base and its purpose is no longer unknown | 8,800 records in capture 2, 194,006 in capture 3, 5,622 in capture 1 — total split, zero crossovers (Part 34 §C.3.1, Part 33 §33.3) |
| **C26** | Gateway UDP source port | *(unaddressed anywhere)* | The gateway answers from an **ephemeral, session-varying** port (34686, 50375 observed), **never 1789**. Bind `:1789` unconnected; filter on source **host** | 2,513 answer datagrams in capture 2; 181,309 in capture 3 (Part 34 §C.3.2) |
| **C27** | Gateway record `+0x04..0x14` | **CORRECTION.** v3 §2.2/§2.3: "17 bytes of zero padding" | 8-byte tag + **64-bit big-endian microsecond timestamp at `+0x0C`** + CAN channel at `+0x14`. Zero only on the *request* path, because the PC does not fill them. The record is the standard **PEAK PCAN-Ethernet Gateway** frame | +8.5 ppm against the capture clock over 3,837 s; monotonic under BE 8,305/8,549 vs LE 3,032/8,549 (Part 34 §C.4) |
| **C28** | `Geraet_expectedRecordSize` | **CORRECTION.** v3 §3.7.1 treated the table as usable except for three doubtful entries | 🔴 **Only `0x0E → 144` survives measurement.** `0x02`, `0x05`, `0x08` and `0x0F` are all wrong against the wire. **Do not ship the table** — use the measured column (§36.4) and let unmeasured commands time out | 16 sizes measured, identical on both units (Part 34 §C.9) |
| **C29** | Request first-frame `LEN` | **CORRECTION.** v3 §3.4: "`[00][00][00][5 payload]`, LEN = 8" | **`LEN = 3 + min(5, payloadLen)`.** Observed 5, 6, 7 and 8. A reader that always emits 8 and zero-pads **corrupts the checksum**, because the padding is inside the summed range | 250 requests in capture 2, 88,936 in capture 3 (Part 34 §C.6) |
| **C30** | Answer-direction checksum seed | **RESOLUTION.** v3 §3.5.3: "⚠️ Open assumption… verified for requests only" — the project's last open protocol assumption | **Symmetric, confirmed.** And it is the *only* plausible variant that works: omitting the unit seed scores 0/250, ignoring the request bytes scores 0/250, including the request's own checksum scores 0/250 | 248/248, then 88,936/88,936. 178,370 total samples, zero failures (Part 34 §C.8, Part 35 §D.3) |
| **C31** | D3 / D4 "not in the executable" | **RESOLUTION.** v3 §0.5: both blocked on a live device | **Both measured.** D4 → `n = 5`. D3 → `0x01` = 2, `0x12` = 17. `0x1B` re-filed as **D5** and remains open | Part 34 §C.9, §C.9.2 |
| **C32** | Payload bytes per frame | 🔴 **CORRECTION.** v3 §3.6 and Part 34 §C.2: "7 payload bytes per frame" | **`DLC − 1`, clamped to the remaining expected bytes.** The device emits short mid-stream frames at 250-byte flush boundaries. **The decompiled code was always right; the prose summary was not** | 33 short mid-frames at cumulative 251/501/751 bytes; `sum(DLC−1) == total` 88,936/88,936 (Part 35 §D.2) |
| **C33** | Checksum-only frame condition | 🔴 **CORRECTION.** v3 §3.6 and Part 34 §C.7.1: a separate `[seq][ck]` frame iff `expectedSize % 7 == 0` | **Iff the clamped `avail` on the final data-carrying frame equals 7** — i.e. iff that frame was filled with payload, leaving no room. Old rule: 11 counter-examples. New rule: **100.0000%** | 88,936 exchanges; the 11 failures are all 1,001-byte `0x16` answers (Part 35 §D.2.3) |
| **C34** | Frame-count formula | **CORRECTION.** Part 34 §C.7: `frames == ceil(expected/7) + (expected % 7 == 0)` | **Withdrawn — no closed form exists.** The device may insert a short frame at any 250-byte boundary. Stop on the accumulated **byte** count, never on a frame count | one counter-example at 741 bytes / 107 frames (Part 35 §D.2.4) |
| **C35** | `0x16` feature-pair semantics | **RESOLUTION.** v3 §6.2 and Part 17 §8 named the two bytes `lo`/`hi` and read `hi` as a status byte | **`(min, max)` of that feature for that sample.** The positional model was right; the semantics were not. Matches the `WP_*` `Min_Sxx / Max_Sxx` storage schema exactly — the app does not transform the rows, it writes them through | 61,764 pairs, **0** inversions; the 64 escape rows are an **exact bijection** with the 64 `min > max` violations (Part 35 §D.4) |

⚠️ **C25 partially reinstates a struck claim.** Part 17 §11 item 7 read `0x580` as a direction
discriminator; Part 18 §3.3 struck it and v3 adopted the strike (ledger C4). **The strike was
right that `0x580` is not a *transmit* base and that there are not three bases. It was wrong to
conclude that receive shares the transmit base.** Ledger C4 should now read: *two bases, not one
and not three.* The lesson is narrow and worth keeping — `Promos3CanInterface::send` is evidence
about **transmit only**, and no receive-side function was ever read to check it. `0x600` remains
unobserved and unexplained.

⚠️ **Note on C32 and C33.** These are the only corrections in the project where the **Ghidra
output was right and the summary of it was wrong**. Both rules appear in v3 immediately below a
correct quote of the assembler loop that contradicts them. The lesson is narrow and worth
keeping: **when a constant is derived from a variable in the decompilation
(`avail = frame[5] − 1`), do not promote the value it happened to take in every observed sample
into the rule.**

### The one that stops the reader working today

```c
/* promos3_transport.c:19 — as it stands */
out->unit = (int)out->can_id - PROMOS3_BASE_CAN_ID;   /* 0x581 - 1280 = 129 */
```

Every answer frame resolves to unit **129/130**, is rejected against `MAX_UNITS 16`, and the
reader decodes **nothing at all**. Not "decodes badly" — nothing. Fix:

```c
#define PROMOS3_BASE_CAN_REQ  0x500   /* 1280 — app → device */
#define PROMOS3_BASE_CAN_ANS  0x580   /* 1408 — device → app */
/* direction is unambiguous from the ID itself: id >= 0x580 → answer */
```

### The five-line summary

| # | Correction | Severity |
|---|---|---|
| **C26** | Answer CAN-ID base is `0x580 + unit`, not `0x500 + unit` | 🔴 **fatal — reader decodes nothing** |
| **C29** | `0x08` answer is **5** bytes, not the table's **1** | 🔴 **fatal — times out ~16×/s** |
| **C27** | Gateway batches up to 14 records per datagram | 🔴 **~64% frame loss if ignored** |
| **C25** | Gateway is `192.168.222.16`, not `.17` | ⚠️ probe goes nowhere |
| **C30** | `0x16` request byte 2 is `0x01`, not `0x00` | ⚠️ parity with the app |

### What it confirmed (the larger half)

Record framing `00 24 00 80` on **100%** of records in **both** directions · RX/TX structural
symmetry (the Part 18 §3.1 "free confirmation" — collected) · request format byte-identical to
the prediction · 3 reserved bytes zero on 100% of requests · `08 01 f6` byte-identical to the log
line *and* to the synthetic test frame · seq from 0, **0 errors in 4,269 frames** · 7 payload
bytes per frame exactly · `expected = DATA[1] × 10 + 1` on **363/363** messages, with
`recordSize = 10 = featureCount × 2 + 2` for **4 features** arrived at independently from the
wire · checksum **1,353/1,353** requests and **1,352/1,352** answers · one outstanding request
per unit, **0 violations in 1,353** · answer latency 1.2–5.1 ms against a 300 ms timeout ·
**0 retries, 0 timeouts, 0 device errors**.

### The upside nobody predicted

**Answers are not as anonymous as §3.2 feared.** The unit *is* on the wire, and so is the
direction — both encoded in the CAN-ID. Pairing still needs both directions (the *command*
really is absent, exactly as §3.2 says), but a listener can now demultiplex units and separate
request from answer **without any heuristics at all**. That materially improves the passive
option in §17.1, which had been argued down partly on the strength of needing heuristics.

### What it could not give, and the one action that follows

🔴 **The machine was idle for all 21 seconds.** Unit 2: 1,058 of 1,058 measurement rows
all-zero. Unit 1: 1,064 rows near-constant. **Zero `0xFF` escape bytes** — no cycle marker, no
workpiece ID, no reset, no alarm. `GIVESTATUS` and `GIVEPROGID` returned `00 00` on every poll.
Only 4 of the 38 group-1 commands appeared.

So: **the link layer is now fully verified and the body layer is not** — and it could not have
been, from this artefact, at any level of effort.

> **The single highest-value next action is a second capture, 20–30 seconds, taken while the
> machine is actually cutting.** That one artefact would show the `0xFF` escapes, a cycle
> boundary, a workpiece ID, moving feature values, and probably `0x1b` — closing G7, G9, G11 and
> the rest of D3 together. Everything at the link layer is done. Every remaining unknown is body
> semantics, and body semantics need a machine that is doing something.

Full detail, with all measurements and per-command breakdowns: **Part 33**.

## 0.7 ⟦FIELD⟧ Field Correction Ledger — what the wire overturned


The same instrument as §0.6, applied to the field campaign. **Part 31** carries these at full
length with the evidence; this is the summary. Entries are numbered **F1–F32** to keep them
distinct from the static-phase **C**-numbers.

| # | Topic | v3 claim | **Now** | What overturned it |
|---|---|---|---|---|
| **F1** | 🔴 CAN-ID bases | One base, both directions (§2.5, §0.6 C4) | **Two.** `0x500+unit` request, `0x580+unit` answer | 194,006 records, zero exceptions; §23.2 |
| **F2** | 🔴 Payload per frame | 7 bytes per frame (§3.6) | **`min(DLC−1, expected−accumulated)`.** The device flushes every 250 payload bytes and emits a short mid-stream frame | 88,936/88,936 vs 11 counter-examples; §24.1 |
| **F3** | 🔴 Gateway source port | not stated; assumed symmetric | The gateway answers from an **ephemeral** port that varies between sessions. A `connect()`ed socket discards every reply | 34686 and 50375 observed; §23.3 |
| **F4** | The 36-byte header | `+0x04..0x14` = "17 bytes of zero padding" (§2.3) | An 8-byte tag, a **64-bit microsecond device clock** (low dword first), a channel byte and flags | §23.4 |
| **F5** | Answer-direction checksum seed | "assumed symmetric, verified for requests only" (§16.3) | **Measured.** 439,988 verifications, zero failures; three alternative seedings scored 0 | §24.3 |
| **F6** | Gateway address | `192.168.222.17` (§0.2, §2.6, §17.2) | **`192.168.222.16`** on the wire in every capture | §23.1 |
| **F7** | Completion condition | `expected % 7 == 0` selects the checksum-only frame (§3.6) | Keys on the **clamped `avail == 7`**, not on DLC and not on `expected % 7` | §24.2 |
| **F8** | `⌈expected/7⌉` frame count | implied by §3.6's worked example | **Withdrawn — no closed form exists**, because of the 250-byte flush | §24.1 |
| **F9** | `0x08` answer size | 1 (size table, §3.7.1) | **5.** D4 resolved as a value | §25.3 |
| **F10** | Size-table misattributions | 46 at `0x10`, 170 at `0x03`, 40 at `0x0f` (§3.7.1, flagged as doubtful) | **46 → `0x1A`, 170 → `0x0F`, 40 → `0x29`.** The suspicion in §3.7.1 was correct | §25.3 |
| **F11** | `0x16` row base | ambiguous: `Data+0x10` or `+0x11` (§6.2) | **Payload byte 0 is the row count; rows begin at payload byte 1** | §25.1 |
| **F12** | `0x16` row layout | stride known, field order not | `+0..+7` = four `(min,max)` pairs, `+8/+9` = status. Four independent lines of evidence | §25.1 |
| **F13** | `Geraet+0x688` | "sent as 0, meaning unknown" (§6.2, §16.3) | **Sent as 1** on this device. The request is `16 01 01 <ck>` | §25.1.4 |
| **F14** | 🔴 C12 — feature names | v1's `SPINDEL/X/Y/Z` masks `0x81…` declared an error, replaced by `VIBRATION/…` masks `0x01…` | **Both are real, on different units of the same install.** C12 over-corrected | §22.5.3 — new in this edition |
| **F15** | `SGeraetRec +0x14` | `date_or_crc`, INFERRED (§9.1) | **`Serial_Num`, BIG-endian** inside an otherwise little-endian payload — the only mixed-endian field known | §25.2.1 — independently confirmed here |
| **F16** | `0x1B` expected size | 257 (§6.1) | **Unknown.** Never observed in 219,994 exchanges; 257 came from a synthetic test | §25.5 |
| **F17** | Recommendation: master mode | "master mode" (§17.1) | 🔴 **Promiscuous sniffing.** Master mode is now the *discouraged* option — it corrupts captures and cannot share the bus | §29.1 |
| **F18** | Passive capture "worthless" | one-directional capture yields nothing usable (§20.17) | **Overstated.** A one-directional capture still yields liveness, framing, checksums, DLC and size distributions, cadence, and self-identifying constants. What it cannot yield is the command label | §22.6 |
| **F19** | The 30-second test | send to `192.168.222.17:1789` from any socket (§17.2) | Wrong host, **and** an ephemeral local port receives nothing. Bind **1789** and target **`.16`** | §29.2 |
| **F20** | `0x23 GIVE_SENSORVALUES` | a command to poll | **Redundant.** `0x0E` embeds all four `0x23` records verbatim at `+0x14`, stride 14 | §25.2.2 |
| **F21** | Feature index encoding | three candidate encodings (G9) | **`index = log₂(mask & 0x0F)`** — the mask is one-hot, not an index. (G9 proper, the `0x1B` `channelKey`, stays open) | §25.2.2 |
| **F22** | Row count semantics | not addressed | Row count is the **backlog since the previous poll**, capped at **100**. Poll `0x16` slower than ~2 s and samples are lost silently | §26.3 |
| **F23** | Poll cadence | "a 3 ms polled loop" as a protocol property | **A client choice.** 1.5 / 15.6 / 31.25 ms all observed from the same app against the same device, zero errors. Latency is a device property; cadence is not | §26.2 |
| **F24** | Two masters | "do not poll a unit PROVIS3 is also polling" — an etiquette note (§17.1) | 🔴 **A correctness requirement, demonstrated.** 7 bad checksums, all inside the 52 s master window; none before, none after | §27.5, §29.4 |
| **F25** | Who stops the machine | never asked | **UNIT does**, via one PLC output bit. PROVIS3 is not in the reaction path at any point | Part 27 |
| **F26** | QODBC availability | dual-driver abstraction present (§12.1) | The plugin `qsqlodbc4.dll` is **absent from the stock install**; two SQLite-only statements sit in the connection path | Part 28 |
| **F27** | `JOURNALMODE` | `OFF` in the reference INI | Later set to `ON`, which is **not a legal SQLite journal mode**. Use `WAL` | §28.4 |
| **F28** | Measurement history | schema verified, assumed live | 🔴 **Both measurement databases stop on 2026-06-23** while the machine was demonstrably cutting on 2026-08-06. ~6 weeks missing | §28.3 |
| **F29** | Device-error signature | `DATA[0]==0 && DATA[1]==1 && LEN==2`, inference (§0.6 C20) | Constraint **retained** and still untested — no device error occurred in any capture | §24.4 |
| **F30** | Sequence wrap | a risk to handle | **Unreachable** in normal operation: the 100-row cap makes the largest answer ~1,001 bytes ≈ 144 frames; a wrap needs ~1,785 | §26.4 |
| **F31** | `SPINDEL` sensor health | "suspected dead" in an interim report | ✅ **Withdrawn.** It reached 255 in a later capture; the earlier operation simply did not load the spindle | §26.5 |
| **F32** | Display vs wire values | not addressed | The PROVIS3 graph applies a **display transform** (raw 0–255 onto a 0–300 axis, ×1.176). The wire and the database agree; the graph is the odd one out | §26.5 |

## 0.7 ⟦CAP1⟧ The live capture — what actually changed


`JULY5_IMP1.pcapng`: 4,039 packets, 21.24 s, ns resolution. 3,745 UDP packets →
**5,622 gateway records** → **1,353 complete request/answer transactions** across 2 units.
It is the first bidirectional artefact in the project, so it is the first thing that could test
the *pairing* model (§3.2) that all of Parts 3 and 17 rest on. **The model holds.**

**Verdict: the analysis is confirmed, with one fatal correction, three cosmetic ones, and three
measurements that replace guesses.**

---

# ═══════════════════════════════════════════════════════════════
# PART 1 — SYSTEM ARCHITECTURE
# ═══════════════════════════════════════════════════════════════

## 1.1 The two communication channels

<!--variant-->
**⟦CAP1 — variant⟧**

```
┌────────────────────────┐        CAN-over-UDP           ┌──────────────────────┐
│  Prometec device       │  gateway 192.168.222.16:1789  │                      │
│  (MSL5081-16, GType    │◄─────────────────────────────►│    PROVIS3  HMI      │
│   0x44, 4× PROCUR-S)   │        (THIS REPORT)          │  192.168.222.24:1789 │
└────────────────────────┘                               │    (Promos3 app)     │
┌────────────────────────┐            TCP 57400          │                      │
│  Mazak NC control      │◄──────  via NTIFDLL.dll  ─────►│                      │
│  (program, tool, part) │      (separate channel)       │                      │
└────────────────────────┘                               └──────────────────────┘

  app → gateway :  0x501, 0x502   =  0x500 + unit      1 record per datagram
  gateway → app :  0x581, 0x582   =  0x580 + unit      up to 14 records per datagram
```

<!--variant-->
**⟦CAP1 — variant⟧**

🔴 **The gateway address is `192.168.222.16`, measured — not the `.17` that
`[CAN] GatewayAddress` still says.** See §0.7 C25 and §33.1.

<!--variant-->
**⟦FIELD + MEAS — variant⟧**

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

<!--variant-->
**⟦MEAS — variant⟧**

```
 (1) UDP datagram arrives on port 1789   (batch of fixed 36-byte records)
        ▼
 (2) Scan4CANmsg  [FUN_00507760] 🔶
        split into 36-byte records (trim the remainder from the FRONT);
        each record = ONE CAN frame:
          +0x15     LEN (0..8)
          +0x1A..1B CAN-ID (uint16 BIG-ENDIAN hi,lo)     ← read +0x18 as a 32-bit dword instead
          +0x1C..23 8 DATA bytes
          +0x00..14 gateway header (discarded on RX)     ← NOT padding; see §0.6 C27
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

<!--variant-->
**⟦CAP1 — variant⟧**

```
 (1) UDP datagram arrives on port 1789   (batch of fixed 36-byte records)
        │   ✅ MEASURED: the gateway batches an ENTIRE multi-frame answer into ONE
        │   datagram — up to 14 records / 504 bytes observed. The app, by contrast,
        │   sends exactly one record per datagram (1,353/1,353). §0.7 C27
        ▼
 (2) Scan4CANmsg  [FUN_00507760] 🔶
        split into 36-byte records (trim the remainder from the FRONT);
        each record = ONE CAN frame:
          +0x15     LEN (0..8)
          +0x1A..1B CAN-ID (uint16 BIG-ENDIAN hi,lo)
          +0x1C..23 8 DATA bytes
          +0x00..14 gateway header  ← discarded by the app; on RX it is a 64-bit
                                      big-endian µs clock at +0x0C/+0x10 (§0.7 C28)
        ▼
 (3) Unit routing 🔶
        ⚠️ SUPERSEDED (§0.7 C26). The app's own rule is `unit = CAN_ID − *(this+0x48)`
        with `this+0x48 = 1280`, which is correct **for the direction it sends**. On the
        wire there are TWO bases:
              request  (app → gateway) :  unit = CAN_ID − 0x500
              answer   (gateway → app) :  unit = CAN_ID − 0x580   ← what a reader receives
        A reader that subtracts 1280 from an answer ID gets unit 129/130 and drops it.
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

<!--variant-->
**⟦FIELD — variant⟧**

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

<!--variant-->
**⟦MEAS — variant⟧**

| Emitter | Signal | → MainWindow slot |
|---|---|---|
| `Promos3DatenInstanz` (`FUN_00408a60`) | `NewMonitor(QString)` | `ConnectMonitorSignals` |
| `Promos3DatenInstanz` | `CurrentMonDisconnected()` | `OnMonitorDisconnected` |
| `Promos3DatenInstanz` | `selectedMonitorChanged(Promos3RouterObj)` | `updateAlarmBox` |
| NC comm (`FUN_00433a40`) | `showNCmsg(QString)` | `showMsgFromNC` |
| Menu manager (`FUN_00548ad0`) | `CloseMenu(bool)` | `OnCloseSubMenu` |
| Button bar (`FUN_004f5fc0`) | `ButtonClicked(int)` | `On_PushButtonClicked` |
| `GlobaleDaten` | `DownloadChange(bool)` | `OnDownloadModeChanged` |
| `GlobaleDaten` | `GotoUnitMenu(QString)` | `GotoMenuUnit` |

<!--variant-->
**⟦FIELD + CAP1 — variant⟧**

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


> ⚖️ **X1 🔴 — the gateway timestamp at `+0x0C` is two big-endian dwords, LOW FIRST**, not one
> big-endian `u64`. See §23.4, §23.4.1 and the Conflict Register (§0.0.5). This is the one
> disagreement between the editions that silently produces a garbage value.
## 2.2 The 36-byte gateway record — receive ✅

<!--add-->
**⟦MEAS — added⟧**

> 🔴 **CORRECTED BY MEASUREMENT — see Part 34 §C.4 and §0.6 C27.** The struct below reads
> correctly on this installation and is what the binary does, but three things about it are now
> known that it does not say:
>
> 1. `gw_header[0x15]` is **not opaque**. Bytes `+0x0C..0x13` carry a **64-bit big-endian
>    microsecond timestamp** written by the gateway on every answer. It is a far better ordering
>    key than host arrival time, and it is free.
> 2. The CAN-ID is the **low half of a 32-bit big-endian field at `+0x18`**. Reading the word at
>    `+0x1A` is correct for the 11-bit identifiers this cell uses and would silently truncate a
>    29-bit extended identifier. Read the dword; it costs nothing.
> 3. `unit = CAN_ID − 1280` is **wrong for answers**. Answers arrive on `0x580 + unit`.
>
> The corrected field map is §C.4 / §36.2. This record is, field for field, the standard
> **PEAK PCAN-Ethernet Gateway** UDP frame — which means a reader can be written against the
> vendor specification and be right about the cases these captures do not contain (29-bit IDs,
> RTR frames, error frames, multi-channel gateways).

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

<!--add-->
**⟦CAP1 — added⟧**

✅ **Measured (§33.2).** All **5,622** records in the capture were exactly 36 bytes; no datagram
had a non-multiple length. `0x00–03` read `00 24 00 80` on **100%** of records in **both**
directions. `0x16–19` were zero on 100%. `0x15` carried a CAN dlc of 2–8. The CAN-ID at
`0x1A–1B` was big-endian throughout.

<!--add-->
**⟦CAP1 — added⟧**

🔴 **Batching is asymmetric and the numbers matter.** The app sends **one record per datagram,
always** (1,353/1,353). The gateway packs **a whole multi-frame answer into a single datagram** —
up to **14 records (504 bytes)** observed. **A reader that assumes one record per datagram loses
~64% of the frames.** Always split every datagram into `len / 36` records before decoding.

<!--add-->
**⟦CAP1 — added⟧**

✅ **The gateway header is not empty on RX — it is a clock.** Bytes `0x04–0x14` are zero on
app→gateway records, exactly as `FUN_00504290` builds them (§2.3). On gateway→app records they
are zero *except* a **64-bit big-endian microsecond counter: low dword at `+0x0C`, high dword at
`+0x10`**, with `+0x14 = 0`. Over the capture it advanced 21.245927 s against 21.244336 s of pcap
wall time — **ratio 1.000075**, i.e. a real clock with ~75 ppm drift, showing about **19.04 days
of gateway uptime** at capture start.

<!--add-->
**⟦CAP1 — added⟧**

> Part 2.2 originally called `gw_header[0x15]` "timestamp/status (discarded)". That was correct
> — and it is now decodable if you want it. It is **better than pcap arrival time for jitter
> analysis**, precisely because answer frames arrive batched: every record in a batch shares one
> arrival timestamp, but each carries its own gateway µs stamp.

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

<!--add-->
**⟦MEAS — added⟧**

> ✅ 📐 **Prediction collected.** All **194,006** records across all three captures begin
> `00 24 00 80`, in **both directions**, with zero exceptions. RX and TX records are structurally
> identical. The `0x04..0x14` region is genuinely all-zero on the app→gateway path — exactly as
> `FUN_00504290` builds it — which is why it looked like padding: the PC does not fill it, and
> only the *gateway* writes a timestamp there (§0.6 C27).

<!--add-->
**⟦CAP1 — added⟧**

✅ **Collected.** The capture confirms it: `00 24 00 80` appears on 100% of records in **both**
directions, and RX and TX records are structurally identical (§33.2). The Part 18 §3.1 prediction
that this would "confirm symmetry for free" was correct, and it cost one hexdump.

## 2.4 Reassembled CAN message — the internal form ✅

```c
typedef struct { uint32_t ID; uint8_t MSGTYPE; uint8_t LEN; uint8_t DATA[8]; } TPCANMsg;
/* gateway buf[0x1A:0x1B] (BE) → ID;  buf[0x15] → LEN;  buf[0x1C:0x23] → DATA[0:8] */
```

This is the PEAK PCAN standard 14-byte message struct. `LEN` at `+5` and `DATA` at `+6` were
confirmed from code (`canFrame_appendHex`, `FUN_00682010`), not inferred.

## 2.5 CAN-ID addressing ✅ ⚠️ SUPERSEDES §0.6 C4

<!--add-->
**⟦MEAS — added⟧**

> 🔴 **CORRECTED BY MEASUREMENT — see Part 34 §C.3.1 and §0.6 C25. This is the single most
> consequential error in the pre-capture report.**
>
> **There are two bases, split by direction:**
>
> ```c
> #define CANID_BASE_TX  0x500   /* 1280 — PC → gateway : requests */
> #define CANID_BASE_RX  0x580   /* 1408 — gateway → PC : answers  */
> /* unit = id & 0x7F ;  is_answer = (id & 0x580) == 0x580 */
> ```
>
> 📐 194,006 records; requests only ever on `0x501`/`0x502`, answers only ever on
> `0x581`/`0x582`. Zero crossovers.
>
> **Everything below is still true — and that is the point.** `Promos3CanInterface::send`
> really does compute `CAN-ID = BaseCanIDTransfer(1280) + unit`, and the settings dialog really
> does expose exactly one "Base Tx" field. Both statements are about **transmit**, and both are
> confirmed. The error was inferring that *receive* therefore shares that base: `send` cannot
> testify about the receive direction, and no receive-side function was ever consulted to check.
>
> **`0x580` is the answer base.** Its purpose is no longer unknown, which partially reinstates a
> claim struck in Part 18 §3.3 — the reading of `0x580` as a direction discriminator was right;
> calling it a *transmit* base, and counting three bases where there are two, was not. `0x600`
> remains unobserved.
>
> 🔴 **Severity.** A reader implementing the text below computes `unit = 0x581 − 1280 = 129`,
> finds it outside the valid range 1–15, and drops the frame. It drops **every answer it will
> ever receive**, reports zero errors, and looks exactly like a network problem. This one line
> is the difference between a working reader and one that cannot be debugged.
>
> **A consolation.** Because direction and unit are both encoded in the CAN-ID, answers are less
> anonymous than §3.2 feared: a listener can demultiplex units and separate request from answer
> with no heuristics at all. Only the *command* is genuinely absent from an answer.

<!--add-->
**⟦CAP1 — added⟧**

> 🔴 ⚠️ **THIS SECTION IS ITSELF SUPERSEDED — read the measured result first (§0.7 C26).**
> Everything below about the *transmit* direction is correct and stays correct. The conclusion
> drawn from it — that one base therefore governs both directions — is **wrong**, and it is the
> single most consequential error left in the report before the capture.
>
> ```
> requests  (app → gateway) : 0x501, 0x502   = 0x500 + unit    ← BaseCanIDTransfer 1280 ✅
> answers   (gateway → app) : 0x581, 0x582   = 0x580 + unit    ← NOT 1280  🔴
> ```
>
> Only those four IDs appear in the entire 5,622-record capture, cleanly split by direction.
> `this+0x48` **was** read correctly — it simply only ever governs the direction that function
> *sends*. `0x580` is not a transmit base; it is the **answer / receive** base.
>
> **Reader rule:** `if (id >= 0x580) { answer; unit = id - 0x580; } else { request; unit = id - 0x500; }`
> Direction is unambiguous from the ID itself. See §33.3.

```c
local_1c = *(int *)((int)this + 0x48) + unit;      /* FUN_00506220 */
```

<!--variant-->
**⟦CAP1 — variant⟧**

**One base *for transmit*:** `CAN-ID = BaseCanIDTransfer + unit`, with
`BaseCanIDTransfer = 1280 = 0x500` from `[CAN]`, and `unit ∈ [FirstDevice, LastDevice] = 1…15`.
Independently confirmed by the settings dialog (`FUN_006da550`), which exposes exactly one
**"Base Tx"** field described as *"CAN transfer base address in hex"*, with First/Last unit
described as **offsets added to Base Tx** — note that the dialog's own label says **Tx**, which
in hindsight was the clue that it governs one direction only.

<!--variant-->
**⟦FIELD + MEAS — variant⟧**

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

<!--variant-->
**⟦CAP1 — variant⟧**

**The full history of this constant, because it reversed twice.** The CANopen-shaped reading
(`0x600+unit` master→slave, `0x580+unit` slave→master) was proposed in Part 17, rejected in
Part 18 on the grounds that `FUN_00506220` demonstrably transmits on `0x48 + unit`, and has now
been **half-vindicated by measurement**:

<!--variant-->
**⟦CAP1 — variant⟧**

| Reading | `0x500` | `0x580` | `0x600` | Verdict |
|---|---|---|---|---|
| Part 17 — three bases, CANopen-shaped | tx | rx | ? | **direction split: right. Detail: unproven.** |
| Part 18 / v3 — one base, both directions | tx **and** rx | not a base | not a base | **"not a *transmit* base": right. "Therefore not a base": wrong.** |
| **Part 33 — measured** | **request** | **answer** | **never seen** | ✅ |

<!--variant-->
**⟦CAP1 — variant⟧**

So: `0x580` **is** the answer base (measured, 4,269 answer frames). `0x600` did **not** appear in
21 seconds of traffic and remains genuinely unexplained. The lesson worth keeping is that
"`FUN_00506220` does not transmit on it" was a true statement about one function that got
generalised into a false statement about the bus.

<!--variant-->
**⟦CAP1 — variant⟧**

This mattered because `0x580` was briefly believed to be the direction discriminator that would
unblock passive capture — and it turns out **it is exactly that.** Passive capture is not
*required* (master mode still needs none, §17.1), but the passive option is materially better
than §17.1 assumed: see §0.7 and §33.3.

<!--variant-->
**⟦CAP1 — variant⟧**

🔴 **Reader trap — and this is the live bug, not a hypothetical.** A reader that computes
`unit = can_id - 1280` and drops anything `>= MAX_UNITS` maps every real answer (`0x581`,
`0x582`) to units **129 / 130**, fails the `MAX_UNITS 16` test, and **silently discards the
entire receive direction**. This is precisely what `promos3_transport.c:19` does today
(§0.7, §17.5). If `0x600 + n` ever does appear, count and log it — do not drop it in silence.

<!--variant-->
**⟦FIELD + MEAS — variant⟧**

The CANopen-shaped reading (`0x600+unit` master→slave, `0x580+unit` slave→master) was an
attractive hypothesis and it was wrong — `FUN_00506220` demonstrably transmits on
`0x48 + unit`. The two other constants exist and are unexplained; they are simply not
transmit bases. This mattered because it was briefly believed to be the direction
discriminator that would unblock passive capture. It is not, and passive capture turned out
not to be needed at all (§0.6 C18).

<!--variant-->
**⟦MEAS — variant⟧**

🔴 **Reader trap.** A reader that computes `unit = can_id - 1280` and drops anything
`>= MAX_UNITS` will map `0x580+n` and `0x600+n` to units 128+ and 256+ and silently discard
them. If those IDs ever appear in real traffic, you want them counted and logged, not
dropped in silence.

<!--variant-->
**⟦FIELD — variant⟧**

🔴 **Reader trap.** A reader that computes `unit = can_id - 1280`
<!-- FIELD -->
> ### ⚠️ FIELD — this trap is real, it fires on every answer, and it is not an edge case
>
> The paragraph below hedges: *"if those IDs ever appear in real traffic."* They appear in
> **all** of it. `0x580+n` is the answer base. `promos3_transport.c:19` computes
> `unit = can_id − 1280` → 129 or 130, `:44` drops anything `>= MAX_UNITS`, and the reader
> discards **100% of the answer traffic** while reporting no error and no checksum failure.
>
> The advice below — *"you want them counted and logged, not dropped in silence"* — was
> exactly right, and following it would have surfaced this in one run. §23.2. and drops anything
`>= MAX_UNITS` will map `0x580+n` and `0x600+n` to units 128+ and 256+ and silently discard
them. If those IDs ever appear in real traffic, you want them counted and logged, not
dropped in silence.

## 2.6 Reference network setup

<!--variant-->
**⟦MEAS — variant⟧**

```
Devices 10659 / 10663:  GType 0x44 (MSL5081-16), 1 channel, 4× PROCUR-S sensors
Gateway:                192.168.222.17:1789     ← ⚠️ STALE: the wire says .16 (§0.3.1)
                        PCANGateway=1  BaseCanIDTransfer=1280  BusID=512
                        BaudrateRegister=22  CanDeviceType=2  HardWareHandle=16  DriverNo=50
Unit sweep:             FirstDevice=1 … LastDevice=15
Ethernet streaming:     Active=0 (disabled), would-be ports 1789–1799, streaming 2789
Mazak NC:               TCP 57400 via NTIFDLL
```

<!--variant-->
**⟦MEAS — variant⟧**

📐 **Measured endpoints** (all three captures agree):

<!--variant-->
**⟦MEAS — variant⟧**

```
PROVIS3 host  192.168.222.24 : 1789   (bound; sends FROM 1789 TO 1789)
Gateway       192.168.222.16 : 1789   (receives on 1789)
Gateway       192.168.222.16 : 34686  \ answers come FROM an ephemeral port that
Gateway       192.168.222.16 : 50375  / varies between sessions — never from 1789
```

<!--variant-->
**⟦MEAS — variant⟧**

⚠️ `[Ethernet] LastPort = 1799` and `LastUsedPort = 1793` in the reference INI are PROVIS3's own
persisted values and match neither observed port. **Filter on host, never on port** (§0.6 C26).

<!--variant-->
**⟦CAP1 — variant⟧**

```
Devices 10659 / 10663:  GType 0x44 (MSL5081-16), 1 channel, 4× PROCUR-S sensors
Gateway (INI):          192.168.222.17:1789          ← STALE
Gateway (MEASURED):     192.168.222.16:1789          ← USE THIS   🔴 §0.7 C25
PROVIS3 host:           192.168.222.24, bound :1789
                        (the gateway replies from an ephemeral source port — :50375 observed —
                         so a reader must NOT filter answers on source port 1789)
                        PCANGateway=1  BaseCanIDTransfer=1280  BusID=512
                        BaudrateRegister=22  CanDeviceType=2  HardWareHandle=16  DriverNo=50
CAN-IDs (measured):     requests 0x501 0x502   answers 0x581 0x582
Unit sweep:             FirstDevice=1 … LastDevice=15
Ethernet streaming:     Active=0 (disabled), would-be ports 1789–1799, streaming 2789
Mazak NC:               TCP 57400 via NTIFDLL
```

<!--variant-->
**⟦CAP1 — variant⟧**

⚠️ The `.16` / `.17` discrepancy has two possible explanations and the capture cannot
distinguish them: either the INI copy in the project predates a re-address, or it belongs to a
different cell. Either way, **`.16` is where the packets actually go.**

<!--variant-->
**⟦FIELD — variant⟧**

<!-- FIELD -->
> ### ⚠️ FIELD — corrected addresses
>
> ```
> Gateway (PEAK PCAN-Ethernet):  192.168.222.16 : 1789    ← wire; the INI's .17 is not on the wire
> PROVIS3 host:                  192.168.222.24 : 1789    ← binds AND sources 1789
> Gateway answer source port:    ephemeral, varies (34686, 50375 observed)
> ```
> §23.1, §23.3.

<!--variant-->
**⟦FIELD — variant⟧**

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

<!--variant-->
**⟦CAP1 — variant⟧**

| cmd | byte 1 | byte 2 | byte 3 | byte 4 |
|---|---|---|---|---|
| `0x01` GIVESTATUS | — | — | — | — |
| `0x08` GIVEPLCVALUES | station | — | — | — |
| `0x0e` GIVEKANAL | station | — | — | — |
| `0x16` GIVESAMMELMERKMALE | station | `Geraet+0x688 ? 1 : 0` — ⚠️ **measured `0x01` on this box, not 0** (§0.7 C30) | — | — |
| `0x1b` GIVESIGNALVERLAUF | station | feature | p3 | p4 |
| `0x1c` GIVEOLDWORKPROZ | station | p3 | — | — |
| `0x1f` GIVEMUSTER | station | p3 | `(p4 & 0x0F) \| (p5 << 4)` | 0 |
| `0x23` GIVE_SENSORVALUES | round-robin slot index (`Geraet+0x60`, scanning `Geraet+0x4d0…`; slots 0–3 = features, 4–11 = sensors) | | | |

<!--variant-->
**⟦FIELD + MEAS — variant⟧**

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

### ✅ Measured request bytes — all four polled commands, both units

Every one of the 1,353 requests in the capture matched the predicted shape exactly:

```
[00][00][00][cmd][params …][ck]        LEN = 3 + payload,  single frame
```

The three reserved bytes were zero on **100%** of requests (their purpose remains unexplained —
but they are at least stable). No request needed a continuation frame: every payload was ≤ 4
bytes, exactly as predicted.

| request bytes (unit 1 / unit 2) | cmd | meaning | checksum arithmetic |
|---|---|---|---|
| `00 00 00 16 01 01 e7` / `…e6` | `0x16` | GIVESAMMELMERKMALE, station 1, param **1** | `−(1+0x16+1+1) = 0xE7` ✓ |
| `00 00 00 08 01 f6` / `…f5` | `0x08` | GIVEPLCVALUES, station 1 | `−(1+8+1) = 0xF6` ✓ |
| `00 00 00 01 fe` / `…fd` | `0x01` | GIVESTATUS, no params | `−(1+1) = 0xFE` ✓ |
| `00 00 00 33 00 cc` / `…cb` | `0x33` | GIVEPROGID, param 0 | `−(1+0x33+0) = 0xCC` ✓ |

`08 01 f6` is **byte-identical to `LogFile-260701-T1154`** and to the synthetic test frame in
Part 18 §3.2 — three independent derivations of the same six bytes.

🔴 **Note the `0x16` request carries `01` in byte 2, not `00`.** §6.2 and §16.3 both record
`Geraet+0x688` as "sent as 0, meaning unknown". On this box it is **nonzero** and the request
carries `0x01`. The meaning is still unknown; the value is not what was assumed (§0.7 C30).

✅ **`params[0]` is the station — settled from the one angle the code could not give.** Unit 2
is addressed as CAN-ID `0x502` and *still* sends `params[0] = 0x01`. **The parameter does not
track the unit.** Because this box has exactly one station, station and channel had been
numerically indistinguishable in every previous artefact; the second unit breaks the tie. This
closes the Part 16 §16.3 open question in favour of the Part 17 reading from `FUN_004d0320`
(§0.6 C15, §0.7 C32).

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

## 3.4 Request framing onto CAN ✅

From `Promos3CanInterface::send` (`FUN_00506220`):

<!--variant-->
**⟦MEAS — variant⟧**

```
first frame:      [00][00][00][ up to 5 payload bytes ]     LEN = 3 + min(5, payloadLen)
continuation N:   [seq][ up to 7 payload bytes        ]     LEN = 1 + chunk
```

<!--variant-->
**⟦MEAS — variant⟧**

> 📐 **`LEN = 3 + min(5, payloadLen)`, not a constant 8** (§0.6 C29). Observed values are 5, 6,
> 7 and 8 across 89,186 requests — a short request produces a short first frame.
> 🔴 **A reader that always emits `LEN = 8` and zero-pads corrupts the checksum**, because the
> padding bytes fall inside the summed range.
>
> | `LEN` | payload `[cmd][args][ck]` | requests (capture 2) |
> |---:|---:|---:|
> | 5 | 2 | 14 |
> | 6 | 3 | 19 |
> | 7 | 4 | 184 |
> | 8 | 5 | 33 |
>
> ✅ The three reserved bytes are **zero on 100% of requests** in all three captures. Purpose
> still unexplained, but they are at least stable.
>
> ⚠️ The **continuation** rule remains 🔶 GHIDRA. No multi-frame request appears in any capture
> — the read-only poll set is all ≤ 4 payload bytes, and the one command that would produce one
> (`0x0C SETZYKLUS`, a 170-byte cycle write) never ran. Filed as **D6**; irrelevant to a
> read-only reader.

<!--variant-->
**⟦FIELD + CAP1 — variant⟧**

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

<!--variant-->
**⟦CAP1 — variant⟧**

✅ **RESOLVED — the assumption was right, and it is now measured.** The answer-direction seed
was flagged here and in §16.3 as symmetric-by-assumption, verified for requests only.

<!--variant-->
**⟦CAP1 — variant⟧**

| test | result |
|---|---|
| request checksum, `−(unit + Σ params)` | **1,353 / 1,353** ✅ |
| answer checksum, spanning **both** directions | **1,352 / 1,352** ✅ (the one miss is truncated at capture end) |

<!--variant-->
**⟦CAP1 — variant⟧**

Note what this second row proves about the *model*, not just the arithmetic: **the answer
checksum cannot be validated without the request bytes.** That is independent, structural
confirmation that the two directions are one transaction — the pairing model of §3.2, tested
against real packets for the first time (§0.7 C33, §33.5).

<!--variant-->
**⟦CAP1 — variant⟧**

Handy equivalent form for a reader that has already computed the request checksum:

<!--variant-->
**⟦CAP1 — variant⟧**

```
ck_answer = (ck_request − Σ answer_payload) & 0xFF
```

<!--variant-->
**⟦FIELD + MEAS — variant⟧**

⚠️ **Open assumption:** the answer-direction seed is assumed symmetric with the request. It is
verified for requests only.

<!--add-->
**⟦MEAS — added⟧**

> ✅ 📐 **CLOSED — the project's last open protocol assumption.** See Part 34 §C.8, Part 35 §D.3
> and §0.6 C30. Applying the formula verbatim to the answer direction:
>
> ```c
> checksum = −( unit + Σ request_bytes[0 .. n−2] + Σ answer_payload ) & 0xFF
> ```
>
> | direction | samples | failures |
> |---|---:|---:|
> | requests | 89,186 | **0** |
> | answers | 89,184 | **0** |
> | **total** | **178,370** | **0** |
>
> And it is not merely *consistent* with the data — it is the **only** plausible variant that is.
> Three alternatives were tested against all 250 answers of capture 2:
>
> | hypothesis | ok / 250 |
> |---|---:|
> | omit the unit seed | 0 |
> | unit seed, but ignore the request bytes | 0 |
> | include the request's own trailing checksum | 0 |
>
> Both `sent_n − 1` (excluding the request's own checksum) and the unit seed are therefore
> **independently required by the bytes**. Note what this proves about the model: an answer's
> checksum cannot be validated without the request bytes — independent confirmation that the two
> directions really are one transaction.
>
> Handy equivalent form for a reader that already has the request checksum:
> `ck_answer = (ck_request − Σ answer_payload) & 0xFF`.
>
> 🔴 **Use the checksum to *validate* an attribution you already have, never to *derive* one.**
> As an attribution oracle it fails completely — see Part 34 §C.12.

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

<!--variant-->
**⟦MEAS + CAP1 — variant⟧**

So **`payloadPerFrame = 7`**, and:

<!--variant-->
**⟦FIELD — variant⟧**

So **`payloadPerFrame = 7`**, and:
<!-- FIELD -->
> ### ⚠️ FIELD 🔴 — the decompiled loop above is right; the sentence that summarises it is wrong
>
> The loop quoted immediately above says `avail = frame[5] - 1`, clamped. That is correct and
> it is what the device does. **`payloadPerFrame` is `DLC − 1`, not 7.** The constant 7 was
> true of every sample available at the time and of nothing else: the device flushes its
> transmit buffer every **250 payload bytes** and emits a short mid-stream frame at each
> boundary — observed at cumulative byte counts 251, 501 and 751, and never elsewhere.
>
> This is the only correction in the whole project where Ghidra was right and the prose
> summary of it was wrong. The corrected rule scores **88,936 / 88,936**; the `expected % 7`
> rule below has **11 counter-examples**. The `⌈144/7⌉ = 21` worked example that follows is
> withdrawn — no closed form for the frame count exists. **Stop on the accumulated byte
> count, never on a frame count.** §24.1–24.2.

| condition | where the checksum lives |
|---|---|
| `expectedSize % 7 != 0` | last byte of the last data frame (`DATA[LEN-1]`) |
| `expectedSize % 7 == 0` | a **separate 2-byte frame** `[seq][checksum]` |

🔴 A reader that does not know about the checksum-only frame will treat it as a truncated
data message.

<!--add-->
**⟦CAP1 — added⟧**

✅ **Measured (§33.6).** Answer frames are `[seq][≤7 payload]` with `seq` starting at `0x00`, and
there were **0 sequence errors in 4,269 frames**. Seven payload bytes per frame, exactly as
specified. `expected` counts the message **excluding** the checksum byte — confirmed against the
`0x16` formula.

<!--add-->
**⟦CAP1 — added⟧**

⚠️ **The checksum-only branch remains untested.** No message in the capture window happened to
hit `expected % 7 == 0`, so no `[seq][ck]`-only frame occurred. Keep the code path; it is
specified from the disassembly and there is no reason to doubt it, but it has not been seen.

**Worked example, `cmd 0x0e` (`GIVEKANAL`, 144 bytes from the size table):**
`⌈144/7⌉ = 21` frames — 20 × `LEN=8` (seq + 7 payload), then `LEN=6` (seq + 4 payload +
checksum). `144 % 7 = 4 ≠ 0`, so no checksum-only frame.

<!--add-->
**⟦MEAS — added⟧**

<!--add-->
**⟦MEAS — added⟧**

> ## 🔴 3.6.1 CORRECTED BY MEASUREMENT — the two framing rules above are wrong
>
> **See Part 35 §D.2, and §0.6 C32 / C33 / C34. This is the correction to read most carefully,
> because it is the one the decompiler never got wrong.**
>
> Look again at the loop quoted three paragraphs above:
>
> ```c
> avail = frame[5] - 1;                                  /* = DLC - 1, NOT the constant 7 */
> if (avail > expected - accumulated) avail = expected - accumulated;   /* clamp */
> ```
>
> **It reads `DLC − 1` and clamps to the bytes still outstanding. It never assumes 7.** The
> summary sentence "`payloadPerFrame = 7`" was true of every sample available when it was
> written, and it was promoted into a rule. It is not one.
>
> ### What the wire shows
>
> Census of payload bytes per frame (`DLC − 1`) across 88,936 exchanges:
>
> | payload bytes | as a mid-stream frame | as the final frame |
> |---:|---:|---:|
> | 7 | 16,100 | 3 |
> | 6 | **12** | 22,244 |
> | 5 | **21** | 14,166 |
> | 4 | — | 52 |
> | 3 | — | 44,467 |
> | 2 | — | 7,965 |
> | 1 | — | 39 *(the checksum-only frames)* |
>
> Short **final** frames are expected. Short **mid-stream** frames are not under the 7-byte
> model — and 33 of them occur. Their positions are not random:
>
> | short mid-frame at frame index | occurrences | cumulative payload bytes at that point |
> |---:|---:|---:|
> | 35 | 12 | **251** |
> | 71 | 11 | **501** |
> | 107 | 10 | **751** |
>
> **The device flushes its transmit buffer every 250 payload bytes and emits a short frame at
> each boundary.** For `0x16` the payload is a 1-byte row count followed by 10-byte rows, so 250
> bytes is exactly **25 rows**, and the boundaries fall at 1+250, 1+500, 1+750. Whether the
> trigger is a byte buffer or a row block cannot be separated from `0x16` alone (filed as **D9**).
>
> ⚠️ **This is why the earlier captures saw nothing.** The longest complete answer in capture 2
> was 170 bytes — below the first boundary. The rules did not hold and then break; they were
> never tested.
>
> ### The corrected rule 📐 88,936 / 88,936 = 100.0000%
>
> ```c
> acc = 0;
> for each frame {
>     if (acc >= expected) break;
>     avail = min(DLC - 1, expected - acc);      /* the clamp is load-bearing */
>     append DATA[1 .. avail];
>     acc += avail;
> }
> if (avail == 7)   /* the last data frame was FULL: no room for the checksum */
>     take one more frame; it must be LEN == 2, checksum = DATA[1];
> else
>     checksum = DATA[LEN-1] of the frame just consumed;
> ```
>
> | rule | agreement over 88,936 exchanges |
> |---|---:|
> | **corrected (clamped `avail == 7`)** | **88,936 / 88,936 — 100.0000%** ✅ |
> | old (`expectedSize % 7 == 0`) | 88,925 / 88,936 — **11 counter-examples** 🔴 |
> | naïve variant ("last frame had `DLC == 8`") | 88,933 / 88,936 — 3 counter-examples |
>
> All 11 counter-examples to the old rule are 1,001-byte `0x16` answers: `1001 % 7 == 0`, so it
> predicts a checksum-only frame, but the three mid-stream short frames shift the final frame off
> the boundary and the checksum lands inline instead. The 3 counter-examples to the `DLC == 8`
> variant are 41-byte answers whose final frame has `DLC = 8` but whose clamped `avail` is 6 —
> the frame is physically full while only 6 of its bytes are payload, so the checksum occupies
> `DATA[7]`. **The clamp is what makes the rule exact.**
>
> ### There is no frame-count formula 📐
>
> Part 34 offered `frames == ceil(expected/7) + (expected % 7 == 0)`. It scores 88,935/88,936,
> and the single failure — a 741-byte answer in 107 frames where the formula predicts 106 — is
> enough to retire it. **Withdrawn. Accumulate `DLC − 1` and stop on the byte count, never on a
> frame count.**
>
> ### Severity
>
> A reader using the `%7` rule mishandles ~0.012% of exchanges — but **the affected exchanges are
> precisely the long `0x16` blocks that carry the backlog of real measurement samples.** It waits
> for a checksum-only frame that never comes, times out, and discards a 100-row block. On this box
> that is one dropped measurement burst per ~8,000 polls, appearing as an occasional unexplained
> gap in the data. The worst possible subset to lose.
>
> ### What survived, at scale
>
> | rule | result |
> |---|---:|
> | `DATA[0]` = sequence, 0,1,2,… , +1 per frame | **88,936 / 88,936**, 0 discontinuities |
> | checksum position, corrected rule | **88,936 / 88,936** |
> | `sum(DLC − 1)` == total assembled bytes | **88,936 / 88,936** |
> | `0x16` length `= DATA[1] × 10 + 1` | **88,936 / 88,936**, including all 1,001-byte cases |
>
> ⚠️ **Sequence wrap past 255 is still untested** (**D8**). The largest answer anywhere is 144
> frames; a wrap would need an answer of ≈1,785 bytes. The `+1 per frame, wraps at 256` behaviour
> remains 🔶 GHIDRA.
>
> ### The checksum-only frame, when it does occur 📐
>
> Capture 2 gives a clean partition on the commands short enough for the old rule to hold:
>
> | `expected % 7` | exchanges | trailing frame |
> |---|---:|---|
> | `== 0` | 10 | **`LEN = 2`, `[seq][checksum]`** — all 10 |
> | `!= 0` | 240 | checksum inline as `DATA[LEN-1]` — all 240 |
>
> Both `%7 == 0` commands there answer 14 bytes: `0x06 GIVEKONFIG` and `0x23 GIVE_SENSORVALUES`
> — two of the most useful commands on the box. 🔴 A reader that omits the checksum-only frame
> treats **4% of its exchanges** as truncated.

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

<!--add-->
**⟦MEAS — added⟧**

> 🔴 **CORRECTED BY MEASUREMENT — see Part 34 §C.9 / §C.9.1 and §0.6 C28.**
> **Do not carry this table into a reader.** Of the entries that could be tested against the
> wire, **only `0x0E → 144` survives.** Four are wrong:
>
> | cmd | table says | wire says | |
> |---|---:|---:|---|
> | `0x02 GIVEGTYPE` | 14 | **3** | 🔴 wrong |
> | `0x05 GIVEUSEDZYKTAB` | 16 | **32** | 🔴 wrong |
> | `0x08 GIVEPLCVALUES` | 1 | **5** | 🔴 wrong (this is D4) |
> | `0x0E GIVEKANAL` | **144** | **144** | ✅ exact |
> | `0x0F GIVEZYKLUS` | 40 | **170** | 🔴 wrong |
>
> v3's suspicion that "some entries are keyed by **record type** rather than by command" is
> confirmed and is worse than suspected: `0x0F` answers **170**, which is the `SZykRecV4802`
> size that the table parks at `0x03 SETANZMODE` — the entry v3 flagged as "⚠️ odd for a SET
> command". The 170 is real; it is filed under the wrong key. Likewise `0x1A GIVEHARDWAREREC`
> answers **46**, the `SHardwareRec` size the table parks at `0x10` — resolving v3's
> "⚠️ but `GIVEHARDWAREREC` is `0x1a`, not `0x10`" in favour of the command name.
>
> **Use the measured table in §36.4.** For a command with no measured size, do **not** guess —
> let the exchange time out. A timeout is a loud failure; a wrong `expectedSize` is a silent one
> that consumes the *next* answer's frames, which is exactly the corruption reproduced in
> §18.1 case C.

A flat switch keyed by command number; an unknown key logs `"Versionsfehler"` and returns −1.

<!--variant-->
**⟦CAP1 — variant⟧**

| cmd | table says | **measured** | note |
|---|---|---|---|
| `0x01` | *(no entry)* | **2** ✅ | GIVESTATUS — never calls `setRecvSize`; now measured (§33.7) |
| `0x02`, `0x28` | 14 | — | `SGrenzRec` ✅ |
| `0x03` | 170 | — | `SZykRecV4802` ✅ ⚠️ odd for a SET command |
| `0x04` | 4 | — | |
| `0x05` | 16 | — | |
| `0x08`, `0x09`, `0x0c` | 1 | 🔴 **`0x08` = 5** | see the D4 box below — the table's 1 is **wrong on this device** |
| `0x0e` | **144** | — | `SKanalRecV40` ✅ **call-site verified** |
| `0x0f` | 40 | — | |
| `0x10` | 46 | — | `SHardwareRec` ✅ ⚠️ but `GIVEHARDWAREREC` is `0x1a`, not `0x10` |
| `0x11` | 2 | — | |
| `0x16` | *(computed)* | **`count × 10 + 1`** ✅ | formula confirmed on 363/363 messages (§3.7, §33.6) |
| `0x33` | *(no entry)* | **2** ✅ | GIVEPROGID — measured (§33.7) |
| `0x35`, `0x3f` | 20 | — | |
| `0x36` | 60 | — | |
| `0x37` | 64 | — | |
| `0x38` | 160 | — | |

<!--variant-->
**⟦CAP1 — variant⟧**

> 🔴 **`0x08` is the one that breaks a reader, and it is the D4 branch firing.**
> The table entry (`0x08, 0x09, 0x0c → 1`, "every SET returns a 1-byte ack") gives **1**. The
> device sends **5**, on all 342 `0x08` transactions in the capture. That is exactly this branch:
>
> ```c
> else n = (Geraet[0x4e6] >> 4) + (Geraet[0x4e6] & 0x0F);   /* version 0xE5 → this branch */
> ```
>
> So `Geraet+0x4e6` is **nonzero** and its nibbles sum to **5** on this box (`0x41`, `0x14`,
> `0x23`, `0x32`, `0x05`, `0x50` all fit). **D4 is resolved as a value — 5 — without needing to
> know which nibble is which**, which is all a reader needs. A reader hardcoding 1 for `0x08`
> would time out on every poll, **~16 times a second**. (§0.7 C29, §33.7)
>
> ⚠️ The generalisation matters more than the number: **the size table is a static default that
> device configuration can override at runtime.** Where the table and the device disagree, the
> device wins. Prefer measured sizes; treat the table as the fallback.

<!--variant-->
**⟦FIELD + MEAS — variant⟧**

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

<!--add-->
**⟦CAP1 — added⟧**

> ⚠️ **The capture could not test this — and it strengthened the case for keeping the `LEN == 2`
> constraint anyway.** There were **0 device-error frames** in 1,353 transactions, so the
> signature itself is untested against real bytes. But the capture makes the ambiguity concrete:
> `0x16` answers in this window begin `00 03…` through `00 09…`, i.e. `DATA[1]` **is** the row
> count, and a one-row block **would** produce exactly `00 01` on a `LEN 8` frame. The `LEN == 2`
> constraint is the only thing separating the two. **Keep it.** (§33.8)

> The `LEN == 2` constraint is §0.6 C20 and it is not optional. Without it the signature is
> identical to a healthy first data frame whose first payload byte is 1 — which for `0x16`
> means "one row", the single most common case there is. A reader missing this constraint
> discards most live measurement data and counts it as device errors. This was found by
> *writing and testing* the link layer, not by reading code; the constraint itself is marked
> as an inference to confirm against a real capture.

<!--add-->
**⟦MEAS — added⟧**

> 📐 **Measured, and the discriminator turns out to be the other byte** (Part 34 §C.7.2).
> `LEN == 2` is necessary but **not sufficient**, because a checksum-only frame is *also*
> `LEN == 2`:
>
> - 21 `LEN == 2` answer frames occur in capture 2.
> - **All 10 checksum-only frames carry `DATA[0] = 2`.** None carries `DATA[0] = 0`.
> - **0 device-error answers** occur in any capture.
>
> The separator is **`DATA[0]`, the sequence byte**: an error answer is a whole message, so its
> sequence is **0**; a checksum-only frame is the *last* frame of a multi-frame answer, so its
> sequence is **≥ 1**. That matches the decompiled guard `frame2[5] == 2 && frame2[6] != 0`
> exactly. 🔴 A reader keying only on `DATA[1] == 1` will misread roughly 1 in 256 checksum-only
> frames as a device error.
>
> ⚠️ **Nothing in this section has ever been exercised on the wire.** Across 88,936 exchanges in
> a live production cell: **0** device errors, **0** retries, **0** timeouts, **0** sequence
> discontinuities, **0** checksum failures, **0** answers without an outstanding request. On a
> healthy cell the error paths are simply never taken. That is good operational news and bad
> test-coverage news — **the retry ladder, the abort path and the error-answer frame cannot be
> validated against any capture that exists. They must be tested by injection** (filed as **D7**).

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

### 3.10.1 The poll cycle as actually observed 📐

The static reading above is right about the *set* and incomplete about the *cycle*. The measured
steady-state dialogue is exactly **8 requests**, and it did not vary once across **11,116
consecutive cycles** (Part 35 §D.5):

```
u1:0x16   u1:0x08   u1:0x01   u1:0x33     u2:0x16   u2:0x08   u2:0x01   u2:0x33
   ↑         ↑         ↑         ↑
 samples    PLC     status   prog-id
```

preceded, **exactly once per unit at session start**, by `0x0E GIVEKANAL` — the descriptor
fetch. That is the whole of it: **one configuration read, then four commands per unit, forever.**

Two amendments to the static account:

- `0x33 MC_GIVEPROGID` **is** in the poll set. It is absent from `FUN_004d1310` and from the
  de-duplication filter, so it is issued from elsewhere; the wire shows it every cycle.
- `0x12 MC_GIVEALARM` is in the de-dup filter but **was not polled** during any capture window.
  It is presumably issued on demand or on a slower timer.
- The `0x16` command is sent **once** per unit per cycle here, not once per station per cycle —
  consistent with `channelCount == 1` on this box.

| quantity | measured |
|---|---|
| full 8-request cycle | median **12.64 ms**, p90 15.2, p99 19.8, max 83.7 |
| cycle rate | **77.6 cycles/s** |
| request → next request | median **1.51 ms**, p10 1.12, p90 2.17 |
| request → first answer frame | median **1.17–1.93 ms** by command; p99 ≤ 2.9; max **9.8 ms** |
| inter-frame gap within one answer (device clock) | median **151 µs**, p10 143, p90 168 |
| answer datagram batching | 1–15 records; max **540 bytes** |

⚠️ **Amends §0.2 fact 5 and §1.4.** The measured inter-request interval is **1.5 ms**, roughly
double the 3 ms rate the static analysis reports. Nothing depends on the exact figure, but a
master implementation pacing itself at 3 ms will run at **half** the app's throughput.

**Timeout headroom.** `[CAN] unitAnswerTimeout = 300` against a worst observed latency of 9.8 ms
is a 31× margin. **50 ms is ample** — but arm the deadline on the **last frame received**, not
on the request: a 144-frame answer takes 144 × 151 µs ≈ **22 ms** to stream, which would breach
a naïve 20 ms request-anchored deadline.

### ✅ The cadence as actually observed (§33.8)

```
per unit:   0x16  →  0x08  →  0x01  →  0x33          interleaved between units 1 and 2
```

| measurement | value |
|---|---|
| transactions | **1,353 in 21.2 s = 63.7 tx/s** |
| median inter-transaction gap | **15.7 ms** (p95 16.7 ms, max 125 ms) |
| command mix | `0x16` 363 · `0x08` 342 · `0x33` 341 · `0x01` 307 |
| one outstanding request per unit | **0 violations in 1,353** — `Interface_setLastSentPaket`'s enforcement is real and visible |
| answer latency | **1.2–5.1 ms** against `unitAnswerTimeout = 300` — two orders of margin |
| retries / timeouts / device errors | **0 / 0 / 0** |

Two differences from the static reading, neither harmful but both worth knowing:

- ⚠️ **`0x33 MC_GIVEPROGID` is in the poll set** and no static analysis had placed it there. It
  is not in `sendCommandToUnit`'s de-duplication set either (§2.8), which lists
  `{0x01, 0x08, 0x12, 0x16}` — so `0x33` is re-issued without dedup protection.
- ⚠️ **`0x12 MC_GIVEALARM` did not appear at all** in 21 s. It is in the dedup set, so it *is* a
  periodic command; it simply did not fire during an idle window. Its expected answer size
  therefore remains unmeasured (D3).
- Only **one** `0x16` per unit was observed, not the two the `for station` loop implies — this
  box has `channelCount = 1`, so the loop runs once. Consistent, not contradictory.

The single answerless transaction in the file is the **last** request in it — capture truncation,
not a fault.

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

### 5.2.1 ⟦MEAS⟧ The same table in decimal — as the binary's own tag strings write it


*Restored from `promos3_protocol_map.md` §3. Kept because the app's `Kom_NN` tag strings are
**decimal**, so this is the form you will match against when grepping the binary or reading a log
line, and because it carries five names the hex table above leaves as "(unnamed)".*

German keys: `GIVE` = read · `SET` = write · `Zyklus` = cycle · `Kanal` = channel ·
`Merkmal` = feature · `Geraet` = device · `Muster` = pattern · `Alarm gesehen` = alarm seen.

| dec | hex | Command | Meaning |
|---:|---|---|---|
| 01 | 0x01 | `MC_GIVESTATUS` | read status |
| 02 | 0x02 | `MC_GIVEGTYPE` | read device type |
| 04 | 0x04 | `MC_GIVEMERKMAL` | read feature |
| 05 | 0x05 | `MC_GIVEUSEDZYKTAB` | read used-cycle table |
| 06 | 0x06 | `MC_GIVEKONFIG` | read config |
| 08 / 09 | 0x08 / 0x09 | `MC_GIVEPLCVALUES` / `MC_SETPLCVALUES` | read / write PLC values |
| 10 | 0x0a | `MC_SETGERAET` | write device record |
| 11 | 0x0b | `MC_SETKANAL` | write channel record |
| 12 | 0x0c | `MC_SETZYKLUS` | write cycle |
| 14 | 0x0e | `MC_GIVEKANAL` | read channel |
| 15 | 0x0f | `MC_GIVEZYKLUS` | read cycle |
| 17 | 0x11 | `MC_ALARMGESEHEN` | mark alarm seen |
| 18 | 0x12 | `MC_GIVEALARM` | read alarm |
| 19 | 0x13 | `MC_QUITALARM` | acknowledge alarm |
| 21 | 0x15 | `MC_PRESSEDKEYS` | key presses (touch UI) |
| 22 | 0x16 | `MC_GIVESAMMELMERKMALE` | read collected features |
| 24 | 0x18 | `MC_GIVETEACHSTATUS` | read teach status |
| 26 | 0x1a | `MC_GIVEHARDWAREREC` | read hardware record (`SHardwareRec`) |
| 27 | 0x1b | `MC_GIVESIGNALVERLAUF` | read signal trace |
| 28 | 0x1c | `MC_GIVEOLDWORKPROZ` | read old workpiece process |
| **30** | **0x1e** | **`MC_SETMUSTER`** | **write pattern** — ⭐ *not in the hex table above* |
| 31 | 0x1f | `MC_GIVEMUSTER` | read pattern |
| 33 | 0x21 | `MC_GIVE_CDR_DATA` | read CDR (NC context) data |
| 35 / 36 | 0x23 / 0x24 | `MC_GIVE_SENSORVALUES` / `MC_SET_SENSORVALUES` | read / write sensor values |
| 37 | 0x25 | `MC_GIVE_ACTZYKINDEX` | read active-cycle index |
| **38** | **0x26** | **`MC_SET_EINZEL_TEACH`** | **single-teach write** — ⭐ *not in the hex table above* |
| 39 | 0x27 | `MC_GIVE_EINZEL_TEACH` | single-teach read |
| 40 | 0x28 | `MC_GIVE_EINRICHTEN_STATUS` | read setup status |
| 44 | 0x2c | `MC_SET_DSP_GERAET` | write DSP device |
| 45 | 0x2d | `MC_DSP_STANDARD` | DSP standard |
| 48 | 0x30 | `MC_CIAB_COMMAND` | CIAB (adaptive) command — the segmented-transfer path |
| 50 | 0x32 | `MC_SETZYKLUSWITHTIME` | write cycle with time |
| 51 | 0x33 | `MC_GIVEPROGID` | read program id |
| 53 / 54 / 55 | 0x35 / 0x36 / 0x37 | `MC_GIVE_ACF_INFO` / `MC_SET_ACF_INFO` / `MC_SET_ACF_INFO_INTERN` | ACF (adaptive feed) info |
| 56 | 0x38 | `MC_GET_WKS_ID` | read workpiece id |
| 57 | 0x39 | `MC_GET_ACF_DATA` | read ACF data |
| 60 / 61 | 0x3c / 0x3d | `MC_GET_GERAET_ACF` / `MC_SET_GERAET_ACF` | device ACF read / write |

**Trend / streaming command family** — named in the binary's strings but not tied to a numbered
group-1 dispatch case. They drive the history screens and the live curves:

```
MC_SET_STREAMING      MC_GIVE_TREND_DATA      MC_GET_NEW_DATA_TREND
MC_GET_TREND_SETUP    MC_GIVE_SENSORVALUES    MC_GIVEDYNVALUES
```

⚠️ ⭐ **Cross-check against measurement.** Every one of the four commands the wire shows in the
steady-state poll loop appears in this table with the expected number: `22 → 0x16`
`GIVESAMMELMERKMALE`, `08 → 0x08` `GIVEPLCVALUES`, `01 → 0x01` `GIVESTATUS`, `51 → 0x33`
`GIVEPROGID`. The decimal/hex convention is confirmed on real traffic.

⚠️ Five commands the wire measured are **still unnamed in both tables**: `0x0D` (66 bytes —
identified by content as `SGeraetRec`, so it is `MC_GIVEGERAETEREC` or equivalent, §6.7),
`0x14` (36 bytes), `0x29` (40 bytes), `0x2a`, `0x2b`, `0x34`.

### 5.2.1 ⟦CAP1⟧ 🔴 Decimal vs hex — the numbering trap that runs through every source document


The application's own tag strings number commands in **decimal** (`bearbeite_Kom_27` = command
`0x1B`), the dispatch switch is naturally read in **hex**, and the earliest analysis documents
tabulated group 1 in **decimal** while every later one used hex. The two numbering schemes
describe the same 38 commands. This table is the bridge — it is the single most common source
of confusion when comparing an old document against a new one.

| dec | hex | Command | dec | hex | Command |
|---|---|---|---|---|---|
| 01 | `0x01` | `MC_GIVESTATUS` | 30 | `0x1e` | `MC_SETMUSTER` |
| 02 | `0x02` | `MC_GIVEGTYPE` | 31 | `0x1f` | `MC_GIVEMUSTER` |
| 04 | `0x04` | `MC_GIVEMERKMAL` | 33 | `0x21` | `MC_GIVE_CDR_DATA` |
| 05 | `0x05` | `MC_GIVEUSEDZYKTAB` | 35 | `0x23` | `MC_GIVE_SENSORVALUES` |
| 06 | `0x06` | `MC_GIVEKONFIG` | 36 | `0x24` | `MC_SET_SENSORVALUES` |
| 08 | `0x08` | `MC_GIVEPLCVALUES` | 37 | `0x25` | `MC_GIVE_ACTZYKINDEX` |
| 09 | `0x09` | `MC_SETPLCVALUES` | 38 | `0x26` | `MC_SET_EINZEL_TEACH` |
| 10 | `0x0a` | `MC_SETGERAET` | 39 | `0x27` | `MC_GIVE_EINZEL_TEACH` |
| 11 | `0x0b` | `MC_SETKANAL` | 40 | `0x28` | `MC_GIVE_EINRICHTEN_STATUS` |
| 12 | `0x0c` | `MC_SETZYKLUS` | 44 | `0x2c` | `MC_SET_DSP_GERAET` |
| 14 | `0x0e` | `MC_GIVEKANAL` | 45 | `0x2d` | `MC_DSP_STANDARD` |
| 15 | `0x0f` | `MC_GIVEZYKLUS` | 48 | `0x30` | `MC_CIAB_COMMAND` |
| 17 | `0x11` | `MC_ALARMGESEHEN` | 50 | `0x32` | `MC_SETZYKLUSWITHTIME` |
| 18 | `0x12` | `MC_GIVEALARM` | 51 | `0x33` | `MC_GIVEPROGID` |
| 19 | `0x13` | `MC_QUITALARM` | 53 | `0x35` | `MC_GIVE_ACF_INFO` |
| 21 | `0x15` | `MC_PRESSEDKEYS` | 54 | `0x36` | `MC_SET_ACF_INFO` |
| 22 | `0x16` | `MC_GIVESAMMELMERKMALE` | 55 | `0x37` | `MC_SET_ACF_INFO_INTERN` |
| 24 | `0x18` | `MC_GIVETEACHSTATUS` | 56 | `0x38` | `MC_GET_WKS_ID` |
| 26 | `0x1a` | `MC_GIVEHARDWAREREC` | 57 | `0x39` | `MC_GET_ACF_DATA` |
| 27 | `0x1b` | `MC_GIVESIGNALVERLAUF` | 60 | `0x3c` | `MC_GET_GERAET_ACF` |
| 28 | `0x1c` | `MC_GIVEOLDWORKPROZ` | 61 | `0x3d` | `MC_SET_GERAET_ACF` |

⚠️ **Three names in this table are not in the dispatch table above**, because they are
**send-only** and therefore have no receive-handler case label: `0x1e MC_SETMUSTER` (the write
counterpart of `0x1f GIVEMUSTER`), `0x26 MC_SET_EINZEL_TEACH` (counterpart of `0x27`), and
`0x3d MC_SET_GERAET_ACF` (counterpart of `0x3c`). They were recovered from the string dump in
the first analysis pass and are recorded here so the read/write pairing is complete.

German glossary for the table: `GIVE` = read · `SET` = write · `Zyklus` = cycle ·
`Kanal` = channel · `Merkmal` = feature · `Geraet` = device · `Muster` = pattern ·
`Alarm gesehen` = alarm seen · `Einzel Teach` = single-teach · `Einrichten` = setup.

### 5.2.2 ⟦MEAS⟧ `MC3_` command table as first recovered — decimal form


*Restored from `promos3_protocol_map.md` §2. ⚠️ **Superseded as an authority** by the binary's own
registry in §5.3.1, which is what the app uses. Kept because it records the `Sende_Kom_NN` tag
numbering, which is decimal and which is how you will find these functions, and because it lists
four commands the registry does not.*

| dec NN | Command | Direction(s) | Purpose | Status |
|---|---|---|---|---|
| 03 | `MC3_GET_CB_VERSION` | send + parse | control-board firmware version | ⬜ |
| 04 | `MC3_SENSOR_INFO` | send + parse | sensor descriptors | ✅ |
| 04 | `MC3_MERKMAL_INFO` | send | feature (Merkmal) info | ⬜ |
| 05 | `MC3_MERKMAL_INFO` | parse | feature info reply | ⬜ |
| 06 | `MC3_GERAETEREC` | send + parse | device record (`SGeraetRec`) | 🟡 (record ✅ via DB) |
| 07 | `MC3_SET_STREAMING` | send + parse | **start/stop the live stream** | 🟡 |
| 08 | `MC3_LIMIT_INFO` | send + parse | limit bands (`SGrenzRec`) | 🟡 |
| 08 | `MC3_EXTRALIMIT_INFO` | send | extended limits | ⬜ |
| 09 | `MC3_CYCLE_INFO` | send + parse | cycle record (`SZykRec`) | 🟡 |
| 09 | `MC3_EXTRACYCLE_INFO` | send | extended cycle | ⬜ |
| 09 | `MC3_EXTRA_MERKMAL_INCYCLE` | send | feature-in-cycle extra | ⬜ |
| 09 | `MC3_EXTRA_SENSOR_VFAKT` | send | extra sensor scaling factor | ⬜ |
| 09 | `MC3_MERKMAL_INCYCLE_SETTINGS` | send | feature-in-cycle settings | ⬜ |
| 10 | `MC3_PLC_SETTINGS` | send | PLC settings | ⬜ |
| 11 | `MC3_SENSOR_VFAKT` | send + parse | **sensor scaling factor (VFAKT)** | 🟡 |
| 12 | `MC3_MERKMAL_INCYCLE_SETTINGS` | send + parse | feature-in-cycle settings | ⬜ |
| 13 | `MC3_GERAETE_SETTING` | send | device settings | ⬜ |
| 14 | `MC3_SYSTEM` | send + parse | system info | ⬜ |
| 15 | `MC3_ALARM` | send + parse | **alarm / status** | ✅ |
| 16 | `MC3_EVENT` | send + parse | event log entry | 🟡 |
| 21 | `MC3_SENSOR_VFAKT` | send | sensor scaling (alt) | ⬜ |
| 24 | `MC3_SYSTEM_MODE` | send + parse | system operating mode | ⬜ |
| 26 | `MC3_PATTERN_INFO` | send + parse | pattern-monitoring info | ⬜ |
| 27 | `MC3_SET_OUTPUTS` | send + parse | set device outputs | ⬜ |
| 27 | `MC3_SIGNALVERLAUF` | send + parse | **signal trace (amplitudes)** | ✅ |
| 28 | `MC3_ETH_MAC_ADDRESS` | send + parse | device MAC address | ⬜ |
| 99 | `MC3_DOWNLOAD` / `DOWNLOADFILE` | send + parse | firmware / file download | ⬜ |

Legend as originally written: ✅ **VERIFIED** (byte layout proven) · 🟡 **PARTIAL** (command known,
purpose clear, body partly decoded) · ⬜ **NAMED** (command exists, body not decoded).

**`MC3_` tokens found in the binary's strings but never tied to a numbered handler.** Most were
resolved by the registry (§5.3.1); the four in bold were **not**, and remain unplaced:

`MC3_DEVICEREC` ✓(0x06) · `MC3_DEVICE_DESCRPTION` ✓(0x12) · `MC3_DEVICE_SETTING` ✓(0x0d) ·
`MC3_DOWNLOAD_IDENTIFIER` ✓(0x99) · `MC3_FEATURE_INFO` ✓(0x05) · `MC3_FEATURE_INCYCLE_SETTINGS`
✓(0x0c) · **`MC3_GET`** · **`MC3_GET_DATE`** · **`MC3_SET_DATE`** · **`MC3_SET_MODE`** ·
`MC3_GIVEGTYPE` ✓(0x02) · `MC3_GIVESTATUS` ✓(0x01) · `MC3_LAST_SIGNAL` ✓(0x11) ·
`MC3_LICENSE_INFO` ✓(0x19) · `MC3_UNKNOWN` ✓(0x00)

### 5.2.2 ⟦CAP1⟧ The `MC_` trend / streaming family


Recovered as tag strings in the first analysis pass, and **not yet tied to numbered handlers**.
They drive the history screen and the live curves on installations that use them:

```
MC_SET_STREAMING · MC_GIVE_TREND_DATA · MC_GET_NEW_DATA_TREND ·
MC_GET_TREND_SETUP · MC_GIVE_SENSORVALUES · MC_GIVEDYNVALUES
```

`MC_GIVE_SENSORVALUES` is `0x23` and `MC_GIVEDYNVALUES` has a recovered sender
(`Geraet_sendeKom_MC_GIVEDYNVALUES`, `FUN_004c6ca0`, §13.6). The four trend/streaming tokens have
neither a dispatch case nor a sender address recovered, and none of them appeared in the live
capture. ⚠️ **Do not assume the `MC_` side has a working streaming mode**: the streaming framings
in §4.5 are `MC3_`-only and gate on `getTargetType == 2`, so on this box they are dead code.

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

<!--add-->
**⟦CAP1 — added⟧**

**`MC3_` tokens seen in the string dump but never tied to a numbered handler.** The first
analysis pass grepped every `MC3_*` literal out of the binary. The registry above resolved most
of them. These four are the residue — they appear as strings but have no registry entry, no
dispatch case and no recovered sender:

<!--add-->
**⟦CAP1 — added⟧**

```
MC3_GET · MC3_GET_DATE · MC3_SET_DATE · MC3_SET_MODE
```

<!--add-->
**⟦CAP1 — added⟧**

⚠️ `MC3_GET` is plausibly a prefix fragment rather than a command. The date pair and
`MC3_SET_MODE` look like real commands that are either handled through a sub-command of
`MC3_SYSTEM` (`0x0e`) / `MC3_SYSTEM_MODE` (`0x18`), or belong to a firmware generation this
binary only partly supports. Recorded so nobody re-greps for them; not blocking, and irrelevant
to this `MC_` box.

<!--add-->
**⟦CAP1 — added⟧**

For completeness, the following tokens *were* on the same unresolved list in the first pass and
**are now resolved** by the registry: `MC3_DEVICEREC` (`0x06`), `MC3_DEVICE_DESCRPTION` (`0x12`),
`MC3_DEVICE_SETTING` (`0x0d`), `MC3_DOWNLOAD_IDENTIFIER` (`0x99`), `MC3_FEATURE_INFO` (`0x05`),
`MC3_FEATURE_INCYCLE_SETTINGS` (`0x0c`), `MC3_GIVEGTYPE` (`0x02`), `MC3_GIVESTATUS` (`0x01`),
`MC3_LAST_SIGNAL` (`0x11`), `MC3_LICENSE_INFO` (`0x19`), `MC3_UNKNOWN` (`0x00`).

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

<!--variant-->
**⟦MEAS — variant⟧**

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

<!--variant-->
**⟦CAP1 — variant⟧**

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
- 🔴 **The live capture did not contain a single `0x1b` transaction.** The app polls the trace
  only when a trace view is open and the machine is producing one; the capture window was idle.
  So the entire body layout in this section — the 5-byte header, the 125 samples, the trailer —
  **remains Ghidra-derived and unconfirmed against real bytes**, and `channelKey` (G9) is still
  open. This is the primary reason a second, *busy-machine* capture is the top-priority action
  (§0.7, §33.11).

<!--variant-->
**⟦FIELD — variant⟧**

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
<!-- FIELD -->
> ### ⚠️ FIELD — `0x1B` was never seen. Everything above is unvalidated, and 257 is withdrawn.
>
> Seven captures, 219,994 exchanges, **zero instances of `0x1B`**. It is not in the poll
> loop; 154 s of continuous cutting produced none; and it is not emitted by the `EventList`,
> `AlarmManager`, `DataLog`, `MonitoringSettings`, `System` or `CycleManager` screens. The
> structure above therefore stands as 🔶 GHIDRA and nothing more. The size **257 is
> withdrawn** — it came from a synthetic test.
>
> **It may not matter.** `0x1B` is the *waveform* (125 consecutive samples). `0x16`, now
> fully decoded (§25.1), is the *envelope* — `(min,max)` per 20 ms window. PROVIS3 itself
> stores only the envelope: `WP_0000N_01` holds exactly the `0x16` row and the waveform is
> drawn on screen and discarded. For SQL, trending, reporting and alarms, everything the
> application retains is already available. §25.5 gives the one-line way to find `0x1B`
> without a capture.

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

<!--add-->
**⟦CAP1 — added⟧**

> ✅ **Confirmed on real bytes (§33.6).** **363 / 363** `0x16` messages in the capture satisfy
> `len = count × 10 + 1` with remainder 0, across row counts 3–9:
>
> | rows in answer | 3 | 4 | 5 | 6 | 7 | 8 | 9 |
> |---|---|---|---|---|---|---|---|
> | messages | 6 | 36 | 90 | 134 | 75 | 17 | 5 |
>
> And `recordSize = 10` is `featureCount × 2 + 2` for **featureCount = 4** — the four PROCUR-S
> sensors, **arrived at independently from the wire** rather than assumed from the config record.
> Part 17 §8's stride formula and the §3.7 completion formula are the same formula, and both are
> now measured. `DATA[1]` is confirmed as the row count.

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

<!--variant-->
**⟦CAP1 — variant⟧**

⚠️ The decompiler shows rows starting at `Data+0x10`, which is the same byte as the count; the
`+1` in the size formula says rows start *after* it. Assume `base = 0x11` and confirm on the first
real block. ✅ The capture's `len = count × 10 + 1` result confirms the arithmetic (`+1` = the
count byte, rows after it), though not the in-memory offset.

<!--variant-->
**⟦CAP1 — variant⟧**

⚠️ `Geraet+0x688` — the flag that becomes request byte 2 of `0x16` — was recorded here as "sent
as 0". 🔴 **It is sent as `0x01` on this box** (§0.7 C30): the live request is
`00 00 00 16 01 01 e7`. So the flag is *set*. Its meaning is still unknown.

<!--variant-->
**⟦FIELD + MEAS — variant⟧**

⚠️ The decompiler shows rows starting at `Data+0x10`, which is the same byte as the count; the
`+1` in the size formula says rows start *after* it. Assume `base = 0x11` and confirm on the first
real block.

<!--variant-->
**⟦MEAS — variant⟧**

⚠️ `Geraet+0x688` — the flag that becomes request byte 2 of `0x16` — is sent as 0 and its meaning
is unknown.

<!--variant-->
**⟦FIELD — variant⟧**

⚠️ `Geraet+0x688` — the flag that becomes request byte 2 of `0x16` — is sent as 0 and its meaning
is unknown.
<!-- FIELD -->
> ### ⚠️ FIELD — several of the caveats above are now settled on the wire
>
> - **Row base resolved.** Payload byte 0 is the row count; rows begin at payload byte 1. The
>   `+1` in the size formula wins over the decompiler's apparent `Data+0x10`. ✅ WIRE
> - **Row layout resolved.** `+0..+7` are four `(min,max)` pairs, `+8/+9` are status bytes —
>   confirmed four independent ways, including an exact 64/64 bijection with the escape rows.
>   ✅ WIRE
> - **`Geraet+0x688` is 1, not 0.** The captured request is `16 01 01 <ck>` — station 1,
>   byte 2 = 1 — and its checksum closes on that reading for both units. ✅ WIRE
> - **`0xFF` in a *Max* byte is ordinary saturation, not an escape.** Only `row[0] == 0xFF`
>   marks an escape.
> - **The row count is a backlog, capped at 100.** Never poll `0x16` slower than ~2 s per
>   unit or samples are lost silently — the answer still arrives and still checksums.
>
> §25.1.

### 6.2.1 ⭐ The row layout, decoded 📐 (§0.6 C35)

**This is the substantive decode gain of the whole measurement phase.** 22,234 `0x16` exchanges
yielded **15,521 measurement rows** — enough to test a layout rather than guess one
(Part 35 §D.4).

```
payload[0]             = row count n              (0 … 100 observed)
payload[1 + r*10 … ]   = row r, 10 bytes:

  +0  Min_F0   +1  Max_F0      feature 0    (unit 2: VIBRATION)
  +2  Min_F1   +3  Max_F1      feature 1    (unit 2: M131 DEBI)
  +4  Min_F2   +5  Max_F2      feature 2    (unit 2: M131BASINC)
  +6  Min_F3   +7  Max_F3      feature 3    (unit 2: M08 DEBI)
  +8  status0                  flags, observed {0x00, 0x10, 0x20, 0x30}
  +9  status1                  flags, observed {0x00, 0x20, 0x80, 0xA0}
```

stride = `featureCount × 2 + 2 = 4×2 + 2 = 10`, **exactly as predicted above** — and `base = 0x11`
is confirmed: rows start *after* the count byte.

**The positional model was right; the semantics were not.** The two bytes of each feature pair
are not `lo`/`hi` with `hi` as a status byte. They are **`(minimum, maximum)`** of that feature
over the sample:

| test | result |
|---|---:|
| feature pairs examined (non-escape rows) | **61,764** |
| pairs where `byte[2f] > byte[2f+1]` | **0** |

Zero inversions in 61,764 samples. The two bytes of each pair also share an identical value range
per feature — feature 0 spans 0–35 on both bytes, feature 1 spans 0–108 on both, feature 2
0–111, feature 3 0–114. That is what a `(min, max)` pair of one signal looks like, and is not
what a `(value, flags)` pair looks like.

**Independent corroboration from the storage side.** Part 10 records the per-workpiece
measurement tables as storing a per-sensor min/max envelope:

```
WP_00001_01 :  Min_S01, Max_S01, Min_S02, Max_S02, Min_S03, Max_S03, Min_S04, Max_S04
```

Four `(min, max)` pairs, one row per sample index — **byte for byte the wire layout above.** The
storage schema and the wire format are the same structure. That answers the open question of how
the app gets from `0x16` to `WP_*`: **it does not transform anything, it writes the rows
through.** It also confirms the raw-0–255 amplitude representation (Part 7) from a third
independent direction.

#### The escape mechanism — confirmed by an exact bijection ✅ 📐

The escape model above (`lo == 0xFF`, `hi` selects the marker, the *following* row carries the
parameter) is confirmed in every particular:

| test | result |
|---|---:|
| rows with `byte[0] == 0xFF` | **64** |
| rows where any `min > max` | **64** |
| overlap | **64** |
| escape rows that do *not* violate `min ≤ max` | **0** |
| violating rows that are *not* escapes | **0** |

An exact bijection. The escape is the **only** thing in 15,521 rows that breaks the `min ≤ max`
invariant — which confirms both models at once and hands a reader a **free integrity check: a
non-escape row with `min > max` means the reassembly is wrong.** That check catches precisely the
class of bug that C32/C33 would have caused.

Every one of the 64 escapes carries marker `0xFB` — the documented *"per-feature reset across all
features"* — replicated across all four feature slots, with the parameter in the next row exactly
as specified:

```
row r    :  ff fb  ff fb  ff fb  ff fb  30 a0      <- escape, marker 0xFB, all four features
row r+1  :  00 01  00 01  00 01  00 01  30 a0      <- the parameter row
```

⚠️ Markers `0x00` (new cycle) and `0xFE` (workpiece ID) **do not appear** in any capture — no
cycle boundary and no workpiece change occurred in any captured window. Their handling, and the
double-buffering behaviour that depends on the `0x00` marker, stay 🔶 GHIDRA.

🔴 **Do not read `0xFF` in a Max byte as an escape.** Rows such as `fe ff 01 01 01 01 27 27` are
ordinary **saturated** readings (`min` 254, `max` 255) and they occur in real data. The escape is
signalled by `byte[0]` — the *minimum of feature 0* — and only there.

#### Row-count behaviour 📐

| rows per poll | occurrences | note |
|---:|---:|---|
| 0 | 7,964 | nothing new since the last poll; payload is 1 byte |
| 1 | 14,164 | steady state |
| 2 – 4 | 94 | |
| 37, 74, 100 | 12 | **backlog flush** — 100 rows = 1,001 bytes = 144 frames |

At 77.6 poll cycles per second and typically one row per cycle, the effective sample rate is
**≈78 Hz per unit** in capture 3. Capture 1, on a lighter poll cadence, measured the *device's*
own feature sample rate directly at **50.1 rows/s (unit 1)** and **49.8 rows/s (unit 2)** — i.e.
the device samples at **50 Hz** and the app's `0x16` poll rate floats to match, taking 3–9 rows
per poll when it polls more slowly than the device samples. Both numbers are real; they measure
different things. **Size buffers for the device rate (50 Hz), not the poll rate.**

⚠️ The occasional 100-row burst is the device emptying a buffer. **A reader that cannot handle a
144-frame answer loses exactly the bursts** — the densest data on the wire.

⚠️ `expected == 1` (row count 0) is **not** the "`expected == 0` → pure ack" case of §3.7. It is
a one-byte payload plus a checksum, in one frame. No zero-length answer occurs in any capture, so
the pure-ack path remains 🔶 GHIDRA.

⚠️ The status bytes `+8` / `+9` take only four values each in 15,521 rows, and their meaning is
not established. The `hi`-bit table above (teach `0x01`, start/stop `0x10`, tool change `0x40`,
`0x08` → status bit 7) was derived for the *feature* bytes under the old model and should be
re-read as applying to these two trailing status bytes. `0x10`/`0x20`/`0x30` on `status0` and
`0x20`/`0x80`/`0xA0` on `status1` are consistent with that but do not prove it. ⚠️ INFERRED.

### 🔴 What the capture could **not** settle: the row's internal layout

This is the largest single gap left in the whole project, and it is worth being precise about why
the capture did not close it.

The `0x16` row is **10 bytes with 4 feature slots and a trailing `+2`**. The two candidate splits
are:

```
candidate A:   [f0 lo][f0 hi][f1 lo][f1 hi][f2 lo][f2 hi][f3 lo][f3 hi][extra][extra]
candidate B:   [extra][extra][f0 lo][f0 hi][f1 lo][f1 hi][f2 lo][f2 hi][f3 lo][f3 hi]
```

**Both parse the captured data identically**, because the captured data never moves:

- Unit 2: **1,058 of 1,058** measurement rows are **all-zero**.
- Unit 1: all 1,064 rows are near-constant —
  `00 00 00 | 01 00 | 01 00 00 26 26 00 20` — i.e. one feature pair parked at `0x26`/`0x25`
  (38/37) and one byte-pair toggling 0/1.
- **Zero `0xFF` escape bytes in the entire file.** No new-cycle marker, no workpiece ID, no
  `0xFB` reset, no alarm. The whole escape mechanism above is therefore **still Ghidra-derived
  and unconfirmed**.

A row that never changes cannot distinguish which pair belongs to which feature, nor which two
bytes are the trailing `+2`. **Only a machine that is cutting can.** (§33.9)

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

## 6.7 Bodies decoded from the wire 📐 — index

Six further `MC_` bodies were decoded from capture 2, taking group-1 body coverage from 2 of 38
to **9 of 38**. Full detail is in **Part 34 §C.10**; this is the index.

| cmd | name | size | what it gives you | §|
|---|---|---:|---|---|
| `0x06` | `GIVEKONFIG` | 14 | `[version][channels][sensors]` at offsets 0/1/2 — `e5 01 04`, byte-identical to the runtime log's "Version 229 Channels 1 Sensors 4". **The `E5 01 04` anchor Part 15 predicted a capture would find — and it sits at payload offset 0 with nothing in front of it, which is G1 closing by deletion, on the wire** | C.10.1 |
| `0x0D` | *(unnamed → **`SGeraetRec`**)* | 66 | 🔶 **The single most useful discovery command on the box.** One answer gives `GeraetTyp 0x44`, `GSubType 5`, 1 channel, 4 sensors, 8 × sensor-type slots (`0x80` PROCUR-S), and `ReduzLim 6612` LE. **Six independent field matches** against values derived from a completely different source (the PMD export `1974.txt`) | C.10.5 |
| `0x0E` | `GIVEKANAL` | 144 | The `SKanalRecV40` channel record, and with it **the feature descriptor block at body `+0x4D`, stride 12, `[mask][11-byte name]`** — plus the proof that `mask & 0x0F` is **one-hot**, so `index = log2(mask & 0x0F)`. `CDRLim` confirms as `aa aa aa aa` at `+0x10` | C.10.3 |
| `0x12` | `GIVEALARM` | 17 | A **16-entry ring** of stored alarms, walked by `[0x12][station][index][00]` with `index` 0x00–0x0F — and the **device wall-clock timestamp decoded** at `+0x0A..0x0F` as **day, month, year(+2000), hour, minute, second** | C.10.4 |
| `0x02` | `GIVEGTYPE` | 3 | `44 05 01` — `GeraetTyp`, `GSubType`, 1. ⚠️ **No serial number**; 14 bytes would be needed to carry one, and the table's 14 is wrong | C.10.6 |
| `0x08` | `GIVEPLCVALUES` | 5 | `00 00 XX 00 ff`, with byte 2 **genuinely live** — 7 distinct values across the capture (`0x01`×7,505, `0x00`×4,473, `0x04`×2,991, `0x03`×2,431, `0x40`×2,079, `0x05`×1,412, `0x02`×1,343). The low bits look like a small bit-field and `0x40` stands apart — plausibly the tool-change bit. ⚠️ INFERRED | C.10.7, D.7 |
| `0x23` | `GIVE_SENSORVALUES` | 14 | Carries live data; `args` is the round-robin sensor slot (`Geraet+0x60`) — unit 1 walks 4–7, unit 2 walks 0–3. Unit 2's bodies open `0x80` / `0x81` = **PROCUR-S / PROCUR-I**, so the sensor-type byte is at body offset 0. 🔶 | C.10.7 |
| `0x16` | `GIVESAMMELMERKMALE` | `n×10+1` | §6.2.1 above | D.4 |
| `0x1B` | `GIVESIGNALVERLAUF` | — | 🔴 **Never observed.** §6.1 remains the code-derived layout | — |

⚠️ **A warning that applies to all of the short bodies.** The machine was idle or in steady state
for every captured second. `0x01 GIVESTATUS` returned `00 00` and `0x33 GIVEPROGID` returned
`00 00` on **every one of 11,117 polls each**; `0x25 GIVE_ACTZYKINDEX` returned `00 00 00`;
`0x14` returned 36 zero bytes and `0x29` returned 40. **Their sizes are trustworthy. Their
contents say nothing about field layout.** Do not infer "this field is always zero" from an idle
machine.

---

# ═══════════════════════════════════════════════════════════════
# PART 7 — SCALING (raw → physical)   ✅ RESOLVED: NO FACTOR
# ═══════════════════════════════════════════════════════════════

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

<!--add-->
**⟦CAP1 — added⟧**

> **Historical note — where the scaling question came from.** The first analysis pass identified
> a real mechanism and correctly flagged it as unresolved: `MC3_SENSOR_VFAKT`
> (*Verstärkungsfaktor* = gain factor) as a per-sensor multiplier, plus a **`FindProcurFactors`**
> routine reading `SFactor1..4` from **`SFactors.ini`**, with a rule of thumb from the code that
> "many values scale by ×0.001". That mechanism exists in the binary. It is simply **not used by
> this device generation**: the VFAKT worker is a stub, `SFactors.ini` is absent, and every
> database column that would carry a scaled value carries raw counts instead. The mechanism is
> recorded here so that a future install which *does* ship `SFactors.ini` is recognised for what
> it is rather than treated as a contradiction of this Part.

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

> ### ⚠️ FIELD — that is `MiSensType[8]`; there is a separate `SensorType[4]` and it differs per unit
>
> `MiSensType[8]` at `SGeraetRec +0x1A` is `0x80` ×8 on **both** units — this is the sentence
> above, and it is correct. But `+0x16..+0x19` (called `za_mi_area` and marked INFERRED in
> §9.1) is `SensorType_1..4`, and it is **not** the same:
>
> | Unit | serial | `SensorType_1..4` | resolves to | operator feature names |
> |---|---|---|---|---|
> | 1 | 10659 (`exVL2-*.txt`) | `00 00 00 00` | none set | `SPINDEL · X AXIS · Y AXIS · Z AXIS` |
> | 2 | 10663 (`1974.txt`) | `30 14 14 14` | **VBI 211**, PA 211, PA 211, PA 211 | `VIBRATION · M131 DEBI · M131BASINC · M08 DEBI` |
>
> Slot 0 of unit 2 holds a **vibration** sensor (`0x30 = VBI 211`) and the operator named
> feature 0 **`VIBRATION`**. That correspondence is an independent cross-check on the
> `+0x16 = SensorType_1..4` identification. §25.2.1.

## 8.3 ChannelStatus (0–7) 🔶

<!--variant-->
**⟦MEAS — variant⟧**

`0=Not 1=OK 2=Wrong 3=Later 4=(?) 5=Reset 6=Suppressed 7=Alarm missing`

<!--variant-->
**⟦MEAS — variant⟧**

⚠️ Slot **4** has no label in the recovered table. It is not "absent" — it is present and blank.
Do not renumber around it.

<!--variant-->
**⟦FIELD + CAP1 — variant⟧**

`0=Not 1=OK 2=Wrong 3=Later 5=Reset 6=Suppressed 7=Alarm missing`

<!--add-->
**⟦CAP1 — added⟧**

⚠️ **`4` is a hole in the table** — it is a valid value in a 0–7 range but no label was recovered
for it. Do not silently map it onto a neighbour; print it as `Unknown(4)`.

## 8.4 AccessLevel 🔶

<!--variant-->
**⟦MEAS + CAP1 — variant⟧**

`00=Operator 01–03=Operator 1-3 04=Setter 05=Administrator 06=Machine manufacturer 63=SERVICE`

<!--variant-->
**⟦CAP1 — variant⟧**

(The `01–03` "Operator 1/2/3" tier came from the first analysis pass and is easy to lose when
only the round numbers are quoted. `63` is decimal 99.)

<!--variant-->
**⟦FIELD — variant⟧**

`00=Operator 04=Setter 05=Administrator 06=Machine manufacturer 63=SERVICE`

## 8.5 EventCode (selected) 🔶

<!--variant-->
**⟦MEAS — variant⟧**

*Restored in full from `promos3_protocol_map.md` §4; v3 carried an abridged subset.*

<!--variant-->
**⟦MEAS + CAP1 — variant⟧**

```
01 RTC Set                  02 Cycle settings change    03 Limit change
04 Cycle mode change        06 List cleared             07 Device renamed
08 Feature change           09 Sensor change            0B Cycle Amp. factor
0D Unit change              0E PLC change               0F Download
11 Alarms Ack               13 Op. Mode change          14 Reboot
15 System mode change       33–39 system errors         FF Empty
```

<!--variant-->
**⟦CAP1 — variant⟧**

The full recovered list, merged from `initStatusTables` and the first-pass string dump. Earlier
documents printed an abridged version of this table; the abridged form is a subset, not a
correction.

<!--variant-->
**⟦CAP1 — variant⟧**

⚠️ `05`, `0A`, `0C`, `10`, `12` and `16..32` have no recovered label. Treat them as
`Unknown(NN)` rather than assuming they are unused.

<!--variant-->
**⟦FIELD — variant⟧**

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

<!-- FIELD -->
> ### ⚠️ FIELD — `+0x14` is `Serial_Num`, big-endian. The `date_or_crc` label below is wrong.
>
> The struct below marks `+0x14` as `date_or_crc // INFERRED (1974.txt: 29 A7)`. It is the
> **serial number, stored big-endian inside an otherwise little-endian record** — the only
> mixed-endian field known in the protocol.
>
> ```
> 1974.txt        +0x14 = 29 A7   →  BE 0x29A7 = 10663   = Unit 2   ✅ matches the runtime log
> exVL2-1/2.txt   +0x14 = 29 A3   →  BE 0x29A3 = 10659   = Unit 1   ✅ matches the runtime log
> ```
>
> Read little-endian the same bytes give 42793 and 41769 — large, plausible, and wrong.
> 🔴 This is the kind of error that ships. §25.2.1, and **F15** in §0.7. Also add:
> `+0x16..0x19 = SensorType_1..4` (the `za_mi_area` line below), `+0x04..0x07 =
> CDR / Setup / PLC_Konf / Setup_Coll`, `+0x22 = SampleDiv`.

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

<!-- FIELD -->
> ### ⚠️ FIELD — the warning below is right; the example under it is only half the install
>
> This section, and ledger entry **C12**, treat `SPINDEL / X AXIS / Y AXIS / Z AXIS` with
> masks `0x81/0x82/0x84/0x88` as a **report-v1 error corrected by `1974.txt`**. It was not an
> error. `1974.txt` is **unit 2**; `exVL2-1.txt` and `exVL2-2.txt` (both in this project,
> byte-identical to each other) are **unit 1**, and they carry `SPINDEL / X AXIS / Y AXIS /
> Z AXIS` at `+0x4D` with masks `0x81/0x82/0x84/0x88`. Both name sets are real, on the same
> installation. The live `0x0E` answers confirm it per unit.
>
> This does not weaken the warning — it strengthens it, because the two units of one machine
> disagree. But it means **C12 must be read as a narrowing, not a reversal**, and it means
> the `--config-unit 1=exVL2-1.txt --config-unit 2=exVL2-1.txt` line in §17.6 and in
> `run_commands.txt` labels unit 2 with unit 1's features. §22.5.3.

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

<!--add-->
**⟦MEAS — added⟧**

**The full 144-byte struct**, restored from report v1 §7.2 (v3 carried only the verified-field
table). Fields marked INFERRED are positional reasoning against the `Channels` table's column
order, not byte-proven:

<!--add-->
**⟦MEAS — added⟧**

```c
#pragma pack(push,1)
typedef struct {
    uint8_t  PLC_Type;              // +0x00 VERIFIED (0x10)
    uint8_t  PLC_Version;           // +0x01 VERIFIED (0x20)
    uint8_t  Channel_Num;           // +0x02 VERIFIED
    uint8_t  cfg03[3];              // +0x03 INFERRED (Teach_Type / Teach_Amount …)
    uint8_t  Spindle_Delay;         // +0x06 INFERRED (0x0a)
    uint8_t  Sync_Barrier;          // +0x07 INFERRED (0x0a)
    uint8_t  cfg08[8];              // +0x08 INFERRED
    uint8_t  CDRLim[4];             // +0x10 VERIFIED (0xAA each) — 📐 re-confirmed on the wire
    uint8_t  reserved14[0x4D-0x14]; // +0x14 INFERRED (Sens_Link / MDL_* + pad)
    SKanalFeature features[4];      // +0x4D VERIFIED — 📐 re-confirmed on the wire, both units
    uint8_t  tail[144 - (0x4D+48)];
} SKanalRecV40;                     // 144 bytes
#pragma pack(pop)
```

<!--add-->
**⟦MEAS — added⟧**

📐 **The whole record is now confirmed end to end**: `0x0E GIVEKANAL` answers exactly **144
bytes**, `CDRLim` reads `aa aa aa aa` at body `+0x10`, and the four 12-byte descriptors sit at
body `+0x4D` on both units — with two entirely different name sets in the same firmware
(Part 34 §C.10.3). **The at-rest layout and the on-wire layout are the same bytes**, which is the
strongest single validation of the PMD-versus-database cross-referencing method.

**Reader rules:**

- **Read feature names dynamically from `SKanalRec`** — they are operator-assigned per machine,
  and on this box they are Turkish/German shop-floor labels. A wrong label will look plausible.
- The **low nibble** (`0x01 / 0x02 / 0x04 / 0x08`) is the feature-select bit; the **high `0x80`
  bit is a separate flag** (set in the other machine's example, clear here). Match on
  `mask & 0x0F` (or the bit position) and treat `0x80` as a flag — do **not** key on
  `mask == 0x81`.

## 9.3 `SGrenzRec` / `SHardwareRec` / `SZykRecV4802`

<!--variant-->
**⟦MEAS — variant⟧**

- **`SGrenzRec`** (limits, 14 bytes) — `1974.txt`:
  `d9 01 04 04 04 00 04 fa fc 07 08 32 08 fa`. Full column mapping to table `Limits`:
  `Limtype, Level, Feat_Num, Response_Time, Act_Start, Act_End (≈ 0xfa/0xfb = 250/251), Act_Mode,
  Pattern_Ref`. 🔶 Levels seen on this box: **20 / 35 / 50 / 70 / 115 / 140 / 152 / 170** — the
  same raw 0–255 units as the amplitude (Part 7). Size 14 matches the size-table entries for
  commands `0x02` and `0x28`. ✅

<!--variant-->
**⟦MEAS — variant⟧**

  ⚠️ **Coincidence worth flagging, not a finding.** The measured 14-byte body of
  `0x06 GIVEKONFIG` is `e5 01 04 04 04 00 04 fa fc 07 08 32 08 fa` — identical to the
  `SGrenzRec` example above except for its first byte. Both are 14 bytes and both end
  `… fa fc 07 08 32 08 fa`. Either the two records share a tail structure, or the PMD export and
  the wire answer are the same block viewed through different first-byte semantics. Unresolved;
  recorded so the next person notices it too.
- **`SHardwareRec`** (46 bytes) — `1974.txt`: `02 01 02 03 04 00 …` (mostly zero). Hardware
  ID/version block; table `Hardware` (`Board_Vers`, `Del_Date1..4`). 🔶
  📐 **`0x1A GIVEHARDWAREREC` measures 46 bytes**, resolving v3's "⚠️ but `GIVEHARDWAREREC` is
  `0x1a`, not `0x10`" **in favour of the command name**: the record size is right, the table's
  key is wrong (§0.6 C28).
- **`SZykRecV4802`** (cycle, 170 bytes) — 9 records present in `1974.txt`; size 170 confirmed.
  Maps to table `Cycles` (`Name`, `Duration`, `MonIndex`, `Sensor_Ref1..4`, `Feature_Ref1..4`,
  `Limit_Ref1..8`, `PLCRep_Ref1..8`, …) and `Cycle_Sensors` (`Sens_Param1..3`, `Gain`, `Meantime`,
  `Komp_Start`). Size 170 matches the size-table entry for `0x03`.

<!--variant-->
**⟦MEAS — variant⟧**

  📐 **And it is the true size of `0x0F GIVEZYKLUS`** — measured at **170 bytes**, against the 40
  the size table claims for `0x0F`. The 170 in the table is real; it is filed under the wrong key
  (§0.6 C28). ⚠️ The captured body is cycle 0, unconfigured, so its **contents** teach nothing.

<!--variant-->
**⟦MEAS — variant⟧**

  **Internal offset map**, restored from report v1 §7.3 (v3 omitted it):

<!--variant-->
**⟦MEAS — variant⟧**

  | Offset | Field | Confidence |
  |---|---|---|
  | +0x00 | cycle index / flags | 🔶 |
  | +0x04 | `Duration` (16-bit LE) | 🔶 |
  | +0x0A | monitor / teach params | 🔶 |
  | +0x12, +0x16, +0x1A | 32-bit counters / times | 🔶 |
  | +0x5D.. | embedded per-feature limit blocks | 🔶 |
  | last 14 | trailer `14 14 14 14 00×5 0a 0a 0a 0a 00` | ✅ terminator |

<!--variant-->
**⟦MEAS — variant⟧**

  The embedded limit blocks near `+0x5D` map to the `Limits` table (`Limtype` / `Level` /
  `Feat_Num`), separated by `0xFB` markers (`Act_End ≈ 251` recurs throughout `Limits`). Decoded
  examples from `1974.txt`: `Level=0x91 window 0x14` · `Level=0x7d Feat=01` · `Level=0x7d Feat=02`
  · `Level=0xa0 Feat=03`. **These are the upper/lower monitoring bands per feature — the green
  threshold lines on the HMI**, and therefore what G8's "%" display needs.

<!--variant-->
**⟦CAP1 — variant⟧**

- **`SGrenzRec`** (limits, ~14 bytes) — `1974.txt`:
  `d9 01 04 04 04 00 04 fa fc 07 08 32 08 fa`. Maps to table `Limits` (`Limtype`, `Level`,
  `Feat_Num`, `Act_End` ≈ 251, …). Levels seen on this box: 20 / 35 / 50 / 70 / 115 / 140 / 152 /
  170. Size 14 matches the size-table entries for commands `0x02` and `0x28`. ✅
  ⚠️ `Act_End ≈ 251` is worth noting because it sits just under 255: it is a **window position**
  in the same 0–255 space as everything else, not a saturated amplitude.
- **`SHardwareRec`** (~46 bytes) — `1974.txt`: `02 01 02 03 04 …`. Table `Hardware`
  (`Board_Vers`, `Del_Date1..4`). Size 46 matches the size-table entry for `0x10`
  (⚠️ though `GIVEHARDWAREREC` is command `0x1a` — see §3.5.2).
- **`SZykRecV4802`** (cycle, 170 bytes) — 9 records present in `1974.txt`; size 170 confirmed.
  Maps to table `Cycles` (`Name`, `Duration`, `MonIndex`, `Sensor_Ref1..4`, `Feature_Ref1..4`,
  `Limit_Ref1..8`, `PLCRep_Ref1..8`, …) and `Cycle_Sensors` (`Sens_Param1..3`, `Gain`, `Meantime`,
  `Komp_Start`). Size 170 matches the size-table entry for `0x03`. Structure recovered in the
  first pass: a cycle-index header, `Duration` at `+0x04`, counters, then **embedded per-feature
  limit blocks**, and a distinctive **trailer `14 14 14 14 … 0a 0a 0a 0a 00`** — that trailer is
  a useful sync marker when locating cycle records in a raw PMD dump by eye.

<!--variant-->
**⟦FIELD — variant⟧**

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
                 GatewayAddress = 192.168.222.17   🔴 STALE — measured .16 (§0.7 ⟦CAP1⟧ C25; §23.1; §33.1)
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

<!--add-->
**⟦CAP1 — added⟧**

🔴 **`GatewayAddress` is stale in this INI copy.** The live capture shows every datagram
exchanged with **`192.168.222.16`**, not `.17`. This is the one configuration value in the file
that a reader must **not** trust — see §0.7 C25 and §33.1. It also means that any tool which
bootstraps itself purely from `PROVISsettings.ini` will silently send to a host that does not
answer, and will look exactly like a dead bus.

<!--add-->
**⟦CAP1 — added⟧**

⚠️ **Related, and easy to get wrong:** the gateway replies from an **ephemeral source port**
(`:50375` in the capture), not from 1789. The app binds :1789 locally and reads whatever arrives;
a reader that filters on *source* port 1789 will discard every answer.

Reading INI values goes through `ini_readInt` (`FUN_00437f50`), which `tryLock`s for 3000 ms and
raises an `ErrorManager` entry on timeout.

---

# ═══════════════════════════════════════════════════════════════
# PART 13 — COMPLETE FUNCTION REFERENCE
# ═══════════════════════════════════════════════════════════════

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

<!--variant-->
**⟦MEAS — variant⟧**

| Address | Name | Conf. |
|---|---|---|
| FUN_004236f0 | `initStatusTables` — builds the decoder rings (ToolStatus @+0x44, SensorType @+0x4c, …) | 🔶 |
| FUN_00437f50 | `ini_readInt` — INI integer read (`tryLock` 3000 ms → ErrorManager on timeout) | 🔶 |
| FUN_004041c0 | `ErrorManager_log` — app-wide log entry (category, level, msg) | 🔶 |
| FUN_00403650 | `ErrorManager_initLogFile` — reads `[ErrorManager] WithDebug`; opens `<settingsDir><LogFile>`; writes `"LOG START at: %1; Version: %2"`. Log device = `DAT_00a1a000` | 🔶 |
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

<!--variant-->
**⟦FIELD + CAP1 — variant⟧**

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

<!--variant-->
**⟦MEAS — variant⟧**

…plus all `QListData::*` wrappers and the QMap/QVector detach/insert/free family, which are
identifiable by signature alone.

<!--variant-->
**⟦FIELD + CAP1 — variant⟧**

…plus all `QListData::*` wrappers and the QMap/QVector detach/insert/free family, which are
identifiable by signature alone. The full low-level Qt-container / QString plumbing catalog from
the earliest version of this analysis is unchanged and omitted here for brevity; it is
name-and-forget and not needed to build the reader.

## 13.16 Restored catalog — the functions v3 omitted for brevity

v3 stated that "the full low-level Qt-container / QString plumbing catalog from the earliest
version of this analysis is unchanged and omitted here for brevity." A mechanical diff of every
`FUN_` address across all fifteen source documents finds **57 functions named in an earlier
document that do not appear in v3 at all** — and they are not all Qt plumbing. The Ethernet-server
set, the sensor-DB reconciliation chain and the stream-reader helpers are real subsystem
functions. All 57 are restored below so this document is a complete index.

⚠️ Addresses marked **†** came from handoff notes rather than functions opened directly; verify
the address lands correctly before committing the rename in a build.

### 13.16.1 Transport — PEAK hardware path (never taken on this box)

| Address | Name | Purpose |
|---|---|---|
| FUN_00504700 | `CanInterface_cleanupHwClients` | PEAK-only teardown: `CAN_DisconnectFromNet` / `CAN_RemoveClient` / `CAN_RemoveNet` over 16 clients. Gateway mode never runs this |
| FUN_00504530 | `canApi_resolveAndCall` | `dlsym` + invoke a `CanApi2.dll` export |
| FUN_00504310 | *(unresolved — listed as a duplicate in the v1 index)* | recorded so nobody re-derives it |

### 13.16.2 Reassembly helpers

| Address | Name | Purpose |
|---|---|---|
| FUN_006840b0 | `QListData_free` | free a `QListData` |
| FUN_00408d60 | `bufferMap_erase` | remove a unit entry from the buffer map |
| FUN_007a2e30 | `QVector_append` | the reassembly-buffer append |

### 13.16.3 Stream-reader helpers — how every body decoder reads its bytes

**This set is worth having.** Every `bearbeite_Kom_*` body decoder in Part 6 is written in terms
of these six calls; Qt4 places `QByteArray::Data`'s payload at `+0x10`, which is why that constant
appears throughout.

| Address | Name | Purpose |
|---|---|---|
| FUN_004423e0 | `stream_peekCurrent` | peek the current byte container (`+8` remaining, `+0x10` first byte). **Returns the *wire* bytes** — contrast `stream_peekU16` (§15.1) |
| FUN_0049fcf0 | `stream_advance` | advance / skip the read position |
| FUN_00613a80 | `stream_readRecord` | `memcpy` N bytes from the front of the current `QByteArray` (data starts at `+0x10`). **This is the call that reads the 31-byte `SENSOR_INFO` records** |
| FUN_00442460 | `stream_peekU16` | peek a `u16` — reads the `Paket+0x20` **aux context**, not the wire |
| FUN_00442420 | `packet_getStation` | get the sender station / router key |
| FUN_0046dc40 | `stream_skip(n)` | skip n bytes |
| FUN_004081e0 | `QByteArray_detachResize` | `QByteArray` detach / resize (copy-on-write) |

### 13.16.4 Sensor DB reconciliation — `SENSOR_INFO` → SQLite

The chain that turns a decoded sensor descriptor into a database row. `MC3_`-side, so not
exercised on this box, but it is what defines the `Sensors` table's column semantics.

| Address | Name | Purpose |
|---|---|---|
| FUN_005c2380 | `Geraet_reconcileSensor` | [tag-proven] `"AbgleichSensor"` — reconcile a sensor record with the DB; insert if new |
| FUN_005c04d0 | `DB_findSensorRef` | `SELECT` sensor by fields |
| FUN_005bc1a0 | `DB_findActiveSensorRef` | find the active sensor ref |
| FUN_005bdd80 | `DB_updateRefValidity` | update ref validity |
| FUN_005befb0 | `DB_insertSensorRow` | [tag-proven] `"FuegeZeilezuTabellehinzu"` (= "add row to table") — **its INSERT column list is what defines the `SensorInfoRecord` layout in §6.5** |
| FUN_00524360 | `DB_isClosed` | mutex-checked "closed" flag |

### 13.16.5 Ethernet server / streaming socket

Distinct from the `Interface`/`EthThread` set in §13.9: this is the `QTcpServer` subclass and the
streaming UDP socket beneath it. Inactive on this box (`[Ethernet] Active = 0`).

| Address | Name | Purpose |
|---|---|---|
| FUN_00552fc0 | `Promos3EthServer_ctor` | `QTcpServer` subclass (`Promos3TcpServer`); zeroes fields, socket wiring elsewhere |
| FUN_005541a0 † | `processStreamingData` | `readyRead`: `hasPendingDatagrams` → `readDatagram` → per-IP `QVector<QByteArray>` → emit `dataReady`. Socket at `+0x2c`, port `+0x24` |
| FUN_00778560 † | `emit_dataReady` | emit `dataReady(QString)` via `QMetaObject::activate` (staticMetaObject `@0x00a1929c`, signal idx 1) |
| FUN_00551800 † | `ensureStreamingSocketBound` | bind the streaming UDP socket to port `+0x24` |
| FUN_00551eb0 | `deviceMap_find` | IP → device lookup (map `@+0x10`) |
| FUN_00553580 | `bufferMap_insertVector` | insert a per-IP `QVector` |
| FUN_00554560 | `ethServer_setPortConfig` | set server port config |
| FUN_00551600 | `ethServer_setId` | set id (`+0x48`) |
| FUN_005514a0 | `ethServer_setPortA` | set `u16` port (`+0x1e`). ⚠️ label unverified |
| FUN_00551650 | `ethServer_setStreamPort` | set `s16` port (`+0x1c`). ⚠️ label unverified |

`Promos3EthInterface_init` (`FUN_004fb1c0`, already in §13.9) wires this set together: creates the
server at `+0x18`, sets ports/id, and connects
`NewStreamingData(Promos3RouterObj)` → `StreamingDataReceived`,
`NewUnitConnected(Promos3RouterObj)` → `OnNewUnitConnected`,
`newHandshakeDatagram(QHostAddress, QByteArray*)` → `processPendingDatagrams`,
plus the `CheckSendPending` and `searchForNewUnits` timers.

### 13.16.6 Trace-decode helpers

| Address | Name | Purpose |
|---|---|---|
| FUN_00490c90 | `QList_short_append` | append one `int16` to a `QList<short>` — **called 125 times per trace** |
| FUN_00490590 / FUN_0048f9c0 | *(QList detach / copy internals)* | Qt container plumbing |
| FUN_00642ee0 | `onTraceComplete` | redraw / notify after a full trace |

### 13.16.7 Central objects, NC comm and licensing

| Address | Name | Purpose |
|---|---|---|
| FUN_00404310 | `Promos3ErrorManager_instance` | mutex-guarded singleton (`DAT_00a19ffc`); logs `"***Promos3ErrorManager started"` |
| FUN_00406930 | `Promos3IniFile_instance` | settings/INI singleton (`DAT_00a1a1cc`) |
| FUN_00406160 | `Promos3FileFunctions_?` | referenced as the INI backing object; not opened |
| FUN_00473f00 | `Promos3OpModeUpdater_ctor` | two `QTimer`s — 222 ms → `requestStatusUpdate`, 1111 ms → `onStopUpdates` |
| FUN_004aaf50 | `Promos3LicenseValidator_instance` | singleton (`DAT_00a1b1c0`) |
| FUN_004faed0 | `Promos3NCcommFile_ctor` | opens `NCaccess.ini` (fallback `GUDaccess.ini`) |
| FUN_004fb050 | `Promos3NCcommFile_instance` | singleton (`DAT_00a1b880`) |
| FUN_00548ad0 | *(menu manager)* | emits `CloseMenu(bool)` → `OnCloseSubMenu` |

### 13.16.8 Translation, theme and INI plumbing

| Address | Name | Purpose |
|---|---|---|
| FUN_00425f40 | `initTranslationAndStatusTables` | `connect(TranslationLoaded → StrListsInit)`, then `initStatusTables` |
| FUN_00414a90 | `Promos3Translator_ctor` | translator singleton (`DAT_00a1a340`) |
| FUN_00414b20 | `loadTranslationFiles` | load `*.qm` translation files |
| FUN_00415fa0 | *(style manager ctor, 0x28 bytes)* | singleton `DAT_00a1a410` |
| FUN_00416030 | `buildPalette` | `QPalette` (light/dark theme) |
| FUN_00419970 | `tr_helper` | Qt translation helper (GUI) |
| FUN_00437cb0 | `ini_readString` | string INI read |
| FUN_00437ba0 | `ini_readSectionValue` | section + key → trimmed value; `QMap<section, QMap<key,value>>` |
| FUN_00437760 / FUN_004376f0 | `QMap_lowerBound_stringKey` | skip-list search by `QString` key |
| FUN_00413a10 | `QMap_value_stringKey_stringVal` | `value(key)` or empty |
| FUN_0044d830 | `QMap_operatorBracket_stringKey_intVal` | `QMap<QString,int>::operator[]` |
| FUN_0044a200 | `QMap_createNode_stringKey_intVal` | node create (`QString` key, `int` value) |

### 13.16.9 Qt container / QString plumbing — name and forget

| Address | Name |
|---|---|
| FUN_00414020 | `QMap_insert_stringKey` |
| FUN_00413ad0 | `QMap_createNode_stringKey` |
| FUN_0044a010 | `QMap_freeData_stringValue` |
| FUN_0044b200 | `QMap_detach_stringKey` |
| FUN_0046a380 | `MapValue_assign` |
| FUN_0046a3f0 | `QString_deref` |
| FUN_0046a2b0 | `QString_construct` |

### 13.16.10 The lazy-singleton idiom (reference)

Many globals use the same shape: `if (DAT_xxxx == 0) { p = operator_new(N); DAT_xxxx = Ctor(p, parent); }`.
Recognising it saves opening the function at all.

| Global | Object | Ctor |
|---|---|---|
| DAT_00a1a244 | `Promos3DatenInstanz` | FUN_00408440 |
| DAT_00a1a840 | `NCcommThread` | FUN_00433640 |
| DAT_00a19ffc | `Promos3ErrorManager` | FUN_004040f0 |
| DAT_00a1a1cc | `Promos3IniFile` | `Promos3IniFile_ctor` |
| DAT_00a1b880 | `Promos3NCcommFile` | FUN_004faed0 |
| DAT_00a1b1c0 | `Promos3LicenseValidator` | FUN_004aae70 |
| DAT_00a1a340 | `Promos3Translator` | FUN_00414a90 |
| DAT_00a1a410 | *(style manager, 0x28 bytes)* | FUN_00415fa0 |
| DAT_00a1ab04 | `Promos3SqlDatenbankManager` | FUN_0044cdc0 / instance FUN_0044d070 |

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

# ═══════════════════════════════════════════════════════════════

**Question this Part answers:** *what is still missing before a reader can talk to the device and
display its data correctly, 100% of the time?*

<!--add-->
**⟦MEAS — added⟧**

> 📐 **This Part records the state at the end of the static phase.** The register moved again
> three times during the measurement phase — G4 was reopened and re-closed, G2 was reopened and
> re-closed, G7/G9/G11 advanced substantially, D3 and D4 closed, and D5–D9 opened.
> **The final state is §36.6.** This Part is kept in full because the *progression* is the useful
> part: it shows which assessments were right at the time, which were premature, and — in the
> case of G4 — which were closed on a wrong premise and had to be reopened.

The gap register was opened when protocol knowledge stood at ~78% and a trustworthy reader at
~45%. Each gap carries a **completion %** — how much of that item is in hand, where 100% means
nothing is left to do. The **Progress** column shows how each gap moved across the investigation,
so that a reader of an older document can see where their copy sits.

## 16.1 Scoreboard

<!--variant-->
**⟦CAP1 — variant⟧**

The **Progress** column ends with the post-capture state. Where the capture changed a verdict
the row is marked ⭐.

<!--variant-->
**⟦CAP1 — variant⟧**

| # | Gap | Progress | Now | Blocks live reading? |
|---|---|---|---|---|
| G1 | Message header wire layout | 20% → 95% → 100% → **100%** ✅ | **closed by deletion** — no header exists, and the capture confirms none appears on the wire | no |
| G2 | Completion rule + expected-length table | 30% → 90% → 100% → **100%** ✅ ⭐ | seq + 7B/frame + size table + checksum; verified in code, in tests, **and on 363/363 real messages with 0 sequence errors in 4,269 frames** | no |
| G3 | Request side / master role | 0% → 35% → 75% → 100% → **100%** ✅ ⭐ | framing, checksum, poll cycle, cadence, discovery all known — and **byte-identical to the captured requests** | no |
| G4 | Capture strategy / CAN-ID base | 0% → 0% → 35% → 100% → **corrected** ⚠️ ⭐ | 🔴 **two bases, split by direction** (`0x500` req / `0x580` ans). v3's "one base" was wrong and it is the live reader bug. The upside: direction **and** unit are on the wire, so passive demultiplexing needs no heuristics | 🔴 **yes — until patched** |
| G5 | Checksum | 0% → 90% → 100% → **100%** ✅ ⭐ | two code sites + one log line — **and now 1,353/1,353 requests plus 1,352/1,352 answers**, closing the answer-direction seed assumption | no |
| G6 | Record-layout versioning (`Geraet_getRecordVersion`) | 20% → 20% → **20%** | `FUN_004c5c70` still unread — judged low value | no |
| G7 | `MC_` (group-1) body layouts | ~15% → ~60% → ~65% → **~65%** ⭐ | **unchanged, and now known to be unchangeable from this artefact.** The capture caught an idle machine: zero `0xFF` escapes, all-zero or frozen rows, no `0x1b` at all. Needs a *busy-machine* capture | no |
| G8 | Limits loaded + the "%" display | 60% → 70% → **70%** | alarm, station and field names recovered; limits still not loaded by the reader | no |
| G9 | `channelKey` → feature index encoding | 60% → **60%** ⭐ | no `0x1b` transaction occurred, so still open; and the `0x16` row's internal split is open for the same reason | no |
| G10 | Unit ↔ serial ↔ model string | 70% → **100%** ✅ | 1-based index → `MSL5081-16` | no |
| G11 | Device-side timestamps | 50% → **80%** ⭐ | ⭐ **gateway µs clock decoded** at RX `+0x0C`/`+0x10` — 64-bit BE, ~75 ppm drift. Better than host arrival time, *especially* because answers arrive batched. The device-side *alarm* timestamp is still unread | no |
| G12 | Reader robustness (timeouts, counters, xlsx durability, record/replay) | 60% → **80%** | link layer written and tested; no `--record` / `--replay` yet — ⚠️ and the capture is exactly the artefact `--replay` should have been able to consume | no |
| G13 | *(what is NOT missing)* | — | see §16.4 | — |
| **D3** | Real expected answer sizes for `0x01`, `0x12`, `0x1B` | — | ⭐ **partly measured:** `0x01` = **2**, `0x33` = **2**, `0x16` = **`count×10+1`**. `0x12` and `0x1B` never fired — still guesses | measurement needed for 2 of 4 |
| **D4** | The `0x08` size branch (`Geraet+0x4e6`) | — | ⭐ ✅ **RESOLVED: 5.** The table said 1. The nibble branch fires; the nibbles sum to 5 | no — closed |

<!--variant-->
**⟦FIELD — variant⟧**

<!-- FIELD -->
> **⚠️ FIELD — this register is the static-phase final state and is superseded by Part 30.**
> Summary of the movement: **G4 reopened and then closed differently** (two bases, and the
> answer is promiscuous sniffing rather than master mode); **G5, G1, G2, G3 upgraded from
> ✅ VERIFIED to ✅ WIRE**; **G7 moved 65% → ~85%** (12 of 38 bodies); **G10 and G11 closed**;
> **D3 and D4 closed**; and **four new gaps G14–G17** were opened by the control-flow
> analysis in Part 27. One protocol gap remains: `0x1B`.

<!--variant-->
**⟦FIELD + MEAS — variant⟧**

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

<!--variant-->
**⟦CAP1 — variant⟧**

| Measure | Gap register | v3 | **v4 (post-capture)** |
|---|---|---|---|
| Protocol *knowledge* (transport + framing + config + DB + dispatch) | ≈78% | ≈99% | **≈99%** — the same number, but now *tested* rather than *asserted* |
| Link layer specifically | — | ≈99% | **100%** ✅ measured end to end |
| Body / payload semantics (group 1) | — | ~65% | **~65%** — blocked on a busy machine, not on analysis |
| Live *reader* that is correct and trustworthy end to end | ≈45% | ≈75% | **≈78%** (three patches away from ≈90%) |
| Group-1 commands named | 3 / 38 | ~35 / 38 | **~38 / 38** (send-only pairs added, §5.2.1) |

<!--variant-->
**⟦CAP1 — variant⟧**

> ⚠️ **Read the knowledge line carefully.** It did not move, and that is the point: the capture
> was not a discovery exercise, it was a *falsification* exercise. Two claims failed it. The
> other ~99% survived contact with real packets, which is a materially stronger statement than
> the same percentage was before.

<!--variant-->
**⟦FIELD + MEAS — variant⟧**

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

### `<!> D3 — Real expected answer sizes` — device state — ⭐ **half measured**

The size table (§3.7.1) is authoritative for `0x02` (14) and `0x0e` (144, call-site verified).

| cmd | status | value |
|---|---|---|
| `0x01 MC_GIVESTATUS` | ✅ **MEASURED** | **2** |
| `0x33 MC_GIVEPROGID` | ✅ **MEASURED** *(not previously on the list — it is in the poll set)* | **2** |
| `0x16 MC_GIVESAMMELMERKMALE` | ✅ **MEASURED** | **`count × 10 + 1`** |
| `0x08 MC_GIVEPLCVALUES` | ✅ **MEASURED** | **5** *(table said 1 — see D4)* |
| `0x12 MC_GIVEALARM` | ⚠️ **still a guess** | mapped onto the table's `0x11` entry, which is `ALARMGESEHEN`, not `GIVEALARM` — probably wrong |
| `0x1B MC_GIVESIGNALVERLAUF` | ⚠️ **still a guess** | 257, from a *synthetic* test, not real bytes |

`0x01` never calls `Paket_setRecvSize` at all — which is why it had no table entry and why §20.19
called it a poor first probe. It is now measured anyway.

🔴 **`0x12` and `0x1B` did not appear in 21 seconds of capture.** `0x12` is a periodic command
(it is in the dedup set, §2.8) that simply did not fire on an idle machine with no alarms.
`0x1B` only fires when a trace is being requested. **Both need a busy-machine capture** — the same
artefact that G7 and G9 need.

### `<!> D4 — The `0x08` size branch` — ✅ **RESOLVED**

```c
if (version < 0xD6 || Geraet[0x4e6] == 0)
     n = base + (GType=='D'||'H' ? 1 : 0) + (traceMapNode(station)==4 ? 1 : 0);
else n = (Geraet[0x4e6] >> 4) + (Geraet[0x4e6] & 0x0F);          /* ← this branch fires */
```

Version is `0xE5`, so if `Geraet+0x4e6` is nonzero the nibble branch applies.

✅ **It is nonzero, and the answer is 5.** The device sends 5 bytes for `0x08` on all 342 captured
transactions, against the size table's `1`. So `Geraet+0x4e6`'s nibbles sum to 5 — `0x41`, `0x14`,
`0x23`, `0x32`, `0x05` and `0x50` all fit, and **it does not matter which**: a reader needs the
sum, not the split.

**The general lesson is bigger than the number.** `Geraet_expectedRecordSize` is a *static
default that device configuration overrides at runtime*. Where the table and the device disagree,
the device wins. Any remaining table entry should be treated as a fallback, not as truth —
which is an argument for §17.3's measure-them-all approach over trusting §3.7.1.

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

## 16.5 The capture that used to be the whole plan — ✅ **taken; see Part 33**

<!--variant-->
**⟦CAP1 — variant⟧**

> **Status update.** This section was written when no capture existed. One now does
> (`JULY5_IMP1.pcapng`, Part 33) — obtained as a **pcapng packet capture** rather than through
> the `LogCANMessage=1` route described below. Of the four validation goals listed at the end of
> this section, **three were achieved**: the sequence/checksum framing was confirmed against real
> bytes, the unit-2 request confirmed that request byte 1 is the station, and received gateway
> records were confirmed to start `00 24 00 80`. The fourth — resolving the `channelKey` encoding
> (G9) — **was not**, because no `0x1b` trace transaction occurred in an idle window.
>
> The `LogCANMessage=1` route below **remains valid and is still worth knowing**, because it
> needs no capture tooling and no admin rights at all. It is the fallback if a second capture
> cannot be arranged the same way as the first.

<!--variant-->
**⟦FIELD — variant⟧**

<!-- FIELD -->
> **⚠️ FIELD — a capture was taken, seven of them, and `LogCANMessage` was not the route.**
> The campaign used `dumpcap` and promiscuous socket capture rather than the binary's own
> `[ErrorManager] LogCANMessage = 1`. The four things this section lists as still-useful were
> all delivered: the framing was confirmed against real bytes, the request byte-1 station
> claim was double-confirmed on unit 2, and received records do begin `00 24 00 80`. The one
> item it lists that was **not** delivered is `channelKey` (G9) — because that needs a `0x1B`
> trace and no `0x1B` was ever seen. §29.3 gives the current capture procedure.

```ini
; PROVISsettings.ini
[ErrorManager]
LogCANMessage = 1        ; currently 0
```

Run PROVIS3 against the machine for 60 seconds with the monitoring screen open, then take the log.
Raw CAN frames are written to it. **No Wireshark, no PEAK card, no admin rights.**

<!--variant-->
**⟦CAP1 — variant⟧**

⚠️ **Its role changed from discovery to validation.** When the gap register was opened, this
single artefact was going to close G1 (header offsets, anchored on `E5 01 04` from the KONFIG
answer), G2 (where the length lives), G5 (checksum shape) and part of G4. All of those were
closed by static analysis instead. What a capture was still good for:

<!--variant-->
**⟦CAP1 — variant⟧**

| goal | outcome in `JULY5_IMP1.pcapng` |
|---|---|
| confirm the sequence/checksum framing against real bytes | ✅ **done** — 0 seq errors / 4,269 frames; checksum 1,353 + 1,352 |
| resolve the `channelKey` encoding (G9) | ❌ **not done** — no `0x1b` transaction on an idle machine |
| check a **unit-2** request, to confirm request byte 1 is the station | ✅ **done** — unit 2 is `0x502` and still sends `params[0] = 0x01` |
| confirm received gateway records also start `00 24 00 80` | ✅ **done** — 100%, both directions |

<!--variant-->
**⟦CAP1 — variant⟧**

**And it found four things nobody was looking for:** the stale gateway address, the answer-side
CAN-ID base, the datagram batching, and the `0x08` size. That ratio — three of four planned
findings, plus four unplanned ones, two of them fatal — is the argument for taking the **second**
capture rather than reasoning further.

<!--variant-->
**⟦CAP1 — variant⟧**

**A third capture goal, added by the first one:** a busy-machine window, 20–30 s, to close G7,
G9, G11 and the rest of D3 (§33.11).

<!--variant-->
**⟦FIELD + MEAS — variant⟧**

⚠️ **Its role has changed from discovery to validation.** When the gap register was opened, this
single artefact was going to close G1 (header offsets, anchored on `E5 01 04` from the KONFIG
answer), G2 (where the length lives), G5 (checksum shape) and part of G4. All of those are now
closed by static analysis instead. What the capture is still good for:

<!--variant-->
**⟦FIELD + MEAS — variant⟧**

- confirming the sequence/checksum framing against real bytes;
- resolving the `channelKey` encoding (G9);
- checking a **unit-2** request, to double-confirm that request byte 1 is the station;
- confirming that received gateway records also start `00 24 00 80` (free symmetry check).

<!--add-->
**⟦MEAS — added⟧**

> ✅ 📐 **This happened — three times over, via pcap rather than `LogCANMessage`.** Every item on
> the list above was collected, and the scorecard for the *predictions* is worth keeping:
>
> | Prediction | Outcome |
> |---|---|
> | "one capture would close G1, anchored on `E5 01 04`" | ✅ **Exactly right.** `GIVEKONFIG` answers `e5 01 04 …` at payload offset **0**, with nothing in front of it. G1's closure *by deletion* is confirmed on the wire |
> | "confirm the sequence/checksum framing" | ✅ 88,936/88,936 sequence, 178,370/178,370 checksum — and it **also caught two framing rules that were wrong** |
> | "resolve the `channelKey` encoding (G9)" | ✅ mostly — the descriptor side is proven one-hot (`mask & 0x0F`), so the index is `log2`. The request-side `channelKey` for `0x1B` is still untested because `0x1B` never ran |
> | "check a unit-2 request, to confirm byte 1 is the station" | ✅ **Confirmed the other way from a pure guess.** Unit 2 is addressed as CAN-ID `0x502` and still sends `params[0] = 0x01`. The parameter does **not** track the unit. It is the station (§0.6 C15) |
> | "confirm RX records also start `00 24 00 80`" | ✅ 194,006/194,006, both directions |
>
> ⚠️ **And the capture found four things nobody predicted** — the two-base CAN-ID, the ephemeral
> source port, the gateway's microsecond clock, and the 250-byte flush boundary. Three of those
> four are blocking. That is the argument for capturing even when the analysis looks complete.
>
> ⚠️ `LogCANMessage = 1` was never needed. All three captures were taken with pcap on the wire.

---

# ═══════════════════════════════════════════════════════════════
# PART 17 — READER IMPLEMENTATION GUIDE
# ═══════════════════════════════════════════════════════════════

# ═══════════════════════════════════════════════════════════════

> 🔴 **SUPERSEDED FOR IMPLEMENTATION — use Part 36 §36.5.** This Part was written before any
> capture existed. Its §17.2 test datagram is *correct as constructed* but its **procedure will
> silently fail** (the reply is dropped by the kernel), and its §17.5 change-list contains four
> instructions that are now wrong. Both are corrected in Part 36.
>
> §17.1 (passive versus master) is **unchanged and its conclusion is strengthened** — see the
> banner in §17.1. §17.6 (tooling inventory) and §17.7 (stop reading Ghidra) still stand.


> ⚖️ **X3 🔴 — the editions disagree on this recommendation, and both are partly right.**
> ⟦MEAS⟧ strengthens *master*; ⟦FIELD⟧ reverses it to *promiscuous sniffing*. The resolution —
> sniff both directions on the host, never master alongside a running PROVIS3, and treat
> ⟦MEAS⟧'s §C.12 attribution result as the reason a one-directional capture is useless for
> body attribution — is in the Conflict Register, §0.0.5. Read both boxes below.
## 17.1 The decision that shapes everything: passive or master?

<!--variant-->
**⟦MEAS + CAP1 — variant⟧**

**Recommendation: master mode.**

<!--variant-->
**⟦MEAS — variant⟧**

> 📐 **Strengthened, not changed.** The measurement phase produced the strongest evidence yet for
> master mode, and it came from an accident. Capture 2 is a deduplicated file in which **146 of
> 396 exchanges have no request** — an exact, unintentional simulation of the passive-observer
> problem. Attributing them was attempted rather than assumed (Part 34 §C.12):
>
> - **The checksum is not an attribution oracle.** Across the first 40 unpaired answers, every
>   one admitted **~48 consistent `(command, args)` pairs spanning 6 distinct commands.** The
>   reason is structural: the checksum is one byte and the argument bytes are free, so for almost
>   any target there exists an argument string that satisfies it.
> - **Length narrows but does not close it.** Of the 15 fixed-size commands measured, three
>   length classes are ambiguous — payload 2 (`0x01 GIVESTATUS` vs `0x33 GIVEPROGID`), payload 3
>   (`0x02 GIVEGTYPE` vs `0x25 GIVE_ACTZYKINDEX`), payload 14 (`0x06 GIVEKONFIG` vs
>   `0x23 GIVE_SENSORVALUES`) — and applying the checksum to those pairs resolved **none** of
>   them. The variable-length `0x16` collides with everything.
>
> 🔴 **The consequence for a passive reader is severe: it has no way to recover attribution after
> a single dropped mirror packet, and no way to *detect* that it has lost it** — the frames still
> checksum against the wrong request 1/256 of the time, but the *lengths* will often still fit.
>
> **One narrower thing does work, and it repaired real data.** When the candidate set is small
> and the arguments are *fixed* rather than free, the checksum becomes decisive. One exchange
> presented a 61-byte answer while a `0x06` request was outstanding, and the body had the
> `n×10+1` shape of `0x16`:
>
> ```
> request 16 01 01 e7   (0x16, station 1, arg 1)  ->  checksum matches observed 0x59   ok
> request 06 01 f8      (0x06, station 1)         ->  no match
> ```
>
> The answer belonged to a `0x16` request; the pairing was wrong and the checksum caught it.
> **Use the checksum to validate an attribution you already have, never to derive one.** As a
> validator it is excellent — it caught a mis-pairing that length alone would have accepted.
>
> ⚠️ **One thing did get easier for passive mode.** The two-base CAN-ID (§0.6 C25) means a
> listener on a mirror can separate requests from answers and demultiplex units **without
> heuristics** — which removes the "the app's own requests will corrupt your reassembly buffers"
> objection below. That objection is now solved by a bitmask. The *attribution* objection is not,
> and it is the fatal one.

<!--variant-->
**⟦FIELD — variant⟧**

**Recommendation: master mode.**
<!-- FIELD -->
> ### ⚠️ FIELD 🔴 — this recommendation is reversed. Use promiscuous sniffing.
>
> Master mode works, and everything this section says about *why* it works is correct. But
> the campaign established two things that were not known when it was written:
>
> 1. **A promiscuous sniff sees both directions and needs no port mirror.** On the PROVIS3
>    host itself, `SIO_RCVALL` (or npcap) captures the app's requests *and* the gateway's
>    answers without binding a port, without transmitting, and without taking datagrams away
>    from PROVIS3. The objection below — that unicast delivery cannot be duplicated on one
>    host — is true only of a *bound socket*. It does not apply to a promiscuous capture.
> 2. **Two masters on one bus is a correctness failure, and it was demonstrated.** One
>    capture contains 7 bad checksums, all 7 inside the 52-second window in which the reader
>    was polling in master mode; none before, none after. Answers carry no command byte, so
>    each master attributes whatever arrives to *its own* pending request.
>
> Revised order of preference: **`--sniff` (safe alongside PROVIS3) → `--replay` (offline) →
> `--listen` (PROVIS3 stopped) → `--master` (PROVIS3 stopped, exclusive, and never while
> capturing for analysis).** §29.1.

| Deployment | Works? | What it needs |
|---|---|---|
| PROVIS3 runs and polls; reader listens passively | data flows | **a both-direction port mirror** (see below) |
| PROVIS3 stopped; reader listens passively | **silent forever** | nothing on the bus to hear |
| Reader replaces PROVIS3 (master) | works standalone | request framing, discovery, poll loop — **all now known** |

<!--add-->
**⟦CAP1 — added⟧**

> ⭐ **The capture materially improved the passive case — read this before deciding.** Two of
> the three objections below are now weaker than when this section was written:
>
> - **Direction and unit are on the wire after all.** Requests are `0x500 + unit`, answers are
>   `0x580 + unit` (§0.7 C26). The "request/answer discriminator" that the fourth bullet below
>   calls for is not a heuristic — it is a comparison against `0x580`. Likewise "feed the app's
>   own requests into reassembly and corrupt it" is now a solved problem: they are trivially
>   separable, and a source-IP filter is not even strictly required.
> - **The `MC_` "answers are anonymous" fact is narrower than it sounded.** The *command* really
>   is absent, so pairing is still required and §3.2 stands. But *unit* and *direction* are free.
>
> What has **not** changed: unicast delivery still cannot be duplicated on the same host, so a
> passive reader still needs a **both-direction port mirror / SPAN** and libpcap. And the aux
> context vector still never appears on the wire. **The recommendation therefore stands — master
> mode — but the margin is narrower**, and if a mirror already exists for other reasons, passive
> is now a reasonable choice rather than a fragile one.

**Why passive is hard.** `MC_` answers are anonymous (§3.1), so decoding *anything* requires
observing **both** app→gateway requests and gateway→app answers and pairing them per unit. That
removes "bind :1789 and listen" from the table entirely:

<!--variant-->
**⟦CAP1 — variant⟧**

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
  ⭐ **Both are now trivial:** the discriminator is `id >= 0x580`, and the gateway is `.16`
  (⚠️ note it answers from an *ephemeral* source port, so filter on source **IP**, never on
  source port).
- And even then, the aux context vector (`Paket+0x20`) that tells a handler which feature it asked
  for never appears on the wire — a passive reader must reconstruct it from the request bytes.

<!--variant-->
**⟦FIELD + MEAS — variant⟧**

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

## 17.2 The one 30-second test — ✅ **superseded by Part 33, but keep it as a smoke test**

<!--variant-->
**⟦CAP1 — variant⟧**

> This test was designed to answer "does anything come back at all". Part 33 answers that with
> 1,353 transactions, so its *diagnostic* purpose is served. It remains the right first thing to
> run when bringing up a reader on a new box or after a network change — with **two corrections**:
> send it to **`192.168.222.16`**, and expect a **5-byte** answer body, not a 1-byte ack.

<!--variant-->
**⟦CAP1 — variant⟧**

Form this request and send it to **`192.168.222.16:1789`** (🔴 **not `.17`** — §0.7 C25):

<!--variant-->
**⟦FIELD + MEAS — variant⟧**

Form this request and send it to `192.168.222.17:1789`:

```
36-byte record:
  00 24 00 80 00 00 00 00 00 00 00 00 00 00 00 00
  00 00 00 00 00 06 00 00 00 00 05 01 00 00 00 08
  01 f6 00 00
                 ^ dlc 6      ^ CAN-ID 0x501   ^ DATA
```

<!--variant-->
**⟦MEAS — variant⟧**

This is `MC_GIVEPLCVALUES`, unit 1, station 1 — the one request whose exact bytes are independently
verified against the runtime log. **If anything comes back, everything else follows. If nothing
does, that is a real result no decompiler was going to give.**

<!--variant-->
**⟦MEAS — variant⟧**

> 🔴 **The datagram is right; the procedure is wrong. Corrected in §36.5.1.**
>
> 📐 Every field of the datagram above is confirmed by capture — `00 24 00 80`, DLC 6, CAN-ID
> `0x501`, DATA `00 00 00 08 01 f6`. Three changes:
>
> 1. Send it to **`192.168.222.16`**, not `.17` (§0.3.1).
> 2. Send it from a socket **bound to 1789 and NOT connected**, or the kernel drops the reply
>    before your code sees it, because the gateway answers from an ephemeral port (§0.6 C26).
> 3. Expect the answer on CAN-ID **`0x581`**, not `0x501` (§0.6 C25).
>
> 🔴 **And note how badly the closing sentence ages under bug 2.** *"If nothing does, that is a
> real result"* is exactly the wrong inference to draw from a connected socket: the device
> answered, the kernel discarded it, and the operator concludes the link is dead.
>
> The expected reply is now **known rather than hoped for**: **5 payload bytes**, `00 00 00 00 ff`,
> in a single frame with `DLC = 7`, arriving in **1–2 ms**.

<!--variant-->
**⟦CAP1 — variant⟧**

This is `MC_GIVEPLCVALUES`, unit 1, station 1 — the one request whose exact bytes are independently
verified against the runtime log, **and now against 342 live transactions** (§33.4).

<!--variant-->
**⟦CAP1 — variant⟧**

**What to expect back, measured:**

<!--variant-->
**⟦CAP1 — variant⟧**

```
answer CAN-ID : 0x581              ← 0x580 + unit, NOT 0x501     🔴
answer body   : 5 bytes + checksum ← NOT the size table's 1      🔴
latency       : 1.2 – 5.1 ms
framing       : one frame, [seq=0][5 payload][ck]  (LEN 7)
```

<!--variant-->
**⟦CAP1 — variant⟧**

⚠️ The datagram carrying that answer may also carry **other units' frames batched with it** —
split on 36 bytes before doing anything else (§0.7 C27).

<!--variant-->
**⟦CAP1 — variant⟧**

**If anything comes back, everything else follows. If nothing does, that is a real result no
decompiler was going to give.**

<!--variant-->
**⟦FIELD — variant⟧**

This is `MC_GIVEPLCVALUES`, unit 1, station 1 — the one request whose exact bytes are independently
<!-- FIELD -->
> **⚠️ FIELD — the record below is byte-correct and would still have returned nothing.** Two
> reasons, both established from the wire: the gateway is at **`.16`**, not `.17`; and the
> gateway emits only to a **fixed destination port 1789**, so a socket on an ephemeral local
> port transmits successfully and receives forever nothing. Bind local **1789**. The
> corrected, ready-to-send records for six commands and both units are in §29.2.

<!--variant-->
**⟦FIELD — variant⟧**

verified against the runtime log. **If anything comes back, everything else follows. If nothing
does, that is a real result no decompiler was going to give.**

## 17.3 Then measure the sizes

For each of `0x01`, `0x02`, `0x06`, `0x08`, `0x0e`, `0x12`, `0x16`: send the request, accept frames
until the bus is quiet for 300 ms, and record the total payload byte count. That is **the real
size table, measured**. It closes D3 and D4 together and validates the answer-direction checksum
as a side effect.

<!--add-->
**⟦CAP1 — added⟧**

⭐ **Partly done, passively, by Part 33** — without sending anything. Four sizes fell out of
simply watching the app do its own polling:

<!--add-->
**⟦CAP1 — added⟧**

| cmd | measured | table said |
|---|---|---|
| `0x01` | **2** | *(no entry)* |
| `0x08` | **5** | **1** 🔴 |
| `0x16` | **`count × 10 + 1`** | *(computed — formula ✅)* |
| `0x33` | **2** | *(no entry)* |

<!--add-->
**⟦CAP1 — added⟧**

Still to measure: **`0x02`, `0x06`, `0x0e`, `0x12`, `0x1B`**. Note that `0x02`/`0x06`/`0x0e` are
*handshake and configuration* commands — they fire once at unit registration, before a capture
normally starts. To catch them passively you must **start the capture and then restart PROVIS3**,
or request them yourself in master mode. `0x12` and `0x1B` need a machine that is actually
working. The answer-direction checksum was validated as a side effect exactly as predicted
(§33.5).

## 17.4 If machine access is not available

Then the priority inverts and none of §17.2–17.3 applies. Build instead:

1. **`--replay`** against synthetic datagrams, so the decode path can be developed at a desk;
2. **the confirmed constants wired in**, so the tool is ready on the day access happens;
3. **this document**, handed to whoever does have access.

## 17.5 Changes required in the existing reader

<!--variant-->
**⟦MEAS — variant⟧**

> 🔴 **SUPERSEDED — use §36.5.** Four lines below are now wrong (the `% 7` checksum-only rule, the
> `[00][00][00][5 payload]` fixed request framing, "single CAN-ID base", and the implied 7-byte
> frame payload), and eleven further items are missing. The list is kept because the DELETE
> section is still correct and still the most valuable part of it.

<!--variant-->
**⟦FIELD — variant⟧**

<!-- FIELD -->
> **⚠️ FIELD — none of the changes below have been applied to the code in this project tree,
> and the list is now incomplete.** Verified against the current sources: `promos3_transport.c:19`
> still computes `unit = can_id − PROMOS3_BASE_CAN_ID`; `:62` still carries the
> *"a short frame ends the message"* heuristic that §0.6 C3 calls provably corrupting; `:52`
> still copies `f->data[0..len]` into the reassembly buffer, **including the sequence byte**;
> `reasm_expected_len()` is still a stub returning 0; and `parse_message_header()` is still
> called at `:74`. `main.c` binds `INADDR_ANY` with no source filter and has no `--master`,
> `--sniff` or `--replay`. Add to the list below: the two CAN-ID bases (§23.2), `DLC−1`
> framing (§24.1), and the socket rules in §23.3. The full corrected change list is §29.5.

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

### 🔴 Do these five first — without them the reader produces nothing

Ordered by consequence. Items 1–3 are from the live capture and each one alone is fatal.

```
1. PATCH  promos3_transport.c:19 — SPLIT THE CAN-ID BASE BY DIRECTION.
          Today:  out->unit = can_id - PROMOS3_BASE_CAN_ID;   /* 0x581-1280 = 129 */
                  -> every answer rejected against MAX_UNITS 16 -> DECODES NOTHING.
          Fix:    #define PROMOS3_BASE_CAN_REQ  0x500
                  #define PROMOS3_BASE_CAN_ANS  0x580
                  if (id >= PROMOS3_BASE_CAN_ANS) { dir=ANSWER;  unit = id - 0x580; }
                  else                            { dir=REQUEST; unit = id - 0x500; }
          Without this, nothing else in this list matters.                      §0.7 C26

2. PATCH  the expected-size table:  0x08 -> 5   (NOT 1)
                                    0x01 -> 2
                                    0x33 -> 2
                                    0x16 -> count*10 + 1
          A reader hardcoding 1 for 0x08 times out ~16x/second.                 §0.7 C29

3. PATCH  the datagram splitter: split EVERY datagram into len/36 records.
          The gateway batches up to 14 records per datagram; one-record-per-
          datagram loses ~64% of frames.                                        §0.7 C27

4. PATCH  the probe/target address: 192.168.222.16, not .17.
          And filter answers on source IP only — the gateway replies from an
          ephemeral source port (:50375 observed), never from 1789.             §0.7 C25

5. PATCH  the 0x16 request: byte 2 = 0x01, not 0x00 (Geraet+0x688 is set here). §0.7 C30
```

### Then the pre-capture list, which is unchanged and still required

```
DELETE  parse_message_header()                      — no such thing exists for MC_
DELETE  the "short frame ends the message" heuristic — provably corrupts (§18.1)
DELETE  reasm_expected_len()'s fallback              — replaced by the size table

ADD     per-unit request tracker: {command, expectedSize, sentBytes, deadline, attempts}
ADD     frame layer: seq = DATA[0]; payload = DATA[1..LEN-2]; verify sequence continuity
ADD     completion: accumulated == expectedSize (size table, or the 0x16 formula)
ADD     promos3_checksum() verbatim (§14.10)
ADD     checksum-only frame handling when expectedSize % 7 == 0   ← still untested live
ADD     status codes 1 = retry / 2 = abort / 4 = incomplete, mirroring UnitComm_assembleAnswer_MC
ADD     device-error detection: DATA[0]==0 && DATA[1]==1 && LEN==2   ← the LEN==2 part matters
ADD     --record / --replay (~50 lines) — the highest-value tooling item

PATCH   gw_build_record(): header = 00 24 00 80, rest zero            ← capture-confirmed
PATCH   request framing: [00][00][00][5 payload] then [seq][7 payload] ← capture-confirmed
PATCH   feature-name loading: read from SKanalRec, match on mask & 0x0F
WIRE    the master link layer into main.c as a --master mode

KEEP    the CONF_* honesty gating — it is still what stops guessed layouts printing as fact
KEEP    the LEN==2 constraint on device-error detection — the capture shows exactly why
        (0x16 answers begin 00 03..00 09; a 1-row block WOULD read 00 01)       §33.8
```

⚠️ **One instruction from v3 is now itself wrong and must be ignored:** *"PATCH single CAN-ID
base; delete any 3-base probe dimension."* Do **not** collapse to a single base. The direction
split is real (item 1 above).

### Optional, and newly worthwhile

```
ADD     decode the gateway RX clock: u64 BE at record +0x0C (lo dword) / +0x10 (hi dword),
        microseconds. Use it for inter-frame timing instead of packet arrival time —
        batched answers all share one arrival timestamp but carry distinct gateway
        stamps. ~10 lines, and it closes most of G11.                           §0.7 C28

ADD     a direction counter + an "unknown CAN-ID base" counter. If 0x600+n ever
        appears, you want it logged, not dropped.                               §2.5
```

`promos3_msg_t` loses `group` / `command` as **parsed** fields and gains them as **attributed**
fields, plus a `bool attributed` that is false whenever no request was observed.

## 17.6 Tooling inventory

<!--variant-->
**⟦CAP1 — variant⟧**

| File | Contents | State |
|---|---|---|
| `promos3.h` | shared types, transport constants, decoder-ring enums, `CONF_*` gating | present; header comment still describes the two retired "CALIBRATE" items |
| `promos3_transport.c` | 36-byte record split, CAN-ID routing, per-unit reassembly | present; 🔴 **line 19 is the fatal CAN-ID bug — patch first (§17.5 item 1)**; then the full §17.5 rewrite |
| `promos3_decode.c` | header parse + body decoders + printing | present; `parse_message_header()` **to be deleted** |
| `promos3_proto.c` | command-name and enum lookups | present; group-1 names can be upgraded from §5.2 |
| `promos3_config.c` / `.h` | PMD config-record parser (`SGeraetRec`, `SKanalRecV40`, cycles, limits) | present and working (`--config-unit`) |
| `promos3_state.c` / `.h` | reader state | present; **does not yet load cycles/limits** (G8) |
| `span.h`, `xlsx.c` / `.h` | byte-span helper; xlsx writer | present; xlsx flushes only on clean exit (G12) |
| `main.c` | UDP listener + modes (`--raw`, `--decode`, `--config-unit`) | present; binds `INADDR_ANY:1789`; **no source-address or direction filter** — ⭐ the direction filter is now a one-line `id >= 0x580` test (§0.7 C26) |
| *(new)* `--pcap FILE` | read `JULY5_IMP1.pcapng`-style captures through the same decode path | ⚠️ **absent, and now the single most useful thing to add.** A capture exists; the reader cannot consume it. This is `--replay` (G12) with a pcapng front-end |
| `promos3_master.h` / `.c` | `MC_` master link layer: checksum, request builder, frame layer, completion rule, per-unit request tracker, poll cycle, retry ladder, counters, RX record split | **written and tested** — ⚠️ *not present in the current project tree; retrieve it or rewrite from Part 3* |
| `test_master.c` | 20 assertions, all passing (§18.2) | **written** — ⚠️ *same caveat* |
| `promos3_learn.c` | probe / measure harness | **largely obsolete** now that the transmit path is byte-exact |
| `promos3_listen.c` | early UDP listener/decoder (no pcap, no admin) | superseded — assumed a clean Promos3 body per datagram |
| `promos3_records.h` | verified packed structs | superseded by `promos3_config.*`; feature-name handling must follow §9.2 |
| `promos3_sniff.c` | pcap variant (needs libpcap + admin) | retired — ⚠️ **may need to come back** if passive mode with a port mirror is chosen (§17.1). ⭐ Its case improved: direction and unit are now on the wire (§0.7 C26), so a passive front-end no longer needs heuristics |

<!--variant-->
**⟦FIELD + MEAS — variant⟧**

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

<!--add-->
**⟦CAP1 — added⟧**

⭐ **That prediction was tested and it held.** The capture supplied four corrections and four
measurements; re-reading the binary would have supplied none of them — three (the gateway
address, the CAN-ID direction split, the batching) are properties of the *deployment* rather than
the *program*, and the fourth (`0x08` = 5) is device configuration overriding a static table.

<!--add-->
**⟦CAP1 — added⟧**

**And it holds again for what is left.** The remaining unknowns — the `0x16` row split, the
`channelKey` encoding, the escape-byte mechanism, `0x12`/`0x1B` sizes, the device-side alarm
timestamp — are all **body semantics**, and body semantics need a machine that is *doing
something*. A second capture during real cutting is worth more than every remaining function in
the binary put together. (§33.11)

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

<!--variant-->
**⟦CAP1 — variant⟧**

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
| **Gateway endpoint (`.16`)** | `JULY5_IMP1.pcapng` | **live capture** | ✅ **measured** |
| **CAN-ID direction split (`0x500`/`0x580`)** | `JULY5_IMP1.pcapng` — 5,622 records, 4 distinct IDs | **live capture** | ✅ **measured** |
| **Datagram batching (1 vs ≤14 records)** | `JULY5_IMP1.pcapng` | **live capture** | ✅ **measured** |
| **Gateway µs clock at RX `+0x0C`/`+0x10`** | `JULY5_IMP1.pcapng` — 21.245927 s vs 21.244336 s wall | **live capture** | ✅ **measured** |
| **Answer-direction checksum** | `JULY5_IMP1.pcapng` — 1,352/1,352 | **live capture** | ✅ **measured** |
| **Expected sizes `0x01`=2, `0x08`=5, `0x33`=2** | `JULY5_IMP1.pcapng` | **live capture** | ✅ **measured** |
| **`0x16` stride = 10 / `count×10+1`** | `JULY5_IMP1.pcapng` — 363/363 | **live capture** | ✅ **measured** |
| **Poll cadence, latency, 50 Hz sample rate** | `JULY5_IMP1.pcapng` — 1,353 transactions | **live capture** | ✅ **measured** |
| **`params[0]` = station (from unit 2)** | `JULY5_IMP1.pcapng` | **live capture** | ✅ **measured** |

<!--variant-->
**⟦CAP1 — variant⟧**

**Most of these files exist because PROVIS3 produces them itself** — SQLite working databases,
PMD `.txt` exports, ErrorManager logs. They were collected by copying, not by capture. The only
data the app does **not** save is the live stream, which is why the transport needed Ghidra.

<!--variant-->
**⟦CAP1 — variant⟧**

⭐ **`JULY5_IMP1.pcapng` is the exception, and the only artefact in the project the application
did not generate.** It is also the only one that could have falsified the analysis, which is why
Part 33 is kept structurally separate: every claim in Parts 0–21 can still be traced to whether
it was *derived* or *measured*.

<!--variant-->
**⟦FIELD + MEAS — variant⟧**

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

<!--variant-->
**⟦FIELD + MEAS — variant⟧**

**These files exist because PROVIS3 produces them itself** — SQLite working databases, PMD `.txt`
exports, ErrorManager logs. They were collected by copying, not by capture. The only data the app
does **not** save is the live stream, which is why the transport needed Ghidra.

## 19.2 Files used

<!--variant-->
**⟦CAP1 — variant⟧**

```
SQLite config:       Provis-10659 (-250127_1838), Provis-10663
SQLite measurement:  ProvisLog-10663
PMD hex exports:     1974.txt, exVL2-1.txt, exVL2-2.txt
INI:                 PROVISsettings.ini, PROVISsecurity.ini (+ OLD-),
                     NCaccess.ini (+ OLD-, ALT2-), CDR_DESCRIPT_ENU.ini
Runtime logs:        LogFile.txt,
                     LogFile-260701-T0545.txt, -T0749.txt, -T0952.txt, -T1154.txt
String dump:         mazak_strings.txt
Packet capture:      JULY5_IMP1.pcapng   (4,039 packets, 21.24 s, ns resolution,
                                          Ethernet; 3,745 UDP -> 5,622 gateway records
                                          -> 1,353 transactions across 2 units)   << Part 33
Reader source:       main.c, promos3_{transport,decode,proto,state,config}.c/.h,
                     promos3.h, span.h, xlsx.c/.h, run_commands.txt
```

<!--variant-->
**⟦FIELD + MEAS — variant⟧**

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

<!--variant-->
**⟦CAP1 — variant⟧**

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
| 20.32 | The gateway address `192.168.222.17` | CORRECTION |
| 20.33 | "One CAN-ID base, both directions" | **CORRECTION** 🔴 |
| 20.34 | "A datagram is a batch" — never quantified | RESOLUTION |
| 20.35 | The gateway header as "discarded" | RESOLUTION |
| 20.36 | `0x08` expected answer size = 1 | **CORRECTION** 🔴 |
| 20.37 | `0x16` request byte 2 "sent as 0" | CORRECTION |
| 20.38 | The poll set as `{0x01, 0x08, 0x12, 0x16}` | CORRECTION |
| 20.39 | The answer-direction checksum seed | RESOLUTION |
| 20.40 | "One capture would VALIDATE the transport" (v1) | RECONCILIATION |

<!--variant-->
**⟦FIELD + MEAS — variant⟧**

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

<!-- FIELD -->
> **⚠️ FIELD — this correction was half right and the half it got wrong was the expensive
> half.** `0x500` really is the single *transmit* base and `FUN_00506220` really does
> transmit on `this+0x48 + unit`; that stands, ✅ WIRE-confirmed. But `0x580` is **not**
> "unexplained" — it is the receive base, and the CANopen-shaped hypothesis this entry
> dismisses was right about `0x580`, wrong about `0x600` (still never observed) and wrong
> about which way round they went. §23.2, and **F1** in §0.7.

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

<!-- FIELD -->
> **⚠️ FIELD — a fifth stage.** The reconciliation below has four stages; the campaign added
> a fifth that supersedes it: *"100% — a promiscuous sniff on the PROVIS3 host sees both
> directions, needs no mirror, no bound port and no transmit, and is safe alongside a running
> PROVIS3."* The objection preserved below is specifically about **bound sockets** and
> remains true of them. §29.1.

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

<!-- FIELD -->
> **⚠️ FIELD — one more row for the table below:** *v4 (this report, measured):* protocol
> knowledge **≈99.9%**, trustworthy live reader **≈95%, proven on live production data**.
> What now stands between 95% and 100% is `0x1B`, the missing six weeks of measurement
> history (§28.3), and engineering — not reverse engineering.

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

# ── Entries below this line come from the live capture (Part 33) ──

Everything from §20.32 onward was overturned, quantified or resolved by
`JULY5_IMP1.pcapng` rather than by further static analysis. These are the entries most likely
to matter to someone holding **v3**, which is otherwise a current document.

## 20.32 The gateway address `192.168.222.17` — **CORRECTION**

**Was** (every document from the first architecture map onward, and §2.6, §12.6, §17.2): the
gateway is at `192.168.222.17:1789`, read directly from `[CAN] GatewayAddress` in
`PROVISsettings.ini`.

**Is:** **`192.168.222.16:1789`.** The PROVIS3 host (`192.168.222.24`, bound `:1789`) exchanges
every one of the capture's 3,745 UDP packets with `.16`. The port is right; the host is not.

Either the INI copy in the project predates a re-address, or it belongs to a different cell. The
capture cannot distinguish those, and it does not need to.

⚠️ **The generalisable point:** this is the only value in `PROVISsettings.ini` that the capture
contradicted, and it happens to be the one a reader bootstraps its socket from. A tool that trusts
the INI here **sends to a host that does not answer and looks exactly like a dead bus** — the most
expensive kind of wrong to debug. Verify the endpoint before concluding anything about the
protocol.

⚠️ **Second-order trap:** the gateway replies from an **ephemeral source port** (`:50375` in the
capture), not from 1789. Filter on source **IP**, never on source port.

## 20.33 "One CAN-ID base, both directions" — **CORRECTION** 🔴

This constant has now reversed **twice**, so the full history is worth stating once:

| Stage | Claim | Verdict |
|---|---|---|
| Part 17 §5.3 | **Three** bases `0x500 / 0x580 / 0x600`; CANopen-shaped; "this is the direction discriminator" 🔴 IMPORTANT | **direction split: right. Specifics: unproven.** |
| Part 18 §3.3 / v3 §0.6 C4 / §2.5 | **One** base. `FUN_00506220` computes `id = *(this+0x48) + unit`, `this+0x48 = 1280`; the settings dialog exposes exactly one "Base Tx" field. "TX and RX share it." | **the code reading: right. The conclusion: wrong.** |
| **Part 33 §33.3 — measured** | **Two** bases: requests `0x500 + unit`, answers **`0x580 + unit`**. `0x600` never appeared. | ✅ |

**Is:** `0x580` is not a *transmit* base — Part 18 was right about that — but it **is** the
**answer / receive** base. `this+0x48` was read correctly; it simply only ever governs the
direction that function sends. The settings dialog's own label says **"Base Tx"**, which in
hindsight was the tell.

**Why this is the worst error in the corpus:** it is silent and total. A reader computing
`unit = can_id − 1280` maps every real answer to unit 129/130, fails `MAX_UNITS 16`, and
**discards the entire receive direction**. Not degraded output — no output. This is exactly what
`promos3_transport.c:19` does today (§17.5 item 1).

**The compensating upside, which is genuine:** *answers are less anonymous than §3.2 feared.* The
unit is on the wire and so is the direction. Pairing still requires both directions — the
*command* really is absent, and §3.2 stands unchanged — but a listener can demultiplex units and
separate request from answer **with no heuristics at all**. That improves the passive option in
§17.1 materially (§20.17 is thereby partly re-reconciled: G4's passive-mode objections shrink to
"you still need a mirror", which was always the hard part).

**The methodological lesson worth keeping:** "function *F* does not transmit on *X*" is a true
statement about one function. It was generalised into "*X* is not a base", which is a statement
about the bus, and the bus had not been observed. Static analysis of a *sender* can never
establish what a *receiver* sees.

## 20.34 "A datagram is a batch" — never quantified — **RESOLUTION**

**Was:** every document says a UDP datagram is "a batch of 36-byte records" and stops there. No
document states how many, in which direction, or what happens to a reader that guesses wrong.

**Is, measured:**

| direction | records per datagram |
|---|---|
| app → gateway | **exactly 1**, on 1,353 of 1,353 |
| gateway → app | **the whole multi-frame answer in one datagram** — up to **14 records / 504 bytes** observed |

**A reader that assumes one record per datagram loses ~64% of the frames.** The `Scan4CANmsg`
loop (§2.2, §14.1) always handled this correctly, because it splits on `size % 0x24` and iterates;
the risk was only ever in a re-implementation that "simplified" it. Now quantified so that nobody
simplifies it.

## 20.35 The gateway header as "discarded" — **RESOLUTION**

**Was** (§2.2, and the first architecture map): `gw_header[0x15]` — "gateway timestamp/status
(discarded)". Accurate as a description of what the *app* does, and it left the bytes unexamined.

**Is:** the app does discard them, and they are **not empty**. On gateway→app records, bytes
`0x04–0x14` are zero *except* a **64-bit big-endian microsecond counter — low dword at `+0x0C`,
high dword at `+0x10`** — with `+0x14 = 0`. On app→gateway records they are all zero, exactly as
`FUN_00504290` builds them (§2.3), which is itself a nice confirmation of that function.

Over the capture the counter advanced 21.245927 s against 21.244336 s of pcap wall time —
**ratio 1.000075**, i.e. a real clock with ~75 ppm drift, indicating **~19.04 days of gateway
uptime** at capture start.

**Why it is worth decoding:** it is strictly better than packet arrival time for jitter analysis,
*because of §20.34* — every record in a batched answer shares one arrival timestamp but carries
its own gateway stamp. This is most of gap G11, for about ten lines of code.

## 20.36 `0x08` expected answer size = 1 — **CORRECTION** 🔴

**Was** (§3.7.1, from `Geraet_expectedRecordSize`): `{0x08, 0x09, 0x0c} → 1`, glossed as "one-byte
ack — consistent with every `SET…` returning an ack".

**Is: 5.** On all 342 `0x08` transactions in the capture. That gloss was the mistake:
`0x08` is `MC_GIVEPLCVALUES`, a **read**, not a SET — it was grouped with two SETs in the switch
and inherited their explanation.

The mechanism is the D4 branch, and it fires:

```c
else n = (Geraet[0x4e6] >> 4) + (Geraet[0x4e6] & 0x0F);   /* version 0xE5 → this branch */
```

So `Geraet+0x4e6` is nonzero and its nibbles sum to 5. **D4 is closed as a value without knowing
which nibble is which**, which is all a reader needs.

**Practical consequence:** a reader hardcoding 1 times out on every `0x08` poll, **~16 times a
second**, and the retry ladder then masks the cause as a flaky link.

**The general form of this correction is the important part:** `Geraet_expectedRecordSize` is a
**static default that device configuration overrides at runtime**. Where the table and the device
disagree, the device wins. Every remaining entry in §3.7.1 should be treated as a fallback rather
than as truth — which strengthens the case for §17.3's measure-them-all approach.

## 20.37 `0x16` request byte 2 "sent as 0" — **CORRECTION**

**Was** (§3.3, §6.2, §16.3): request byte 2 of `0x16` is `Geraet+0x688 ? 1 : 0`, "sent as 0 and
its meaning is unknown".

**Is:** sent as **`0x01`** on this box. The live request is `00 00 00 16 01 01 e7` — station
`0x01`, then flag `0x01`, checksum `−(1+0x16+1+1) = 0xE7` ✓. So `Geraet+0x688` is **set**.

The *meaning* is still unknown — that part of the original statement stands. Only the value was
wrong, and a master-mode reader that sends `0x00` is not reproducing what the app sends.

## 20.38 The poll set as `{0x01, 0x08, 0x12, 0x16}` — **CORRECTION**

**Was** (§3.10 from `FUN_004d1310`, corroborated by the dedup filter in §2.8): the cycle is
`0x16 × channels → 0x08 × channels → 0x01`, and the periodically re-issued set is
`{0x01, 0x08, 0x12, 0x16}`.

**Is, observed:** `0x16 → 0x08 → 0x01 → **0x33**`, interleaved between units 1 and 2.

| | static reading | measured |
|---|---|---|
| `0x33 MC_GIVEPROGID` | **not in the poll set** | **341 transactions** — it is |
| `0x12 MC_GIVEALARM` | in the dedup set, so periodic | **0 transactions** in 21 s idle |
| `0x16` per unit | one per channel (loop) | one — this box has `channelCount = 1` ✓ consistent |

`0x33` is genuinely absent from both `FUN_004d1310` and the dedup list, so it is issued from a
different site and **without dedup protection**. Neither fact was recoverable from the two
functions that were read; it took watching the app run.

⚠️ `0x12`'s absence is *not* evidence against the dedup-derived reading — an idle machine with no
alarms has nothing to fetch. It does mean `0x12`'s expected answer size remains unmeasured (D3).

## 20.39 The answer-direction checksum seed — **RESOLUTION**

**Was** (§3.5.3, §16.3, flagged in both as an open assumption): "the answer-direction seed is
assumed symmetric with the request. It is verified for requests only."

**Is:** ✅ **the assumption was right, and it is now measured** — 1,352 / 1,352 (the single miss is
a transaction truncated at capture end). Requests verified 1,353 / 1,353.

**What the second number proves is bigger than the checksum.** The answer checksum **cannot be
validated without the request bytes**. That is independent, structural confirmation of the pairing
model in §3.2 — the two directions really are one transaction — obtained from arithmetic rather
than from disassembly. It is the strongest single piece of evidence in the project for the
architectural claim that everything else in Part 3 rests on.

Equivalent working form: `ck_answer = (ck_request − Σ answer_payload) & 0xFF`.

## 20.40 "One capture would VALIDATE the transport" (v1) — **RECONCILIATION**

**Was** (the first architecture document, §10): *"Nothing here required Wireshark. A single
capture would only VALIDATE the transport (Parts 2–5) and pin the exact message-header field
order."*

**Is: half right, and the wrong half is instructive.**

- ✅ **"Nothing here required Wireshark"** — true, and it stayed true. The entire protocol was
  recovered without one. That claim survives completely.
- ✅ **"Would validate the transport"** — true. It did, comprehensively, and mostly favourably.
- ❌ **"ONLY validate"** — false. The capture produced **four corrections**, two of them fatal to
  a working reader, plus four measurements that replaced guesses. "Only" was the word that did
  not survive.
- ⚠️ **"Pin the exact message-header field order"** — moot. There is no header (§20.1).

**The reconciliation:** static analysis established the protocol; the capture established the
**deployment**. Three of the four corrections (the gateway address, the CAN-ID direction split as
seen by a *receiver*, the batching ratio) are facts about how this installation behaves on a wire,
not facts about what the program contains — and no amount of decompilation would have produced
them. The fourth (`0x08` = 5) is device configuration overriding a compiled-in default.

That is the durable lesson of the whole project: **the binary tells you what the software can do;
only the wire tells you what this installation actually does.**

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

<!--variant-->
**⟦CAP1 — variant⟧**

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
| **request base / answer base** | the two CAN-ID bases: `0x500 + unit` app→device, `0x580 + unit` device→app. **Direction is readable from the ID alone** (`id >= 0x580` → answer) |
| **batching** | the gateway's habit of packing an entire multi-frame answer into one UDP datagram (≤14 records / 504 bytes observed). The app never batches: one record per datagram |
| **gateway µs clock** | a 64-bit big-endian microsecond counter in the RX gateway header — low dword `+0x0C`, high dword `+0x10`. ~75 ppm drift; preferable to packet arrival time because batched records share an arrival stamp |
| **transaction** | one request plus its answer, paired per unit. The capture's unit of measurement (1,353 of them in 21.2 s) |
| **`JULY5_IMP1.pcapng`** | the live bidirectional capture that Part 33 reports on — the only project artefact PROVIS3 did not generate itself |

<!--variant-->
**⟦FIELD + MEAS — variant⟧**

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

<!--variant-->
**⟦CAP1 — variant⟧**

| Term | Meaning |
|---|---|
| **PROCUR-S / -I / -B** | Prometec sensor types (`0x80` / `0x81` / `0x82`); this box has 4× PROCUR-S |
| **MI sensor** | measurement-input sensor (`MiSensType`) |
| **GType 0x44** | the MSL-16 device family; resolved model here = `MSL5081-16` |
| **GeraetTyp as ASCII** | `0x44 = 'D'`, `0x48 = 'H'` — the binary compares it as a character |
| **Gain** (`Cycle_Sensors.Gain`, 0..126) | the sensor-side **hardware** amplifier setting; **not** applied at display time |
| **ReduzLim** | a device record field, `0x19D4` = 6612 on this box |
| **SampleDiv** | sample divider, 1 on this box |
| **feature sample rate** | the device's own measurement rate — **50 Hz**, measured (50.1/s unit 1, 49.8/s unit 2). The app's `0x16` poll rate floats to match, returning 3–9 rows per answer |
| **CDRLim** | channel record limit array, `0xAA` (170) ×4 on this box |

<!--variant-->
**⟦FIELD + MEAS — variant⟧**

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

> **End of the material inherited from v3 (Parts 0–21).** v3 in turn superseded
> `analysis_jul_28_1_0_0.md` (v2), `analysis_appendix_datamodel.md` (Appendix A),
> `analysis_appendix_B.md` (Appendix B), `analysis_part15_gap_register.md`,
> `analysis_part16_mc_answer_protocol.md`, `analysis_part17_session_handoff.md` and
> `analysis_part18_session_report.md` — all of which remain superseded (§32.7).
>
> **Parts 22–32 follow, and are new in this edition.** They carry the field campaign: what the
> wire confirmed, what it overturned, and what is still unknown. Where a Part below supersedes
> one above, the superseded Part carries a ⚠️ FIELD callout pointing forward.

---

---

# ═══════════════════════════════════════════════════════════════
# PART 22 — THE LIVE-CAPTURE CAMPAIGN: EVIDENCE BASE AND SOURCE RECONCILIATION
# ═══════════════════════════════════════════════════════════════

**Question this Part answers:** *what was actually measured, how much of it, and where do the
eight field documents disagree with each other?*

Parts 0–21 were produced without a single packet. This Part opens the phase that was, and it
does two jobs: it states the evidence base, and it reconciles the eight documents (**F-a**
through **F-h**, see *About this edition*) into one account. The reconciliation is not
housekeeping — one of the three conflicts is a systematic direction inversion that would send
an implementer in exactly the wrong direction, and one of them reverses a correction that
Part 20 records as settled.

---

## 22.1 Aggregate evidence base

| | |
|---|---:|
| Packet captures | **7** |
| PROVIS3 runtime logs | 4 |
| PMD (configuration) databases | 2 |
| Measurement databases | 2 |
| INI revisions | 3 |
| Reader CSV outputs | 2 |
| UI screenshots | 1 |
| **Attributed request/answer exchanges decoded** | **219,994** |
| **Checksum verifications (both directions)** | **439,988** |
| **Measurement rows decoded** | **~250,000** |
| Gateway records parsed | 217,151 |
| `min > max` invariant violations outside escapes | **0** |
| Device errors observed | **0** |
| Timeouts observed | **0** |
| Sequence breaks attributable to the link | **0** |

Every statistic in Parts 22–29 was evaluated over a full record set, not a sample.

---

## 22.2 Capture inventory

| Capture | Size | Records | Transactions | Completed | Bad ck | Seq err | `0x16` rows | Analysed in |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| six-datagram set | 6 datagrams, 41 records | 41 | — | — | 0 | 0 | 31 | F-a, F-b |
| `JULY5_IMP1.pcapng` | 519,944 B | 5,622 | 1,353 | 1,352 | 0 | 0 | 2,122 | F-c, F-e |
| `packets_july5.pcapng` | 89,512 frames | 67,018 | — (one-directional) | — | — | — | — | F-d |
| `capture2today.pcapng` | 16,966,464 B | 191,580 | 40,798 | 40,761 | 0 | 4 | 65,098 | F-e |
| `captureeventlist_too.pcapng` | 1,646,236 B | 19,949 | 4,139 | 4,136 | 0 | 0 | 6,069 | F-e |
| **subtotal (F-e's three)** | | **217,151** | **46,290** | **46,249** | **0** | **4** | **73,289** | |
| plus three further captures | | | | | | | | F-f |
| **campaign total** | | | **219,994** | | **0** | **4** | **~250,000** | |

**On the 41 incomplete transactions.** 37 are capture-boundary truncations. The remaining 4
are sequence breaks, all inside the 17 MB file. They are most likely Wireshark drops rather
than link faults: the gateway never re-sent, and the surrounding transactions are clean.
**Treat 4 / 46,290 as a capture artefact, not a protocol finding** — and note that no error
answer, no timeout and no retry occurred anywhere in the campaign, so the link's error paths
remain effectively untested (§26.4).

**On the seven bad checksums that do exist.** They are not in the table above because they
belong to a different capture and a different cause: all seven fall inside a single
52-second window in which the reader was itself polling in master mode. See §29.4 — this is
the demonstration of the two-master hazard, and it is the reason master mode must never be
used while capturing for analysis.

---

## 22.3 What each document was working from

The eight documents do not describe eight independent findings; several re-analyse the same
bytes. Knowing which is which is the whole basis of the reconciliation.

```
six datagrams (D1–D6) ──┬── F-a   first pass, hand-decoded
                        └── F-b   mechanical re-parse; corrected field map; fixtures

JULY5_IMP1.pcapng ──────┬── F-c   first bidirectional analysis   ⚠️ direction inverted
                        └── F-e   re-analysed with two later captures

packets_july5.pcapng ────── F-d   one-directional, 303 s, 67,018 records

all of the above + 3 more ─ F-f   campaign summary — MOST AUTHORITATIVE

no captures ────────────┬── F-g   control-flow ownership, from existing corpus
                        └── F-h   QODBC plugin work
```

**Precedence used throughout Parts 22–32**, highest first:

```
F-f  >  F-e  >  F-b  ≈  F-a  >  F-d  >  F-c
```

F-f outranks the rest because it had every capture, because it corrected two of its own
earlier documents, and because it is the only one that reports a **negative** result against
a rule the project had adopted (the constant 7, §24.1). F-c ranks last on the direction
question and only on that question — its arithmetic is sound and is used freely elsewhere.

F-g and F-h sit outside this ordering: neither touches the wire, and neither conflicts with
anything.

---

## 22.4 🔴 Conflict 1 — F-c inverts the direction of the entire protocol

### 22.4.1 The disagreement

| | F-c (`analysis_appendix_F__2_.md`) | F-a, F-b, F-d, F-e, F-f |
|---|---|---|
| `192.168.222.16` | **master / PROVIS3** | **PEAK gateway** |
| `192.168.222.24` | **device / CAN gateway** | **PROVIS3 host** |
| `0x500 + unit` | **answer** (slave → master) | **request** (PC → gateway) |
| `0x580 + unit` | **request** (master → slave) | **answer** (gateway → PC) |

F-c states the rule explicitly: *"requests ride `0x580 + unit`, answers ride `0x500 + unit`."*
That is exactly backwards, and because F-c also swaps the two IP addresses, the error is
**internally consistent** — nothing inside F-c contradicts it. It has to be settled from
outside.

### 22.4.2 Six independent lines, all agreeing against F-c

**1 — IP stack fingerprint.** `.24` transmits with **TTL 128, DF clear, TOS 0x00** — the
Windows default. `.16` transmits with **TTL 64, DF set, DSCP 0x10 (IPTOS_LOWDELAY)** — the
signature of a small embedded stack. A Qt4 application on Windows is on `.24`. (F-a §F.1,
F-b §F.7, F-e §F.1.)

**2 — Only the gateway stamps the record.** The 36-byte record's timestamp (`+0x0C`) and tag
(`+0x04`) are **zero on every record built by the PC** and **populated on every record emitted
by the gateway** (§23.4). In the six-datagram set the zero-timestamp record is the
`.24 → .16` one, and it bears CAN-ID **`0x501`**. A record with no gateway timestamp did not
come from the gateway.

**3 — That record is a request, and it decodes as one.** Its payload is
`00 00 00 33 00 cc` — the `[00][00][00][cmd][station][ck]` request shape, with `cmd = 0x33 =
MC_GIVEPROGID`. Its checksum closes at `−(1 + 0x33 + 0x00) = 0xCC` with **seed unit = 1**,
matching `0x501 & 0x7F`. Requests carry a command byte; answers do not (§3.2). This one does.

**4 — `BaseCanIDTransfer` is the transmit base.** `[CAN] BaseCanIDTransfer = 1280 = 0x500`,
and `Promos3CanInterface::send` (`FUN_00506220`) transmits on `this+0x48 + unit` where
`this+0x48 = 0x500`. The INI and the send function together fix `0x500 + unit` as what the
**PC emits**. This is v3's own §2.5 and it was never in doubt; F-c's reading requires the app
to receive on its own transmit base.

**5 — Datagram shape.** The app emits **exactly one record per datagram** (1,353 / 1,353 in
`JULY5_IMP1`). The gateway **coalesces a whole multi-frame answer into one datagram** — up to
14 records / 504 bytes observed. F-c reports precisely this split and attributes the
single-record side to the device.

**6 — F-c's own two halves cross-identify each other.** This is the decisive one, and it uses
nothing but F-c's own numbers.

### 22.4.3 F-c's numbers, re-read under the corrected direction

F-c's message-size histogram for the 4,269-frame side (frames per reassembled message → count):

```
1×989   5×6   6×36   8×90   9×135   11×75   12×17   14×5
```

Message count: `989 + 6 + 36 + 90 + 135 + 75 + 17 + 5 = ` **1,353**.

That is **exactly** the frame count on the other side. One message on the 4,269-frame side per
frame on the 1,353-frame side — the one-outstanding-request discipline of §1.5, visible as an
identity. Under F-c's reading it would mean each of 1,353 answers triggers exactly one of
1,353 requests, which inverts causality.

Now apply the completion rule of §24.2 to `cmd 0x16`, whose answer is `n × 10 + 1` bytes:

| rows `n` | body bytes | frames | F-c's count | F-a's packets |
|---:|---:|---:|---:|---|
| 3 | 31 | 5 | 6 | |
| 4 | 41 | 6 | 36 | packet 3 ✅ |
| 5 | 51 | 8 | 90 | packet 6 ✅ |
| 6 | 61 | 9 | 135 | packet 2 ✅ |
| 7 | 71 | 11 | 75 | packet 4 ✅ |
| 8 | 81 | 12 | 17 | packet 5 ✅ |
| 9 | 91 | 14 | 5 | |

Every bucket in F-c's histogram is a row count between 3 and 9 — and F-e, analysing the same
file with an independent parser, reports *"counts range 3–9 per poll."* Four of F-a's five
hand-decoded packets land on the same mapping, with the right final-frame `LEN` and the right
checksum position in each case.

Total rows implied: `3·6 + 4·36 + 5·90 + 6·135 + 7·75 + 8·17 + 9·5 = ` **2,128**. F-e counts
**2,122** `0x16` rows in `JULY5_IMP1` and reports exactly **one** incomplete transaction. A
single truncated 6-row message accounts for the difference precisely.

The other side is equally unambiguous. F-c's DLC histogram there is `5×307 · 6×683 · 7×363`
— and those are the exact lengths of the known request records (§29.2):

| DLC | request record | commands | count |
|---:|---|---|---:|
| 5 | `00 00 00 01 fe` | `GIVESTATUS` | 307 |
| 6 | `00 00 00 08 01 f6` · `00 00 00 33 00 cc` · `00 00 00 0e 01 f0` | `GIVEPLCVALUES` · `GIVEPROGID` · `GIVEKANAL` | 683 |
| 7 | `00 00 00 16 01 01 e7` | `GIVESAMMELMERKMALE` | 363 |

F-c's own poll census — run on the *other* side — returns `GIVESTATUS 307 + GIVEPLCVALUES 342
+ GIVEPROGID 340 = 989`, and 989 is its single-frame message count. `342 + 340 = 682` against
683 DLC-6 requests; `363` DLC-7 requests against `364` multi-frame messages. Both discrepancies
are **one**, in opposite directions — the standard signature of a capture that begins
mid-transaction and ends mid-transaction, and consistent with F-e's independent
*"1,353 transactions, 1,352 completed."*

### 22.4.4 Why F-c's seven checksum matches are real anyway

F-c reports seven predicted-equals-observed checksum matches and treats them as confirmation
of the **request** formula `−(unit + cmd) & 0xFF`. They are genuine byte-level matches. They
are matches on the **answer** direction, and the agreement with the simplified formula is a
degenerate case, not an independent rule.

The full spanning checksum (§24.3) is:

```
ck = −( unit + Σ request[0 … n−2] + Σ answer_payload )  (mod 256)
```

Take `GIVESTATUS`, unit 1. Request `00 00 00 01 fe` → `Σ request[0…n−2] = 1`. The answer is
the single frame `00 00 00 fe` = `[seq 00][payload 00 00][ck fe]`, so `Σ answer_payload = 0`
(the machine was idle; `GIVESTATUS` returned `00 00` throughout the campaign, §26.5).

```
ck = −(1 + 1 + 0) = 0xFE          observed 0xFE   ✅
```

F-c's simplified `−(unit + cmd) = −(1 + 1) = 0xFE` gives the same byte — because with three
leading reserved zeros and no station byte, `Σ request[0…n−2]` **is** the command, and with a
zero-sum payload the third term vanishes.

`GIVEPLCVALUES`, unit 1, is more interesting because the payload is not zero:

```
request  00 00 00 08 01 f6      Σ request[0…n−2] = 0x08 + 0x01 = 9
answer   00 00 00 00 00 ff f7   = [seq][00 00 00 00 ff][ck f7]   Σ payload = 0xFF = 255
ck = −(1 + 9 + 255) = −265 ≡ 0xF7                observed 0xF7   ✅
```

F-c's `−(1 + 8) = 0xF7` agrees only because the station byte (`+1`) and the payload (`+255 ≡
−1`) cancel modulo 256. A coincidence, and a fortunate one — it is why F-c's table looks
clean.

**Consequence.** F-c's §F.4 is a valid seven-fold confirmation of the **answer-direction**
checksum on a capture where the payloads happened to sum to zero or to −station. It is not a
request-side confirmation, and it cannot be, because the frames it examined were answers. Its
own puzzled note — *"the command byte is not a clean literal in these poll frames"* — was the
symptom of the inversion, read as a quirk of the protocol.

### 22.4.5 What F-c got right, and what to keep from it

Everything except the direction labels. Specifically, retain:

- the frame accounting (`4,269` and `1,353`, reconciling exactly);
- the message-size histogram, re-read per §22.4.3;
- the seven checksum matches, re-labelled as answer-direction;
- **the reader drop-bug proof.** F-c computes `0x581 − 0x500 = 129` and `0x582 − 0x500 = 130`,
  both `≥ MAX_UNITS`, and concludes the reader discards them silently. That conclusion is
  correct and is unaffected by the inversion — it is the same defect §23.2 describes.

Discard only: the direction column of its §F.1 and §F.3 tables, the rule statement
*"requests ride `0x580 + unit`"*, and its §F.5 characterisation of the multi-frame messages as
*"the master writing records"* of a **SET*** type. Those messages are the live measurement
stream. F-c's own description of their contents — repeating groups around `26 26 00 20` /
`25 25 00 20` — is the shape of an **idle** measurement row: one feature sitting at 0x25–0x26
(37–38 counts) with `min == max`, and a `00 20` status pair. Compare the line F-e's reader
prints from decoded traffic: `M08 DEBI 37..38 [tail 00 20]`.

---

## 22.5 Conflict 2 — which units, which serials, which feature names

### 22.5.1 The disagreement

| Document | Serials reported | Source |
|---|---|---|
| Parts 0–21, F-b, F-d, F-g | **10659** (unit 1), **10663** (unit 2) | runtime log, config DB `Provis-10663` |
| F-f | **10660**, **10665** | `0x0D` answers, `Devices` table, `ProvisLog-10660` / `ProvisLog-10665` |

### 22.5.2 Both are real — the installation carries four serials in two pairs ✅

`PROVISsettings.ini [DatabasePMD]` in this project names all four, and pairs them by PMD file:

```ini
LastMonDataFile-10659 = 1971
LastMonDataFile-10663 = 1971
LastMonDataFile-10665 = bas?c-setup
LastMonDataFile-10660 = bas?c-setup
```

Two pairs, two configuration sets. Parts 0–21 worked from the `1971` pair; the field campaign's
measurement databases are the `bas?c-setup` pair. Both are `GType 68 / SubType 5`, both report
1 channel and 4 sensors, and nothing in the protocol distinguishes them.

⚠️ **INFERRED, and worth resolving:** if the campaign ran against the second pair, the
gateway-address discrepancy (`.17` in the INI, `.16` on the wire) is explained as **a second
cell** rather than a stale file — which changes it from a configuration error to a
documentation gap. This is open item **F-6** (§30.3) and it is answered by reading the
gateway's own configuration.

**Practical rule regardless:** a reader must take the serial from the device (`0x0D` at
`+0x14`, §25.2.1), never from a file name and never from a hard-coded constant.

### 22.5.3 ⭐ The feature names — and a reversal of ledger entry C12

This is **new in this edition** and it is settled from two files that have been in the project
tree since before the campaign began.

Part 9.2 and ledger entry **C12** record that report v1 claimed the four features were
`SPINDEL / X AXIS / Y AXIS / Z AXIS` with masks `0x81/0x82/0x84/0x88`, and that report v2
**corrected** this from `1974.txt` to `VIBRATION / M131 DEBI / M131BASINC / M08 DEBI` with
masks `0x01/0x02/0x04/0x08`. F-e's live `0x0E` answers reproduce the second set exactly and
appear to confirm the correction.

**They are both right, on different units of the same machine.** The `SKanalRecV40` name table
at `+0x4D` (12-byte entries, `[mask][11-byte NUL-padded ASCII]`):

```
1974.txt        01 "VIBRATION"   02 "M131 DEBI"   04 "M131BASINC"   08 "M08 DEBI"
                SGeraetRec +0x14 = 29 A7  →  BE 0x29A7 = 10663  =  Unit 2

exVL2-1.txt     81 "SPINDEL"     82 "X AXIS"      84 "Y AXIS"       88 "Z AXIS"
exVL2-2.txt     (byte-identical to exVL2-1.txt)
                SGeraetRec +0x14 = 29 A3  →  BE 0x29A3 = 10659  =  Unit 1
```

Both serials match the runtime log line `Promos3DatenProvis2Geraet: Unit N … SNr NNNNN`. And
F-f's live `0x0E` results, from the wire and with no file involved, assign them the same way:
**unit 1 `SPINDEL / X AXIS / Y AXIS / Z AXIS` (masks `0x81/82/84/88`); unit 2 `VIBRATION /
M131 DEBI / M131BASINC / M08 DEBI` (masks `0x01/02/04/08`).** Three independent sources agree.

**Consequences:**

1. **C12 is a narrowing, not a reversal.** Report v1 was not wrong; it was reading unit 1.
   Report v2 read `1974.txt`, which is unit 2, and concluded v1 had been mistaken. The lesson
   C12 draws — *names are per-install, operator-assigned, read them at runtime* — is correct
   and is now **stronger**, because the two units of a single machine disagree. Recorded as
   **F14** in §0.7 and §31.
2. 🔴 **The documented test invocation mislabels unit 2.** Part 17.6 and `run_commands.txt`
   both use `--config-unit 1=exVL2-1.txt --config-unit 2=exVL2-1.txt` — the same file for
   both units. Unit 2's rows are then printed under unit 1's labels: `SPINDEL` where the
   sensor is a vibration probe. Correct pairing:

   ```
   --config-unit 1=exVL2-1.txt  --config-unit 2=1974.txt
   ```
3. 🔴 **F-d's recommended procedure expects the wrong labels.** F-d §F.7 step 2 predicts that
   `--config-unit 1=exVL2-1.txt --config-unit 2=exVL2-2.txt` will surface `VIBRATION, M131
   DEBI, M131BASINC, M08 DEBI`. Both files are unit 1 and both carry `SPINDEL / X AXIS /
   Y AXIS / Z AXIS`. Following that step and seeing the "wrong" names would look like a decode
   failure and is not one.
4. **The `0x80` bit is per-unit, not per-install.** Unit 1's masks carry it; unit 2's do not.
   `mask & 0x0F` is the index in both cases (§25.2.2), so matching on the low nibble is
   correct — but a reader that matches on the full byte works on unit 2 and silently fails on
   unit 1. What the `0x80` bit *means* is not established. ⚠️ It is not simply "sensor module
   present": `MiSensType[8]` is `0x80` ×8 on **both** units, while `SensorType_1..4` is
   `30 14 14 14` on unit 2 and `00 00 00 00` on unit 1 (§25.2.1) — the opposite pairing to
   what a slot-occupancy reading would predict. Open.

---

## 22.6 Conflict 3 — is a one-directional capture worth anything?

**The positions.** Part 20 §20.17 records the assessment that *"a one-directional capture is
worthless"*, on the correct ground that `MC_` answers are anonymous and must be paired with a
request to be named. F-d §F.5.1 pushes back: *"'worthless' overstates it."*

**Reconciled — F-d is right, and the distinction is worth stating precisely.** A
one-directional capture cannot yield the **command label**, and nothing else it yields depends
on the label. What it does yield, at zero risk to production:

| Available from one direction | Not available |
|---|---|
| Unit liveness and enumeration (the unit is in the CAN-ID) | Which command any answer answers |
| Framing and record-split validation | The request-side parameters |
| Checksum arithmetic *closure* (the trailing byte is where predicted) | Checksum *verification* — the seed spans the request |
| DLC and body-size distributions | Field semantics inside a body |
| Poll cadence, timing, sample rate | The aux context vector (`Paket+0x20`) |
| Any answer carrying a self-identifying constant | |

**And in F-d's specific case the size→command mapping is now available anyway**, because the
sizes were measured later (§25.3). Re-reading F-d's own body-size table against that:

| Body bytes | Unit 1 | Unit 2 | = payload + ck | Command |
|---:|---:|---:|---|---|
| 3 | 4,990 | 4,931 | 2 + 1 | `0x01 GIVESTATUS` / `0x33 GIVEPROGID` |
| 6 | 2,494 | 2,464 | 5 + 1 | `0x08 GIVEPLCVALUES` ✅ (D4 = 5) |
| 62 | 1,563 | 1,562 | 61 + 1 | `0x16`, n = 6 |
| 72 | 508 | 508 | 71 + 1 | `0x16`, n = 7 |
| 52 | 390 | 366 | 51 + 1 | `0x16`, n = 5 |
| 171 | 42 | 139 | 170 + 1 | `0x0F GIVEZYKLUS` ✅ (`SZykRecV4802`) |
| 18 | 15 | 16 | 17 + 1 | `0x12 GIVEALARM` ✅ (16-entry ring) |
| 82 | 12 | 7 | 81 + 1 | `0x16`, n = 8 |
| 42 | 10 | 10 | 41 + 1 | `0x16`, n = 4 |
| 15 | 5 | 5 | 14 + 1 | `0x06 GIVEKONFIG` or `0x23 GIVE_SENSORVALUES` ⚠️ |
| 4 | 3 | 3 | 3 + 1 | `0x02 GIVEGTYPE` or `0x25 GIVE_ACTZYKINDEX` ⚠️ |
| **1002** | — | **8** | 1001 + 1 | ⭐ **`0x16` at the 100-row cap** |

**Twelve of twelve map.** Two are ambiguous between commands of equal size — which is exactly
F-d's point about the missing label, and it is now a two-way ambiguity rather than a total
one.

**This closes F-d's open item F-4.** F-d flagged the 1002-byte bucket as *"the largest bucket
by an order of magnitude; likely a bulk transfer worth isolating,"* appearing on unit 2 only.
It is not a bulk transfer. The device caps a `0x16` answer at exactly **100 rows**
(§26.3), producing a 1,001-byte body plus checksum. Eight occurrences on unit 2 means unit 2
was polled slowly enough, eight times, for its backlog to saturate — which is the operational
trap in §26.3, visible in the data as a size bucket.

F-d's DLC distribution corroborates independently: 1,019 frames at `DLC = 3` against 1,016
messages of `n = 7` (whose final frame clamps to `avail = 1`, giving `LEN = 3`) — agreement to
0.3%.

**Remaining valid caution from F-d.** Where two commands share a size, one direction cannot
separate them; and a passive capture can never recover the aux context vector that tells a
`0x1B` handler which feature it asked for (§6.1). For validating a reader's transport and
reassembly layers, one direction is sufficient. For attributing bodies, it is not.

---

## 22.7 Two documents that conflict with nothing

**F-g (control-flow ownership)** performs no new decompilation and re-derives its conclusions
from artefacts already in the corpus: `mazak_strings.txt`, the runtime logs, the config-DB
schema, `1974.txt`, and functions decompiled in Parts 3, 6, 9 and 13. It answers a question
Parts 0–21 never asked, and its answer changes the risk profile of the whole project. Part 27.

**F-h (QODBC enablement)** is deployment work against a real install and touches no protocol
claim. It resolves the deployment blocker that F-f hit, and independently identifies the same
class of dialect problem F-f identified by a different route. Part 28.

One naming note carried from F-f: **an earlier document also titled "Appendix F"** covered
*The Deployed Configuration*; that material is Part 12 of this report. All eight campaign
documents are renumbered into Parts 22–32 here, and the label "Appendix F" is retired.

---

## 22.8 Method note — what actually produced results

Nothing in the campaign rests on a single source. The pattern that worked was
**triangulation**: disassembly gave candidate structures, the wire gave ground truth, and the
application's own SQLite tables gave field *names* for bytes the wire supplies only offsets
for. Where all three agreed a finding is ✅; where only one or two did, it is 🔶 or ⚠️ and says
so.

**The corrections that mattered were not places where the reverse engineering failed.** They
were places where a value observed in every available sample had been promoted to a rule:

- **the constant 7 bytes per frame** — true of every message shorter than 250 bytes, and of no
  other (§24.1);
- **the single CAN-ID base** — true of the transmit path, which is the only path the evidence
  covered (§23.2);
- **"17 bytes of zero padding"** — true of records the PC builds, which were the only records
  anyone had looked at (§23.4).

Each held perfectly until the first sample that could disprove it. The general lesson for the
remaining open items is in §30.4.

---

# ═══════════════════════════════════════════════════════════════
# PART 23 — TRANSPORT, RE-ESTABLISHED ON THE WIRE
# ═══════════════════════════════════════════════════════════════

**Question this Part answers:** *why does a correctly written reader receive nothing?*

Three defects, any one of which is individually sufficient to produce a reader that starts,
runs, reports no error, passes every checksum it is given, and writes an empty file. All three
were present simultaneously. **This Part supersedes §2.2, §2.3, §2.5 and §2.6.**

---

## 23.1 Topology ✅ WIRE

| Role | Address | Port behaviour |
|---|---|---|
| **PEAK PCAN-Ethernet gateway** | **192.168.222.16** | receives on **1789**; answers **from an ephemeral port** |
| **PROVIS3 host** | **192.168.222.24** | **binds 1789** and **sends from 1789** |
| Ad-hoc test host (one earlier probe) | 192.168.222.132 | 40 malformed datagrams; not part of the system |

```
REQUEST   192.168.222.24 : 1789   →   192.168.222.16 : 1789
ANSWER    192.168.222.16 : 50375  →   192.168.222.24 : 1789
                           ^^^^^                        ^^^^
                        ephemeral                      fixed
```

Direction is readable from the IP header alone, without knowing the addresses: the PC sends
**TTL 128, DF clear, TOS 0x00**; the gateway sends **TTL 64, DF set, DSCP 0x10** (IPTOS_LOWDELAY).
A second, record-level discriminator is in §23.4.

### 🔴 The INI's gateway address is not on the wire

```ini
[CAN]
GatewayAddress = 192.168.222.17   ; ← does not appear in any capture
GatewayPort    = 1789             ; ← correct
```

`192.168.222.17` appears in **zero packets** across all seven captures. `.16` appears in all of
them. Any PROVIS3 instance still holding `.17` cannot reach the bus, and the 30-second test in
§17.2 is aimed at the wrong host.

⚠️ **Why the file disagrees is unresolved.** Either the INI is stale, or it belongs to a
different cell — see §22.5.2, where the four-serial finding makes the second reading plausible.
Open item **F-6** (§30.3). It does not affect any protocol finding: the IP is configuration,
not protocol.

---

## 23.2 🔴 There are two CAN-ID bases ✅ WIRE

This is the single most consequential correction in the project.

```
0x500 + unit      PC → gateway        REQUEST
0x580 + unit      gateway → PC        ANSWER
```

Only four identifiers appear across every capture — `0x501`, `0x502`, `0x581`, `0x582` —
cleanly split by direction, over **194,006 records with zero exceptions**. Both units resolve
to serial numbers on record and both stream continuously.

`unit = CAN-ID & 0x7F` in both directions, and the unit derived that way is the value that
makes the checksum arithmetic close (§24.3) — an independent confirmation rather than an
assumption. Equivalently, since the blocks cannot overlap:

```c
unit = can_id & 0x00F;      /* 0x501..0x50F  vs  0x581..0x58F           */
base = can_id & 0xF80;      /* 112 identifiers between the two blocks   */
```

**The identifier alone gives both unit and direction, statelessly.** No per-socket state, no
IP inspection, no port matching.

### 23.2.1 Why v3 concluded there was one base, and why that was reasonable

`Promos3CanInterface::send` (`FUN_00506220`) computes `local_1c = *(int*)(this+0x48) + unit`
with `this+0x48 = BaseCanIDTransfer = 1280`. The settings dialog exposes exactly one **"Base
Tx"** field. Both observations are correct — and both are **evidence about the transmit path
only**. No receive-side function was ever read to check the other direction, and a *send*
function has no reason to know the answer base. Every capture before the first bidirectional
one was one-directional, so the single-base model was never contradicted.

The structural argument that should have prompted the check: **CAN identifiers name a
message, not a recipient, and the bus is a broadcast medium.** A request/response protocol on
a broadcast medium must allocate two identifier blocks or the asker parses its own request as
an answer. The `0x80` offset is bit 7 of the identifier functioning as a direction flag — the
CANopen convention, in which `0x580 + node` is the response block.

`BaseCanIDTransfer = 1280` is the only base named in the INI. **The receive base is implied by
convention and is never written down anywhere** — not in the INI, not in the settings dialog,
not in any log line.

### 23.2.2 The constructor constants, finally explained

Part 15.3 records three constants from the `Promos3CanInterface` constructor. Part 20 §20.4
dismissed the CANopen-shaped reading of them as an attractive hypothesis that was wrong. It
was half wrong:

| Constant | v3 verdict (§2.5) | **Now** |
|---|---|---|
| `this+0x48 = 0x500` | the transmit/receive base ✅ | **transmit base only** ✅ WIRE |
| `this+0x54 = 0x580` | "purpose unknown, NOT a transmit base" | **the receive base** ✅ WIRE |
| `this+0x58 = 0x600` | "purpose unknown, NOT a transmit base" | still **never observed**, in any capture ⚠️ |

The hypothesis was right that `0x580` carries a direction; wrong about `0x600`; and wrong
about which way round `0x500` and `0x580` went. The dismissal was right that neither is a
*transmit* base.

### 23.2.3 🔴 The defect in the reader, and why it is invisible

Confirmed against the current sources in this project tree:

```c
/* promos3_transport.c */
:16   out->can_id = (uint16_t)((r[0x1A] << 8) | r[0x1B]);
:19   out->unit   = (int)out->can_id - PROMOS3_BASE_CAN_ID;   /* 0x582 − 1280 = 130 */
:44   if (f->unit < 0 || f->unit >= MAX_UNITS) return 0;      /* 130 >= 16 → dropped */
```

```
0x581 − 0x500 = 129   ┐  both ≥ MAX_UNITS (16)  →  silently dropped
0x582 − 0x500 = 130   ┘
```

**The reader discards 100% of the answer traffic.** In `JULY5_IMP1` that is 4,269 of 5,622
records; across the campaign it is every measurement row that was ever transmitted. It keeps
only the requests — which, since they are the app's own, tell it nothing it did not already
know.

There is no crash, no checksum error, no counter increment and no log line. The tool runs
clean and produces an empty spreadsheet. This is the concrete mechanism behind *"passive
reading produces nothing usable"* for this generation.

The v3 text at §2.5 anticipated the shape of this exactly — *"you want them counted and
logged, not dropped in silence"* — and the recommendation was not implemented.

### 23.2.4 The fix

```c
#define PROMOS3_BASE_CAN_REQ  0x500   /* 1280 — PC → gateway */
#define PROMOS3_BASE_CAN_ANS  0x580   /* 1408 — gateway → PC */

unit = can_id & 0x00F;
base = can_id & 0xF80;
/* attribute answer[u] to the most recent outstanding request[u], per-unit tracker */
```

Recognise all three bases — `0x500+u` (request), `0x580+u` (answer), `0x600+u` (reserved,
never seen) — and **count anything else rather than dropping it.**

`JULY5_IMP1.pcapng` is a ready-made **regression fixture**: a correct reader must surface ≥ 2
units, recover commands `{0x01, 0x08, 0x33}` on the request side, reassemble 1,353
transactions, and pass every checksum.

### 23.2.5 One consolation

Part 3.2's finding — that `MC_` answers carry no command and no group — is unchanged and is
the hardest constraint in the protocol. But answers are anonymous **only as to command**. The
**unit is on the wire**, in the identifier. A passive listener can demultiplex fifteen machines
with no heuristics and no state at all.

---

## 23.3 🔴 The gateway answers from an ephemeral port ✅ WIRE

The gateway's source port was **50375** in the July capture and **34686** in the later ones. It
drifts across gateway restarts. Its **destination is always `192.168.222.24:1789`**.

**The gateway does not reply to the socket that asked. It transmits to a statically configured
host and port.** Three consequences govern every form of live access:

1. 🔴 **A `connect()`ed UDP socket has every reply discarded by the kernel** before user code
   sees it, because the source address/port do not match the connected peer. **Bind
   unconnected and filter on source *host*, never on source port.**
2. 🔴 **A client must bind local port 1789.** An ephemeral local port transmits successfully
   and receives nothing, forever, however correct the request. This is a hard transport rule,
   not a firewall symptom.
3. 🔴 **A client must run on `192.168.222.24`.** From any other host the answers are delivered
   elsewhere entirely.

This is the direct cause of the failed field runs: `promos3_view.exe --master --gateway
192.168.222.16:1789` aborted every command with `got 0 of N bytes` across `MC_GIVEKONFIG
(0x06)`, `MC_GIVEGTYPE (0x02)`, `MC_GIVEKANAL (0x0E)`, `MC_GIVESAMMELMERKMALE (0x16)`,
`MC_GIVEPLCVALUES (0x08)` and `MC_GIVESTATUS (0x01)`. **The requests themselves were
well-formed** — the tool emitted `08 01 f6` for `MC_GIVEPLCVALUES`, byte-identical to the
verified record; command byte, station byte and checksum all correct. The banner read
`local port: 0 (ephemeral)`. The answers were delivered to `.24:1789`, where nothing was
listening.

### 23.3.1 A second, unconfirmed defect

One capture contains **zero packets from `192.168.222.24` to `192.168.222.16`**, in either
direction, on any port — while that host's own mDNS/NBNS egress *is* present in the same
trace. Either the capture was not running during the `--master` attempt, or outbound UDP was
being dropped at WFP level by endpoint security before npcap saw it.

⚠️ Later captures do show `.24` transmitting to `.16` normally, which makes a
capture-window artefact by far the likelier reading. Distinguishing them is a one-minute test:

```
ip.src==192.168.222.24 && ip.dst==192.168.222.16
```

Empty while `--master` runs ⇒ outbound UDP is being dropped. Populated ⇒ it was a capture
artefact and the ephemeral-port defect is the whole story. The ephemeral port alone is
sufficient to explain the total failure.

---

## 23.4 The 36-byte gateway record — the real field map ✅ WIRE

`00 24 00 80` opens **217,151 of 217,151 records in both directions**. What Parts 2.2/2.3 call
`gw_header[0x15]` — *"gateway timestamp/status (discarded)"* and *"17 bytes of zero padding"* —
is a structured PEAK PCAN-Ethernet Gateway header, and the receive direction populates it.

```
off   len  field                       notes
0x00   2   record length  = 0x0024     BIG-ENDIAN, constant
0x02   2   record type    = 0x0080     constant — CAN-message record
0x04   8   tag / message id            zero on this link, both directions
0x0C   4   timestamp LOW  dword    ┐   64-bit microsecond counter, BIG-ENDIAN dwords
0x10   4   timestamp HIGH dword    ┘   🔴 LOW FIRST. Reading 0x0C..0x13 as one BE u64 is WRONG.
                                       REQUEST: all zero.  ANSWER: populated.
0x14   1   CAN channel    = 0          single-bus install; selector vs padding indistinguishable
0x15   1   LEN (DLC)                   2..8 — THE ONLY VALID LENGTH
0x16   1   flags          = 0          standard 11-bit ID, data frame
0x17   1   reserved       = 0
0x18   4   CAN identifier              BIG-ENDIAN, 32-bit
0x1C   8   DATA                        only LEN bytes are meaningful
                                       ---- 36 bytes total ----
```

### 23.4.1 The device clock is real, and it is better than packet arrival time ✅ WIRE

Over `JULY5_IMP1` the counter advanced **21.245927 s** against **21.244336 s** of pcap wall
time — a ratio of 1.000075, about **75 ppm**. It is a per-frame timestamp applied by the
gateway at the moment the CAN frame arrived, and it is a better time base than packet arrival
time **because answer frames arrive batched**: a nine-frame answer lands in one datagram with
one arrival timestamp, but nine distinct device timestamps 80–262 µs apart.

It is an **uptime counter, not an epoch.** It read 19.04 days in July and 19.07 days in the
later capture, establishing that the same gateway had not rebooted between them — which dates
four captures relative to each other with no reference to any host clock. The low dword wraps
every **71.6 minutes**; a reader must handle the wrap or use the full 64 bits.

🔴 **The word order is the trap.** Reading `+0x0C..0x13` as a single big-endian `u64` produced
`12,302,785,157,688,983,949 µs` in a real reader. The high dword sits at `+0x10`. On the
six-datagram set the high dword is constant `0x0000017F` = 383, giving
`383 · 2³² + ts_low µs ≈ 19.04 days` — consistent, and the reading under which the counter
tracks wall time to 75 ppm.

⚠️ One earlier document read `+0x10` as a `u16` zero followed by a `u16` **handle** =
`0x017F`. Same bytes, different interpretation; the timestamp reading is the one that produces
a rate-checkable quantity, and it is adopted.

**This closes G11 to 85%** — the reader can and should stamp every frame with the device's own
clock rather than the host's (§30.1).

### 23.4.2 Direction is readable from the record alone

On PC→gateway records the timestamp (`+0x0C`) and tag (`+0x04`) are **zero**; on gateway→PC
records the timestamp is populated. A reader on a mirrored port can classify direction without
inspecting IP headers at all. Useful as a cheap cross-check, and it was one of the six lines
that settled §22.4.

### 23.4.3 🔴 Bytes past `LEN` are not cleared by the gateway

A `LEN = 4` answer observed in the field carried `00 00 00 cc` followed by `00 ff f7 01` —
**stale bytes from the previous frame** (`00 00 00 00 ff f7` is the `0x08` answer). The
application zero-fills its own padding on transmit; the gateway does not on receive.

A reader that trusts the full 8-byte `DATA` array instead of honouring `LEN` will ingest
residue as payload. It will not fail loudly: it will produce plausible extra bytes and a
checksum that does not close.

⚠️ Note `promos3_transport.c:18` does `memcpy(out->data, r + 0x1C, CAN_MAX_DATA)` — it copies
all eight bytes unconditionally. That is safe **only** because every downstream consumer
honours `out->len`. Keep it that way, or clear the tail.

### 23.4.4 Datagram batching — always split on `len / 36`

- The app sends **exactly one record per datagram** (1,353 / 1,353 in `JULY5_IMP1`).
- The gateway packs **a whole multi-frame answer into a single datagram** — up to 14 records /
  504 bytes observed; up to 1,001-byte bodies imply larger still.
- Every UDP payload is an exact multiple of 36, in every capture, with **zero exceptions**.

🔴 **A reader assuming one record per datagram loses ~64% of frames.** The `Scan4CANmsg`
front-trim path (§2.2, §14.1) was therefore **never exercised** in any capture and remains
unverified — keep it, but do not assume it is correct.

### 23.4.5 The CAN-ID field width

v3 reads the identifier as a `u16` at `+0x1A`; the corrected map has a `u32` at `+0x18`. For
11-bit identifiers these are **identical** — `+0x18..+0x1B` reads `00 00 05 xx`. The 16-bit
read is what the binary itself does and is not a live bug. Widening it to a 32-bit big-endian
read at `+0x18` is **hardening** against extended identifiers, not a fix.

---

## 23.5 Request wire format, byte-exact ✅ WIRE — 46,290 / 46,290

```
DATA = [00][00][00][cmd][params…][ck]          LEN = 3 + payload + 1
```

The three reserved bytes are **zero on every request observed**, in every capture. Their
purpose is still unexplained (§16.3 flagged this) but the shape is now confirmed far outside
the decompiler. **Every request in all three of F-e's captures fits one frame.** A continuation
frame would be `[seq][≤7]`; none was ever needed, because the poll set's longest request is
five payload bytes.

### 23.5.1 `params[0]` is the station, not the unit ✅ WIRE

Unit 2 is addressed as CAN-ID `0x502` and still sends `params[0] = 0x01`. This confirms ledger
entry **C15** on the wire and closes the naive reading permanently.

⚠️ **But the station byte is not universal across the command set.** `GIVEPROGID` sends
`00 00 00 33 00 cc` — byte after the command is `0x00`, not the station. Compare:

| Command | Request DATA | Byte after `cmd` |
|---|---|---|
| `0x01 GIVESTATUS` | `00 00 00 01 fe` | *(none — 0 params)* |
| `0x33 GIVEPROGID` | `00 00 00 33 00 cc` | `0x00` |
| `0x08 GIVEPLCVALUES` | `00 00 00 08 01 f6` | `0x01` station |
| `0x0E GIVEKANAL` | `00 00 00 0e 01 f0` | `0x01` station |
| `0x16 GIVESAMMELMERKMALE` | `00 00 00 16 01 01 e7` | `0x01` station |
| `0x12 GIVEALARM` | `00 00 00 12 01 00 00 ec` | `0x01` station |

The generalisation *"`data[1]` = station"* was drawn from two senders (`0x0e`, `0x1b`) and
should be **narrowed to the commands that take a station parameter**. Build requests from a
per-command descriptor, not from a rule.

---

# ═══════════════════════════════════════════════════════════════
# PART 24 — FRAMING, COMPLETION AND CHECKSUM, WIRE-VERIFIED
# ═══════════════════════════════════════════════════════════════

**Question this Part answers:** *why do messages never complete, or complete at the wrong
length?*

**This Part supersedes §3.6 and §3.7.**

---

## 24.1 🔴 Payload per frame is `DLC − 1`, not 7 ✅ WIRE

Both this report's §3.6 and an earlier appendix promoted *"7 payload bytes per frame"* into a
rule. **The decompiled loop never said that.** It says:

```c
avail = frame[5] - 1;                                  /* = DLC − 1 */
if (avail > expected - accumulated) avail = expected - accumulated;
```

The constant 7 was true of every sample then available and of nothing else. The device
**flushes its transmit buffer every 250 payload bytes** and emits a short mid-stream frame at
each boundary. Short frames were observed at cumulative payload counts **251, 501 and 751 —
never elsewhere.**

| Rule | Agreement |
|---|---|
| **corrected: `avail = min(DLC−1, expected−accumulated)`** | **88,936 / 88,936 — 100.0000%** |
| old: `expected % 7 == 0` selects the checksum-only frame | **11 counter-examples** |
| `⌈expected / 7⌉` as a frame count | **withdrawn — no closed form exists** |

**This is the only correction in the project where Ghidra was right and the prose summary of
it was wrong.** It is also the reason a reader can appear to work perfectly on short messages
and fail only on the large ones — every `0x16` answer under 250 bytes obeys the constant 7,
and only the 100-row answers (§26.3) and `0x0F`/`0x0E` bodies cross a flush boundary.

⚠️ Consequently the `⌈144/7⌉ = 21` worked example in §3.6 is withdrawn, and F-b's
wire-verification of `⌈expected/7⌉` — genuine, on five messages — is **narrowed to messages
shorter than 250 bytes**, which all five were.

---

## 24.2 The corrected completion rule ✅ WIRE

```c
acc = 0;
for each frame {
    if (acc >= expected) break;
    avail = min(DLC - 1, expected - acc);      /* the clamp */
    append DATA[1 .. avail];
    acc += avail;
}
if (avail == 7)        /* frame filled with payload: no room for the checksum */
    take one more frame; it is [seq][checksum], and LEN must be 2;
else
    checksum = DATA[LEN-1] of the frame just consumed;
```

**Stop on the accumulated byte count. Never on a frame count.**

### 24.2.1 🔴 The clamp branch is the most easily mis-implemented line in the assembler

The decision *"is there room for the checksum in this frame?"* keys on the **clamped `avail`**,
not on the DLC. A reader that keys it on `DLC == 8` will hang waiting for a frame that never
arrives.

The proof case is in the six-datagram set. One answer's final frame carries `DLC = 8` — a
*full* frame — yet the checksum sits at `DATA[7]` and no `[seq][ck]` frame follows:

```
expected − accumulated = 6
avail = min(DLC−1, 6) = min(7, 6) = 6        ← the clamp fires: 7 → 6
avail != 7  →  ck = DATA[LEN−1] = DATA[7]
```

Under a naive reading a full frame means *"expect a separate checksum frame"*, and the message
never terminates.

### 24.2.2 Four final-frame shapes, all obeying the rule ✅ WIRE

From the six-datagram set, hand-decoded and then re-parsed mechanically:

| Packet | Frames | Rows `n` | body | Final `LEN` | Clamped payload | Checksum at |
|---|---:|---:|---:|---:|---:|---|
| 2 | 9 | 6 | 61 | 7 | 5 | `DATA[6]` |
| 3 | 6 | 4 | 41 | 8 | 6 | `DATA[7]` ← the clamp case |
| 4 | 11 | 7 | 71 | 3 | 1 | `DATA[2]` |
| 5 | 12 | 8 | 81 | 6 | 4 | `DATA[5]` |
| 6 | 2 (tail) | 5 | 51 | 4 | 2 | `DATA[3]` |

Sequence numbers run `0,1,2,…` with **no gaps across 40 frames**, and zero sequence errors in
4,269 frames in July (4 in 150,782 in the large file, attributed to capture drops).

### 24.2.3 🔴 Datagram boundaries do not align with message boundaries

Packet 6 above begins at sequence **6**, not 0 — its earlier frames arrived in a previous
datagram. **A reassembler must not assume one datagram equals one message, in either
direction.** The `Scan4CANmsg`-derived reader does not make that assumption; a
from-scratch implementation easily might.

### 24.2.4 The `[seq][ck]`-only branch has never been exercised ⚠️

No checksum-only frame appeared in any capture. This is consistent rather than surprising: it
fires only when the clamped `avail` lands exactly on 7, and none of the observed message
lengths did. **It remains untested and will fire the first time a message length works out
that way.** Keep the code; do not claim it is verified.

### 24.2.5 🔴 Do not use "accept when the checksum closes" for unknown sizes

This heuristic was tried, and it produces **false accepts**. `0x0F` answers were truncated at
6, 20, 27, 34, 48, 55, 83, 104, 160 and 167 bytes before the true 170 — because a 1-in-256
chance per frame fires often across a 25-frame message. The measured size table (§25.3) now
covers everything PROVIS3 actually asks, so the heuristic can be removed entirely.

---

## 24.3 The checksum, closed in both directions ✅ WIRE

```
ck = −( unit + Σ request[0 … n−2] + Σ answer_payload )   (mod 256)
```

Equivalently: `ck_answer = (ck_request − Σ answer_payload) & 0xFF`.

| Direction | Verifications | Failures |
|---|---:|---:|
| Request | 46,290 / 46,290 | 0 |
| Answer (spanning form) | 46,249 / 46,249 | 0 |
| **Campaign total, both directions** | **439,988** | **0** |

**Three alternative seedings were tested against the full set and each scored 0.** The
recovered formula is therefore not merely *consistent* with the data — it is the only
plausible variant that is.

**The unit number, not `unit − 1`, is the seed.** The three reserved request bytes and the
whole 36-byte gateway header are excluded.

### 24.3.1 This closes the project's last static-phase assumption

§16.3 listed *"the answer-direction checksum seed is assumed symmetric with the request
direction; it is verified for requests only."* That is now measured.

**Note what it proves structurally.** An answer **cannot** be validated without its request:
the seed spans both. That is independent confirmation that the two directions form one
transaction, and it is precisely why any reader must **pair before it decodes** — and why a
one-directional capture can observe that the trailing byte is where predicted but cannot
verify it (§22.6).

### 24.3.2 Worked verifications

**Request side, six-datagram set** — `GIVEPROGID`, unit 1:

```
group 1 → seed = unit = 1
Σ request[0…n−2] = 0x00 + 0x00 + 0x00 + 0x33 + 0x00 = 0x33
ck = −(1 + 0x33) = 0xCC              observed 0xCC   ✅ WIRE
```

**Answer side, six-datagram set** — five answers, five different payload sums, one invariant:

```
ck + Σ(payload bytes) ≡ 0xE6   (mod 256)      — 5 / 5
```

An additive invariant of that form arises only if the payload contributes as a plain byte sum
and everything else is a per-request constant — which is exactly the recovered form.
Rearranging gives a hard constraint on the unmatched request:

```
unit + Σ(request bytes excluding checksum) = 26   (0x1A)
```

**And a later capture supplied the request that satisfies it.** F-b derived the constraint
without the request in hand and noted it was satisfied by either `16 02 <ck>` (station 2) or
`16 01 01 <ck>`. F-e later captured the actual record: **`00 00 00 16 01 01 e7`** — station 1,
byte 2 = 1, unit 2. Check: `2 + (0x16 + 1 + 1) = 2 + 24 = 26` ✅. Two documents, two captures,
one prediction and one observation, converging.

That observation also resolves an open item: **`Geraet+0x688` is 1, not 0** — see §25.1.4.

**Request side, `JULY5_IMP1`** — seven predicted-equals-observed matches across three commands
and both units. Under §22.4.4 these are re-labelled as answer-direction verifications with
zero-sum payloads, which is what makes them agree with the simplified `−(unit + cmd)` form:

| cmd | name | unit | predicted | observed |
|---|---|---:|---|---|
| `0x01` | GIVESTATUS | 1 | 0xFE | **0xFE** ✅ |
| `0x01` | GIVESTATUS | 2 | 0xFD | **0xFD** ✅ |
| `0x08` | GIVEPLCVALUES | 1 | 0xF7 | **0xF7** ✅ |
| `0x08` | GIVEPLCVALUES | 2 | 0xF6 | **0xF6** ✅ |
| `0x33` | GIVEPROGID | 1 | 0xCC | **0xCC** ✅ |
| `0x33` | GIVEPROGID | 2 | 0xCB | **0xCB** ✅ |
| `0x16` | GIVESAMMELMERKMALE | 1 | 0xE9 | **0xE9** ✅ |

⚠️ **A useful property, and a limit on it.** `−(unit + cmd)` inverts uniquely given the unit,
so **unit and command are both recoverable from a request's trailing checksum** even without
decoding the intra-frame layout. This works because the reserved bytes are zero. It does
**not** extend to requests carrying parameters, and it does not work on answers.

---

## 24.4 Device error answers, and the state of the error paths ⚠️

**The device error answer is exactly `[seq 00][01]` with `LEN == 2`.**

The `LEN` constraint (ledger entry **C20**) is what keeps it distinguishable from a healthy
one-row `0x16` block, which also begins `00 01`. **Keep the constraint.**

🔴 **It is still an inference.** No device error occurred in any capture — 219,994 exchanges,
zero errors, zero timeouts, zero link-attributable sequence breaks. The error paths of this
protocol are effectively **untested**:

| Path | State |
|---|---|
| Device error answer `[00][01]`, `LEN == 2` | ⚠️ inferred, never observed |
| `try again` (retry, status 1) | 13 events found in one log, all recovering |
| `aborting` (status 2) | 🔴 **never reached in any artefact** |
| Timeout handling | never triggered |
| Checksum-only frame | never triggered (§24.2.4) |
| `Scan4CANmsg` front-trim | never triggered (§23.4.4) |
| Sequence wrap past 255 | unreachable in normal operation (§26.4) |

**These must be tested by fault injection, not by capture.** No amount of watching a healthy
link will exercise them, and the campaign's clean record is evidence about the link's health,
not about the reader's error handling.

⚠️ **The log prints command numbers in decimal.** `command 15` is `0x0F`, not `0x15`. Easy,
silent, and it will corrupt any attempt to correlate a log against a capture.

---

# ═══════════════════════════════════════════════════════════════
# PART 25 — COMMAND BODIES DECODED FROM LIVE TRAFFIC
# ═══════════════════════════════════════════════════════════════

**Question this Part answers:** *what do the bytes inside an answer mean?*

Twelve of 38 group-1 bodies are decoded, up from two, and sixteen answer sizes are measured,
up from two. The productive technique was **cross-referencing wire bytes against the
application's own SQLite tables**, which supply *names* for bytes the wire gives only offsets
for. **This Part supersedes §6.1 and §6.2 and completes §3.7.1.**

---

## 25.1 ⭐ `0x16 MC_GIVESAMMELMERKMALE` — the live measurement block, fully decoded ✅ WIRE

This is the heart of the system: the block the app polls continuously and the only source of
per-feature values that the application itself retains.

```
payload[0]              = row count n
payload[1 + r*stride]   = row r          stride = featureCount*2 + 2 = 10

  +0  Min_F0   +1  Max_F0      +2  Min_F1   +3  Max_F1
  +4  Min_F2   +5  Max_F2      +6  Min_F3   +7  Max_F3
  +8  status0                  +9  status1

message length = n × 10 + 1        (excluding the trailing checksum)
```

The formula `count × recordSize + 1` held on **11,613 / 11,613** messages with remainder 0, and
`recordSize = 10 = featureCount × 2 + 2` for **featureCount = 4** — derived from the wire,
independently of any configuration file. §6.2's stride formula is confirmed on real bytes, and
so is ledger entry **C19**.

### 25.1.1 Row base — the §6.2 ambiguity resolved ✅ WIRE

§6.2 flagged that the decompiler appeared to place row data at the same byte as the row count
(`Data+0x10`) while the `+1` in the length formula implied rows begin after it. **The `+1`
wins: payload byte 0 is the row count and rows begin at payload byte 1.** Taking the first
payload byte as the row count reproduces every observed message length exactly, across five
lengths in the six-datagram set and 11,613 messages at scale.

### 25.1.2 The `(min, max)` pairing — four independent lines ✅

The field order was the last thing to settle, and one document left it explicitly open with
two candidate splits (a trailing 2-byte tail versus a leading 2-byte head), noting that the
choice changes which feature a value is attributed to. It resolves as **`[f0 lo hi][f1 lo hi]
[f2 lo hi][f3 lo hi][status ×2]`** — the trailing-tail layout, which is also the indexing the
decompiler uses (`data[base + r*stride + f*2]`).

1. **61,764 feature pairs with zero inversions.** `min ≤ max` is never violated. Across the
   whole campaign, `min > max` outside escapes: **0**.
2. ⭐ **An exact 64/64 bijection with the escape rows.** The only rows that break the
   invariant are escapes (`row[0] == 0xFF`), and **every** escape breaks it. That confirms
   both models simultaneously — the pairing *and* the escape marker — and it hands a reader a
   free integrity check that costs one comparison per row.
3. **The storage schema matches byte for byte.** `WP_0000N_01` in the measurement database has
   columns `Min_S01, Max_S01, … Min_S04, Max_S04`. The application does not transform the row;
   it writes it through.
4. **Behaviour under load.** Idle, `min == max` — which a constant would also satisfy, so idle
   data alone cannot decide it. Cutting, the envelope opens on **60–76%** of pairs and never
   inverts. This is why the idle captures could not settle the question and one cutting
   capture did.

### 25.1.3 The escape mechanism ✅ WIRE

```
row[0] == 0xFF   →  this row is an ESCAPE
row[1]           →  the marker
next row         →  carries the parameter
```

| Marker | Meaning |
|---|---|
| `0x00` | **new cycle** — the next row's byte is the new cycle index |
| `0xFB` | **per-feature reset** across all features (observed 82 times) |
| `0xFE` | **workpiece ID** — the next byte is the ID size, cross-checked against `[WorkpieceID] IDsize` |

🔴 **`0xFF` in a *Max* byte is ordinary saturation, not an escape.** Only `row[0] == 0xFF`
marks one. A reader that scans the whole row for `0xFF` will read saturated features as cycle
boundaries — and `M131 DEBI` on this installation has been sitting at 255 for months (§26.5),
so it would fire constantly.

Flag bits in the status bytes, gated on `version > 0xD8` (this box is `0xE5`, so all active):
`0x01` teach · `0x10` **start/stop** · `0x40` tool change · `0x08` sets bit 7 of the derived
status. `lo & 0x04` = alarm, which timestamps the row and fires the tool-wear path.

**Double buffering (§6.2) is unchanged and still matters.** On a mid-block cycle boundary the
remaining samples go to shadow maps and swap in at the boundary; ignoring it attributes
post-boundary samples to the wrong cycle.

⚠️ **No `0xFF` escape occurred in 73,289 rows of the idle captures** — no cycle marker, no
workpiece ID, no reset, no alarm flag. The escape table above is therefore ✅ for `0xFB` (82
observations in a cutting capture) and 🔶/⚠️ for `0x00` and `0xFE`.

### 25.1.4 The request, and `Geraet+0x688` = 1 ✅ WIRE

```
00 00 00 16 01 01 e7        unit 1        /* [00][00][00][cmd 0x16][station 1][flag 1][ck] */
00 00 00 16 01 01 e6        unit 2
```

§6.2 and §16.3 both record `Geraet+0x688` — the flag that becomes request byte 2 — as *"sent
as 0, meaning unknown."* **It is sent as 1.** The checksum closes on that reading for both
units (`−(1 + 22 + 1 + 1) = 0xE7`; `−(2 + 22 + 1 + 1) = 0xE6`) and only on that reading.

Its *meaning* is still unknown. But a reader reproducing PROVIS3's behaviour must send 1, and
a reader that sends 0 will get a checksum mismatch on every answer — not a timeout, a
mismatch, which is a much more confusing failure.

### 25.1.5 ⭐ The traffic was identified from the recovered rules alone

Worth recording as a method result, because it is the strongest possible test of a recovered
specification: nothing about the first capture's contents was known in advance, and three
constraints derived from unrelated parts of the spec converged on one interpretation.

1. **CAN identifier.** `0x0582 & 0x7F` = **unit 2**.
2. **Checksum residual.** Solving the answer checksum for the unmatched request gives
   `unit + Σ request[0…n−2] = 26`. With unit 2 as the seed, the request bytes excluding its own
   checksum sum to **24**. With `cmd 0x16 = 22`, the parameters must sum to 2.
3. **Length formula.** `0x16` is the one command with a *computed* answer length,
   `expected = rowCount × recordSize + 1`. Taking the first payload byte as the row count
   reproduces **all five** observed message lengths exactly, with `recordSize = 10`.

Command `0x16` is `MC_GIVESAMMELMERKMALE` — "give collected features". Three constraints from
three unrelated derivations, agreeing.

⚠️ **One intermediate step in that chain was wrong and it is instructive.** From "parameters
sum to 2" the first analysis concluded *station = 2*. The two readings `16 02 <ck>` (station 2)
and `16 01 01 <ck>` (station 1, flag 1) both sum to 2, and a later capture showed the second is
correct. The *conclusion* (`cmd 0x16`) was right; the *route* was ambiguous and was flagged as
such at the time. Arithmetic that admits two solutions should be reported as admitting two.

And from `stride = 10` the same analysis derived **featureCount = 4**, matching the four
sensors `MC_GIVEKONFIG` reports on this installation — a fourth independent agreement.

---

## 25.2 Configuration and identity commands

### 25.2.1 ⭐ `0x0D GIVEGERAETEREC` — `SGeraetRec`, 66 bytes, and the mixed-endian serial

Nine fields confirmed against the `Devices` table:

```
+0x00 GType          +0x01 GSubType       +0x02 Channel_Amount   +0x03 MiSens_Amount
+0x04 CDR            +0x05 Setup          +0x06 PLC_Konf         +0x07 Setup_Coll
+0x14 Serial_Num  (BIG-ENDIAN)            +0x16 SensorType_1..4
+0x1A MiSensType_1..8                     +0x22 SampleDiv
+0x26 ReduzLim    (little-endian)
```

🔴 **`Serial_Num` at `+0x14` is big-endian inside an otherwise little-endian payload.** It is
the only mixed-endian field known in the protocol, and it is the kind of error that ships: read
little-endian it yields large, plausible numbers.

**Independent confirmation, new in this edition.** §9.1 carries this field as
`date_or_crc // INFERRED (1974.txt: 29 A7)`. The two PMD dumps in this project settle it
without any capture:

| File | `+0x14` | BE | LE | Runtime log |
|---|---|---:|---:|---|
| `1974.txt` | `29 A7` | **10663** ✅ | 42793 | `Unit 2 … SNr 10663` ✅ |
| `exVL2-1.txt` / `exVL2-2.txt` | `29 A3` | **10659** ✅ | 41769 | `Unit 1 … SNr 10659` ✅ |

and, from the field campaign's own pair, `29 A4` → 10660 (LE: 42025) and `29 A9` → 10665
(LE: 43305). **Four serials, four exact matches, big-endian; four plausible and wrong numbers,
little-endian.** This closes **G10** completely and upgrades §9.1's `date_or_crc` line.

Two further cross-checks fall out of the same two files:

- **`+0x16 SensorType_1..4`** — unit 2 reads `30 14 14 14`, which against the §8.2 decoder ring
  is **VBI 211** (a vibration sensor) followed by three **PA 211**. The operator named
  feature 0 of that unit **`VIBRATION`**. Sensor type and operator label agree, from two
  unrelated sources. Unit 1 reads `00 00 00 00`. (§9.1 carries `+0x16` as
  `za_mi_area // INFERRED`; it is `SensorType`.)
- **`+0x1A MiSensType[8]` = `0x80` ×8 on both units** — PROCUR-S — and `+0x22 SampleDiv = 1`,
  `+0x26 ReduzLim = D4 19` → little-endian `0x19D4` = 6612. All three already ✅ in §9.1; the
  point is that the **same record mixes both endiannesses**, three bytes apart.

⚠️ **One value does not sit comfortably.** `+0x06 PLC_Konf` reads `0` in both PMD files, and
`0` in `GetPLCTypeTxt` is *"Unknown interface"* — while the units demonstrably have a working
fieldbus to the machine (§27.3). Either the PMD export predates PLC configuration, or the
enum at this offset differs from `GetPLCTypeTxt`'s. Worth one check before relying on the
field. `+0x07 Setup_Coll = 1` **does** cross-check: it corresponds to the config field
*"Collision during Setup"*, and §27.3 shows that carve-out is real.

### 25.2.2 ⭐ `0x0E GIVEKANAL` — feature names live from the device, and it embeds `0x23`

144-byte channel record, `SKanalRecV40`. ~120 of 144 bytes named.

```
+0x00..0x13   channel header  (PLC_Type, PLC_Version, Channel_Num, Teach_*, CDRLim1..4)
+0x14..0x4B   4 × 14-byte sensor records          ==  0x23 answers, byte-identical
+0x4D..0x78   4 × 12-byte feature descriptors:  [mask][11-byte NUL-padded ASCII]
+0x7C         MDL_Period          +0x7D  MDL_Time
```

**The name table sits at message offset `0x4D`** — exactly where §9.2 predicted it from the
configuration file, now confirmed on live traffic. Any reader can learn its own labels at
runtime by issuing one `0x0E` per unit; **no configuration file is needed**, and given §22.5.3
none should be trusted.

| mask | index | unit 1 | unit 2 |
|---|---:|---|---|
| `0x81` / `0x01` | 0 | `SPINDEL` | `VIBRATION` |
| `0x82` / `0x02` | 1 | `X AXIS` | `M131 DEBI` |
| `0x84` / `0x04` | 2 | `Y AXIS` | `M131BASINC` |
| `0x88` / `0x08` | 3 | `Z AXIS` | `M08 DEBI` |

**Feature index = log₂(mask & 0x0F).** The mask is **one-hot** (1/2/4/8), not an index. Match
on the low nibble; the `0x80` bit is a separate flag that is set on unit 1 and clear on unit 2
(§22.5.3) and whose meaning is open.

🔴 **`0x23 GIVE_SENSORVALUES` is redundant.** The four 14-byte sensor records at `+0x14`,
stride 14, are **byte-identical** to what `0x23` returns for the corresponding slot — verified
8/8 across both units, wire against wire, with no database involved. One `0x0E` at startup
yields all four; polling `0x23` is four extra exchanges per unit for data already held.

⚠️ **Cadence caution.** PROVIS3 asks for `0x0E` only on refresh — about **10 times in 4
minutes**. A passive listener may wait a long time for one. A master should ask once at
startup.

**Values are raw 0–255 counts.** This device generation has no scaling factor — re-confirmed
against the measurement database, where live samples, stored maxima and limit thresholds share
one unit (Part 7 stands, ✅ WIRE). `M131BASINC 38` means 38 counts of full scale.
🔴 **Engineering units require the sensor range from the PROCUR-S setup or datasheet. They are
not on the wire and cannot be recovered from it.**

### 25.2.3 `0x06 GIVEKONFIG` — byte-verified against the runtime log ✅ WIRE

```
00 e5 01 04 04 04 00 04 | 01 fa fc 07 08 32 08 fa | 02 ca
   ^^ ^^ ^^                                          ^^
```

`Version = 0xE5 = 229`, `Channels = 1`, `Sensors = 4`, trailing checksum `0xCA`. Against the
log line `bearbeite_Kom_06_MC_GIVEKONFIG: Version 229 Channels 1 Sensors 4` ✅.

**This validates the entire decode chain in one step** — gateway framing → record split →
fragment reassembly → field offsets → an independently produced log line.

⚠️ **Actionable for the reader:** `promos3_proto.c:78` marks `MC_GIVEKONFIG` as
`CONF_PROVISIONAL` with the comment *"offsets guessed"*. **The first three post-sequence bytes
are now byte-verified and may be promoted.** The remaining eleven bytes of the 14-byte body
are not, so promote the three, not the command.

### 25.2.4 `0x02 GIVEGTYPE` ✅ WIRE

```
00 44 05 01 b3
   ^^ ^^
```

`GeraetTyp = 0x44`, `SubTyp = 5`. Log: `Promos3DatenProvis2Geraet: Unit 1 Type 68 SubType 5 SNr
10659` — 68 = 0x44 ✅. Answer size **3**.

---

## 25.3 ⭐ The measured answer-size table — D3 and D4 closed

Message bytes **excluding** the checksum byte. Every entry confirmed by the spanning checksum
closing at exactly that length. **This supersedes §3.7.1's table for every command PROVIS3
actually asks.**

| cmd | name | size | cmd | name | size |
|---|---|---:|---|---|---:|
| `0x01` | `GIVESTATUS` | **2** | `0x14` | *(unnamed)* | **36** |
| `0x02` | `GIVEGTYPE` | **3** | `0x16` | `GIVESAMMELMERKMALE` | **`n×10 + 1`** |
| `0x05` | `GIVEUSEDZYKTAB` | **32** | `0x1A` | `GIVEHARDWAREREC` | **46** |
| `0x06` | `GIVEKONFIG` | **14** | `0x23` | `GIVE_SENSORVALUES` | **14** |
| `0x08` | `GIVEPLCVALUES` | **5** | `0x25` | `GIVE_ACTZYKINDEX` | **3** |
| `0x0D` | `GIVEGERAETEREC` | **66** | `0x29` | *(unnamed)* | **40** |
| `0x0E` | `GIVEKANAL` | **144** | `0x33` | `GIVEPROGID` | **2** |
| `0x0F` | `GIVEZYKLUS` | **170** | `0x12` | `GIVEALARM` | **17** |
| **`0x1B`** | **`GIVESIGNALVERLAUF`** | 🔴 **unknown — never observed** | | | |

### 25.3.1 D4 closed: `0x08` returns 5, not 1

The size table's blanket *"every SET returns a 1-byte ack"* does not apply to `0x08`. This is
the D4 branch:

```c
n = (Geraet[0x4e6] >> 4) + (Geraet[0x4e6] & 0x0F);
```

so that byte's nibbles **sum to 5** on this machine. **D4 is resolved as a value** without
needing to know which nibble is which. The body is `[in1][in2][in3][in4][out1]`, matching the
log line *"PLC inputs 4, outputs 1"* — a second, independent confirmation.

🔴 A reader hard-coding 1 times out roughly **sixteen times per second**.

### 25.3.2 Three misattributions in §3.7.1 — the suspicion there was correct

§3.7.1 flagged that three size-table entries did not align with the recovered command names and
suggested some entries may be keyed by **record type** rather than by command. Measured:

| Size | §3.7.1 had it at | **Actually belongs to** | Record |
|---:|---|---|---|
| 46 | `0x10` | **`0x1A GIVEHARDWAREREC`** | `SHardwareRec` |
| 170 | `0x03` | **`0x0F GIVEZYKLUS`** | `SZykRecV4802` |
| 40 | `0x0f` | **`0x29`** *(unnamed)* | — |

All three suspicions were right, and the record-type hypothesis is the likeliest explanation.

### 25.3.3 D3: two of three closed

- **`0x01 GIVESTATUS` = 2.** Closed.
- **`0x12 GIVEALARM` = 17.** Closed — and §16.2's suspicion that the `0x11 ALARMGESEHEN` entry
  had been borrowed for it was correct.
- 🔴 **`0x1B GIVESIGNALVERLAUF` — still unknown.** See §25.5. The value **257 is withdrawn**;
  it came from a synthetic test.

---

## 25.4 `0x12 GIVEALARM` — the event list ✅ WIRE

17-byte record. The request walks an index: `12 01 <index> 00 <ck>`.

```
[0]        total alarms held by this unit      (15 on unit 1, 16 on unit 2)
[1]        alarm code
[2..9]     context — channel / feature / limit / signal
[10..15]   DD MM YY hh mm ss
[16]       zero
```

**31 of 31 non-empty records parse as a valid date**; the other 7 are all-zero empty slots.

🔴 **Byte `[0]` is a count and is nonzero even in an empty slot**, so emptiness must be tested
on `[1..16]`. A reader testing `[0] == 0` will report every empty slot as a live alarm.

Observed codes: `0xFD`, `0x0C`, `0x23`, `0x24`, `0x0A`, `0x1A`, `0x1B`, `0x1E`. Timestamps span
2020–2025 — a genuine multi-year machine history, and useful evidence that the ring is not
cleared on restart.

```
code 0x24   12.01.2022 15:09:40   ctx 00 00 00 05 01 40 00 04   (16 held)
code 0x0A   31.10.2025 10:59:40   ctx 00 00 00 05 01 54 00 04
code 0xFD   24.07.2020 09:05:13
```

⚠️ **The code→text mapping is not on the wire.** `CDR_DESCRIPT_ENU.ini` is the place to resolve
it and it has not yet been cross-referenced. Open item.

⚠️ **`Constraints.Alarms = 50` against an apparently 16-entry ring.** Unresolved — walk `0x12`
past index 15 and see what comes back. Open item.

⚠️ **Alarm reporting is a poll, never a push.** The error string *"-CAN: Received data without
request"* exists precisely because unsolicited device traffic is an error condition. A reader's
alarm latency is bounded by its own poll interval and it **can miss transitions between
polls**. Since alarms are reports of completed events (Part 27), this is acceptable for
display — but a reader must never present itself as an alarm *annunciator*. Label the column
as reported, and stamp it with the **device** timestamp (§23.4.1), not the host clock.

---

## 25.5 🔴 `0x1B GIVESIGNALVERLAUF` — the last protocol gap

**Seven captures. 219,994 exchanges. Zero instances.**

What was ruled out along the way:

- it is **not** in the poll loop;
- it is **not** triggered by the machine running — 154 s of continuous cutting produced none;
- it is **not** produced by the `EventList`, `AlarmManager`, `DataLog`, `MonitoringSettings`,
  `System` or `CycleManager` screens.

⚠️ **A correction to earlier guidance in the campaign.** Capture was twice directed at the
`MonitoringData` screen. A screenshot showed this is the **PMD file manager** (Import/Export,
Load TO unit, Save from unit) — not a waveform view. Views present in the binary but **never
visited in any logged session**: `MainView`, `HoldView` (*BildHalt*), `Rework`, `TeachIn`,
`Action`.

### 25.5.1 ⭐ The fast way to find it needs no capture at all

The binary logs `-Request LoadSignalVerlauf: ` whenever it requests a trace. That string
appears **zero times** in every log collected. So:

```
1.  Navigate the PROVIS3 UI — MainView, HoldView, Rework, TeachIn, Action.
2.  findstr /i "SignalVerlauf" LogFile.txt
3.  Whichever screen produces that line is the one to capture.
4.  30 seconds with dumpcap, no --master, then check `unknown-size cmds > 0`.
```

Step 4's counter is the detector: a correct reader **deliberately refuses to guess `0x1B`'s
size**, so an incremented unknown-size counter is unambiguous.

### 25.5.2 It may not be needed at all

`0x1B` is the **waveform** — 125 consecutive samples, the curve shape. `0x16`, now fully
decoded, is the **envelope**: `(min, max)` per 20 ms window.

**PROVIS3 itself stores only the envelope.** `WP_0000N_01` holds exactly the `0x16` row; the
waveform is drawn on screen and discarded. For SQL, trending, reporting and alarms —
everything the application retains — the data is already available. `0x1B` matters only for
drawing the live oscilloscope view.

⚠️ Consequently **G9** (`channelKey` encoding) cannot move either: it needs a channel-bearing
`0x1B` body. The three candidate encodings in §16.2 remain three.

---

# ═══════════════════════════════════════════════════════════════
# PART 26 — LINK BEHAVIOUR, TIMING AND MACHINE STATE
# ═══════════════════════════════════════════════════════════════

**Question this Part answers:** *how does the link actually behave, and how do you tell from
the data whether the machine is cutting?*

---

## 26.1 Discovery and the poll loop ✅ WIRE

```
STARTUP, once per unit:     0x0D  →  0x06  →  0x0E        both units in lockstep
STEADY STATE, per unit:     0x16 · 0x08 · 0x01 · 0x33
```

The steady-state set is exactly the de-duplicated set §3.10 predicted from
`Promos3CanThread::sendCommandToUnit` (`0x16`, `0x08`, `0x01`, `0x12`), with `0x12` polled
less often. The startup triple was not predicted and is new: **`0x0D` before `0x06` before
`0x0E`** — device record, then configuration, then channel. A master should follow the same
order, because `0x0E`'s decode depends on the feature count `0x06` supplies.

---

## 26.2 🔴 Cadence is a client choice; latency is a device property ✅ WIRE

§3.10 and §17.1 describe *"a 3 ms polled loop"* as though it were a property of the protocol.
It is not. **The same application, against the same device, was observed at:**

| Cadence | Character |
|---|---|
| **1.5 ms** | free-running, unit-major |
| **15.6 ms** | one Windows timer tick |
| **31.25 ms** | two ticks, command-major |
| 250 ms | (a fourth capture) |

All with **zero errors**, sometimes 39 minutes apart. A 19× spread.

**First-answer latency was unchanged across all of them: median 1.2–6.0 ms, worst 9.8 ms.**
Against `[CAN] unitAnswerTimeout = 300` ms that is a factor of thirty of headroom, and it means
the polled loop is nowhere near being the bottleneck.

🔴 **Do not derive a timeout from an observed cadence.** They are unrelated quantities. Derive
it from the latency, and keep the app's own 300 ms.

Corroborating measurements: a complete answer occupies **1.4–1.8 ms** of bus time (9 frames in
1,443 µs; 11 frames in 1,759 µs), with consecutive frames **80–262 µs** apart. That spacing is
consistent with a bus in the several-hundred-kbit range and rules out a slow bus.

⚠️ `[CAN] BaudrateRegister = 22`, read as decimal-written-hex, is `0x16`, which is also the
`Promos3CanInterface` constructor's `this+0x24`. Suggestive, but the register-to-bitrate
mapping was never verified against PEAK documentation. **Treat the bitrate as unresolved.**

---

## 26.3 ⭐ The device samples at 50 Hz and caps an answer at 100 rows ✅ WIRE

🔴 **Row count is not a property of the answer. It is the backlog since that unit's previous
poll.**

| Capture | Poll interval | Rows/poll | **Rows/s/unit** |
|---|---:|---:|---:|
| A | 12.6 ms | 0–1 | 50.81 |
| B | 250.0 ms | 12–13 | 50.27 |
| C | 15.6 ms | 1–3 | 50.32 |
| D | 31.3 ms | 1–2 | 50.18 |

A **19× spread in poll rate; the underlying rate agrees within 1%.** The device feature sample
rate is **50 Hz** and the application's poll rate floats to match. (Measured independently at
50.1 /s on unit 1 and 49.8 /s on unit 2 in a separate capture.)

**And the row count saturates at exactly 100** — never 101. That produces:

- the **1,001-byte** maximum body (and the 1002-byte bucket in §22.6);
- the three transmit-buffer flush boundaries at 251/501/751 payload bytes (§24.1);
- a hard bound on reassembly buffer size.

### 26.3.1 🔴 The operational trap: never poll `0x16` slower than ~2 s per unit

At 50 Hz the 100-row cap fills in **exactly 2.0 seconds**. Beyond that, samples are lost
**silently**: the answer still arrives, still checksums, and simply contains less history than
the elapsed time. Nothing in the protocol reports the loss.

This is visible in the field data — eight 1002-byte answers on one unit (§22.6) are eight
occasions on which that unit's buffer saturated.

Useful corollaries: buffer for 1,001 bytes plus framing; size the xlsx/CSV writer for ~100
rows/s/unit; and if row counts start hitting 100, the poll loop is behind.

---

## 26.4 Error paths and sequence wrap

**Across 219,994 exchanges on a healthy link: 0 device errors, 0 timeouts, 0 sequence breaks.**
Retries were found only in a log — 13 events, all `try again`, none reaching `aborting`.

⚠️ **The abort branch remains unverified and must be tested by injection, not capture.** See
§24.4 for the full list of untested paths.

### 26.4.1 Sequence wrap is unreachable ✅

With the row count capped at 100 the largest possible answer is ~1,001 bytes ≈ **144 frames**.
A wrap past sequence 255 needs ~1,785 bytes. **It cannot occur in normal operation.**

A reader therefore need not fear it — but must never claim to have tested it. If a wrap is ever
observed, something upstream has changed and the 100-row cap should be re-measured.

---

## 26.5 Machine-state findings

### 26.5.1 🔴 `GIVEPROGID` and `GIVESTATUS` are useless as run indicators on this installation

Both returned `00 00` on **every poll of every capture**, including 154 s of continuous
cutting. Whatever populates them is not configured here.

**Use instead**, in order of reliability:

1. **`0x16` status bit `0x10`** (start/stop) — §25.1.3;
2. **escape-row bursts**, which land on cycle boundaries;
3. **amplitude** — feature values moving at all.

### 26.5.2 Cycle detection works, and two signals agree

A capture with the machine running showed **four part cycles on an exact 43-second period**,
~10 s of cutting each, with escape bursts landing **precisely** on the cycle boundaries. Two
independent signals — the periodicity of the amplitude envelope, and the escape marker —
agreeing without either being derived from the other.

### 26.5.3 ⚠️ `M131 DEBI` has been clipping at 255 for months

Median **255** on the wire in August; `Trend_C01_F02.Max_Val = 255` on every recent row back to
June. **A channel pinned at full scale carries no information and cannot meaningfully trip a
limit.** This is a sensor-range or scaling problem at the machine, not a protocol problem, and
it is a live monitoring defect on a production tool. Open item (§30.3).

It also interacts with §25.1.3: a reader that treats any `0xFF` as an escape will fire
continuously on this channel.

### 26.5.4 ✅ `SPINDEL` is healthy — an earlier recommendation withdrawn

An interim report suspected a dead sensor after `SPINDEL` read zero through 1,900 cutting
samples. A later capture showed it reaching **255**. The earlier operation simply did not load
the spindle. **That recommendation is withdrawn.** Recorded because acting on it would have
meant replacing a working sensor.

### 26.5.5 🔴 Display values differ from wire values — the wire is right

Reported discrepancy: `M08 DEBI` ≈ 180 in the reader, ≈ 220 on the PROVIS3 graph.

**The reader is correct.** `WP_00006_01.Max_S04` averages **188.1** against the reader's
178–188, and **no stored row anywhere holds an S04 value between 210 and 230**. The graph
applies a **display transform** — most likely scaling raw 0–255 onto the 0–300 plot axis
(× 1.176; 188 → 221).

This is consistent with ledger entry **C13**: the 0–300 axis is headroom, not an amplitude
range, and Part 7's "no scaling factor" result stands. What is new is that the *graph*
transforms for display while the *database* does not.

**Decisive test:** if `M131 DEBI` (raw 254–255) appears pinned at ~300 on the graph, the
transform is confirmed.

🔴 **Keep raw values in CSV and SQL — that is what the database itself stores — and apply any
transform at display time.** A reader that "corrects" its values to match the graph will
disagree with every historical row PROVIS3 ever wrote.

---

# ═══════════════════════════════════════════════════════════════
# PART 27 — CONTROL-FLOW OWNERSHIP: WHO STOPS THE MACHINE
# ═══════════════════════════════════════════════════════════════

**Question this Part answers:** *when a monitored value exceeds a limit, who produces the alarm
and who stops the machine — and what happens if a second PROVIS3 writes a limit to the same
unit?*

Parts 1–21 answer *how the bytes move*. They never ask *who decides*. This Part closes that
hole, and the answer determines whether a replacement reader is a safety-relevant component or
not.

⚠️ **Method note.** **No new decompilation was performed for this Part.** Every claim is
re-derived from artefacts already in the corpus: `mazak_strings.txt` (the binary's Qt string
table, including its own operator help text), `LogFile*.txt`, the config-DB schema, `1974.txt`,
and functions decompiled in Parts 3, 6, 9 and 13. Where this Part asserts something those
artefacts do not prove, it is marked ⚠️ INFERRED or 🔴 UNVERIFIED.

---

## 27.1 Headline

> **The limit comparison and the stop decision belong to the monitoring unit. PROVIS3 is not in
> the reaction path at any point. The machine does not evaluate anything — it receives one bit
> and applies its own PLC ladder to it.**

Three consequences follow immediately, and they shape the whole project:

1. **A replacement reader is not safety-relevant.** Protection survives PROVIS3 being closed,
   crashed, or replaced. This retroactively justifies the read-only-observer decision on
   **safety** grounds, not merely effort grounds.
2. **Nothing in the reader can cause or prevent a machine stop** — *unless it writes
   configuration*. The read path and the write path have entirely different risk profiles and
   must not share a code path or a CLI verb.
3. **The alarm the reader sees is a report of something that already happened.** It is not a
   trigger. Latency in the reader is a display problem, never a protection problem.

---

## 27.2 The three boxes

The report's vocabulary uses *device*, *unit*, *Geraet* and *monitor* interchangeably, and uses
*machine* loosely. For control-flow discussion that ambiguity is fatal. Three fixed names,
recommended for all subsequent documents:

| # | Name | What it is | Evidence it is separate hardware |
|---|---|---|---|
| **1** | **PC** | PROVIS3 HMI, 32-bit Qt4, Windows | — |
| **2** | **UNIT** | Prometec monitoring box, `MSL5081-16`, fw `Rtm_V14.5.H86`, cfg version 229 | own serial, own MAC, own firmware, own licence, own expansion slots — §27.2.1 |
| **3** | **MACHINE** | Mazak CNC + its PLC ladder | talks to UNIT only over a fieldbus — §27.3.3 |

### 27.2.1 UNIT is a standalone embedded device, not part of the CNC ✅

Five independent proofs, all from `mazak_strings.txt` and the runtime logs:

| Proof | Artefact |
|---|---|
| **Two of them on one machine** | `SNr 10659` and `SNr 10663`, both `Type 68 SubType 5` — a machine has one CNC |
| **Own identity block** | info-dialog fields: `Unit name · Unit type · Unit channels · Serial number · Firmware · Mac address · PLC-Interface · Unit hardware · Ethernet Anybus module · Sensor Modules` |
| **Independently flashable** | *"The firmware download will be started using the file %1 — the monitoring system might restart several times during this process"* — the Mazak keeps running throughout |
| **Own licence, serial-bound** | *"loading the wrong licence could set the monitoring unit out of service"*; `License error - Serial mismatch` |
| **Physical expansion slots** | *"A specific sensor module is assigned to each feature if there is one located in a slot"* — 4 × PROCUR-S (`0x80`) on this box |

⚠️ INFERRED but near-certain: UNIT is mounted **inside the machine's electrical cabinet**.
Nothing in the corpus states its physical location; the inference rests on the fieldbus wiring,
the sensor cabling to the drives, and normal retrofit practice. Not load-bearing for anything
below.

---

## 27.3 Evidence chain — who produces the alarm

### 27.3.1 The decisive artefact — the application's own Setup-mode help text ✅

The strongest single piece of evidence is the operator documentation embedded twice in the
string table (once for `Setup`, once for `SETUP`):

> *"During these trial runs, it is often expedient to prevent the not-yet optimized
> **monitoring system from intervening in the machine processes**. The SETUP function enables
> the triggered alarms to be shown on the display **WITHOUT any effect on the machine
> controller**. […] Application of this function **suppresses transmission of all alarms […]
> from the monitoring system to the PLC**. […] **Damage to workpiece, tool or machine will not
> be minimized as long as the SETUP function remains active.**"*

Four separate facts fall out of one paragraph:

1. The path is **monitoring system → PLC**. The PC is not mentioned; it cannot be, because
   Setup mode does not disconnect the PC — the display keeps working.
2. The monitoring system is the thing that **intervenes**. Not the machine, not the HMI.
3. Setup mode cuts **exactly one wire**: UNIT → PLC. Everything else keeps running.
4. Protection is *lost* when that wire is cut, which means protection **is** that wire.

Corroborating text from the Rework help, same structure:

> *"Application of this function while a machining process is running will result in the
> suppression of all alarms for limits of the underload, missing, work under […] types until
> the function is ended by the operator."*

And the safety carve-out that proves the mechanism is real:

> *"depending on the settings made when the system was commissioned, one limit of the Overload
> type at the top limit of the measuring range to monitor the machine for collisions may remain
> active when the Adjust mode is running"*

— cf. the config field `Collision during Setup` (`_CollisionDuringSetup`) and `Devices.Setup`,
and note that `SGeraetRec +0x07 Setup_Coll` reads **1** in both PMD files in this project
(§25.2.1). **A masking feature that has to carve out an exception for collision limits is
masking a real output, not a screen element.**

### 27.3.2 The limits physically live in UNIT ✅

The limit set is not evaluated where it is edited. It is **downloaded into UNIT** and stored
there:

```
"Do you really want to load %1 to the monitoring unit?
 All settings int the unit will be thereby overwritten!"        [sic]
```

with loader entry points `LoadAll() · LoadChannel() · LoadProgram() · LoadCycle() ·
LoadMerkmal() · LoadLimit()` (class `Promos3PMDLoader`), and completion logged as:

```
01.07.26 12:01:54.868   PMDload:  Finished Loading PMD to monitor 2
```

The `Limits` schema is device-side configuration, not display state:

```sql
Limits(Limtype, Level, Feat_Num, Response_Time, Act_Start, Act_End, Act_Mode, Pattern_Ref)
```

**`Response_Time` is the clincher.** A *reaction delay* field only makes sense inside the thing
that reacts; a PC-side display has nothing to delay. Likewise `Act_Start` / `Act_End` /
`Act_Mode` — a time window during which the limit is armed — is arming logic, and arming
happens where the comparison happens.

Confirmed at rest in `1974.txt`: `SGrenzRec`, 14 bytes, `Level` values
`20 / 35 / 50 / 70 / 115 / 140 / 152 / 170` — raw counts, the same unit as the samples (Part 7).

### 27.3.3 The UNIT → MACHINE wiring exists and is configured ✅

```
01.07.26 12:01:24.796   Promos3DatenProvis2Geraet:
    Unit 1 Type 68 SubType 5 SNr 10659 PLC inputs 4, outputs 1
01.07.26 12:02:15.511   Promos3DatenProvis2Geraet:
    Unit 2 Type 68 SubType 5 SNr 10663 PLC inputs 4, outputs 1
```

**4 input bytes, 1 output byte**, per unit, over a hard industrial fieldbus. From
`GetPLCTypeTxt`:

```
PROFINET IRT · PROFINET · DEVICENET · CANOPEN · INTERBUS · PROFIBUS DP · BAPSI
                                                        (0 = "Unknown interface")
```

**You do not specify PROFIBUS to talk to yourself.** That cable exists because boxes 2 and 3
are different devices.

The bit dictionary (UI list: `Outputs` / `The PLC outputs` / `Inputs` / `The PLC inputs`):

| Direction | Bit names |
|---|---|
| **UNIT → MACHINE** (⚠️ inferred split) | `Tool breakage · Tool wearout · Tool missing · Message Spindle 1 · Message Spindle 2 · Message Spindle 3 · AC-Control disabled` |
| **MACHINE → UNIT** (⚠️ inferred split) | `Program running · Axis Running · Spindle Running · X/Y/Z/W Axis running · Spindle at commanded speed · Rapid Feed · Start of cycle (SOC) · Cut valid · Prg-Tool Valid · Data valid · Reduced monitoring · External alarm reset · External Teach-In · New Tool · Message ack · Clear Message · Accl/Decl trigger (when SAP) · Control byte 1/2 · Data word · Workpiece ID · Reserve 1..4` |

⚠️ **INFERRED — the split is semantic, not read out of code.** It is supported by arithmetic:
the outbound list is **7 named bits + 1 reserve = 8 bits = exactly the 1 output byte** this box
reports, and the inbound list is ~25–30 bits, fitting the 4 input bytes. That fit is
suggestive, not proof. → **G16**.

Related: `[AlarmNames]` in `PROVISsettings.ini` for this install —
`1 Collision · 2 Break · 3 Wearout · 4 Missing · 5 Coolant · 6–8 blank`, with
`[Shortcuts] Type of alarm output = Wearout / Break / Collision`, and the per-limit config
field `Messageoutput` / `_MessageOutput` (*"Select the desired message output for which a
certain alarm message should appear"*).

**Each limit is individually mapped to an output slot at configuration time** — further
confirmation that the output assertion is UNIT's job and is pre-wired, not computed live by
anything on the PC.

### 27.3.4 PROVIS3's only write-back into the alarm path is *acknowledge* ✅

Inbound, on request only:

```
bearbeite_Kom_15 (MC3_ALARM)  /  MC_GIVEALARM cmd 0x12
    " Received Alarm: %d Status: %d"
    → Alarms(Date, ProgRef, ChannelNr, CycleNr, FeatureNr, LimitNr, Ack, Ack_Date,
             Signal, TimeOffset)
```

Outbound — **the entire set of PC→UNIT alarm-path writes**:

| Action | Artefact |
|---|---|
| Acknowledge / quit | `HandleAlarmQuit`, `* * * Quit Alarm`, subcommand `0x0A`, `0xFFFF` = clear all |
| Classify (bookkeeping only) | `Alarm correct` / `Alarm wrong` / `Alarm missing` / `Evaluate later` |
| Optionally re-tune limits | *"Shall PROVIS adjust the affected limits automatically?"* — a **configuration** write, deferred, operator-driven |

And the operator text for the acknowledge:

> *"The alarm is reset and the operator can move the machine again in order to find the alarm
> cause."*

**Reset — not stop.** There is no "stop the machine" verb anywhere in the PC→UNIT command set.

### 27.3.5 Counter-evidence considered and rejected

| Apparent counter-evidence | Why it does not overturn §27.1 |
|---|---|
| `Sende_Kom_27_MC3_SET_OUTPUTS` / `bearbeite_Kom_27` (`FUN_004b9150`), *"Outputs successfully set"* | PROVIS3 **can** command output bits. But this is group-2 (`MC3_`, the wrong generation for this box) and it is a commissioning / test-panel function — `Test selection` combo, `Outputs` / `Inputs` panel. It is not in the per-cycle loop, and the poll cycle (§3.10, §26.1) does not contain it. |
| MHI (Machine Health Inspector) alarm outputs — *"Select the output message to be set when a feed test generates an alarm"* | MHI runs scheduled **test cycles**, not production monitoring. Same output mechanism, different trigger. Does not put the PC in the production reaction path. |
| `changePMDfromNC` (`FUN_004341f0`) — a Mazak↔PMD **write** bridge | Selects *which configuration set* is active from the NC program. Configuration switching, not reaction. |
| `ACfeed` / `AC-Control disabled` / `ACfeed output` | Adaptive feed **control** is a separate licensed function with its own output byte (`_ACfeedOutput`). It modulates feed override continuously; it is not the limit-alarm path. Out of scope rather than counter-evidence. |

None of these puts the PC between a limit violation and a machine stop.

---

## 27.4 The reaction path, byte by byte

### 27.4.1 Downstream — limit → UNIT (configuration time, once)

**`SGrenzRec`, 14 bytes.** Real record from `1974.txt`:

```
d9 01 04 04 04 00 04 fa fc 07 08 32 08 fa
```

Column mapping, from the `Limits` DDL in the order emitted by `FuegeZeilezuLimitshinzu`:

```
Limtype, Level, Feat_Num, Response_Time, Act_Start, Act_End, Act_Mode, Pattern_Ref
```

Size 14 matches the expected-size table entries for commands `0x02` and `0x28` ✅.

🔴 **UNVERIFIED: which byte offset carries which column.** The 14-byte *size* is confirmed; the
field *offsets* are not. **Do not write a limit record from a guessed offset.** → **G14**.

**Limits also ride inside the cycle record**, and *that* part is verified and already
implemented in `promos3_config.c` — 7-byte entries at `+0x5D` of the 170-byte `SZykRecV4802`:

```c
size_t o = 0x5D;                                   /* 7-byte limit entries */
while (n < 8 && span_has(s, o, 7) && span_u8(s, o) == 0x01) {
    z.limits[n].level = span_u8(s, o + 1);         /* the threshold, raw 0..255 */
    z.limits[n].index = span_u8(s, o + 2);         /* which feature             */
    z.limits[n].term  = span_u8(s, o + 5);         /* 0xFB / 0xFF               */
    n++; o += 7;
}
```

Entry 0 is the channel / CDR limit (`Channels.CDRLim1..4` = `0xAA` = 170 on this box); entries
1..7 are per-feature by index.

### 27.4.2 At UNIT — the comparison

Everything needed for the decision is resident in UNIT and needs no external party:

| Input | Where it comes from |
|---|---|
| sample, raw 0–255 | sensor module in the slot |
| threshold `Level`, raw 0–255 | `SGrenzRec` / cycle record, stored at PMD download |
| hold-off `Response_Time` | same record |
| arming window `Act_Start` / `Act_End` / `Act_Mode` | same record |
| machining context | the 4 PLC **input** bytes from MACHINE |

**Same units on both sides.** Part 7 established there is no scaling factor: `Features.Feat_Max`
saturates at 255, `Trend.Max_Val` and `WP_*.Max_S0x` never exceed 255, `Sensors.Calibration` is
`'0'` on every row, and `Limits.Level` runs 20..170. **The comparison is a byte compare.**

### 27.4.3 Outbound — UNIT → MACHINE

One bit in the single output byte, asserted per the limit's configured `Messageoutput` slot,
after `Response_Time` has elapsed.

⚠️ **What MACHINE does with that bit is outside this corpus entirely.** Feed hold, spindle
stop, M00, block-stop or a lamp — that is the machine builder's PLC ladder. Nothing in the
PROVIS3 binary, the databases or the INI files describes it. → **G17**, and it is **not
closeable by reverse-engineering PROVIS3.**

### 27.4.4 Upstream — UNIT → PC (on request only)

`MC_GIVEALARM`, group-1 command `0x12`. The measured 17-byte record is in §25.4. The entry
format below is `MC3_`-derived and stays **PROVISIONAL** for this box:

```
[u16 alarmNumber][31-byte record]
    rec+0x00  u16  entryId
    rec+0x02  u16  status      ← LOW BYTE = ToolStatus code
    rec+0x1D  u8   channelKey  (0xFF = none)
```

ToolStatus low byte — **the reason for the stop** (§8.1):

```
0=empty        1=Overload      2=Underload          3=Contact
4=Missing      5=Work Over     6=Work Under         7=Cut start
8=Cut end      9=Dynam. upper  A=Dynam. lower       B=Pattern upper
C=Pattern lower D=ACF contact  E=cutdetect contact  F=Tool wear
```

🔴 **This transfer is a poll, never a push.** The error string *"-CAN: Received data without
request"* exists precisely because unsolicited device traffic is an error condition. Combined
with §3.2 — *answers carry no command and no group; both are inherited from the outstanding
request* — the alarm report is only interpretable in the context of the request that fetched
it.

### 27.4.5 Reset — and one path that does not involve the PC at all

- **PC:** `MC3_ALARM` subcommand `0x0A` / `HandleAlarmQuit`; `0xFFFF` clears all.
- **MACHINE:** the `External alarm reset` PLC **input** bit.

That second path is further confirmation of the ownership model: **MACHINE can clear an alarm
in UNIT directly, with PROVIS3 absent.**

### 27.4.6 The whole path in one figure

```
CONFIG TIME (once, PC present)
  PC ──14-byte SGrenzRec (+ cycle records)──▶ UNIT      "…will be thereby overwritten!"
                                              └─ stored in flash, PC no longer needed

RUN TIME (every cycle, PC may be OFF)
  MACHINE ──4 input bytes──▶ UNIT        (Spindle Running, Axis Running, SOC, Rapid Feed…)
  sensor  ──raw 0..255 ────▶ UNIT
                              │
                              │  sample > Level, held for Response_Time,
                              │  inside Act_Start..Act_End window?
                              │
                    ┌─────────┴─────────┐
                   no                  yes
                    │                   │
                 nothing    ┌───────────┴────────────┐
                            │                        │
                  ①  1 output bit ──▶ MACHINE   ②  alarm record stored in UNIT
                     (immediate, µs–ms)            (waits; PC must poll 0x12)
                            │                        │
                     MACHINE's own ladder      PC: display + Alarms table
                     decides stop/hold/lamp    (report only — no decision)

RESET
  PC: MC3_ALARM subcmd 0x0A          "…operator can move the machine again"
  or MACHINE: External alarm reset input bit
```

**The two arrows out of the decision are asymmetric, and that asymmetry is the whole answer:**
① is a wire and is immediate; ② is a mailbox and only empties when someone asks.

---

## 27.5 What a second PROVIS3 does

Scenario: a laptop running PROVIS3 joins the LAN, reaches the same gateway, and writes a limit
— while the machine's own PROVIS3 is running.

### 27.5.1 The machine's behaviour changes immediately ✅

The limit is in UNIT. UNIT compares against it on the next cycle. There is no staging, no
confirmation, no second party. **This is true regardless of what either PC displays.**

### 27.5.2 The other PC's display does **not** update ✅

There is no push. The protocol is strictly request/answer (§3.1) with one outstanding request
per unit; nothing arrives that a PC did not ask for. The other PROVIS3 keeps showing its
**local SQLite mirror** (`Provis-10663`) until it re-reads.

When it does resync, the reconcile layer runs:

```
Datenbankabgleich failed with %1 from Unit %2
Error in Datenbankabgleich from Unit %1
AbgleichDevice · AbgleichCycle · AbgleichSensor · AbgleichDeviceVersion
VglLimits_mit_Database · VglPattern_mit_Database
```

The row-matching strategy is **content-addressed** — `FindLimitRef` / `VglLimits_mit_Database`
match on the full tuple:

```sql
SELECT ID FROM Limits WHERE Limtype = … AND Level = … AND Feat_Num = …
    AND Response_Time = … AND Act_Start = … AND Act_End = …
    AND Act_Mode = … AND Pattern_Ref = …
```

A changed `Level` matches nothing → **a new row is inserted** and `LimitSet` is repointed,
rather than an update in place.

⚠️ INFERRED consequence: after resync the two installs agree on *values* but their `Limits.ID`
primary keys **diverge permanently**. Anything that correlates the two databases by ID —
including `Alarms.LimitNr` across installs — is unsafe. → **G15**.

### 27.5.3 🔴 The real hazard: two masters, anonymous answers

This is the finding that matters most, and it is structural rather than a configuration issue.

From `UnitComm_assembleAnswer_MC` (`FUN_00684160`), already in §3.2:

```c
group   = Paket_getGroup(requestPaket);          /* FUN_00436470 = *(u32*)request */
newMsg  = Promos3Paket_ctor(new(0x50), group, routerA, routerB, &assembledBytes, 0, 0);
newMsg[10] = local_13c;        /* +0x28 = command     ← copied from the REQUEST */
newMsg[11] = requestPaket[11]; /* +0x2c  sub-command  */
newMsg[12] = requestPaket[12]; /* +0x30  station      */
```

`local_13c = requestPaket[10]`, read **before any answer byte is touched**.

> **An answer's identity — group, command, sub-command, station — comes entirely from the
> receiver's own outstanding request. None of it is on the wire.**

Part 3 recorded this as a problem for *passive listening*. **It is a far worse problem for
concurrent mastering**, and that consequence was never written down before F-g:

- PC-A polls `0x16`; PC-B polls `0x12`. **Both receive both answers.**
- Each labels whatever arrives with **its own** pending command.
- An alarm record gets parsed as a measurement block, or a limit record as a status record.
- **Checksums still pass** — they are computed over bytes, and the bytes are intact.
- **Result: silent, plausible, wrong data on both PCs.** No exception, no log entry.

⭐ **This was subsequently demonstrated, not merely reasoned.** One capture contains **7 bad
checksums, all 7 inside the 52-second window** in which a second master was polling; none
before, none after. See §29.4.

The binary already knows this class of failure and complains about it locally:

```
"Requesting cmd %1 over pending requested cmd %2"
"Trying to send several Canbus commands before answer is received,
 last command %1 new command %2"
"-CAN: Received data without request"
"answer timedout, received"
[CAN] unitAnswerTimeout=300   [Comm] MaxResend=1
```

But those guards are **per process**. There is no bus-level arbitration, no token, no session,
no client ID. **The protocol assumes exactly one master.**

Secondary damage: the discovery churn. `searchForNewUnits` removes a unit after
`unitAnswerTimeout × 3` = 900 ms of no answer. With a competing master stealing answer windows,
both PCs will thrash:

```
11:56:06.714  searchForNewUnits: unit 1 detected as not active, will be removed
11:56:06.714  unRegisterUnit:    Unregister Unit 1
11:56:12.315  registerUnit:      Unit 1 registered
11:56:12.338  bearbeite_Kom_06_MC_GIVEKONFIG: Version 229 Channels 1 Sensors 4
```

⚠️ **Honest caveat:** in the captured logs this churn is the *normal idle* pattern (the poll
gate `this+0x28` is closed while the operator navigates menus). It is **not** evidence of a
second master in the reference capture. It is cited here as the **signature to expect** — the
difference being that with two masters it would be continuous and simultaneous on both PCs.

### 27.5.4 No locking, no version stamp — last writer wins 🔴

Nothing in the binary implements optimistic concurrency: no config revision counter compared
before write, no "changed by another client" check, no write lock. Combined with:

```
[Settings] PMDAutoSave = …
"Do you really want to load %1 to the monitoring unit?
 All settings int the unit will be thereby overwritten!"
```

…the machine's PROVIS3 can **silently revert a laptop's limit change** by pushing its own stale
cache, potentially without an operator pressing anything. Neither screen would indicate that
this happened. The device event log records `03 = Limit change` (§8.5) but nothing surfaces it
as a conflict.

### 27.5.5 The `MazakConnect` asymmetry ✅

The on-machine PROVIS3 is not merely another client. It has an NC API binding a laptop cannot
have:

```
01.07.26 12:01:24.734  NCMazak:      MazakConnect succeeded
01.07.26 12:01:24.734  NC::readVar:  MazakGetRegister : 8508-1, uniqueNum: 0
                       ... every ~3 s, indefinitely
```

with `NTIFDLL` / `MazConnect_s` / `structMazAnswer` / `readVar(SStation,int)` /
`writeVar(SStation,int,QStringList)` and the warning *"Handle was disconnected before calling
MazakDisconnect!!"*.

That instance is installed **on the CNC's own Windows PC**, beside the Mazak HMI, and uses it
to fill `Source_Ref` / `ProgRef` / `NCProgram: %1 in cycle: %2.%3` / `NCTool: %1 in cycle:
%2.%3`. A remote PC gets no `MazakConnect`, so its cycle→program correlation is blind and its
`Log` and `Source` tables will not line up with the machine's. ⚠️ INFERRED: this also means
`changePMDfromNC` cannot function on a remote install.

### 27.5.6 Operational rule

> **One master per gateway, at any instant.** To write configuration from a second PC, stop
> PROVIS3 on the machine PC first, write, then let it restart and resync. To read only, **do
> not master at all** — sniff promiscuously and observe both directions (§29.1).

---

## 27.6 New gaps opened by this Part

Continuing the register of Part 16 (G1–G13 in use; D3/D4 are device-state items).

| # | Gap | State | Blocks? | How to close |
|---|---|---|---|---|
| **G14** | `SGrenzRec` **field offsets** and the limit-**write** command number | size ✅ 14 B; offsets 🔴; write cmd 🔴 (`0x02` vs `0x28` both size-match) | only config **writes** | decompile the `SGrenzRec` parser + its `Sende_Kom_*`; **or** diff two PMD exports across one known `Level` edit — *no machine needed* |
| **G15** | Cross-install `Limits.ID` divergence after content-addressed resync | ⚠️ inferred | correlating two installs | compare `Limits` in two config DBs of the same unit |
| **G16** | PLC **bit-to-slot map**: which of the 8 output bits carries which `AlarmName` | ⚠️ inferred split; arithmetic fits | interpreting machine reaction | read `PLCReport` / `Channels.PLC_Konf` from the config DB; `GetPLCrec` (`FUN_004adb90`) |
| **G17** | MACHINE-side ladder semantics — what each output bit actually causes | 🔴 **out of scope** | nothing in this project | machine-builder documentation only; **not** obtainable from PROVIS3 |

🔴 **G14 is the only one with real risk attached.** Sending a wrong-command 14-byte payload to
a live unit is an uncontrolled write to a device that holds collision protection. The
no-machine route (diffing two PMD exports) should be exhausted first.

---

## 27.7 Consequences for the reader project

**ADR-F1 — The reader is a read-only observer, and this is now a safety argument, not only a
scope argument.** Protection lives entirely in UNIT↔MACHINE. A reader that never writes cannot
degrade protection. The original read-only decision stands, with a stronger justification than
it originally had.

**ADR-F2 — Separate the write path behind a hard gate.** Config writes are the *only* way this
project can affect machine safety. They must not share a CLI verb, a code path or a default
with reading. Suggested: a distinct `--write-config` binary or subcommand, refusing to run
unless the operator asserts that no other PROVIS3 is polling.

**ADR-F3 — Never master concurrently with a live PROVIS3.** §27.5.3 makes this a correctness
requirement, not etiquette. If master mode is used at all it must be **exclusive** — and per
§29.1 it should now rarely be used at all.

**ADR-F4 — Alarm display can be relaxed; alarm *fetching* cannot be trusted to arrive.** Alarms
are polled (`0x12`), so the reader's alarm latency is bounded by its own poll interval and it
can miss transitions between polls. Since alarms are reports of completed events this is
acceptable for display — but the reader must **never present itself as an alarm annunciator**.
Label the column as reported, with the device timestamp (§23.4.1), not the host clock.

**ADR-F5 — Document the three-box vocabulary in the reader's own docs.** The single most common
misunderstanding this Part corrects is *"PROVIS3 stops the machine."* Anyone reading the
reader's output needs to know it is watching a report, not a control loop.

---

## 27.8 Summary

| Question | Answer | Confidence |
|---|---|---|
| Who compares sample to limit? | **UNIT** | ✅ |
| Who produces the alarm? | **UNIT** | ✅ |
| Who tells MACHINE to stop? | **UNIT**, via 1 output bit over fieldbus | ✅ |
| What does MACHINE do with it? | its own PLC ladder decides | 🔴 out of scope (G17) |
| Is PROVIS3 in the reaction path? | **No** — display, log, acknowledge only | ✅ |
| Does protection survive PROVIS3 closing? | **Yes** | ✅ |
| Does protection survive UNIT being off? | **No** | ✅ |
| What goes down the wire as a limit? | `SGrenzRec`, 14 bytes; `Level` = raw byte 0–255 | ✅ size / 🔴 offsets (G14) |
| What comes back as an alarm? | `[u16 no][31-byte rec]`, `rec+0x02` low byte = ToolStatus | 🔶 provisional (G7); size 17 ✅ WIRE |
| Will a second PROVIS3 see my limit? | machine: instantly. other screen: only after resync, and IDs will diverge | ✅ / ⚠️ (G15) |
| Is it safe to run two PROVIS3 masters? | **No** — answers are anonymous; silent cross-decoding | ✅ reasoned, ⭐ demonstrated (§29.4) |

---

# ═══════════════════════════════════════════════════════════════
# PART 28 — DATABASES, CONFIGURATION AND THE QODBC BACK-END
# ═══════════════════════════════════════════════════════════════

**Question this Part answers:** *is the stored history usable, and can PROVIS3 be pointed at
SQL Server?*

Two independent efforts feed this Part: the campaign's attempt to switch the running
application to `QODBC` (which failed twice, for two different reasons, and caused an outage),
and a later deployment session that resolved the first of those reasons. They agree on the
conclusion and disagree on nothing.

---

## 28.1 The measurement schema, verified against real files ✅

`ProvisLog-10660` / `ProvisLog-10665`, SQLite, **15 tables**, `user_version = 10`, integrity
ok. The Ghidra-derived schema of Part 10 is confirmed:

| Table | Rows | Content |
|---|---:|---|
| `Log` | 7,040 | cycle index; **`Data_Ref` is the join key** into `WP_*` |
| `WP_0000N_01` × 6 | 319,683 | ⭐ `Min_S01..Max_S04` — **the `0x16` wire row, written through unmodified** |
| `Trend_C01_F01..F04` | 456 ea. | per-feature peak per cycle |
| `Status_C01`, `Statistics` | 456 ea. | joined on `Source` |
| `Alarms` | 6 | `FeatureNr` 0–3 — **confirms 0-based feature indexing** |

The `WP_*` correspondence is the third of the four independent lines that settle the `(min,max)`
pairing (§25.1.2): **the application does not transform the row, it stores it.** That is what
makes a replicator viable and it is what makes the wire format worth decoding at all.

---

## 28.2 🔴 Measurement logging stopped on 2026-06-23

**Both files stop on 2026-06-23.** The machine was demonstrably cutting on **2026-08-06** —
39,000 exchanges of it were decoded from the wire — and **none of it is in these files.**
Roughly **six weeks of history is missing.**

The files sit at **7.88 MB and 8.35 MB** against:

```ini
[…]
DBLimitedTo = 1        ; 1 = limit by FILE SIZE
MaxFileSize = 10       ; megabytes
```

Either they rolled over to historic copies, or **logging stopped at the ceiling and has been
silently discarding since**.

🔴 **This must be resolved before any replicator is worth building.** Replicating a database
that stopped receiving data six weeks ago produces an empty result and a confident-looking
pipeline.

**Mitigation:** switching to `DBLimitedTo = 3` (limit by workpiece count) avoids the file-size
ceiling entirely. Locate the historic files first.

This is open item **2** in §30.3 and one of only two items on the critical path.

---

## 28.3 The INI settings that matter for durability

| Key | Reference value | Should be | Why |
|---|---|---|---|
| `JOURNALMODE` | `OFF` (this project's copy) | **`WAL`** | lets an out-of-process replicator read while PROVIS3 writes |
| `SYNCMODE` | `0` | **`1`** | removes power-loss corruption risk |
| `DBLimitedTo` | `1` (file size) | **`3`** (workpiece count) | avoids the §28.2 ceiling |
| `MaxFileSize` | `10` | — | only relevant while `DBLimitedTo = 1` |

⚠️ **A value of `JOURNALMODE = ON` was observed on the target install during the campaign.**
`ON` is **not a legal SQLite journal mode.** SQLite ignores it and falls back to the default —
which is *safer* than the original `OFF`, but is not what was intended and is not what anyone
would predict from reading the file. The reference copy in this project still reads `OFF`.
Set `WAL` explicitly.

---

## 28.4 The QODBC attempt — failed twice, for two different reasons

### 28.4.1 Attempt 1 — the plugin is not installed

```
The driver type: QODBC is not available. Error: −1, Driver not loaded        × 79
```

The Qt plugin `qsqlodbc4.dll` is **absent from the installation**. The application never
reached a SQL Server, so **nothing about credentials, dialect or schema was tested** by this
attempt. It is a missing-file failure, not a licensing or feature lock. §28.5 resolves it.

### 28.4.2 🔴 Attempt 2 — a self-inflicted outage

With `Log_Type = QODBC` and placeholder credentials, **unit discovery stopped entirely**:

```
240 driver errors
156 register events / 141 UNregister events
"Menu Navigation: No connected device"
93 × "GetCreationDate: OpenDatabase() failed"
```

The failed log-database open **cascaded**: `AddP2Geraet` could not verify the database version,
and registration never completed. Reverting `Log_Type` to `QSQLITE` restored it; units now
register in 50 ms.

🔴 **Lesson recorded against the campaign's own advice: six INI changes were delivered at once.
Change one thing per restart.**

The structural point is worth extracting: **a database failure takes down unit discovery.**
The two subsystems are not isolated. Any experiment with `PMD_Type` / `Log_Type` on a
production machine is an experiment with whether the machine is monitored.

### 28.4.3 QODBC may not be viable on this build regardless

`attachPmdDatabase` issues:

```sql
ATTACH '…Provis-10660' AS …
```

**on the log-database connection.** `ATTACH` is SQLite-only. The PMD file must therefore live
on a SQLite connection, which means the log connection **cannot** be SQL Server — at least not
while the two are attached to each other.

That the vendor shipped without the ODBC plugin at all is corroborating evidence that the path
was never exercised in production.

---

## 28.5 Making the ODBC branch reachable

Part 12.1 establishes that the binary carries a **dual-driver** SQL abstraction targeting both
`QSQLITE` and `QODBC`. This section documents activating it on a real install: why the stock
deployment cannot reach it, what artefact is missing, and how it was obtained under real
constraints (**no administrator rights, no MSVC toolchain**).

**Status at close:** plugin deployed and version-matched ✅ · configuration not yet switched ⚠️ ·
end-to-end SQL Server write **unverified** ⚠️.

### 28.5.1 Why a plugin is required at all

Qt 4 does not link SQL back-ends into `QtSql4.dll`. Each driver is a separate plugin DLL,
discovered at runtime by scanning the `sqldrivers/` subdirectory of every registered library
path. The application directory is registered by default, which is why a bare `sqldrivers\`
folder beside the executable is sufficient — **no `qt.conf` was needed**.

Naming scheme `qsql<driver>4.dll`:

| Driver name in `PMD_Type` / `Log_Type` | Plugin file | Present in stock install |
|---|---|---|
| `QSQLITE` | `qsqlite4.dll` | ✅ yes (444,928 bytes, 2012-11-26) |
| `QODBC` | `qsqlodbc4.dll` | ❌ **absent** → added |
| `QMYSQL` | `qsqlmysql4.dll` | ❌ n/a |
| `QPSQL` | `qsqlpsql4.dll` | ❌ n/a |

This confirms Part 12's reading **from the deployment side**: the vendor ships one binary
supporting both dialects and selects the back-end purely by *which plugin is present plus which
driver name is configured*. **Nothing in the executable had to change.**

> **Corroborating detail.** `qsqlite4.dll` sits in the *install's own* `sqldrivers\` directory
> rather than in a Qt-wide plugin path, which proves the vendor's deployment model uses the
> application-directory search path. The added `qsqlodbc4.dll` therefore lands on a path the
> binary is **already demonstrably scanning**, rather than a speculative one. ✅

### 28.5.2 Two compatibility gates, either of which rejects silently

**Gate 1 — build key.** Every Qt 4 plugin exports `qt_plugin_query_verification_data`,
returning a build key the host compares against its own compiled-in `QT_BUILD_KEY`. On Windows
the key encodes the **compiler family**, so an MSVC-built host rejects a MinGW-built plugin
outright.

PROVIS3 imports `MSVCR90.dll` with a `Microsoft.VC90.CRT` manifest 🔶 → built with **MSVC 2008
(VC90), 32-bit**. The plugin must come from a `vs2008` Qt distribution. The `mingw`, `vs2010`
and `vs2013` variants are all disqualified.

**Gate 2 — version rule.** The loader requires the plugin's Qt **major** version to equal the
host's, and the plugin's version to be **≤** the host's. The patch level is not compared.

| Host `QtCore4.dll` | 4.8.4 plugin verdict |
|---|---|
| 4.8.0 – 4.8.7 | ✅ accepted |
| 4.7.x or older | ❌ rejected — *"uses incompatible Qt library"* |

Measured: host = `4.8.4.0`, plugin = `4.8.4.0` ✅ — an **exact** match, not merely a compatible
one. Analytically useful: it **collapses the remaining failure surface to configuration and to
the ODBC stack itself**.

### 28.5.3 Why a from-source build was rejected ⚠️→✅

The available toolchain was portable MinGW (`w64devkit`). Building
`src/plugins/sqldrivers/odbc` with it fails on two independent grounds:

1. **Build-key rejection** — the resulting DLL is refused at load time regardless of
   correctness.
2. **C++ ABI incompatibility** — the plugin passes `QString`/`QVariant` objects across the DLL
   boundary into the host's MSVC-built `QtSql4.dll`. MinGW and MSVC differ in name mangling,
   vtable layout and exception handling. Even a force-loaded plugin would fault.

Additionally, building the plugin at all requires a complete Qt 4 build tree (headers plus
import libraries) produced by the *same* compiler — i.e. the whole framework would have to be
built first.

**Conclusion: extraction from the official binary distribution is the only viable path.**
Recorded because *"just compile it"* is the intuitive response and it is a dead end.

### 28.5.4 Acquisition procedure — no admin rights, no MSVC

**Artefact.** `qt-win-opensource-4.8.4-vs2008.exe`, 244,861,376 bytes, from the Qt archive.
⚠️ Note that **4.8.6 is the last release offering a `vs2008` build**; 4.8.7 ships
mingw/vs2010/vs2013 only and is unusable for this target.

🔴 **The blocking detail.** The Qt installer is an **NSIS-2** package. 7-Zip can extract from
NSIS payloads, but *only* through the full `7z.exe` + `7z.dll` pair — the reduced `7zr.exe` and
`7za.exe` builds handle 7z-format archives only and fail with *"Cannot open the file as
archive."* Observed directly, and **the single most likely place for a reproduction attempt to
stall.**

Bootstrap, entirely user-writable:

```powershell
# 1. 7zr CAN open the 7-Zip distributable, because that one is a 7z SFX
.\7zr.exe x 7z2602-x64.exe -o"C:\Users\<user>\7zip" -y

# 2. the extracted full 7-Zip then handles the NSIS payload
cd C:\Users\<user>\7zip
.\7z.exe l "C:\...\qt-win-opensource-4.8.4-vs2008.exe" | Select-String qsqlodbc
```

Observed archive structure ✅ — outer PE wrapper, inner NSIS-2 stream, `$_14_` being the NSIS
output-directory variable preserved literally as a folder name:

```
Type = PE  →  Path = [0], Type = Nsis, SubType = NSIS-2, Method = LZMA:23
  $_14_\plugins\sqldrivers\qsqlodbc4.dll     89,600   2012-11-26 03:50:40   ← target
  $_14_\plugins\sqldrivers\qsqlodbc4.lib      2,070
  $_14_\plugins\sqldrivers\qsqlodbcd4.dll   164,352   ← DEBUG build, do not deploy
  $_14_\plugins\sqldrivers\qsqlodbcd4.lib     2,084
  $_14_\src\plugins\sqldrivers\odbc\tmp\obj\release_shared\qsqlodbc.intermediate.manifest
```

Extraction (`e` flattens the path; the `$` requires escaping in PowerShell):

```powershell
.\7z.exe e "C:\...\qt-win-opensource-4.8.4-vs2008.exe" `
    -o"C:\Users\<user>\qtplugin" "`$_14_\plugins\sqldrivers\qsqlodbc4.dll" -y
```

> 🔴 **Trap.** `qsqlodbcd4.dll` (the `d` suffix, 164,352 bytes) is the **debug** build and will
> be rejected by a release host. **Size is the fastest discriminator: 89,600 = release.**

### 28.5.5 Deployment and post-conditions

```powershell
$provis = "…\CoroPlus\Provis3"
New-Item -ItemType Directory -Path "$provis\sqldrivers" -Force | Out-Null
Copy-Item …\qtplugin\qsqlodbc4.dll "$provis\sqldrivers\" -Force
```

| File | Size | Date | Origin |
|---|---:|---|---|
| `sqldrivers\qsqlite4.dll` | 444,928 | 2012-11-26 10:49 | vendor (pre-existing) |
| `sqldrivers\qsqlodbc4.dll` | 89,600 | 2012-11-26 02:50 | added |

| Verification | Result |
|---|---|
| Host `QtCore4.dll` FileVersion | `4.8.4.0` ✅ |
| Plugin FileVersion | `4.8.4.0` ✅ |
| Plugin variant | release (89,600 B, not 164,352 B) ✅ |
| Target directory already on Qt's scan path | ✅ proven by the existing `qsqlite4.dll` |
| Binary unchanged | ✅ no patching required |

**Recommended additional check (not yet run).** Hash the installer's `qsqlite4.dll` against the
install's copy. A match proves the vendor deploys the *stock* Qt 4.8.4 VS2008 build rather than
a private rebuild, raising plugin-acceptance confidence from "version-matched" to "provably
identical toolchain":

```powershell
.\7z.exe e "...\qt-win-opensource-4.8.4-vs2008.exe" -o"…\qtplugin" -r "qsqlite4.dll" -y
Get-FileHash …\qtplugin\qsqlite4.dll, "$provis\sqldrivers\qsqlite4.dll" | Select Hash, Path
```

---

## 28.6 Configuration surface — INI keys → ODBC connection string ✅

The connection string is assembled from the format literal at `0x009632c0` ✅:

```
DRIVER={SQL SERVER};SERVER=%1;PORT=%2;PASSWORD=%3;USERNAME=%4;DATABASE=%5
```

Cross-referencing the INI-key literals in the `0x00957f14`–`0x00958114` cluster against the
shipped `PROVISsettings.ini` gives a complete, **verified** parameter map. **Every ODBC key is
already present in the reference file — merely commented out**, because that install runs
SQLite:

| Format slot | PMD key | Log key | Reference INI state | Notes |
|---|---|---|---|---|
| `SERVER=%1` | `PMD_Hostname` | `Log_Hostname` | `#PMD_Hostname = localHost` | commented; default hint `localHost` |
| `PORT=%2` | `PMD_Port` | `Log_Port` | `#PMD_Port =` | commented, empty |
| `PASSWORD=%3` | `PMD_Password` | `Log_Password` | `#PMD_Password=` | commented, empty |
| `USERNAME=%4` | `PMD_Username` | `Log_Username` | `#PMD_Username = manufact` | commented; **default hint `manufact`** |
| `DATABASE=%5` | `PMD_Databasename` | `Log_Databasename` | `Provis` / `ProvisLog` | **active** |
| *(driver select)* | `PMD_Type` | `Log_Type` | `QSQLITE` | **the switch** |
| *(SQLite-only)* | `PMD_Dir` | `Log_Dir` | `#PMD_Dir =` | file path; meaningless under ODBC |

**Analytical value.** The commented block is effectively **vendor documentation of the ODBC
deployment mode**: it names every key, preserves the intended ordering, and leaks two defaults
(`localHost`, `manufact`) that would otherwise have to be guessed. It also confirms the PMD and
Log databases are configured **independently** — they can run on different back-ends, which is
the basis of the staged migration in §28.9.

Two further keys in the same cluster — `JOURNALMODE` and `SYNCMODE` — drive the
`PRAGMA journal_mode =` / `PRAGMA synchronous =` literals at `0x009633ac` and `0x009633c4`.
These are SQLite-only statements; whether the ODBC path branches around them is §28.8.2.

---

## 28.7 Verification methodology — four layers

Four independent layers, ordered so each isolates a different failure domain. **This ordering
is the deliverable** — running them out of order conflates Qt-level failures with ODBC-level
ones.

### Layer 1 — ODBC stack, PROVIS3 excluded

Test the exact connection-string shape outside the application. 🔴 **Must be run from 32-bit
PowerShell** (`C:\Windows\SysWOW64\WindowsPowerShell\v1.0\powershell.exe`), because PROVIS3 is
a 32-bit process and therefore binds the **WOW64** ODBC stack — the 64-bit driver registry is a
different namespace and testing there proves nothing.

```powershell
$cs = "DRIVER={SQL SERVER};SERVER=<host>;DATABASE=<db>;UID=<user>;PWD=<pw>"
$c = New-Object System.Data.Odbc.OdbcConnection $cs
$c.Open(); $c.State; $c.Close()
```

Driver registration: `HKLM:\SOFTWARE\WOW6432Node\ODBC\ODBCINST.INI\ODBC Drivers`, or
`C:\Windows\SysWOW64\odbcad32.exe`.

### Layer 2 — Qt plugin acceptance

```powershell
$env:QT_DEBUG_PLUGINS=1
& "$provis\<exe>.exe"
```

PROVIS3 is a GUI-subsystem binary, so `qDebug`/`qWarning` output goes to `OutputDebugString`
and requires **DebugView** to observe. Success = the loader reports `qsqlodbc4.dll` with keys
`("QODBC", "QODBC3")`. The failure text distinguishes *"not a Qt plugin"* from *"incompatible
Qt library"* — i.e. it discriminates gate 1 from gate 2 of §28.5.2.

### Layer 3 — application-level acceptance, using the binary's own diagnostics

The most economical oracle, because the relevant literals are already recovered:

| Log literal | Address | Meaning |
|---|---|---|
| `The driver type: %1 is not available. Error: %2, %3` | `0x00963368` | plugin still not loaded → return to Layer 2 |
| `Fail to open database Type: %1; Name: %2; Directory %3 - Error: %4` | `0x00963278` | plugin loaded ✅, connection refused → Layer 1 problem; `%4` carries the raw ODBC diagnostic |
| `The database has invalid connection for %1` | `0x0096330c` | connection object resolved but unusable |
| `There is no connection name for the database %1` | `0x00963338` | connection-key resolution failure (config, not driver) |
| `database connection for: pmd_<SN> successfully set` | *(observed)* | **success** — emitted by `InitializeDatabase` |

```powershell
Select-String -Path "$provis\LogFile.txt" `
  -Pattern "not available|Fail to open database|invalid connection|InitializeDatabase" | Select -Last 40
```

The reference `LogFile.txt` shows the success form under SQLite — `InitializeDatabase: database
connection for: pmd_10663 successfully set` — with **one pair of `pmd_*` / `log_*` connections
per unit serial**, plus one pair per archived database generation. That per-unit fan-out is the
expected shape under ODBC too, and **its absence would itself be diagnostic**.

### Layer 4 — proof of write

ODBC tracing is authoritative: `C:\Windows\SysWOW64\odbcad32.exe` → **Tracing** tab → log path
→ *Start Tracing Now*. Settings live under `HKCU`, so **no elevation is required**. The trace
captures `SQLDriverConnect` (revealing the assembled connection string verbatim) followed by
`SQLExecDirect` carrying the `CREATE TABLE` / `INSERT INTO` statements. ⚠️ Disable afterwards —
it is slow and grows without bound.

Corroborating signals:

- SQLite artefacts (`Provis-<SN>`, `ProvisLog`) should **cease being modified** — check
  `LastWriteTime`.
- Server-side, `SELECT name, create_date FROM sys.tables ORDER BY create_date DESC` should show
  the app's own schema appearing. Per Part 12.1 the ODBC branch emits
  `CREATE TABLE … IDENTITY(1,1)` and **omits the `ID` column on insert**, so **an empty target
  database is the correct starting state** — the application builds its own schema.

---

## 28.8 Risk register

### 28.8.1 🔴 `UeberpruefeTabelle` uses SQLite-only syntax ⚠️ **[HIGH]**

`SqlDb_checkTableExists` (`FUN_00526d10`, tag-proven `"UeberpruefeTabelle"`) issues:

```sql
SELECT name FROM sqlite_master WHERE type='table' AND name= '%1'      @ 0x00963448
```

`sqlite_master` **does not exist on SQL Server.** A string-table sweep found **no equivalent
table-existence probe** for the ODBC dialect. The nearest relative is a *column*-level probe:

```sql
SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = '   @ 0x00962718
```

`INFORMATION_SCHEMA` is ANSI/SQL-Server vocabulary, which **proves a genuine SQL-Server-aware
code path exists** and that the ODBC support is not vestigial ✅. But it answers a different
question.

Three hypotheses, in decreasing likelihood:

1. `FUN_00526d10` branches internally on driver type and the ODBC arm reuses the
   `INFORMATION_SCHEMA` query (a non-empty column list implying table existence). ⚠️
2. Table existence under ODBC is inferred from lazy-create failure rather than probed —
   consistent with `SqlDb_fuegeAlarmsHinzu` being described as *"lazy-creates + INSERTs"*. ⚠️
3. The probe is genuinely SQLite-only and the ODBC path is incompletely maintained. ⚠️

**Action:** re-open `FUN_00526d10` in Ghidra and check for a dialect branch and an xref from it
to `0x00962718`. **This is the highest-value single next step for the migration** — it
determines whether ODBC is a configuration change or a code-level dead end. Related literals to
trace: `Creating the table %1 from database %2 failed. Error %3 %4` (`0x0096354c`),
`FuegeTabellehinzu` (`0x009635f0`), `GetTables` (`0x00963540`),
`The database %1 does not contain the table %2 …` (`0x00963590`).

⚠️ **Note this is the same class of problem as §28.4.3's `ATTACH`, found by a different
route.** Two independent SQLite-only statements sit in the connection path. That is not a
coincidence; it is what an unexercised code path looks like.

### 28.8.2 SQLite `PRAGMA` statements under ODBC ⚠️ **[MEDIUM]**

`PRAGMA journal_mode =` (`0x009633ac`) and `PRAGMA synchronous =` (`0x009633c4`) are driven by
`JOURNALMODE` / `SYNCMODE`. If `SqlDb_openDatabase` (`FUN_00525700`) issues these
unconditionally, **every ODBC connection open will generate a syntax error from SQL Server.**
Whether that is fatal or merely logged is unknown. **Action:** inspect the `PRAGMA` emission
site in `FUN_00525700` for a driver-type guard.

### 28.8.3 `{SQL Server}` driver is legacy ⚠️ **[MEDIUM]**

The driver name is **hardcoded in the format literal** — it is not configurable through the
INI. `{SQL Server}` is the original driver bundled with Windows and **predates TLS 1.2
support**. Against a modern SQL Server instance enforcing TLS 1.2 it can fail at handshake time
regardless of credentials. There is no configuration-level remedy: mitigations are server-side
(permit the legacy protocol) or binary patching of the literal. **Layer 1 surfaces this before
any application-level work is wasted on it.**

### 28.8.4 Settings file not located ⚠️ **[BLOCKING for that install]**

`PROVISsettings.ini` was **absent from the application directory** on the target install ✅
(observed — `Copy-Item` failed with `PathNotFound`). Nothing can proceed until it is found: the
`PMD_Type` / `Log_Type` switch is the entire activation mechanism.

```powershell
Get-ChildItem -Path $provis -Recurse -Filter "*.ini" -ErrorAction SilentlyContinue
Get-ChildItem "C:\ProgramData","$env:APPDATA","$env:LOCALAPPDATA" -Recurse -Filter "PROVIS*.ini" -ErrorAction SilentlyContinue
Get-ChildItem HKCU:\Software -Recurse -Depth 2 | Where-Object Name -match 'PROVIS|Promos|Coro'
```

The registry sweep is included because `QSettings` falls back to the registry when no
INI-format path is configured. Note also that the vendor demonstrably ships **multiple INI
variants** (`NCaccess.ini`, `OLD-NCaccess.ini`, `PROVISsecurity.ini`, `ALT2-NCaccess.ini`), so
a differently named or per-profile settings file is plausible.

### 28.8.5 Back up before switching ⚠️

`PMD_Type` / `Log_Type` govern **where live production data is written**, and §28.4.2 shows a
failed switch takes unit discovery down with it. Make the change on a copy, preserve the
pre-change INI, and change one key per restart.

---

## 28.9 The decision: replicate, don't migrate

**Recommended architecture: PROVIS3 keeps writing SQLite; an out-of-process replicator copies
to SQL Server.**

| | In-place ODBC migration | Out-of-process replicator |
|---|---|---|
| Vendor support needed | effectively yes | **no** |
| Can corrupt the monitoring system | **yes** (§28.4.2) | no |
| Blocked on `sqlite_master` / `ATTACH` | **yes** (§28.4.3, §28.8.1) | no |
| Blocked on legacy TLS | possibly (§28.8.3) | no |
| Couples machine uptime to database uptime | **yes** | no |
| INI changes required | many | **two** (`JOURNALMODE = WAL`, `SYNCMODE = 1`) |

It decouples the machine from the database, cannot corrupt the monitoring system, and needs no
vendor support. **The two INI changes it requires are the ones §28.3 recommends anyway.**

⚠️ And §28.2 must be resolved first, or the replicator will faithfully copy a database that
stopped six weeks ago.

### 28.9.1 If ODBC is mandated anyway — the staged sequence

Derived from the independence of the PMD and Log configuration blocks (§28.6). This staging
keeps the production measurement path on the known-good back-end while the risky one is
exercised:

1. Resolve §28.8.4 (locate settings) — **blocking**.
2. Run **Layer 1** to clear the ODBC stack and §28.8.3 *before touching the application*.
3. Resolve §28.8.1 in Ghidra — **determines feasibility**.
4. Switch **`Log_Type` only** to `QODBC`, leaving `PMD_Type = QSQLITE`. The log database is the
   lower-value dataset and exercises the same driver, dialect and table-creation paths.
   ⚠️ §28.4.2 shows even this can stop unit discovery — do it on a machine that is not in
   production.
5. Run Layers 2–4. Confirm schema creation server-side.
6. **Only then** consider `PMD_Type` — and note §28.4.3 suggests it may not be possible while
   `ATTACH` is in the path.

---

## 28.10 Cross-references and artefact inventory

| This Part | Relates to |
|---|---|
| §28.5.1 driver selection | Part 12.1 — dual-driver dialect abstraction |
| §28.6 connection parameters | Part 12.2 — `Verbindung` 10-QString connection struct; `SqlDb_getVerbindung` (`FUN_00525530`) |
| §28.7 Layer 3 literals | Part 11.3.2 — `SqlDb_openDatabase` (`FUN_00525700`) |
| §28.8.1 table probe | Part 11.3.2 — `SqlDb_checkTableExists` (`FUN_00526d10`) |
| §28.7 Layer 4 schema notes | Part 12 — ODBC `IDENTITY(1,1)`, `ID` column omitted on insert; `SqlBuild_insertColumnPrefix` (`FUN_00556680`), `SqlBuild_valuesPrefix` (`FUN_005565e0`) |
| §28.7 Layer 3 success form | Part 11 — `InitializeDatabase` per-unit connection fan-out |
| §28.1 measurement schema | Part 10 |

| Artefact | Detail |
|---|---|
| `qt-win-opensource-4.8.4-vs2008.exe` | 244,861,376 B · PE wrapper → NSIS-2 · LZMA:23 |
| `qsqlodbc4.dll` (release) | 89,600 B · `4.8.4.0` · `$_14_\plugins\sqldrivers\` · **deployed** |
| `qsqlodbcd4.dll` (debug) | 164,352 B · **not deployed** — release host |
| `7z.exe` + `7z.dll` | 576,000 B / 1,906,688 B · v26.02 · **required** for NSIS; `7zr.exe` insufficient |
| Deployment target | `…\CoroPlus\Provis3\sqldrivers\` |

---

# ═══════════════════════════════════════════════════════════════
# PART 29 — LIVE ACCESS, TOOLING AND OPERATING PROCEDURE
# ═══════════════════════════════════════════════════════════════

**Question this Part answers:** *how do I actually get data off this machine without breaking
anything?*

**This Part supersedes §17.1, §17.2 and §17.5.**

---

## 29.1 🔴 The four access modes, and which one to use

| Mode | Transmits | Binds a port | Safe alongside a running PROVIS3 | Sees both directions |
|---|---|---|---|---|
| **`--sniff`** (promiscuous) | **no** | **no** | ✅ **yes** | ✅ yes |
| `--replay` (offline file) | no | no | ✅ yes (offline) | ✅ yes |
| `--listen` (plain bind :1789) | no | yes | ⚠️ **only if it can bind** — may steal datagrams | answers only |
| `--master` | **yes** | yes | 🔴 **NO** | ✅ yes |

**Recommendation: `--sniff`.** This reverses §17.1.

### 29.1.1 Why sniffing beats mastering

§17.1 rejected passive operation on the ground that *"you cannot receive a unicast stream
twice"* — one of two processes gets the datagrams, and `SO_REUSEADDR` does not duplicate
unicast delivery. **That objection is true of a bound socket and false of a promiscuous
capture.** On the PROVIS3 host itself, `SIO_RCVALL` (raw promiscuous socket) or npcap sees:

- the app's **requests** (`0x500 + unit`), and
- the gateway's **answers** (`0x580 + unit`),

without binding a port, without transmitting, and without taking a single datagram away from
PROVIS3. Since the two directions carry different CAN-ID bases (§23.2), pairing them per unit
is stateless and trivial — which is exactly what the anonymous-answer problem (§3.2) requires.

**No port mirror and no SPAN is needed.** §17.1's remaining passive options (a switch mirror to
a second NIC, or asking the gateway to send to a second endpoint) are unnecessary.

### 29.1.2 The access matrix by circumstance

| PROVIS3 | Admin rights | Workable method |
|---|---|---|
| running | yes | ✅ **raw promiscuous sniff** (`SIO_RCVALL`) — passive, no interference |
| running | no | none via plain sockets. **Npcap**, if installed for non-admin use, is the only route |
| stopped | either | **master mode**: bind `:1789`, send requests, decode answers |
| stopped | either | plain `bind(:1789)` listen — binds fine but stays **silent** |

🔴 **The last row is the trap.** Closing PROVIS3 frees the port but removes **the only source of
traffic**. The device only answers; with PROVIS3 gone, nobody is asking. **Closing PROVIS3 is
necessary but not sufficient — the tool must also become the master.**

### 29.1.3 🔴 Two masters must not share the bus

PROVIS3 enforces one outstanding request per unit — **0 violations in 46,290 transactions** —
and a second asker breaks that invariant. §27.5.3 gives the mechanism; §29.4 gives the
demonstration. If master mode is used, it must be **exclusive**.

---

## 29.2 Ready-to-send request records ✅ WIRE

36-byte gateway records, byte-for-byte as captured from PROVIS3. **These are copied from live
traffic, not synthesised**, and every checksum below has been re-verified.

**Unit 1, CAN-ID `0x501`:**

| Command | 36-byte record |
|---|---|
| `0x01` STATUS | `00 24 00 80 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 05 00 00 00 00 05 01 00 00 00 01 fe 00 00 00` |
| `0x08` PLCVALUES | `00 24 00 80 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 06 00 00 00 00 05 01 00 00 00 08 01 f6 00 00` |
| `0x0E` GIVEKANAL | `00 24 00 80 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 06 00 00 00 00 05 01 00 00 00 0e 01 f0 00 00` |
| `0x12` ALARM idx 0 | `00 24 00 80 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 08 00 00 00 00 05 01 00 00 00 12 01 00 00 ec` |
| `0x16` SAMMELMERKMALE | `00 24 00 80 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 07 00 00 00 00 05 01 00 00 00 16 01 01 e7 00` |
| `0x33` PROGID | `00 24 00 80 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 06 00 00 00 00 05 01 00 00 00 33 00 cc 00 00` |

**Unit 2** is identical with `05 02` at `+0x1A` and the checksum one lower:

```
01 fd        08 01 f5        0e 01 ef        12 01 00 00 eb        16 01 01 e6        33 00 cb
```

Two further requests, emitted by the field tool and checksum-correct:

```
0x06 GIVEKONFIG   06 01 f8       0x02 GIVEGTYPE   02 fd     (no station byte — cf. §23.5.1)
```

⚠️ **One difference between the tool and the application, and it matters.** The field tool
emitted `16 01 00 e8` for `0x16` — station 1, **flag 0**. PROVIS3 emits `16 01 01 e7` — flag
**1** (§25.1.4). Both checksums are internally correct, so the tool's request is well-formed;
but a reader that sends flag 0 where the app sends 1 is not reproducing the app's behaviour and
may get a different answer. **Send `16 01 01`.**

---

## 29.3 Recommended procedure, ordered by risk

Steps 1–3 transmit nothing and cannot collide with a running PROVIS3.

### Step 0 — Preconditions

```
Gateway is 192.168.222.16, NOT .17                              (§23.1)
Run on 192.168.222.24, or answers go elsewhere                  (§23.3)
Do not connect() the UDP socket; filter on source HOST          (§23.3)
```

### Step 1 — Passive sniff (safe with PROVIS3 running)

🔴 **On Windows, use no pipe — PowerShell corrupts binary streams.** Capture to a file, then
read the file.

```
dumpcap -i <N> -f "host 192.168.222.16 and host 192.168.222.24" -w trace.pcapng
promos3_live --sniff trace.pcapng --follow --csv out.csv
```

Expect ≈ 220 records/s with two units alternating, and ~100 measurement rows/s/unit (§26.3).
Silence means the capture filter or the interface is wrong, not that the bus is idle.

### Step 2 — Decode with per-unit configuration

🔴 **Use the correct PMD file per unit** (§22.5.3) — this is not what the documented example
does:

```
promos3_reader --decode --port 1789 \
    --config-unit 1=exVL2-1.txt --config-unit 2=1974.txt
```

Better still, **skip the files**: issue one `0x0E` per unit at startup and read the feature
names from the device (§25.2.2). Then there is nothing to get wrong.

Expect unit 1 → `SPINDEL / X AXIS / Y AXIS / Z AXIS`; unit 2 → `VIBRATION / M131 DEBI /
M131BASINC / M08 DEBI`.

### Step 3 — Log to spreadsheet and correlate against the machine

```
promos3_reader --decode --port 1789 \
    --config-unit 1=exVL2-1.txt --config-unit 2=1974.txt \
    --xlsx live.xlsx --state state.bin
```

Keep **raw 0–255 values** in the output (§26.5.5). Stamp rows with the **device clock**
(§23.4.1), not the host clock.

### Step 4 — Active master, only if steps 1–3 leave a gap

Preconditions, **all mandatory**:

- local socket bound to **1789** (§23.3);
- PROVIS3 **stopped**, or pointed at a different unit;
- machine not in production;
- **never while capturing for analysis** (§29.4).

Master mode should issue `0x0D → 0x06 → 0x0E` at startup (§26.1) to learn the device record,
configuration and feature names, optionally walk the event list (`0x12` by index), then poll
`0x16 / 0x08 / 0x01 / 0x33` per unit with a 300 ms timeout and one retry — the same discipline
PROVIS3 uses. Observed app behaviour for reference: 63.7 tx/s, median gap 15.7 ms, answer
latency 1.2–5.1 ms.

### 29.3.1 Egress confirmation, if nothing arrives

Run this capture filter while `--master` executes (§23.3.1):

```
ip.src==192.168.222.24 && ip.dst==192.168.222.16
```

Empty ⇒ outbound UDP is being dropped at WFP level by endpoint security. Populated ⇒ the
ephemeral-local-port defect is the whole story.

### 29.3.2 Working display filters

```
udp.dstport==1789 && ip.src==192.168.222.16      /* the gateway → PC stream (answers) */
udp.dstport==1789 && ip.src==192.168.222.24      /* the PC → gateway stream (requests) */
data[26:2]==05:82                                /* unit 2 answers only               */
data[26:2]==05:01                                /* unit 1 requests only               */
```

⚠️ Do **not** filter on `udp.srcport==1789` for answers — the gateway sources from an ephemeral
port (§23.3).

---

## 29.4 ⭐ Two masters make a capture unparseable — demonstrated

One capture contains **7 bad checksums. All 7 fall inside the 52-second window** in which the
reader was polling in `--master` mode. **None before. None after.**

The mechanism is §27.5.3: answers carry no command byte, so a parser attributes them by *"last
request to this unit"*. With two masters that attribution is wrong for whichever answers belong
to the other one — and because the *bytes* are intact, the failure surfaces as a checksum
mismatch only when the mis-attributed request's contribution to the seed happens to differ. The
rest of the time it produces silently wrong data.

🔴 **Never run `--master` while capturing for analysis.** This is also the cleanest available
diagnostic for the hazard: **bad checksums clustered in a time window, with clean traffic either
side, means two masters.**

---

## 29.5 The corrected change list for the reader

⚠️ **None of §17.5's changes have been applied to the code in this project tree.** Verified
against the current sources. The list below **replaces** §17.5.

```
── TRANSPORT (all three of these individually cause total silence) ──────────
FIX     promos3_transport.c:19   unit = can_id & 0x00F ; base = can_id & 0xF80
                                 recognise 0x500+u (req) and 0x580+u (ans)      §23.2
FIX     socket setup             bind LOCAL port 1789; do NOT connect();
                                 accept from any source PORT, filter source HOST §23.3
FIX     gateway address          192.168.222.16, not .17                        §23.1

── FRAMING (causes messages that never complete, or complete short) ─────────
FIX     answer assembler         avail = min(DLC-1, expected-accumulated)
                                 — NOT the constant 7                           §24.1
FIX     checksum-only decision   key on the CLAMPED avail == 7,
                                 NOT on DLC == 8 and NOT on expected % 7        §24.2.1
FIX     promos3_transport.c:52   append DATA[1..avail] — the sequence byte is
                                 currently being copied into the payload
DELETE  promos3_transport.c:62   the "short frame ends the message" heuristic    §0.6 C3
DELETE  parse_message_header()   no header exists for MC_                        §0.6 C1
DELETE  reasm_expected_len()     replaced by the measured size table             §25.3
DELETE  "accept when the checksum closes" for unknown sizes — false accepts      §24.2.5

── ATTRIBUTION AND STATE ────────────────────────────────────────────────────
ADD     per-unit request tracker {command, expectedSize, sentBytes, deadline, attempts}
ADD     pair answer[u] to the most recent outstanding request[u] BEFORE decoding §24.3.1
ADD     promos3_checksum() verbatim, spanning form                               §24.3
ADD     device-error detection: DATA[0]==0 && DATA[1]==1 && LEN==2               §24.4
ADD     status codes 1 = retry / 2 = abort / 4 = incomplete
NARROW  request builder — data[1] = station applies per-command, not universally  §23.5.1
PATCH   0x16 request byte 2 = 1, not 0  (Geraet+0x688)                           §25.1.4

── DECODE ───────────────────────────────────────────────────────────────────
ADD     the measured size table; refuse to guess 0x1B and COUNT the refusal      §25.3
ADD     0x16 rows: base = payload[1]; stride 10; four (min,max) pairs + 2 status §25.1
ADD     escape handling: row[0]==0xFF only — never a Max byte                    §25.1.3
ADD     free integrity check: min > max outside an escape is a decode error      §25.1.2
ADD     feature names from 0x0E at startup; index = log2(mask & 0x0F)            §25.2.2
ADD     0x0D serial at +0x14 read BIG-ENDIAN                                     §25.2.1
DROP    polling 0x23 — 0x0E already contains it                                  §25.2.2

── OBSERVABILITY AND TOOLING ────────────────────────────────────────────────
ADD     gw_parse_record(): surface ts_low/ts_high (LOW dword first) and channel  §23.4
ADD     stamp rows with the DEVICE clock, not the host clock                     §23.4.1
ADD     --record / --replay — still the highest-value tooling item
ADD     --sniff (promiscuous, no bind, no transmit)                              §29.1
FIX     --raw must actually clear master mode (it currently does not)            §29.6.1
FIX     --port must not also change the DESTINATION port                         §29.6.1
HARDEN  can_id — 32-bit BE read at +0x18 (not a live bug for 11-bit IDs)         §23.4.5
HARDEN  honour LEN; bytes past it are stale gateway residue                      §23.4.3

KEEP    the CONF_* honesty gating — it is why the early header mistake was loud
PROMOTE MC_GIVEKONFIG (0x06) first three offsets from CONF_PROVISIONAL           §25.2.3
```

`promos3_msg_t` loses `group` / `command` as **parsed** fields and gains them as **attributed**
fields, plus a `bool attributed` that is false whenever no request was observed.

---

## 29.6 Tooling inventory

### 29.6.1 Tools built during the campaign

**`promos3_pcap.c`** — offline reader. Parses pcapng and classic pcap **without libpcap**,
pairs transactions, verifies checksums, decodes `0x16` rows, exports CSV. Options:
`--rows --raw --quiet --port --recsize --csv`.

```
gcc -std=c99 -O2 -Wall -Wextra -o promos3_pcap.exe promos3_pcap.c
```

An independent C reimplementation reproducing the Python analysis totals **exactly** — a useful
cross-check on both.

**`promos3_live.c`** — one decoder, four sources. Self-contained C11, ~1,430 lines, no
dependencies beyond sockets. Builds clean at `-Wall -Wextra -Wpedantic`, clean under
ASan/UBSan.

```
--sniff --ip <local ip>   passive promiscuous; works while PROVIS3 runs; admin
--master                  binds :1789, asks the device itself; PROVIS3 closed
--listen                  plain bind :1789; PROVIS3 closed; silent unless
                          something else is polling
--file <capture>          replay, honours pcapng timestamp resolution
```

```
gcc -std=gnu99 -O2 -Wall -Wextra -D_WIN32_WINNT=0x0601 -mconsole \
    -o promos3_live.exe promos3_live.c -lws2_32
```

Other options: `--rows --interval MS --names "A,B,C" --layout b --recsize N --gateway IP
--units 1,2 --port N --gw-port N --follow --csv`.

Sample output:

```
14:22:07  unit 1   VIBRATION 0  M131 DEBI 0..1  M131BASINC 0  M08 DEBI 37..38
                   [tail 00 20]  50 Hz  prog 0000
```

⭐ **Validated end-to-end on live production data: 26,975 measurement rows over 257 s, both
units at full rate, while PROVIS3 ran normally** — 100% of rows falling inside the capture's own
device-clock window.

### 29.6.2 Two bugs found in the campaign's own reader

🔴 **`--port` changed the destination port as well as the local bind.** Given `--port 1790` it
sent correctly-formed requests to `192.168.222.16:1790`, where nothing listens. **That is why
one CSV came out empty.** `--gw-port` is now separate and both warn if not 1789.

🔴 **The PEAK timestamp word order.** Reading `+0x0C..0x13` as one big-endian `u64` gave
`12,302,785,157,688,983,949 µs`. **The two dwords are low first, then high** (§23.4.1).

A third defect, in a different tool: **`promos3_view.exe --raw` does not disable master mode**
— the banner still read `mode: master (asks)` after `--raw` was passed. Use a
transmit-incapable binary for passive work, or fix the flag precedence.

### 29.6.3 The state of the code in this project tree

| File | Contents | State |
|---|---|---|
| `promos3.h` | shared types, transport constants, decoder-ring enums, `CONF_*` gating | present; `PROMOS3_BASE_CAN_ID 1280` is the **only** base defined — see §23.2.4 |
| `promos3_transport.c` | record split, CAN-ID routing, per-unit reassembly | 🔴 **all three transport defects present**; `:19`, `:52`, `:62` |
| `promos3_decode.c` | header parse + body decoders + printing | `parse_message_header()` still called from `promos3_transport.c:74` — **delete** |
| `promos3_proto.c` | command-name and enum lookups | present; `0x06` still `CONF_PROVISIONAL` "offsets guessed" — **may be partly promoted** (§25.2.3) |
| `promos3_config.c` / `.h` | PMD config-record parser | present and working; the cycle-record limit parse at `+0x5D` is verified (§27.4.1) |
| `promos3_state.c` / `.h` | reader state | present; **does not yet load cycles/limits** (G8) |
| `span.h`, `xlsx.c` / `.h` | byte-span helper; xlsx writer | present; xlsx flushes only on clean exit (G12) |
| `main.c` | UDP listener + `--raw` / `--decode` / `--config-unit` | binds `INADDR_ANY:1789`; **no source filter, no `--master`, no `--sniff`, no `--replay`** |
| `run_commands.txt` | build + run lines | 🔴 uses `exVL2-1.txt` for **both** units — mislabels unit 2 (§22.5.3) |

**Superseded / retired:** `promos3_learn.c` (probe harness — obsolete now the transmit path is
byte-exact), `promos3_listen.c` (assumed a clean Promos3 body per datagram),
`promos3_records.h` (superseded by `promos3_config.*`), `promos3_sniff.c` (retired, but see
§29.1 — a promiscuous capture path is now the **recommended** mode, so this may be the tool to
revive).

**Written and tested but not in this tree:** `promos3_master.h`/`.c` (the `MC_` master link
layer) and `test_master.c` (20 assertions, all passing — §18.2). ⚠️ Retrieve them or rewrite
from Parts 3, 23 and 24 — and note that anything written before the campaign will carry the
one-base and constant-7 defects.

### 29.6.4 Regression fixtures available without machine access

| Fixture | Exercises |
|---|---|
| `JULY5_IMP1.pcapng` | 2 units; commands `{0x01, 0x08, 0x33}` on the request side; 1,353 transactions; every checksum; both CAN-ID bases |
| the six-datagram set | sequence continuity; **the clamp branch**; the computed length formula; both checksum directions; a mid-answer datagram boundary; five distinct DLC values; stale bytes past `LEN` |
| `capture2today.pcapng` | 40,798 transactions; the 4 capture-drop sequence breaks; the 250-byte flush boundaries |
| `packets_july5.pcapng` | 67,018 records; the 100-row cap (1002-byte bodies); DLC distribution at scale |

**A correct reader must**: surface ≥ 2 units, recover the request commands, reassemble every
transaction, pass every checksum, and produce row counts in 3–9 for the idle captures.

**`--replay` remains the highest-value missing item in the codebase.** It converts every
remaining question from *"book a machine window"* into *"iterate at a desk"* — and the fixtures
above already exist.

---

# ═══════════════════════════════════════════════════════════════
# PART 30 — GAP REGISTER, FOURTH EDITION
# ═══════════════════════════════════════════════════════════════

**Question this Part answers:** *what is still unknown, how much does it matter, and what is the
cheapest thing that would close it?*

**This Part supersedes Part 16.** Part 16's register (G1–G13, D3–D4) is reproduced with its
field-campaign outcome; G14–G17 arrive from Part 27; G18 is new here.

⚠️ **One entry moves backwards.** G4 was closed in v3 — *"one base; master mode needs no capture
at all"* — and the wire says both halves of that were wrong. It is re-opened and re-closed on
different evidence. A register that only ever moves forward is not measuring anything.

---

## 30.1 The register at v4

| # | Gap | v3 state | **v4 state** | Blocks |
|---|---|---|---|---|
| **G1** | Message header wire layout | 100% ✅ closed by deletion | ✅ **holds.** No `MC_` header exists; the 36-byte structure is the *gateway's*, and it is now fully mapped (§23.4) — a different object entirely | no |
| **G2** | Completion rule + expected-length table | 100% ✅ | ⚠️→✅ **re-closed on corrected terms.** The rule was right in shape and wrong in two constants: `min(DLC−1, …)` not 7, and clamped-`avail` not `expected % 7` (§24.1, §24.2). Size table measured (§25.3) | no |
| **G3** | Request side / master role | 100% ✅ | ✅ **holds, and is byte-exact.** Real requests in §29.2 | no |
| **G4** | Capture strategy / CAN-ID base | 100% ✅ *(both halves wrong)* | 🔴→✅ **re-opened and re-closed.** **Two** bases, not one (§23.2); and promiscuous capture is now the *recommended* method while master mode is discouraged (§29.1). §20.17's reconciliation is withdrawn | no |
| **G5** | Checksum | 100% ✅ | ✅ **holds, both directions, 439,988 verifications** (§24.3) | no |
| **G6** | Record-layout versioning (`Geraet_getRecordVersion`, `FUN_004c5c70`) | 20% | **20%** — unchanged. One firmware version observed in the field, so the selector never branched. Still judged low value | no |
| **G7** | `MC_` (group-1) body layouts | ~65% | **~80%.** `0x16` fully decoded, `0x0D`/`0x0E`/`0x06`/`0x02`/`0x12` decoded, 16 sizes measured. `0x0D`/`0x14`/`0x29` bodies still unexamined beyond their sizes; `0x1B` unobserved | some decoding |
| **G8** | Limits loaded + the "%" display | 70% | **75%.** §26.5.5 settles the display question — the graph applies a ×1.176 transform and the wire is right — but the reader still does not load limits from the PMD record | reader completeness |
| **G9** | `channelKey` → feature index encoding | 60% | ⚠️ **split.** The *feature-mask* encoding is closed: `index = log₂(mask & 0x0F)` (§25.2.2). The `0x1B` `channelKey` proper stays open because `0x1B` was never observed | trace→feature mapping in `0x1B` only |
| **G10** | Unit ↔ serial ↔ model string | 100% ✅ | ✅ **holds and is strengthened.** Serial is big-endian at `+0x14` (§25.2.1) — four independent matches | no |
| **G11** | Device-side timestamps | 50% | ✅ **closed.** 64-bit µs counter, **low dword first**, 75 ppm, wraps every 71.6 min (§23.4.1). It is an *uptime* counter, not a wall clock — pair it with a host anchor | no |
| **G12** | Reader robustness (timeouts, counters, xlsx durability, record/replay) | 80% | **80%** — unchanged, and now the highest-value remaining engineering item. `--replay` still absent; fixtures now exist (§29.6.4) | iteration speed |
| **G13** | *(what is NOT missing)* | — | see §30.4 | — |
| **G14** | `SGrenzRec` field offsets + the limit-**write** command number | — | 🔴 **open.** Size ✅ 14 B; offsets unknown; write command ambiguous (`0x02` vs `0x28` both size-match) | config **writes** only |
| **G15** | Cross-install `Limits.ID` divergence after content-addressed resync | — | ⚠️ inferred | correlating two installs |
| **G16** | PLC bit-to-slot map — which output bit carries which `AlarmName` | — | ⚠️ inferred; the arithmetic fits | interpreting machine reaction |
| **G17** | MACHINE-side ladder semantics | — | 🔴 **out of scope.** Nothing in this project describes it | nothing here |
| **G18** | ⭐ Two sensor-type encodings that disagree | — | 🔴 **new, open.** See §30.1.1 | sensor provenance |
| **D3** | Real expected answer sizes for `0x01`, `0x12`, `0x1B` | measurement needed | ✅ **`0x01`=2, `0x12`=17** measured. 🔴 **`0x1B` still unknown** (§25.5) | `0x1B` decode |
| **D4** | The `0x08` size branch (`Geraet+0x4e6`) | measurement needed | ✅ **closed: 5** (§25.3) | no |

### 30.1.1 ⭐ G18 — the PMD file and the device disagree about the sensors

Both sources use the **same** decoder ring (§8.2), and they do not agree:

| Source | Unit 2 sensor types | Decodes as |
|---|---|---|
| PMD config file (`MiSensType[8]`) | `80 80 80 80 …` — an 8-byte run, present in **both** `1974.txt` and `exVL2-1.txt` ✅ | 4× **PROCUR-S** |
| Live `0x0D` answer, `+0x16` | `30 14 14 14` ✅ | **VBI 211** + 3× **PA 211** |

Two readings, and the report should not pretend to pick one:

1. **They are different fields.** PROCUR-S is a Prometec *transducer/interface* product; VBI 211
   and PA 211 are *sensor element* types. The PMD may record what the channel is wired through
   and the device may report what is on the end of it. Under this reading both are correct and
   `+0x16` is well named.
2. **`+0x16` is not `SensorType`.** The decoder ring fits, but a fitting decode is not a proof.

⚠️ **The evidence leans hard on (1)**: the operator independently named unit 2's feature 0
`VIBRATION`, and the byte for that channel is the one and only `0x30` — **VBI 211, a vibration
sensor**. That coincidence is not available to reading (2). It is enough to *prefer* (1) and not
enough to *close* it.

**Cheapest close:** read `Hardware` / `Channels` in the config database, which stores both, or
compare the PROCUR-S setup sheet against the device. **No machine time needed.**

Note this also narrows v3 §8.2's closing sentence — *"this box's four sensors are all `0x80` =
PROCUR-S"* — which was true of the **PMD file** and is not what the **device** says.

---

## 30.2 🔴 The critical path — two items, in order

Everything else can wait. These two cannot.

### 1. `0x1B` — the only structurally unknown message left

`0x1B` (`MC_SIGNALVERLAUF`, the signal trace) is the last message whose **size is not even
known**. It never appeared in 219,994 exchanges because PROVIS3 only requests it when a user
opens the trace view. v3's figure of 257 came from a synthetic test and is **withdrawn**
(§25.5).

**Cheapest close, costing nothing and needing no machine:**

```
findstr /i "SignalVerlauf" LogFile.txt
```

Then, if the app was ever used that way, the size follows from one capture with the trace window
open. G9's remaining half closes with it.

### 2. 🔴 Six weeks of missing measurement history

Both measurement databases stop on **2026-06-23**. The machine was cutting on **2026-08-06**.
Nothing between the two is stored (§28.2).

This outranks every protocol question in the report, because **the protocol work exists in order
to get data, and the data is currently not being kept.** A replicator built today would copy a
database that has been dead for six weeks and would look like it was working.

**Cheapest close:** find the rolled-over historic files; set `DBLimitedTo = 3`.

---

## 30.3 Open items carried from the campaign

| # | Item | State at v4 |
|---|---|---|
| **F-1** | Who is the requesting master? | ✅ **Closed.** PROVIS3 on `192.168.222.24`; the one-directional capture was a capture-point artefact, not a mirroring arrangement (§22.6) |
| **F-2** | Is `.24` an intended destination or a leftover? | ⚠️ **Open.** Read the gateway's own configuration. §22.5.2 raises the possibility that `.16`/`.17` are **two cells**, not one stale file — which would change the answer |
| **F-3** | Unit flap | ⚠️ **Open, but bounded — see §30.3.1** |
| **F-4** | 1002-byte bodies on unit 2 only | ✅ **Closed.** `0x16` at the 100-row cap: 100 × 10 + 1 = 1,001 body bytes. Not a bulk transfer (§26.3) |
| **F-5** | Size → command attribution | ✅ **Closed** by the bidirectional captures |
| **F-6** | 🔴 `.17` vs `.16` | ⚠️ **Open.** The wire is unambiguous — `.16`, in all seven captures — but *why the INI says `.17`* is not established, and §22.5.2's second-cell hypothesis means "the INI is simply stale" may be the wrong conclusion. **Affects every deployment note in this report** |
| **F-7** | Alarm code → operator text | ⚠️ **Open.** `0x12` is decoded structurally (§25.4) but the code→text table is not. `CDR_DESCRIPT_ENU.ini` (52 lines, Prometec, field-descriptor format) and the `Alarms` table are the sources |
| **F-8** | `Constraints.Alarms = 50` vs the 16-entry ring | ⚠️ **Open.** The configured alarm capacity and the observed on-device event ring do not agree. Likely two different objects — a stored history limit and a live ring — but unverified |
| **F-9** | `0x0F` ↔ `Cycles` mapping | ⚠️ **Open.** `0x0F` measures 170 bytes (§25.3); the correspondence to the `Cycles` table is untested |
| **F-10** | The error/abort ladder | ⚠️ **Open by design.** Status codes 1/2/4 are documented (§24.4) and **no device error occurred in any capture** — so the ladder has never executed. Closing it requires deliberate injection, which requires a non-production machine |
| **F-11** | NC channel down | ⚠️ **Open.** `NCMazak: connection not possible, error: −90. resetting` — TCP 57400, `NTIFDLL`. Program-name and tool-number correlation is unavailable while this is down, which is why `0x33 GIVEPROGID` returns `00 00` (§26.5.4) |
| **F-12** | `0x0D` / `0x14` / `0x29` bodies | ⚠️ **Open.** Sizes measured (66 / 36 / 40); `0x0D` partly decoded (§25.2.1); `0x14` and `0x29` unexamined |
| **F-13** | Sensor ranges from the PROCUR-S setup | ⚠️ **Open.** Would convert raw 0–255 into engineering units. Not required for monitoring — see §26.5.5, **keep raw** |

### 30.3.1 F-3 refined — the flap is an episode, not a cycle

F-d described the unit flap as a standing ~10 s cycle. Counting across the five log files in
this project says otherwise:

| Log | `…detected as not active, will be removed` |
|---|---|
| `LogFile-260701-T0545.txt` | **0** |
| `LogFile-260701-T0749.txt` | **0** |
| `LogFile-260701-T0952.txt` | **0** |
| `LogFile-260701-T1154.txt` | 2 |
| `LogFile.txt` | 23 |

All 23 events in `LogFile.txt` fall between **11:54:29 and 12:03:03 on 01.07.26** — an 8½-minute
window — inside a log that runs to **03.07.26 14:45**. The two in the T1154 file are the same
episode caught at the rotation boundary. ✅

**So the flap is a bounded ~9-minute episode on one morning, not a chronic condition.** That
matters for what it is worth investigating as: a transient (a gateway restart, a cable event, a
PROVIS3 restart storm) rather than a standing timeout misconfiguration. It also means it does
**not** explain the §28.2 six-week logging gap — wrong date, wrong duration, wrong order of
magnitude.

⚠️ Still open: what the episode was. But it has dropped several priority levels.

---

## 30.4 What is NOT missing — updated (so nobody re-does it)

v3's §16.4 list survives, with additions. **None of the following needs any further work:**

- **The wire framing.** Records, split, CAN-ID routing, sequence, clamp, checksum-only frame,
  both checksum directions. Verified at a scale (439,988 checksums) that leaves no room.
- **The request format.** Byte-exact records for six commands on two units, in §29.2.
- **The `0x16` measurement block.** Row count, stride, field order, escapes, markers, cap,
  sample rate. Four independent lines of evidence on the field order alone.
- **The gateway record.** All 36 bytes, including the clock word order.
- **Who stops the machine.** Part 27. The answer is UNIT, and PROVIS3 is not in the path.
- **Model / serial / unit identity.** G10, strengthened.
- **The measurement schema.** Part 10, plus §28.1's row counts against real files.
- **Whether the reader can be passive.** §29.1. Yes, and it should be.

⚠️ And one thing that is **not** missing but *is* wrong in the tree: none of §17.5's fixes have
been applied. See §29.5.

---

## 30.5 The method lesson

Three of the four defects that would have made a reader **silently return nothing** were
invisible to static analysis, and each was invisible in a different way:

| Defect | Why Ghidra could not see it | Cost of not knowing |
|---|---|---|
| **Two CAN-ID bases** | the second base is never a literal in the binary — it is whatever the *gateway* puts on the wire | 100% of answers discarded, no error |
| **Ephemeral source port** | a property of the peer's socket, not of any code | every reply dropped by the kernel |
| **250-byte flush** | a *device firmware* behaviour with no counterpart in the PC-side code | messages that never complete |

The fourth — the gateway address — was in a configuration file that was simply **wrong**.

The generalisable point is narrower than "capture beats decompilation," and worth stating
precisely: **static analysis recovers what one side of a conversation intends; it cannot recover
what the other side actually does.** Every one of the four is a property of the *peer* — the
gateway's CAN-ID convention, the gateway's socket, the device's flush policy, the device's
address. The binary was read correctly. It just was not the whole system.

Two corollaries earned the hard way in this campaign:

- 🔴 **Change one thing per restart.** Six INI changes at once produced a 240-error outage whose
  cause took a separate investigation to isolate (§28.4.2).
- 🔴 **Never instrument and participate at the same time.** Running the reader in master mode
  while capturing produced seven checksum failures that were not protocol failures at all
  (§29.4). The tool corrupted its own evidence.

And one that cuts the other way, in defence of the static phase: **the `CONF_*` honesty gating
is why the header mistake was loud rather than silent.** A decoder that marks its guesses as
guesses fails visibly. Keep it (§29.5).

---

# ═══════════════════════════════════════════════════════════════
# PART 31 — SUPERSESSION LOG II: WHAT THE WIRE OVERTURNED
# ═══════════════════════════════════════════════════════════════

Every claim in **this report's own Parts 0–21** — and in the eight field documents — that a
later finding overturned, narrowed, reconciled or withdrew. If you are holding v3, or any single
Appendix F, this is the list of statements in it to stop believing.

> **§0.7 is the one-line-per-item summary of this Part (entries F1–F32).** This Part is the long
> form: the same reversals with the evidence and the consequence. Where an `F`-number and a
> `31.x` number cover the same item they do not conflict — they are the short and long
> descriptions of one finding. **Part 20 (entries C1–C24) is the equivalent log for the static
> phase and is not superseded** — it is a different phase of the same investigation.

**Taxonomy.** **CORRECTION** reverses an earlier claim. **NARROWING** keeps a claim but reduces
its scope. **RECONCILIATION** merges two descriptions that were both partly right.
**RESOLUTION** closes something previously recorded as open. **WITHDRAWAL** removes a claim with
nothing replacing it — the honest outcome when the evidence turns out to have been synthetic.

## 31.0 Index

| # | Subject | Type | Ledger |
|---|---|---|---|
| 31.1 | One CAN-ID base for both directions | CORRECTION 🔴 | F1 |
| 31.2 | Seven payload bytes per frame | CORRECTION 🔴 | F2 |
| 31.3 | The gateway's source port | CORRECTION 🔴 | F3 |
| 31.4 | "17 bytes of zero padding" | RESOLUTION | F4 |
| 31.5 | The answer-direction checksum seed | RESOLUTION | F5 |
| 31.6 | The gateway address | CORRECTION 🔴 | F6 |
| 31.7 | `expected % 7 == 0` as the completion key | CORRECTION | F7 |
| 31.8 | `⌈expected/7⌉` as the frame count | WITHDRAWAL | F8 |
| 31.9 | `0x08` answers are 1 byte | CORRECTION | F9 |
| 31.10 | Three size-table misattributions | RESOLUTION | F10 |
| 31.11 | Where the `0x16` rows begin | RESOLUTION | F11 |
| 31.12 | The `0x16` row field order | RESOLUTION | F12 |
| 31.13 | `Geraet+0x688` is sent as 0 | CORRECTION | F13 |
| 31.14 | C12 — the feature names | **NARROWING** ⭐🔴 | F14 |
| 31.15 | `SGeraetRec +0x14` = `date_or_crc` | CORRECTION ⭐ | F15 |
| 31.16 | `0x1B` expects 257 bytes | WITHDRAWAL 🔴 | F16 |
| 31.17 | Master mode as the recommended posture | CORRECTION 🔴 | F17 |
| 31.18 | "A one-directional capture is worthless" | NARROWING | F18 |
| 31.19 | The 30-second test | CORRECTION | F19 |
| 31.20 | `0x23` as a command to poll | RESOLUTION | F20 |
| 31.21 | Three candidate feature-index encodings | RESOLUTION | F21 |
| 31.22 | What the `0x16` row count means | RESOLUTION | F22 |
| 31.23 | "A 3 ms polled loop" as a protocol property | RECONCILIATION | F23 |
| 31.24 | Two masters as an etiquette note | CORRECTION 🔴 | F24 |
| 31.25 | Who stops the machine | RESOLUTION ⭐ | F25 |
| 31.26 | QODBC availability | CORRECTION | F26 |
| 31.27 | `JOURNALMODE` | RECONCILIATION | F27 |
| 31.28 | Measurement history assumed live | CORRECTION 🔴 | F28 |
| 31.29 | The device-error signature | RECONCILIATION | F29 |
| 31.30 | Sequence wrap as a risk to handle | RESOLUTION | F30 |
| 31.31 | The "dead SPINDEL sensor" | WITHDRAWAL | F31 |
| 31.32 | Display values vs wire values | RESOLUTION | F32 |
| 31.33 | Three claims the field campaign made that this report rejects | — | — |

---

## 31.1 🔴 One CAN-ID base for both directions — **CORRECTION** (F1)

**Was** (§2.5; Part 20 §20.4 explicitly *corrected an earlier three-base claim down to one*):
`PROMOS3_BASE_CAN_ID = 1280` (`0x500`), one base, both directions, unit = `can_id − 1280`.

**Is:** **two** bases. `0x500 + unit` carries **requests** (PC → gateway); `0x580 + unit`
carries **answers** (gateway → PC). 194,006 records across seven captures, **zero exceptions**.

**Evidence.** Direct, and not subtle: every datagram from `192.168.222.24` carries `05 0N`, every
datagram from `192.168.222.16` carries `05 8N`, and the request bodies decode to valid command
bytes with correct checksums while the answer bodies decode to valid records. §23.2.

**Consequence, and why this is the single worst defect in the tree.**
`promos3_transport.c:19` computes `unit = can_id − 1280`, yielding **129 and 130** for the answer
frames. Line 44 discards any unit ≥ `MAX_UNITS` (16). So the reader **discards 100% of answers,
silently, with no error and no counter.** It looks like an idle bus.

Part 20 §20.4's correction was in the right direction — three bases really were wrong — and it
over-shot. **`0x580` is not a third base; it is the second half of the one that survived.**

Fix: `unit = can_id & 0x00F; base = can_id & 0xF80`.

---

## 31.2 🔴 Seven payload bytes per frame — **CORRECTION** (F2)

**Was** (§3.6): each CAN frame carries a sequence byte plus exactly 7 payload bytes.

**Is:** `avail = min(DLC − 1, expected − accumulated)`. Two things break the constant:

1. the **final** frame is short by the remainder — which §3.6 knew, in the form of a modulo rule;
2. 🔴 the **device flushes every 250 payload bytes** and emits a short frame mid-stream. Short
   frames appear at accumulated 251, 501, 751 — nowhere a `%7` rule predicts.

**Evidence.** The corrected rule reproduces **88,936 of 88,936** frame lengths. The old rule has
**11 counter-examples** in the same data. §24.1.

**Consequence.** A reader using the constant either over-reads (corrupting the tail) or waits
forever for bytes that already arrived under a different accounting.

---

## 31.3 🔴 The gateway's source port — **CORRECTION** (F3)

**Was:** not stated anywhere in Parts 0–21; the implicit model was symmetric — the gateway
answers *from* 1789 because it is answered *to* 1789.

**Is:** the gateway answers **from an ephemeral source port** that changes between sessions.
**34686** and **50375** were both observed, to a fixed destination `192.168.222.24:1789`.

**Consequence, and it is fatal.** A `connect()`ed UDP socket filters on the peer's `(host, port)`
pair. Every reply is discarded **by the kernel**, before the application sees a byte. The
application cannot log what it never receives.

**Fix:** bind local port 1789; do **not** `connect()`; filter on the source **host**. §23.3.

⚠️ Note the compound failure mode: F1, F3 and F6 each independently produce *exactly the same
symptom* — a reader that runs cleanly and reports nothing. Fixing any two of the three still
produces silence. This is why §29.5 lists all three under one banner.

---

## 31.4 "17 bytes of zero padding" — **RESOLUTION** (F4)

**Was** (§2.3): bytes `+0x04..0x14` of the 36-byte record are padding.

**Is:** an 8-byte tag at `+0x04`, a **64-bit microsecond device clock** at `+0x0C` (**low dword
first**), a channel byte at `+0x14`, DLC at `+0x15`, flags at `+0x16`. §23.4.

They read as zero in the capture that produced §2.3 because that capture contained
**application-generated** records, where the app leaves them zero. **The gateway fills them in.**
A one-sided capture of the wrong side is why this looked like padding.

This closes **G11** and provides the only trustworthy timebase in the system.

⚠️ Two traps live in this field, both found the hard way: reading the eight bytes as one
big-endian `u64` yields `12,302,785,157,688,983,949 µs` (§29.6.2), and bytes past `LEN` are
**not cleared** — they are stale residue from the previous record (§23.4.3).

---

## 31.5 The answer-direction checksum seed — **RESOLUTION** (F5)

**Was** (§16.3): the answer checksum was "assumed symmetric," verified for requests only.

**Is:** measured. `ck = −(unit + Σrequest[0..n−2] + Σanswer_payload) & 0xFF`. **439,988
verifications, zero failures.** Three alternative seedings (`unit−1`, `0`, request-only) each
scored **0 matches**, so the result is not a coincidence of a weak checksum. §24.3.

⭐ The structurally interesting part: the answer checksum **spans the request**. That is what
makes it a transaction integrity check rather than a frame check — and it is also why two
masters produce checksum failures (§31.24).

---

## 31.6 🔴 The gateway address — **CORRECTION** (F6)

**Was** (§0.2, §2.6, §17.2, and `NCaccess.ini`): `192.168.222.17`.

**Is:** `192.168.222.16`. **Zero packets** to or from `.17` in seven captures totalling 217,151
records. §23.1.

⚠️ **What is *not* established is why.** The obvious reading — the INI is stale — is
contradicted by §22.5.2: the four device serials fall into **two pairs** pointing at **two
different PMD databases**, which is consistent with a second cell existing. Recorded as open item
**F-6** in §30.3 precisely because the correction is certain and the explanation is not.

---

## 31.7 `expected % 7 == 0` as the completion key — **CORRECTION** (F7)

**Was** (§3.6): when `expected % 7 == 0`, a final frame carrying only the checksum is sent.

**Is:** the decision keys on the **clamped `avail == 7`** — i.e. on whether the *last data frame*
was full after clamping — not on `expected % 7` and **not on DLC**. §24.2.

The two rules agree whenever the 250-byte flush does not intervene, which is why the old one
survived the static phase intact. Once flushes exist, `expected % 7` is computing the wrong
quantity.

---

## 31.8 `⌈expected/7⌉` as the frame count — **WITHDRAWAL** (F8)

**Was:** implied by §3.6's worked example — a reader can predict how many frames an answer takes.

**Is:** **withdrawn. No closed form exists.** The flush boundary depends on accumulated payload,
which depends on where previous flushes fell. §24.1.

Nothing replaces it, and nothing needs to: a reader that tracks `accumulated` against `expected`
never needs a frame count. **The formula was an optimisation of a problem that does not exist.**

---

## 31.9 `0x08` answers are 1 byte — **CORRECTION** (F9)

**Was** (size table, §3.7.1): 1. Flagged as depending on the `Geraet+0x4e6` branch, recorded as
**D4**.

**Is:** **5**, consistently, on this device. §25.3. **D4 closes as a measured value**, not as a
decoded branch — the branch still exists in the binary; this device simply always takes one arm
of it.

---

## 31.10 Three size-table misattributions — **RESOLUTION** (F10)

**Was** (§3.7.1, and flagged there as doubtful): 46 at `0x10`, 170 at `0x03`, 40 at `0x0F`.

**Is:** **46 → `0x1A`, 170 → `0x0F`, 40 → `0x29`.** §25.3.

⭐ Worth recording as a small vindication of the static method: §3.7.1 **said** these looked
wrong. The suspicion was correct and the correction was simply unavailable without measurement.
A table that flags its own doubtful rows is more useful than one that does not.

---

## 31.11 Where the `0x16` rows begin — **RESOLUTION** (F11)

**Was** (§6.2): ambiguous between `Data+0x10` and `Data+0x11`.

**Is:** **payload byte 0 is the row count; rows begin at payload byte 1.** §25.1. The ambiguity
was an artefact of counting from the wrong origin — there is no `0x10`-byte header to count past,
because (per Part 20 §20.1) there is no header at all.

---

## 31.12 The `0x16` row field order — **RESOLUTION** (F12)

**Was:** stride 10 known; the meaning of the ten bytes not.

**Is:** `+0..+7` = four `(min, max)` pairs, one per feature; `+8`, `+9` = status. §25.1.

**Four independent lines**, which is why this is stated without hedging:

1. **61,764 pairs, zero inversions** of `min ≤ max`. Under any other field order this would fail
   constantly.
2. An exact **64/64 bijection** between escape rows and the rows the alternative layout would
   mis-slice.
3. ⭐ The database columns are literally named `Min_S01 … Max_S04`, in this order, in
   `WP_0000N_01` — and §28.1 shows the app stores the wire row **unmodified**.
4. The envelope **opens to 60–76% while cutting** and collapses when idle — the physical
   signature of a min/max envelope, not of four independent scalars.

**Free integrity check falling out of (1):** `min > max` outside an escape row is a decode error.
Wire it in.

---

## 31.13 `Geraet+0x688` is sent as 0 — **CORRECTION** (F13)

**Was** (§6.2, §16.3): sent as 0; meaning unknown.

**Is:** sent as **1** on this device. The live request is `00 00 00 16 01 01 e7`. §25.1.4.

⚠️ The field tool emitted `16 01 00 e8` — checksum-correct, flag **0**. Both are well-formed;
only one reproduces the application. **Send flag 1** (§29.2).

---

## 31.14 ⭐🔴 C12 — the feature names — **NARROWING** (F14)

**This entry supersedes Part 20 §20.7 and ledger entry C12.**

**Was** (C12 / §20.7): report v1 listed `SPINDEL / X AXIS / Y AXIS / Z AXIS` with masks
`0x81/82/84/88`. v2 declared this an **error** and replaced it wholesale with
`VIBRATION / M131 DEBI / M131BASINC / M08 DEBI`, masks `0x01/02/04/08`.

**Is:** 🔴 **both are real. They are two different units of the same install.** C12 was a
correct observation converted into an over-correction.

**Evidence — from files already in this project, requiring no machine access:**

| PMD file | `+0x14` serial | BE | Unit | Masks | Feature names |
|---|---|---|---|---|---|
| `exVL2-1.txt` = `exVL2-2.txt` (byte-identical) | `29 A3` | 10659 | **1** | `81 82 84 88` | `SPINDEL / X AXIS / Y AXIS / Z AXIS` |
| `1974.txt` | `29 A7` | 10663 | **2** | `01 02 04 08` | `VIBRATION / M131 DEBI / M131BASINC / M08 DEBI` |

The campaign's live `0x0E` answers confirm the same split independently, from the wire. §22.5.3.

**Consequence, and it is an active defect in the tooling:**

`run_commands.txt` and §17.6 both specify
`--config-unit 1=exVL2-1.txt --config-unit 2=exVL2-1.txt` — the **same file for both units**.
Unit 2's four channels are therefore labelled `SPINDEL / X / Y / Z` when they are actually
`VIBRATION / M131 DEBI / M131BASINC / M08 DEBI`. **The numbers are right and every label is
wrong**, which is the worst possible failure mode for a monitoring tool: the operator reads
"spindle load" and is looking at coolant flow.

Correct invocation: `--config-unit 1=exVL2-1.txt --config-unit 2=1974.txt`.

**Better still: don't use the files.** Issue one `0x0E` per unit at startup and read the names
from the device (§25.2.2). Then no file can be mismatched to a unit.

⚠️ **F-d §F.7 step 2 predicts the wrong labels** for the same reason, and should not be followed
as written.

**Method note.** This is the only entry in either supersession log where the *correction* was
more wrong than the *original claim*. The lesson is specific: when two sources disagree about a
device's configuration, **check whether they are describing the same device** before deciding one
is in error. Here the discriminating field — the serial at `+0x14` — was sitting in both files
the whole time, and was itself mis-typed as `date_or_crc` (§31.15). Two errors that concealed
each other.

---

## 31.15 ⭐ `SGeraetRec +0x14` = `date_or_crc` — **CORRECTION** (F15)

**Was** (§9.1): `date_or_crc`, marked `// INFERRED`.

**Is:** **`Serial_Num`, read BIG-ENDIAN** — inside an otherwise little-endian payload. The only
mixed-endian field known in this protocol. §25.2.1.

**Evidence — four for four, and the wrong reading is *plausible*, which is the point:**

| Bytes | BE | LE | In the runtime log? |
|---|---:|---:|---|
| `29 A3` | **10659** | 42,025 | ✅ `pmd_10659` |
| `29 A7` | **10663** | 42,793 | ✅ `pmd_10663` |
| `29 A4` | **10660** | 41,769 | ✅ `ProvisLog-10660` |
| `29 A9` | **10665** | 43,305 | ✅ `ProvisLog-10665` |

All four big-endian readings appear verbatim in `LogFile.txt` and in the database filenames. All
four little-endian readings are five-digit numbers that look entirely reasonable and correspond to
nothing.

⭐ **This is the field that resolves §31.14**, and the reason it was not used earlier is that it
was mis-typed. Recovering it converted an unresolvable disagreement between two documents into a
two-line table.

**Also corrected in the same record:** `+0x16` is `SensorType_1..4`, not `za_mi_area`. Unit 2
reads `30 14 14 14` = **VBI 211** + 3× **PA 211** against the §8.2 ring — and the operator
independently named that unit's feature 0 `VIBRATION`. ⚠️ But see **G18** (§30.1.1): the PMD file
says `0x80` PROCUR-S ×8 for the same unit, so `+0x16` and `MiSensType` are describing different
things, or one of them is not what it is labelled.

---

## 31.16 🔴 `0x1B` expects 257 bytes — **WITHDRAWAL** (F16)

**Was** (§6.1): 257.

**Is:** 🔴 **unknown.** `0x1B` was **never observed** in 219,994 exchanges, because PROVIS3 only
requests the signal trace when a user opens the trace view — and nobody did during any capture.
The figure 257 came from a **synthetic test**, not from the device. §25.5.

**Nothing replaces it.** It is the last message whose size is not even known, and closing it is
item 1 on the critical path (§30.2). It is also half of what keeps **G9** open.

⚠️ **A reader must refuse to guess `0x1B` and must count the refusal.** Accepting an unknown-size
message "when the checksum closes" produces false accepts (§24.2.5).

---

## 31.17 🔴 Master mode as the recommended posture — **CORRECTION** (F17)

**Was** (§17.1, and §20.17's reconciliation of G4): passive capture is impractical — *"you cannot
receive a unicast stream twice"* — so master mode is the recommended approach, and `promos3_sniff.c`
is not needed.

**Is:** 🔴 **reversed. Promiscuous sniffing is recommended; master mode is discouraged.** §29.1.

The original objection is **true of a bound socket and false of a promiscuous capture**.
`SIO_RCVALL` or npcap on the PROVIS3 host sees both directions without binding a port, without
transmitting, and without taking a single datagram away from PROVIS3. And because the two
directions now carry **different CAN-ID bases** (§31.1), pairing them is stateless — which
happens to solve the anonymous-answer problem (§3.2) for free.

**No SPAN port and no mirror is needed either** — §17.1's remaining passive options are
unnecessary.

Master mode is now the *discouraged* option because it transmits, because it cannot share the bus
(§31.24), and because it corrupts the very captures it is being used to produce.

⚠️ **`promos3_sniff.c` was retired on the strength of §20.17.** It may be the tool to revive
(§29.6.3).

---

## 31.18 "A one-directional capture is worthless" — **NARROWING** (F18)

**Was** (§20.17): a capture of only one direction yields nothing usable.

**Is:** **overstated.** F-d's 67,018-record one-directional capture independently yielded
liveness, framing, sequence continuity, checksums, DLC and body-size distributions, cadence, unit
identity and self-identifying constants — and its size histogram is one of the six lines that
convicts F-c of direction inversion (§22.4).

**What a one-directional capture genuinely cannot yield is the command label**, because answers
are anonymous (§3.2). That is a real and severe limitation. It is one limitation, not
worthlessness. §22.6.

---

## 31.19 The 30-second test — **CORRECTION** (F19)

**Was** (§17.2): send a request to `192.168.222.17:1789` from any socket and watch for a reply.

**Is:** wrong host (§31.6), **and** an ephemeral local port receives nothing (§31.3). Both
defects must be fixed for the test to mean anything — and the test as written fails
*identically* whether the protocol understanding is right or wrong, which makes it worse than no
test.

**Corrected form:** bind local **1789**, target **`.16`:1789**, run on `.24`, send
`00 00 00 0e 01 f0` inside the 36-byte record of §29.2.

---

## 31.20 `0x23` as a command to poll — **RESOLUTION** (F20)

**Was:** `0x23 GIVE_SENSORVALUES` listed as a command a reader should issue.

**Is:** **redundant.** `0x0E` embeds all four `0x23` records **verbatim** at `+0x14`, stride 14 —
verified 8/8. §25.2.2. Drop it from the poll loop; one fewer transaction per unit per cycle.

---

## 31.21 Three candidate feature-index encodings — **RESOLUTION** (F21)

**Was** (G9, §16.2): three plausible encodings for mapping a channel key to a feature index.

**Is:** **`index = log₂(mask & 0x0F)`.** The mask is **one-hot**, not an index. §25.2.2. The
`Alarms` table's `FeatureNr` values of 0–3 (§28.1) confirm the base is 0.

⚠️ This closes the *feature-mask* half of G9. The `0x1B` `channelKey` half stays open behind
§31.16.

---

## 31.22 What the `0x16` row count means — **RESOLUTION** (F22)

**Was:** not addressed anywhere in Parts 0–21.

**Is:** the row count is the **backlog accumulated since the previous poll**, and it **caps at
100**. §26.3.

Three consequences, all operational:

- Maximum `0x16` body is **1,001 bytes** (100 × 10 + 1) — which is what F-d's mysterious
  1002-byte bucket was (§30.3, F-4).
- The device samples at **50 Hz**, so a 2-second gap fills the cap exactly.
- 🔴 **Never poll `0x16` slower than ~2 s per unit.** Past the cap, samples are dropped **by the
  device, silently**. No error, no counter, no gap in the sequence numbering. The data simply
  never existed.

---

## 31.23 "A 3 ms polled loop" as a protocol property — **RECONCILIATION** (F23)

**Was:** described as a property of the protocol.

**Is:** **cadence is a client choice; latency is a device property.** The same application
against the same device was observed at **1.5, 15.6, 31.25 and 250 ms** intervals with **zero
errors**. Median answer latency is 1.2–6.0 ms, worst observed 9.8 ms. §26.2.

Both statements were about real observations. They were measuring different things and only one
of them constrains a reader's design.

---

## 31.24 🔴 Two masters as an etiquette note — **CORRECTION** (F24)

**Was** (§17.1): "do not poll a unit PROVIS3 is also polling" — phrased as courtesy.

**Is:** 🔴 **a correctness requirement, and it is demonstrated, not argued.**

One capture contains **7 bad checksums. All 7 fall inside the 52-second window in which the
reader was polling in master mode. None before. None after.** §29.4.

**Mechanism** (§27.5.3): answers carry no command byte, so every parser attributes them by *"the
last request I sent to this unit."* With two masters, that attribution is wrong for whichever
answers belong to the other one. Because the answer checksum **spans the request** (§31.5), a
mis-attribution sometimes shows up as a checksum failure — and **the rest of the time it produces
silently wrong data that verifies correctly.**

PROVIS3 maintains one outstanding request per unit across **46,290 transactions, 0 violations**.
That invariant is what the protocol relies on in place of a command field.

⭐ **Diagnostic worth keeping:** bad checksums clustered in a time window, with clean traffic
either side, means two masters — not a corrupted link.

---

## 31.25 ⭐ Who stops the machine — **RESOLUTION** (F25)

**Was:** never asked in Parts 0–21.

**Is:** **the UNIT does**, via a single PLC output bit. PROVIS3 is **not in the reaction path at
any point** — it configures limits and it logs, and the protection continues to function with
PROVIS3 closed. Part 27.

Two consequences that change the risk assessment of this entire project:

- ✅ **A read-only reader is not safety-relevant.** Sniffing, polling and logging cannot affect
  whether the machine stops.
- 🔴 **A reader that writes configuration is.** Limits go to the unit, and the unit acts on them
  without further reference to the PC. This is why **G14** (§30.1) is the only open gap carrying
  real physical risk.

---

## 31.26 QODBC availability — **CORRECTION** (F26)

**Was** (§12.1): the binary carries a dual-driver SQL abstraction targeting `QSQLITE` and
`QODBC`, implying ODBC is a configuration switch away.

**Is:** the abstraction is real ✅ — but `qsqlodbc4.dll` is **absent from the stock install**
(79 × *"The driver type: QODBC is not available"*), and **two SQLite-only statements sit in the
connection path**: `ATTACH` in `attachPmdDatabase`, and
`SELECT name FROM sqlite_master` in `UeberpruefeTabelle`. Part 28.

The plugin problem is solved (§28.5). The two SQLite-only statements are not, and §28.9 therefore
recommends **replicating rather than migrating**.

⚠️ Also corrected: the *cost* of experimenting. Switching `Log_Type` to `QODBC` with placeholder
credentials **stopped unit discovery entirely** — 240 driver errors, 93 `OpenDatabase() failed`,
*"No connected device"*. A database failure takes down the monitoring subsystem. The two are not
isolated (§28.4.2).

---

## 31.27 `JOURNALMODE` — **RECONCILIATION** (F27)

**Was:** this project's `PROVISsettings.ini` reads `JOURNALMODE = OFF`. The field report states
it is `ON`.

**Is:** **both are accurate, at different times.** The reference copy reads `OFF`; the value was
changed to `ON` on the target install during the campaign.

⚠️ And `ON` is **not a legal SQLite journal mode.** SQLite ignores it and falls back to the
default — which is *safer* than `OFF`, but is not what was intended and is not what anyone reading
the file would predict. Set **`WAL`** explicitly, with `SYNCMODE = 1`. §28.3.

---

## 31.28 🔴 Measurement history assumed live — **CORRECTION** (F28)

**Was:** the measurement schema was verified (Part 10) and tacitly assumed to be receiving data.

**Is:** 🔴 **both measurement databases stop on 2026-06-23.** The machine was demonstrably cutting
on **2026-08-06** — 39,000 exchanges of it were decoded. **~6 weeks of history is missing.**
§28.2.

The files sit at 7.88 and 8.35 MB against `MaxFileSize = 10`, `DBLimitedTo = 1`. Either they
rolled to historic copies, or logging stopped at the ceiling and has been discarding since.

**This outranks every protocol finding in the report.** The decoding exists in order to obtain
data; the data is currently not being retained.

---

## 31.29 The device-error signature — **RECONCILIATION** (F29)

**Was** (§0.6 C20): `DATA[0]==0 && DATA[1]==1 && LEN==2`, derived by inference.

**Is:** **retained unchanged, and still untested** — because **no device error occurred in any
capture**. §24.4. Status codes 1 = retry, 2 = abort, 4 = incomplete are documented from the
binary and have never executed on the wire.

Recorded here not as a change but because *"survived the field campaign without being exercised"*
is a materially different confidence state from *"verified,"* and the ledger should not let the
two blur. Open item **F-10** (§30.3).

---

## 31.30 Sequence wrap as a risk to handle — **RESOLUTION** (F30)

**Was:** listed as a condition a reader must handle.

**Is:** **unreachable in normal operation.** The 100-row cap (§31.22) bounds the largest answer at
~1,001 bytes ≈ 144 frames. A sequence wrap needs ~1,785. §26.4.

⚠️ Keep the wrap handling anyway — it costs three lines and the bound depends on a device-side cap
that no document guarantees. But it is not a design constraint and it should not shape the
reassembler.

---

## 31.31 The "dead SPINDEL sensor" — **WITHDRAWAL** (F31)

**Was:** an interim field report recommended investigating a suspected dead `SPINDEL` sensor,
based on a capture in which it never moved.

**Is:** ✅ **withdrawn.** It reached **255** in a later capture. The earlier operation simply did
not load the spindle. §26.5.

⭐ **The instructive part is the shape of the error, not the sensor.** A flat channel in a capture
is evidence about *the operation that was captured*, not about the sensor. Absence of variation is
not evidence of absence of function — and a maintenance recommendation was nearly issued on it.

**What is real in the same data:** `M131 DEBI` has been clipping at **255** for months. That one
is a genuine finding and it survives.

---

## 31.32 Display values vs wire values — **RESOLUTION** (F32)

**Was:** not addressed. Part 20 §20.21 had already corrected the "0–300 display axis" reading
once, in the static phase.

**Is:** the PROVIS3 graph applies a **display transform** — raw 0–255 mapped onto a 0–300 axis,
a factor of **×1.176**. §26.5.5.

⭐ **The wire and the database agree with each other. The graph is the odd one out.** A reader
comparing its own output against the PROVIS3 screen will find a consistent 17.6% discrepancy and
conclude it has a decoding error. It does not.

**Keep raw 0–255 in any export.** Do not reproduce the transform — it is a presentation choice,
not a unit conversion, and reproducing it would make the export disagree with the vendor's own
database.

---

## 31.33 Three claims the field campaign made that this report rejects

Supersession runs both ways. These are corrections **to the eight Appendix F documents**, and any
reader holding one of them individually should apply these.

### 31.33.1 🔴 F-c's direction inversion — **REJECTED**

`analysis_appendix_F__2_.md` places PROVIS3 at `.16` and the gateway at `.24`, and states that
requests ride `0x580+unit` while answers ride `0x500+unit`. **Every direction claim in that
document is inverted.** Because it swaps the IPs as well, it is *internally consistent* — nothing
inside it contradicts it, which is exactly why it needs to be refuted from outside.

Six independent lines convict it, including one built from **F-c's own numbers**: its message-size
histogram sums to **1,353**, matching the frame count on the other side, and every bucket maps to a
`0x16` row count in 3–9 — which F-e reports independently. Its seven checksum matches are real but
are *answer*-direction verifications whose terms cancel. §22.4.

⚠️ **Do not use F-c standalone for anything directional.** Its statistics are sound; its labels
are backwards.

### 31.33.2 F-a §F.7's "one unexplained observation" — **EXPLAINED**

`analysis_appendix_F_capture_validation.md` decodes the `0x501` request's command byte as `0x00`
and concludes that `0x500+n` cannot be the request channel — leaving it as an open anomaly.

It assumed a leading sequence byte. The actual framing is **three reserved zeros then the
command**, so the byte in question is `0x33` = `GIVEPROGID`. The observation was correct; the
offset was off by three. §22.4.

### 31.33.3 F-d §F.7 step 2's predicted feature labels — **WRONG**

For the reason in §31.14: it expects unit 2 to report `SPINDEL / X / Y / Z`. Unit 2 reports
`VIBRATION / M131 DEBI / M131BASINC / M08 DEBI`. Follow §29.3 step 2 instead.

---

# ═══════════════════════════════════════════════════════════════
# PART 32 — GLOSSARY ADDENDA AND ARTEFACT INVENTORY
# ═══════════════════════════════════════════════════════════════

**Part 21's glossary is not superseded.** This Part adds the terms Parts 22–31 introduce, amends
the three Part 21 entries the wire contradicted, and closes with the full inventory of every
artefact this edition draws on.

---

## 32.1 Amendments to Part 21

Three entries in §21.3 and §21.4 are now wrong as written. They are reproduced here with their
corrections rather than edited in place, so that a reader holding a printed Part 21 can find them.

| §21 entry | As written | **Amended** |
|---|---|---|
| **BaseCanIDTransfer (1280 / 0x500)** | "the CAN-ID base; `unit = CAN_ID − base`. **There is exactly one**" | 🔴 **There are two.** `0x500 + unit` = request, `0x580 + unit` = answer. `unit = can_id & 0x00F`, `base = can_id & 0xF80` (§23.2) |
| **checksum-only frame** | "a 2-byte `[seq][checksum]` frame, sent when `expectedSize % 7 == 0`" | The frame is real; the condition is wrong. It is sent when the **clamped `avail == 7`** (§24.2) |
| **PROCUR-S / -I / -B** | "…this box has 4× PROCUR-S" | True of the **PMD file**. The **device** reports `30 14 14 14` = VBI 211 + 3× PA 211 for unit 2. See **G18** (§30.1.1) |

---

## 32.2 New terms — transport and framing

| Term | Meaning |
|---|---|
| **request base / answer base** | `0x500 + unit` and `0x580 + unit`. The pair that replaces the single `BaseCanIDTransfer`. Because they differ, direction is recoverable from any single frame — which is what makes stateless pairing, and passive sniffing, work |
| **device clock** | the 64-bit microsecond counter at gateway-record `+0x0C`. ⚠️ **Low dword first, then high.** An *uptime* counter, not a wall clock: 75 ppm accurate, wraps every **71.6 minutes**. The only trustworthy timebase in the system (§23.4.1) |
| **PEAK tag** | the 8 bytes at gateway-record `+0x04`. Present in gateway-generated records, zero in application-generated ones — which is why §2.3 read the whole region as padding |
| **`LEN` residue** | ⚠️ bytes past the record's `LEN` field are **not cleared**; they are stale data from the previous record. Honour `LEN` (§23.4.3) |
| **coalescing** | the gateway packs up to **14** CAN records (504 bytes) into one UDP datagram; the application sends exactly one. 🔴 Always split a datagram on `len / 36` — never assume one record per datagram (§23.4) |
| **250-byte flush** | the device's mid-stream flush policy: after every 250 accumulated payload bytes it emits a short frame. The reason `⌈expected/7⌉` has no closed form (§24.1) |
| **clamped `avail`** | `min(DLC − 1, expected − accumulated)` — the payload actually taken from a frame, and the quantity the checksum-only decision keys on (§24.1, §24.2) |
| **spanning checksum** | `ck = −(unit + Σrequest[0..n−2] + Σanswer_payload) & 0xFF`. The answer checksum covers **the request as well as the answer**, making it a transaction check rather than a frame check — and the mechanism by which two masters produce checksum failures (§24.3, §31.24) |
| **ephemeral source port** | the gateway answers **from** a port that varies per session (34686, 50375 observed) **to** a fixed `:1789`. 🔴 Never `connect()` the socket; filter on source **host** (§23.3) |
| **attributed field** | a `promos3_msg_t` field carried over from the outstanding request rather than parsed from the wire — `group` and `command`. Paired with `bool attributed`, false when no request was observed (§29.5) |

## 32.3 New terms — measurement and operation

| Term | Meaning |
|---|---|
| **row / stride 10** | one `0x16` measurement sample: four `(min, max)` byte pairs then two status bytes. `stride = featureCount × 2 + 2` (§25.1) |
| **envelope** | the `(min, max)` pair for one feature over one sample interval. Opens to 60–76% while cutting, collapses when idle — the physical signature that settles the field order (§25.1.2) |
| **escape row** | a row whose **byte 0** is `0xFF`. 🔴 `0xFF` in a **Max** byte means saturation, not an escape — the distinction is the difference between a decoder and a corrupter (§25.1.3) |
| **markers** | escape-row subtypes: `0x00` = new cycle, `0xFB` = reset, `0xFE` = workpiece ID (§25.1.3) |
| **backlog** | the meaning of `payload[0]`: rows accumulated since the previous poll, **capped at 100** (§26.3) |
| **the 100-row cap** | the device's ceiling on a single `0x16` answer → max body **1,001 bytes**. 🔴 Poll slower than ~2 s per unit and samples are dropped **by the device, silently** (§26.3) |
| **50 Hz** | the device's measurement sample rate, derived from the backlog/interval relationship (§26.3) |
| **cadence vs latency** | ⚠️ cadence is a **client choice** (1.5–250 ms all observed, zero errors); latency is a **device property** (median 1.2–6.0 ms, worst 9.8) (§26.2) |
| **display transform** | PROVIS3's graph maps raw 0–255 onto a 0–300 axis, **×1.176**. The wire and the database agree; the graph is the odd one out. **Export raw** (§26.5.5) |
| **two-master hazard** | 🔴 two pollers on one unit. Answers are anonymous, so each master mislabels the other's answers with its own pending command. Demonstrated: 7 bad checksums, all inside one 52-second window (§27.5, §29.4) |
| **reaction path** | the chain that actually stops the machine: sensor → UNIT limit comparison → **one PLC output bit** → MACHINE ladder. **PROVIS3 is not in it** (Part 27) |
| **sniff / listen / master / replay** | the four reader postures. ✅ `--sniff` is safe alongside a running PROVIS3; ⚠️ `--listen` binds and may steal datagrams; 🔴 `--master` transmits and must be exclusive; ✅ `--replay` is offline (§29.1) |
| **the silent-listen trap** | 🔴 closing PROVIS3 frees port 1789 but removes the only source of traffic. A plain `bind()` then succeeds and receives **nothing** (§29.1.2) |

## 32.4 New terms — deployment and databases

| Term | Meaning |
|---|---|
| **build key** | the Qt 4 plugin compatibility token encoding compiler family. An MSVC host rejects a MinGW plugin outright — which is why the ODBC plugin had to be **extracted**, not built (§28.5.2) |
| **NSIS-2 payload** | the Qt installer's inner archive format. 🔴 Requires the **full** `7z.exe` + `7z.dll`; the reduced `7zr`/`7za` builds fail with *"Cannot open the file as archive"* (§28.5.4) |
| **`$_14_`** | the NSIS output-directory variable, preserved literally as a folder name inside the payload. The plugin lives at `$_14_\plugins\sqldrivers\` (§28.5.4) |
| **release vs debug plugin** | `qsqlodbc4.dll` **89,600 B** = release ✅; `qsqlodbcd4.dll` **164,352 B** = debug, rejected by a release host. 🔴 Size is the fastest discriminator (§28.5.4) |
| **the four verification layers** | 1 = ODBC stack via **32-bit** PowerShell; 2 = `QT_DEBUG_PLUGINS=1` + DebugView; 3 = the binary's own log literals; 4 = ODBC tracing. ⚠️ The **ordering** is the deliverable (§28.7) |
| **`DBLimitedTo`** | 1 = limit by file size, 3 = limit by workpiece count. 🔴 The recommended change, because it removes the ceiling implicated in the six-week gap (§28.2) |
| **replicator (vs migration)** | the recommended architecture: PROVIS3 keeps SQLite; an out-of-process copier feeds SQL Server. Needs two INI changes instead of many, and cannot take the monitoring system down (§28.9) |

## 32.5 Confidence markers — addendum to §21.5

The scale gains one level above `✅ VERIFIED`, and it is used throughout Parts 22–31.

| Marker | Meaning |
|---|---|
| **✅ WIRE** | observed on the live wire, at scale, with the count stated. The strongest claim in this report |
| ✅ VERIFIED | proven in the binary or in a file, by two independent routes |
| 🔶 GHIDRA | decompiler-derived; correct in shape, unconfirmed in constants |
| ⚠️ INFERRED | reasoned from surrounding evidence; not directly observed |
| 🔴 | a trap, a defect, or a claim withdrawn |
| ⭐ | a finding that changes what a reader should do |

⚠️ **`✅ WIRE` does not dominate `✅ VERIFIED` on every axis.** The wire shows what *this* device
did on *these* days; the binary shows what the software is *capable of*. `0x1B` is the standing
example — invisible to 219,994 exchanges and plainly present in the code. **Where the two
disagree about a constant, the wire wins. Where they disagree about existence, the binary wins.**

---

## 32.6 Artefact inventory

### 32.6.1 Source documents consolidated into this edition

**Inherited through v3** — all seven remain superseded and should not be consulted directly:

`analysis_jul_28_1_0_0.md` (v2) · `analysis_appendix_datamodel.md` (Appendix A) ·
`analysis_appendix_B.md` (Appendix B) · `analysis_part15_gap_register.md` ·
`analysis_part16_mc_answer_protocol.md` · `analysis_part17_session_handoff.md` ·
`analysis_part18_session_report.md`

**New in this edition** — the eight field documents, labelled F-a…F-h throughout:

| Label | File | Bytes | Role | Standalone caveat |
|---|---|---:|---|---|
| **F-a** | `analysis_appendix_F_capture_validation.md` | 12,391 | 6 datagrams hand-decoded | §F.7's "unexplained observation" is explained — §31.33.2 |
| **F-b** | `analysis_appendix_F__1_.md` | 27,392 | the same 6 re-parsed; CAN-ID correction; §F.13 fixtures | — |
| **F-c** | `analysis_appendix_F__2_.md` | 13,694 | `JULY5_IMP1.pcapng` | 🔴 **systematic direction inversion** — §31.33.1 |
| **F-d** | `analysis_appendix_F__3_.md` | 13,322 | `packets_july5.pcapng`, 67,018 records, one-directional | §F.7 step 2 predicts wrong feature labels — §31.33.3 |
| **F-e** | `analysis_appendix_F.md` | 19,017 | 3 pcapng files, 217,151 records | — |
| **F-f** | `PROVIS3_appendix_F_session_report.md` | 23,058 | campaign summary — **most authoritative** | — |
| **F-g** | `analysis_appendix_F_control_flow.md` | 32,065 | who stops the machine → Part 27 | — |
| **F-h** | `analysis_appendix_F_odbc_enablement.md` | 23,160 | the Qt ODBC plugin → §28.5 | — |

⚠️ Three byte-identical copies of the v3 report were supplied (md5 `9e04ce05…`, 224,244 B each)
and were deduplicated to one.

⚠️ **Document precedence, when two of the eight disagree:**
**F-f > F-e > F-b ≈ F-a > F-d > F-c.** Established in §22.3.

### 32.6.2 Packet captures

| Capture | Records | Directions | What it is good for |
|---|---:|---|---|
| `packets_july5.pcapng` | 67,018 | one | scale; DLC distribution; the 100-row cap |
| `JULY5_IMP1.pcapng` | 1,353 tx | both | ⭐ the compact regression fixture — both bases, every checksum |
| `capture2today.pcapng` | 40,798 tx | both | the 4 capture-drop sequence breaks; 250-byte flush boundaries |
| the six-datagram set | 6 | both | ⭐ the clamp branch, both checksum directions, a mid-answer boundary, 5 DLCs, `LEN` residue |
| — campaign total | **217,151** | — | 439,988 checksum verifications, 0 failures |

### 32.6.3 Device and configuration artefacts

| File | Contents | Used for |
|---|---|---|
| `1974.txt` | PMD export, 1,804 B · serial `29 A7` → **10663 = unit 2** | ⭐ §22.5.3, §31.14 — the file that settles the feature-name dispute |
| `exVL2-1.txt`, `exVL2-2.txt` | PMD export, 1,804 B · **byte-identical** · serial `29 A3` → **10659 = unit 1** | the same dispute, other side |
| `PROVISsettings.ini` | `[DatabasePMD]`, driver selection, `JOURNALMODE`, `DBLimitedTo` | Part 28 |
| `PROVISsecurity.ini`, `OLD-PROVISsecurity.ini` | access levels | §8.4 |
| `NCaccess.ini`, `OLD-NCaccess.ini`, `ALT2-NCaccess.ini` | NC channel config; **the `.17` address** | §31.6, open item F-6 |
| `CDR_DESCRIPT_ENU.ini` | 52 lines, Prometec field-descriptor format | open item F-7 — alarm code → text |
| `LogFile.txt` + 4 rotations | runtime log | ⭐ §31.15 serial confirmation; §30.3.1 the unit-flap bounding; §28.7 Layer 3 |
| `mazak_strings.txt` | extracted binary strings | address anchors throughout Parts 11–12 |
| `ProvisLog-10660`, `ProvisLog-10665` | SQLite, 15 tables, `user_version = 10` | §28.1 — and 🔴 §28.2, both stop 2026-06-23 |

⭐ **Everything needed to close G14, G16, G18 and open items F-7, F-8, F-9 is in this list.** None
of them requires machine time. That is the cheapest remaining work in the project.

### 32.6.4 Code

**In this project tree** — see §29.6.3 for the per-file state.
🔴 **None of §17.5's corrections have been applied.**

`promos3.h` · `promos3_transport.c` · `promos3_decode.c` · `promos3_proto.c` ·
`promos3_config.c/.h` · `promos3_state.c/.h` · `span.h` · `xlsx.c/.h` · `main.c` ·
`run_commands.txt` (🔴 mislabels unit 2 — §31.14)

**Built during the campaign, outside this tree:** `promos3_pcap.c` (offline, no libpcap) ·
`promos3_live.c` (~1,430 lines C11; ⭐ validated on **26,975 rows over 257 s** of live production
data while PROVIS3 ran normally)

**Written and tested, not in this tree:** `promos3_master.h/.c` · `test_master.c` (20 assertions,
all passing) — ⚠️ predate the campaign, so they carry the one-base and constant-7 defects.

**Retired:** `promos3_learn.c` · `promos3_listen.c` · `promos3_records.h` · `promos3_sniff.c`
(⚠️ retired on the strength of §20.17, which §31.17 reverses — this may be the tool to revive)

### 32.6.5 Deployment artefacts

`qt-win-opensource-4.8.4-vs2008.exe` (244,861,376 B) → `qsqlodbc4.dll` (89,600 B, `4.8.4.0`,
release) deployed to `…\CoroPlus\Provis3\sqldrivers\`. Requires full `7z.exe` + `7z.dll` v26.02.
⚠️ 4.8.6 is the **last** release offering a `vs2008` build.

---

## 32.7 What this document supersedes

**This report (v4.0) supersedes all fifteen source documents listed in §32.6.1**, and
consequently also everything v3 superseded:

> `analysis_jul_28_1_0_0.md` (v2) · `analysis_appendix_datamodel.md` (Appendix A) ·
> `analysis_appendix_B.md` (Appendix B) · `analysis_part15_gap_register.md` ·
> `analysis_part16_mc_answer_protocol.md` · `analysis_part17_session_handoff.md` ·
> `analysis_part18_session_report.md` · `PROVIS3_consolidated_report_v3.md` ·
> and the eight Appendix F documents F-a … F-h.

⚠️ **Two Parts of the inherited material are superseded *by* this edition and were retained
anyway**, because they document how the investigation moved rather than only where it arrived:

- **Part 16** (gap register) → superseded by **Part 30**;
- **§17.1, §17.2, §17.5** (access, the 30-second test, the change list) → superseded by
  **Part 29**;
- **§20.17** (the G4 reconciliation) → reversed by **§31.17**;
- **§20.7 / ledger C12** (feature names) → narrowed by **§31.14**.

Every other Part of v3 stands, with the ⚠️ FIELD callouts marking where the wire touched it.

---

## 32.8 If you read one thing

Three defects will make a reader run cleanly and return nothing, and **fixing two of the three
still returns nothing**:

```
1.  unit = can_id & 0x00F ;  base = can_id & 0xF80      §23.2   (answers are 0x580+unit)
2.  bind LOCAL 1789 ; do NOT connect() ; filter by HOST §23.3   (gateway sources ephemeral)
3.  the gateway is 192.168.222.16, not .17              §23.1   (the INI is wrong)
```

Then `avail = min(DLC−1, expected−accumulated)` — never the constant 7 (§24.1) — and
`--sniff`, never `--master`, alongside a running PROVIS3 (§29.1).

And before building anything on the stored history: **check whether it is still being written.**
It stopped on 2026-06-23 (§28.2).

---

*End of consolidated report, v4.0.*

*Fifteen source documents · 217,151 captured records · 439,988 checksum verifications ·
32 field corrections · 18 gaps, 11 closed.*

---

# ═══════════════════════════════════════════════════════════════
# PART 33 — CAPTURE 1: FIRST LIVE VERIFICATION
# ═══════════════════════════════════════════════════════════════

> **Provenance and numbering.** Originally circulated as **"Part 19 — Live Capture
> Verification"**. The ⟦MEAS⟧ edition renumbered it to *its* Part 22 (because that edition
> already had a Part 19, Data sources) and rewrote its internal section numbers from `19.x`
> to `22.x`. **This edition renumbers it again to Part 33 / `33.x`**, so it does not collide
> with ⟦FIELD⟧'s Part 22 (the campaign evidence base). Cross-references have been remapped
> throughout; nothing else in the text has been altered.
>
> This Part is a **merge of the ⟦MEAS⟧ and ⟦CAP1⟧ narratives of the same capture**. Where the
> two editions word a finding differently, both are kept and tagged.
>
> ⚠️ **§33.6's "seven payload bytes per frame" is superseded** — see ⚖️ X7 in the front matter,
> §D.2 (Part 35) and §24.1 (Part 24).

## 33.0 ⟦CAP1⟧ The capture, as the one-capture edition framed it

*⟦CAP1⟧ opened its edition's Part 22 with this framing. It is kept here, demoted, because it
states plainly what a single capture could and could not establish.*

**Artefact:** 4,039 packets, 21.24 s, Ethernet, ns resolution.
**Relevant traffic:** 3,745 UDP packets → **5,622 gateway records** → **1,353 complete
request/answer transactions** across 2 units.

**Verdict: the analysis is confirmed, with one hard correction and three measured values.**

This is the first two-directional artefact in the project, so it is the first thing that could
test the *pairing* model (§3.2) that everything else rests on. **It holds.**

> **How to read this Part.** It is the original measurement report, preserved substantially
> as written so that the evidence stays separable from the analysis it validates. Its findings
> have already been threaded back into Parts 0–21 with ⚠️/⭐ markers and into the correction
> ledger as **C25–C33** (§0.6, §0.7) and the supersession log as **§20.32–§20.40**. Nothing here
> is new relative to those; this is where the numbers live.

---

**Source artefact:** `JULY5_IMP1.pcapng` — the project's **first** two-directional capture, and
therefore the first artefact able to test the pairing model (§3.2) that the entire architecture
rests on. It holds.

**Artefact:** 4,039 packets, 21.24 s, Ethernet, ns resolution.
**Relevant traffic:** 3,745 UDP packets → **5,622 gateway records** → **1,353 complete
request/answer transactions** across 2 units.
**Verdict: the analysis is confirmed, with one hard correction and three measured values.**

This is the first two-directional artefact in the project, so it tests the *pairing* model
(§3.2 — answers carry no command) that everything else rests on. It holds.

## 33.1 Endpoints — the INI is stale

| | capture | `PROVISsettings.ini` |
|---|---|---|
| PROVIS3 host | `192.168.222.24`, bound **:1789** | — |
| Gateway | `192.168.222.16`, ephemeral src **:50375** | `GatewayAddress = 192.168.222.17` |
| Port | 1789 both ways ✅ | `GatewayPort = 1789` ✅ |

<!--var-->
**⟦CAP1 — variant⟧**

The gateway is **`.16`, not `.17`**. Either the INI copy in the project predates a re-address or
it belongs to a different cell. **The §17.2 "30-second test" datagram must be sent to
`192.168.222.16:1789`, not `.17`.** Direction is not assumed — it is proven by content
(§33.2 / §33.3).

<!--var-->
**⟦MEAS — variant⟧**

The gateway is **.16, not .17**. Either the INI copy in the project predates a re-address or it
belongs to a different cell. **The §17.2 / §36.5.1 "30-second test" datagram must be sent to
`192.168.222.16:1789`, not `.17`.** Direction is not assumed — it is proven by content
(§33.2/22.3).

## 33.2 Record framing — exact ✅

All 5,622 records are 36 bytes; no datagram had a non-multiple length.

| field | predicted | observed |
|---|---|---|
| `0x00–03` | `00 24 00 80` | `00 24 00 80` on **100%** of records, **both directions** |
| `0x15` | CAN dlc | 2–8 |
| `0x16–19` | zero | zero on 100% |
| `0x1A–1B` | CAN-ID big-endian | ✅ |
| `0x1C–23` | DATA | ✅ |

<!--var-->
**⟦CAP1 — variant⟧**

The Part 18 §3.1 guess that *"received records also start `00 24 00 80`, which would confirm
symmetry for free"* — **collected**. RX and TX records are structurally identical.

<!--var-->
**⟦CAP1 — variant⟧**

**App→gateway records:** bytes `0x04–0x14` all zero, exactly as `FUN_00504290` builds them.

<!--var-->
**⟦CAP1 — variant⟧**

**Gateway→app records:** zero except a **64-bit big-endian microsecond counter at `0x0C`
(low dword) / `0x10` (high dword)**, plus `0x14 = 0`. Over the capture it advances 21.245927 s
against 21.244336 s of pcap wall time — **ratio 1.000075**. It is a real, usable gateway
timestamp with ~75 ppm drift and about **19.04 days of uptime** at capture start. Part 2.2 called
`gw_header[0x15]` "timestamp/status (discarded)" — correct, and now decodable if wanted (it is
far better than pcap arrival time for jitter analysis, since answer frames arrive batched).

<!--var-->
**⟦MEAS — variant⟧**

The v3 §2.3 guess that *"received records also start `00 24 00 80`, which would confirm
symmetry for free"* — **collected**. RX and TX records are structurally identical.

<!--var-->
**⟦MEAS — variant⟧**

**App→gateway records:** bytes `0x04–0x14` all zero, exactly as `FUN_00504290` builds them.
**Gateway→app records:** zero except a **64-bit big-endian microsecond counter at `0x0C`
(low dword) / `0x10` (high dword)**, plus `0x14 = 0`. Over the capture it advances 21.245927 s
against 21.244336 s of pcap wall time — **ratio 1.000075**. It is a real, usable gateway
timestamp with ~75 ppm drift and about **22.04 days of uptime** at capture start. Section §2.2 called
`gw_header[0x15]` "timestamp/status (discarded)" — correct, and now decodable if wanted
(it is far better than pcap arrival time for jitter analysis, since answer frames arrive batched).

**Batching, newly visible:** the app sends **one record per datagram, always** (1,353/1,353).
The gateway **batches an entire multi-frame answer into a single datagram** — up to 14 records
(504 bytes) observed. A reader that assumes one record per datagram loses ~64% of the frames.

## 33.3 CAN-ID — ⚠️ **CORRECTION to §2.5 / §0.6 C4** (→ ledger C25)

*⟦CAP1⟧ titles this same section* **"CAN-ID — ⚠️ CORRECTION to Part 18 §3.3"** *— the same
correction, cited in the standalone-document numbering of §0.0.3 Layer 1.*

```
requests  (app → gateway) : 0x501, 0x502          = 0x500 + unit   ✅ BaseCanIDTransfer 1280
answers   (gateway → app) : 0x581, 0x582          = 0x580 + unit   ⚠️ NOT 1280
```

<!--var-->
**⟦CAP1 — variant⟧**

Only four IDs appear in the whole capture, cleanly split by direction. Part 18 concluded *"One
base, not three… whatever `0x580`/`0x600` are, they are not transmit bases."* That is **true and
irrelevant**: `0x580` is not a *transmit* base, it is the **answer/receive** base. `this+0x48`
being a single field was read correctly; it only ever governs the direction that function sends.

<!--var-->
**⟦MEAS — variant⟧**

Only four IDs appear in the whole capture, cleanly split by direction. v3 §2.5 concluded *"One
base, not three… whatever `0x580`/`0x600` are, they are not transmit bases."* That is **true and
irrelevant**: `0x580` is not a *transmit* base, it is the **answer/receive** base. `this+0x48`
being a single field was read correctly; it only ever governs the direction that function sends.

**Impact on the code as it stands:**

```c
/* promos3_transport.c:19 */
out->unit = (int)out->can_id - PROMOS3_BASE_CAN_ID;   /* 0x581 - 1280 = 129 */
```

Every answer frame currently resolves to unit **129/130**, is rejected against `MAX_UNITS 16`,
and the reader decodes **nothing**. This is the one bug in the capture that was fatal rather than
cosmetic. Fix:

```c
#define PROMOS3_BASE_CAN_REQ  0x500   /* 1280 — app → device */
#define PROMOS3_BASE_CAN_ANS  0x580   /* 1408 — device → app */
/* direction is unambiguous from the ID itself: id >= 0x580 → answer */
```

The upside: **answers are not as anonymous as §3.2 feared.** The unit is on the wire, and so is
the direction. Pairing still requires both directions (the *command* really is absent), but a
listener can now demultiplex units and separate request from answer without any heuristics.

## 33.4 Request format — byte-exact ✅

Every one of the 1,353 requests:

```
[00][00][00][cmd][params…][ck]      LEN = 3 + payload,  single frame
```

The three reserved bytes are zero on 100% of requests — Part 18's "purpose unexplained" stands,
but they are at least stable. No request needed a continuation frame (all payloads ≤ 4 bytes,
as predicted). Observed requests, all four commands, both units:

| request | cmd | meaning |
|---|---|---|
| `00 00 00 16 01 01 e7` / `…e6` | `0x16` | GIVESAMMELMERKMALE, station 1, param 1 |
| `00 00 00 08 01 f6` / `…f5` | `0x08` | GIVEPLCVALUES, station 1 |
| `00 00 00 01 fe` / `…fd` | `0x01` | GIVESTATUS, no params |
| `00 00 00 33 00 cc` / `…cb` | `0x33` | GIVEPROGID, param 0 |

<!--var-->
**⟦CAP1 — variant⟧**

`08 01 f6` is **byte-identical to `LogFile-260701-T1154`** and to the synthetic frame in Part 18
§3.2. The Part 16 §16.3 open question — *"is `params[0]` the channel or the station?"* — is now
closed **the other way from a pure guess**: unit 2 is addressed as `0x502` and still sends
`params[0] = 0x01`. The parameter does **not** track the unit. It is the station, as Part 17
concluded from `FUN_004d0320`. ✅

<!--var-->
**⟦MEAS — variant⟧**

`08 01 f6` is **byte-identical to `LogFile-260701-T1154`** and to the synthetic frame in Part 18
§3.2. The §0.6 C15 open question — *"is `params[0]` the channel or the station?"* — is now
closed **the other way from a pure guess**: unit 2 is addressed as `0x502` and still sends
`params[0] = 0x01`. The parameter does **not** track the unit. It is the station, as §3.3
concluded from `FUN_004d0320`. ✅

## 33.5 Checksum — the spanning form verified in the answer direction ✅

```
ck = -( unit + Σ request[0 .. n-2] + Σ answer_payload )   (mod 256)
```

| test | result |
|---|---|
| request checksum (`-(unit + Σ params)`) | **1,353 / 1,353** ✅ |
| answer checksum, spanning both directions | **1,352 / 1,352** ✅ (1 truncated at capture end) |

<!--var-->
**⟦CAP1 — variant⟧**

The Part 18 §10 caveat *"answer-direction checksum seed assumed symmetric with the request
(verified for requests only)"* — **the assumption was right, and it is now measured.** Note what
this proves about the model: the answer checksum cannot be validated without the request bytes,
which is independent confirmation that the two directions are one transaction.

<!--var-->
**⟦MEAS — variant⟧**

The v3 §3.5.3 caveat *"answer-direction checksum seed assumed symmetric with the request
(verified for requests only)"* — **the assumption was right, and it is now measured.** Note what
this proves about the model: the answer checksum cannot be validated without the request bytes,
which is independent confirmation that the two directions are one transaction.

Handy equivalent form for the reader: `ck_answer = (ck_request − Σ answer_payload) & 0xFF`.

## 33.6 Framing and completion rule ✅

- Answer frames are `[seq][≤7 payload]`, seq from `0x00`, **0 sequence errors in 4,269 frames**.
- 7 payload bytes per frame, exactly as specified.
- Message = `expected` bytes then the checksum byte; no `[seq][ck]`-only frame occurred in this
  window (no message length hit `expected % 7 == 0`), so that branch remains untested.
- `expected` counts the message **excluding** the checksum byte — confirmed against the `0x16`
  formula below.

### `cmd 0x16` variable length — the formula is exact ✅

`expected = DATA[1] × recordSize + 1`, with **recordSize = 10**:

| count | 3 | 4 | 5 | 6 | 7 | 8 | 9 |
|---|---|---|---|---|---|---|---|
| messages | 6 | 36 | 90 | 134 | 75 | 17 | 5 |

<!--var-->
**⟦CAP1 — variant⟧**

**363 / 363 messages satisfy `len = count × 10 + 1` with remainder 0.** And `recordSize = 10` is
`featureCount × 2 + 2` for **featureCount = 4** — the four PROCUR-S sensors, arrived at
independently from the wire. Part 17 §8's stride formula is confirmed on real bytes.

<!--var-->
**⟦MEAS — variant⟧**

**363 / 363 messages satisfy `len = count × 10 + 1` with remainder 0.** And `recordSize = 10`
is `featureCount × 2 + 2` for **featureCount = 4** — the four PROCUR-S sensors, arrived at
independently from the wire. §6.2's stride formula is confirmed on real bytes.

## 33.7 Measured answer sizes — closes part of D3/D4, and finds a table error

<!--var-->
**⟦CAP1 — variant⟧**

| cmd | name | measured `expected` | Part 17 table said |
|---|---|---|---|
| `0x01` | GIVESTATUS | **2** | not in table (Part 18: "a guess") |
| `0x08` | GIVEPLCVALUES | **5** | **1** ⚠️ |
| `0x33` | GIVEPROGID | **2** | not in table |
| `0x16` | GIVESAMMELMERKMALE | `count×10 + 1` | formula ✅ |

<!--var-->
**⟦MEAS — variant⟧**

| cmd | name | measured `expected` | v3 size table said |
|---|---|---|---|
| `0x01` | GIVESTATUS | **2** | not in table (v3 §0.5 D3: "a guess") |
| `0x08` | GIVEPLCVALUES | **5** | **1** ⚠️ |
| `0x33` | GIVEPROGID | **2** | not in table |
| `0x16` | GIVESAMMELMERKMALE | `count×10 + 1` | formula ✅ |

`0x08` is the important one. The table entry (`0x08, 0x09, 0x0c → 1`, "every SET returns a 1-byte
ack") gives **1**; the device sends **5**. This is exactly the D4 branch:

```c
else n = (Geraet[0x4e6] >> 4) + (Geraet[0x4e6] & 0x0F);      /* version 0xE5 → this branch */
```

So `Geraet+0x4e6` is **nonzero** and its nibbles sum to **5** on this box (`0x41`, `0x14`, `0x23`,
`0x32`, `0x05`, `0x50` all fit). D4 is resolved *as a value* — 5 — without needing to know which
nibble is which. A reader hardcoding 1 for `0x08` would time out on every poll, ~16 times a
second.

## 33.8 Poll cadence, arbitration, health

- **1,353 transactions in 21.2 s = 63.7 tx/s.** Median inter-transaction gap **15.7 ms**, p95
  16.7 ms, max 125 ms.
- Per-unit cycle observed: `0x16 → 0x08 → 0x01 → 0x33`, interleaved between units 1 and 2 — the
  §3.10 cadence, minus the second `0x16`, plus `0x33`. Command mix over the capture:
  `0x16` 363, `0x08` 342, `0x33` 341, `0x01` 307.
- **One outstanding request per unit: 0 violations in 1,353.** `Interface_setLastSentPaket`'s
  enforcement is real and visible.
- Answer latency **1.2–5.1 ms**, against `unitAnswerTimeout = 300`. Two orders of margin.
- **0 retries, 0 timeouts, 0 device-error frames** (`DATA[0]==0 && DATA[1]==1`, len 2). The
  §3.8 concern that a healthy first data frame is indistinguishable from an error answer is
  untested here — but note `0x16` answers begin `00 03…` through `00 09…`, i.e. `DATA[1]` is the
  row count, and a 1-row block **would** produce `00 01` on a len-8 frame. The `len == 2`
  constraint is what saves it. Keep it.
- The single answerless transaction is the last request in the file. Capture truncation, not a
  fault.

## 33.9 What the capture does **not** give you

Be clear-eyed about this: **the machine was idle for all 21 seconds.**

- Unit 2: **1,058 of 1,058** measurement rows are all-zero.
- Unit 1: all 1,064 rows are near-constant — `00 00 00|01 00|01 00 00 26 26 00 20`, i.e. one
  feature pair parked at 0x26/0x25 (38/37) and one byte-pair toggling 0/1.
- **Zero `0xFF` escape bytes.** No new-cycle marker, no workpiece ID, no `0xFB` reset, no alarm.
- `0x01` GIVESTATUS returned `00 00` and `0x33` GIVEPROGID returned `00 00` on **every single
  poll**, both units. No program loaded, nothing running.
- Only 4 of the 38 group-1 commands appear. No `0x1b` GIVESIGNALVERLAUF (the live trace), no
  `0x0e` GIVEKANAL, no config or handshake traffic — that happened before the capture started.

So: **the link layer is now fully verified and the body layer is not.** The `0x16` row is 10
bytes with 4 feature slots; which two bytes are the trailing `+2` and which pair belongs to which
feature cannot be settled from a row that never moves. The two candidate splits
(`[f0..f3][extra2]` vs `[extra2][f0..f3]`) both parse this data.

**Also measured, and useful:** rows arrive at **50.1 /s (unit 1)** and **49.8 /s (unit 2)** — the
device's feature sample rate is **50 Hz**, and the app's `0x16` poll rate floats to match
(count 3–9 per poll). That is a real number for sizing buffers and for the xlsx writer.

## 33.10 Scoreboard delta

| Gap | v3 | Now | Basis |
|---|---|---|---|
| G1 header layout | 100% | 100% ✅ | held — no header on the wire |
| G2 completion rule | 100% | 100% ✅ | 363/363 on the `0x16` formula, 0 seq errors |
| G3 request side | 100% | 100% ✅ | byte-identical to prediction |
| G4 ID base / capture | 100% | **corrected** ⚠️ | answer base `0x580`; reader bug found |
| G5 checksum | 100% | 100% ✅ | now verified in the answer direction too |
| G7 MC_ body layouts | ~65% | ~65% | idle capture — no movement possible |
| G11 device timestamps | 50% | **80%** | gateway µs counter decoded at `0x0C`/`0x10` |
| D3 sizes | guesses | **3 measured** | `0x01`=2, `0x08`=5, `0x33`=2 |
| D4 `0x08` branch | unknown | **resolved: 5** | table said 1 |

## 33.11 Next actions, in order

1. **Patch `promos3_transport.c`** — split the CAN-ID base by direction (§33.3). Without this
   nothing else matters.
2. **Patch the size table** — `0x08 → 5`, add `0x01 → 2`, `0x33 → 2`, `0x16 → count×10+1`.
3. **Handle batched datagrams** — split every datagram into `len/36` records before decoding.
4. **Point the §17.2 probe at `192.168.222.16`**, not `.17`.
5. **Ask for a second capture *while the machine is cutting*** — same length is fine, 20–30 s.
   That single artefact is now the only thing standing between the reader and G7: it would show
   the `0xFF` escapes, a cycle boundary, a workpiece ID, moving feature values, and probably
   `0x1b`. Everything at the link layer is done; the remaining unknowns are all body semantics,
   and body semantics need a machine that is doing something.

<!--common-->
**⟦MEAS — added⟧**

*End of Part 19.*

## 33.12 What to ask for in the second capture

**⟦CAP1 — section present only in the 1-capture edition⟧**


Written out explicitly, because the first capture succeeded technically and still missed G7 —
purely because of *when* it was taken. The artefact is cheap; the machine window is not.

| Requirement | Why |
|---|---|
| **20–30 s, machine actually cutting** — a full workpiece cycle from start to end if possible | The only way to see `0xFF` escapes, a cycle boundary and a workpiece ID (§6.2) |
| **Both directions**, as before | Non-negotiable — answers are unpairable without requests (§3.2) |
| **A trace view open in PROVIS3 during capture** | Forces `0x1b GIVESIGNALVERLAUF`, which closes G9 and the `0x1B` half of D3 (§6.1) |
| **Provoke one alarm if safely possible** (or capture during a known limit crossing) | The only way to get an `MC_` alarm body, which is still `MC3_`-derived and PROVISIONAL (§6.4, G7) |
| **Restart PROVIS3 while capturing**, if a maintenance window allows | Catches unit registration: `0x02 GIVEGTYPE`, `0x06 GIVEKONFIG`, `0x0e GIVEKANAL` — three more measured sizes plus the handshake (§3.9, §17.3) |
| **Note the wall-clock start time** | Lets the gateway µs clock (§33.2) be anchored to real time |
| **Same host, same cell** | So `.16` vs `.17` and the CAN-ID bases can be confirmed as stable rather than incidental |

**Expected yield:** G7 from ~65% → ~90%, G9 closed, G11 closed, D3 fully closed. That is every
remaining item on the register except G6 (record-layout versioning, judged low value) and G8
(limit loading, which is reader engineering rather than reverse engineering).

---

*End of Part 33.*

---

*End of consolidated report (v4).*

*This document supersedes: `promos3_protocol_map.md` (v1), `PROVIS3_architecture.md` (v1),
`analysis_jul_28_1_0_0.md` (v2), `analysis_appendix_datamodel.md` (Appendix A),
`analysis_appendix_B.md` (Appendix B), `analysis_part15_gap_register.md`,
`analysis_part16_mc_answer_protocol.md`, `analysis_part17_session_handoff.md`,
`analysis_part18_session_report.md`, `PROVIS3_consolidated_report_v3.md`, and
`analysis_part19_capture_verification.md`.*

⚠️ *Two documents referenced by the project — `analysis_appendix_C_wire_capture.md` and
`analysis_appendix_D_poll_loop_capture.md` — were not available when this edition was assembled
and are therefore **not** merged. If they surface, reconcile them against Part 33 and against the
correction ledger entries C25–C33; nothing in this report depends on them, but they may contain
measurements this edition does not.*

# ═══════════════════════════════════════════════════════════════
# PART 34 — CAPTURE 2: BREADTH  (Appendix C)
# ═══════════════════════════════════════════════════════════════

> **Originally circulated as "Part 22 / Appendix C: Live Wire Capture Validation"** (renumbered
> to Part 23 by the ⟦MEAS⟧ edition, and to **Part 34** here). Its
> internal `C.x` section numbers are **kept unchanged**, because Part 35 cites them heavily
> (`§C.7.1`, `§C.15` …) and renumbering would break those references. Cite sections of this
> Part as **§C.n**. Cross-references to the pre-capture report have been remapped to this
> edition's numbering; nothing else in the text has been altered.
>
> ⚠️ Where this Part writes **"v3 §x"** it means *§x of Parts 0–21 as originally written, before
> the captures*. Those section numbers are unchanged in this edition, so the reference resolves —
> but the section it points at now carries a correction banner pointing back here.


**Addendum to `PROVIS3_consolidated_report_v3.md` (v3.0).**
**Status: this Part supersedes parts of the body of v3. See §C.3 and the ledger in §C.14.**

**Question this Part answers:** *the consolidated report was produced with "no Wireshark, no packet
capture, and no live machine access." A capture now exists. Which of ~99% of recovered protocol
knowledge survives contact with real bytes — and which does not?*

**Source artefact:** `ALL_merged__uniq.pcapng` — 3,397 packets distilled from **286,373** frames
across five captures of PROVIS3 PC `192.168.222.24` ⇄ CAN gateway `192.168.222.16`, one example of
every distinct request/answer exchange observed. Decoded here into **8,800 gateway records**
(250 requests, 8,550 answer frames), 396 exchanges, 250 distinct request kinds, units 1 and 2.

**Method.** The pcapng was parsed byte-for-byte with a purpose-written reader (no tshark), records
split at the 36-byte stride, and every structural claim in Parts 2–3 of the consolidated report
re-tested as a *predicate over all 8,800 records* rather than spot-checked. Where a rule is
reported below as holding, it holds with **zero counter-examples** unless a count is given.

Confidence markers are the report's own: ✅ VERIFIED, 🔶 GHIDRA, ⚠️ INFERRED, 🔴 trap.

---

## C.0 Headline

> **The reverse engineering was right about the protocol and wrong about the wire.**
>
> Every framing rule recovered from Ghidra — sequence bytes, 7 payload bytes per frame, the
> checksum algorithm in *both* directions, the checksum-only frame, the `0x16` length formula, the
> `ceil(n/7)` frame count — is confirmed exactly, most of them across all 250 exchanges with no
> exceptions. That is an unusually clean result for static analysis.
>
> But **three of the four facts a reader needs to receive a single byte are wrong in v3**: the
> answer CAN-ID base, the gateway's UDP source port, and the "17 bytes of zero padding" in the
> gateway record. A reader built strictly to v3 binds the right port and then discards 100% of
> traffic — silently, with no error. All three are fixed below.
>
> Separately, the capture supplies both items v3 correctly identified as *unrecoverable from the
> binary*: **D3 and D4 are closed with measured numbers**, and the answer-direction checksum — v3's
> one flagged "open assumption" — is closed at 248/248.

| Measure | v3 | After this capture |
|---|---|---|
| Protocol *knowledge* | ≈99% | **≈99.5%** (D3, D4 closed; body layouts still the gap) |
| Live *reader* correct end to end | ≈75% | **≈90%** (all blocking wire facts now measured) |
| `MC_` answer sizes known from real bytes | 2 of 38 | **16 of 38** |
| `MC_` body layouts decoded | 2 of 38 | **8 of 38** |

---

## C.1 Provenance and the limits of this artefact

Stated up front, because two findings below are artefacts of the capture rather than the protocol.

The file is a **deduplicated merge**. The poll loop resends the same handful of requests thousands
of times; grouping was done into complete request/answer exchanges and only the first example of
each distinct kind kept. Consequences a reader of this Part must hold on to:

1. **Adjacency is synthetic.** Two frames next to each other in the file were not necessarily next
   to each other on the wire. Nothing in §C.12 (timing) is derived from packet adjacency — all
   timing comes from the gateway's own hardware timestamp (§C.4), which the merge preserves.
2. **Two exchanges are cut.** One `0x16` answer is truncated at 64 of the 143 frames its own
   length field demands. It is excluded from the checksum statistics, and identified as truncated
   *by* the length rule (§C.10.2), which is itself a small confirmation of that rule.
3. **146 of 396 exchanges have no request in the file.** This is a dedup artefact, not a protocol
   event — but it turned out to be a useful natural experiment (§C.13).

⚠️ **This capture is probably not the box the report describes.** The gateway is `192.168.222.16`;
`PROVISsettings.ini` says `.17`. The device record (§C.10.5) carries unit identifiers of 10660 and
10665 where the report's cell has SNr 10659 and 10663. Everything structural matches exactly —
same firmware `0xE5`, same `GType 0x44`, same `GSubType 5`, same `ReduzLim 6612`, same `CDRLim
0xAA×4`, same 4×`0x80` sensors — so this is the *same model and configuration*, very likely a
sister cell. Treat identifiers as installation-specific; treat structure as general.

---

## C.2 What the capture confirms

The following were recovered from disassembly alone and are now proven against real bytes. Listed
because the report's method — "cross-confirmation wherever possible" — earned this, and because
knowing which parts are load-bearing matters when the rest is being revised.

| Claim (v3 §) | Test | Result |
|---|---|---|
| Gateway record is 36 bytes (§0.2) | 8,800 records, every datagram an exact multiple of 36 | ✅ 0 exceptions |
| Record begins `00 24 00 80` (§2.3) | all 8,800 records, **both directions** | ✅ 0 exceptions — closes the "worth cross-checking that received records also start `00 24 00 80`" note in §2.3 |
| DLC at `+0x15` (§0.2) | consistent with payload length in all records | ✅ |
| CAN-ID big-endian (§0.2) | ✅ — but read it as 32-bit at `+0x18`, see §C.4 | ✅ / ⚠️ |
| `unit = CAN-ID − base`, units 1–15 (§0.2) | units 1 and 2 only, both directions | ✅ |
| Request = `[cmd][station][params…][ck]` (§3.3) | 250 requests | ✅ 0 exceptions |
| Request first frame is `[00][00][00]` + payload (§3.4) | 250 requests | ✅ (length rule refined, §C.7) |
| Request checksum `−(unit + Σ)` (§3.5) | 250 of 250 | ✅ 0 exceptions |
| Answer `DATA[0]` = seq from 0, +1/frame (§3.6) | all attributed exchanges | ✅ 0 exceptions |
| 7 payload bytes per frame (§3.6) | frame count = `ceil(n/7)` in all 250 | ✅ 0 exceptions |
| Checksum-only frame iff `size % 7 == 0` (§3.6) | 10 exchanges `%7==0` → all have one; 240 `%7≠0` → none do | ✅ **perfect partition, 0 exceptions** |
| `0x16` length = `DATA[1] × recSize + 1` (§3.7) | `recSize = 10 = 4 features×2 + 2`; holds on both units | ✅ |
| Payload little-endian (§0.2) | `ReduzLim` reads 6612 LE, 54297 BE | ✅ |
| **No header on the `MC_` wire** (§20.1) | `GIVEKONFIG` body starts `E5 01 04` at payload offset **0** | ✅ see below |
| Answers carry no command/group (§3.2) | 146 unattributed answers are unidentifiable (§C.13) | ✅ confirmed the hard way |

**The `E5 01 04` anchor.** the gap register (§16.5) predicted that one capture would close G1 "(header
offsets, anchored on `E5 01 04`)". The anchor is here — `GIVEKONFIG` (`0x06`) answers with
`e5 01 04 04 04 00 04 fa fc 07 08 32 08 fa`, i.e. **version 229, 1 channel, 4 sensors** exactly as
the runtime log prints them — and it sits at payload offset **0**, with nothing in front of it.
G1's closure *by deletion* is correct.

---

## C.3 What the capture overturns

Three corrections, all in the transport layer, all blocking.

### 🔴 C.3.1 — There are **two** CAN-ID bases. Requests `0x500`, answers `0x580`.

**v3 says** (§0.2 fact 2, §2.5, ledger C4, §20.4): *"**One** base, not three… Transmit and receive
use the same base… `0x580` and `0x600` are stored in the constructor but are **not** transmit
bases; their purpose is unknown. **G4 closed as a consequence.**"*

**The wire says:**

| direction | CAN-IDs observed | records |
|---|---|---|
| PC → gateway (requests) | `0x501`, `0x502` | 250 |
| gateway → PC (answers) | `0x581`, `0x582` | 8,550 |

Zero answers on `0x500+unit`. Zero requests on `0x580+unit`. The split is total across 8,800
records.

**Reconciliation — v3 is half right, and the half it got right is the half it was reasoning
about.** `Promos3CanInterface::send` really does compute `CAN-ID = BaseCanIDTransfer(1280) + unit`,
and the settings dialog really does expose one "Base Tx" field. Both statements are about
**transmit**, and both are confirmed. The error was the inference that *receive* therefore shares
that base — `send` cannot testify about the receive direction, and nothing else was consulted.
**`0x580` is the answer base. Its purpose is no longer unknown.**

This restores, in the receive direction only, the claim made in the session handoff and struck by
the session report (Part 20 §20.4) — the original reading of `0x580` as a direction discriminator was correct; the error
was calling it a *transmit* base and calling three bases where there are two. `0x600` remains
unobserved and unexplained.

🔴 **Severity.** A reader implementing v3 §0.2 computes `unit = 0x581 − 1280 = 129`, which is
outside the valid range 1–15, and drops the frame. It drops **every answer it will ever receive**,
reports zero errors, and looks like a network problem. This single line is the difference between
a working reader and one that cannot be debugged.

```c
/* correct */
#define CANID_BASE_TX  0x500   /* PC  -> gateway : requests */
#define CANID_BASE_RX  0x580   /* gateway -> PC  : answers  */
/* unit = id & 0x7F ;  is_answer = (id & 0x580) == 0x580 */
```

### 🔴 C.3.2 — The gateway answers from an **ephemeral** source port, never 1789.

**v3 says** (§0.2, §17.2): transport is UDP `:1789`; the 30-second test sends to
`192.168.222.17:1789`. Nothing in v3 addresses the *source* port of the answer.

**The wire says:**

| flow | source | destination | datagrams |
|---|---|---|---|
| requests | `192.168.222.24:`**`1789`** | `192.168.222.16:1789` | 250 |
| answers | `192.168.222.16:`**`34686`** | `192.168.222.24:1789` | 1,620 |
| answers | `192.168.222.16:`**`50375`** | `192.168.222.24:1789` | 893 |

The PC sends *from* 1789 *to* 1789. The gateway replies from a high port that **differs between
sessions** (two distinct values across the five captures). It never sources from 1789.

🔴 **Severity.** Sending the §17.2 test datagram from a **connected** UDP socket — the natural way
to write it, and what `connect()` + `send()` gives you — makes the kernel drop every reply, because
the reply's source port does not match the connected peer. The tool sees nothing and the operator
concludes the device did not answer. §17.2's *"If anything comes back, everything else follows. If
nothing does, that is a real result"* is exactly the wrong inference to draw under this bug.

```c
/* bind :1789, do NOT connect(); accept datagrams from any source port on the gateway host */
bind(fd, {INADDR_ANY, 1789});
recvfrom(fd, buf, sizeof buf, 0, &from, &flen);
if (((struct sockaddr_in*)&from)->sin_addr.s_addr != gateway_ip) continue;  /* filter on HOST */
```

⚠️ Note also `[Ethernet] LastPort=1799` and `LastUsedPort` 1793 in the reference INI (v3 ledger
C24, §21.4). Those are PROVIS3's own persisted values and do not match either port seen here.
Filter on **host**, never on port.

### C.3.3 — The "17 bytes of zero padding" is a timestamp, a tag and a channel.

**v3 says** (§2.2 / §2.3): `0x00-01` length; `0x02-03` constant `00 80`; **`0x04-14` — 17 bytes of zero
padding**; `0x15` LEN; `0x16-19` zero; `0x1A-1B` CAN-ID BE; `0x1C-23` data.

**The wire says** those bytes are not padding on the answer path. They are zero only on the
*request* path, because the PC does not fill them. On answers, `+0x0C..0x13` carries a **64-bit
big-endian microsecond timestamp** written by the gateway. Full map in §C.4.

The record is, field for field, the **PEAK PCAN-Ethernet Gateway** UDP frame format. Recognising
that is worth more than the individual fields: it means the transport is a documented,
off-the-shelf, vendor-standard container, not a Prometec invention, and a reader can be written
against the vendor spec with confidence about the cases this capture does not contain (29-bit IDs,
RTR frames, error frames, multi-channel gateways).

---

## C.4 The gateway record — corrected field map ✅

36 bytes, big-endian throughout the container. Verified across 8,800 records.

```
off   size  field                         observed
0x00   2    length (BE)                   0x0024 = 36        — constant, 8800/8800
0x02   2    message type (BE)             0x0080 = CAN frame — constant, 8800/8800
0x04   8    tag / client handle           all zero (both directions)
0x0C   8    timestamp (BE, microseconds)  answers: monotonic; requests: zero
0x14   1    CAN channel                   0 — constant
0x15   1    DLC                           2..8
0x16   1    flags                         0 — constant (no RTR / no extended / no error frame)
0x17   1    reserved                      0 — constant
0x18   4    CAN-ID (BE, 32-bit)           0x00000501/0502 requests, 0x581/0582 answers
0x1C   8    DATA[0..7]                    DLC bytes significant, remainder zero
```

⚠️ v3's `CAN-ID big-endian at +0x1A..0x1B` is the **low half** of the 32-bit field at `+0x18`. It
reads correctly for 11-bit identifiers and would silently truncate a 29-bit extended identifier.
This installation only ever uses 11-bit IDs, so the v3 reader is not wrong *here* — but read the
full dword; it costs nothing.

### C.4.1 The timestamp is real, and it is the device clock ✅

Not inferred — measured against the capture's own nanosecond timestamps over the full file:

| | value |
|---|---|
| capture wall-clock span | 3,836.6723 s |
| gateway timestamp span | 3,836.7047 s (as microseconds) |
| drift | **+8.5 ppm** |
| monotonic under BE | 8,305 / 8,549 adjacent pairs (breaks are merge reordering) |
| monotonic under LE | 3,032 / 8,549 → **byte order is BE, decisively** |
| value at first frame | 1,643,471 s ≈ **19.02 days** — gateway uptime, not epoch |

**This closes a large part of G11 for free.** v3 §16.2 records G11 (device-side timestamps) at 50%,
with the note *"reader still uses host clock"* and the warning that *"under load, host-clock
stamping will misorder events against the machine's own log."* Every answer frame arrives already
stamped by the gateway's own hardware clock at microsecond resolution. A reader should key
ordering on `+0x0C` and use the host clock only to anchor the epoch once per session.

⚠️ It is an **uptime counter, not a date**. It is monotonic and drift-free enough to order events
and measure intervals; it cannot date them without an anchor. The low word wraps every 71.6 minutes
— visible in this capture as the high word stepping 382 → 383 — so a reader must use the full 64
bits and not just `+0x0C..0x0F`.

---

## C.5 UDP framing behaviour

| property | observed | consequence for a reader |
|---|---|---|
| records per **request** datagram | always exactly 1 | — |
| records per **answer** datagram | 1 to **15** | 🔴 must loop over records; must not assume 1 |
| largest answer datagram | **540 bytes** (15 × 36) | receive buffer ≥ 1500; 540 is the observed max, not a spec limit |
| distribution | 2,017 × 1 record; 447 × 2; 131 × 15; rest spread | batching is opportunistic, not fixed |

v3's `Scan4CANmsg` front-trim behaviour (§16.4 G13, verified) already handles this correctly. It is
recorded here because the 15-record burst is the case that breaks a naïve `recv()` → `parse one
record` loop, and it occurs 131 times in a 3,397-packet file.

---

## C.6 Request framing — confirmed and refined ✅

All 250 requests are single-frame. **No multi-frame request appears in this capture.**

```
DATA[0..2] = 00 00 00          (always; the "reserved 3 bytes" of §3.2)
DATA[3]    = command
DATA[4..]  = arguments
DATA[n-1]  = checksum
DLC        = 3 + payload_length
```

| DLC | payload (`[cmd][args][ck]`) | count |
|---:|---:|---:|
| 5 | 2 | 14 |
| 6 | 3 | 19 |
| 7 | 4 | 184 |
| 8 | 5 | 33 |

⚠️ **Refinement to §3.4.** v3 states the first frame is *"`[00][00][00][ 5 payload bytes ]` LEN =
8"*. That is the maximum case, not the rule. The rule is **`LEN = 3 + min(5, payloadLen)`** — a
short request produces a short first frame, and `LEN` is 5, 6, 7 or 8. A reader that always emits
`LEN = 8` and zero-pads will corrupt the checksum, because the padding bytes are inside the summed
range.

⚠️ **`0x0C SETZYKLUS` is absent from this capture**, so the multi-frame request continuation rule
(`[seq][7 payload]`, §3.4) remains 🔶 GHIDRA — code-derived, still unverified on the wire. It is
the one request-side rule this artefact does not test. v3 §20.5's correction (requests *are* split
like answers; the log dumper caps at 8 bytes) is untouched by this capture, neither confirmed nor
denied.

---

## C.7 Answer framing — confirmed ✅

```
DATA[0]         = sequence, 0,1,2,… (+1 per frame, wraps at 256)
DATA[1..LEN-2]  = payload, 7 per full frame
DATA[LEN-1]     = checksum, final frame only, only if it fits
```

**Frame-count predicate, tested on all 250 attributed exchanges:**

```
frames == ceil(expected / 7) + (expected % 7 == 0 ? 1 : 0)
```

**0 violations.** The worked example in v3 §3.6 — `0x0E GIVEKANAL`, 144 bytes, 21 frames — is
observed exactly: 21 frames, 20 × `LEN=8` then `LEN=6`, no checksum-only frame because
`144 % 7 = 4`.

### C.7.1 The checksum-only frame — perfect partition ✅

| `expected % 7` | exchanges | trailing frame |
|---|---:|---|
| `== 0` | 10 | **`LEN=2`, `[seq][checksum]`** — all 10 |
| `!= 0` | 240 | checksum inline as `DATA[LEN-1]` — all 240 |

Zero exchanges on the wrong side. Both `%7==0` commands here answer 14 bytes: `0x06 GIVEKONFIG`
and `0x23 GIVE_SENSORVALUES`. 🔴 v3's warning stands and is now measured: *a reader that does not
implement the checksum-only frame will treat 4% of its exchanges as truncated* — and they will be
two of the most useful commands on the box.

### C.7.2 The `LEN==2` ambiguity is safely resolved by `DATA[0]` ✅

v3 ledger C20 insists the device-error signature is `DATA[0]==0 && DATA[1]==1 && **LEN==2**` and
that the `LEN==2` part "is not optional". The capture shows why the *other* discriminator is the
load-bearing one:

- 21 `LEN==2` answer frames occur.
- **All 10 checksum-only frames carry `DATA[0] = 2`.** None carries `DATA[0] = 0`.
- **0 device-error answers** occur in this capture.

So `LEN==2` alone does **not** separate the two — a checksum-only frame is also `LEN==2`. The
separator is `DATA[0]`: an error answer is sequence 0 (it is a whole message), a checksum-only
frame is the *last* frame of a multi-frame answer and its sequence is therefore ≥ 1. This matches
the decompiled guard `frame2[5]==2 && frame2[6]!=0` exactly, and it means a reader keying only on
`DATA[1]==1` will misread roughly 1 in 256 checksum-only frames as a device error.

---

## C.8 The checksum — closed in **both** directions ✅

v3 §3.5.3 carries the project's last open protocol assumption:

> ⚠️ **Open assumption:** the answer-direction seed is assumed symmetric with the request. It is
> verified for requests only.

**Closed.** Applying the recovered formula verbatim to the answer direction:

```c
checksum = −( unit + Σ request_bytes[0 .. n−2] + Σ answer_payload ) & 0xFF
```

| direction | result |
|---|---:|
| requests (250) | **250 ok, 0 bad** |
| answers (248 assessable) | **248 ok, 0 bad** |

The two excluded exchanges are the capture artefacts of §C.1 and are discussed in §C.10.2 — one is
truncated; the other is a mis-pairing that the checksum itself detected and repaired.

**Three alternative seedings were tested against all 250 answers and every one scored 0:**

| hypothesis | ok / 250 |
|---|---:|
| omit the unit seed | 0 |
| unit seed but ignore the request bytes | 0 |
| include the request's own trailing checksum | 0 |

The recovered formula is therefore not merely consistent with the data — it is the *only* one of
the plausible variants that is. Both `sent_n − 1` (exclude the request's own checksum) and the unit
seed are independently required by the bytes. G5 is closed at 100% in both directions.

---

## C.9 Measured answer sizes — **D3 and D4 are closed** ✅

v3 §0.5 identifies two items as "**device runtime state** — not recoverable from the binary at any
effort". Both are now measured. Sizes below are **payload bytes excluding the checksum**, i.e.
exactly the `expectedSize` a reader stamps into `Paket+0x14`. Identical on units 1 and 2 in every
case.

| cmd | name | **measured** | v3 size table | verdict |
|---|---|---:|---:|---|
| `0x01` | `GIVESTATUS` | **2** | *(absent)* | **D3 closed** |
| `0x02` | `GIVEGTYPE` | **3** | 14 | 🔴 **table wrong** |
| `0x05` | `GIVEUSEDZYKTAB` | **32** | 16 | 🔴 **table wrong** |
| `0x06` | `GIVEKONFIG` | **14** | *(absent)* | new |
| `0x08` | `GIVEPLCVALUES` | **5** | 1 | 🔴 **D4 closed; table wrong** |
| `0x0D` | *(unnamed)* | **66** | *(absent)* | new — and identified, §C.10.5 |
| `0x0E` | `GIVEKANAL` | **144** | **144** | ✅ **exact agreement** |
| `0x0F` | `GIVEZYKLUS` | **170** | 40 | 🔴 **table wrong** |
| `0x12` | `GIVEALARM` | **17** | *(guessed 2 via `0x11`)* | **D3 closed** |
| `0x14` | *(unnamed)* | **36** | *(0x24 fallback)* | ✅ consistent with the `0x24` retry |
| `0x16` | `GIVESAMMELMERKMALE` | **`n×10 + 1`** | *(formula)* | ✅ **formula confirmed** |
| `0x1A` | `GIVEHARDWAREREC` | **46** | *(46 listed at `0x10`)* | ✅ **⚠️ resolved** |
| `0x23` | `GIVE_SENSORVALUES` | **14** | *(absent)* | new |
| `0x25` | `GIVE_ACTZYKINDEX` | **3** | *(absent)* | new |
| `0x29` | *(unnamed)* | **40** | *(absent)* | new |
| `0x33` | `GIVEPROGID` | **2** | *(absent)* | new |

`0x1B GIVESIGNALVERLAUF` **does not appear in this capture** — the live amplitude trace was not
being requested during any of the five sessions. Its size remains the synthetic guess of 257 and is
the single most valuable measurement still outstanding.

### C.9.1 What this does to `Geraet_expectedRecordSize`

v3 §3.7.1 flags three entries that "do not align with the recovered command names" and suggests
"some entries are keyed by **record type** rather than by command". The measurements make that
concrete and considerably worse:

- `0x0E → 144` is the **only** table entry that measurement confirms.
- `0x0F` is tabled at 40 but answers **170** — and 170 is the `SZykRecV4802` size that the table
  parks at `0x03 SETANZMODE`, the entry v3 called "⚠️ odd for a SET command". The 170 is real; it
  is filed under the wrong key.
- `0x1A` answers **46** — the `SHardwareRec` size the table parks at `0x10`. v3's "⚠️ but
  `GIVEHARDWAREREC` is `0x1a`, not `0x10`" is resolved in favour of the command name.
- `0x08` is tabled at 1 (ack) but answers **5**. `0x02` is tabled at 14 but answers **3**.

🔴 **Recommendation: do not carry the table into the reader.** Use §C.9's measured column for the
16 commands measured, and the `0x16` formula for `0x16`. Treat any unmeasured entry as unknown and
let the exchange time out rather than mis-terminate — a timeout is a loud failure, a wrong
`expectedSize` is a silent one that consumes the *next* answer's frames (the exact corruption §18.1
case C reproduced).

### C.9.2 D4 — the `0x08` branch, pinned

v3 §0.5 D4:

```c
if (version < 0xD6 || Geraet[0x4e6] == 0)
     n = base + (GType=='D'||'H' ? 1 : 0) + (traceMapNode(station)==4 ? 1 : 0);
else n = (Geraet[0x4e6] >> 4) + (Geraet[0x4e6] & 0x0F);
```

Version is `0xE5` ≥ `0xD6`, so the nibble branch governs iff `Geraet+0x4e6 ≠ 0`. Measured
`n = 5`, on both units, so:

```
(Geraet[0x4e6] >> 4) + (Geraet[0x4e6] & 0x0F) == 5
  → Geraet[0x4e6] ∈ { 0x05, 0x14, 0x23, 0x32, 0x41, 0x50 }
```

⚠️ The config byte itself is still not directly observed. But **a reader does not need it** — it
needs `n`, and `n = 5` is now measured. D4 is closed for implementation purposes; it remains open
only as a curiosity about which of six values the config carries.

Observed body: `00 00 00 00 ff` on both units.

---

## C.10 Newly decoded bodies

Six command bodies not previously seen, plus two confirmations. This takes `MC_` body coverage from
2 of 38 to 8 of 38 and directly advances **G7**.

### C.10.1 `0x06 GIVEKONFIG` — 14 bytes ✅

```
e5 01 04 04 04 00 04 fa fc 07 08 32 08 fa
^^ ^^ ^^
|  |  +-- sensors  = 4
|  +----- channels = 1
+-------- version  = 229 (0xE5)
```

Byte-identical on units 1 and 2, and identical to the runtime log's
`bearbeite_Kom_06_MC_GIVEKONFIG: Version 229 Channels 1 Sensors 4`. **Three fields ✅ VERIFIED at
offsets 0, 1, 2.** The remaining 11 bytes (`04 04 00 04 fa fc 07 08 32 08 fa`) are stable across
both units and undecoded.

### C.10.2 `0x16 GIVESAMMELMERKMALE` — the length formula, confirmed ✅

| unit | args | `DATA[1]` = n | payload | `n×10 + 1` | |
|---:|---|---:|---:|---:|---|
| 1 | `01 01` | 7 | 71 | 71 | ✅ |
| 2 | `01 01` | 6 | 61 | 61 | ✅ |
| 1 | `01 00` | 100 | 446 | **1001** | truncated by the merge (64 of 143 frames) |

`recordSize = 10` is exactly `featureCount × 2 + 2 = 4×2+2`, confirming the stride rule of v3 §6.2
/ §6.2 on real data, and confirming that `Paket+0x34` is loaded with 10 on this box.

The third row is the capture artefact of §C.1 — and note that **the length rule is what identifies
it as truncated**. That is the rule doing exactly the job a reader needs it for.

### C.10.3 `0x0E GIVEKANAL` — 144 bytes; **feature names and the mask encoding** ✅

The 144-byte `SKanalRecV40` contains a block of four **12-byte feature descriptors** beginning at
body offset **`0x4D`**:

```
+0x4D + 12k :  [mask:1][name:11, NUL-padded ASCII]      k = 0..3
```

| k | unit 1 mask | unit 1 name | unit 2 mask | unit 2 name |
|---:|---:|---|---:|---|
| 0 | `0x81` | `SPINDEL` | `0x01` | `VIBRATION` |
| 1 | `0x82` | `X AXIS` | `0x02` | `M131 DEBI` |
| 2 | `0x84` | `Y AXIS` | `0x04` | `M131BASINC` |
| 3 | `0x88` | `Z AXIS` | `0x08` | `M08 DEBI` |

Two results here.

**First, `mask & 0x0F` ∈ {1, 2, 4, 8} — a one-hot bit, not an index.** The feature index is
`log2(mask & 0x0F)`. This confirms v3 §17.5's patch instruction *"feature-name loading: read from
`SKanalRec`, match on `mask & 0x0F`"* against real bytes, and it is the encoding **G9** has been
waiting for. G9 (`channelKey` → feature index) moves from 60% to ~90%: the descriptor side is
proven; only the request-side `channelKey` for `0x1B` remains untested, because `0x1B` is absent.

**Second — these are the report's own labels.** v3 §16.2 warns that this box's features are
*"operator-assigned Turkish/German shop labels (`VIBRATION / M131 DEBI / M131BASINC / M08 DEBI`)"*
and that a wrong index base *"mislabels every plotted bar… and a wrong label looks plausible"*.
Unit 2's descriptor block is that exact list, in that exact order, bound to masks 1/2/4/8. **The
labelling risk is retired for this installation.** Unit 1 carries a different set entirely
(`SPINDEL`, `X AXIS`, `Y AXIS`, `Z AXIS`) with the high bit set — a second reason never to
hard-code names.

⚠️ Bit `0x80` is set on all four of unit 1's masks and none of unit 2's. Most likely an
enable/active or sensor-vs-feature flag. Unexplained; do not include it in the index computation.

`CDRLim` also confirms: body `+0x10` reads `aa aa aa aa` on both units — the `0xAA (170) ×4` of
v3 §21.4. ✅

### C.10.4 `0x12 GIVEALARM` — 17 bytes; **the device timestamp, decoded** ✅

Requested as `[0x12][station][index][00]`, where `index` walks `0x00`–`0x0F`: a **16-entry ring of
stored alarms**. Body layout, from a census of all 33 captured alarm records:

```
+0x00  slot      (15 in every record captured)
+0x01  alarm code
+0x02..0x09  parameters (channel, feature, limit, …) — undecoded
+0x0A  day     observed 1..31
+0x0B  month   observed 1..12
+0x0C  year    observed 19..25   (+2000)
+0x0D  hour    observed 0..19
+0x0E  minute  observed 0..59
+0x0F  second  observed 0..59
+0x10  0
```

The field ranges settle the ambiguity: `+0x0A` reaches 31 and `+0x0B` never exceeds 12, so the
order is **day, month, year** — not year-first. Decoded, the ring reads as a clean chronological
history, which is itself a check on the decode:

| index | code | decoded |
|---:|---:|---|
| `0x00` | 253 | 2019-11-29 11:10:00 |
| `0x02` | 12 | 2020-07-24 09:05:13 |
| `0x05` | 27 | 2020-07-24 12:52:42 |
| `0x07` | 12 | 2021-04-06 17:37:34 |
| `0x09` | 36 | 2022-01-12 15:10:04 |
| `0x0E` | 10 | 2025-10-31 11:11:56 |
| `0x0F` | 0 | all-zero — empty slot |

Monotonically increasing with ring index, ending in an empty slot. **This is the `QDateTime` that
`FUN_00626960` reads** (v3 §16.2 G11) and it is the source for `Alarms.Date`. Together with §C.4.1
this takes **G11 from 50% to ~90%**: sub-second ordering from the gateway timestamp, wall-clock
dating from the alarm record.

⚠️ Century is assumed. The field carries `19`–`25`; `+2000` is the only sane reading but is not
proven by these bytes.

### C.10.5 `0x0D` — 66 bytes; this is **`SGeraetRec`** 🔶

v3 §5.2 lists `0x0D` as *(unnamed)*, handler `FUN_0040aa40`, "sets the selected monitor if the
station is unknown". Its answer is 66 bytes — and v3 §15.7 records `Geraet+0x4BA` as
"`SGeraetRec` begins (**66 bytes**, copied wholesale)", with `+0x4BA GeraetTyp`, `+0x4BB GSubType`,
`+0x4BC CHANNEL count`, `+0x4BD sensor count`.

Measured body, unit 1:

```
44 05 01 04 00 00 00 01 00 …  29 a4 …  80 80 80 80 80 80 80 80  01 00 00 00  d4 19 …  41
^^ ^^ ^^ ^^                                ^^ 8 × sensor type                  ^^^^^ ReduzLim
```

| body offset | value | matches |
|---|---|---|
| `+0x00` | `0x44` | `GeraetTyp` — the MSL-16 family ✅ |
| `+0x01` | `5` | `GSubType` → `MSL5081-16` ✅ |
| `+0x02` | `1` | channel count ✅ |
| `+0x03` | `4` | sensor count ✅ |
| `+0x1A..0x21` | `80` ×8 | sensor-type slots — `0x80` = **PROCUR-S** ✅ |
| `+0x26` | `6612` LE | **`ReduzLim` = `0x19D4`** ✅ — v3 §21.4 exactly |

Six independent field matches against values the report derived from a completely different source
(the PMD export `1974.txt` and the binary). **`0x0D` is `MC_GIVEGERAETEREC` (or equivalent), and it
is the single most useful discovery command on the box** — one 66-byte answer identifies model,
topology, sensor complement and limits. It also re-confirms the little-endian payload rule at
`ReduzLim`.

⚠️ A `u16` at `+0x14` reads 10660 (unit 1) and 10665 (unit 2) big-endian — the right magnitude for
the serial numbers, but not equal to the report's 10659/10663 (§C.1: probably a different cell).
**The serials 10659/10663 appear nowhere in this capture in any byte order**, so `GIVEGTYPE` is not
their source and v3 §16.2 G10's *"serial arrives via the GIVEGTYPE/registerUnit path"* is not
supported here. Field identity at `+0x14` is ⚠️ INFERRED and needs one confirmed pairing.

### C.10.6 `0x02 GIVEGTYPE` — 3 bytes ✅

```
44 05 01     GeraetTyp 0x44 · GSubType 5 · 0x01
```

Identical on both units. Confirms the model-resolution inputs of v3 §8.6 (`GSubType 5`, 1-based →
`MSL5081-16`). Note there is **no serial number** — the answer is 3 bytes, and 14 (the tabled size)
would be needed to carry one.

### C.10.7 Short bodies, recorded for completeness

| cmd | args | body |
|---|---|---|
| `0x01 GIVESTATUS` | — | `00 00` |
| `0x33 GIVEPROGID` | `00` | `00 00` |
| `0x25 GIVE_ACTZYKINDEX` | `01` | `00 00 00` |
| `0x05 GIVEUSEDZYKTAB` | `01` | `ff ff ff ff 0f` + 26 × `00` + `fc` |
| `0x14` *(unnamed)* | — | 36 × `00` |
| `0x29` *(unnamed)* | — | 40 × `00` |
| `0x0F GIVEZYKLUS` | `01 00` | 170 bytes — `SZykRecV4802`, cycle 0 unconfigured |

⚠️ The machine was idle for most of the captured window: `GIVESTATUS`, `GIVEPROGID` and
`GIVE_ACTZYKINDEX` all read zero, and `0x14`/`0x29` are entirely zero. **Their sizes are trustworthy;
their contents say nothing about field layout.** Do not infer "this field is always zero" from
these.

`0x23 GIVE_SENSORVALUES` (14 bytes) is the exception — it carries live data, and its `args` is the
round-robin sensor slot (`Geraet+0x60`): unit 1 walks 4–7, unit 2 walks 0–3. Unit 2's bodies open
with `0x80` and `0x81` — **PROCUR-S and PROCUR-I** (v3 §21.4), so the sensor-type byte is at body
offset 0. 🔶

---

## C.11 Timing — measured

All from the gateway's own timestamp (§C.4.1), so unaffected by the merge.

| quantity | value |
|---|---|
| request → first answer frame, median | **1.2 – 4.7 ms** depending on command |
| request → first answer frame, worst observed | **13.5 ms** (`0x0F`, 181 samples) |
| inter-frame gap within one answer, median | **178 µs** (p10 154, p90 200) |
| implied device frame rate | ≈ 5,600 frames/s |

**Implications.**

- `[CAN] unitAnswerTimeout = 300` is ~22× the worst latency observed. A reader can use a far
  tighter deadline; 50 ms would be conservative and would fail 22× faster during bring-up.
- A long answer costs `frames × 178 µs`. The 143-frame `0x16` full block ≈ **25 ms** — still well
  inside 300 ms, but a reader must arm its deadline on the **last frame received**, not on the
  request, or long answers will time out spuriously.
- v3 §0.2's "3 ms polling loop" is consistent: median service time is 1–5 ms, so the loop is
  request-bound, not idle-bound.

---

## C.12 Attribution without a request — a **negative** result

The 146 unpaired exchanges (§C.1) are an accidental but exact simulation of the passive-observer
problem: an answer whose request was never seen. v3's central design claim is that these are
unidentifiable. It was tested rather than assumed.

**Hypothesis.** The checksum covers the request bytes. Given a payload and its checksum, brute-force
the `(command, args)` space and keep the candidates that reproduce it.

**Result: the checksum is not an attribution oracle.** Across the first 40 unpaired answers, every
one admitted ~48 consistent `(command, args)` pairs spanning 6 distinct commands. The reason is
structural: the checksum is one byte and the argument bytes are free, so for any target there is
almost always an argument string that satisfies it. **§3.2's "answers are anonymous" is correct
and cannot be worked around this way.**

Length narrows it but does not close it. Of the 15 fixed-size commands measured, three length
classes are ambiguous:

| payload | candidate commands |
|---:|---|
| 2 | `0x01 GIVESTATUS`, `0x33 GIVEPROGID` |
| 3 | `0x02 GIVEGTYPE`, `0x25 GIVE_ACTZYKINDEX` |
| 14 | `0x06 GIVEKONFIG`, `0x23 GIVE_SENSORVALUES` |

and applying the checksum to those pairs resolved **none** of them. The variable-length `0x16`
collides with everything.

**The one thing that does work is much narrower**, and it is worth recording because it repaired
real data here. When the candidate set is small and the arguments are *fixed* rather than free, the
checksum becomes decisive. One exchange in this capture presented a 61-byte answer while a `0x06`
request was outstanding; the body had the `n×10+1` shape of `0x16`. Testing the two hypotheses with
their actual argument strings:

```
request 16 01 01 e7   (0x16, station 1, arg 1)  →  checksum matches observed 0x59   ✔
request 06 01 f8      (0x06, station 1)         →  no match
```

The answer belonged to a `0x16` request; the pairing was wrong. **Use the checksum to *validate* an
attribution you already have, never to *derive* one.** As a validator it is excellent — it caught a
mis-pairing that length alone would have accepted.

> **Consequence for the passive-vs-master decision (v3 §17.1).** This is the strongest evidence yet
> for **master**. A passive observer that misses a single request — one dropped mirror packet — has
> no way to recover attribution for everything that follows on that unit, and no way to *detect*
> that it has lost it, because the frames still checksum against the wrong request only 1/256 of
> the time but the *lengths* will often still fit.

---

## C.13 Gap register — post-capture

| # | Gap | v3 | Now | Change |
|---|---|---|---|---|
| G1 | Header wire layout | 100% ✅ | **100%** ✅ | confirmed on the wire (`E5 01 04` at offset 0) |
| G2 | Completion rule + size table | 100% ✅ | **100%** ✅ | rule confirmed 250/250; **table contents refuted**, see D3 |
| G3 | Request side / master role | 100% ✅ | **100%** ✅ | confirmed; `LEN` rule refined |
| G4 | Capture strategy / CAN-ID base | 100% ✅ | 🔴 **reopened → 100%** | v3's answer was wrong; two bases (§C.3.1) |
| G5 | Checksum | 100% ✅ | **100%** ✅ | now verified in **both** directions, 498 samples |
| G6 | Record-layout versioning | 20% | **20%** | untouched; `0x0D` gives the version-stamped record if wanted |
| G7 | `MC_` body layouts | ~65% | **~75%** | 6 new bodies; `0x06`/`0x0D`/`0x0E`/`0x12` decoded |
| G8 | Limits + "%" display | 70% | **75%** | `CDRLim` confirmed on the wire |
| G9 | `channelKey` → feature index | 60% | **~90%** | one-hot `mask & 0x0F`, with real names (§C.10.3) |
| G10 | Unit ↔ serial ↔ model | 100% ✅ | ⚠️ **90%** | model ✅; **serial source not found** (§C.10.5) |
| G11 | Device-side timestamps | 50% | **~90%** | gateway µs clock + alarm D-M-Y H:M:S |
| G12 | Reader robustness | 80% | **80%** | unchanged — but this file *is* the missing replay corpus |
| **D3** | Real sizes for `0x01`,`0x12`,`0x1B` | measurement needed | **2 of 3 closed** | `0x01`=2, `0x12`=17; **`0x1B` still open** |
| **D4** | The `0x08` size branch | measurement needed | **closed** | `n = 5` (§C.9.2) |
| **NEW D5** | `0x1B GIVESIGNALVERLAUF` size and body | — | **open** | absent from all five captures |
| **NEW D6** | Multi-frame **request** continuation | — | **open** | no multi-frame request captured |

**Aggregate:** protocol knowledge ≈99.5%; a correct end-to-end reader ≈90%. What stands between 90%
and 100% is now *one command* — `0x1B`, the live amplitude trace — plus engineering.

---

## C.14 Correction ledger additions (C25–C31)

Extends v3 §0.6 / Part 20. Same convention: **CORRECTION** reverses, **RECONCILIATION** merges,
**RESOLUTION** closes.

| # | Item | v3 said | Now | Evidence |
|---|---|---|---|---|
| **C25** | Answer CAN-ID base | **CORRECTION.** "One base… transmit and receive use the same base"; `0x580` purpose unknown; G4 closed | **Two bases.** Requests `0x500+unit`, answers `0x580+unit`. `0x580` is the answer base | 8,800 records, total split (§C.3.1) |
| **C26** | Gateway UDP source port | *(unaddressed)* | Gateway answers from an **ephemeral, session-varying** port (34686, 50375), never 1789. Bind `:1789` unconnected; filter on host | 2,513 answer datagrams (§C.3.2) |
| **C27** | Gateway record `+0x04..0x14` | **CORRECTION.** "17 bytes of zero padding" | 8-byte tag + **64-bit BE µs timestamp** at `+0x0C` + channel at `+0x14`. The record is the standard PEAK gateway frame | 8.5 ppm vs capture clock (§C.4) |
| **C28** | `Geraet_expectedRecordSize` | **CORRECTION.** Table treated as usable except for 3 doubtful entries | Only `0x0E` is confirmed. `0x02`, `0x05`, `0x08`, `0x0F` are all wrong against measurement. Do not ship the table | §C.9 |
| **C29** | Request first-frame `LEN` | **CORRECTION.** "`[00][00][00][5 payload]` LEN = 8" | `LEN = 3 + min(5, payloadLen)`; observed 5, 6, 7, 8 | 250 requests (§C.6) |
| **C30** | Answer-direction checksum seed | **RESOLUTION.** "⚠️ Open assumption… verified for requests only" | Symmetric, confirmed. 248/248; all 3 alternative seedings score 0/250 | §C.8 |
| **C31** | D3 / D4 "not in the executable" | **RESOLUTION.** Both blocked on a live device | Both measured. D4 → `n = 5`; D3 → `0x01`=2, `0x12`=17. `0x1B` re-filed as D5 | §C.9 |

⚠️ **C25 partially reinstates a struck claim.** the session handoff (Part 20 §20.4) read `0x580` as a direction
discriminator; the session report struck it and v3 adopted the strike (ledger C4). The strike was correct
that `0x580` is not a *transmit* base and that there are not three bases. It was wrong to conclude
that receive shares the transmit base. **Ledger C4 should now read: two bases, not one and not
three.** The lesson is narrow and worth keeping: `Promos3CanInterface::send` is evidence about
transmit only, and no receive-side function was ever read to check it.

---

## C.15 Changes required in the reader

Supersedes and extends §17.5, and is itself superseded by **§36.5** where they differ. Items marked 🔴 are the difference between receiving data and
receiving nothing.

```
🔴 FIX   CAN-ID: two bases. TX 0x500+unit, RX 0x580+unit.
         unit = id & 0x7F;  is_answer = (id & 0x580) == 0x580
         (v3's "unit = id - 1280" drops 100% of answers)

🔴 FIX   socket: bind :1789 UNCONNECTED. Do not connect() to the gateway.
         Accept from any source port; filter on source HOST only.

🔴 FIX   gw_parse_record(): CAN-ID is a 32-bit BE dword at +0x18, not a word at +0x1A.
         DLC +0x15, channel +0x14, flags +0x16 (reject nonzero until understood).

🔴 FIX   request framing: LEN = 3 + min(5, payloadLen). Do NOT zero-pad to 8 —
         padding is inside the checksum's summed range.

   ADD   timestamp: read the 64-bit BE microsecond counter at +0x0C. Use it for
         ordering and intervals; anchor to host clock once per session.
         Handle the low-word wrap every 71.6 min (use all 64 bits).

   ADD   datagram loop: up to 15 records (540 bytes) per answer datagram.

   ADD   expected sizes from the MEASURED table (§C.9), not the binary's table.
         Unknown command -> do not guess; let it time out.

   ADD   0x16: expected = DATA[1] * 10 + 1   (recordSize = features*2 + 2)

   ADD   checksum-only frame when expected % 7 == 0.
         Distinguish from a device error by DATA[0]: error is seq 0, checksum-only is seq >= 1.
         Do NOT key on DATA[1]==1 alone.

   ADD   answer checksum verification -(unit + Sum req[0..n-2] + Sum payload).
         Use it to VALIDATE attribution, never to derive it.

   ADD   feature names from SKanalRec 0x0E at body +0x4D, stride 12,
         [mask][11-byte name]; index = log2(mask & 0x0F). Never hard-code names.

   ADD   alarm timestamps from 0x12 body +0x0A..0x0F = D,M,Y,h,m,s (year +2000).

   ADD   receive deadline armed on LAST FRAME RECEIVED, not on the request
         (a 143-frame answer takes ~25 ms at 178 us/frame).
         50 ms is ample; 300 ms is 22x the worst observed latency.

   ADD   0x0D as the discovery command: one 66-byte SGeraetRec gives model,
         channels, sensor complement and ReduzLim in a single exchange.

   KEEP  the CONF_* honesty gating.
   KEEP  everything else in v3 §17.5 not contradicted above.
```

### C.15.1 The 30-second test, corrected

§17.2's datagram is **correct as constructed** — `00 24 00 80`, DLC 6, CAN-ID `0x501`, DATA
`00 00 00 08 01 f6` — and this capture confirms every field of it. Two changes to the *procedure*:

1. Send it from a socket **bound to 1789 and not connected**, or the reply is dropped by the kernel
   before your code sees it (§C.3.2).
2. Expect the answer on CAN-ID **`0x581`**, not `0x501` (§C.3.1).

Expected reply, now known rather than hoped for: **5 payload bytes**, `00 00 00 00 ff`, in a single
frame with `DLC = 7`, arriving in **1–2 ms**.

---

## C.16 Reproduction

Every number in this Part is mechanically derived from `ALL_merged__uniq.pcapng`. The decode chain
is: pcapng EPB → Ethernet → IPv4 → {UDP, ICMP-quoted UDP} → 36-byte records → CAN frames →
per-unit exchanges. ICMP-quoted datagrams are included; the `packets_july5` session shows the PC
answering 634 quoted datagrams with port-unreachable, i.e. PROVIS3 was not bound to 1789 while it
ran, so the CAN payloads are intact inside the quotations but the session is one-sided and carries
no requests. It is usable for framing checks only, and is excluded from every attributed statistic
above.

Statistics quoted as "0 exceptions" were evaluated as predicates over the full record set, not
sampled.

**This file is also the `--replay` corpus that G12 has wanted since Part 15.** It contains one
example of every distinct exchange the installation produces, with byte-exact original timestamps.
A reader that decodes all 250 attributed exchanges from this file, verifies 250 request checksums
and 248 answer checksums, and reproduces §C.9's size column is correct on everything except
`0x1B` — without booking a machine window.

---

*End of Appendix C.*

*This Part amends Parts 0–21 of this report at §0.2 (fact 2), §0.5, §0.6 (C4), §2.2, §2.3, §2.5,
§3.4, §3.5.3, §3.6, §3.7.1, §17.2 and §17.5 — all of which now carry inline correction banners
pointing here. Where this Part and Parts 0–21 disagree on a wire fact, **this Part is measurement
and Parts 0–21 are inference; prefer this Part.** Where this Part and Part 35 disagree, prefer
Part 35 — it has the larger sample. The normative merged result is **Part 36**.*

---

# ═══════════════════════════════════════════════════════════════
# PART 35 — CAPTURE 3: DEPTH  (Appendix D)
# ═══════════════════════════════════════════════════════════════

> **Originally circulated as "Part 23 / Appendix D: Raw Poll-Loop Capture"** (renumbered to
> Part 24 by the ⟦MEAS⟧ edition, and to **Part 35** here). Its internal
> `D.x` section numbers are **kept unchanged**; cite sections of this Part as **§D.n**.
> Where this Part and Part 34 disagree, **this Part wins** — it has a 356× larger sample.


**Status: this Part supersedes two framing rules stated in §3.6 and repeated in Part 34 §C.7.
See §D.2 and the ledger in §D.9 — and §0.6 C32/C33/C34, where the same corrections are recorded.**

**Question this Part answers:** *Part 34 was built from a deduplicated file in which no complete
answer exceeded 170 bytes. Do the framing rules still hold when the device sends a kilobyte — and
what is actually inside the live measurement block?*

**Source artefact:** `july_6_packet1.pcapng` — **183,997 packets**, a raw unfiltered capture of the
same cell (PROVIS3 PC `192.168.222.24` ⇄ gateway `192.168.222.16`), **143.2 seconds** of an
uninterrupted poll loop. Decoded into **194,006 gateway records** (88,936 requests, 105,070 answer
frames) and **88,936 complete attributed exchanges** — a 356× larger attributed sample than
Part 34, and the first artefact containing no deduplication at all.

Confidence markers are the report's own: ✅ VERIFIED, 🔶 GHIDRA, ⚠️ INFERRED, 🔴 trap.

---

## D.0 Headline

> **Two rules broke, and the live measurement block decoded.**
>
> Part 34's `%7` checksum-placement rule and its `ceil(n/7)` frame-count rule are **wrong**.
> They held perfectly on 250 exchanges only because that file contained nothing long enough to
> expose them. The device flushes its transmit buffer every 250 payload bytes and emits a short
> frame at each boundary, so **payload bytes per frame is `DLC − 1`, not 7** — exactly as the
> decompiled assembler always said, and exactly as v3's *prose* did not. The corrected rule is
> given in §D.2 and holds **88,936 / 88,936**.
>
> Against that, everything else got stronger. The checksum verifies **88,936/88,936 in each
> direction** — a 177,872-sample confirmation. Sequence continuity: 88,936/88,936. Zero retries,
> zero timeouts, zero device errors.
>
> And `0x16 GIVESAMMELMERKMALE` — the live measurement block, the single most valuable body on the
> box after `0x1B` — **is decoded** (§D.4). Each row is four `(min, max)` byte pairs plus two
> status bytes, verified across 61,764 feature pairs with **zero violations**, and the escape
> mechanism is confirmed by an exact 64/64 bijection.

| Measure | After Part 34 | After this capture |
|---|---|---|
| Protocol *knowledge* | ≈99.5% | **≈99.7%** |
| Live *reader* correct end to end | ≈90% | **≈93%** |
| `MC_` body layouts decoded | 8 of 38 | **9 of 38** (`0x16` is the valuable one) |
| Largest complete answer seen | 170 B | **1,001 B / 144 frames** |
| Attributed exchanges verified | 250 | **88,936** |

---

## D.1 Provenance — and why this file tests what C could not

| | Part 34 file | This file |
|---|---|---|
| nature | deduplicated, 1 exchange per kind | **raw, unfiltered** |
| attributed exchanges | 250 | **88,936** |
| distinct commands | 16 | 5 (`0x0E` once, then `0x16 / 0x08 / 0x01 / 0x33`) |
| largest complete answer | 170 B (25 frames) | **1,001 B (144 frames)** |
| adjacency / timing | synthetic | **real** |
| retries, cadence, ordering | not observable | **observable** |

The two files are complementary and neither supersedes the other: C has breadth (16 commands,
16 answer sizes, six decoded bodies), D has depth (one poll loop, 88,936 times, at full length).
**Every size Part 34 measured is reproduced here exactly** — `0x01`→2, `0x08`→5, `0x33`→2, `0x0E`→144,
`0x16`→`n×10+1` — which is a useful independent check on Part 34's method.

**Same installation, ~18 hours later.** `0x0E GIVEKANAL` returns the identical descriptor block —
unit 1 `SPINDEL / X AXIS / Y AXIS / Z AXIS` at masks `0x81/0x82/0x84/0x88`, unit 2 `VIBRATION /
M131 DEBI / M131BASINC / M08 DEBI` at masks `0x01/0x02/0x04/0x08`, `CDRLim` `aa aa aa aa` on both.
The gateway uptime counter reads **19.768 days** here against **19.022 days** in the Part 34 capture — a
gap of 17.9 hours, with the counter never reset. That is a clean third-party confirmation that the
`+0x0C` field is a continuous uptime clock (§C.4.1) and that both files are the same physical box.

---

## D.2 🔴 The framing correction — frames are not all 7 bytes

### D.2.1 What the wire shows

Part 34 §C.2 asserts *"7 payload bytes per frame"* and validates *"frame count = `ceil(n/7)`"*
across 250 exchanges with zero exceptions. §3.6 says the same. Both are wrong in general.

Census of payload bytes per frame (`DLC − 1`) across all 88,936 exchanges:

| payload bytes | as a mid-stream frame | as the final frame |
|---:|---:|---:|
| 7 | 16,100 | 3 |
| 6 | **12** | 22,244 |
| 5 | **21** | 14,166 |
| 4 | — | 52 |
| 3 | — | 44,467 |
| 2 | — | 7,965 |
| 1 | — | 39 *(the checksum-only frames)* |

Short **final** frames are expected. Short **mid-stream** frames are not, under the v3 model — and
33 of them occur. Their positions are not random:

| short mid-frame at frame index | occurrences | cumulative payload bytes at that point |
|---:|---:|---:|
| 35 | 12 | **251** |
| 71 | 11 | **501** |
| 107 | 10 | **751** |

**The device flushes every 250 payload bytes.** For `0x16` the payload is a 1-byte row count
followed by 10-byte rows, so 250 bytes is exactly **25 rows** — the boundaries fall at 1+250,
1+500, 1+750. Whether the trigger is a 250-byte buffer or a 25-row block cannot be separated from
`0x16` alone, and no other command in either capture produces an answer longer than 250 bytes.

⚠️ **This is why Part 34 saw nothing.** Its longest complete answer was 170 bytes — below the first
boundary. The rules did not "hold and then break"; they were never tested.

### D.2.2 What the decompiled code always said

§3.6 quotes the assembler loop correctly:

```c
avail = frame[5] - 1;                                  /* = DLC - 1, NOT the constant 7 */
if (avail > expected - accumulated) avail = expected - accumulated;   /* clamp */
```

The code reads `DLC − 1` and clamps to the remaining expected bytes. It never assumes 7. The error
was in the *prose summary* — "7 payload bytes per frame" — which was true of every sample then
available and got promoted to a rule. Tested directly:

```
sum(DLC − 1) over all frames  ==  total assembled bytes     →  88,936 / 88,936  ✅
```

### D.2.3 The corrected checksum-placement rule ✅

Not `expectedSize % 7 == 0`. The real condition is whether the **clamped `avail`** on the final
data-carrying frame came out at 7 — i.e. whether that frame was completely filled with payload,
leaving no room for the trailing checksum byte.

```c
acc = 0;
for each frame {
    if (acc >= expected) break;
    avail = min(DLC - 1, expected - acc);
    append DATA[1 .. avail];
    acc += avail;
}
if (avail == 7)   /* last frame was full: no room for the checksum */
    take one more frame; it must be LEN==2, checksum = DATA[1];
else
    checksum = DATA[LEN-1] of the frame just consumed;
```

| rule | agreement over 88,936 exchanges |
|---|---:|
| **corrected (clamped `avail == 7`)** | **88,936 / 88,936 — 100.0000%** ✅ |
| Part 34 / Parts 0–21 (`expectedSize % 7 == 0`) | 88,925 / 88,936 — **11 counter-examples** 🔴 |
| "last frame had `DLC == 8`" | 88,933 / 88,936 — 3 counter-examples |

All 11 counter-examples are 1,001-byte `0x16` answers: `1001 % 7 == 0`, so the old rule predicts a
checksum-only frame, but the three mid-stream short frames shift the final frame off the boundary
and the checksum lands inline instead.

The 3 counter-examples to the naïve `DLC == 8` variant are 41-byte answers whose final frame has
`DLC = 8` but whose clamped `avail` is 6 — the frame is physically full while only 6 of its bytes
are payload, so the checksum occupies `DATA[7]`. **The clamp is what makes the rule exact.**

🔴 **Severity.** A reader using the `%7` rule mishandles ~0.012% of exchanges here — but the
affected exchanges are precisely the long `0x16` blocks that carry the backlog of real measurement
samples. It waits for a checksum-only frame that never comes, times out, and discards a 100-row
block. On this box that is one dropped measurement burst per ~8,000 polls, appearing as an
occasional unexplained data gap.

### D.2.4 Frame-count predicate — withdrawn

Part 34 §C.7 offers `frames == ceil(expected/7) + (expected % 7 == 0)`. It scores 88,935/88,936
here, and the single failure (a 741-byte answer in 107 frames where the formula predicts 106) is
enough to retire it. **There is no closed form for the frame count**, because the device may insert
a short frame at any 250-byte boundary. A reader must accumulate `DLC − 1` and stop on the byte
count, never on a frame count.

---

## D.3 Everything else, re-verified at 356× scale ✅

| rule | result |
|---|---:|
| record header `00 24 00 80` | **194,006 / 194,006** |
| every datagram an exact multiple of 36 | **181,309 / 181,309** |
| requests on `0x500 + unit`, answers on `0x580 + unit` (§C.3.1) | **194,006 / 194,006**, total split |
| gateway source port ephemeral, never 1789 (§C.3.2) | **34686** throughout — same port as one of C's two |
| channel byte `+0x14` and flags byte `+0x16` both zero | 194,006 / 194,006 |
| request framing `[00][00][00]` + payload, `LEN = 3 + min(5, payloadLen)` | **88,936 / 88,936** |
| **request checksum** `−(unit + Σ)` | **88,936 / 88,936** |
| **answer checksum** `−(unit + Σreq[0..n−2] + Σpayload)` | **88,936 / 88,936** |
| **sequence continuity** `DATA[0] = 0,1,2,…` | **88,936 / 88,936** |
| `0x16` length `= DATA[1] × 10 + 1` | **88,936 / 88,936**, including all 1,001-byte cases |

The checksum now stands at **178,370 verified samples across both directions and both captures,
with zero failures.** Part 34 §C.8 closed the answer-direction seed as an open assumption on
248 samples; that closure is now beyond reasonable doubt.

⚠️ **Sequence wrap is still untested.** The largest answer here is 144 frames. A wrap past 255
would require an answer of ≈1,785 bytes; none exists in either capture. The `+1 per frame, wraps at
256` behaviour remains 🔶 GHIDRA.

---

## D.4 ⭐ `0x16 GIVESAMMELMERKMALE` — the live measurement block, decoded ✅

This is the substantive gain from the file. 22,234 `0x16` exchanges yielded **15,521 measurement
rows**, enough to test a layout rather than guess one.

### D.4.1 The row layout

```
payload[0]              = row count n            (0 … 100 observed)
payload[1 + r*10 .. ]   = row r, 10 bytes:

  +0  Min_F0   +1  Max_F0      feature 0   (unit 2: VIBRATION)
  +2  Min_F1   +3  Max_F1      feature 1   (unit 2: M131 DEBI)
  +4  Min_F2   +5  Max_F2      feature 2   (unit 2: M131BASINC)
  +6  Min_F3   +7  Max_F3      feature 3   (unit 2: M08 DEBI)
  +8  status0                  flag byte, observed {0x00, 0x10, 0x20, 0x30}
  +9  status1                  flag byte, observed {0x00, 0x20, 0x80, 0xA0}
```

stride `= featureCount × 2 + 2 = 4×2 + 2 = 10`, exactly as §6.2 predicts.

### D.4.2 The evidence for `(min, max)`

v3 and §6.2 name the two bytes of each feature pair `lo` and `hi` and treat `hi` as a
status/marker byte. The positional model is right; **the semantics are `(minimum, maximum)`**.

| test | result |
|---|---:|
| feature pairs examined (non-escape rows) | **61,764** |
| pairs where `byte[2f] > byte[2f+1]` | **0** |

Zero inversions in 61,764 samples. The two bytes of each pair also share an identical value range
per feature — feature 0 spans 0–35 on both bytes, feature 1 spans 0–108 on both, feature 2 0–111,
feature 3 0–114 — which is what a `(min, max)` pair of one signal looks like and is not what a
`(value, flags)` pair looks like.

**Independent corroboration from the database side.** Part 10 records the per-workpiece
measurement tables as storing a *per-sensor min/max envelope*:

```
WP_00001_01 :  Min_S01, Max_S01, Min_S02, Max_S02, Min_S03, Max_S03, Min_S04, Max_S04
```

Four `(min, max)` pairs, one row per sample index — **byte for byte the wire layout above.** The
storage schema and the wire format are the same structure. That resolves the open question of how
the app gets from `0x16` to `WP_*`: it does not transform anything, it writes the rows through.

⚠️ This also settles that the amplitude representation is raw 0–255 counts on the wire, consistent
with the "no scaling factor" result (Part 7), now confirmed from a third source.

### D.4.3 The escape mechanism — confirmed by an exact bijection ✅

§6.2 states that `lo == 0xFF` is an escape, that `hi` selects the marker, and that *the
following row carries the parameter*. All three confirmed:

| test | result |
|---|---:|
| rows with `byte[0] == 0xFF` | **64** |
| rows where any `min > max` | **64** |
| overlap | **64** |
| escape rows that do not violate `min ≤ max` | **0** |
| violating rows that are not escapes | **0** |

An exact bijection. The escape is the *only* thing in 15,521 rows that breaks the `min ≤ max`
invariant — which confirms both models at once, and gives a reader a free integrity check: a
non-escape row with `min > max` means the reassembly is wrong.

**Every one of the 64 escapes carries marker `0xFB`** — the documented *"per-feature reset across all
features"* (§6.2) — and the escape is replicated across all four feature slots, with the parameter in the
next row exactly as documented:

```
row r    :  ff fb  ff fb  ff fb  ff fb  30 a0      <- escape, marker 0xFB, all four features
row r+1  :  00 01  00 01  00 01  00 01  30 a0      <- the parameter row
```

⚠️ Markers `0x00` (new cycle) and `0xFE` (workpiece ID) do **not** appear — no cycle boundary and
no workpiece change occurred in this 143-second window. Their handling stays 🔶 GHIDRA.

🔴 **Do not read `0xFF` in the max byte as an escape.** Rows such as `fe ff 01 01 01 01 27 27` are
ordinary saturated readings (`min` 254, `max` 255) and appear in the data. The escape is signalled
by `byte[0]`, the *minimum* of feature 0, and only there.

### D.4.4 Row-count behaviour

| rows per poll | occurrences | note |
|---:|---:|---|
| 0 | 7,964 | nothing new since the last poll; payload is 1 byte |
| 1 | 14,164 | steady state |
| 2 – 4 | 94 | |
| 37, 74, 100 | 12 | **backlog flush** — 100 rows = 1,001 bytes = 144 frames |

At 77.6 poll cycles per second (§D.5) and typically one row per cycle, the effective sample rate is
≈78 Hz per unit. ⚠️ The occasional 100-row burst is the device emptying a buffer; a reader that
cannot handle a 144-frame answer will lose exactly the bursts, which is the worst possible subset
to lose.

⚠️ `expected == 1` (row count 0) is **not** the "`expected == 0` → pure ack" case of §3.7. It is
a one-byte payload plus a checksum, in one frame. No zero-length answer occurs in either capture,
so the pure-ack path is still 🔶 GHIDRA.

---

## D.5 The poll loop — measured ✅

The cycle is exactly **8 requests**, and it does not vary once across **11,116 consecutive cycles**:

```
u1:0x16  u1:0x08  u1:0x01  u1:0x33   u2:0x16  u2:0x08  u2:0x01  u2:0x33
   ↑        ↑        ↑        ↑
 samples   PLC    status  prog-id
```

preceded, exactly once per unit at session start, by `0x0E GIVEKANAL` — the descriptor fetch. That
is the whole of the steady-state dialogue: **one configuration read, then four commands per unit
forever.**

| quantity | measured |
|---|---|
| full 8-request cycle | median **12.64 ms**, p90 15.2, p99 19.8, max 83.7 |
| cycle rate | **77.6 cycles/s** |
| request → next request | median **1.51 ms**, p10 1.12, p90 2.17 |
| request → first answer frame | median **1.17 – 1.93 ms** by command; p99 ≤ 2.9; max **9.8 ms** |
| inter-frame gap (device clock) | median **151 µs**, p10 143, p90 168 |
| answer datagram batching | 1–15 records; max **540 bytes** |

⚠️ **Amends §0.2 fact 5 and §1.4** ("a 3 ms polling loop"). The measured inter-request interval is
**1.5 ms**, roughly double the rate the static analysis states. Nothing depends on the exact figure, but a master
implementation pacing itself at 3 ms will run at half the app's throughput.

**Timeout headroom.** `[CAN] unitAnswerTimeout = 300` against a worst observed latency of 9.8 ms is
a 31× margin. Part 34 §C.11's suggestion of a 50 ms deadline is confirmed as ample — but arm it
on the **last frame received**: a 144-frame answer takes 144 × 151 µs ≈ **22 ms** to stream, which
would breach a naïve 20 ms request-anchored deadline.

---

## D.6 What did *not* happen — and why that matters

Across 88,936 exchanges, in a live production cell:

| event | occurrences |
|---|---:|
| device error answer (`DATA[0]==0 && DATA[1]==1 && LEN==2`) | **0** |
| request re-sent within 250 ms (a retry) | **0** |
| answer timeout | **0** |
| sequence discontinuity | **0** |
| checksum failure, either direction | **0** |
| answer with no outstanding request | **0** |
| multi-frame request | **0** |
| `0x1B GIVESIGNALVERLAUF` | **0** |

Two readings, and both matter.

**The link is clean.** On a healthy cell the error paths are simply never exercised. That is good
operational news and bad test-coverage news: the **retry ladder, the abort path, the error-answer
frame and the `LEN==2` disambiguation of §3.8 / Part 34 §C.7.2 remain entirely unverified on the wire.**
A reader's error handling cannot be validated against any capture that exists; it must be tested by
injection.

**`0x1B` is absent from six captures now.** The live amplitude trace was not requested in any of
the five sessions behind Part 34, nor in this one. It is not part of the steady-state poll loop
— it is fetched only when the operator opens the signal-trace view. **D5 will not close by
capturing more idle traffic; it needs someone standing at the HMI opening that screen.** That is a
concrete, cheap action, and it is now the single highest-value item in the project.

---

## D.7 Minor findings

**`0x08 GIVEPLCVALUES` is genuinely live.** Payload `00 00 XX 00 ff`, with byte 2 taking 7 distinct
values across the capture:

| byte[2] | `0x01` | `0x00` | `0x04` | `0x03` | `0x40` | `0x05` | `0x02` |
|---|---:|---:|---:|---:|---:|---:|---:|
| count | 7,505 | 4,473 | 2,991 | 2,431 | 2,079 | 1,412 | 1,343 |

The low bits look like a small bit-field and `0x40` stands apart — plausibly the tool-change bit
that §6.2 documents for the `0x16` status path. ⚠️ INFERRED; recorded for whoever decodes the
PLC word.

**`0x01 GIVESTATUS` and `0x33 GIVEPROGID` were constant** (`00 00`) across 11,117 polls each. The
cell was in a steady state with no program change. Their **sizes** are confirmed; their **layouts**
remain undetermined, and Part 34 §C.10.7's warning stands: do not infer "this field is always
zero" from an idle machine.

**Clock drift.** Gateway span 143.2117 s against capture span 143.2150 s. Part 34 measured +8.5
ppm over 3,837 s; this window gives −23 ppm over 143 s. ⚠️ A 143-second window is too short to pin
the sign — the disagreement is host-clock jitter, not device instability. Treat C's longer-baseline
figure as the better estimate; the operative point is that the counter tracks real time to within
tens of ppm and is fit for ordering and interval measurement.

---

## D.8 Gap register — post-D

| # | Gap | After C | Now | Change |
|---|---|---|---|---|
| G1 | Header wire layout | 100% ✅ | **100%** ✅ | — |
| G2 | Completion rule + size table | 100% ✅ | 🔴 **reopened → 100%** ✅ | the `%7` and `ceil(n/7)` rules were wrong; corrected rule verified 88,936/88,936 |
| G3 | Request side / master role | 100% ✅ | **100%** ✅ | poll cycle and cadence now measured, not inferred |
| G4 | CAN-ID base | 100% ✅ | **100%** ✅ | two-base split re-confirmed at 194,006 records |
| G5 | Checksum | 100% ✅ | **100%** ✅ | 178,370 total samples, zero failures |
| G6 | Record-layout versioning | 20% | **20%** | untouched |
| G7 | `MC_` body layouts | ~75% | **~80%** | `0x16` decoded — the important one |
| G8 | Limits + "%" display | 75% | **75%** | — |
| G9 | `channelKey` → feature index | ~90% | **~90%** | mask encoding re-confirmed on the same box |
| G10 | Unit ↔ serial ↔ model | ⚠️ 90% | **90%** | serial source still not found |
| G11 | Device-side timestamps | ~90% | **~95%** | uptime counter confirmed continuous across an 18-hour gap |
| G12 | Reader robustness | 80% | **85%** | this file is a 143-second full-rate replay corpus |
| **D5** | `0x1B` size and body | open | **open** — *needs an operator action, not a longer capture* | absent from 6 sessions |
| **D6** | Multi-frame request continuation | open | **open** | no request >8 bytes in 88,936 |
| **NEW D7** | Error / retry / abort paths | — | **open** | zero occurrences in a clean link; must be tested by injection |
| **NEW D8** | Sequence wrap past 255 | — | **open** | needs an answer ≳1,785 bytes |
| **NEW D9** | The 250-byte flush boundary | — | **⚠️ characterised, not explained** | is it a byte buffer or a 25-row block? |

**Aggregate:** protocol knowledge ≈99.7%; a correct end-to-end reader ≈93%. What remains is `0x1B`,
the untested error paths, and engineering.

---

## D.9 Correction ledger additions (C32–C35)

Extends §0.6 / Part 20 and Part 34 §C.14. The same four entries appear in §0.6 as C32–C35.

| # | Item | Previously | Now | Evidence |
|---|---|---|---|---|
| **C32** | Payload bytes per frame | **CORRECTION.** §3.6 and Part 34 §C.2: "7 payload bytes per frame" | **`DLC − 1`, clamped to the remaining expected bytes.** The device emits short mid-stream frames at 250-byte flush boundaries. The decompiled code was always right; the prose summary was not | 33 short mid-frames at cumulative 251/501/751; `sum(DLC−1) == total` 88,936/88,936 (§D.2) |
| **C33** | Checksum-only frame condition | **CORRECTION.** §3.6 and Part 34 §C.7.1: separate `[seq][ck]` frame iff `expectedSize % 7 == 0` | **iff the clamped `avail` on the final data frame equals 7.** Old rule: 11 counter-examples. New rule: **100.0000%** | 88,936 exchanges (§D.2.3) |
| **C34** | Frame-count formula | **CORRECTION.** Part 34 §C.7: `frames == ceil(expected/7) + (expected%7==0)` | **Withdrawn — no closed form exists.** Stop on the accumulated byte count, never on a frame count | 1 counter-example at 741 bytes (§D.2.4) |
| **C35** | `0x16` feature-pair semantics | **RESOLUTION.** §6.2: bytes named `lo`/`hi`, `hi` read as a status byte | **`(min, max)` of that feature for the sample.** Positional model correct, semantics corrected. Matches the `WP_*` `Min_Sxx/Max_Sxx` schema exactly | 61,764 pairs, 0 inversions; 64/64 escape bijection (§D.4) |

⚠️ **Note on C32/C33.** These are the first corrections in the project where the **Ghidra output was
right and the summary of it was wrong**. Both rules appear in §3.6 immediately below a correct quote
of the assembler loop that contradicts them. The lesson is narrow and worth keeping: when a
constant is derived from a variable in the decompilation (`avail = frame[5] − 1`), do not promote
the value it happened to take in every observed sample into the rule.

---

## D.10 Changes required in the reader

Supersedes the corresponding lines of Part 34 §C.15. The merged, normative form is **§36.5**. Items marked 🔴 change behaviour on real
traffic.

```
🔴 FIX   reassembly: payload per frame = DLC - 1, clamped:
             avail = min(DLC - 1, expected - accumulated)
         NOT the constant 7. Short mid-stream frames occur at 250-byte boundaries.

🔴 FIX   checksum placement: after the last payload byte,
             if (avail == 7)  -> ONE more frame follows: [seq][checksum], LEN must be 2
             else             -> checksum is DATA[LEN-1] of the frame just consumed
         DELETE any test on (expected % 7).

🔴 FIX   completion: stop when accumulated == expected.
         DELETE any frame-count formula; there is no closed form.

   ADD   0x16 row decode, stride = featureCount*2 + 2:
             [Min_F0][Max_F0][Min_F1][Max_F1][Min_F2][Max_F2][Min_F3][Max_F3][st0][st1]
         escape: row[0] == 0xFF -> row[1] is the marker (0xFB reset seen),
                 the NEXT row carries the parameter.
         Do NOT treat 0xFF in a Max byte as an escape - that is saturation.

   ADD   integrity check: in a non-escape row, min > max means the reassembly is wrong.
         Free, and it catches exactly the class of bug C32/C33 would have caused.

   ADD   handle a 144-frame / 1001-byte answer without special-casing.
         Losing it means losing the backlog bursts - the densest data on the wire.

   ADD   receive deadline armed on LAST FRAME RECEIVED. 50 ms is ample
         (worst observed latency 9.8 ms; longest answer streams for ~22 ms).

   NOTE  master pacing: the app issues a request every ~1.5 ms, not 3 ms;
         a full 8-request cycle over 2 units takes ~12.6 ms.

   NOTE  error/retry/abort paths are UNVERIFIED - no occurrence in 88,936 exchanges.
         Test them by injection, not by capture.

   KEEP  everything in Part 34 §C.15 not listed above - all of it re-verified here.
```

---

## D.11 Reproduction

All figures are mechanically derived from `july_6_packet1.pcapng` by the same chain as Part 34:
pcapng EPB → Ethernet → IPv4 → UDP → 36-byte records → CAN frames → per-unit exchanges. Non-cell
traffic (mDNS, NetBIOS, LLMNR, a HASP licence beacon on UDP 1947, and three hosts broadcasting on
2008) was filtered by host pair and forms no part of any statistic. Predicates reported as
"*n / n*" were evaluated over the full set, not sampled.

**As a replay corpus this file is stronger than Part 34's.** C has one example of every exchange
kind; D has the poll loop at full rate for 143 seconds, including 12 long-answer bursts and 64
escape rows. A reader that ingests both, verifies 89,186 request checksums and 89,184 answer
checksums, reproduces the size table, decodes 15,521 measurement rows with zero `min > max`
violations outside the 64 escapes, and handles a 144-frame answer, is correct on everything the
installation does except `0x1B` and the error paths.

---

*End of Appendix D.*

*This Part amends Parts 0–21 at §0.2 (fact 5 and fact 8), §1.4, §3.6, §3.7 and §6.2, and Part 34
at §C.2, §C.7, §C.7.1 and §C.15 — all of which now carry inline correction banners pointing here.
Where this Part and an earlier one disagree, this Part has the larger sample; where it and the
decompiled code agree against earlier prose, **the code was right all along.** The normative
merged result is **Part 36**.*

---

# ═══════════════════════════════════════════════════════════════
# PART 36 — ⭐ THE NORMATIVE WIRE SPECIFICATION
# ═══════════════════════════════════════════════════════════════

**This Part is the single place where every correction is already applied.** It is written for
someone building a reader who does not want to reconcile three captures against a static analysis
themselves. Everything here is either 📐 MEASURED or explicitly flagged as not.

Parts 1–21 are the derivation. Parts 33–35 are the evidence. **This Part is the answer.**

## 36.1 Precedence

Where two Parts of this document disagree, resolve in this order:

```
Part 36  (this Part — merged and normative)
   ^
Part 35  (88,936 attributed exchanges, raw)
   ^
Part 34  (250 attributed exchanges, 16 commands, deduplicated)
   ^
Part 33  (1,353 attributed exchanges, 4 commands)
   ^
Parts 1-21  (static analysis + the app's own files and logs)
```

with two standing exceptions:

- **A decompiled expression outranks any prose that summarises it**, including prose in this Part.
  This is the C32/C33 lesson (§0.6): `avail = frame[5] − 1` was right for the whole project while
  the sentence beneath it was wrong.
- **The application's own exported files outrank a capture for at-rest record layouts.** The PMD
  hex ↔ SQLite cross-reference (Part 9) is byte-for-byte proof; a capture of an idle machine shows
  you a valid record full of zeros.

## 36.2 Layer 1 — the socket and the gateway record 📐

### 36.2.1 Endpoints and socket setup

```
Gateway host      192.168.222.16          <- NOT the .17 in PROVISsettings.ini
Gateway port      1789                    <- requests go here
Local bind        0.0.0.0:1789            <- send FROM 1789, receive ON 1789
```

🔴 **Three socket rules, each of which silently produces zero data if broken:**

```c
/* 1. Bind :1789. The app sends FROM 1789 TO 1789, and the gateway replies TO 1789. */
bind(fd, {INADDR_ANY, 1789});

/* 2. Do NOT connect(). The gateway answers from an EPHEMERAL source port that varies
 *    between sessions (34686 and 50375 observed). A connected socket makes the kernel
 *    drop every reply before your code sees it.                                       */

/* 3. Filter on HOST, never on port. [Ethernet] LastPort=1799 and LastUsedPort=1793 in
 *    the reference INI match neither observed port; they are PROVIS3's own persisted
 *    values and are irrelevant to the gateway.                                        */
recvfrom(fd, buf, sizeof buf, 0, &from, &flen);
if (((struct sockaddr_in *)&from)->sin_addr.s_addr != gateway_ip) continue;
```

### 36.2.2 Datagram → records

A datagram is a **batch** of 36-byte records. 📐 Every datagram in every capture is an exact
multiple of 36 (181,309/181,309 in capture 3 alone).

| direction | records per datagram | max datagram |
|---|---|---|
| app → gateway | **always exactly 1** | 36 B |
| gateway → app | **1 to 15** | **540 B** |

🔴 **You must loop over records.** A 15-record burst occurs 131 times in a 3,397-packet file, and
in capture 1 a reader assuming one record per datagram loses **~64% of all frames**. Receive
buffer ≥ 1500; 540 is the observed maximum, not a specification limit.

Split from the **front**, as `Scan4CANmsg` does: `QByteArray::remove(0, size % 0x24)` trims the
remainder off the head, not the tail.

### 36.2.3 The 36-byte record — corrected field map 📐

Big-endian throughout the container. Verified across 194,006 records, both directions.

```
off   size  field                          observed
0x00   2    length (BE)                    0x0024 = 36        constant, 194006/194006
0x02   2    message type (BE)              0x0080 = CAN frame constant, 194006/194006
0x04   8    tag / client handle            all zero, both directions
0x0C   8    timestamp (BE, microseconds)   answers: monotonic; requests: zero
0x14   1    CAN channel                    0 — constant
0x15   1    DLC                            2..8
0x16   1    flags                          0 — constant (no RTR/extended/error frame)
0x17   1    reserved                       0 — constant
0x18   4    CAN-ID (BE, 32-bit)            0x501/0x502 requests, 0x581/0x582 answers
0x1C   8    DATA[0..7]                     DLC bytes significant, remainder zero
```

> ### ⚖️ X1 🔴 STOP — the `timestamp_be` field in the struct below is wrong as declared
>
> The row above and the `uint64_t timestamp_be` in the struct treat `+0x0C..0x13` as one 64-bit
> big-endian integer. **It is not.** `+0x0C` holds the **LOW** dword and `+0x10` the **HIGH**
> dword, each big-endian — low first. Reading it as a single BE `u64` produced
> `12,302,785,157,688,983,949 µs` in a real reader (§23.4, §23.4.1).
>
> This Part's own prose already says so: §36.2.4 below notes the counter *"wraps every 71.6
> minutes"* at `+0x0C..0x0F`, and 2³² µs = 4,294.97 s = 71.58 min — which is only true if that
> dword is the low half. §33.2 likewise reads it as *"`0x0C` (low dword) / `0x10` (high dword)"*.
>
> **Implement:** `ts_us = ((uint64_t)be32(rec+0x10) << 32) | be32(rec+0x0C);`
> Everything else in the struct is confirmed by both editions.

```c
#pragma pack(push,1)
typedef struct {
    uint16_t length_be;      /* 0x0024 */
    uint16_t msgtype_be;     /* 0x0080 */
    uint8_t  tag[8];         /* zero on this installation */
    uint64_t timestamp_be;   /* gateway µs uptime counter — answers only */
    uint8_t  channel;        /* 0 */
    uint8_t  dlc;            /* 2..8 */
    uint8_t  flags;          /* 0 — reject nonzero until understood */
    uint8_t  reserved;       /* 0 */
    uint32_t can_id_be;      /* read the FULL dword, not the word at +0x1A */
    uint8_t  data[8];
} GatewayRecord;             /* 36 bytes */
#pragma pack(pop)
```

⚠️ **Read the CAN-ID as a 32-bit big-endian dword at `+0x18`**, not as a word at `+0x1A`. The word
form is correct for the 11-bit identifiers this installation uses and would silently truncate a
29-bit extended identifier. It costs nothing to read the dword.

✅ **This is the standard PEAK PCAN-Ethernet Gateway UDP frame, field for field.** Recognising
that is worth more than the individual fields: the transport is a documented, off-the-shelf,
vendor-standard container, so a reader can be written against the vendor specification and be
right about the cases these captures do not contain — 29-bit identifiers, RTR frames, error
frames and multi-channel gateways.

### 36.2.4 The gateway timestamp — use it 📐

`+0x0C` is a **64-bit big-endian microsecond counter** written by the gateway on every answer.

| property | value |
|---|---|
| drift against capture wall clock | **+8.5 ppm** over 3,836.7 s |
| monotonic under BE / under LE | 8,305 / 8,549 vs 3,032 / 8,549 — **BE, decisively** |
| value at first frame (capture 2) | 1,643,471 s ≈ **19.02 days** |
| value at first frame (capture 3, ~18 h later) | ≈ **19.77 days**, never reset |

**Key ordering on this field and use the host clock only to anchor the epoch once per session.**
It is far better than packet arrival time for jitter and interval work, because answer frames
arrive batched.

⚠️ It is an **uptime counter, not a date.** It orders and measures intervals; it cannot date
anything without an anchor.

🔴 **The low word wraps every 71.6 minutes** — visible in capture 2 as the high word stepping
382 → 383. **Use all 64 bits**, not just `+0x0C..0x0F`.

⚠️ Capture 3's shorter window gives −23 ppm against capture 2's +8.5 ppm. A 143-second baseline is
too short to pin the sign; that disagreement is host-clock jitter, not device instability. Take
the longer-baseline figure. The operative point is that the counter tracks real time to within
tens of ppm.

## 36.3 Layer 2 — CAN addressing, framing and reassembly 📐

### 36.3.1 CAN-ID: two bases, split by direction

```c
#define CANID_BASE_TX  0x500   /* 1280 — PC → gateway : requests */
#define CANID_BASE_RX  0x580   /* 1408 — gateway → PC : answers  */

unit      =  id & 0x7F;                  /* 1 .. 15 */
is_answer = (id & 0x580) == 0x580;
```

📐 194,006 records; total split; zero crossovers in any capture. Requests only ever `0x501`/`0x502`,
answers only ever `0x581`/`0x582`.

🔴 **`unit = can_id − 1280` drops 100% of answers**, computes unit 129/130, fails the range check,
and reports no error. If you implement one line from this Part, implement this one.

⚠️ `0x600` is present in `Promos3CanInterface`'s constructor (`this+0x58`) and has **never been
observed on the wire**. Count and log it; do not drop it silently.

### 36.3.2 Request framing

```
DATA[0..2] = 00 00 00                    always; purpose unexplained but 100% stable
DATA[3]    = command
DATA[4..]  = arguments
DATA[n-1]  = checksum
DLC        = 3 + min(5, payload_length)      <-- NOT a constant 8
```

where `payload_length` counts `[cmd][args][checksum]`.

🔴 **Do not zero-pad to `DLC = 8`.** The padding bytes fall inside the checksum's summed range and
will corrupt it. 📐 Observed DLC values are 5, 6, 7 and 8 across 89,186 requests.

**Continuation frames** (`[seq][up to 7 payload]`, seq pre-incrementing from 0) remain 🔶 GHIDRA —
**no multi-frame request occurs in any capture** (filed as D6). Irrelevant to a read-only reader:
every command in the poll set is ≤ 4 payload bytes.

### 36.3.3 Answer framing and reassembly — the corrected rule

```
DATA[0]        = sequence, 0,1,2,… (+1 per frame; wrap at 256 is 🔶 GHIDRA, never observed)
DATA[1 .. ]    = payload, (DLC - 1) bytes, CLAMPED to the bytes still expected
DATA[LEN-1]    = checksum, on the final frame, if it fits
```

```c
size_t acc = 0; int avail = 0;
for (each frame of this answer) {
    if (acc >= expected) break;
    if (frame->data[0] != seq_expected++) { /* sequence break: resync, count, do not swallow */ }
    avail = min(frame->dlc - 1, expected - acc);      /* the clamp is load-bearing */
    memcpy(buf + acc, &frame->data[1], avail);
    acc += avail;
}
if (avail == 7) {              /* last data frame was FULL — no room for the checksum */
    take one more frame;       /* it MUST be DLC == 2 */
    checksum = frame->data[1];
} else {
    checksum = frame->data[frame->dlc - 1];
}
```

📐 **88,936 / 88,936 = 100.0000%.** The two superseded forms:

| rule | agreement | why it fails |
|---|---:|---|
| **clamped `avail == 7`** | **88,936 / 88,936** | — |
| `expectedSize % 7 == 0` | 88,925 / 88,936 | 11 counter-examples, all 1,001-byte `0x16` answers |
| "last frame had `DLC == 8`" | 88,933 / 88,936 | 3 counter-examples at 41 bytes, where `DLC = 8` but clamped `avail = 6` |

🔴 **Completion is `accumulated == expected`. There is no frame-count formula** — the device may
insert a short frame at any 250-byte boundary, so `ceil(n/7)` is withdrawn (§0.6 C34). Stop on the
byte count, never on a frame count.

**Why short mid-stream frames exist:** the device flushes its transmit buffer every **250 payload
bytes**. 📐 33 short mid-stream frames, at cumulative payload 251, 501 and 751 bytes. For `0x16`
that is exactly 25 rows, so whether the trigger is a byte buffer or a row block is undecidable from
this data (D9).

### 36.3.4 Distinguishing a `DLC == 2` frame

Both a device-error answer and a checksum-only frame are `DLC == 2`. **The discriminator is
`DATA[0]`, the sequence byte:**

| frame | `DATA[0]` | `DATA[1]` |
|---|---|---|
| device error | **0** (it is a whole message) | 1 |
| checksum-only | **≥ 1** (it is the last frame of many) | the checksum |

📐 All 10 checksum-only frames observed carry `DATA[0] = 2`. **0** device errors occur in any
capture. This matches the decompiled guard `frame2[5] == 2 && frame2[6] != 0` exactly.

🔴 A reader keying on `DATA[1] == 1` alone misreads roughly 1 in 256 checksum-only frames as a
device error. A reader keying on `DLC == 2` alone cannot tell them apart at all.

### 36.3.5 The checksum

```c
/* group 0/1 (MC_) — this installation */
checksum = -( unit + Σ request_bytes[0 .. n-2] + Σ answer_payload ) & 0xFF;

/* equivalently, if you already hold the request's checksum: */
ck_answer = (ck_request - Σ answer_payload) & 0xFF;

/* group 2 (MC3_) — other installations */
checksum = -1 - Σ message_bytes;      /* ⟺ Σ(all bytes incl. checksum) == 0xFF */
```

📐 **178,370 samples across both directions and all three captures. Zero failures.**

The `n − 2` is decisive and independently required by the bytes: it proves the last byte of a
request is that request's own checksum. All three plausible alternative seedings score **0 / 250**:

| hypothesis | ok / 250 |
|---|---:|
| omit the unit seed | 0 |
| unit seed, but ignore the request bytes | 0 |
| include the request's own trailing checksum | 0 |

🔴 **Use the checksum to validate an attribution you already have. Never to derive one.** As an
oracle it fails completely — a single unpaired answer admits ~48 consistent `(command, args)`
candidates (§C.12). As a validator it is excellent: it caught a real mis-pairing in capture 2 that
length alone accepted.

⚠️ The checksum is appended **before** framing, so on a long request it lands wherever the frame
split puts it — not at a fixed position within a frame.

### 36.3.6 Timing budget 📐

| quantity | measured | design to |
|---|---|---|
| request → first answer frame | median 1.17–1.93 ms; p99 ≤ 2.9 ms; **max 9.8 ms** | — |
| inter-frame gap within an answer | median **151 µs** (p10 143, p90 168) | — |
| longest answer stream time | 144 frames × 151 µs ≈ **22 ms** | — |
| `[CAN] unitAnswerTimeout` | 300 ms — a **31× margin** | **50 ms is ample** |
| master pacing | request every **~1.5 ms**; 8-request cycle **12.64 ms** | not 3 ms |

🔴 **Arm the receive deadline on the LAST FRAME RECEIVED, not on the request.** A 144-frame answer
streams for ~22 ms and would breach a naïve request-anchored 20 ms deadline.

## 36.4 Layer 3 — expected answer sizes 📐

🔴 **Do not ship `Geraet_expectedRecordSize`'s table.** Of the entries measurement could test, only
`0x0E` survives. Use this table. Sizes are **payload bytes excluding the checksum** — exactly the
value stamped into `Paket+0x14`. Identical on units 1 and 2 in every case.

| cmd | name | **size** | binary's table | verdict |
|---|---|---:|---:|---|
| `0x01` | `GIVESTATUS` | **2** | *(absent)* | measured (closes D3) |
| `0x02` | `GIVEGTYPE` | **3** | 14 | 🔴 table wrong |
| `0x05` | `GIVEUSEDZYKTAB` | **32** | 16 | 🔴 table wrong |
| `0x06` | `GIVEKONFIG` | **14** | *(absent)* | measured |
| `0x08` | `GIVEPLCVALUES` | **5** | 1 | 🔴 table wrong (closes D4) |
| `0x0D` | *(unnamed — `SGeraetRec`)* | **66** | *(absent)* | measured |
| `0x0E` | `GIVEKANAL` | **144** | **144** | ✅ exact agreement |
| `0x0F` | `GIVEZYKLUS` | **170** | 40 | 🔴 table wrong |
| `0x12` | `GIVEALARM` | **17** | *(guessed 2)* | measured (closes D3) |
| `0x14` | *(unnamed)* | **36** | *(0x24 fallback)* | ✅ consistent |
| `0x16` | `GIVESAMMELMERKMALE` | **`DATA[1] × 10 + 1`** | *(formula)* | ✅ formula confirmed |
| `0x1A` | `GIVEHARDWAREREC` | **46** | *(46, filed at `0x10`)* | ✅ resolved in favour of the name |
| `0x23` | `GIVE_SENSORVALUES` | **14** | *(absent)* | measured |
| `0x25` | `GIVE_ACTZYKINDEX` | **3** | *(absent)* | measured |
| `0x29` | *(unnamed)* | **40** | *(absent)* | measured |
| `0x33` | `GIVEPROGID` | **2** | *(absent)* | measured |
| `0x1B` | `GIVESIGNALVERLAUF` | 🔴 **UNKNOWN** | *(257, synthetic)* | **never observed — D5** |

**The `0x16` formula, stated exactly:**

```
expected = DATA[1] * recordSize + 1
recordSize = featureCount * 2 + 2          /* = 10 for 4 features */
             + 2 more when GeraetTyp == 'H' (0x48); this box is 'D' (0x44)
```

📐 88,936/88,936, including every 1,001-byte case. `recordSize = 10` is `4 × 2 + 2` — the four
PROCUR-S features, arrived at independently from the wire.

🔴 **For any command not in this table, do not guess. Let the exchange time out.** A timeout is a
loud failure; a wrong `expectedSize` is a silent one that consumes the *next* answer's frames —
the exact corruption reproduced in §18.1 case C.

## 36.5 The reader change-list — merged and final

Supersedes §17.5, §C.15 and §D.10. 🔴 items are the difference between receiving data and
receiving nothing.

```
=== DELETE ===============================================================
DELETE  parse_message_header()          - no header exists on the MC_ wire
DELETE  the "short frame ends the message" heuristic  - provably corrupts (§18.1)
DELETE  reasm_expected_len()'s fallback - replaced by the measured size table
DELETE  any test on (expectedSize % 7)  - superseded by the clamped-avail rule
DELETE  any frame-count formula         - no closed form exists
DELETE  any 3-base CAN-ID probe dimension

=== 🔴 BLOCKING FIXES ====================================================
🔴 FIX  CAN-ID: TWO bases. TX 0x500+unit, RX 0x580+unit.
        unit = id & 0x7F;  is_answer = (id & 0x580) == 0x580
        ("unit = id - 1280" drops 100% of answers)

🔴 FIX  socket: bind :1789 UNCONNECTED. Do not connect() to the gateway.
        Accept from any source port; filter on source HOST only.

🔴 FIX  gateway host is 192.168.222.16, not the .17 in the INI.

🔴 FIX  gw_parse_record(): CAN-ID is a 32-bit BE dword at +0x18, not a word at +0x1A.
        DLC +0x15, channel +0x14, flags +0x16 (reject nonzero until understood).

🔴 FIX  request framing: LEN = 3 + min(5, payloadLen). Do NOT zero-pad to 8 -
        the padding is inside the checksum's summed range.

🔴 FIX  reassembly: payload per frame = DLC - 1, CLAMPED:
            avail = min(DLC - 1, expected - accumulated)
        NOT the constant 7. Short mid-stream frames occur at 250-byte boundaries.

🔴 FIX  checksum placement: after the last payload byte,
            if (avail == 7) -> ONE more frame follows: [seq][checksum], DLC must be 2
            else            -> checksum is DATA[DLC-1] of the frame just consumed

🔴 FIX  completion: stop when accumulated == expected. Never on a frame count.

=== ADD ==================================================================
ADD  per-unit request tracker: {command, expectedSize, sentBytes, deadline, attempts}
ADD  datagram loop: up to 15 records (540 bytes) per answer datagram.
ADD  expected sizes from the MEASURED table (§36.4). Unknown command -> do not
     guess; let it time out.
ADD  0x16 expected = DATA[1] * 10 + 1   (recordSize = featureCount*2 + 2)
ADD  answer checksum verification -(unit + Σreq[0..n-2] + Σpayload).
     Use it to VALIDATE attribution, never to derive it.
ADD  DLC==2 disambiguation by DATA[0]: error is seq 0, checksum-only is seq >= 1.
     Do NOT key on DATA[1]==1 alone.
ADD  timestamp: read the 64-bit BE microsecond counter at +0x0C. Use it for
     ordering and intervals; anchor to the host clock once per session.
     Handle the low-word wrap every 71.6 min (use all 64 bits).
ADD  receive deadline armed on LAST FRAME RECEIVED. 50 ms is ample.
ADD  handle a 144-frame / 1001-byte answer without special-casing.
     Losing it means losing the backlog bursts - the densest data on the wire.
ADD  0x16 row decode, stride = featureCount*2 + 2:
        [Min_F0][Max_F0][Min_F1][Max_F1][Min_F2][Max_F2][Min_F3][Max_F3][st0][st1]
     escape: row[0] == 0xFF -> row[1] is the marker (0xFB reset observed),
             the NEXT row carries the parameter.
     Do NOT treat 0xFF in a Max byte as an escape - that is saturation.
ADD  integrity check: in a non-escape row, min > max means the reassembly is wrong.
     Free, and it catches exactly the class of bug the %7 rule would have caused.
ADD  feature names from SKanalRec (0x0E) at body +0x4D, stride 12,
     [mask][11-byte NUL-padded name]; index = log2(mask & 0x0F).
     NEVER hard-code names. Treat 0x80 as a separate flag.
ADD  alarm timestamps from 0x12 body +0x0A..0x0F = D,M,Y,h,m,s (year +2000).
ADD  0x0D as the discovery command: one 66-byte SGeraetRec gives model, channel
     count, sensor complement and ReduzLim in a single exchange.
ADD  --record / --replay (~50 lines) - and then run it against the capture corpus
     in §36.7 before ever booking a machine window.

=== NOTE =================================================================
NOTE master pacing: the app issues a request every ~1.5 ms, not 3 ms;
     a full 8-request cycle over 2 units takes ~12.6 ms.
NOTE error/retry/abort paths are UNVERIFIED - zero occurrences in 88,936
     exchanges. Test them by INJECTION, not by capture.
NOTE do not poll a unit PROVIS3 is also polling. Stop PROVIS3 or aim elsewhere.
     Collision symptom: "Trying to send several Canbus commands before answer
     is received".

=== KEEP =================================================================
KEEP the CONF_* honesty gating. It is why the early header mistake was loud
     rather than silent, and it should survive every rewrite.
KEEP Scan4CANmsg's front-trim behaviour - already correct.
```

`promos3_msg_t` loses `group` / `command` as **parsed** fields and gains them as **attributed**
fields, plus a `bool attributed` that is false whenever no request was observed.

### 36.5.1 The 30-second test, corrected

The datagram is byte-confirmed by capture. **Three changes to the procedure**, any one of which
turns a working device into an apparently dead one:

```
Send to  192.168.222.16 : 1789          <- .16, not .17
From     a socket bound to :1789, NOT connected
Expect   the answer on CAN-ID 0x581     <- not 0x501

36-byte record:
  00 24 00 80 00 00 00 00 00 00 00 00 00 00 00 00
  00 00 00 00 00 06 00 00 00 00 05 01 00 00 00 08
  01 f6 00 00
                 ^ DLC 6      ^ CAN-ID 0x501   ^ DATA 00 00 00 08 01 f6
```

This is `MC_GIVEPLCVALUES`, unit 1, station 1 — the one request whose exact bytes were
independently verified against the runtime log before any capture existed, and every field of
which the captures confirm.

**Expected reply, now known rather than hoped for:** **5 payload bytes**, `00 00 00 00 ff`, in a
single frame with `DLC = 7`, on CAN-ID `0x581`, arriving in **1–2 ms**.

🔴 **And note what §17.2's original closing sentence would have cost you.** *"If nothing comes
back, that is a real result"* is exactly the wrong inference to draw from a connected socket: the
device answered, the kernel discarded the reply, and the operator concludes the link is dead.

## 36.6 Final gap register

| # | Gap | Static phase | **Final** | State |
|---|---|---|---|---|
| G1 | Message header wire layout | 100% ✅ | **100%** ✅ | Closed **by deletion** — and confirmed on the wire: `GIVEKONFIG` answers `e5 01 04 …` at payload offset 0 with nothing in front of it |
| G2 | Completion rule + size table | 100% ✅ | 🔴 reopened → **100%** ✅ | The rule was right in the code and wrong in the prose; corrected form verified 88,936/88,936. **The table's contents are refuted** — use §36.4 |
| G3 | Request side / master role | 100% ✅ | **100%** ✅ | Poll cycle and cadence now measured rather than inferred; `LEN` rule refined |
| G4 | Capture strategy / CAN-ID base | 100% ✅ | 🔴 reopened → **100%** ✅ | v3's answer was wrong. Two bases. Closed on measurement rather than on inference |
| G5 | Checksum | 100% ✅ | **100%** ✅ | Both directions, 178,370 samples, 0 failures. The last open assumption in the project |
| G6 | Record-layout versioning | 20% | **20%** | Untouched. `FUN_004c5c70` still unread; judged low value while one firmware is in scope. `0x0D` supplies the version-stamped record if wanted |
| G7 | `MC_` body layouts | ~65% | **~80%** | 9 of 38 decoded, including both live commands. The rest are config writes already available in SQLite |
| G8 | Limits and the "%" display | 70% | **75%** | `CDRLim` confirmed on the wire; the limit *load* into the reader is still not written. ~1 day of work |
| G9 | `channelKey` → feature index | 60% | **~90%** | Descriptor side proven: `mask & 0x0F` is one-hot, index = `log2`. Only the request-side `channelKey` for `0x1B` is untested, because `0x1B` never ran |
| G10 | Unit ↔ serial ↔ model | 100% ✅ | ⚠️ **90%** | Model ✅ (`MSL5081-16`, 1-based). **Serial source not found** — the serials appear nowhere in any capture in any byte order, so `GIVEGTYPE` is not their source |
| G11 | Device-side timestamps | 50% | **~95%** | Sub-second ordering from the gateway µs clock; wall-clock dating from the `0x12` alarm record's D-M-Y h:m:s |
| G12 | Reader robustness | 80% | **85%** | The replay corpus G12 has wanted since the gap register opened now exists (§36.7). xlsx durability still flushes only on clean exit |
| G13 | *(what is NOT missing)* | — | see §16.4 | — |
| ~~D3~~ | Sizes for `0x01`, `0x12`, `0x1B` | measurement needed | **2 of 3 closed** | `0x01` = 2, `0x12` = 17. `0x1B` re-filed as D5 |
| ~~D4~~ | The `0x08` size branch | measurement needed | ✅ **CLOSED** | `n = 5`. `Geraet[0x4e6] ∈ {0x05, 0x14, 0x23, 0x32, 0x41, 0x50}` — and **a reader does not need to know which**, it needs `n` |
| **D5** | `0x1B` size and body | — | 🔴 **OPEN — highest value** | Absent from 6 sessions. Not in the poll loop; fetched only when the operator opens the signal-trace view |
| **D6** | Multi-frame request continuation | — | open | No request > 8 bytes in 89,186. Irrelevant to a read-only reader |
| **D7** | Error / retry / abort paths | — | open | Zero occurrences in a clean link. **Must be tested by injection** |
| **D8** | Sequence wrap past 255 | — | open | Needs an answer ≳ 1,785 bytes; none exists |
| **D9** | The 250-byte flush boundary | — | ⚠️ characterised, not explained | Byte buffer or 25-row block? Undecidable from `0x16` alone |

**Aggregate: protocol knowledge ≈99.7%; a correct end-to-end reader ≈93%.**

### 36.6.1 Minor open assumptions

Carried forward from §16.3, with their post-capture status:

| Assumption | Status |
|---|---|
| Answer-direction checksum seed symmetric with the request | ✅ **CLOSED** — measured, and the only variant that works |
| Device-error `LEN == 2` constraint | ⚠️ **Refined, not closed.** `DLC == 2` is necessary but not sufficient; `DATA[0]` is the real discriminator. Zero device errors observed, so still unverified |
| `Geraet+0x688` — request byte 2 of `0x16` | ⚠️ still unknown; sent as 0 |
| The 3 reserved bytes at the head of a request | ⚠️ purpose unexplained, but 📐 **100% stable at `00 00 00`** across 89,186 requests |
| `Paket_setPriority(…, 2)` | harmless while one request is outstanding |
| `MC3_` field-descriptor attributes `A` and `B` | ⚠️ still interpreted (size vs type); needs one raw `MC3_` frame, and no `MC3_` box was captured |
| Which of `EthThread_initFromIni` / `EthThread2_initFromIni` is called from where | ⚠️ pending an xref check; non-blocking |
| Size-table entries `0x03`, `0x10`, `0x3f` misaligned with command names | ✅ **Explained** — the table is keyed by **record type** for those entries. `0x0F`→170 is the `SZykRec` size filed at `0x03`; `0x1A`→46 is the `SHardwareRec` size filed at `0x10` |
| `0x16` status bytes `+8` / `+9` | ⚠️ four values each in 15,521 rows; meaning not established |
| Century in the `0x12` alarm date | ⚠️ field carries 19–25; `+2000` is the only sane reading but is not proven by these bytes |
| `MC_` alarm body layout (§6.4) | ⚠️ still `MC3_`-derived and **PROVISIONAL** — but `0x12`'s *timestamp* block is now measured |

**Every size doubt degrades into a timeout, not corruption.** The request tracker catches it, the
counters record it, and nothing reaches the output as a plausible-looking lie. That is what the
`CONF_*` gating was built for.

## 36.7 The replay corpus

**Three capture files now exist, and together they are a complete offline test harness.** This
closes the "highest-value missing tool" item that has stood open since the gap register was
written — record/replay was ~50 lines of code and no corpus; now the corpus is the hard part and
it is done.

| File | Nature | Value |
|---|---|---|
| `JULY5_IMP1.pcapng` | 21 s, 4,039 packets, 1,353 exchanges, 4 commands | The pairing model's first test; per-unit demultiplexing |
| `ALL_merged__uniq.pcapng` | deduplicated, 3,397 packets, 250 exchanges, **16 distinct commands** | **Breadth.** One example of every exchange kind the installation produces |
| `july_6_packet1.pcapng` | raw, 183,997 packets, **88,936 exchanges**, 143 s | **Depth.** The poll loop at full rate, 12 long-answer bursts, 64 escape rows |

**A reader is correct on everything this installation does — except `0x1B` and the error paths —
if it can:**

1. decode all 250 attributed exchanges from the breadth file and all 88,936 from the depth file;
2. verify **89,186 request checksums** and **89,184 answer checksums**;
3. reproduce the §36.4 size column;
4. decode **15,521 measurement rows** with **zero `min > max` violations outside the 64 escapes**;
5. handle a **144-frame / 1,001-byte** answer without special-casing;
6. survive a **15-record / 540-byte** datagram.

**None of that needs a machine window.**

⚠️ **One caveat on the breadth file.** It is a deduplicated merge, so **adjacency is synthetic** —
two frames next to each other in the file were not necessarily adjacent on the wire. All timing in
Part 34 is derived from the gateway's own hardware timestamp, which the merge preserves, and none
from packet adjacency. It also contains 146 exchanges with no request (a dedup artefact that
turned into a useful natural experiment, §C.12) and one truncated `0x16` answer.

⚠️ One session inside the breadth file (`packets_july5`) shows the PC answering 634 ICMP
port-unreachable messages, i.e. **PROVIS3 was not bound to 1789 while it ran**. The CAN payloads
survive intact inside the ICMP quotations, but the session is one-sided and carries no requests.
Usable for framing checks only; excluded from every attributed statistic.

## 36.8 The one action that unblocks the most

**Someone stands at the HMI and opens the signal-trace view while a capture runs.**

That is it. Five minutes, no equipment beyond what already produced three captures.

`0x1B GIVESIGNALVERLAUF` is the live amplitude trace — the black bars, the thing the whole reader
exists to display — and it has been absent from **six capture sessions across three files**. The
reason is now understood: **it is not part of the steady-state poll loop.** The app fetches it only
when an operator opens that screen. No amount of additional idle capture will produce it.

What that one action closes:

- **D5** — the size and body of `0x1B`, the last genuinely unknown command;
- **G9** to 100% — the request-side `channelKey` encoding, which currently has three candidate
  interpretations and whose wrong choice **mislabels every plotted bar with a plausible-looking
  name**;
- the `mode` / aux-context question in §6.1 — which feature a given trace answers for;
- probably the `0x00` (new cycle) and `0xFE` (workpiece ID) escape markers in `0x16`, plus the
  double-buffering behaviour that depends on them, if the machine is also **cutting**.

**A capture taken while the machine is actually cutting is worth more than a longer idle one.**
Every capture so far was of an idle or steady-state cell: 1,058 of 1,058 measurement rows all-zero
on one unit, `GIVESTATUS` and `GIVEPROGID` returning `00 00` on 11,117 consecutive polls, zero
`0xFF` escape bytes in capture 1, no cycle boundary and no workpiece change in any window. **The
link layer is fully verified. The body layer is verified only for the fields that a stationary
machine happens to populate.**

The second-highest-value action is unglamorous: **fault injection**, to exercise D7. The retry
ladder, the abort path and the error-answer frame are specified from code and have never once
fired on a healthy cell. A reader's error handling cannot be validated against any capture that
exists or is likely to exist.

---

# ═══════════════════════════════════════════════════════════════
# PART 37 — DOCUMENT LINEAGE & ARCHIVE
# ═══════════════════════════════════════════════════════════════

**Question this Part answers:** *I am holding one of the fifteen source documents. What in it is
still true, what was overturned, and where did its unique content go?*

Part 20 is the supersession log — it lists **claims**. This Part lists **documents**. Between them
they mean nothing in the corpus is orphaned.

## 37.1 The lineage

```
SESSION 1  PROVIS3_MASTER_REPORT.md ........ v1, the first full receive-path recovery
           promos3_protocol_map.md .......... the command vocabulary
           PROVIS3_architecture.md .......... the architecture/protocol map
                    │
                    ▼
           analysis_jul_28_1_0_0.md ≡ PROVIS3_MASTER_REPORT_v2.md ...... v2
                    │        (byte-identical files — one document, not two)
SESSION 2  ├── analysis_appendix_datamodel.md ..... Appendix A
           └── analysis_appendix_B.md ............. Appendix B
SESSION 3  ├── analysis_part15_gap_register.md
SESSION 4  ├── analysis_part16_mc_answer_protocol.md
           ├── analysis_part17_session_handoff.md
SESSION 5  └── analysis_part18_session_report.md
                    │
                    ▼
SESSION 6  PROVIS3_consolidated_report_v3.md ........ merges the seven above
           analysis_part19_capture_verification.md .. FIRST CAPTURE
SESSION 7  analysis_appendix_C_wire_capture.md ...... SECOND CAPTURE
SESSION 8  analysis_appendix_D_poll_loop_capture.md . THIRD CAPTURE
                    │
                    ▼
           THIS DOCUMENT (v4.0)
```

Two structural facts about the corpus worth stating plainly:

1. **`analysis_jul_28_1_0_0.md` and `PROVIS3_MASTER_REPORT_v2.md` are byte-identical**
   (md5 `5611bc88…`). They are one document under two filenames, not two sources.
2. **`PROVIS3_consolidated_report_v3.md` appears twice** in the project (once in the uploads,
   once in the project files) and is also byte-identical to itself. Same document.

## 37.2 Per-document disposition

### 1. `PROVIS3_MASTER_REPORT.md` — report v1 ⚠️ SUPERSEDED

*The first end-to-end recovery. Its receive-path skeleton survives essentially intact; its
protocol-header model and its feature names do not.*

| What it said | Disposition |
|---|---|
| The full receive path, `Scan4CANmsg` → unit routing → reassembly → dispatch → decode | ✅ **Stands.** Now §1.2 |
| Endianness split (BE transport, LE payload) | ✅ **Stands and measured.** §2.1 |
| The 36-byte gateway record; "gw_header discarded" | ⚠️ Structurally right, **field map corrected** — the header carries a µs timestamp (§0.6 C27) |
| `[command byte NN][length][payload]` message header, "exact field order INFERRED" | 🔴 **CORRECTION — no header exists on the `MC_` wire** (§0.6 C1, Part 20 §20.1). The open item closed *by deletion* |
| Features `SPINDEL / X AXIS / Y AXIS / Z AXIS`, masks `0x81/0x82/0x84/0x88` | 🔴 **CORRECTION — per-install** (§0.6 C12, Part 20 §20.7). Ironically 📐 **capture 2 shows unit 1 carrying exactly these names and masks** — so v1 was describing a real machine, just not the one its own PMD files came from |
| Scaling: "physical = raw × factor, read `SFactors.ini`" | 🔴 **CORRECTION — no factor exists** (§0.6 C13, Part 7). `SFactors.ini` is not present on this install and the app runs fine without it |
| "0–300 display axis implies scaling" | 🔴 **CORRECTION** — that is `Trend.Work_Val`, a cycle-position quantity (Part 20 §20.21) |
| The complete function index (§8.1–8.14) | ✅ **Restored in full** — v3 dropped 57 of these; they are back at **§13.16** |
| `SZykRecV4802` offset map and the `14 14 14 14 … 0a 0a 0a 0a 00` trailer | ✅ **Restored** at §9.3 — v3 omitted it |
| Full `SKanalRecV40` and `SGeraetRec` C structs | ✅ **Restored** at §9.1–9.2 |
| `SGrenzRec` full column mapping incl. `Act_End ≈ 250/251` | ✅ **Restored** at §9.3 |
| Tooling: `promos3_listen.c`, `promos3_records.h`, `promos3_sniff.c` | Superseded; see §17.6 and §37.3 |

### 2. `promos3_protocol_map.md` ⚠️ PARTLY SUPERSEDED

*The command vocabulary. Still the best single source for the decimal `Kom_NN` convention.*

| What it said | Disposition |
|---|---|
| The legacy `MC_` decimal command table (~40 entries) | ✅ **Restored in full** at **§5.2.1**, cross-checked against the hex dispatch table. It supplies two names the hex table lacks (`0x1E MC_SETMUSTER`, `0x26 MC_SET_EINZEL_TEACH`) and 📐 all four polled commands match |
| The `MC3_` decimal command table | ⚠️ **Superseded as an authority** by the binary's own registry (§5.3.1), but **restored** at §5.2.2 because it records the `Sende_Kom_NN` tag numbering |
| `MC3_` `0x11 = MC3_SENSOR_VFAKT` | 🔴 **CORRECTION** — the registry puts VFAKT at `0x0b` and `MC3_LAST_SIGNAL` at `0x11` (§0.6 C10) |
| Unresolved `MC3_` token list | ✅ **Restored** at §5.2.2. All but four were resolved by the registry; `MC3_GET`, `MC3_GET_DATE`, `MC3_SET_DATE`, `MC3_SET_MODE` remain unplaced |
| Full EventCode ring (17 entries) | ✅ **Restored** at §8.5 — v3 carried 9 |
| ChannelStatus with the blank slot 4 | ✅ **Restored** at §8.3 |
| Full sparse SensorType ring | ✅ Already in §8.2 |
| Trend/streaming command family | ✅ **Restored** at §5.2.1 |
| §7 "what remains unknown": the datagram outer framing | ✅ **Closed.** §36.2, and it needed neither Ghidra alone nor Wireshark alone — it took both |

### 3. `PROVIS3_architecture.md` ⚠️ SUPERSEDED

*A condensed architecture map. Almost entirely a subset of v1 and v2.*

Its one unique contribution — the `SZykRec` trailer bytes and the `SGrenzRec` `Act_End ≈ 251`
note — is restored at §9.3. Its closing claim, *"Nothing here required Wireshark. A single capture
would only VALIDATE the transport"*, is **half right and worth remembering**: the capture did
validate the transport, and it also **corrected three blocking facts and one framing rule**
(§0.1). "Only validate" was over-confident.

### 4. `analysis_jul_28_1_0_0.md` ≡ `PROVIS3_MASTER_REPORT_v2.md` — report v2 ⚠️ SUPERSEDED

Fully absorbed into Parts 0–21 by v3, and thence into this document. Its headline open item —
*"exact wire byte-offsets of `[group]/[command]/[length]`"* — closed **by deletion** (Part 20
§20.1). Its scaling resolution (no factor) ✅ stands and has since been confirmed from a third
direction (Part 35 §D.4.2). Its `MC3_` German handler labels are registry aliases (§0.6 C11).

### 5. `analysis_appendix_datamodel.md` — Appendix A ✅ ABSORBED INTACT

The `Promos3DataRecord` domain object and the SQLite/ODBC read path. **Now Part 11, essentially
unchanged** — nothing in it was overturned, and it gained an unexpected confirmation: the `WP_*`
`Min_Sxx / Max_Sxx` envelope it documents from the storage side turns out to be **byte-for-byte
the `0x16` wire row** (§6.2.1). One reconciliation: `FUN_005e1c90` (§0.6 C22).

### 6. `analysis_appendix_B.md` — Appendix B ✅ ABSORBED INTACT

30 SQL/config/receive functions, the `MC3_` command registry, the field-descriptor table. Split
across Parts 5.3, 5.5, 10.1, 12 and 13. Its header claim to close "the Part 13 open item" is a
**RECONCILIATION** (Part 20 §20.26): it closed the *group-2* field-layout question; the group-1
wire-offset question closed later and differently. Its `[Ethernet]` INI table lists **code
defaults**, which differ from the reference deployment on four keys (§0.6 C24) — both are correct.

### 7. `analysis_part15_gap_register.md` ⚠️ SUPERSEDED BY §36.6

Opened G1–G13. **All four items it identified as blocking (G1, G2, G3, G4) are now closed**, and
its central judgement — *"three of them were previously recorded as non-blocking; they are
blocking"* — was correct at the time. Two of its specific calls need flagging:

- Its **§15.5 "weak hint"** — that `0xF6 = ~(0x08 + 0x01)` looked like a one's-complement sum but
  did not fit the 8-byte sample, so *"treat it as untested, not as a finding"* — was **correct and
  correctly hedged**. The hint was right; the 8-byte sample was a *truncated multi-frame request*
  (Part 20 §20.5, §20.15).
- Its **§15.11 prediction** that one capture would close G1 "anchored on `E5 01 04`" was 📐
  **exactly right** (§16.5).
- Its **§15.0(a)** conclusion that "a request is a single CAN frame" was 🔴 wrong — the log dumper
  caps at 8 bytes (Part 20 §20.5). ⚠️ Though note: 📐 across 89,186 captured requests, **every
  single one is a single frame.** The claim was wrong in general and true of everything a
  read-only reader will ever send.

### 8. `analysis_part16_mc_answer_protocol.md` ⚠️ SUPERSEDED, one claim reinstated

The document that discovered *answers carry no command and no group* — **the single most
consequential finding in the project** (§3.2), 📐 confirmed the hard way by Part 34 §C.12. Its
checksum recovery ✅ stands and is now measured at 178,370 samples. Two corrections: `Paket+0x20`
is the aux context, not the wire buffer (§0.6 C6/C7); and its G4 pessimism was reconciled rather
than reversed (Part 20 §20.17).

### 9. `analysis_part17_session_handoff.md` ⚠️ SUPERSEDED, one claim reinstated

⚠️ **Its §11 item 7 — "three CAN-ID bases; `0x580` is the direction discriminator" — was struck by
Part 18 and is now PARTLY REINSTATED.** The strike was right that `0x580` is not a *transmit* base
and that there are not three bases. **It was wrong to conclude that receive shares the transmit
base.** The original instinct about `0x580` was correct (§0.6 C25). Its other corrections stand:
`FUN_005073f0` is not the splitter (§0.6 C5), `Geraet+0x4BC` is the channel count (§0.6 C8),
`FUN_005018f0` is Ethernet (§0.6 C9). Its §8 `0x16` block model was **positionally right and
semantically wrong** — `lo`/`hi` are `(min, max)` (§0.6 C35).

### 10. `analysis_part18_session_report.md` ⚠️ SUPERSEDED on its central claim

Recovered the transmit path byte-exactly — ✅ **and every byte of it is confirmed on the wire.**
Its §3.3 CAN-ID correction is the one entry in this corpus that was **right about what it denied
and wrong about what it asserted** (see item 9). Its §8.2 discovery — that the documented
device-error signature is ambiguous, found by *writing and running* the code rather than reading
it — is 📐 **refined by measurement**: `DLC == 2` is necessary but not sufficient, and `DATA[0]`
is the real discriminator (§36.3.4). Its §11.4 instruction *"do not read more Ghidra"* was
correct; the next useful byte did come from the machine.

### 11. `PROVIS3_consolidated_report_v3.md` ⚠️ SUPERSEDED ON THE WIRE, INTACT ELSEWHERE

Parts 0–21 of this document *are* v3, with correction banners inserted and restored material
merged back in. Its method statement — *"No Wireshark, no packet capture, and no live machine
access was used at any point"* — was true when written and is the reason the measurement phase was
worth doing. **Everything it got wrong is in the transport layer; everything above the transport
layer survived contact with real bytes.** That is an unusually clean division and it is the
headline result of the whole project.

### 12–14. The three capture documents ✅ ABSORBED AS PARTS 22–24

| Original | Now | Numbering |
|---|---|---|
| `analysis_part19_capture_verification.md` ("Part 19") | **Part 33** | `19.x` → `22.x`; cross-refs remapped |
| `analysis_appendix_C_wire_capture.md` ("Part 33 / Appendix C") | **Part 34** | `C.x` **kept** — Part 35 cites them |
| `analysis_appendix_D_poll_loop_capture.md` ("Part 34 / Appendix D") | **Part 35** | `D.x` **kept** |

⚠️ **The original numbering collided three ways** — the first capture document called itself
"Part 19" while v3 already had a Part 19, and the second and third called themselves "Part 33" and
"Part 34". This edition resolves it as above. One internal typo was fixed: Appendix C §C.1 and its
size table cited `§C.11.5` for the `SGeraetRec` section, which is `§C.10.5`.

⚠️ **Part 34 is corrected by Part 35 on two of its own rules** — the `%7` checksum placement and
the `ceil(n/7)` frame count (§0.6 C32–C34). Part 34's conclusions were sound on 250 exchanges and
broke at 88,936, for a reason that is entirely honourable: its longest complete answer was 170
bytes, below the device's first 250-byte flush boundary. **The rules did not hold and then break;
they were never tested.**

## 37.3 Tooling lineage

| File | Origin | State |
|---|---|---|
| `promos3_listen.c` | v1 §11.1 | **Superseded.** Assumed a clean Promos3 body per datagram; the wire is 36-byte records needing split and reassembly |
| `promos3_records.h` | v1 §11.2 | **Superseded** by `promos3_config.*`; its feature-name handling must follow §9.2 (never hardcode) |
| `promos3_sniff.c` | v1 §11.3 | **Retired** under master mode. ⚠️ Would return if passive mode with a port mirror were chosen (Part 20 §20.30) — but §17.1's attribution result argues strongly against that path |
| `promos3_learn.c` | later | **Largely obsolete** — the transmit path is byte-exact |
| `promos3_transport.c` | current tree | 🔴 **Needs the §36.5 rewrite.** Its `out->unit = can_id - PROMOS3_BASE_CAN_ID` is the bug that drops every answer |
| `promos3_decode.c` | current tree | `parse_message_header()` **to be deleted** |
| `promos3_master.c` / `test_master.c` | session 5 | **Written and tested**, 20 assertions passing — ⚠️ *not present in the current project tree; retrieve or rewrite from Part 3 + §36.5* |
| `--record` / `--replay` | never written | **~50 lines, and the corpus now exists** (§36.7). Highest-value remaining tooling item |

## 37.4 What this corpus got right, and what it teaches

Recorded because the *pattern* of the errors is more useful than the errors:

1. **Static analysis was right about everything above the transport layer and wrong about three
   things inside it.** Dispatch, bodies, records, schemas, decoder rings, scaling, the data model
   — all survived. The CAN-ID base, the source port and the gateway header did not. **The layer
   nearest the wire is the layer a binary tells you least about**, because the binary describes
   what it *sends*, and half the protocol is what it *receives*.
2. **`send` cannot testify about receive.** The single worst error in the corpus (§0.6 C25) came
   from reading one direction's function and inferring the other's behaviour, with no
   counter-check. It was then *confirmed* by a settings dialog that also only describes transmit.
   Two agreeing sources, both about the same half of the problem.
3. **Do not promote a constant out of a variable.** `avail = frame[5] − 1` became "7 bytes per
   frame" because 7 was what it always evaluated to in the available samples (§0.6 C32).
4. **Write the code early.** The device-error ambiguity (§0.6 C20) was found by running a test, not
   by reading a function — and static analysis had produced a correct-sounding rule that was
   unusable.
5. **Capture even when the analysis looks finished.** v3 assessed itself at ~99% knowledge and
   ~75% reader. The captures moved knowledge by 0.7 points and the *reader* by 18 — because the
   things still missing were few, small, and each individually fatal.
6. **An idle machine verifies a link layer and teaches you nothing about a body.** Every capture
   so far shows a stationary cell. The link layer is done; the body layer is done only for fields
   a stationary machine populates. That is why §36.8 asks for an operator, not for more bytes.

---

*End of report (v4.0).*

*This document supersedes and contains: `PROVIS3_MASTER_REPORT.md`, `promos3_protocol_map.md`,
`PROVIS3_architecture.md`, `analysis_jul_28_1_0_0.md` ≡ `PROVIS3_MASTER_REPORT_v2.md`,
`analysis_appendix_datamodel.md`, `analysis_appendix_B.md`, `analysis_part15_gap_register.md`,
`analysis_part16_mc_answer_protocol.md`, `analysis_part17_session_handoff.md`,
`analysis_part18_session_report.md`, `PROVIS3_consolidated_report_v3.md`,
`analysis_part19_capture_verification.md`, `analysis_appendix_C_wire_capture.md`, and
`analysis_appendix_D_poll_loop_capture.md`.*

---

# ═══════════════════════════════════════════════════════════════
# PART 38 — THE THREE SOURCE EDITIONS' FRONT MATTER, PRESERVED VERBATIM
# ═══════════════════════════════════════════════════════════════

Each of the three v4.0 editions opened with its own title block, lineage table, consolidation
rules, confidence scale and table of contents. Those were superseded by §0.0.1–§0.0.6 of this
edition, but they are **not redundant** — each records what its author knew and intended at the
time, and two of them contain lineage detail that appears nowhere else. All three are reproduced
here in full, unedited, with their headings demoted so they nest under this Part.

⚠️ **Everything inside this Part is historical.** Where it disagrees with §0.0.1–§0.0.6, the
front matter of this edition is current. In particular, all Part numbers quoted below are in the
*source edition's* numbering — use the concordance in §0.0.3 to translate them.

---

## 38.1 ⟦FIELD⟧ — `PROVIS3_consolidated_report_v4__1_.md` (7 captures, 2026-08-07)

*This block also contains, nested inside it, the complete front matter of consolidated report
**v3.0** — the static-analysis edition that is the common ancestor of all three v4 editions.*

### PROVIS3 / Prometec Monitoring — Consolidated Reverse-Engineering **and Field-Validation** Report

**Version 4.0 — single consolidated edition (supersedes all prior parts and all prior appendices)**

**Target:** PROVIS3 HMI application (Sandvik / Prometec CNC tool-monitoring), 32-bit Qt4
binary, branded for Mazak. App version **3.1.44.4 / "V3.1.44 HF4"**, DB schema **10**.

**Goal:** Recover the device↔HMI communication protocol and data formats completely enough
that a modern 64-bit application can read live sensor telemetry, alarms, configuration and
history **without** the original software, without the PEAK/PCAN hardware, and without the
32-bit dependency chain.

**Method — and what changed in this edition.** Version 3.0 was produced entirely by Ghidra
static analysis cross-referenced against the application's own exported artefacts (SQLite
databases, PMD hex dumps, INI files) and its own runtime logs. It stated, accurately at the
time: *"No Wireshark, no packet capture, and no live machine access was used at any point."*

**That is no longer true, and this edition exists because of it.** Between the first packet
capture and 2026-08-07 the recovered model was tested against **seven packet captures, four
runtime logs, four databases, three INI revisions, a live master-mode run and a UI
screenshot** — an aggregate of **219,994 attributed request/answer exchanges**, **439,988
checksum verifications** and roughly **250,000 decoded measurement rows**. Almost everything
held. Three things did not, and each of the three was the difference between a reader that
works and a reader that runs clean, reports no errors, and produces an empty file.

---

#### About this edition

Version 3.0 merged seven analysis artefacts produced across five working sessions. Version 4.0
merges those, unchanged, with **eight further documents** produced across the live-capture
campaign. Fifteen source artefacts in total.

##### Inherited from v3.0 (static-analysis phase)

| Source document | Session | What it contributed |
|---|---|---|
| `analysis_jul_28_1_0_0.md` (report v2) | 1 | Architecture, transport, dispatch map, payload bodies, scaling, config records, measurement DB |
| `analysis_appendix_datamodel.md` (Appendix A) | 2 | `Promos3DataRecord` domain object, SQLite read path |
| `analysis_appendix_B.md` (Appendix B) | 2 | 30 SQL/config/receive functions, MC3_ command registry, field descriptors |
| `analysis_part15_gap_register.md` | 3 | Gap register G1–G13, reader test evidence, master/slave discovery |
| `analysis_part16_mc_answer_protocol.md` | 4 | MC_ answer framing, checksum, completion rule, MC3_ assembler |
| `analysis_part17_session_handoff.md` | 4 | MC_ command table, size table, request side, unit discovery, architecture |
| `analysis_part18_session_report.md` | 5 | Transmit path, poll cycle, CAN-ID resolution, model string, link-layer code |

##### New in v4.0 (field-validation phase)

Eight documents were produced during the campaign, **all eight of them titled "Appendix F"**.
They overlap, they were written against different captures, and in three places they
contradict each other. They are given stable labels here — **F-a** through **F-h** — and are
used with those labels throughout Parts 22–32. Nothing in any of them has been discarded.

| Label | Source document | Primary artefact | What it contributed |
|---|---|---|---|
| **F-a** | `analysis_appendix_F_capture_validation.md` | 6 datagrams, hand-decoded | First contact with real traffic. Gateway record confirmed byte for byte; six checksum verifications; traffic identified from the rules alone; row-base ambiguity resolved |
| **F-b** | `analysis_appendix_F__1_.md` | the same 6 datagrams, re-parsed mechanically | Corrected gateway field map; the `avail`-clamp branch exercised; `count × recordSize + 1` wire-verified; answer-direction checksum discharged; **the CAN-ID base correction**; a six-datagram regression corpus |
| **F-c** | `analysis_appendix_F__2_.md` | `JULY5_IMP1.pcapng`, 4,039 packets | First bidirectional trace. Frame accounting, request size histogram, seven checksum matches, the reader drop-bug proven. ⚠️ **Contains a systematic direction inversion — reconciled in §22.4** |
| **F-d** | `analysis_appendix_F__3_.md` | `packets_july5.pcapng`, 89,512 frames | 67,018-record single-direction sample; answer CAN-ID base closed at scale; DLC and body-size distributions; the ephemeral-local-port defect; the honest limits of a one-directional capture |
| **F-e** | `analysis_appendix_F.md` | 3 pcapng files, 217,151 records | The consolidated capture analysis: topology, timestamps, measured answer sizes, `0x0E` feature names live from the device, `0x12` event list, ready-to-send request records, two reader tools |
| **F-f** | `PROVIS3_appendix_F_session_report.md` | 7 captures, 219,994 exchanges | **The campaign summary and the most authoritative document of the eight.** The `DLC−1` framing correction, the fully decoded `0x16` measurement block, twelve command bodies, link behaviour, machine state, the reader's own bugs |
| **F-g** | `analysis_appendix_F_control_flow.md` | no new decompilation | Control-flow ownership: who compares the limit, who stops the machine, what a second PROVIS3 does. Opens G14–G17 |
| **F-h** | `analysis_appendix_F_odbc_enablement.md` | Qt plugin acquisition, 2026-08-07 | QODBC back-end enablement: why the branch is unreachable, how the plugin was obtained without admin rights, the four-layer verification method, three migration risks |

##### Consolidation rules applied

Unchanged from v3.0, and applied again to the eight new documents.

**Nothing has been discarded.** Where two documents described the same thing, they have been
merged into one statement of current truth. Where a later session *overturned* an earlier
conclusion, the current truth is stated in the body and the superseded claim is preserved —
in the **Correction Ledger (§0.6)** for the static phase, and in **Part 31 (Supersession Log
II)** for the field phase — together with the evidence that overturned it. Knowing what was
wrong, and why, is what stops it being re-derived.

Three additions specific to this edition:

1. **Where the eight field documents disagree, the disagreement is stated, not smoothed
   over.** §22.4 is a dedicated reconciliation. Every conflict is resolved against evidence,
   and where it cannot be resolved it is left open and marked.
2. **v3's Parts 0–21 are reproduced verbatim.** Where the field campaign overturned or
   extended something, a boxed **⚠️ FIELD** callout has been inserted next to the original
   text pointing forward to the Part that supersedes it. The original claim is never edited
   away — a reader holding a v3 printout can find their sentence and see what happened to it.
3. **Two findings in this edition are new here** and appear in none of the fifteen source
   documents. Both were produced by checking the field documents' claims against files that
   were sitting in the project tree the whole time: the resolution of the feature-name
   contradiction (§22.5.3, and it reverses ledger entry **C12**), and the independent
   confirmation of the big-endian `Serial_Num` field (§25.2.1).

##### ⚠️ Two Part-numbering systems are in circulation — read this before following a reference

The eight field documents were written against the **standalone analysis parts**, not against
consolidated v3. Both use the words "Part 15" through "Part 18" and they mean different
things. A reference like *"Part 17 §5.3"* inside F-b points at
`analysis_part17_session_handoff.md`, **not** at Part 17 of this report.

| Reference in F-a … F-h | Means | In this report |
|---|---|---|
| "Part 2 §2.3", "Part 2 §1.3" | report v2 (`analysis_jul_28_1_0_0.md`) | Part 2 |
| "Part 9.7", "Part 7.2", "Part 8.1", "Part 8.5" | report v2 sections | Parts 7, 8, 9 |
| "Part 15 §G2", "Part 15 §13.2", "Part 15 §15.x" | `analysis_part15_gap_register.md` | Part 16 (gap register) / Part 17 |
| "Part 16 §16.1 … §16.10" | `analysis_part16_mc_answer_protocol.md` | Part 3 (`MC_` link layer) |
| "Part 17 §2.x, §5.3, §7, §8, §13.2" | `analysis_part17_session_handoff.md` | Parts 2, 3, 5, 6, 15, 17 |
| "Part 18 §3.1, §3.3, §10, §11.2" | `analysis_part18_session_report.md` | Parts 2, 3, 16 |
| "Part 25 / Appendix F (The Deployed Configuration)" | an earlier document of that name | Part 12 |

All references **inside Parts 22–32 of this report** have been rewritten to point at this
report's own numbering. The table above is for reading the eight source documents themselves,
should you still hold them.

##### How to read it

Part 0 is the summary and the correction ledger. **Parts 1–4 are the protocol proper — the
part you implement — but read them together with Parts 23 and 24, which correct three things
in them.** Parts 5–10 are the reference tables (dispatch, payloads, decoder rings, records,
databases). Parts 11–15 are the binary-level appendices: the application data model, the SQL
layer, the full function reference, annotated snippets and object layouts. Parts 16–21 are
project state as of the static phase. **Parts 22–32 are the field campaign** and are the
current state of everything.

**If you are about to write code, read Parts 23, 24 and 29 first.** Everything that will
silently produce nothing, or silently produce plausible wrong numbers, is in those three.

Shortcuts:

| I want to… | Go to |
|---|---|
| build the link layer for this box | Parts 2 and 3, **as corrected by Parts 23–24** |
| build it for another site (`MC3_`) | Part 4 |
| know why my reader receives nothing | **§23.2** (two CAN-ID bases) and **§23.3** (ephemeral port) |
| know why my messages never complete | **§24.1** (`DLC−1`, not 7) |
| decode the live measurement stream | **§25.1** (the `0x16` block, fully decoded) |
| look up a `FUN_` address | Part 13 |
| know whether something is still open | **Part 30** |
| know what an older document got wrong | §0.6 and Part 20 (static phase); **Part 31** (field phase) |
| run something against a live machine | **Part 29** — and read §29.1 before you transmit anything |
| understand what can stop the machine | **Part 27** |
| move the databases to SQL Server | **Part 28** |

---

#### Confidence scale

Used uniformly throughout. Version 4.0 adds one grade **above** the v3 scale, introduced by
F-b: a claim proven against captured traffic outranks one proven against the application's own
files, because the wire is the only artefact the application cannot be wrong about.

| Marker | Meaning |
|---|---|
| ✅ **WIRE** | **Proven against captured network traffic.** Predicted-equals-observed, or byte-level correspondence with a live trace. The strongest evidence class in the project. |
| ✅ **VERIFIED** | Proven against raw hex, a database value, a runtime log line, or the function's own literal tag string. Byte-for-byte or value-for-value. |
| 🔶 **GHIDRA** | Recovered from disassembly. Reliable, code-derived, but not externally cross-checked. |
| ⚠️ **INFERRED** | Reasoned from context. Not yet confirmed by bytes. |
| 🔴 | Flags a trap: something that will silently produce plausible-looking wrong output if ignored. |

Where a percentage appears next to a function name it is the analyst's per-function estimate
from the session that recovered it.

Two naming conventions appear in the binary and are used here as the binary uses them:

- **[tag-proven]** — the function builds a QString naming itself (a `Promos3MutexLocker`
  label, an `ErrorManager` tag, or a class-qualified string such as
  `"Promos3CanInterface::receive"`). These names are the binary's own.
- **[structural]** — the name is an analysis label derived from what the code does.
  Verify before committing it to a build.

**⚠️ FIELD** boxes inside Parts 0–21 mark v3 text that the campaign changed. They are
additions; the text they sit next to is v3's, unedited.

---

#### Table of contents

| Part | Title | Covers |
|---|---|---|
| **0** | Executive summary | what was achieved, the facts that matter, status, what remains, the correction ledger |
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
| **16** | Gap register (static-phase state) | G1–G13 with their full progression, plus the two device-state items D3/D4 |
| **17** | Reader implementation guide (static-phase) | passive vs master, the 30-second test, what to change, tooling inventory |
| **18** | Test evidence | the reproduced corruption bug, the 20 passing assertions, the bug the tests found |
| **19** | Data sources & provenance | how every fact was obtained, files used, method notes |
| **20** | Supersession log I (static phase) | every claim an older document got wrong, and what replaced it |
| **21** | Glossary | German, Turkish, protocol, hardware and confidence terms |
| **22** | **The live-capture campaign** | evidence base, capture inventory, the eight-document reconciliation, the three contradictions resolved |
| **23** | **Transport, re-established on the wire** | two CAN-ID bases, the ephemeral source port, the PEAK 36-byte record's real field map, the device clock |
| **24** | **Framing, completion and checksum** | `DLC−1` not 7, the 250-byte flush, the corrected completion rule, the checksum closed in both directions |
| **25** | **Command bodies decoded from live traffic** | the `0x16` measurement block, sixteen measured sizes, twelve decoded bodies, feature names from the device, the event list |
| **26** | **Link behaviour, timing and machine state** | discovery and poll cadence, latency, error paths, the 50 Hz sample rate, cycle detection, sensor health |
| **27** | **Control-flow ownership** | who compares the limit, who stops the machine, what a second PROVIS3 does, G14–G17 |
| **28** | **Databases, configuration and the QODBC back-end** | the measurement schema verified, the logging gap, the Qt plugin, the four-layer verification, the migration decision |
| **29** | **Live access, tooling and operating procedure** | the four access modes, what is safe alongside PROVIS3, the reader's own bugs, the recommended procedure |
| **30** | **Gap register v4 and open items** | G1–G17 final state, D-items, the critical path |
| **31** | **Supersession log II (field phase)** | F1–F32: every claim the captures overturned, narrowed or reconciled |
| **32** | **Glossary addenda and artefact inventory** | new terms, every file used, reproduction notes |

---

### PROVIS3 / Prometec Monitoring — Consolidated Reverse-Engineering Report

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

#### About this edition

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

#### Confidence scale

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

#### Table of contents

> ⚠️ **This is v3's own table of contents, reproduced as it stood, and it stops at Part 21.**
> It is not the table of contents for this edition — see the front matter above for Parts 0–32.
> Parts 22–32 are new in v4.0 and follow Part 21.

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

---

## 38.2 ⟦MEAS⟧ — `PROVIS3_COMPLETE_REPORT_v4.md` (3 captures, normative spec)

### PROVIS3 / Prometec Monitoring — Complete Reverse-Engineering Report

**Version 4.0 — the single combined edition. Supersedes every prior document and appendix.**

**Target:** PROVIS3 HMI application (Sandvik / Prometec CNC tool-monitoring), 32-bit Qt4
binary, branded for Mazak. App version **3.1.44.4 / "V3.1.44 HF4"**, DB schema **10**.

**Goal:** Recover the device↔HMI communication protocol and data formats completely enough
that a modern 64-bit application can read live sensor telemetry, alarms, configuration and
history **without** the original software, without the PEAK/PCAN hardware, and without the
32-bit dependency chain.

**Method, in two phases.**

*Phase 1 — static (sessions 1–5).* Ghidra static analysis of the binary, cross-referenced
against the application's own exported artefacts (SQLite databases, PMD hex dumps, INI files)
and its own runtime logs. No Wireshark, no packet capture and no live machine access was used
at any point. This phase produced the protocol as documented in Parts 1–21.

*Phase 2 — measurement (sessions 6–8).* Three packet captures of the live cell were obtained
and every structural claim of Phase 1 was re-tested as a **predicate over the full record
set**, not spot-checked. This phase confirmed the protocol, corrected the wire, and closed the
two items Phase 1 had correctly identified as unrecoverable from the executable. It is
documented in Parts 22–24, and the resulting single normative wire specification is **Part 25**.

> **If you are implementing a reader and read only one Part, read Part 25.** It is the
> post-measurement specification with every correction already applied. Parts 1–21 remain the
> reasoning and the reference; Parts 22–24 are the evidence.

---

#### About this edition

This document merges **every analysis artefact produced across all eight working sessions** into
one reference. Nothing from any source document has been dropped.

| # | Source document | Session | What it contributed |
|---|---|---|---|
| 1 | `PROVIS3_MASTER_REPORT.md` (report v1) | 1 | First full receive-path recovery; the low-level function catalog; the original config-record structs incl. `SZykRecV4802` offsets and trailer |
| 2 | `promos3_protocol_map.md` | 1 | The command vocabulary: full `MC3_` table, the legacy `MC_` decimal table, decoder rings, the unresolved-token list |
| 3 | `PROVIS3_architecture.md` | 1 | The architecture/protocol map: two-channel diagram, receive path, record formats, status summary |
| 4 | `analysis_jul_28_1_0_0.md` ≡ `PROVIS3_MASTER_REPORT_v2.md` (report v2) | 1 | Architecture, transport, dispatch map, payload bodies, scaling resolution, config records, measurement DB |
| 5 | `analysis_appendix_datamodel.md` (Appendix A) | 2 | `Promos3DataRecord` domain object, SQLite/ODBC read path |
| 6 | `analysis_appendix_B.md` (Appendix B) | 2 | 30 SQL/config/receive functions, `MC3_` command registry, field descriptors |
| 7 | `analysis_part15_gap_register.md` | 3 | Gap register G1–G13, reader test evidence, master/slave discovery |
| 8 | `analysis_part16_mc_answer_protocol.md` | 4 | `MC_` answer framing, checksum, completion rule, `MC3_` assembler |
| 9 | `analysis_part17_session_handoff.md` | 4 | `MC_` command table, size table, request side, unit discovery, architecture |
| 10 | `analysis_part18_session_report.md` | 5 | Transmit path, poll cycle, CAN-ID resolution, model string, link-layer code |
| 11 | `PROVIS3_consolidated_report_v3.md` | 6 | The consolidation of 4–10 that forms the spine of Parts 0–21 |
| 12 | `analysis_part19_capture_verification.md` | 6 | **First capture** (`JULY5_IMP1.pcapng`) — the two-base CAN-ID correction, three measured sizes, 50 Hz sample rate → **Part 22** |
| 13 | `analysis_appendix_C_wire_capture.md` (Appendix C / Part 22) | 7 | **Breadth capture** (`ALL_merged__uniq.pcapng`) — the PEAK gateway record, the ephemeral port, six decoded bodies, 16 measured sizes → **Part 23** |
| 14 | `analysis_appendix_D_poll_loop_capture.md` (Appendix D / Part 23) | 8 | **Depth capture** (`july_6_packet1.pcapng`) — the `DLC−1` framing correction, the `0x16` `(min,max)` decode, the measured poll loop → **Part 24** |
| 15 | *(this edition)* | — | **Part 25**, the single normative post-measurement wire specification, final gap register and final reader checklist |

**Merge rules applied.**

1. **Nothing has been discarded.** Where two documents described the same thing they were merged
   into one statement of current truth. Material that v3 abridged for brevity — the low-level Qt
   plumbing catalog, the Ethernet-server function set, the early command vocabulary — has been
   **restored** (Parts 13.16, 5.2.1, 26).
2. **Where a later session overturned an earlier one**, the current truth is in the body and the
   superseded claim is preserved in the **Correction Ledger (§0.6)**, extended here to **C35**, with
   the evidence that overturned it. Every ⚠️ **SUPERSEDED** marker in the body points at it.
3. **Where measurement and inference disagree, measurement wins.** Parts 22–24 are packet captures;
   Parts 1–21 are static analysis. Sections of Parts 1–21 that a capture overturned now carry an
   inline 🔴 **CORRECTED BY MEASUREMENT** banner naming the Part that corrects them. The original
   static reasoning is left intact underneath, because it is still the derivation.
4. **Where two captures disagree, the larger sample wins.** Part 24 (88,936 exchanges) supersedes
   Part 23 (250 exchanges) on the two framing rules where they conflict.

**How to read it.**

| You want | Go to |
|---|---|
| The summary and every reversal | Part 0 |
| **To implement a reader** | **Part 25** (normative spec), then Parts 2–3 for the reasoning |
| The protocol as reasoned out | Parts 1–4 (`MC_`, this box) or Part 4 (`MC3_`, other sites) |
| Reference tables — dispatch, payloads, rings, records, DBs | Parts 5–10 |
| The application's own data model and SQL layer | Parts 11–12 |
| A `FUN_` address | Part 13 (incl. §13.16, the restored low-level catalog) |
| Annotated decompiler extracts and object layouts | Parts 14–15 |
| What is still open | Part 25 §25.6, or Part 16 for the historical progression |
| Proof for any wire claim | Parts 22, 23, 24 |
| You are holding an older document | §0.6, Part 20, Part 26 |

---

#### Confidence scale

Used uniformly throughout. Where a percentage appears next to a function name it is the
analyst's per-function estimate from the session that recovered it.

| Marker | Meaning |
|---|---|
| 📐 **MEASURED** | Proven on the wire, as a predicate over a full capture record set. The strongest marker in this document; introduced in v4.0 (Parts 22–24). Where a count is given — "88,936 / 88,936" — that is the number of independent samples that satisfied the rule and the number tested. |
| ✅ **VERIFIED** | Proven against raw hex, a database value, a runtime log line, or the function's own literal tag string. Byte-for-byte or value-for-value. |
| 🔶 **GHIDRA** | Recovered from disassembly. Reliable, code-derived, but not externally cross-checked. |
| ⚠️ **INFERRED** | Reasoned from context. Not yet confirmed by bytes. |
| 🔴 | Flags a trap: something that will silently produce plausible-looking wrong output if ignored. |

⚠️ **A note on 🔶 GHIDRA versus the prose that summarises it.** Corrections C32 and C33 (§0.6) are
the only two in this project where the decompiler output was *right* and the English sentence
directly underneath it was *wrong* — a constant was promoted out of a variable
(`avail = frame[5] − 1` became "7 payload bytes per frame") because 7 was the value it took in
every sample then available. When this report quotes a decompiled expression and then paraphrases
it, **the expression is the specification and the paraphrase is a convenience.**

Two naming conventions appear in the binary and are used here as the binary uses them:

- **[tag-proven]** — the function builds a QString naming itself (a `Promos3MutexLocker`
  label, an `ErrorManager` tag, or a class-qualified string such as
  `"Promos3CanInterface::receive"`). These names are the binary's own.
- **[structural]** — the name is an analysis label derived from what the code does.
  Verify before committing it to a build.

---

#### Table of contents

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
| **22** | **Capture 1 — first live verification** | `JULY5_IMP1.pcapng`: the two-base CAN-ID correction, batching, three measured sizes, the 50 Hz sample rate |
| **23** | **Capture 2 — breadth** | `ALL_merged__uniq.pcapng`: the PEAK gateway record and its µs clock, the ephemeral source port, six decoded bodies, 16 measured answer sizes, the attribution negative result |
| **24** | **Capture 3 — depth** | `july_6_packet1.pcapng`: `DLC−1` framing, the corrected checksum placement, `0x16` decoded as `(min,max)` pairs, the measured poll loop |
| **25** | ⭐ **The normative wire specification** | the single post-measurement spec, final gap register, final reader checklist, replay corpus, what is still open |
| **26** | Document lineage & archive | what each of the fifteen source documents said, what replaced it, and where its unique content now lives |

---

---

## 38.3 ⟦CAP1⟧ — `PROVIS3_consolidated_report_v4.md` (1 capture)

### PROVIS3 / Prometec Monitoring — Consolidated Reverse-Engineering Report

**Version 4.0 — single consolidated edition (supersedes all prior parts and appendices)**

> 🔴 **If you read nothing else, read §0.7.** A live bidirectional packet capture
> (`JULY5_IMP1.pcapng`) was taken after v3.0 was written. It **confirms the analysis
> almost entirely** — but it also corrects **four** things, one of which is a fatal bug
> that makes the current reader decode nothing at all. §0.7 lists them; **Part 22** is the
> full measurement report.

**Target:** PROVIS3 HMI application (Sandvik / Prometec CNC tool-monitoring), 32-bit Qt4
binary, branded for Mazak. App version **3.1.44.4 / "V3.1.44 HF4"**, DB schema **10**.

**Goal:** Recover the device↔HMI communication protocol and data formats completely enough
that a modern 64-bit application can read live sensor telemetry, alarms, configuration and
history **without** the original software, without the PEAK/PCAN hardware, and without the
32-bit dependency chain.

**Method:** Ghidra static analysis of the binary, cross-referenced against the application's
own exported artefacts (SQLite databases, PMD hex dumps, INI files) and its own runtime logs.
**Parts 0–21 were produced with no Wireshark, no packet capture and no live machine access at
any point.** **Part 22** is the later, independent validation of that work against a real
bidirectional capture — it is kept structurally separate precisely so that the two evidence
bases stay distinguishable: everything that was *predicted* can still be told apart from
everything that was *measured*.

---

#### About this edition

This document merges **ten** separate analysis artefacts produced across seven working sessions
into one authoritative reference:

| Source document | Session | What it contributed |
|---|---|---|
| `promos3_protocol_map.md` (v1) | 0 | First command map (both generations, decimal numbering), the three live-packet decoders, decoder rings, the `SFactors.ini` / `FindProcurFactors` scaling lead |
| `PROVIS3_architecture.md` (v1) | 0 | First end-to-end architecture diagram, the two channels, gateway record, config-record summary, the original provenance table |
| `analysis_jul_28_1_0_0.md` (report v2) | 1 | Architecture, transport, dispatch map, payload bodies, scaling, config records, measurement DB |
| `analysis_appendix_datamodel.md` (Appendix A) | 2 | `Promos3DataRecord` domain object, SQLite read path |
| `analysis_appendix_B.md` (Appendix B) | 2 | 30 SQL/config/receive functions, MC3_ command registry, field descriptors |
| `analysis_part15_gap_register.md` | 3 | Gap register G1–G13, reader test evidence, master/slave discovery |
| `analysis_part16_mc_answer_protocol.md` | 4 | MC_ answer framing, checksum, completion rule, MC3_ assembler |
| `analysis_part17_session_handoff.md` | 4 | MC_ command table, size table, request side, unit discovery, architecture |
| `analysis_part18_session_report.md` | 5 | Transmit path, poll cycle, CAN-ID resolution, model string, link-layer code |
| `PROVIS3_consolidated_report_v3.md` | 6 | The consolidation of the seven documents above — the spine of Parts 0–21 |
| `analysis_part19_capture_verification.md` | 7 | ⭐ **Live bidirectional capture** — the endpoint correction, the CAN-ID direction split, datagram batching, the gateway µs clock, three measured answer sizes, D4 resolved, measured cadence → **Part 22** |

⚠️ **Two source documents referenced by the project could not be located and are therefore
NOT merged here:** `analysis_appendix_C_wire_capture.md` and
`analysis_appendix_D_poll_loop_capture.md`. If they exist, they should be reconciled against
Part 22, which covers the same subject matter from the `JULY5_IMP1.pcapng` artefact. Nothing
in this report depends on them, but the possibility that they contain unique measurements is
recorded here rather than silently ignored.

**Consolidation rules applied.** Nothing has been discarded. Where two documents described
the same thing, they have been merged into one statement of current truth. Where a later
session *overturned* an earlier conclusion, the current truth is stated in the body of the
report and the superseded claim is preserved in the **Correction Ledger (§0.6)** with the
evidence that overturned it — because knowing what was wrong, and why, is what stops it being
re-derived. Every ⚠️ **SUPERSEDED** marker in the body points back to that ledger.

**How to read it.** Part 0 is the summary, the correction ledger and the live-capture delta.
Parts 1–4 are the protocol proper — the part you implement. Parts 5–10 are the reference tables
(dispatch, payloads, decoder rings, records, databases). Parts 11–15 are the binary-level
appendices: the application data model, the SQL layer, the full function reference, annotated
snippets and object layouts. Parts 16–21 are project state: what is left, what to build, what to
do next, where every fact came from, what earlier documents got wrong, and the glossary.
**Part 22 is the live-capture verification** — the only Part in the document whose evidence is
measured packets rather than disassembly.

⚠️ **A note on the numbering.** Part 22 is placed after the glossary rather than being inserted
next to the other evidence Part (Part 18). This is deliberate: several hundred internal
cross-references point at Parts 13, 16, 17 and 20 by number, and renumbering them to make one
Part sit prettier would risk breaking references that people actually follow. §0.7 carries the
capture's conclusions up to the front so that placement never costs a reader anything.

Shortcuts: building the link layer → **Parts 2 and 3** (this box) or **Part 4** (other sites);
looking up a `FUN_` address → **Part 13**; wondering whether something is still open → **Parts 16
and 17**; holding an older document and wondering what changed → **§0.6, §0.7 and Part 20**;
wanting the measured ground truth → **Part 22**.

---

#### Confidence scale

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

#### Table of contents

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
| **22** | ⭐ **Live capture verification** | the `JULY5_IMP1.pcapng` measurement: endpoints, framing, CAN-ID direction split, batching, the gateway clock, measured sizes and cadence, and what an idle machine could not show |

---

---

*End of PROVIS3 Unified Report v5.0.*

*This edition merges `PROVIS3_consolidated_report_v4__1_.md` ⟦FIELD⟧,
`PROVIS3_COMPLETE_REPORT_v4.md` ⟦MEAS⟧ and `PROVIS3_consolidated_report_v4.md` ⟦CAP1⟧ — and,
through them, every document those three superseded. Nothing was discarded; where the three
disagreed, the disagreement is recorded in §0.0.5 and both readings are kept in the body.*
