/* ============================================================================
 * promos3_view.c  --  Prometec PROVIS3 / Promos3 "MC_" protocol READER.
 *
 * It turns CAN-over-UDP traffic back into the numbers the original HMI puts on
 * screen, and says, per packet, WHAT IT IS FOR: which widget it feeds, which
 * database table it ends up in, what the operator would actually see.
 *
 * Companion program: promos3_sim.c  (the synthetic machine that produces it).
 *
 * ---------------------------------------------------------------------------
 * BUILD - nothing to install, no third-party library, no .lib hunting
 *
 *   Windows / MinGW  (-lws2_32 goes LAST; that ordering is the whole reason
 *                     for the classic "undefined reference to `recvfrom'"):
 *       gcc -std=c11 -O2 -Wall -Wextra promos3_view.c -o promos3_view.exe -lws2_32
 *
 *   Windows / MSVC   (library named by the #pragma below, so
 *                     "LNK1104: cannot open file 'ws2_32.lib'" cannot occur):
 *       cl /nologo /W3 /O2 promos3_view.c
 *
 *   Linux / macOS:
 *       cc -std=c11 -O2 -Wall -Wextra promos3_view.c -o promos3_view
 *
 *   NO SOCKETS AT ALL (replay a capture file; links zero libraries):
 *       gcc -std=c11 -O2 -DP3_NO_NET promos3_view.c -o promos3_view
 *
 * TRY IT WITH NO MACHINE, two terminals:
 *       promos3_sim  --serve
 *       promos3_view --master --gateway 127.0.0.1:1789
 * or with no network at all:
 *       promos3_sim  --out shift.cap --cycles 5
 *       promos3_view --replay shift.cap
 *
 * CHECK IT BEFORE YOU TRUST IT:
 *       promos3_view --selftest      (11 checks, no network, no machine)
 *
 * Note: -std=c89 also builds; the only complaint is -Woverlength-strings
 * about the --help text, which every real compiler accepts.
 *
 * ---------------------------------------------------------------------------
 * THE ONE RULE THIS PROGRAM OBEYS
 *   It never prints a decoded value whose byte layout is unproven as if it
 *   were fact. Every block carries [verified] / [table] / [assumed], and
 *   anything assumed is shown as raw bytes next to the interpretation, so
 *   holding this screen beside the real HMI settles the layout for good.
 *
 * WHY THERE IS A --master MODE AT ALL
 *   An MC_ answer carries no command, no group and no length. Those fields are
 *   inherited from the request that is still outstanding. A one-directional
 *   listener therefore sees anonymous byte blobs; only the asker knows what
 *   came back. That single fact is the most important design constraint in
 *   this protocol, and it is why the reader asks the questions itself.
 *
 * STYLE - data-oriented, pragmatic functional: plain-data structs, pure
 * transforms in sections 3-6, all I/O confined to sections 7-9, behaviour
 * driven by tables rather than by control flow.
 * ==========================================================================*/

#if !defined(_WIN32) && !defined(_POSIX_C_SOURCE)
#  define _POSIX_C_SOURCE 200809L
#endif
#ifdef _MSC_VER
#  define _CRT_SECURE_NO_WARNINGS 1
#  define _WINSOCK_DEPRECATED_NO_WARNINGS 1
#endif

#include <stdio.h>
#include <stdlib.h>
#include <stdarg.h>
#include <string.h>
#include <time.h>
#include <signal.h>

/* ===========================================================================
 * SECTION 1 -- PORTABILITY SHIMS (identical to promos3_sim.c)
 * ========================================================================= */
#ifdef _WIN32
#  define WIN32_LEAN_AND_MEAN
#  ifndef P3_NO_NET
#    include <winsock2.h>              /* before windows.h, always */
#    ifdef _MSC_VER
#      pragma comment(lib, "ws2_32.lib")
#    endif
     typedef SOCKET p3_sock;
     typedef int    p3_socklen;
#    define P3_BADSOCK   INVALID_SOCKET
#    define p3_closesock closesocket
#  endif
#  include <windows.h>
#else
#  include <sys/types.h>
#  include <sys/time.h>
#  include <unistd.h>
#  ifndef P3_NO_NET
#    include <sys/socket.h>
#    include <sys/select.h>
#    include <netinet/in.h>
#    include <arpa/inet.h>
     typedef int       p3_sock;
     typedef socklen_t p3_socklen;
#    define P3_BADSOCK   (-1)
#    define p3_closesock close
#  endif
#endif

static unsigned long now_ms(void)
{
#ifdef _WIN32
    return (unsigned long)GetTickCount();
#else
    struct timeval tv;
    gettimeofday(&tv, NULL);
    return (unsigned long)tv.tv_sec * 1000UL + (unsigned long)(tv.tv_usec / 1000);
#endif
}

static volatile sig_atomic_t g_stop = 0;
static void on_sigint(int s) { (void)s; g_stop = 1; }

/* ===========================================================================
 * SECTION 2 -- WIRE FACTS.  Byte-identical with promos3_sim.c.
 * ========================================================================= */
#define GW_REC          36
#define GW_OFF_LEN      0x15
#define GW_OFF_ID_HI    0x1A
#define GW_OFF_ID_LO    0x1B
#define GW_OFF_DATA     0x1C
#define CAN_MAXDATA     8
#define BASE_CAN_ID     1280
#define GW_PORT         1789
#define PAY_PER_FRAME   7
#define MAX_MSG         4096
#define MAX_UNITS       16
#define NFEAT_MAX       4
#define MERKMAL_VALUE_IS_HI 1     /* see promos3_sim.c: unconfirmed convention */

typedef struct {
    int           id;
    int           len;
    unsigned char data[CAN_MAXDATA];
} can_frame;

enum { SZ_FIXED = 0, SZ_ROWS = 1 };
enum { C_VERIFIED = 0, C_TABLE = 1, C_ASSUMED = 2 };

static const char *conf_tag(int c)
{
    if (c == C_VERIFIED) return "[verified]";
    if (c == C_TABLE)    return "[table]";
    return "[assumed]";
}

typedef struct {
    int         cmd;
    const char *name;
    int         req_len;
    int         size_rule;
    int         size;
    int         conf;
    const char *gui;         /* what this packet does on screen              */
    const char *note;
} cmd_desc;

/* The size column is the expected ANSWER payload. Where it is [assumed] the
 * number is a guess: a wrong guess costs a timeout, never a wrong value on
 * screen, because the checksum has to agree before anything is decoded.
 * Use --probe to measure the real ones (see the note at the end of --help). */
static const cmd_desc CMD_TAB[] = {
 { 0x01, "MC_GIVESTATUS",         2, SZ_FIXED,   4, C_ASSUMED,
   "unit-connected indicator and the status line",
   "sender never calls setRecvSize - size is a pure guess" },
 { 0x02, "MC_GIVEGTYPE",          2, SZ_FIXED,  14, C_TABLE,
   "unit identity: type, sub-type, serial -> title bar and unit list",
   "size table says 14 but labels the record SGrenzRec - known conflict" },
 { 0x06, "MC_GIVEKONFIG",         3, SZ_FIXED,   3, C_ASSUMED,
   "startup: builds the unit model, logs Version/Channels/Sensors",
   "body anchored on E5 01 04 from the app's own log line" },
 { 0x08, "MC_GIVEPLCVALUES",      3, SZ_FIXED,   2, C_ASSUMED,
   "PLC I/O lamps (this box: 4 inputs, 1 output)",
   "true size is computed at runtime from Geraet+0x4e6 - open item D4" },
 { 0x0e, "MC_GIVEKANAL",          3, SZ_FIXED, 144, C_VERIFIED,
   "unit configuration page and the LABELS of the live feature bars",
   "SKanalRecV40, size verified at the call site" },
 { 0x12, "MC_GIVEALARM",          3, SZ_FIXED,  34, C_ASSUMED,
   "alarm box (updateAlarmBox) and the Alarms table",
   "layout is MC3_-derived; size entry probably belongs to 0x11" },
 { 0x16, "MC_GIVESAMMELMERKMALE", 4, SZ_ROWS,    0, C_VERIFIED,
   "THE live screen: feature bars, trend, Trend_C01_Fnn and Log rows",
   "size = rows*(features*2+2)+1, first payload byte is the row count" },
 { 0x1b, "MC_GIVESIGNALVERLAUF",  6, SZ_FIXED, 257, C_ASSUMED,
   "the waveform plot: 125 points of one feature, raw counts",
   "5 header + 125*int16 + 2 trailer; 257 came from a synthetic test" }
};
#define CMD_TAB_N ((int)(sizeof CMD_TAB / sizeof CMD_TAB[0]))

static const cmd_desc *cmd_find(int cmd)
{
    int i;
    for (i = 0; i < CMD_TAB_N; i++) if (CMD_TAB[i].cmd == cmd) return &CMD_TAB[i];
    return NULL;
}

/* [MonitorTypes] 0x44 - the -16 family. Index is GSubType-1 (1-based). */
static const char *MONTYPE_44[] = {
    "MDL5081-16","MDL5082-16","MDL5051-16","MDL5052-16",
    "MSL5081-16","MSL5082-16","MSL5051-16","MSL5052-16",
    "MSL5074-16","MSL3031-16","MSL3032-16","MSL3011-16",
    "MSL3012-16","MDL5031-16","MDL5032-16","MSL5034-16"
};

/* [AlarmNames] as configured on THIS box - operator-assigned, not defaults */
static const char *ALARM_SLOT[] = {
    "?", "Collision", "Break", "Wearout", "Missing", "Coolant",
    "Alarm 6", "Alarm 7", "Alarm 8"
};

/* ToolStatus ring (report part 6.1) */
static const char *TOOL_STATUS[16] = {
    "empty","overload","underload","contact","missing","work over","work under",
    "cut start","cut end","dyn upper","dyn lower","pattern upper","pattern lower",
    "ACF contact","cut detect","tool wear"
};

/* ===========================================================================
 * SECTION 3 -- PURE CODEC LAYER (identical maths to the simulator)
 * ========================================================================= */
static unsigned char p3_checksum(int unit,
                                 const unsigned char *sent, int sent_n,
                                 const unsigned char *recv, int recv_n)
{
    int seed = unit, i;
    if (sent && sent_n > 0) for (i = 0; i < sent_n - 1; i++) seed += sent[i];
    if (recv) for (i = 0; i < recv_n; i++) seed += recv[i];
    return (unsigned char)(-seed);
}

static unsigned char p3_ck_request(int unit, const unsigned char *msg, int n)
{
    int seed = unit, i;
    for (i = 0; i < n; i++) seed += msg[i];
    return (unsigned char)(-seed);
}

static int mc_canonical_request(int cmd, int unit, int station,
                                unsigned char *out, int cap)
{
    const cmd_desc *cd = cmd_find(cmd);
    int n = 0, want = cd ? cd->req_len : 3;
    if (want > cap) return -1;
    out[n++] = (unsigned char)cmd;
    if (want > 2) out[n++] = (unsigned char)station;
    while (n < want - 1) out[n++] = 0x00;
    out[n] = p3_ck_request(unit, out, n);
    n++;
    return n;
}

static void gw_write(unsigned char *out36, int can_id, int len,
                     const unsigned char *data)
{
    int i;
    memset(out36, 0, GW_REC);
    out36[0] = 0x00; out36[1] = 0x24;
    out36[2] = 0x00; out36[3] = 0x80;
    out36[GW_OFF_LEN]   = (unsigned char)len;
    out36[GW_OFF_ID_HI] = (unsigned char)((can_id >> 8) & 0xFF);
    out36[GW_OFF_ID_LO] = (unsigned char)(can_id & 0xFF);
    for (i = 0; i < len && i < CAN_MAXDATA; i++) out36[GW_OFF_DATA + i] = data[i];
}

static int gw_read(const unsigned char *in36, can_frame *f)
{
    int i;
    f->len = in36[GW_OFF_LEN];
    if (f->len > CAN_MAXDATA) return 0;
    f->id = (in36[GW_OFF_ID_HI] << 8) | in36[GW_OFF_ID_LO];
    for (i = 0; i < CAN_MAXDATA; i++) f->data[i] = in36[GW_OFF_DATA + i];
    return 1;
}

/* request framing: [00][00][00][5 payload] then [seq][7 payload] */
static int mc_frame_request(const unsigned char *msg, int n, int can_id,
                            can_frame *out, int max)
{
    int i, seq = 1, cnt, chunk;
    if (max < 1) return -1;
    chunk = n > 5 ? 5 : n;
    out[0].id = can_id;
    out[0].data[0] = 0; out[0].data[1] = 0; out[0].data[2] = 0;
    memcpy(out[0].data + 3, msg, (size_t)chunk);
    out[0].len = 3 + chunk;
    cnt = 1; i = chunk;
    while (i < n) {
        chunk = n - i;
        if (chunk > PAY_PER_FRAME) chunk = PAY_PER_FRAME;
        if (cnt >= max) return -1;
        out[cnt].id = can_id;
        out[cnt].data[0] = (unsigned char)(seq & 0xFF);
        memcpy(out[cnt].data + 1, msg + i, (size_t)chunk);
        out[cnt].len = 1 + chunk;
        cnt++; i += chunk; seq++;
    }
    return cnt;
}

/* answer framing, the device side of the same rule - used by --selftest and
 * kept here so both programs state the format in identical code */
static int mc_frame_answer(const unsigned char *pay, int n, unsigned char ck,
                           int can_id, can_frame *out, int max)
{
    int i = 0, seq = 0, cnt = 0;
    while (i < n) {
        int chunk = n - i;
        if (chunk > PAY_PER_FRAME) chunk = PAY_PER_FRAME;
        if (cnt >= max) return -1;
        out[cnt].id = can_id;
        out[cnt].data[0] = (unsigned char)(seq & 0xFF);
        memcpy(out[cnt].data + 1, pay + i, (size_t)chunk);
        if (chunk < PAY_PER_FRAME) {
            out[cnt].data[1 + chunk] = ck;
            out[cnt].len = chunk + 2;
        } else out[cnt].len = 8;
        cnt++; i += chunk; seq++;
    }
    if (n % PAY_PER_FRAME == 0) {
        if (cnt >= max) return -1;
        out[cnt].id = can_id;
        out[cnt].data[0] = (unsigned char)(seq & 0xFF);
        out[cnt].data[1] = ck;
        out[cnt].len = 2;
        cnt++;
    }
    return cnt;
}

static int rd_i16le(const unsigned char *p) /* -> int, sign extended */
{
    int v = p[0] | (p[1] << 8);
    return (v & 0x8000) ? v - 0x10000 : v;
}

/* ===========================================================================
 * SECTION 4 -- THE LEARNED MODEL OF A UNIT
 * Everything the reader knows about a unit, learned from its own answers.
 * ========================================================================= */
typedef struct {
    int seen;
    int version, channels, sensors;      /* from 0x06                       */
    int gtype, gsubtype, serial;         /* from 0x02                       */
    int features;                        /* from 0x0e (nonzero masks)       */
    unsigned char fmask[NFEAT_MAX];
    char          fname[NFEAT_MAX][12];
    int  cycle, wp_id;                   /* tracked from the 0x16 markers   */
    int  marker_wait;                    /* a marker row expects a parameter */
    int  marker_code;
    long blocks, rows_seen, alarms;
} unit_model;

static void model_init(unit_model *m)
{
    memset(m, 0, sizeof *m);
    m->channels = 1; m->sensors = 4; m->features = 4;   /* this box's default */
    m->fmask[0] = 1; m->fmask[1] = 2; m->fmask[2] = 4; m->fmask[3] = 8;
    m->marker_code = -1;
}

/* channelKey -> feature slot. Three encodings are in play and it is not yet
 * settled which one the device uses (gap G9), so accept all three and say
 * which one matched rather than silently picking one. */
static int feature_index(const unit_model *m, int key, const char **how)
{
    int i;
    for (i = 0; i < m->features; i++)
        if (m->fmask[i] == (unsigned char)key) { *how = "mask"; return i; }
    for (i = 0; i < m->features; i++)
        if ((m->fmask[i] | 0x80) == (unsigned char)key) { *how = "mask|0x80"; return i; }
    if (key >= 0 && key < m->features) { *how = "plain index"; return key; }
    *how = "unmatched";
    return -1;
}

static const char *feature_name(const unit_model *m, int key)
{
    const char *how;
    int i = feature_index(m, key, &how);
    if (i < 0 || !m->fname[i][0]) return "(unnamed feature)";
    return m->fname[i];
}

/* ===========================================================================
 * SECTION 5 -- THE LINK LAYER: one outstanding request per unit
 *
 *   frame k of an answer : [seq][payload ...][checksum if it fits]
 *   completion           : accumulated == expected  (size table, or, for the
 *                          0x16 live block, rows*recordSize+1 taken from the
 *                          first payload byte)
 *   validation           : checksum spans unit id + request + payload
 * ========================================================================= */
enum {
    LK_IDLE = 0, LK_MORE, LK_DONE, LK_BAD_SEQ, LK_BAD_CK, LK_DEV_ERR,
    LK_UNSOLICITED, LK_DISCARD
};

typedef struct {
    int  busy;
    int  cmd;
    unsigned char req[8];
    int  req_n;
    int  expected;             /* -1 = not yet known, -2 = measure by quiet   */
    int  rec_size;             /* stride, for the 0x16 rule                   */
    unsigned char buf[MAX_MSG];
    int  got;
    int  next_seq;
    int  last_avail;           /* payload bytes taken from the last frame     */
    unsigned char ck_rx;
    int  have_ck;
    int  poisoned;             /* this answer is ruined; wait for the resend  */
    unsigned long deadline, last_rx;
    int  attempts;
} link_state;

typedef struct {              /* what a completed answer looks like to the UI */
    int unit, cmd;
    const unsigned char *body;
    int body_len;
    int ck_ok;                 /* 1 ok, 0 bad, -1 could not be checked        */
    int attributed;            /* 0 = anonymous blob (passive, no request)    */
    const char *how;           /* how it was attributed                        */
} p3_msg;

static void link_arm(link_state *lk, int unit, int cmd, int station,
                     int rec_size, int expected, unsigned long now, int timeout)
{
    memset(lk, 0, sizeof *lk);
    lk->busy = 1;
    lk->cmd = cmd;
    lk->req_n = mc_canonical_request(cmd, unit, station, lk->req, sizeof lk->req);
    lk->expected = expected;
    lk->rec_size = rec_size;
    lk->next_seq = 0;
    lk->deadline = now + (unsigned long)timeout;
    lk->attempts = 1;
}

/* Feed one answer frame. Returns an LK_* code and fills *out when LK_DONE. */
static int link_feed(link_state *lk, int unit, const can_frame *f, p3_msg *out)
{
    int avail;
    if (!lk->busy) return LK_UNSOLICITED;
    lk->last_rx = now_ms();
    /* Once an answer is ruined the rest of its frames are worthless. Keep the
     * request open so the timeout ladder resends it, exactly as the app does
     * ("try again" -> "aborting"), and swallow the remaining frames quietly. */
    if (lk->poisoned) return LK_DISCARD;

    /* A frame that is only [seq][ck] AFTER the payload is complete is the
     * lone-checksum frame, not an error. */
    if (lk->have_ck == 0 && lk->expected >= 0 && lk->got == lk->expected &&
        f->len == 2 && lk->last_avail == PAY_PER_FRAME) {
        lk->ck_rx = f->data[1];
        lk->have_ck = 1;
    }
    else if (f->len == 2 && f->data[0] == 0x00 && f->data[1] == 0x01 &&
             lk->got == 0 && lk->expected != 0) {
        /* Device error answer. The report gives the signature as
         * DATA[0]==0 && DATA[1]==1; that is also a healthy first frame of a
         * one-byte answer, so it is constrained here to len==2 with nothing
         * accumulated and a non-zero expected size. Confirm on a real capture. */
        lk->busy = 0;
        return LK_DEV_ERR;
    }
    else {
        if (f->data[0] != (unsigned char)(lk->next_seq & 0xFF)) {
            lk->poisoned = 1;
            return LK_BAD_SEQ;              /* "Unknown answer format ..."   */
        }
        avail = f->len - 1;
        if (avail < 0) avail = 0;

        /* the 0x16 rule: the first payload byte is the row count and it is
         * what sets the length of the whole answer */
        if (lk->expected == -1 && avail > 0)
            lk->expected = f->data[1] * lk->rec_size + 1;

        if (lk->expected >= 0 && avail > lk->expected - lk->got)
            avail = lk->expected - lk->got;
        if (lk->got + avail > (int)sizeof lk->buf) { lk->poisoned = 1; return LK_BAD_SEQ; }
        memcpy(lk->buf + lk->got, f->data + 1, (size_t)avail);
        lk->got += avail;
        lk->next_seq++;
        lk->last_avail = avail;

        if (lk->expected >= 0 && lk->got >= lk->expected) {
            if (avail == PAY_PER_FRAME) {
                return LK_MORE;              /* the checksum needs its own frame */
            }
            lk->ck_rx = f->data[f->len - 1];
            lk->have_ck = 1;
        } else {
            return LK_MORE;
        }
    }

    if (!lk->have_ck) return LK_MORE;

    {
        unsigned char want = p3_checksum(unit, lk->req, lk->req_n, lk->buf, lk->got);
        out->unit = unit;
        out->cmd = lk->cmd;
        out->body = lk->buf;
        out->body_len = lk->got;
        out->ck_ok = (want == lk->ck_rx) ? 1 : 0;
        out->attributed = 1;
        out->how = "request";
        lk->busy = 0;
        return out->ck_ok ? LK_DONE : LK_BAD_CK;
    }
}

/* Identify an anonymous answer by its checksum.
 *
 * The checksum covers unit id + request bytes + payload, so it is a 8-bit
 * fingerprint of the request that produced this answer. With only a handful
 * of read-only commands, and the canonical request for each of them being
 * deterministic, we can simply try them all. A match is not free evidence -
 * an 8-bit sum collides once in 256 - so we also require the observed length
 * to agree with the size table, and we report how many candidates matched.
 * Returns the command, -1 for none, -2 for ambiguous (fills *n_match). */
static int identify_by_checksum(int unit, const unsigned char *body, int len,
                                unsigned char ck, int station, int *n_match)
{
    int i, found = -1, n = 0;
    *n_match = 0;
    for (i = 0; i < CMD_TAB_N; i++) {
        unsigned char req[8], want;
        int rn = mc_canonical_request(CMD_TAB[i].cmd, unit, station, req, sizeof req);
        if (rn < 0) continue;
        want = p3_checksum(unit, req, rn, body, len);
        if (want != ck) continue;
        if (CMD_TAB[i].size_rule == SZ_FIXED && CMD_TAB[i].size != len) continue;
        n++;
        if (found < 0) found = CMD_TAB[i].cmd;
    }
    *n_match = n;
    if (n == 1) return found;
    if (n > 1)  return -2;
    return -1;
}

/* -- passive assembler ----------------------------------------------------
 * With no request in sight there is no command, no length and no way to check
 * anything against an expectation. All a listener has is the sequence number:
 * seq 0 starts a new answer, and the very last byte of the last frame is the
 * checksum. That is implemented here, honestly labelled, and it is the best
 * that direction of the wire can do. */
typedef struct {
    unsigned char buf[MAX_MSG];
    int  got, next_seq, active;
    unsigned long last_rx;
} passive_state;

static int passive_feed(passive_state *ps, const can_frame *f, int *complete_len)
{
    int avail = f->len - 1;
    int started_new = 0;
    if (avail < 0) return 0;
    if (f->data[0] == 0) {
        started_new = ps->active && ps->got > 0;
        if (started_new) *complete_len = ps->got;
        if (started_new) return 1;         /* caller drains, then re-feeds     */
        ps->got = 0; ps->next_seq = 0; ps->active = 1;
    }
    if (!ps->active) return 0;
    if (f->data[0] != (unsigned char)(ps->next_seq & 0xFF)) { ps->active = 0; return -1; }
    if (ps->got + avail > (int)sizeof ps->buf) { ps->active = 0; return -1; }
    memcpy(ps->buf + ps->got, f->data + 1, (size_t)avail);
    ps->got += avail;
    ps->next_seq++;
    ps->last_rx = now_ms();
    return 0;
}

/* ===========================================================================
 * SECTION 6 -- PRESENTATION.  "What does this packet put on the screen?"
 * Pure formatting; every decoder states its confidence and shows raw bytes
 * whenever the layout is not proven.
 * ========================================================================= */
/* Presentation-only switch: --quiet keeps one line per answer and drops the
 * detail. The decoders still run, so the learned model and the counters stay
 * correct either way. This is a display flag, not program state. */
static int g_detail = 1;

static void pr(const char *fmt, ...)
{
    va_list ap;
    if (!g_detail) return;
    va_start(ap, fmt);
    vprintf(fmt, ap);
    va_end(ap);
}

static void hexdump(const unsigned char *p, int n, const char *pad)
{
    int i;
    int show = n > 128 ? 128 : n;
    if (!g_detail) return;
    for (i = 0; i < show; i++) {
        if ((i % 16) == 0) pr("%s%04x  ", pad, i);
        pr("%02x ", p[i]);
        if ((i % 16) == 15) pr("\n");
    }
    if (show % 16) pr("\n");
    if (n > show) pr("%s... %d bytes total\n", pad, n);
}

static void bar(int v, int vmax, int width)
{
    int i, k;
    if (!g_detail) return;
    if (vmax <= 0) vmax = 1;
    k = v * width / vmax;
    if (k < 0) k = 0;
    if (k > width) k = width;
    pr("[");
    for (i = 0; i < width; i++) if (g_detail) putchar(i < k ? '#' : '.');
    pr("]");
}

static void sparkline(const int *v, int n, int cols)
{
    static const char RAMP[] = " .:-=+*#%@";
    int i;
    if (!g_detail) return;
    for (i = 0; i < cols; i++) {
        int a = i * n / cols, b = (i + 1) * n / cols, j, mx = 0;
        if (b <= a) b = a + 1;
        for (j = a; j < b && j < n; j++) if (v[j] > mx) mx = v[j];
        if (g_detail) putchar(RAMP[(mx * 9) / 255 > 9 ? 9 : (mx * 9) / 255]);
    }
    if (g_detail) putchar('\n');
}

/* --- 0x06 MC_GIVEKONFIG ------------------------------------------------- */
static void show_konfig(unit_model *m, const p3_msg *g)
{
    if (g->body_len < 3) { pr("      body too short\n"); return; }
    m->version = g->body[0];
    m->channels = g->body[1];
    m->sensors = g->body[2];
    m->seen = 1;
    pr("      Version %d   Channels %d   Sensors %d\n",
           m->version, m->channels, m->sensors);
    pr("      GUI: the unit model is built here; this is the line the app\n"
           "           writes to its log as bearbeite_Kom_06_MC_GIVEKONFIG\n");
    if (m->version != 229)
        pr("      note: record layouts are version selected; this reader is\n"
               "            calibrated for version 229 (Rtm_V14.5.H86)\n");
}

/* --- 0x02 MC_GIVEGTYPE -------------------------------------------------- */
static void show_gtype(unit_model *m, const p3_msg *g)
{
    if (g->body_len < 7) { hexdump(g->body, g->body_len, "      "); return; }
    m->gtype = g->body[0];
    m->gsubtype = g->body[1];
    m->serial = g->body[4] | (g->body[5] << 8);
    pr("      GType 0x%02X   GSubType %d   serial %d   version %d\n",
           m->gtype, m->gsubtype, m->serial, g->body[6]);
    if (m->gtype == 0x44 && m->gsubtype >= 1 &&
        m->gsubtype <= (int)(sizeof MONTYPE_44 / sizeof MONTYPE_44[0]))
        pr("      model %s   (MonitorTypes 0x44, index is GSubType-1)\n",
               MONTYPE_44[m->gsubtype - 1]);
    pr("      GUI: unit list entry and window title  \"Unit %d Type %d "
           "SubType %d SNr %d\"\n", g->unit, m->gtype, m->gsubtype, m->serial);
    pr("      field offsets here are ASSUMED - compare with the HMI\n");
    hexdump(g->body, g->body_len, "      raw ");
}

/* --- 0x0e MC_GIVEKANAL: SKanalRecV40, the feature LABELS ---------------- */
static void show_kanal(unit_model *m, const p3_msg *g)
{
    int f, n = 0;
    if (g->body_len < 144) {
        pr("      short SKanalRecV40 (%d of 144 bytes)\n", g->body_len);
        hexdump(g->body, g->body_len, "      ");
        return;
    }
    pr("      PLC type %d   PLC version %d   channel %d\n",
           g->body[0x00], g->body[0x01], g->body[0x02]);
    pr("      CDR limits  %d %d %d %d\n",
           g->body[0x10], g->body[0x11], g->body[0x12], g->body[0x13]);
    for (f = 0; f < NFEAT_MAX; f++) {
        const unsigned char *slot = g->body + 0x4D + f * 12;
        int i;
        if (slot[0] == 0) continue;
        m->fmask[n] = slot[0];
        for (i = 0; i < 11; i++) m->fname[n][i] = (char)slot[1 + i];
        m->fname[n][11] = 0;
        for (i = 10; i >= 0; i--)                 /* trim trailing blanks/nul */
            if (m->fname[n][i] == ' ' || m->fname[n][i] == 0) m->fname[n][i] = 0;
            else break;
        pr("      feature %d  mask 0x%02X  \"%s\"\n", n, slot[0], m->fname[n]);
        n++;
    }
    if (n > 0) m->features = n;
    pr("      GUI: these are the LABELS of the live bars and of the trend\n"
           "           tabs; they are operator assigned, never hardcoded\n");
    pr("      learned: %d features -> 0x16 stride is %d bytes per row\n",
           m->features, m->features * 2 + 2);
}

/* --- 0x16 MC_GIVESAMMELMERKMALE: the live screen ------------------------ */
static void show_merkmale(unit_model *m, const p3_msg *g, int max_rows)
{
    int stride = m->features * 2 + 2;
    int rows, r, f, printed = 0;
    if (g->body_len < 1) { pr("      empty block\n"); return; }
    rows = g->body[0];
    pr("      rows %d   stride %d   (features %d, 2 unidentified bytes/row)\n",
           rows, stride, m->features);
    if (1 + rows * stride > g->body_len) {
        pr("      block is shorter than rows*stride+1 - showing raw\n");
        hexdump(g->body, g->body_len, "      ");
        return;
    }
    m->blocks++;
    for (r = 0; r < rows; r++) {
        const unsigned char *row = g->body + 1 + r * stride;
        int st0, val0;
#if MERKMAL_VALUE_IS_HI
        st0 = row[0]; val0 = row[1];
#else
        st0 = row[1]; val0 = row[0];
#endif
        m->rows_seen++;
        if (m->marker_wait) {                        /* parameter row         */
            m->marker_wait = 0;
            if (m->marker_code == 0x00) {
                m->cycle = st0;
                pr("      row %d  PARAMETER  new cycle index = %d\n", r, st0);
            } else if (m->marker_code == 0xFE) {
                m->wp_id++;
                pr("      row %d  PARAMETER  workpiece id size = %d "
                       "(cross-check [WorkpieceID] IDsize)\n", r, st0);
            } else {
                pr("      row %d  PARAMETER  value = %d\n", r, st0);
            }
            m->marker_code = -1;
            continue;
        }
        if (st0 == 0xFF) {                           /* escape / marker row   */
            const char *what = "unknown marker";
            if (val0 == 0x00) what = "NEW CYCLE  -> GUI clears the bars and "
                                    "starts a new cycle";
            else if (val0 == 0xFB) what = "RESET per feature";
            else if (val0 == 0xFE) what = "WORKPIECE ID -> GUI starts a new "
                                          "workpiece row in Log";
            pr("      row %d  MARKER 0x%02X  %s\n", r, val0, what);
            m->marker_wait = 1;
            m->marker_code = val0;
            continue;
        }
        if (printed >= max_rows) { continue; }
        printed++;
        pr("      row %d\n", r);
        for (f = 0; f < m->features; f++) {
            int a = row[f * 2], b = row[f * 2 + 1];
            int st, val;
#if MERKMAL_VALUE_IS_HI
            st = a; val = b;
#else
            st = b; val = a;
#endif
            pr("        %-11s ", m->fname[f][0] ? m->fname[f] : "feature");
            bar(val, 255, 24);
            pr(" %3d  raw %02x %02x", val, a, b);
            /* The flag bits all live in one byte; the report lists 0x04 as
             * belonging to "lo" and 0x01/0x10/0x40 to "hi", which cannot both
             * be true. One flags byte holding all five is the only coherent
             * reading, so they are decoded from the status byte and the raw
             * pair is always printed next to them. */
            if (st & 0x04) { pr("  ALARM"); m->alarms++; }
            if (st & 0x01) pr("  teach");
            if (st & 0x10) pr("  start/stop");
            if (st & 0x40) pr("  tool change");
            if (st & 0x08) pr("  flag08");
            pr("\n");
        }
        pr("        row trailer %02x %02x  (2 bytes, meaning not recovered)\n",
               row[stride - 2], row[stride - 1]);
    }
    if (rows > max_rows)
        pr("      (%d further data rows suppressed, use --rows-shown)\n",
               rows - max_rows);
    pr("      GUI: this block IS the live screen. Values are RAW COUNTS\n"
           "           0..255 - there is no scaling factor in this generation.\n"
           "           The percentage the HMI shows is raw/limit level * 100.\n");
    pr("      which byte of each pair is the amplitude is UNCONFIRMED;\n"
           "      both are printed above so one look at the HMI settles it\n");
}

/* --- 0x1b MC_GIVESIGNALVERLAUF: the waveform plot ----------------------- */
static void show_trace(const unit_model *m, const p3_msg *g)
{
    int samples[125];
    int i, n = 0, mn = 32767, mx = -32768;
    long sum = 0;
    const char *how = "";
    if (g->body_len < 7) { hexdump(g->body, g->body_len, "      "); return; }
    pr("      toolKey %d  channelKey 0x%02X (%s, matched by %s)  "
           "paramA %d  flag %d  mode %d\n",
           g->body[0], g->body[1], feature_name(m, g->body[1]),
           (feature_index(m, g->body[1], &how), how),
           g->body[2], g->body[3], g->body[4]);
    for (i = 5; i + 1 < g->body_len && n < 125; i += 2) {
        int v = rd_i16le(g->body + i);
        samples[n++] = v;
        if (v < mn) mn = v;
        if (v > mx) mx = v;
        sum += v;
    }
    if (n == 0) { hexdump(g->body, g->body_len, "      "); return; }
    pr("      %d samples   min %d   max %d   avg %ld   (raw counts, no scaling)\n",
           n, mn, mx, sum / n);
    pr("      ");
    sparkline(samples, n, 64);
    pr("      GUI: the signal plot widget draws exactly these %d points.\n"
           "           This waveform exists ONLY on the wire - the database\n"
           "           keeps a min/max envelope, never the raw curve.\n", n);
    pr("      header offsets are ASSUMED (the trace decoder reads from\n"
           "      Data+0x10, which may mean there is no 5-byte header)\n");
}

/* --- 0x08 MC_GIVEPLCVALUES --------------------------------------------- */
static void show_plc(const p3_msg *g)
{
    int i;
    if (g->body_len < 1) { pr("      empty\n"); return; }
    pr("      inputs ");
    for (i = 3; i >= 0; i--) if (g_detail) putchar((g->body[0] >> i) & 1 ? '1' : '0');
    if (g->body_len > 1) {
        pr("   outputs ");
        for (i = 0; i < 1; i++) if (g_detail) putchar((g->body[1] >> i) & 1 ? '1' : '0');
    }
    pr("\n      GUI: the PLC I/O lamps (this box declares 4 inputs, 1 output)\n");
    pr("      bit order is ASSUMED\n");
    hexdump(g->body, g->body_len, "      raw ");
}

/* --- 0x01 MC_GIVESTATUS ------------------------------------------------- */
static void show_status(const p3_msg *g)
{
    if (g->body_len >= 1)
        pr("      status byte 0x%02X  (%s)\n", g->body[0],
               TOOL_STATUS[g->body[0] & 0x0F]);
    pr("      GUI: unit-connected indicator, status line\n");
    pr("      both the SIZE and the layout of this answer are guesses -\n"
           "      run --probe 0x01 against the real unit to settle the size\n");
    hexdump(g->body, g->body_len, "      raw ");
}

/* --- 0x12 MC_GIVEALARM -------------------------------------------------- */
static void show_alarm(const p3_msg *g)
{
    if (g->body_len >= 6) {
        int sub = g->body[0], num = g->body[3];
        pr("      sub-command %d (%s)   alarm number %d (%s)\n",
               sub, sub == 1 ? "alarm data" : sub == 8 ? "state marker" :
                    sub == 0x0A ? "acknowledge" : "?",
               num, (num >= 1 && num <= 8) ? ALARM_SLOT[num] : "?");
    }
    pr("      GUI: alarm box (updateAlarmBox), red banner, Alarms table\n");
    pr("      this layout is MC3_-derived, NOT proven for an MC_ box:\n"
           "      shown as raw bytes on purpose\n");
    hexdump(g->body, g->body_len, "      ");
}

/* one entry point: a completed answer -> screen */
static void show_message(unit_model *m, const p3_msg *g, int max_rows,
                         unsigned long t)
{
    const cmd_desc *cd = cmd_find(g->cmd);
    printf("\n[%lu.%03lu] unit %d  %s (0x%02X)  %d bytes  %s  checksum %s%s\n",
           t / 1000, t % 1000, g->unit,
           cd ? cd->name : "unknown command", g->cmd, g->body_len,
           cd ? conf_tag(cd->conf) : "[unknown]",
           g->ck_ok == 1 ? "ok" : g->ck_ok == 0 ? "BAD" : "not checkable",
           g->attributed ? "" : "   *** ANONYMOUS: no request seen ***");
    if (cd) pr("      purpose: %s\n", cd->gui);
    if (g->how && strcmp(g->how, "request") != 0)
        pr("      attribution: %s\n", g->how);
    if (!g->attributed)
        pr("      an MC_ answer carries no command and no length, so this\n"
               "      is a labelled guess, not a decode. Use --master to know.\n");
    if (g->ck_ok == 0) {
        pr("      the checksum did not validate - nothing below is trusted\n");
        hexdump(g->body, g->body_len, "      ");
        return;
    }
    switch (g->cmd) {
    case 0x01: show_status(g); break;
    case 0x02: show_gtype(m, g); break;
    case 0x06: show_konfig(m, g); break;
    case 0x08: show_plc(g); break;
    case 0x0e: show_kanal(m, g); break;
    case 0x12: show_alarm(g); break;
    case 0x16: show_merkmale(m, g, max_rows); break;
    case 0x1b: show_trace(m, g); break;
    default:
        pr("      no decoder for this command - raw bytes only\n");
        hexdump(g->body, g->body_len, "      ");
        break;
    }
    if (cd && cd->note) pr("      caveat: %s\n", cd->note);
}

/* ===========================================================================
 * SECTION 7 -- I/O BOUNDARY: capture files (same format promos3_sim writes)
 * ========================================================================= */
static unsigned long get_u32le(const unsigned char *p)
{
    return (unsigned long)p[0] | ((unsigned long)p[1] << 8) |
           ((unsigned long)p[2] << 16) | ((unsigned long)p[3] << 24);
}

#ifndef P3_NO_NET
static void put_u32le(unsigned char *p, unsigned long v)
{
    p[0] = (unsigned char)(v & 0xFF);
    p[1] = (unsigned char)((v >> 8) & 0xFF);
    p[2] = (unsigned char)((v >> 16) & 0xFF);
    p[3] = (unsigned char)((v >> 24) & 0xFF);
}
#endif

/* ===========================================================================
 * SECTION 8 -- counters
 * ========================================================================= */
typedef struct {
    long dg_in, rec_in, frames, dropped_id, answers, bad_ck, bad_seq,
         dev_err, timeouts, aborts, unsolicited, requests, discarded;
} stats;

/* ===========================================================================
 * SECTION 8b -- SELF TEST.  No socket, no arguments, no machine: it drives
 * the link layer with synthetic frames and checks it against the only real
 * protocol bytes anyone has, plus every framing corner case.
 * ========================================================================= */
static int expect(int cond, const char *what)
{
    printf("  %-58s %s\n", what, cond ? "ok" : "FAIL");
    return cond ? 0 : 1;
}

/* run one complete synthetic answer through the link layer */
static int drive(int unit, int cmd, const unsigned char *pay, int n,
                 int expected, int rec_size, int corrupt_ck, int corrupt_seq,
                 p3_msg *out)
{
    link_state lk;
    can_frame fr[64];
    unsigned char ck;
    int nf, k, r = LK_MORE;
    link_arm(&lk, unit, cmd, 1, rec_size, expected, now_ms(), 1000);
    ck = p3_checksum(unit, lk.req, lk.req_n, pay, n);
    if (corrupt_ck) ck ^= 0xFF;
    nf = mc_frame_answer(pay, n, ck, BASE_CAN_ID + unit, fr, 64);
    if (corrupt_seq && nf > 1) fr[nf / 2].data[0] ^= 0x20;
    for (k = 0; k < nf; k++) {
        r = link_feed(&lk, unit, &fr[k], out);
        if (r != LK_MORE) break;
    }
    return r;
}

static int self_test(void)
{
    unsigned char req[8], rec[GW_REC], pay[512];
    can_frame fr[8], f;
    p3_msg g;
    int bad = 0, n, nf, i;

    printf("self test\n");

    n = mc_canonical_request(0x08, 1, 1, req, sizeof req);
    bad += expect(n == 3 && req[0] == 0x08 && req[1] == 0x01 && req[2] == 0xF6,
                  "request 0x08 unit 1 is 08 01 f6 (matches the app's log)");

    nf = mc_frame_request(req, n, BASE_CAN_ID + 1, fr, 8);
    bad += expect(nf == 1 && fr[0].len == 6 &&
                  fr[0].data[0] == 0 && fr[0].data[1] == 0 && fr[0].data[2] == 0 &&
                  fr[0].data[3] == 0x08 && fr[0].data[4] == 0x01 &&
                  fr[0].data[5] == 0xF6,
                  "framed as DATA 00 00 00 08 01 f6, dlc 6");

    gw_write(rec, BASE_CAN_ID + 1, fr[0].len, fr[0].data);
    bad += expect(rec[0] == 0x00 && rec[1] == 0x24 && rec[2] == 0x00 &&
                  rec[3] == 0x80 && rec[GW_OFF_ID_HI] == 0x05 &&
                  rec[GW_OFF_ID_LO] == 0x01,
                  "gateway record 00 24 00 80 ... CAN id 0x501");
    bad += expect(gw_read(rec, &f) && f.id == 1281 && f.len == 6,
                  "record decodes back to the same frame");

    for (i = 0; i < (int)sizeof pay; i++) pay[i] = (unsigned char)(i & 0xFF);

    memset(&g, 0, sizeof g);
    bad += expect(drive(1, 0x0e, pay, 144, 144, 0, 0, 0, &g) == LK_DONE &&
                  g.body_len == 144 && g.ck_ok == 1,
                  "144-byte SKanalRec answer completes and validates");

    memset(&g, 0, sizeof g);
    bad += expect(drive(1, 0x0e, pay, 144, 144, 0, 1, 0, &g) == LK_BAD_CK,
                  "a corrupted checksum is caught, not decoded");

    memset(&g, 0, sizeof g);
    bad += expect(drive(1, 0x0e, pay, 144, 144, 0, 0, 1, &g) == LK_BAD_SEQ,
                  "an out-of-order frame is caught");

    /* the exact-multiple case: the checksum arrives in a frame of its own */
    memset(&g, 0, sizeof g);
    bad += expect(drive(1, 0x02, pay, 14, 14, 0, 0, 0, &g) == LK_DONE &&
                  g.body_len == 14,
                  "14 bytes (2x7) needs the lone [seq][ck] frame and still works");

    /* the 64-byte message that silently corrupted the earlier transport */
    memset(&g, 0, sizeof g);
    bad += expect(drive(1, 0x0e, pay, 64, 64, 0, 0, 0, &g) == LK_DONE &&
                  g.body_len == 64,
                  "64-byte answer completes exactly, consumes nothing extra");

    /* the dynamic 0x16 length, taken from the first payload byte */
    pay[0] = 2;                                   /* two rows of 10 bytes    */
    memset(&g, 0, sizeof g);
    bad += expect(drive(1, 0x16, pay, 21, -1, 10, 0, 0, &g) == LK_DONE &&
                  g.body_len == 21,
                  "0x16 length = rows*stride+1 learned from the first frame");

    /* passive identification of an anonymous answer */
    {
        unsigned char ck;
        int nm = 0, cmd;
        mc_canonical_request(0x0e, 1, 1, req, sizeof req);
        n = mc_canonical_request(0x0e, 1, 1, req, sizeof req);
        for (i = 0; i < 144; i++) pay[i] = (unsigned char)(i & 0xFF);
        ck = p3_checksum(1, req, n, pay, 144);
        cmd = identify_by_checksum(1, pay, 144, ck, 1, &nm);
        bad += expect(cmd == 0x0e && nm == 1,
                      "an anonymous 144-byte answer is identified as 0x0e");
    }

    printf("%s\n", bad ? "SELF TEST FAILED" : "all good");
    return bad ? 1 : 0;
}

/* ===========================================================================
 * SECTION 9 -- main
 * ========================================================================= */
static void usage(void)
{
    printf(
"promos3_view - read PROVIS3 / Promos3 MC_ traffic and print what it means\n"
"\n"
"MODES\n"
"  --master              ask the questions yourself and decode the answers.\n"
"                        This is the default and the only mode that can name\n"
"                        an answer with certainty.\n"
"  --passive             watch a mirror. MC_ answers carry no command, so\n"
"                        everything is labelled as a guess.\n"
"  --replay FILE.cap     re-run a capture written by promos3_sim or --record\n"
"  --probe 0xNN          send one request, take whatever comes back, and\n"
"                        report the MEASURED answer size (closes the guesses)\n"
"\n"
"WHERE TO TALK\n"
"  --gateway IP:PORT     the CAN gateway            (default 192.168.222.17:1789)\n"
"  --bind PORT           local UDP port, 0 = any    (default 0)\n"
"                        the real gateway answers to port 1789, so against the\n"
"                        real machine use --bind 1789 - which you can only do\n"
"                        while PROVIS3 itself is NOT running\n"
"  --unit N              unit id to poll, repeatable            (default 1)\n"
"\n"
"WHAT TO ASK\n"
"  --poll MS             cycle period                           (default 500)\n"
"  --gap MS              delay between two requests             (default 5)\n"
"  --timeout MS          answer timeout                         (default 300)\n"
"  --resend N            resends before abort ([Comm] MaxResend)(default 1)\n"
"  --trace               also request 0x1b waveforms every cycle\n"
"  --alarm               also request 0x12\n"
"  --size 0xNN=LEN       override an expected answer size\n"
"  --seconds N           stop after N seconds                   (default 0)\n"
"\n"
"OUTPUT\n"
"  --raw                 print CAN frames, decode nothing\n"
"  --record FILE.cap     save every datagram for later --replay\n"
"  --csv FILE            append one row per decoded feature value\n"
"  --rows-shown N        data rows to print per 0x16 block      (default 2)\n"
"  --quiet               one line per answer, no detail\n"
"  --selftest            check the decoder against the known bytes and exit\n"
"\n"
"EXAMPLES\n"
"  promos3_view --master --gateway 127.0.0.1:1789        (against promos3_sim)\n"
"  promos3_view --replay shift.cap\n"
"  promos3_view --master --probe 0x01 --gateway 192.168.222.17:1789\n"
"\n"
"MEASURING THE UNKNOWN SIZES\n"
"  0x01, 0x08, 0x12 and 0x1b are marked [assumed]: nobody has seen their real\n"
"  answer length. --probe sends one request, waits for the bus to go quiet,\n"
"  and then reports the length the checksum agrees with. Run it once per\n"
"  command against the real unit and the guesses become measurements.\n"
"  Do not probe a unit that PROVIS3 is polling at the same time.\n");
}

typedef struct {
    int master, passive, quiet, raw, probe_cmd, rows_shown;
    int bind_port, poll_ms, gap_ms, timeout_ms, resend, seconds;
    int trace, alarm;
    int units[MAX_UNITS], unit_n, units_set;
    int size_override[256];
    int assume[16], assume_n;      /* fallback order for anonymous answers  */
    const char *gw;
    const char *replay_path;
    const char *record_path;
    const char *csv_path;
} view_cfg;

#ifndef P3_NO_NET
static int parse_hostport(const char *s, char *host, int hostcap, int *port)
{
    const char *c = strrchr(s, ':');
    int n;
    if (!c) return 0;
    n = (int)(c - s);
    if (n <= 0 || n >= hostcap) return 0;
    memcpy(host, s, (size_t)n);
    host[n] = 0;
    *port = atoi(c + 1);
    return *port > 0;
}

#endif /* P3_NO_NET */

/* expected answer size for a command, after overrides and learned config */
#ifndef P3_NO_NET
static int expected_size(const view_cfg *cfg, const unit_model *m, int cmd,
                         int *rec_size, int *conf)
{
    const cmd_desc *cd = cmd_find(cmd);
    *rec_size = m->features * 2 + 2;
    *conf = cd ? cd->conf : C_ASSUMED;
    if (cfg->size_override[cmd & 0xFF] > 0) {
        *conf = C_VERIFIED;                    /* the operator measured it     */
        return cfg->size_override[cmd & 0xFF];
    }
    if (!cd) return -2;                        /* measure by quiet time        */
    if (cd->size_rule == SZ_ROWS) return -1;   /* learned from the first frame */
    return cd->size;
}
#endif /* P3_NO_NET */

/* One completed anonymous answer -> named as well as it honestly can be. */
static void passive_deliver(unit_model *m, const view_cfg *cfg, stats *stt,
                            int unit, const unsigned char *buf, int total,
                            int *assume_pos, unsigned long t)
{
    p3_msg g;
    unsigned char ck;
    int nmatch = 0, cmd;
    if (total < 1) return;
    ck = buf[total - 1];
    memset(&g, 0, sizeof g);
    g.unit = unit;
    g.body = buf;
    g.body_len = total - 1;

    cmd = identify_by_checksum(unit, g.body, g.body_len, ck, 1, &nmatch);
    if (cmd >= 0) {
        g.cmd = cmd;
        g.ck_ok = 1;
        g.attributed = 1;
        g.how = "identified by checksum + length (single candidate matched)";
    } else {
        g.cmd = cfg->assume_n ? cfg->assume[(*assume_pos) % cfg->assume_n] : -1;
        g.ck_ok = -1;
        g.attributed = 0;
        g.how = (cmd == -2) ? "several commands match the checksum - ambiguous"
                            : "position in the assumed poll order";
    }
    (*assume_pos)++;
    stt->answers++;
    show_message(m, &g, cfg->rows_shown, t);
}

int main(int argc, char **argv)
{
    static unsigned char dg[65536];
    view_cfg cfg;
    unit_model model[MAX_UNITS];
    link_state link[MAX_UNITS];
    passive_state pas[MAX_UNITS];
    stats st;
    FILE *rec_fp = NULL, *csv_fp = NULL;
    unsigned long t0, next_cycle = 0;
    int i, u;
    /* the poll cycle, exactly as Sende_Kom_MC_GIVESAMMELMERKMALE issues it */
    int queue[MAX_UNITS][16], q_head[MAX_UNITS], q_tail[MAX_UNITS];
    unsigned long next_send = 0;
#ifndef P3_NO_NET
    p3_sock sk = P3_BADSOCK;
    struct sockaddr_in gw_addr;
#endif

    memset(&cfg, 0, sizeof cfg);
    memset(&st, 0, sizeof st);
    memset(link, 0, sizeof link);
    memset(pas, 0, sizeof pas);
    memset(queue, 0, sizeof queue);
    memset(q_head, 0, sizeof q_head);
    memset(q_tail, 0, sizeof q_tail);
    cfg.master = 1; cfg.rows_shown = 2; cfg.poll_ms = 500; cfg.gap_ms = 5;
    cfg.timeout_ms = 300; cfg.resend = 1; cfg.probe_cmd = -1;
    cfg.gw = "192.168.222.17:1789";
    cfg.units[0] = 1; cfg.unit_n = 1;
    /* the order promos3_sim --stream pushes, and the order the app's own poll
     * cycle uses; only a fallback, the checksum identification comes first */
    cfg.assume[0] = 0x06; cfg.assume[1] = 0x0e; cfg.assume[2] = 0x16;
    cfg.assume[3] = 0x08; cfg.assume[4] = 0x01; cfg.assume[5] = 0x1b;
    cfg.assume_n = 6;
    for (i = 0; i < MAX_UNITS; i++) model_init(&model[i]);
    setvbuf(stdout, NULL, _IOLBF, 0);

    for (i = 1; i < argc; i++) {
        const char *a = argv[i];
        if      (!strcmp(a, "--help") || !strcmp(a, "-h")) { usage(); return 0; }
        else if (!strcmp(a, "--selftest")) return self_test();
        else if (!strcmp(a, "--master"))  { cfg.master = 1; cfg.passive = 0; }
        else if (!strcmp(a, "--passive")) { cfg.master = 0; cfg.passive = 1; }
        else if (!strcmp(a, "--raw"))     cfg.raw = 1;
        else if (!strcmp(a, "--quiet"))   cfg.quiet = 1;
        else if (!strcmp(a, "--trace"))   cfg.trace = 1;
        else if (!strcmp(a, "--alarm"))   cfg.alarm = 1;
        else if (!strcmp(a, "--gateway") && i+1 < argc) cfg.gw = argv[++i];
        else if (!strcmp(a, "--bind")    && i+1 < argc) cfg.bind_port = atoi(argv[++i]);
        else if (!strcmp(a, "--poll")    && i+1 < argc) cfg.poll_ms = atoi(argv[++i]);
        else if (!strcmp(a, "--gap")     && i+1 < argc) cfg.gap_ms = atoi(argv[++i]);
        else if (!strcmp(a, "--timeout") && i+1 < argc) cfg.timeout_ms = atoi(argv[++i]);
        else if (!strcmp(a, "--resend")  && i+1 < argc) cfg.resend = atoi(argv[++i]);
        else if (!strcmp(a, "--seconds") && i+1 < argc) cfg.seconds = atoi(argv[++i]);
        else if (!strcmp(a, "--rows-shown") && i+1 < argc) cfg.rows_shown = atoi(argv[++i]);
        else if (!strcmp(a, "--replay")  && i+1 < argc) cfg.replay_path = argv[++i];
        else if (!strcmp(a, "--record")  && i+1 < argc) cfg.record_path = argv[++i];
        else if (!strcmp(a, "--csv")     && i+1 < argc) cfg.csv_path = argv[++i];
        else if (!strcmp(a, "--probe")   && i+1 < argc)
            cfg.probe_cmd = (int)strtol(argv[++i], NULL, 0);
        else if (!strcmp(a, "--unit")    && i+1 < argc) {
            if (!cfg.units_set) { cfg.unit_n = 0; cfg.units_set = 1; } /* drop the default */
            if (cfg.unit_n < MAX_UNITS) cfg.units[cfg.unit_n++] = atoi(argv[++i]);
        }
        else if (!strcmp(a, "--assume") && i+1 < argc) {
            cfg.assume[0] = (int)strtol(argv[++i], NULL, 0);
            cfg.assume_n = 1;
        }
        else if (!strcmp(a, "--assume-cycle") && i+1 < argc) {
            const char *p = argv[++i];
            cfg.assume_n = 0;
            while (*p && cfg.assume_n < 16) {
                cfg.assume[cfg.assume_n++] = (int)strtol(p, NULL, 16);
                while (*p && *p != ',') p++;
                if (*p == ',') p++;
            }
            if (!cfg.assume_n) { cfg.assume[0] = 0x16; cfg.assume_n = 1; }
        }
        else if (!strcmp(a, "--size") && i+1 < argc) {
            const char *v = argv[++i];
            const char *eq = strchr(v, '=');
            if (eq) {
                int c = (int)strtol(v, NULL, 0);
                int n = atoi(eq + 1);
                if (c >= 0 && c < 256 && n > 0) cfg.size_override[c] = n;
            }
        }
        else { fprintf(stderr, "unknown argument: %s  (try --help)\n", a); return 2; }
    }

    if (cfg.replay_path) { cfg.master = 0; cfg.passive = 1; }
    g_detail = !cfg.quiet;

    if (cfg.record_path) {
        rec_fp = fopen(cfg.record_path, "wb");
        if (!rec_fp) { fprintf(stderr, "cannot write %s\n", cfg.record_path); return 1; }
        fwrite("P3CAP1\0\0", 1, 8, rec_fp);
        printf("recording : %s\n", cfg.record_path);
    }
    if (cfg.csv_path) {
        csv_fp = fopen(cfg.csv_path, "w");
        if (csv_fp) fprintf(csv_fp, "t_ms,unit,command,row,feature,value,status\n");
    }

    signal(SIGINT, on_sigint);
    t0 = now_ms();
#ifdef P3_NO_NET
    (void)t0; (void)next_cycle; (void)next_send; (void)link;
    (void)queue; (void)q_tail; (void)dg;
#endif

    /* ---------------- replay: no sockets involved at all ----------------- */
    if (cfg.replay_path) {
        FILE *fp = fopen(cfg.replay_path, "rb");
        unsigned char hdr[8];
        long n_dg = 0;
        unsigned long ts0 = 0, ts_last = 0;
        int first = 1;
        if (!fp) { fprintf(stderr, "cannot open %s\n", cfg.replay_path); return 1; }
        if (fread(hdr, 1, 8, fp) != 8 || memcmp(hdr, "P3CAP1", 6) != 0) {
            fprintf(stderr, "%s is not a P3CAP1 capture\n", cfg.replay_path);
            fclose(fp);
            return 1;
        }
        printf("replaying : %s\n", cfg.replay_path);
        printf("mode      : passive. MC_ answers carry no command, so each one\n"
               "            is identified by its checksum where that is unique,\n"
               "            and by the assumed poll order otherwise.\n");
        while (!g_stop && fread(hdr, 1, 8, fp) == 8) {
            unsigned long ts = get_u32le(hdr);
            int len = (int)get_u32le(hdr + 4), off;
            if (first) { ts0 = ts; first = 0; }
            ts_last = ts;
            if (len <= 0 || len > (int)sizeof dg) break;
            if ((int)fread(dg, 1, (size_t)len, fp) != len) break;
            n_dg++; st.dg_in++;
            for (off = len % GW_REC; off + GW_REC <= len; off += GW_REC) {
                can_frame f;
                int unit, r, clen = 0;
                if (!gw_read(dg + off, &f)) continue;
                st.rec_in++;
                unit = f.id - BASE_CAN_ID;
                if (unit < 1 || unit >= MAX_UNITS) { st.dropped_id++; continue; }
                st.frames++;
                if (cfg.raw) {
                    int b;
                    printf("id 0x%03X unit %2d len %d  ", f.id, unit, f.len);
                    for (b = 0; b < f.len; b++) printf("%02x ", f.data[b]);
                    printf("\n");
                    continue;
                }
                r = passive_feed(&pas[unit], &f, &clen);
                if (r == 1) {                       /* previous answer ended  */
                    passive_deliver(&model[unit], &cfg, &st, unit,
                                    pas[unit].buf, clen, &q_head[unit], ts - ts0);
                    pas[unit].got = 0; pas[unit].next_seq = 0; pas[unit].active = 1;
                    passive_feed(&pas[unit], &f, &clen);
                } else if (r < 0) {
                    st.bad_seq++;
                }
            }
        }
        fclose(fp);
        for (u = 1; u < MAX_UNITS; u++)          /* flush the last answer     */
            if (pas[u].got > 0)
                passive_deliver(&model[u], &cfg, &st, u, pas[u].buf,
                                pas[u].got, &q_head[u], ts_last - ts0);
        printf("\nreplayed %ld datagrams, %ld records, %ld answers, "
               "%ld out-of-order\n", n_dg, st.rec_in, st.answers, st.bad_seq);
        for (u = 1; u < MAX_UNITS; u++)
            if (model[u].blocks)
                printf("unit %d: %ld live blocks, %ld rows, %ld alarm flags\n",
                       u, model[u].blocks, model[u].rows_seen, model[u].alarms);
        if (rec_fp) fclose(rec_fp);
        if (csv_fp) fclose(csv_fp);
        return 0;
    }

#ifdef P3_NO_NET
    fprintf(stderr, "built with -DP3_NO_NET: only --replay FILE.cap works\n");
    return 2;
#else
    /* ---------------- live: master or passive ---------------------------- */
    {
        char host[64];
        int gwport = GW_PORT;
#  ifdef _WIN32
        WSADATA wsa;
        if (WSAStartup(MAKEWORD(2, 2), &wsa) != 0) {
            fprintf(stderr, "WSAStartup failed\n"); return 1;
        }
#  endif
        if (!parse_hostport(cfg.gw, host, (int)sizeof host, &gwport)) {
            fprintf(stderr, "--gateway expects IP:PORT\n"); return 2;
        }
        sk = socket(AF_INET, SOCK_DGRAM, 0);
        if (sk == P3_BADSOCK) { fprintf(stderr, "socket() failed\n"); return 1; }
        {
            struct sockaddr_in a;
            int one = 1;
            setsockopt(sk, SOL_SOCKET, SO_REUSEADDR, (const char *)&one, sizeof one);
            memset(&a, 0, sizeof a);
            a.sin_family = AF_INET;
            a.sin_addr.s_addr = htonl(INADDR_ANY);
            a.sin_port = htons((unsigned short)cfg.bind_port);
            if (bind(sk, (struct sockaddr *)&a, sizeof a) != 0) {
                fprintf(stderr, "bind :%d failed - is PROVIS3 or another reader "
                                "using it?\n", cfg.bind_port);
                return 1;
            }
        }
        memset(&gw_addr, 0, sizeof gw_addr);
        gw_addr.sin_family = AF_INET;
        gw_addr.sin_port = htons((unsigned short)gwport);
        gw_addr.sin_addr.s_addr = inet_addr(host);
        if (gw_addr.sin_addr.s_addr == INADDR_NONE) {
            fprintf(stderr, "--gateway: use a numeric IP, not a name\n"); return 2;
        }
        printf("gateway   : %s:%d\n", host, gwport);
        printf("local port: %d%s\n", cfg.bind_port,
               cfg.bind_port ? "" : "  (ephemeral)");
        printf("mode      : %s   units", cfg.master ? "master (asks)" : "passive");
        for (u = 0; u < cfg.unit_n; u++) printf(" %d", cfg.units[u]);
        printf("\n");
        if (cfg.master)
            printf("            an MC_ answer has no command byte, so only the\n"
                   "            asker can name it. That is why this mode exists.\n");
    }

    /* prime the per-unit command queues */
    for (u = 0; u < cfg.unit_n; u++) {
        int unit = cfg.units[u];
        if (cfg.probe_cmd >= 0) { queue[unit][q_tail[unit]++ % 16] = cfg.probe_cmd; }
        else {
            queue[unit][q_tail[unit]++ % 16] = 0x06;    /* discovery */
            queue[unit][q_tail[unit]++ % 16] = 0x02;
            queue[unit][q_tail[unit]++ % 16] = 0x0e;
        }
    }

    while (!g_stop) {
        fd_set rd;
        struct timeval tv;
        unsigned long now = now_ms();
        int n, off;

        if (cfg.seconds > 0 && (long)(now - t0) > (long)cfg.seconds * 1000L) break;

        /* ---- master: keep exactly one request in flight per unit -------- */
        if (cfg.master && now >= next_send) {
            for (u = 0; u < cfg.unit_n; u++) {
                int unit = cfg.units[u];
                if (link[unit].busy) continue;
                if (q_head[unit] == q_tail[unit]) continue;
                {
                    int cmd = queue[unit][q_head[unit] % 16];
                    int rec_size = 0, conf = 0;
                    int exp = expected_size(&cfg, &model[unit], cmd, &rec_size, &conf);
                    can_frame fr[8];
                    unsigned char rec[GW_REC * 8];
                    int nf, k, off2 = 0;
                    if (cfg.probe_cmd >= 0) exp = -2;   /* measure, do not assume */
                    q_head[unit]++;
                    link_arm(&link[unit], unit, cmd, 1, rec_size, exp, now,
                             cfg.timeout_ms);
                    nf = mc_frame_request(link[unit].req, link[unit].req_n,
                                          BASE_CAN_ID + unit, fr, 8);
                    for (k = 0; k < nf; k++) {
                        gw_write(rec + off2, fr[k].id, fr[k].len, fr[k].data);
                        off2 += GW_REC;
                    }
                    sendto(sk, (const char *)rec, off2, 0,
                           (struct sockaddr *)&gw_addr, (p3_socklen)sizeof gw_addr);
                    st.requests++;
                    if (!cfg.quiet) {
                        const cmd_desc *cd = cmd_find(cmd);
                        int b;
                        printf("\n--> unit %d  %s  request", unit,
                               cd ? cd->name : "cmd");
                        for (b = 0; b < link[unit].req_n; b++)
                            printf(" %02x", link[unit].req[b]);
                        printf("   expect %s%d bytes %s\n",
                               exp == -1 ? "<from first frame> " :
                               exp == -2 ? "<measure> " : "",
                               exp < 0 ? 0 : exp, conf_tag(conf));
                    }
                    next_send = now + (unsigned long)cfg.gap_ms;
                    break;                       /* one request at a time     */
                }
            }
        }

        /* ---- master: refill the cyclic poll set ------------------------- */
        if (cfg.master && cfg.probe_cmd < 0 && now >= next_cycle) {
            for (u = 0; u < cfg.unit_n; u++) {
                int unit = cfg.units[u], c;
                if (q_tail[unit] - q_head[unit] > 8) continue;   /* still busy */
                for (c = 0; c < model[unit].channels; c++)
                    queue[unit][q_tail[unit]++ % 16] = 0x16;
                for (c = 0; c < model[unit].channels; c++)
                    queue[unit][q_tail[unit]++ % 16] = 0x08;
                queue[unit][q_tail[unit]++ % 16] = 0x01;
                if (cfg.alarm) queue[unit][q_tail[unit]++ % 16] = 0x12;
                if (cfg.trace) queue[unit][q_tail[unit]++ % 16] = 0x1b;
            }
            next_cycle = now + (unsigned long)cfg.poll_ms;
        }

        /* ---- timeouts and the retry ladder ------------------------------ */
        for (u = 0; u < cfg.unit_n; u++) {
            int unit = cfg.units[u];
            if (!link[unit].busy) continue;
            if (link[unit].expected == -2 && link[unit].got > 0 &&
                now - link[unit].last_rx > 300) {
                /* --probe / measure mode: the bus went quiet, so the answer
                 * is whatever arrived. Exactly one byte of it is the checksum. */
                p3_msg g;
                unsigned char want;
                int total = link[unit].got;
                memset(&g, 0, sizeof g);
                g.unit = unit; g.cmd = link[unit].cmd;
                g.body = link[unit].buf; g.body_len = total - 1;
                want = p3_checksum(unit, link[unit].req, link[unit].req_n,
                                   g.body, g.body_len);
                g.ck_ok = (want == link[unit].buf[total - 1]) ? 1 : 0;
                g.attributed = 1; g.how = "request";
                printf("\nMEASURED  unit %d  cmd 0x%02X  answer payload = %d bytes"
                       "  checksum %s\n", unit, g.cmd, g.body_len,
                       g.ck_ok ? "AGREES - this is the real size" :
                                 "does not agree - answer was cut short");
                printf("          put it in the table:  --size 0x%02X=%d\n",
                       g.cmd, g.body_len);
                st.answers++;
                show_message(&model[unit], &g, cfg.rows_shown, now - t0);
                link[unit].busy = 0;
                if (cfg.probe_cmd >= 0) g_stop = 1;
                continue;
            }
            if (now > link[unit].deadline) {
                st.timeouts++;
                if (link[unit].attempts <= cfg.resend) {
                    can_frame fr[8];
                    unsigned char rec[GW_REC * 8];
                    int nf, k, off2 = 0;
                    link[unit].attempts++;
                    link[unit].got = 0; link[unit].next_seq = 0;
                    link[unit].have_ck = 0; link[unit].poisoned = 0;
                    link[unit].last_avail = 0;
                    link[unit].deadline = now + (unsigned long)cfg.timeout_ms;
                    nf = mc_frame_request(link[unit].req, link[unit].req_n,
                                          BASE_CAN_ID + unit, fr, 8);
                    for (k = 0; k < nf; k++) {
                        gw_write(rec + off2, fr[k].id, fr[k].len, fr[k].data);
                        off2 += GW_REC;
                    }
                    sendto(sk, (const char *)rec, off2, 0,
                           (struct sockaddr *)&gw_addr, (p3_socklen)sizeof gw_addr);
                    printf("... unit %d cmd 0x%02X timed out, resending (%d/%d)\n",
                           unit, link[unit].cmd, link[unit].attempts - 1, cfg.resend);
                } else {
                    st.aborts++;
                    printf("!!! unit %d cmd 0x%02X aborted after %d attempts"
                           " - got %d of %d bytes\n", unit, link[unit].cmd,
                           link[unit].attempts, link[unit].got,
                           link[unit].expected);
                    if (link[unit].poisoned)
                        printf("    frames were lost or arrived out of order -\n"
                               "    a transport problem, not a decoding one\n");
                    else if (link[unit].got == 0)
                        printf("    nothing came back at all. If this is the real\n"
                               "    machine: is PROVIS3 also polling this unit?\n");
                    else {
                        const cmd_desc *cd2 = cmd_find(link[unit].cmd);
                        printf("    the answer stopped short of the expected size.\n");
                        if (!cd2 || cd2->conf != C_VERIFIED)
                            printf("    that size is a guess - measure it with"
                                   " --probe 0x%02X\n", link[unit].cmd);
                    }
                    link[unit].busy = 0;
                }
            }
        }

        /* ---- receive ---------------------------------------------------- */
        FD_ZERO(&rd);
        FD_SET(sk, &rd);
        tv.tv_sec = 0; tv.tv_usec = 20000;
        if (select((int)sk + 1, &rd, NULL, NULL, &tv) <= 0) continue;

        {
            struct sockaddr_in from;
            p3_socklen fl = (p3_socklen)sizeof from;
            n = (int)recvfrom(sk, (char *)dg, (int)sizeof dg, 0,
                              (struct sockaddr *)&from, &fl);
        }
        if (n <= 0) continue;
        st.dg_in++;
        if (rec_fp) {
            unsigned char h[8];
            put_u32le(h, now_ms() - t0);
            put_u32le(h + 4, (unsigned long)n);
            fwrite(h, 1, 8, rec_fp);
            fwrite(dg, 1, (size_t)n, rec_fp);
        }

        /* Scan4CANmsg: 36-byte records, remainder trimmed from the FRONT */
        for (off = n % GW_REC; off + GW_REC <= n; off += GW_REC) {
            can_frame f;
            int unit, r;
            p3_msg g;
            if (!gw_read(dg + off, &f)) continue;
            st.rec_in++;
            unit = f.id - BASE_CAN_ID;
            if (unit < 1 || unit >= MAX_UNITS) { st.dropped_id++; continue; }
            st.frames++;

            if (cfg.raw) {
                int b;
                printf("id 0x%03X unit %2d len %d  ", f.id, unit, f.len);
                for (b = 0; b < f.len; b++) printf("%02x ", f.data[b]);
                printf("\n");
                continue;
            }

            if (cfg.passive) {
                int clen = 0;
                r = passive_feed(&pas[unit], &f, &clen);
                if (r == 1) {
                    passive_deliver(&model[unit], &cfg, &st, unit, pas[unit].buf,
                                    clen, &q_head[unit], now_ms() - t0);
                    pas[unit].got = 0; pas[unit].next_seq = 0; pas[unit].active = 1;
                    passive_feed(&pas[unit], &f, &clen);
                } else if (r < 0) st.bad_seq++;
                continue;
            }

            memset(&g, 0, sizeof g);
            r = link_feed(&link[unit], unit, &f, &g);
            switch (r) {
            case LK_DONE:
                st.answers++;
                show_message(&model[unit], &g, cfg.rows_shown, now_ms() - t0);
                if (csv_fp && g.cmd == 0x16 && g.body_len > 1) {
                    int stride = model[unit].features * 2 + 2;
                    int rows = g.body[0], rr, ff;
                    for (rr = 0; rr < rows && 1 + (rr+1)*stride <= g.body_len; rr++)
                        for (ff = 0; ff < model[unit].features; ff++) {
                            const unsigned char *row = g.body + 1 + rr * stride;
                            int a = row[ff*2], b = row[ff*2+1];
#if MERKMAL_VALUE_IS_HI
                            fprintf(csv_fp, "%lu,%d,0x16,%d,%s,%d,%d\n",
                                    now_ms() - t0, unit, rr,
                                    model[unit].fname[ff][0] ?
                                    model[unit].fname[ff] : "?", b, a);
#else
                            fprintf(csv_fp, "%lu,%d,0x16,%d,%s,%d,%d\n",
                                    now_ms() - t0, unit, rr,
                                    model[unit].fname[ff][0] ?
                                    model[unit].fname[ff] : "?", a, b);
#endif
                        }
                }
                break;
            case LK_BAD_CK:
                st.bad_ck++;
                printf("!!! unit %d cmd 0x%02X CHECKSUM MISMATCH over %d bytes"
                       " - discarded\n", unit, g.cmd, g.body_len);
                break;
            case LK_BAD_SEQ:
                st.bad_seq++;
                printf("!!! unit %d out-of-order frame (seq %d) - the app calls\n"
                       "    this \"Unknown answer format received on CAN bus\"\n",
                       unit, f.data[0]);
                break;
            case LK_DEV_ERR:
                st.dev_err++;
                printf("!!! unit %d cmd 0x%02X device error answer [00 01]\n",
                       unit, link[unit].cmd);
                break;
            case LK_DISCARD:
                st.discarded++;
                break;
            case LK_UNSOLICITED:
                st.unsolicited++;
                break;
            default: break;
            }
        }
    }

    printf("\n--- summary -------------------------------------------------\n");
    printf("requests sent      %ld\n", st.requests);
    printf("datagrams in       %ld   records %ld   frames %ld\n",
           st.dg_in, st.rec_in, st.frames);
    printf("answers decoded    %ld\n", st.answers);
    printf("checksum failures  %ld\n", st.bad_ck);
    printf("sequence failures  %ld\n", st.bad_seq);
    printf("device errors      %ld\n", st.dev_err);
    printf("timeouts / aborts  %ld / %ld\n", st.timeouts, st.aborts);
    printf("frames for another unit id  %ld\n", st.dropped_id);
    printf("frames dropped after an error  %ld\n", st.discarded);
    printf("unsolicited frames %ld", st.unsolicited);
    if (st.unsolicited)
        printf("   (answers nobody asked for: another master on the bus,\n"
               "                          or leftovers of a discarded answer)");
    printf("\n");
    for (u = 0; u < cfg.unit_n; u++) {
        int unit = cfg.units[u];
        printf("unit %d: %ld live blocks, %ld rows, %ld alarm flags, "
               "cycle %d, features %d\n", unit, model[unit].blocks,
               model[unit].rows_seen, model[unit].alarms,
               model[unit].cycle, model[unit].features);
    }
    if (rec_fp) { fclose(rec_fp); printf("capture written: %s\n", cfg.record_path); }
    if (csv_fp) { fclose(csv_fp); printf("csv written    : %s\n", cfg.csv_path); }
    if (sk != P3_BADSOCK) p3_closesock(sk);
#  ifdef _WIN32
    WSACleanup();
#  endif
    return 0;
#endif  /* P3_NO_NET */
}
