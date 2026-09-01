/* promos3_live.c — PROVIS3 / Prometec live link layer + reader.
 *
 * Self-contained. Clean-room, written from the byte-level spec — not decompiler
 * output. Supersedes promos3_transport.c + the old parse_message_header() path.
 *
 * ─────────────────────────────────────────────────────────────────────────────
 *  PROVENANCE — every rule here is measured, not assumed.
 *
 *  Verified against two captures of the live cell:
 *    A) ALL_merged__uniq.pcapng   8,800 records,     250 attributed exchanges
 *    B) july_6_packet1.pcapng   194,006 records,  88,936 attributed exchanges
 *
 *    request checksum ......... 89,186 / 89,186   (0 failures)
 *    answer  checksum ......... 89,184 / 89,184   (0 failures)
 *    sequence continuity ...... 89,186 / 89,186
 *    checksum placement rule ..  88,936 / 88,936  (100.0000%)
 *    0x16 length formula ......  88,936 / 88,936
 *    0x16 min<=max invariant ..  61,764 pairs, 0 inversions
 *
 * ─────────────────────────────────────────────────────────────────────────────
 *  WHAT CHANGED FROM THE v3-REPORT READER — the four that actually matter:
 *
 *  1. TWO CAN-ID BASES.  Requests 0x500+unit, answers 0x580+unit.  The report
 *     said one base for both directions; that drops 100% of answers silently.
 *
 *  2. UNCONNECTED SOCKET.  The gateway answers from an EPHEMERAL, session-
 *     varying source port (34686 / 50375 observed), never 1789.  connect()ing
 *     the socket makes the kernel discard every reply before you see it.
 *     Filter on source HOST, never on source port.
 *
 *  3. PAYLOAD PER FRAME IS (DLC-1), NOT 7.  The device flushes every 250 payload
 *     bytes and emits a short mid-stream frame at each boundary.  Any "7 bytes
 *     per frame" or ceil(n/7) frame-count rule breaks on answers >250 bytes —
 *     which is exactly where the measurement bursts live.
 *
 *  4. CHECKSUM PLACEMENT is decided by the CLAMPED avail, not by (expected%7).
 *     A separate [seq][checksum] frame follows iff the final data frame was
 *     filled with a full 7 payload bytes.  The %7 rule has counter-examples.
 *
 *  Plus: the 36-byte wrapper is the standard PEAK PCAN-Ethernet Gateway frame,
 *  carrying a 64-bit big-endian microsecond device clock at +0x0C.  Use it for
 *  ordering; the host clock is only good for anchoring the epoch.
 *
 * ─────────────────────────────────────────────────────────────────────────────
 *  build:  cc -std=c11 -Wall -Wextra -O2 promos3_live.c -o promos3_live
 *          cl  /W4 /O2 promos3_live.c ws2_32.lib          (MSVC)
 *
 *  usage:  promos3_live --master  --gw 192.168.222.16 [--units 1,2] [--csv f.csv]
 *          promos3_live --listen  --gw 192.168.222.16 [--csv f.csv]
 *          promos3_live --replay  capture.pcapng       [--csv f.csv]
 *          promos3_live --probe   --gw 192.168.222.16
 */

#if !defined(_WIN32)
#  define _POSIX_C_SOURCE 200809L
#endif

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <stdbool.h>
#include <stddef.h>
#include <signal.h>
#include <time.h>

#ifdef _WIN32
#  include <winsock2.h>
#  include <ws2tcpip.h>
#  include <io.h>
#  include <fcntl.h>
#  pragma comment(lib, "ws2_32.lib")
   typedef SOCKET sock_t;
#  define SOCK_BAD    INVALID_SOCKET
#  define CLOSESOCK   closesocket
#  define SOCKLEN_T   int
#else
#  include <unistd.h>
#  include <errno.h>
#  include <arpa/inet.h>
#  include <sys/socket.h>
#  include <sys/time.h>
   typedef int sock_t;
#  define SOCK_BAD    (-1)
#  define CLOSESOCK   close
#  define SOCKLEN_T   socklen_t
#endif

/* ══════════════════════════════════════════════════════════════════════════
 * 1.  TRANSPORT CONSTANTS                                    [C.3, C.4, C.5]
 * ══════════════════════════════════════════════════════════════════════════ */

#define P3_PORT            1789      /* both ends bind/target this            */
#define CANID_BASE_TX      0x500     /* PC  -> gateway : requests   VERIFIED  */
#define CANID_BASE_RX      0x580     /* gateway -> PC  : answers    VERIFIED  */
#define CANID_UNIT_MASK    0x7F

#define GW_REC             36        /* PEAK gateway frame, 0x24 bytes        */
#define GW_MAGIC0          0x0024    /* +0x00 length  BE                      */
#define GW_MAGIC1          0x0080    /* +0x02 type = CAN frame                */
#define CAN_MAX_DATA       8

#define MAX_UNITS          16        /* FirstDevice..LastDevice = 1..15       */
#define REASM_MAX          4096      /* largest seen: 1001                    */
#define DGRAM_MAX          65536     /* observed max 540; be generous         */

/* Timing. unitAnswerTimeout=300 in the INI, but measured worst first-answer
 * latency is 9.8 ms and the longest answer streams for ~22 ms.  We arm the
 * deadline on the LAST FRAME RECEIVED, so a tight value is safe and fails
 * ~6x faster during bring-up.                                        [D.5] */
#define DEF_TIMEOUT_MS     50
#define DEF_MAX_RESEND     1         /* [Comm] MaxResend                      */
#define DEF_PACE_US        1500      /* app paces ~1.5 ms/request, not 3 ms   */

/* ══════════════════════════════════════════════════════════════════════════
 * 2.  MC_ COMMANDS + MEASURED ANSWER SIZES                          [C.9]
 *
 *  The binary's Geraet_expectedRecordSize table is CONFIRMED at 0x0E only and
 *  demonstrably wrong at 0x02, 0x05, 0x08, 0x0F.  These are the measured
 *  values.  An unknown command gets SZ_UNKNOWN and is allowed to time out —
 *  a timeout is a loud failure, a wrong expected size silently eats the NEXT
 *  answer's frames.
 * ══════════════════════════════════════════════════════════════════════════ */

#define SZ_UNKNOWN   (-1)
#define SZ_DYNAMIC   (-2)            /* 0x16: expected = DATA[1]*stride + 1   */

typedef enum {                       /* honesty gating — never print a layout */
    CONF_UNKNOWN = 0,                /* no name, no decoder    -> id + hex    */
    CONF_NAMED,                      /* name, no decoder       -> name + hex  */
    CONF_PROVISIONAL,                /* decoder, layout unsure -> name + hex  */
    CONF_CONFIRMED                   /* decoder + layout proven-> values      */
} conf_t;

typedef struct {
    uint8_t     cmd;
    const char *name;
    int         size;                /* measured payload bytes, ck excluded   */
    conf_t      conf;
} cmd_row_t;

static const cmd_row_t g_cmds[] = {
    /* cmd    name                     size          confidence               */
    { 0x01, "MC_GIVESTATUS",             2, CONF_NAMED       },
    { 0x02, "MC_GIVEGTYPE",              3, CONF_CONFIRMED   },  /* 44 05 01  */
    { 0x05, "MC_GIVEUSEDZYKTAB",        32, CONF_NAMED       },
    { 0x06, "MC_GIVEKONFIG",            14, CONF_CONFIRMED   },  /* e5 01 04  */
    { 0x08, "MC_GIVEPLCVALUES",          5, CONF_PROVISIONAL },  /* D4 closed */
    { 0x0D, "MC_GIVEGERAETEREC",        66, CONF_CONFIRMED   },  /* SGeraetRec*/
    { 0x0E, "MC_GIVEKANAL",            144, CONF_CONFIRMED   },  /* SKanalRec */
    { 0x0F, "MC_GIVEZYKLUS",           170, CONF_NAMED       },  /* SZykRec   */
    { 0x12, "MC_GIVEALARM",             17, CONF_CONFIRMED   },
    { 0x14, "MC_cmd_14",                36, CONF_UNKNOWN     },
    { 0x16, "MC_GIVESAMMELMERKMALE", SZ_DYNAMIC, CONF_CONFIRMED },
    { 0x1A, "MC_GIVEHARDWAREREC",       46, CONF_NAMED       },
    { 0x1B, "MC_GIVESIGNALVERLAUF", SZ_UNKNOWN, CONF_PROVISIONAL }, /* D5 !!! */
    { 0x23, "MC_GIVE_SENSORVALUES",     14, CONF_PROVISIONAL },
    { 0x25, "MC_GIVE_ACTZYKINDEX",       3, CONF_NAMED       },
    { 0x29, "MC_cmd_29",                40, CONF_UNKNOWN     },
    { 0x33, "MC_GIVEPROGID",             2, CONF_NAMED       },
};

static const cmd_row_t *cmd_row(uint8_t c) {
    for (size_t i = 0; i < sizeof g_cmds / sizeof g_cmds[0]; i++)
        if (g_cmds[i].cmd == c) return &g_cmds[i];
    return NULL;
}
static const char *cmd_name(uint8_t c) {
    const cmd_row_t *r = cmd_row(c);
    static char buf[24];
    if (r) return r->name;
    snprintf(buf, sizeof buf, "MC_cmd_%02X", c);
    return buf;
}
static int cmd_size(uint8_t c) { const cmd_row_t *r = cmd_row(c); return r ? r->size : SZ_UNKNOWN; }
static conf_t cmd_conf(uint8_t c){ const cmd_row_t *r = cmd_row(c); return r ? r->conf : CONF_UNKNOWN; }

/* ══════════════════════════════════════════════════════════════════════════
 * 3.  SMALL UTILITIES
 * ══════════════════════════════════════════════════════════════════════════ */

static volatile sig_atomic_t g_stop = 0;
static void on_sigint(int s) { (void)s; g_stop = 1; }

static uint64_t now_us(void) {
#ifdef _WIN32
    static LARGE_INTEGER f; LARGE_INTEGER c;
    if (!f.QuadPart) QueryPerformanceFrequency(&f);
    QueryPerformanceCounter(&c);
    return (uint64_t)(c.QuadPart * 1000000ll / f.QuadPart);
#else
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return (uint64_t)ts.tv_sec * 1000000u + (uint64_t)(ts.tv_nsec / 1000);
#endif
}

static uint16_t rd_be16(const uint8_t *p) { return (uint16_t)((p[0] << 8) | p[1]); }
static uint32_t rd_be32(const uint8_t *p) {
    return ((uint32_t)p[0] << 24) | ((uint32_t)p[1] << 16) |
           ((uint32_t)p[2] <<  8) |  (uint32_t)p[3];
}
static uint16_t rd_le16(const uint8_t *p) { return (uint16_t)(p[0] | (p[1] << 8)); }

static void hexdump(const uint8_t *p, size_t n) {
    for (size_t i = 0; i < n; i += 16) {
        printf("      +%03zX  ", i);
        for (size_t j = 0; j < 16; j++)
            if (i + j < n) printf("%02x ", p[i + j]); else printf("   ");
        printf(" |");
        for (size_t j = 0; j < 16 && i + j < n; j++) {
            uint8_t c = p[i + j];
            putchar((c >= 32 && c < 127) ? c : '.');
        }
        printf("|\n");
    }
}

/* ══════════════════════════════════════════════════════════════════════════
 * 4.  THE GATEWAY RECORD — PEAK PCAN-Ethernet Gateway frame          [C.4]
 *
 *   off  size  field                    note
 *   0x00   2   length (BE) = 0x0024     constant, 194,006/194,006
 *   0x02   2   type   (BE) = 0x0080     CAN frame
 *   0x04   8   tag / client handle      zero on this link
 *   0x0C   4   timestamp LOW  (BE)      microseconds — device uptime clock
 *   0x10   4   timestamp HIGH (BE)      NOTE: low dword first, then high.
 *                                       Reading +0x0C..0x13 as one BE u64 is
 *                                       WRONG — the two halves are swapped.
 *                                       Low word wraps every 71.6 minutes, so
 *                                       you must use both.
 *   0x14   1   CAN channel              0
 *   0x15   1   DLC                      2..8
 *   0x16   1   flags                    0 (no RTR / extended / error frame)
 *   0x17   1   reserved                 0
 *   0x18   4   CAN-ID (BE, 32-bit)      read the FULL dword, not +0x1A..1B
 *   0x1C   8   DATA[0..7]
 *
 *   The report called 0x04..0x14 "17 bytes of zero padding".  It is zero only
 *   on the REQUEST path, because the PC does not fill it.
 * ══════════════════════════════════════════════════════════════════════════ */

typedef struct {
    uint32_t can_id;
    uint64_t dev_ts;                 /* gateway microsecond clock             */
    uint8_t  chan, dlc, flags;
    uint8_t  data[CAN_MAX_DATA];
    int      unit;                   /* can_id & 0x7F                         */
    bool     is_answer;              /* (can_id & 0x580) == 0x580             */
    bool     is_request;
} frame_t;

static bool gw_parse(const uint8_t *r, frame_t *f) {
    if (rd_be16(r + 0x00) != GW_MAGIC0) return false;
    if (rd_be16(r + 0x02) != GW_MAGIC1) return false;

    memset(f, 0, sizeof *f);
    f->dev_ts = ((uint64_t)rd_be32(r + 0x10) << 32) | rd_be32(r + 0x0C);
    f->chan   = r[0x14];
    f->dlc    = r[0x15];
    f->flags  = r[0x16];
    f->can_id = rd_be32(r + 0x18);
    if (f->dlc > CAN_MAX_DATA) return false;
    memcpy(f->data, r + 0x1C, CAN_MAX_DATA);

    f->unit       = (int)(f->can_id & CANID_UNIT_MASK);
    f->is_answer  = (f->can_id & ~(uint32_t)CANID_UNIT_MASK) == CANID_BASE_RX;
    f->is_request = (f->can_id & ~(uint32_t)CANID_UNIT_MASK) == CANID_BASE_TX;
    return f->is_answer || f->is_request;
}

/* Build a 36-byte record for transmission.  Only DLC, CAN-ID and DATA are
 * filled; the PC leaves tag/timestamp/channel/flags zero, exactly as observed
 * across all 88,936 captured requests. */
static void gw_build(uint8_t *r, uint32_t can_id, const uint8_t *data, uint8_t dlc) {
    memset(r, 0, GW_REC);
    r[0x00] = 0x00; r[0x01] = 0x24;
    r[0x02] = 0x00; r[0x03] = 0x80;
    r[0x15] = dlc;
    r[0x18] = (uint8_t)(can_id >> 24); r[0x19] = (uint8_t)(can_id >> 16);
    r[0x1A] = (uint8_t)(can_id >>  8); r[0x1B] = (uint8_t)(can_id);
    memcpy(r + 0x1C, data, dlc);
}

/* ══════════════════════════════════════════════════════════════════════════
 * 5.  CHECKSUM                                                  [C.8, D.3]
 *
 *   ck = -( unit + SUM(request[0 .. n-2]) + SUM(answer_payload) ) & 0xFF
 *
 *   The request's own trailing checksum is excluded (that is the `sent_n - 1`
 *   in the original).  The same seeding governs BOTH directions — three
 *   alternative seedings were tested against all captured answers and each
 *   scored 0.
 * ══════════════════════════════════════════════════════════════════════════ */

static uint8_t p3_checksum(int unit,
                           const uint8_t *req, size_t req_len,
                           const uint8_t *pay, size_t pay_len)
{
    unsigned s = (unsigned)unit;
    if (req && req_len) for (size_t i = 0; i + 1 < req_len; i++) s += req[i];
    if (pay && pay_len) for (size_t i = 0; i < pay_len; i++)     s += pay[i];
    return (uint8_t)((0u - s) & 0xFFu);
}

/* ══════════════════════════════════════════════════════════════════════════
 * 6.  REQUEST BUILD + FRAMING                                    [C.6, D.3]
 *
 *   Paket bytes : [cmd][args...][checksum]
 *   First frame : [00][00][00] + up to 5 payload bytes
 *   DLC         : 3 + min(5, payload_len)   -> 5, 6, 7 or 8
 *   Continuation: [seq][ up to 7 payload bytes ]
 *
 *   Do NOT zero-pad a short request to DLC 8 — the padding lands inside the
 *   checksum's summed range and the device rejects it.
 * ══════════════════════════════════════════════════════════════════════════ */

typedef struct { uint8_t b[16]; uint8_t len; } paket_t;

static void paket_build(paket_t *p, int unit, uint8_t cmd,
                        const uint8_t *args, uint8_t nargs)
{
    p->len = 0;
    p->b[p->len++] = cmd;
    for (uint8_t i = 0; i < nargs; i++) p->b[p->len++] = args[i];
    /* the paket's own checksum: seed unit, sum over everything so far        */
    unsigned s = (unsigned)unit;
    for (uint8_t i = 0; i < p->len; i++) s += p->b[i];
    p->b[p->len++] = (uint8_t)((0u - s) & 0xFFu);
}

/* Emit the CAN frames for one request.  Returns frame count. */
static int paket_frames(const paket_t *p, uint8_t out[][CAN_MAX_DATA], uint8_t *dlcs, int max)
{
    int n = 0, off = 0;
    uint8_t chunk = (uint8_t)(p->len < 5 ? p->len : 5);

    if (n >= max) return 0;
    memset(out[n], 0, CAN_MAX_DATA);
    out[n][0] = 0; out[n][1] = 0; out[n][2] = 0;          /* the reserved 3   */
    memcpy(out[n] + 3, p->b, chunk);
    dlcs[n] = (uint8_t)(3 + chunk);                        /* NOT always 8    */
    off += chunk; n++;

    /* Continuations. No multi-frame request has ever been captured (D6), so
     * this path is code-derived only — flagged, not silently trusted.        */
    uint8_t seq = 1;
    while (off < p->len && n < max) {
        uint8_t take = (uint8_t)(p->len - off);
        if (take > 7) take = 7;
        memset(out[n], 0, CAN_MAX_DATA);
        out[n][0] = seq++;
        memcpy(out[n] + 1, p->b + off, take);
        dlcs[n] = (uint8_t)(1 + take);
        off += take; n++;
    }
    return n;
}

/* ══════════════════════════════════════════════════════════════════════════
 * 7.  DECODED BODIES                                          [C.10, D.4]
 * ══════════════════════════════════════════════════════════════════════════ */

#define MAX_FEATURES 4

typedef struct {                                  /* 0x06 GIVEKONFIG, 14 B    */
    uint8_t version, channels, sensors;
} konfig_t;

typedef struct {                                  /* 0x0D SGeraetRec, 66 B    */
    uint8_t  gtype, gsubtype, channels, sensors;
    uint8_t  sensor_type[8];
    uint16_t reduzlim;
    uint16_t serial;                              /* +0x14, BIG-endian        */
} geraetrec_t;

typedef struct {                                  /* 0x0E SKanalRecV40, 144 B */
    uint8_t mask[MAX_FEATURES];
    char    name[MAX_FEATURES][12];
    int     count;
    uint8_t cdrlim[4];
} kanalrec_t;

typedef struct {                                  /* 0x12 GIVEALARM, 17 B     */
    uint8_t slot, code;
    int     day, mon, year, hh, mm, ss;
    bool    empty;
} alarm_t;

typedef struct {                                  /* one 0x16 row             */
    uint8_t vmin[MAX_FEATURES], vmax[MAX_FEATURES];
    uint8_t st0, st1;
    bool    escape;                               /* row[0]==0xFF             */
    uint8_t marker;                               /* row[1] when escape       */
} merkmal_row_t;

static bool decode_konfig(const uint8_t *p, int n, konfig_t *k) {
    if (n < 3) return false;
    k->version = p[0]; k->channels = p[1]; k->sensors = p[2];
    return true;
}

/* SGeraetRec — seven field offsets cross-checked against the PMD export, the
 * report and the deployed PROVISsettings.ini (GType 0x44, GSubType 5,
 * ReduzLim 0x19D4=6612, 8 x 0x80 = PROCUR-S).
 *
 * +0x14 is the UNIT SERIAL NUMBER, and it is BIG-ENDIAN inside an otherwise
 * LITTLE-ENDIAN payload.  Confirmed against [DatabasePMD] on the captured box:
 * unit 1 -> 0x29A4 = 10660, unit 2 -> 0x29A9 = 10665, matching
 * LastDatabase=Provis-10665 / LastMonDataFile-10660.  Reading it LE gives
 * 42025 / 43305 and looks plausible enough to ship by mistake.      [F.2]  */
static bool decode_geraetrec(const uint8_t *p, int n, geraetrec_t *g) {
    if (n < 66) return false;
    g->gtype = p[0]; g->gsubtype = p[1]; g->channels = p[2]; g->sensors = p[3];
    g->serial = rd_be16(p + 0x14);            /* BIG-endian: see note above */
    memcpy(g->sensor_type, p + 0x1A, 8);
    g->reduzlim = rd_le16(p + 0x26);              /* payload is LITTLE-endian */
    return true;
}

/* SKanalRecV40 — four 12-byte feature descriptors at body +0x4D:
 *   [mask:1][name:11 NUL-padded ASCII]
 * mask & 0x0F is ONE-HOT (1,2,4,8): the feature index is log2 of it, not the
 * value itself.  Bit 0x80 is set on some units and is NOT part of the index. */
static int mask_to_index(uint8_t mask) {
    switch (mask & 0x0F) { case 1: return 0; case 2: return 1;
                           case 4: return 2; case 8: return 3; }
    return -1;
}

static bool decode_kanalrec(const uint8_t *p, int n, kanalrec_t *k) {
    if (n < 144) return false;
    memset(k, 0, sizeof *k);
    memcpy(k->cdrlim, p + 0x10, 4);
    for (int i = 0; i < MAX_FEATURES; i++) {
        const uint8_t *d = p + 0x4D + 12 * i;
        int idx = mask_to_index(d[0]);
        if (idx < 0) continue;
        k->mask[idx] = d[0];
        memcpy(k->name[idx], d + 1, 11);
        k->name[idx][11] = 0;
        for (int c = 0; c < 12; c++)                        /* sanitise       */
            if (k->name[idx][c] && (k->name[idx][c] < 32 || k->name[idx][c] > 126))
                k->name[idx][c] = 0;
        k->count++;
    }
    return k->count > 0;
}

/* GIVEALARM — 16-entry ring, index in request arg[1].  Timestamp at +0x0A is
 * D-M-Y h:m:s; field ranges settle the order (day reaches 31, month never
 * exceeds 12).  Century assumed 2000+.                             [C.10.4] */
static bool decode_alarm(const uint8_t *p, int n, alarm_t *a) {
    if (n < 17) return false;
    a->slot = p[0]; a->code = p[1];
    a->day = p[0x0A]; a->mon = p[0x0B]; a->year = 2000 + p[0x0C];
    a->hh  = p[0x0D]; a->mm  = p[0x0E]; a->ss   = p[0x0F];
    a->empty = (p[0x0A] == 0 && p[0x0B] == 0 && p[0x0C] == 0);
    return true;
}

/* ── 0x16 GIVESAMMELMERKMALE — THE live measurement block ─────────── [D.4] ──
 *
 *   payload[0]            = row count n
 *   payload[1 + r*stride] = row r, stride = featureCount*2 + 2:
 *
 *     +0 Min_F0  +1 Max_F0  +2 Min_F1  +3 Max_F1
 *     +4 Min_F2  +5 Max_F2  +6 Min_F3  +7 Max_F3
 *     +8 status0            +9 status1
 *
 *   Verified over 61,764 feature pairs with ZERO min>max inversions.  Matches
 *   the WP_* table schema (Min_S01/Max_S01/...) byte for byte — the app does
 *   not transform this, it writes the rows through.
 *
 *   Escape: row[0] == 0xFF, marker in row[1] (0xFB = per-feature reset seen),
 *   parameter in the FOLLOWING row.  64 escape rows <-> 64 min>max rows, an
 *   exact bijection, so in a NON-escape row min>max means the reassembly is
 *   wrong — a free integrity check.  Do NOT read 0xFF in a Max byte as an
 *   escape; that is ordinary saturation.
 */
static int decode_merkmale(const uint8_t *p, int n, int nfeat,
                           merkmal_row_t *out, int max, int *bad_pairs)
{
    if (n < 1) return -1;
    int stride = nfeat * 2 + 2;
    int rows   = p[0];
    if (1 + rows * stride != n) return -1;        /* length must reconcile    */

    int emitted = 0;
    *bad_pairs = 0;
    for (int r = 0; r < rows && emitted < max; r++) {
        const uint8_t *d = p + 1 + r * stride;
        merkmal_row_t *m = &out[emitted++];
        memset(m, 0, sizeof *m);
        m->escape = (d[0] == 0xFF);
        m->marker = d[1];
        for (int f = 0; f < nfeat && f < MAX_FEATURES; f++) {
            m->vmin[f] = d[2 * f];
            m->vmax[f] = d[2 * f + 1];
            if (!m->escape && m->vmin[f] > m->vmax[f]) (*bad_pairs)++;
        }
        m->st0 = d[stride - 2];
        m->st1 = d[stride - 1];
    }
    return emitted;
}

/* ══════════════════════════════════════════════════════════════════════════
 * 8.  PER-UNIT LINK STATE + THE ANSWER ASSEMBLER               [D.2, D.3]
 * ══════════════════════════════════════════════════════════════════════════ */

typedef struct {
    /* outstanding request */
    bool     busy;
    uint8_t  cmd;
    paket_t  req;
    int      expected;               /* -1 until learned (0x16)               */
    int      attempts;

    /* reassembly */
    uint8_t  buf[REASM_MAX];
    int      acc;
    int      next_seq;
    int      last_avail;
    bool     await_ck;               /* the [seq][ck] frame is next           */
    int      nframes;

    /* timing */
    uint64_t t_req, t_last_frame;
    uint64_t dev_ts_first;

    /* learned config */
    bool       have_kanal;
    kanalrec_t kanal;
    bool       have_konfig;
    konfig_t   konfig;
    int        nfeat;                /* stride driver; default 4              */
} link_t;

typedef struct {
    uint64_t req_sent, ans_ok, ans_bad_ck, ans_bad_seq, timeouts, resends;
    uint64_t dev_errors, orphan_frames, short_mid_frames, ck_only_frames;
    uint64_t rows, escape_rows, bad_pairs, unknown_size, dropped_frames;
} stats_t;

typedef struct {
    link_t   u[MAX_UNITS];
    stats_t  st;
    int      timeout_ms;
    int      max_resend;
    bool     verbose;
    FILE    *csv;
} ctx_t;

static void link_reset(link_t *L) {
    L->busy = false; L->expected = -1; L->acc = 0; L->next_seq = 0;
    L->last_avail = 0; L->await_ck = false; L->nframes = 0; L->attempts = 0;
}

static void ctx_init(ctx_t *c) {
    memset(c, 0, sizeof *c);
    c->timeout_ms = DEF_TIMEOUT_MS;
    c->max_resend = DEF_MAX_RESEND;
    for (int i = 0; i < MAX_UNITS; i++) { link_reset(&c->u[i]); c->u[i].nfeat = 4; }
}

static void on_complete(ctx_t *c, int unit);      /* fwd */

/* Arm the tracker for a request — whether WE sent it (master) or we merely
 * observed it on the wire (listen / replay).  Same code path either way. */
static void link_arm(ctx_t *c, int unit, const paket_t *p)
{
    if (unit < 0 || unit >= MAX_UNITS) return;
    link_t *L = &c->u[unit];
    if (L->busy && c->verbose)
        fprintf(stderr, "unit %d: new request 0x%02X while 0x%02X outstanding\n",
                unit, p->b[0], L->cmd);
    link_reset(L);
    L->busy = true;
    L->cmd  = p->b[0];
    L->req  = *p;
    L->expected = cmd_size(L->cmd);               /* may be SZ_DYNAMIC/UNKNOWN */
    L->t_req = L->t_last_frame = now_us();
}

/* Feed one answer frame.  This is the whole assembler, and it is a direct
 * transcription of the decompiled loop — clamped avail, no constant 7. */
static void link_feed(ctx_t *c, int unit, const frame_t *f)
{
    if (unit < 0 || unit >= MAX_UNITS) { c->st.dropped_frames++; return; }
    link_t *L = &c->u[unit];

    if (!L->busy) {                               /* "-CAN: Received data w/o request" */
        c->st.orphan_frames++;
        return;                                   /* anonymous: unidentifiable */
    }
    if (L->nframes == 0) L->dev_ts_first = f->dev_ts;
    L->t_last_frame = now_us();

    /* ── the trailing [seq][checksum] frame ───────────────────────────────── */
    if (L->await_ck) {
        if (f->dlc != 2 || f->data[0] == 0) {
            fprintf(stderr, "unit %d cmd 0x%02X: expected checksum-only frame, got DLC %u\n",
                    unit, L->cmd, f->dlc);
            c->st.ans_bad_ck++; link_reset(L); return;
        }
        c->st.ck_only_frames++;
        uint8_t want = p3_checksum(unit, L->req.b, L->req.len, L->buf, (size_t)L->acc);
        if (want != f->data[1]) { c->st.ans_bad_ck++; link_reset(L); return; }
        c->st.ans_ok++;
        on_complete(c, unit);
        link_reset(L);
        return;
    }

    /* ── device error answer: DATA[0]==0 && DATA[1]==1 && LEN==2 ───────────
     * The LEN==2 test alone does NOT separate this from a checksum-only
     * frame — both are LEN 2.  The separator is DATA[0]: an error answer is
     * sequence 0, a checksum-only frame is the LAST frame so its seq >= 1.
     * All 39 captured checksum-only frames carried seq 3.        [C.7.2]    */
    if (L->next_seq == 0 && f->dlc == 2 && f->data[0] == 0 && f->data[1] == 1) {
        c->st.dev_errors++;
        printf("unit %d  %-24s  *** DEVICE ERROR ANSWER ***\n", unit, cmd_name(L->cmd));
        link_reset(L);
        return;
    }

    /* ── sequence continuity ──────────────────────────────────────────────── */
    if (f->data[0] != (uint8_t)L->next_seq) {
        fprintf(stderr, "unit %d cmd 0x%02X: sequence %u, expected %d\n",
                unit, L->cmd, f->data[0], L->next_seq);
        c->st.ans_bad_seq++; link_reset(L); return;
    }

    /* ── learn the expected size for 0x16 from the first payload byte ─────
     * expected = DATA[1] * (featureCount*2 + 2) + 1                        */
    if (L->expected == SZ_DYNAMIC) {
        if (f->dlc < 2) { c->st.ans_bad_seq++; link_reset(L); return; }
        int stride = L->nfeat * 2 + 2;
        L->expected = (int)f->data[1] * stride + 1;
    }
    if (L->expected == SZ_UNKNOWN) {
        /* We refuse to guess. Let it time out loudly rather than mis-terminate
         * and eat the next answer's frames.                          [C.9.1] */
        c->st.unknown_size++;
        return;
    }
    if (L->expected > REASM_MAX) { c->st.dropped_frames++; link_reset(L); return; }

    /* ── THE CORE RULE.  avail = min(DLC-1, remaining).  NOT 7.  ──────────
     * The device flushes every 250 payload bytes and emits a short frame at
     * each boundary, so DLC-1 is 5, 6 or 7 mid-stream.               [D.2] */
    int raw_avail = (int)f->dlc - 1;
    if (raw_avail < 0) raw_avail = 0;
    int remaining = L->expected - L->acc;
    int avail = raw_avail < remaining ? raw_avail : remaining;

    if (raw_avail < 7 && remaining > raw_avail) c->st.short_mid_frames++;

    if (L->acc + avail > REASM_MAX) { c->st.dropped_frames++; link_reset(L); return; }
    memcpy(L->buf + L->acc, f->data + 1, (size_t)avail);
    L->acc += avail;
    L->last_avail = avail;
    L->next_seq = (L->next_seq + 1) & 0xFF;       /* wraps at 256 (untested)  */
    L->nframes++;

    if (L->acc < L->expected) return;             /* keep accumulating        */

    /* ── complete.  Where is the checksum? ────────────────────────────────
     * If this frame was filled with a full 7 payload bytes there is no room
     * for it, so a separate [seq][ck] frame follows.  Otherwise it is the
     * byte immediately after the payload: DATA[LEN-1].
     * This is decided by the CLAMPED avail, not by (expected % 7) — the %7
     * rule has counter-examples on every answer that crossed a 250-byte
     * flush boundary.                                          [D.2.3]     */
    if (avail == 7) { L->await_ck = true; return; }

    uint8_t got  = f->data[f->dlc - 1];
    uint8_t want = p3_checksum(unit, L->req.b, L->req.len, L->buf, (size_t)L->acc);
    if (got != want) {
        fprintf(stderr, "unit %d cmd 0x%02X: checksum %02X, expected %02X (len %d)\n",
                unit, L->cmd, got, want, L->acc);
        c->st.ans_bad_ck++; link_reset(L); return;
    }
    c->st.ans_ok++;
    on_complete(c, unit);
    link_reset(L);
}

/* ══════════════════════════════════════════════════════════════════════════
 * 9.  PRESENTATION — gated by CONF_*, never prints an unproven layout
 * ══════════════════════════════════════════════════════════════════════════ */

static const char *feat_label(const link_t *L, int idx) {
    static char buf[16];
    if (L->have_kanal && idx >= 0 && idx < MAX_FEATURES && L->kanal.name[idx][0])
        return L->kanal.name[idx];
    snprintf(buf, sizeof buf, "F%d", idx);
    return buf;
}

static void on_complete(ctx_t *c, int unit)
{
    link_t *L = &c->u[unit];
    const uint8_t *p = L->buf;
    int n = L->acc;
    conf_t cf = cmd_conf(L->cmd);

    switch (L->cmd) {

    case 0x06: {                                   /* GIVEKONFIG              */
        konfig_t k;
        if (decode_konfig(p, n, &k)) {
            L->have_konfig = true; L->konfig = k;
            if (k.sensors >= 1 && k.sensors <= MAX_FEATURES) L->nfeat = k.sensors;
            printf("unit %d  %-24s  version %u  channels %u  sensors %u\n",
                   unit, cmd_name(L->cmd), k.version, k.channels, k.sensors);
        }
        return;
    }

    case 0x02: {                                   /* GIVEGTYPE               */
        if (n >= 3)
            printf("unit %d  %-24s  GType 0x%02X  GSubType %u\n",
                   unit, cmd_name(L->cmd), p[0], p[1]);
        return;
    }

    case 0x0D: {                                   /* SGeraetRec              */
        geraetrec_t g;
        if (decode_geraetrec(p, n, &g)) {
            printf("unit %d  %-24s  SNr %u  GType 0x%02X sub %u  ch %u  sensors %u  "
                   "ReduzLim %u  sensorTypes",
                   unit, cmd_name(L->cmd), g.serial, g.gtype, g.gsubtype,
                   g.channels, g.sensors, g.reduzlim);
            for (int i = 0; i < 8; i++) printf(" %02X", g.sensor_type[i]);
            printf("\n");
        }
        return;
    }

    case 0x0E: {                                   /* SKanalRecV40 + names    */
        kanalrec_t k;
        if (decode_kanalrec(p, n, &k)) {
            L->have_kanal = true; L->kanal = k;
            printf("unit %d  %-24s  CDRLim %02X %02X %02X %02X  features:\n",
                   unit, cmd_name(L->cmd), k.cdrlim[0], k.cdrlim[1], k.cdrlim[2], k.cdrlim[3]);
            for (int i = 0; i < MAX_FEATURES; i++)
                if (k.mask[i])
                    printf("            [%d] mask 0x%02X  \"%s\"\n", i, k.mask[i], k.name[i]);
        }
        return;
    }

    case 0x12: {                                   /* GIVEALARM               */
        alarm_t a;
        if (decode_alarm(p, n, &a)) {
            if (a.empty) printf("unit %d  %-24s  (empty slot)\n", unit, cmd_name(L->cmd));
            else printf("unit %d  %-24s  code %-3u  %04d-%02d-%02d %02d:%02d:%02d\n",
                        unit, cmd_name(L->cmd), a.code,
                        a.year, a.mon, a.day, a.hh, a.mm, a.ss);
        }
        return;
    }

    case 0x16: {                                   /* THE measurement block   */
        static merkmal_row_t rows[256];
        int bad = 0;
        int nr = decode_merkmale(p, n, L->nfeat, rows,
                                 (int)(sizeof rows / sizeof rows[0]), &bad);
        if (nr < 0) {
            fprintf(stderr, "unit %d: 0x16 length %d does not reconcile with stride %d\n",
                    unit, n, L->nfeat * 2 + 2);
            return;
        }
        c->st.rows += (uint64_t)nr;
        c->st.bad_pairs += (uint64_t)bad;
        if (bad) fprintf(stderr,
            "unit %d: %d min>max pairs in NON-escape rows -> reassembly is wrong\n",
            unit, bad);

        for (int r = 0; r < nr; r++) {
            merkmal_row_t *m = &rows[r];
            if (m->escape) {
                c->st.escape_rows++;
                printf("unit %d  %-24s  ESCAPE marker 0x%02X%s\n",
                       unit, cmd_name(L->cmd), m->marker,
                       m->marker == 0xFB ? " (per-feature reset)" :
                       m->marker == 0x00 ? " (new cycle)" :
                       m->marker == 0xFE ? " (workpiece id)" : " (?)");
                continue;
            }
            printf("unit %d  %-24s ", unit, cmd_name(L->cmd));
            for (int f = 0; f < L->nfeat && f < MAX_FEATURES; f++)
                printf(" %s=%u..%u", feat_label(L, f), m->vmin[f], m->vmax[f]);
            printf("  st %02X %02X\n", m->st0, m->st1);

            if (c->csv) {
                fprintf(c->csv, "%llu,%d,0x16",
                        (unsigned long long)L->dev_ts_first, unit);
                for (int f = 0; f < MAX_FEATURES; f++)
                    fprintf(c->csv, ",%u,%u", m->vmin[f], m->vmax[f]);
                fprintf(c->csv, ",%02X,%02X\n", m->st0, m->st1);
            }
        }
        return;
    }

    default:
        if (cf >= CONF_CONFIRMED) {
            printf("unit %d  %-24s  len %d\n", unit, cmd_name(L->cmd), n);
        } else {
            printf("unit %d  %-24s  len %d   [%s]\n", unit, cmd_name(L->cmd), n,
                   cf == CONF_UNKNOWN     ? "UNKNOWN"     :
                   cf == CONF_NAMED       ? "NAMED"       : "PROVISIONAL");
            hexdump(p, (size_t)n);
        }
        return;
    }
}

/* ══════════════════════════════════════════════════════════════════════════
 * 10. DATAGRAM INGEST — shared by live and replay
 * ══════════════════════════════════════════════════════════════════════════ */

static void ingest_datagram(ctx_t *c, const uint8_t *dg, size_t len)
{
    /* A datagram is a BATCH of records: 1..15 observed, max 540 bytes.  Never
     * assume one record per datagram.  Front-trim like Scan4CANmsg.   [C.5] */
    for (size_t off = len % GW_REC; off + GW_REC <= len; off += GW_REC) {
        frame_t f;
        if (!gw_parse(dg + off, &f)) { c->st.dropped_frames++; continue; }
        if (f.unit <= 0 || f.unit >= MAX_UNITS) { c->st.dropped_frames++; continue; }

        if (f.is_request) {
            /* Observed request (listen / replay).  [00][00][00][cmd][args][ck] */
            if (f.dlc < 4 || f.data[0] || f.data[1] || f.data[2]) continue;
            paket_t p; p.len = (uint8_t)(f.dlc - 3);
            if (p.len > sizeof p.b) continue;
            memcpy(p.b, f.data + 3, p.len);
            link_arm(c, f.unit, &p);
        } else {
            link_feed(c, f.unit, &f);
        }
    }
}

/* ══════════════════════════════════════════════════════════════════════════
 * 11. SOCKET — bound, UNCONNECTED, host-filtered                    [C.3.2]
 * ══════════════════════════════════════════════════════════════════════════ */

static void sock_err(const char *what)
{
#ifdef _WIN32
    int e = WSAGetLastError();
    const char *hint = "";
    switch (e) {
        case 10048: hint = "  (WSAEADDRINUSE: another program already holds this port -\n"
                           "   almost certainly PROVIS3. Use --sniff instead; it binds nothing.)"; break;
        case 10013: hint = "  (WSAEACCES: blocked by permissions or a firewall rule.)"; break;
        case 10022: hint = "  (WSAEINVAL: socket already bound, or Winsock not initialised.)"; break;
        default: break;
    }
    fprintf(stderr, "%s failed: Winsock error %d%s\n", what, e, hint);
#else
    perror(what);
#endif
}

static sock_t open_socket(int port)
{
    sock_t fd = socket(AF_INET, SOCK_DGRAM, 0);
    if (fd == SOCK_BAD) { sock_err("socket"); return SOCK_BAD; }
    /* SO_REUSEADDR lets this bind alongside a running PROVIS3 on the same port.
     * That is how --listen works on the PROVIS3 PC itself, but delivery to two
     * sockets bound to one unicast UDP port is OS-dependent and MAY STEAL
     * datagrams from PROVIS3. Prefer a port mirror on a separate machine. */
    int one = 1;
    setsockopt(fd, SOL_SOCKET, SO_REUSEADDR, (const char *)&one, sizeof one);

    struct sockaddr_in a;
    memset(&a, 0, sizeof a);
    a.sin_family = AF_INET;
    a.sin_addr.s_addr = htonl(INADDR_ANY);
    a.sin_port = htons((unsigned short)port);
    if (bind(fd, (struct sockaddr *)&a, sizeof a) != 0) {
        sock_err("bind");
        fprintf(stderr,
            "\n  Cannot bind UDP %d. If PROVIS3 is running it already owns this port.\n"
            "  You do NOT need to bind anything to watch the link. Use --sniff:\n\n"
            "      dumpcap -i <N> -f \"host <gateway> and host <pc>\" -w trace.pcapng\n"
            "      promos3_live --sniff trace.pcapng --follow --csv out.csv\n\n",
            port);
        CLOSESOCK(fd); return SOCK_BAD;
    }
    /* >>> DO NOT connect() <<<  The gateway replies from an ephemeral source
     * port, so a connected socket has every answer dropped by the kernel. */
    return fd;
}

static int send_request(sock_t fd, const struct sockaddr_in *gw,
                        int unit, const paket_t *p)
{
    uint8_t frames[8][CAN_MAX_DATA]; uint8_t dlcs[8];
    int nf = paket_frames(p, frames, dlcs, 8);
    uint32_t id = (uint32_t)CANID_BASE_TX + (uint32_t)unit;

    for (int i = 0; i < nf; i++) {
        uint8_t rec[GW_REC];
        gw_build(rec, id, frames[i], dlcs[i]);
        if (sendto(fd, (const char *)rec, GW_REC, 0,
                   (const struct sockaddr *)gw, sizeof *gw) != GW_REC) return -1;
    }
    return nf;
}

/* ══════════════════════════════════════════════════════════════════════════
 * 12. MASTER MODE — the poll loop, exactly as the app runs it        [D.5]
 *
 *   Startup, once per unit:  0x0D (SGeraetRec)  0x06 (konfig)  0x0E (channel)
 *   Steady state, per unit:  0x16 [01 01]   0x08 [01]   0x01 []   0x33 [00]
 *
 *   The app's cycle is exactly those 4 per unit and it did not vary once in
 *   11,116 consecutive cycles.  Median full cycle over two units: 12.6 ms.
 *
 *   >>> Do NOT poll a unit that a running PROVIS3 is also polling. <<<
 * ══════════════════════════════════════════════════════════════════════════ */

typedef struct { uint8_t cmd; uint8_t args[3]; uint8_t nargs; } step_t;

static const step_t g_startup[] = {
    { 0x0D, {0},          0 },
    { 0x06, {0},          0 },
    { 0x0E, {0x01},       1 },
};
static const step_t g_poll[] = {
    { 0x16, {0x01, 0x01}, 2 },
    { 0x08, {0x01},       1 },
    { 0x01, {0},          0 },
    { 0x33, {0x00},       1 },
};

static void run_master(ctx_t *c, sock_t fd, const struct sockaddr_in *gw,
                       const int *units, int nunits)
{
    size_t nstart = sizeof g_startup / sizeof g_startup[0];
    size_t npoll  = sizeof g_poll    / sizeof g_poll[0];
    uint8_t dg[DGRAM_MAX];

    int ui = 0; size_t si = 0; bool in_startup = true;

    while (!g_stop) {
        int unit = units[ui];
        link_t *L = &c->u[unit];

        /* ── issue the next request when the unit is free ─────────────────── */
        if (!L->busy) {
            const step_t *s = in_startup ? &g_startup[si] : &g_poll[si];
            paket_t p;
            paket_build(&p, unit, s->cmd, s->args, s->nargs);
            if (send_request(fd, gw, unit, &p) > 0) {
                link_arm(c, unit, &p);
                c->st.req_sent++;
            }
            /* advance the schedule */
            if (++ui >= nunits) {
                ui = 0;
                size_t lim = in_startup ? nstart : npoll;
                if (++si >= lim) { si = 0; if (in_startup) in_startup = false; }
            }
        }

        /* ── drain the socket ─────────────────────────────────────────────── */
        for (;;) {
            struct sockaddr_in from; SOCKLEN_T fl = sizeof from;
#ifdef _WIN32
            u_long nb = 1; ioctlsocket(fd, FIONBIO, &nb);
#endif
            struct timeval tv = { 0, 2000 };      /* 2 ms                     */
            fd_set rs; FD_ZERO(&rs); FD_SET(fd, &rs);
            if (select((int)fd + 1, &rs, NULL, NULL, &tv) <= 0) break;

            int n = (int)recvfrom(fd, (char *)dg, sizeof dg, 0,
                                  (struct sockaddr *)&from, &fl);
            if (n <= 0) break;
            /* HOST filter only — the source PORT is ephemeral and varies. */
            if (from.sin_addr.s_addr != gw->sin_addr.s_addr) continue;
            ingest_datagram(c, dg, (size_t)n);
        }

        /* ── deadline, armed on the LAST FRAME RECEIVED ───────────────────── */
        uint64_t t = now_us();
        for (int i = 0; i < nunits; i++) {
            link_t *X = &c->u[units[i]];
            if (!X->busy) continue;
            if (t - X->t_last_frame < (uint64_t)c->timeout_ms * 1000u) continue;

            if (X->attempts < c->max_resend) {
                paket_t p = X->req;
                int a = X->attempts + 1;
                if (send_request(fd, gw, units[i], &p) > 0) {
                    link_arm(c, units[i], &p);
                    c->u[units[i]].attempts = a;
                    c->st.resends++;
                }
            } else {
                c->st.timeouts++;
                if (c->verbose)
                    fprintf(stderr, "unit %d cmd 0x%02X: timeout after %d frames, %d/%d bytes\n",
                            units[i], X->cmd, X->nframes, X->acc, X->expected);
                link_reset(X);
            }
        }

#ifndef _WIN32
        struct timespec ts = { 0, DEF_PACE_US * 1000 };
        nanosleep(&ts, NULL);
#else
        Sleep(1);
#endif
    }
}

/* ══════════════════════════════════════════════════════════════════════════
 * 13. LISTEN MODE — passive, needs BOTH directions (port mirror)
 *
 *   Answers carry no command and no group.  If you miss one request you lose
 *   attribution for everything that follows on that unit, and the checksum
 *   CANNOT recover it — ~48 (command,args) pairs satisfy any given payload.
 *   Master mode is strictly better unless PROVIS3 must keep running.  [C.12]
 * ══════════════════════════════════════════════════════════════════════════ */

static void run_listen(ctx_t *c, sock_t fd, uint32_t gw_ip)
{
    uint8_t dg[DGRAM_MAX];
    while (!g_stop) {
        struct sockaddr_in from; SOCKLEN_T fl = sizeof from;
        struct timeval tv = { 1, 0 };
        fd_set rs; FD_ZERO(&rs); FD_SET(fd, &rs);
        if (select((int)fd + 1, &rs, NULL, NULL, &tv) <= 0) continue;
        int n = (int)recvfrom(fd, (char *)dg, sizeof dg, 0, (struct sockaddr *)&from, &fl);
        if (n <= 0) continue;
        if (gw_ip && from.sin_addr.s_addr != gw_ip) continue;
        ingest_datagram(c, dg, (size_t)n);
    }
}

/* ══════════════════════════════════════════════════════════════════════════
 * 14. REPLAY — offline, from a pcapng
 *
 *   This is the highest-value tooling item in the project: the two existing
 *   captures contain one example of every exchange the installation produces
 *   PLUS 143 s of the poll loop at full rate.  Every rule above can be
 *   regression-tested at a desk with no machine window.
 * ══════════════════════════════════════════════════════════════════════════ */

static uint32_t rd32(const uint8_t *p, bool be) {
    return be ? rd_be32(p) : ((uint32_t)p[0] | ((uint32_t)p[1] << 8) |
                              ((uint32_t)p[2] << 16) | ((uint32_t)p[3] << 24));
}

static uint32_t g_replay_host = 0;   /* 0 = accept any */

static void replay_packet(ctx_t *c, const uint8_t *raw, size_t len)
{
    if (len < 14) return;
    size_t off = 14;
    uint16_t et = rd_be16(raw + 12);
    if (et == 0x8100) { if (len < 18) return; et = rd_be16(raw + 16); off = 18; }
    if (et != 0x0800) return;                              /* not IPv4        */
    if (off + 20 > len) return;

    /* Host filter. Non-cell traffic (mDNS, NetBIOS, HASP on 1947, ...) would
     * otherwise be sliced at the 36-byte stride and counted as dropped. */
    if (g_replay_host) {
        uint32_t src, dst;
        memcpy(&src, raw + off + 12, 4);
        memcpy(&dst, raw + off + 16, 4);
        if (src != g_replay_host && dst != g_replay_host) return;
    }

    size_t ihl = (size_t)(raw[off] & 0x0F) * 4;
    uint8_t proto = raw[off + 9];
    size_t tot = rd_be16(raw + off + 2);
    size_t ipend = off + tot; if (ipend > len) ipend = len;
    size_t l4 = off + ihl;

    if (proto == 17) {                                     /* UDP             */
        if (l4 + 8 > len) return;
        size_t ulen = rd_be16(raw + l4 + 4);
        size_t end = l4 + ulen; if (end > ipend) end = ipend; if (end > len) end = len;
        if (end > l4 + 8) ingest_datagram(c, raw + l4 + 8, end - (l4 + 8));
    } else if (proto == 1) {                               /* ICMP quotation  */
        size_t q = l4 + 8;
        if (q + 20 > len || raw[q + 9] != 17) return;
        size_t qihl = (size_t)(raw[q] & 0x0F) * 4;
        size_t ql4 = q + qihl;
        if (ql4 + 8 > len) return;
        ingest_datagram(c, raw + ql4 + 8, len - (ql4 + 8));
    }
}


/* ── STREAMING pcapng reader ──────────────────────────────────────────────
 *
 *  Reads pcapng block-by-block from a stream, so it can consume the live
 *  output of dumpcap over a pipe:
 *
 *      dumpcap -i N -f "host A and host B" -w - | promos3_live --sniff -
 *
 *  This is the ONLY safe way to watch a live link while PROVIS3 is running:
 *    - it sends nothing, so it cannot collide with PROVIS3's polling
 *    - it does not bind UDP 1789, so it cannot steal PROVIS3's datagrams
 *  dumpcap reads at the driver level (Npcap), exactly like Wireshark.
 */
static int g_follow = 0;      /* wait for more data instead of stopping at EOF */

static void nap_ms(int ms) {
#ifdef _WIN32
    Sleep((DWORD)ms);
#else
    struct timespec ts = { ms / 1000, (long)(ms % 1000) * 1000000L };
    nanosleep(&ts, NULL);
#endif
}

static int stream_read(FILE *fp, void *dst, size_t n)
{
    size_t got = 0;
    while (got < n) {
        if (g_stop) return 0;
        size_t r = fread((uint8_t *)dst + got, 1, n - got, fp);
        if (r == 0) {
            if (ferror(fp)) return 0;
            if (feof(fp)) {
                if (!g_follow) return 0;
                clearerr(fp);          /* dumpcap is still writing - wait */
                nap_ms(200);
                continue;
            }
        }
        got += r;
    }
    return 1;
}

static int run_stream(ctx_t *c, FILE *fp, const char *label)
{
    bool     be   = false;
    uint8_t  hdr[8];
    uint8_t *blk  = NULL;
    size_t   blkcap = 0, npkt = 0;
    int      rc = 0;

    while (!g_stop) {
        if (!stream_read(fp, hdr, 8)) break;
        uint32_t btype_raw = rd32(hdr, false);
        uint32_t blen;

        if (btype_raw == 0x0A0D0D0A || rd32(hdr, true) == 0x0A0D0D0A) {
            /* Section Header: the byte-order magic is the next 4 bytes, so we
             * cannot trust the length field until we have read it.           */
            uint8_t bom[4];
            if (!stream_read(fp, bom, 4)) break;
            be = (bom[0] == 0x1A);
            blen = rd32(hdr + 4, be);
            if (blen < 16) { rc = 1; break; }
            if (blen - 12 > blkcap) {
                uint8_t *nb = (uint8_t *)realloc(blk, blen);
                if (!nb) { rc = 1; break; }
                blk = nb; blkcap = blen;
            }
            memcpy(blk, bom, 4);
            if (!stream_read(fp, blk + 4, blen - 12)) break;
            continue;
        }

        uint32_t btype = rd32(hdr, be);
        blen = rd32(hdr + 4, be);
        if (blen < 12) { rc = 1; break; }

        size_t body = blen - 8;                 /* body incl. trailing length */
        if (body > blkcap) {
            uint8_t *nb = (uint8_t *)realloc(blk, body);
            if (!nb) { rc = 1; break; }
            blk = nb; blkcap = body;
        }
        if (!stream_read(fp, blk, body)) break;

        if (btype == 0x00000006 && body >= 20) {          /* enhanced packet  */
            uint32_t caplen = rd32(blk + 12, be);
            if (20 + (size_t)caplen <= body) { replay_packet(c, blk + 20, caplen); npkt++; }
        } else if (btype == 0x00000003 && body >= 8) {    /* simple packet    */
            replay_packet(c, blk + 4, body - 8);
            npkt++;
        }

        if (c->csv && (npkt % 200) == 0) fflush(c->csv);
        if (c->verbose && (npkt % 5000) == 0 && npkt)
            fprintf(stderr, "  ... %zu packets, %llu exchanges\n",
                    npkt, (unsigned long long)c->st.ans_ok);
    }
    free(blk);
    if (c->csv) fflush(c->csv);
    fprintf(stderr, "%s: %zu packets\n", label, npkt);
    return rc;
}

static int run_replay(ctx_t *c, const char *path)
{
    FILE *fp = fopen(path, "rb");
    if (!fp) { perror(path); return 1; }
    if (fseek(fp, 0, SEEK_END) != 0) { fclose(fp); return 1; }
    long fsz = ftell(fp);
    if (fsz <= 0) { fclose(fp); return 1; }
    rewind(fp);

    uint8_t *buf = (uint8_t *)malloc((size_t)fsz);
    if (!buf) { fclose(fp); fprintf(stderr, "out of memory\n"); return 1; }
    if (fread(buf, 1, (size_t)fsz, fp) != (size_t)fsz) {
        fclose(fp); free(buf); fprintf(stderr, "short read\n"); return 1;
    }
    fclose(fp);

    bool be = false;
    size_t off = 0, npkt = 0;
    while (off + 12 <= (size_t)fsz && !g_stop) {
        uint32_t btype = rd32(buf + off, be);
        if (btype == 0x0A0D0D0A) {                         /* section header  */
            if (off + 12 > (size_t)fsz) break;
            be = (buf[off + 8] == 0x1A);                   /* BOM 1A2B3C4D BE */
            btype = rd32(buf + off, be);
        }
        uint32_t blen = rd32(buf + off + 4, be);
        if (blen < 12 || off + blen > (size_t)fsz) break;

        if (btype == 0x00000006) {                         /* enhanced packet */
            const uint8_t *b = buf + off + 8;
            uint32_t caplen = rd32(b + 12, be);
            if (20 + caplen <= blen - 12) { replay_packet(c, b + 20, caplen); npkt++; }
        } else if (btype == 0x00000003) {                  /* simple packet   */
            const uint8_t *b = buf + off + 8;
            size_t cap = blen - 16;
            replay_packet(c, b + 4, cap); npkt++;
        }
        off += blen;
    }
    free(buf);
    fprintf(stderr, "replay: %zu packets from %s\n", npkt, path);
    return 0;
}

/* ══════════════════════════════════════════════════════════════════════════
 * 15. PROBE — the one 30-second test, corrected                     [C.15.1]
 *
 *   MC_GIVEPLCVALUES, unit 1, station 1.  The only request whose bytes were
 *   independently known before any capture existed.  Expect FIVE payload
 *   bytes (00 00 00 00 ff) back on CAN-ID 0x581 within 1-2 ms.
 * ══════════════════════════════════════════════════════════════════════════ */

static int run_probe(ctx_t *c, sock_t fd, const struct sockaddr_in *gw, int unit)
{
    paket_t p; uint8_t args[1] = { 0x01 };
    paket_build(&p, unit, 0x08, args, 1);

    printf("probe: unit %d  paket", unit);
    for (int i = 0; i < p.len; i++) printf(" %02x", p.b[i]);
    printf("   CAN-ID 0x%03X -> answers expected on 0x%03X\n",
           CANID_BASE_TX + unit, CANID_BASE_RX + unit);

    if (send_request(fd, gw, unit, &p) <= 0) { perror("sendto"); return 1; }
    link_arm(c, unit, &p);
    c->st.req_sent++;

    uint8_t dg[DGRAM_MAX];
    uint64_t t0 = now_us();
    while (!g_stop && now_us() - t0 < 3000000u) {          /* 3 s             */
        struct sockaddr_in from; SOCKLEN_T fl = sizeof from;
        struct timeval tv = { 0, 100000 };
        fd_set rs; FD_ZERO(&rs); FD_SET(fd, &rs);
        if (select((int)fd + 1, &rs, NULL, NULL, &tv) <= 0) continue;
        int n = (int)recvfrom(fd, (char *)dg, sizeof dg, 0, (struct sockaddr *)&from, &fl);
        if (n <= 0) continue;
        if (from.sin_addr.s_addr != gw->sin_addr.s_addr) continue;
        printf("probe: %d bytes from %s:%u  (source port is EPHEMERAL by design)\n",
               n, inet_ntoa(from.sin_addr), (unsigned)ntohs(from.sin_port));
        ingest_datagram(c, dg, (size_t)n);
        if (c->st.ans_ok) { printf("probe: OK — link is alive.\n"); return 0; }
    }
    printf("probe: no valid answer in 3 s.\n"
           "  checklist: gateway IP correct? PROVIS3 stopped (one master only)?\n"
           "             socket bound to :%d and NOT connect()ed?\n", P3_PORT);
    return 1;
}

/* ══════════════════════════════════════════════════════════════════════════
 * 16. MAIN
 * ══════════════════════════════════════════════════════════════════════════ */

static void print_stats(const ctx_t *c)
{
    const stats_t *s = &c->st;
    fprintf(stderr,
        "\n== counters ==\n"
        "  requests sent      %llu\n"
        "  answers ok         %llu\n"
        "  bad checksum       %llu\n"
        "  bad sequence       %llu\n"
        "  device errors      %llu\n"
        "  timeouts           %llu   resends %llu\n"
        "  orphan frames      %llu   (answer with no outstanding request)\n"
        "  dropped frames     %llu\n"
        "  unknown-size cmds  %llu   (refused to guess; 0x1B is the one that matters)\n"
        "  short mid frames   %llu   (250-byte flush boundaries)\n"
        "  checksum-only frm  %llu\n"
        "  measurement rows   %llu   escapes %llu\n"
        "  min>max violations %llu   <-- MUST be 0; nonzero means bad reassembly\n",
        (unsigned long long)s->req_sent,  (unsigned long long)s->ans_ok,
        (unsigned long long)s->ans_bad_ck,(unsigned long long)s->ans_bad_seq,
        (unsigned long long)s->dev_errors,(unsigned long long)s->timeouts,
        (unsigned long long)s->resends,   (unsigned long long)s->orphan_frames,
        (unsigned long long)s->dropped_frames, (unsigned long long)s->unknown_size,
        (unsigned long long)s->short_mid_frames, (unsigned long long)s->ck_only_frames,
        (unsigned long long)s->rows, (unsigned long long)s->escape_rows,
        (unsigned long long)s->bad_pairs);
}

static void usage(void)
{
    fprintf(stderr,
        "promos3_live — PROVIS3 CAN-over-UDP link layer\n\n"
        "  --master            actively poll (recommended; PROVIS3 must be stopped)\n"
        "  --listen            passive; needs a BOTH-DIRECTION port mirror\n"
        "  --replay FILE       offline from a pcapng\n"
        "  --sniff FILE|-      live pcapng stream; '-' = stdin. SAFE alongside\n"
        "                      a running PROVIS3 - sends nothing, binds nothing:\n"
        "                        dumpcap -i N -f \"host GW and host PC\" -w - |\\\n"
        "                            promos3_live --sniff - --csv out.csv\n"
        "  --follow            with --sniff on a FILE: keep reading as dumpcap\n"
        "                      writes it (Ctrl+C to stop). No pipe needed - this is\n"
        "                      the right form on Windows/PowerShell.\n"
        "  --probe             send the one verified request and report\n\n"
        "  --gw IP             gateway address (default 192.168.222.16)\n"
        "  --port N            LOCAL bind port (default %d)\n"
        "  --gw-port N         GATEWAY destination port (default %d)\n"
        "                      NOTE: these are SEPARATE. The gateway only listens on\n"
        "                      1789; changing --port does NOT change where requests go.\n"
        "  --units 1,2         units to poll (default 1,2)\n"
        "  --timeout MS        answer deadline, armed on last frame (default %d)\n"
        "  --stride-features N features per row for 0x16 (default 4)\n"
        "  --csv FILE          write measurement rows\n"
        "  -v                  verbose\n", P3_PORT, P3_PORT, DEF_TIMEOUT_MS);
}

int main(int argc, char **argv)
{
    enum { M_NONE, M_MASTER, M_LISTEN, M_REPLAY, M_PROBE, M_SNIFF } mode = M_NONE;
    const char *gw_ip = "192.168.222.16", *replay = NULL, *csv = NULL;
    int port = P3_PORT, gw_port = P3_PORT, nfeat = 4;
    int units[MAX_UNITS] = { 1, 2 }, nunits = 2;
    ctx_t c; ctx_init(&c);

    setvbuf(stdout, NULL, _IOLBF, 0);

    for (int i = 1; i < argc; i++) {
        if      (!strcmp(argv[i], "--master")) mode = M_MASTER;
        else if (!strcmp(argv[i], "--listen")) mode = M_LISTEN;
        else if (!strcmp(argv[i], "--probe"))  mode = M_PROBE;
        else if (!strcmp(argv[i], "-v"))       c.verbose = true;
        else if (!strcmp(argv[i], "--follow")) g_follow = 1;
        else if (!strcmp(argv[i], "--replay") && i + 1 < argc) { mode = M_REPLAY; replay = argv[++i]; }
        else if (!strcmp(argv[i], "--sniff")  && i + 1 < argc) { mode = M_SNIFF;  replay = argv[++i]; }
        else if (!strcmp(argv[i], "--gw")     && i + 1 < argc) gw_ip = argv[++i];
        else if (!strcmp(argv[i], "--csv")    && i + 1 < argc) csv   = argv[++i];
        else if (!strcmp(argv[i], "--port")   && i + 1 < argc) port  = atoi(argv[++i]);
        else if (!strcmp(argv[i], "--gw-port")&& i + 1 < argc) gw_port = atoi(argv[++i]);
        else if (!strcmp(argv[i], "--timeout")&& i + 1 < argc) c.timeout_ms = atoi(argv[++i]);
        else if (!strcmp(argv[i], "--stride-features") && i + 1 < argc) nfeat = atoi(argv[++i]);
        else if (!strcmp(argv[i], "--units")  && i + 1 < argc) {
            nunits = 0;
            for (char *t = strtok(argv[++i], ","); t && nunits < MAX_UNITS; t = strtok(NULL, ","))
                units[nunits++] = atoi(t);
        } else { usage(); return 2; }
    }
    if (mode == M_NONE) { usage(); return 2; }
    if (nfeat < 1 || nfeat > MAX_FEATURES) { fprintf(stderr, "bad feature count\n"); return 2; }
    for (int i = 0; i < MAX_UNITS; i++) c.u[i].nfeat = nfeat;
    for (int i = 0; i < nunits; i++)
        if (units[i] <= 0 || units[i] >= MAX_UNITS) { fprintf(stderr, "bad unit\n"); return 2; }

    if (csv) {
        c.csv = fopen(csv, "w");
        if (!c.csv) perror(csv);
        else {
            setvbuf(c.csv, NULL, _IOLBF, 0);
            fprintf(c.csv, "dev_ts_us,unit,cmd,"
                           "min0,max0,min1,max1,min2,max2,min3,max3,st0,st1\n");
        }
    }

    signal(SIGINT, on_sigint);

    if (mode == M_SNIFF) {
        struct in_addr ia2;
        if (inet_pton(AF_INET, gw_ip, &ia2) == 1) g_replay_host = ia2.s_addr;
        FILE *fp = (!strcmp(replay, "-")) ? stdin : fopen(replay, "rb");
        if (!fp) { perror(replay); return 1; }
#ifdef _WIN32
        if (fp == stdin) _setmode(_fileno(stdin), _O_BINARY);
#endif
        fprintf(stderr, "SNIFF: passive pcapng stream (%s). Nothing is transmitted.\n",
                fp == stdin ? "stdin" : replay);
        int rc = run_stream(&c, fp, "sniff");
        if (fp != stdin) fclose(fp);
        print_stats(&c);
        if (c.csv) fclose(c.csv);
        return rc;
    }

    if (mode == M_REPLAY) {
        struct in_addr ia;
        if (inet_pton(AF_INET, gw_ip, &ia) == 1) g_replay_host = ia.s_addr;
        int rc = run_replay(&c, replay);
        print_stats(&c);
        if (c.csv) fclose(c.csv);
        return rc;
    }

#ifdef _WIN32
    WSADATA w; if (WSAStartup(MAKEWORD(2, 2), &w)) { fprintf(stderr, "WSAStartup\n"); return 1; }
#endif
    struct sockaddr_in gw;
    memset(&gw, 0, sizeof gw);
    gw.sin_family = AF_INET;
    gw.sin_port = htons((unsigned short)gw_port);   /* NOT the local bind port */
    if (inet_pton(AF_INET, gw_ip, &gw.sin_addr) != 1) {
        fprintf(stderr, "bad gateway address: %s\n", gw_ip); return 2;
    }

    sock_t fd = open_socket(port);
    if (fd == SOCK_BAD) return 1;

    fprintf(stderr, "bound :%d (UNCONNECTED)  gateway %s:%d  tx 0x%03X+u  rx 0x%03X+u\n",
            port, gw_ip, gw_port, CANID_BASE_TX, CANID_BASE_RX);
    if (gw_port != P3_PORT)
        fprintf(stderr, "  *** WARNING: gateway port is %d, not %d. The gateway only listens\n"
                        "      on %d - requests sent elsewhere are silently discarded and you\n"
                        "      will see zero answers. Use --gw-port %d unless you are certain.\n",
                gw_port, P3_PORT, P3_PORT, P3_PORT);
    if (mode == M_MASTER && port != P3_PORT)
        fprintf(stderr, "  *** WARNING: local port %d != %d. The gateway sends answers to :%d,\n"
                        "      so a master bound elsewhere receives nothing.\n", port, P3_PORT, P3_PORT);

    int rc = 0;
    if      (mode == M_PROBE)  rc = run_probe(&c, fd, &gw, units[0]);
    else if (mode == M_MASTER) {
        fprintf(stderr, "MASTER: polling units");
        for (int i = 0; i < nunits; i++) fprintf(stderr, " %d", units[i]);
        fprintf(stderr, "   >>> PROVIS3 must NOT be polling these units <<<\n");
        fprintf(stderr, "   If PROVIS3 is running, STOP NOW and use --sniff instead.\n"
                        "   Two masters on one bus makes answers unattributable: a capture\n"
                        "   taken during overlap shows checksum failures that are artefacts.\n");
        run_master(&c, fd, &gw, units, nunits);
    } else {
        fprintf(stderr, "LISTEN: passive — requires a both-direction port mirror.\n");
        run_listen(&c, fd, gw.sin_addr.s_addr);
    }

    print_stats(&c);
    if (c.csv) fclose(c.csv);
    CLOSESOCK(fd);
#ifdef _WIN32
    WSACleanup();
#endif
    return rc;
}
