/* ============================================================================
 * promos3_sim.c  --  Prometec PROVIS3 / Promos3 "MC_" monitoring unit and
 *                    CAN-over-UDP gateway SIMULATOR.
 *
 * It produces byte-exact synthetic traffic that duplicates what the real Mazak
 * monitoring unit does: it answers requests the way the unit answers them, and
 * it can also push a whole shift of measurement traffic at a listener or into
 * a capture file so the decoder can be developed with no machine present.
 *
 * Companion program: promos3_view.c  (reads it and prints what the GUI shows).
 *
 * ---------------------------------------------------------------------------
 * BUILD - nothing to install, no third-party library, no .lib hunting
 *
 *   Windows / MinGW  (PowerShell; note -lws2_32 goes LAST, that is what the
 *                     linker wants, and it is the whole reason for the classic
 *                     "undefined reference to `recvfrom'" message):
 *       gcc -std=c11 -O2 -Wall -Wextra promos3_sim.c -o promos3_sim.exe -lws2_32
 *
 *   Windows / MSVC   (the library is named by the #pragma below, so
 *                     "LNK1104: cannot open file 'ws2_32.lib'" cannot occur
 *                     unless the SDK itself is missing):
 *       cl /nologo /W3 /O2 promos3_sim.c
 *
 *   Linux / macOS:
 *       cc -std=c11 -O2 -Wall -Wextra promos3_sim.c -o promos3_sim
 *
 *   NO SOCKETS AT ALL (writes only a capture file; links literally zero
 *   libraries - the escape hatch if any linker ever misbehaves):
 *       gcc -std=c11 -O2 -DP3_NO_NET promos3_sim.c -o promos3_sim
 *
 * Deliberate portability choices, each one a bug we are not going to have:
 *   no <math.h>        -> never needs -lm
 *   no malloc          -> no leaks, no allocation-failure paths
 *   no %zu, no size_t in printf -> old MinGW msvcrt prints the letters "zu"
 *   no snprintf        -> MSVC before 2015 does not have it
 *   no VLAs, no designated initialisers -> older MSVC in C mode
 *   SOCKET is UNSIGNED on Windows: compared against INVALID_SOCKET, never < 0
 *   source and output are pure ASCII -> Turkish/German consoles are cp857 /
 *   cp1254 and would turn UTF-8 bar characters into garbage
 *
 * ---------------------------------------------------------------------------
 * STYLE - data-oriented, pragmatic functional
 *   Every type is plain data. No hidden state, no ownership, no heap.
 *   Sections 3-5 are pure transforms (data in -> data out); they can be tested
 *   and replayed without a socket in sight. All I/O lives in sections 6-9.
 *   Behaviour is table driven (CMD_TAB), not switch-spaghetti.
 *
 * ---------------------------------------------------------------------------
 * WHERE EVERY CONSTANT COMES FROM  (RE report parts 2, 7, 16, 17, 18)
 *   36-byte gateway record, header 00 24 00 80 ....... Part 18 3.1  verified
 *   LEN@0x15, ID@0x1A..1B big-endian, DATA@0x1C ...... Part 2.2     verified
 *   CAN-ID = 1280 + unit, ONE base both directions ... Part 18 3.3  verified
 *   request  = [cmd][station][params..][checksum] .... Part 16 3.10 verified
 *   request framing [00][00][00][5B] then [seq][7B] .. Part 18 3.2  verified
 *   answer frame = [seq][7 payload][ck if it fits] ... Part 16 2    verified
 *   checksum = -(unit + SUM(request minus own ck)
 *                     + SUM(answer payload)) ......... Part 16 3    byte-verified
 *                                                      against "08 01 f6"
 *   0x16 size = rows * (features*2+2) + 1 ............ Part 18 4.1  verified
 *   SKanalRecV40 features @+0x4D, 4 x [mask][name11] . Part 7.2     verified
 *   answer sizes of 0x01 / 0x08 / 0x12 / 0x1b ........ GUESSES, see CMD_TAB
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
#include <string.h>
#include <time.h>
#include <signal.h>

/* ===========================================================================
 * SECTION 1 -- PORTABILITY SHIMS.  The only #ifdef zone in the program.
 * ========================================================================= */
#ifdef _WIN32
#  define WIN32_LEAN_AND_MEAN
#  ifndef P3_NO_NET
#    include <winsock2.h>            /* MUST be included before windows.h */
#    ifdef _MSC_VER
#      pragma comment(lib, "ws2_32.lib")
#    endif
     typedef SOCKET p3_sock;
     typedef int    p3_socklen;
#    define P3_BADSOCK   INVALID_SOCKET
#    define p3_closesock closesocket
#  endif
#  include <windows.h>               /* Sleep(), GetTickCount()           */
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

static void sleep_ms(int ms)
{
    if (ms <= 0) return;
#ifdef _WIN32
    Sleep((DWORD)ms);
#else
    { struct timespec ts;
      ts.tv_sec  = ms / 1000;
      ts.tv_nsec = (long)(ms % 1000) * 1000000L;
      nanosleep(&ts, NULL); }
#endif
}

static volatile sig_atomic_t g_stop = 0;
static void on_sigint(int s) { (void)s; g_stop = 1; }

/* ===========================================================================
 * SECTION 2 -- WIRE FACTS.  Keep byte-identical with promos3_view.c.
 * ========================================================================= */
#define GW_REC          36          /* one gateway record = one CAN frame   */
#define GW_OFF_LEN      0x15
#define GW_OFF_ID_HI    0x1A
#define GW_OFF_ID_LO    0x1B
#define GW_OFF_DATA     0x1C
#define CAN_MAXDATA     8
#define BASE_CAN_ID     1280        /* [CAN] BaseCanIDTransfer              */
#define GW_PORT         1789        /* [CAN] GatewayPort                    */
#define PAY_PER_FRAME   7           /* MC_: DATA[0] carries the sequence no */
#define MAX_MSG         4096
#define MAX_FRAMES      768
#define MAX_UNITS       16          /* FirstDevice..LastDevice = 1..15      */
#define NFEAT_MAX       4

typedef struct {                    /* one CAN frame, transport neutral     */
    int           id;               /* 11-bit CAN id                        */
    int           len;              /* dlc, 0..8                            */
    unsigned char data[CAN_MAXDATA];
} can_frame;

enum { SZ_FIXED = 0, SZ_ROWS = 1 };            /* SZ_ROWS: rows*stride + 1  */
enum { C_VERIFIED = 0, C_TABLE = 1, C_ASSUMED = 2 };

typedef struct {
    int         cmd;
    const char *name;
    int         req_len;    /* [cmd][params..][ck], total bytes on the wire  */
    int         size_rule;
    int         size;       /* expected ANSWER payload size when SZ_FIXED    */
    int         conf;
    const char *note;
} cmd_desc;

/* The read-only command set of an MC_ box. req_len for 0x08 is byte-verified
 * from the app's own log line: "requested 0x08, 0x01, 0xf6". */
static const cmd_desc CMD_TAB[] = {
  { 0x01, "MC_GIVESTATUS",         2, SZ_FIXED,   4, C_ASSUMED,
    "sender never calls setRecvSize - the size is a pure guess, measure it" },
  { 0x02, "MC_GIVEGTYPE",          2, SZ_FIXED,  14, C_TABLE,
    "size table says 14 but labels it SGrenzRec - known conflict" },
  { 0x06, "MC_GIVEKONFIG",         3, SZ_FIXED,   3, C_ASSUMED,
    "body anchored on E5 01 04 = version / channels / sensors from the log" },
  { 0x08, "MC_GIVEPLCVALUES",      3, SZ_FIXED,   2, C_ASSUMED,
    "true size is computed at runtime from Geraet+0x4e6 (open item D4)" },
  { 0x0e, "MC_GIVEKANAL",          3, SZ_FIXED, 144, C_VERIFIED,
    "SKanalRecV40, size verified at the call site" },
  { 0x12, "MC_GIVEALARM",          3, SZ_FIXED,  34, C_ASSUMED,
    "the size-table entry actually belongs to 0x11 ALARMGESEHEN" },
  { 0x16, "MC_GIVESAMMELMERKMALE", 4, SZ_ROWS,    0, C_VERIFIED,
    "rows*(features*2+2)+1; the first payload byte is the row count" },
  { 0x1b, "MC_GIVESIGNALVERLAUF",  6, SZ_FIXED, 257, C_ASSUMED,
    "5 header + 125*int16 + 2 trailer; 257 came from a synthetic test" }
};
#define CMD_TAB_N ((int)(sizeof CMD_TAB / sizeof CMD_TAB[0]))

static const cmd_desc *cmd_find(int cmd)
{
    int i;
    for (i = 0; i < CMD_TAB_N; i++) if (CMD_TAB[i].cmd == cmd) return &CMD_TAB[i];
    return NULL;
}

/* Which byte of each feature pair carries the amplitude.
 * UNCONFIRMED. Part 17 section 8 states both "lo == 0xFF is an escape" and
 * "lo & 0x04 = alarm", which are only both sensible if lo is a STATUS byte and
 * hi is the VALUE. That is the convention encoded here and in the reader.
 * One real capture settles it; then flip this in both files. */
#define MERKMAL_VALUE_IS_HI 1

/* ===========================================================================
 * SECTION 3 -- PURE CODEC LAYER.  No I/O, no globals, fully testable.
 * ========================================================================= */

/* Promos3 checksum, MC_ generation (groups 0 and 1):
 *     seed = unit
 *          + SUM(request bytes EXCLUDING the request's own trailing checksum)
 *          + SUM(answer payload bytes)
 *     ck   = -seed        (8-bit two's complement)
 * Byte-verified: unit 1, request {08,01} -> -(1+9) = -10 = 0xF6. */
static unsigned char p3_checksum(int unit,
                                 const unsigned char *sent, int sent_n,
                                 const unsigned char *recv, int recv_n)
{
    int seed = unit, i;
    if (sent && sent_n > 0) for (i = 0; i < sent_n - 1; i++) seed += sent[i];
    if (recv) for (i = 0; i < recv_n; i++) seed += recv[i];
    return (unsigned char)(-seed);
}

/* Checksum for a request we are about to send (msg = cmd+params, no ck yet). */
static unsigned char p3_ck_request(int unit, const unsigned char *msg, int n)
{
    int seed = unit, i;
    for (i = 0; i < n; i++) seed += msg[i];
    return (unsigned char)(-seed);
}

/* The canonical request the poll cycle emits for a command. Both programs call
 * this, so a pushed answer (--stream) can still be checksum-verified by a
 * reader that was told which command to assume. */
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

/* Build one 36-byte gateway record. The header is literally 00 24 00 80 + 0s. */
static void gw_write(unsigned char *out36, int can_id, int len,
                     const unsigned char *data)
{
    int i;
    memset(out36, 0, GW_REC);
    out36[0] = 0x00; out36[1] = 0x24;      /* record length 36, BIG-ENDIAN   */
    out36[2] = 0x00; out36[3] = 0x80;      /* constant type/flags            */
    out36[GW_OFF_LEN]   = (unsigned char)len;
    out36[GW_OFF_ID_HI] = (unsigned char)((can_id >> 8) & 0xFF);
    out36[GW_OFF_ID_LO] = (unsigned char)(can_id & 0xFF);
    for (i = 0; i < len && i < CAN_MAXDATA; i++) out36[GW_OFF_DATA + i] = data[i];
}

/* Decode one 36-byte gateway record. 0 if the dlc is impossible. */
static int gw_read(const unsigned char *in36, can_frame *f)
{
    int i;
    f->len = in36[GW_OFF_LEN];
    if (f->len > CAN_MAXDATA) return 0;
    f->id = (in36[GW_OFF_ID_HI] << 8) | in36[GW_OFF_ID_LO];
    for (i = 0; i < CAN_MAXDATA; i++) f->data[i] = in36[GW_OFF_DATA + i];
    return 1;
}

/* Split an answer payload into MC_ answer frames.
 *   frame k : [seq=k][up to 7 payload bytes]
 * The checksum is the byte immediately after the last payload byte IF it fits;
 * when the last data frame was full (n % 7 == 0) it needs a frame of its own,
 * [seq][ck], and that also covers the n == 0 pure-acknowledgement case. */
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
        } else {
            out[cnt].len = 8;
        }
        cnt++; i += chunk; seq++;
    }
    if (n % PAY_PER_FRAME == 0) {                 /* lone checksum frame     */
        if (cnt >= max) return -1;
        out[cnt].id = can_id;
        out[cnt].data[0] = (unsigned char)(seq & 0xFF);
        out[cnt].data[1] = ck;
        out[cnt].len = 2;
        cnt++;
    }
    return cnt;
}

/* Split a request into app->device frames:
 *   first frame  : [00][00][00][up to 5 payload]   len = 3 + chunk
 *   continuation : [seq][up to 7 payload]          len = 1 + chunk       */
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

/* ===========================================================================
 * SECTION 4 -- THE DEVICE MODEL.  Pure generators: state -> payload bytes.
 *
 * This is the part that "duplicates what the machine does": a unit running
 * machining cycles, four feature channels, workpieces, and the occasional
 * overload alarm.
 * ========================================================================= */
typedef struct {
    /* identity -------------------------------------------------------- */
    int unit;                       /* 1..15                              */
    int version;                    /* 229 = 0xE5 on this box             */
    int gtype, gsubtype;            /* 0x44 / 5 -> MSL5081-16             */
    int channels, sensors, features;
    unsigned char fmask[NFEAT_MAX];
    char          fname[NFEAT_MAX][12];
    /* live state ------------------------------------------------------- */
    unsigned rng;
    int tick;                       /* one tick per measurement row       */
    int cycle;                      /* current cycle index                */
    int wp_id;                      /* workpiece counter                  */
    int cut_len;                    /* rows per cycle                     */
    int marker;                     /* -1 none, else pending marker byte  */
    int marker_param;
    int marker_stage;               /* 0 idle, 1 emit marker, 2 emit param*/
    int alarm_in;                   /* rows left with the alarm bit set   */
} sim_dev;

/* integer sine, 64 steps, +-100. Keeps <math.h> and -lm out of the build. */
static const signed char SIN64[64] = {
       0,   10,   20,   29,   38,   47,   56,   63,
      71,   77,   83,   88,   92,   96,   98,  100,
     100,  100,   98,   96,   92,   88,   83,   77,
      71,   63,   56,   47,   38,   29,   20,   10,
       0,  -10,  -20,  -29,  -38,  -47,  -56,  -63,
     -71,  -77,  -83,  -88,  -92,  -96,  -98, -100,
    -100, -100,  -98,  -96,  -92,  -88,  -83,  -77,
     -71,  -63,  -56,  -47,  -38,  -29,  -20,  -10
};

static unsigned rng_next(unsigned *s)
{
    unsigned x = *s;
    x ^= x << 13; x ^= x >> 17; x ^= x << 5;
    *s = x ? x : 0x9E3779B9u;
    return *s;
}

static void dev_init(sim_dev *d, int unit, unsigned seed)
{
    /* the operator-assigned labels of THIS installation, from 1974.txt */
    static const char *NAMES[NFEAT_MAX] =
        { "VIBRATION", "M131 DEBI", "M131BASINC", "M08 DEBI" };
    int f;
    memset(d, 0, sizeof *d);
    d->unit = unit; d->version = 229; d->gtype = 0x44; d->gsubtype = 5;
    d->channels = 1; d->sensors = 4; d->features = 4;
    for (f = 0; f < NFEAT_MAX; f++) {
        d->fmask[f] = (unsigned char)(1 << f);           /* 01 02 04 08 */
        memset(d->fname[f], 0, sizeof d->fname[f]);
        strncpy(d->fname[f], NAMES[f], sizeof d->fname[f] - 1);
    }
    d->rng = seed ? seed : 0xC0FFEEu;
    d->cycle = 1; d->wp_id = 1; d->cut_len = 24;
    d->marker = -1; d->marker_stage = 0;
}

/* one raw amplitude count (0..254) for feature f at a given phase */
static int dev_sample(sim_dev *d, int f, int phase)
{
    static const int BASE[NFEAT_MAX] = { 40,  96, 150,  70 };
    static const int AMPL[NFEAT_MAX] = { 30,  70,  40,  55 };
    int idx = (phase * (f + 1)) & 63;
    int v = BASE[f] + (AMPL[f] * SIN64[idx]) / 100;
    v += (int)(rng_next(&d->rng) % 9u) - 4;              /* +-4 counts noise */
    if (d->alarm_in > 0 && f == 1) v += 60;              /* the overload      */
    if (v < 0) v = 0;
    if (v > 254) v = 254;                                /* 255 = escape      */
    return v;
}

/* advance the machine by one measurement row; may arm a marker */
static void dev_tick(sim_dev *d)
{
    d->tick++;
    if (d->alarm_in > 0) d->alarm_in--;
    if (d->tick % d->cut_len == 0 && d->marker_stage == 0) {
        d->cycle = (d->cycle % 9) + 1;                  /* 9 cycles in the PMD */
        if (d->cycle == 1) {
            d->wp_id++;
            d->marker = 0xFE;                           /* workpiece id marker */
            d->marker_param = 2;                        /* [WorkpieceID] IDsize*/
        } else {
            d->marker = 0x00;                           /* new cycle marker    */
            d->marker_param = d->cycle;
        }
        d->marker_stage = 1;
    }
    if ((rng_next(&d->rng) % 300u) == 0u) d->alarm_in = 5;
}

/* --- 0x16 MC_GIVESAMMELMERKMALE - the live measurement block -------------
 * payload[0]        = row count
 * stride            = features*2 + 2        ('H' device type would be +4)
 * row r, feature f  = [status][value]       (see MERKMAL_VALUE_IS_HI)
 * status == 0xFF    = escape; the value byte is the marker and the FOLLOWING
 *                     row carries the parameter
 * status bit 0x04   = alarm
 * value bits 0x01 / 0x10 / 0x40 = teach / start-stop / tool change
 * The 2 trailing bytes of each row are not identified anywhere in the report;
 * we send zeros and the reader prints them as unknown rather than inventing
 * a meaning for them. */
static int gen_merkmale(sim_dev *d, int rows, unsigned char *out, int cap)
{
    int stride = d->features * 2 + 2;
    int need = rows * stride + 1;
    int r, f, p = 1;
    if (rows < 1 || need > cap) return -1;
    out[0] = (unsigned char)rows;
    for (r = 0; r < rows; r++) {
        int stage = d->marker_stage;                 /* 0 normal, 1 marker, 2 param */
        for (f = 0; f < d->features; f++) {
            unsigned char st, val;
            if (stage == 1) {
                st = 0xFF; val = (unsigned char)d->marker;
            } else if (stage == 2) {
                st = (unsigned char)d->marker_param; val = 0x00;
            } else {
                int v = dev_sample(d, f, d->tick);
                st = (unsigned char)(d->alarm_in > 0 ? 0x04 : 0x00);
                if (d->tick % d->cut_len < 2) st |= 0x10;   /* start/stop mark */
                val = (unsigned char)v;
            }
#if MERKMAL_VALUE_IS_HI
            out[p++] = st;  out[p++] = val;
#else
            out[p++] = val; out[p++] = st;
#endif
        }
        out[p++] = 0x00;                             /* 2 unidentified bytes  */
        out[p++] = 0x00;
        if (stage == 1)      d->marker_stage = 2;
        else if (stage == 2) { d->marker_stage = 0; d->marker = -1; }
        else                 dev_tick(d);
    }
    return need;
}

/* --- 0x0e MC_GIVEKANAL - SKanalRecV40, 144 bytes, layout verified -------- */
static int gen_kanal(const sim_dev *d, unsigned char *out, int cap)
{
    int f, i;
    if (cap < 144) return -1;
    memset(out, 0, 144);
    out[0x00] = 0x10;                                /* PLC_Type    = 16     */
    out[0x01] = 0x20;                                /* PLC_Version = 32     */
    out[0x02] = (unsigned char)d->channels;          /* Channel_Num          */
    for (i = 0; i < 4; i++) out[0x10 + i] = 0xAA;    /* CDRLim[4] = 170      */
    for (f = 0; f < d->features && f < NFEAT_MAX; f++) {
        unsigned char *slot = out + 0x4D + f * 12;   /* [mask][name 11]      */
        slot[0] = d->fmask[f];
        memcpy(slot + 1, d->fname[f], 11);
    }
    return 144;
}

/* --- 0x06 MC_GIVEKONFIG - the "Version 229 Channels 1 Sensors 4" line ---- */
static int gen_konfig(const sim_dev *d, unsigned char *out, int cap)
{
    if (cap < 3) return -1;
    out[0] = (unsigned char)d->version;
    out[1] = (unsigned char)d->channels;
    out[2] = (unsigned char)d->sensors;
    return 3;
}

/* --- 0x1b MC_GIVESIGNALVERLAUF - 125 x int16 LE, raw 0..255, no scaling -- */
static int gen_trace(sim_dev *d, int station, int fi, unsigned char *out, int cap)
{
    int i, p;
    if (cap < 257) return -1;
    out[0] = (unsigned char)station;                       /* toolKey        */
    out[1] = d->fmask[fi < NFEAT_MAX ? fi : 0];            /* channelKey     */
    out[2] = 0x00;                                         /* paramA         */
    out[3] = 0x00;                                         /* flag           */
    out[4] = 0x02;                                         /* mode (!=1 -> B)*/
    p = 5;
    for (i = 0; i < 125; i++) {
        int v = dev_sample(d, fi < NFEAT_MAX ? fi : 0, i * 2);
        out[p++] = (unsigned char)(v & 0xFF);              /* int16 LITTLE   */
        out[p++] = 0x00;
    }
    out[p++] = 0x7D;                                       /* trailer = 125  */
    out[p++] = 0x00;
    return p;                                              /* 257            */
}

/* --- 0x08 MC_GIVEPLCVALUES - this box has 4 PLC inputs and 1 output ------ */
static int gen_plc(const sim_dev *d, unsigned char *out, int cap)
{
    if (cap < 2) return -1;
    out[0] = (unsigned char)((d->tick / 5) & 0x0F);        /* input bitmap   */
    out[1] = (unsigned char)(d->alarm_in > 0 ? 0x01 : 0x00);/* output bitmap */
    return 2;
}

/* --- 0x01 MC_GIVESTATUS - size and layout both unknown, tagged as such --- */
static int gen_status(const sim_dev *d, unsigned char *out, int cap)
{
    if (cap < 4) return -1;
    out[0] = (unsigned char)(d->alarm_in > 0 ? 0x01 : 0x00);
    out[1] = (unsigned char)d->cycle;
    out[2] = (unsigned char)(d->wp_id & 0xFF);
    out[3] = (unsigned char)((d->wp_id >> 8) & 0xFF);
    return 4;
}

/* --- 0x12 MC_GIVEALARM - the layout is MC3_-derived, i.e. provisional ---- */
static int gen_alarm(const sim_dev *d, unsigned char *out, int cap)
{
    if (cap < 34) return -1;
    memset(out, 0, 34);
    out[0x00] = 0x01;                                  /* sub-command 1      */
    out[0x01] = (unsigned char)(d->alarm_in > 0 ? 1 : 0);
    out[0x03] = 0x02;                                  /* alarm 2 = Break    */
    out[0x05] = (unsigned char)d->cycle;
    out[0x21] = 0x01;                                  /* channelKey         */
    return 34;
}

/* --- 0x02 MC_GIVEGTYPE - 14 bytes per the (conflicted) size table -------- */
static int gen_gtype(const sim_dev *d, unsigned char *out, int cap)
{
    int serial = 10659 + (d->unit - 1) * 4;            /* 10659 / 10663 ...  */
    if (cap < 14) return -1;
    memset(out, 0, 14);
    out[0] = (unsigned char)d->gtype;
    out[1] = (unsigned char)d->gsubtype;
    out[2] = (unsigned char)d->channels;
    out[3] = (unsigned char)d->sensors;
    out[4] = (unsigned char)(serial & 0xFF);
    out[5] = (unsigned char)((serial >> 8) & 0xFF);
    out[6] = (unsigned char)d->version;
    return 14;
}

/* single dispatch point: (device, request bytes) -> answer payload */
static int dev_answer(sim_dev *d, const unsigned char *req, int req_n,
                      int rows, unsigned char *out, int cap)
{
    int cmd = req[0];
    int station = (req_n > 2) ? req[1] : 1;
    switch (cmd) {
    case 0x01: return gen_status(d, out, cap);
    case 0x02: return gen_gtype(d, out, cap);
    case 0x06: return gen_konfig(d, out, cap);
    case 0x08: return gen_plc(d, out, cap);
    case 0x0e: return gen_kanal(d, out, cap);
    case 0x12: return gen_alarm(d, out, cap);
    case 0x16: return gen_merkmale(d, rows, out, cap);
    case 0x1b: {
        int key = (req_n > 3) ? req[2] : 0x01;
        int fi = 0, k;
        /* 0xFB and 0xFD are reserved mode selectors, not feature indices */
        if (key != 0xFB && key != 0xFD)
            for (k = 0; k < NFEAT_MAX; k++) if (d->fmask[k] == key) fi = k;
        return gen_trace(d, station, fi, out, cap);
    }
    default: return -1;
    }
}

/* ===========================================================================
 * SECTION 5 -- FAULT INJECTION.  Pure: it only rewrites an array of frames.
 * The reader has to survive every one of these; that is why they exist.
 * ========================================================================= */
typedef struct {
    int drop_frame;      /* -1 off, else index of the frame to delete       */
    int bad_ck;
    int bad_seq;
    int dev_error;       /* answer with the device-error frame [00][01]     */
    int dup_frame;
    int junk_prefix;     /* prepend N junk bytes: exercises the front trim   */
    int batch;           /* gateway records per datagram                    */
} fault_cfg;

static int faults_apply(const fault_cfg *fc, can_frame *fr, int n)
{
    int i;
    if (n <= 0) return n;
    if (fc->dev_error) {
        fr[0].data[0] = 0x00; fr[0].data[1] = 0x01; fr[0].len = 2;
        return 1;
    }
    if (fc->bad_seq && n > 1) fr[n / 2].data[0] ^= 0x40;
    if (fc->bad_ck) fr[n - 1].data[fr[n - 1].len - 1] ^= 0xFF;
    if (fc->dup_frame && n > 1 && n < MAX_FRAMES) {
        for (i = n; i > 1; i--) fr[i] = fr[i - 1];
        n++;
    }
    if (fc->drop_frame >= 0 && fc->drop_frame < n) {
        for (i = fc->drop_frame; i < n - 1; i++) fr[i] = fr[i + 1];
        n--;
    }
    return n;
}

/* ===========================================================================
 * SECTION 6 -- I/O BOUNDARY: the capture file
 *   "P3CAP1\0\0" then repeated: [u32 le t_ms][u32 le len][len bytes]
 * promos3_view --replay reads exactly this, so the whole decode path can be
 * developed and regression tested with no machine and no network.
 * ========================================================================= */
static void put_u32le(unsigned char *p, unsigned long v)
{
    p[0] = (unsigned char)(v & 0xFF);
    p[1] = (unsigned char)((v >> 8) & 0xFF);
    p[2] = (unsigned char)((v >> 16) & 0xFF);
    p[3] = (unsigned char)((v >> 24) & 0xFF);
}

static int cap_open(FILE **fp, const char *path)
{
    *fp = fopen(path, "wb");
    if (!*fp) return 0;
    fwrite("P3CAP1\0\0", 1, 8, *fp);
    return 1;
}

static void cap_write(FILE *fp, unsigned long t, const unsigned char *dg, int n)
{
    unsigned char hdr[8];
    if (!fp) return;
    put_u32le(hdr, t);
    put_u32le(hdr + 4, (unsigned long)n);
    fwrite(hdr, 1, 8, fp);
    fwrite(dg, 1, (size_t)n, fp);
}

/* ===========================================================================
 * SECTION 7 -- I/O BOUNDARY: emit frames as datagrams and/or capture rows
 * ========================================================================= */
typedef struct {
    FILE *cap;
    int   verbose;
#ifndef P3_NO_NET
    p3_sock            sock;
    struct sockaddr_in dst;
    int                have_dst;
#endif
    long dg_out, rec_out, bytes_out;
    unsigned long vclock;    /* file-only mode: a virtual clock, so that two
                              * captures of the same run compare byte for byte */
    int           live;      /* 1 = there is a socket, use the wall clock     */
} sink_ctx;

static void sink_send(sink_ctx *snk, const fault_cfg *fc,
                      const can_frame *fr, int n)
{
    unsigned char dg[GW_REC * 64 + 64];
    int i = 0;
    int per = fc->batch > 0 ? fc->batch : 8;
    if (per > 64) per = 64;
    while (i < n) {
        int k = 0, off = 0, j;
        if (fc->junk_prefix > 0) {                /* exercise the front trim */
            int jp = fc->junk_prefix > 35 ? 35 : fc->junk_prefix;
            for (j = 0; j < jp; j++) dg[off++] = (unsigned char)(0xA0 + j);
        }
        while (k < per && i < n) {
            gw_write(dg + off, fr[i].id, fr[i].len, fr[i].data);
            off += GW_REC; i++; k++;
        }
        snk->dg_out++; snk->rec_out += k; snk->bytes_out += off;
        cap_write(snk->cap, snk->live ? now_ms() : (snk->vclock += 3),
                  dg, off);
#ifndef P3_NO_NET
        if (snk->have_dst && snk->sock != P3_BADSOCK)
            sendto(snk->sock, (const char *)dg, off, 0,
                   (struct sockaddr *)&snk->dst, (p3_socklen)sizeof snk->dst);
#endif
        if (snk->verbose) printf("      datagram: %d bytes, %d records\n", off, k);
    }
}

/* ===========================================================================
 * SECTION 8 -- the device also has to UN-frame what the app sends it
 *
 * First frame is [00][00][00][payload...]; a length below 8 means the request
 * is complete, and every read-only poll request is 2..6 bytes, i.e. one frame.
 * A full first frame means a long SET.. request follows, and for those we use
 * the request-length table. A wrong guess there costs an answer, never data
 * corruption: the requester simply times out, exactly like the real unit.
 * ========================================================================= */
#ifndef P3_NO_NET
typedef struct {
    unsigned char buf[64];
    int n, want, active, next_seq;
} req_asm;

static int req_feed(req_asm *ra, const can_frame *f)
{
    int chunk;
    if (!ra->active) {
        const cmd_desc *cd;
        if (f->len < 4) return 0;                       /* not a first frame */
        chunk = f->len - 3;
        memcpy(ra->buf, f->data + 3, (size_t)chunk);
        ra->n = chunk; ra->next_seq = 1; ra->active = 1;
        cd = cmd_find(ra->buf[0]);
        ra->want = cd ? cd->req_len : chunk;
        if (f->len < 8 || ra->n >= ra->want) { ra->active = 0; return 1; }
        return 0;
    }
    if (f->data[0] != (unsigned char)ra->next_seq) { ra->active = 0; return -1; }
    chunk = f->len - 1;
    if (chunk < 0 || ra->n + chunk > (int)sizeof ra->buf) { ra->active = 0; return -1; }
    memcpy(ra->buf + ra->n, f->data + 1, (size_t)chunk);
    ra->n += chunk; ra->next_seq++;
    if (ra->n >= ra->want) { ra->active = 0; return 1; }
    return 0;
}
#endif /* P3_NO_NET */

/* ===========================================================================
 * SECTION 9 -- self test.  Runs the pure layer against the only real protocol
 * bytes we have. --selftest needs no machine, no network and no arguments.
 * ========================================================================= */
static int expect(int cond, const char *what)
{
    printf("  %-58s %s\n", what, cond ? "ok" : "FAIL");
    return cond ? 0 : 1;
}

static int self_test(void)
{
    unsigned char req[8], pay[MAX_MSG], rec[GW_REC];
    can_frame fr[MAX_FRAMES], f;
    int bad = 0, n, nf;
    sim_dev d;

    printf("self test\n");

    /* the one request whose bytes are known from the app's own log */
    n = mc_canonical_request(0x08, 1, 1, req, sizeof req);
    bad += expect(n == 3 && req[0] == 0x08 && req[1] == 0x01 && req[2] == 0xF6,
                  "request 0x08 unit 1 encodes to 08 01 f6");
    bad += expect(p3_ck_request(2, req, 2) == 0xF5 &&
                  p3_ck_request(3, req, 2) == 0xF4,
                  "same request on units 2 and 3 gives f5 / f4");

    /* the gateway record shape */
    gw_write(rec, BASE_CAN_ID + 1, 6, req);
    bad += expect(rec[0] == 0x00 && rec[1] == 0x24 && rec[2] == 0x00 && rec[3] == 0x80,
                  "gateway record header is 00 24 00 80");
    bad += expect(rec[GW_OFF_ID_HI] == 0x05 && rec[GW_OFF_ID_LO] == 0x01,
                  "unit 1 transmits on CAN id 0x501 (big endian)");
    bad += expect(gw_read(rec, &f) && f.id == 1281 && f.len == 6,
                  "record decodes back to the same frame");

    /* framing: not a multiple of 7 -> checksum rides the last data frame */
    memset(pay, 0xAB, 20);
    nf = mc_frame_answer(pay, 20, 0x5A, 1281, fr, MAX_FRAMES);
    bad += expect(nf == 3 && fr[2].len == 8 && fr[2].data[fr[2].len - 1] == 0x5A,
                  "20-byte answer = 3 frames, checksum in the last one");
    /* framing: exact multiple of 7 -> the checksum needs its own frame */
    nf = mc_frame_answer(pay, 14, 0x5A, 1281, fr, MAX_FRAMES);
    bad += expect(nf == 3 && fr[2].len == 2 && fr[2].data[1] == 0x5A,
                  "14-byte answer needs a separate [seq][ck] frame");
    /* the pure acknowledgement */
    nf = mc_frame_answer(pay, 0, 0x5A, 1281, fr, MAX_FRAMES);
    bad += expect(nf == 1 && fr[0].len == 2 && fr[0].data[1] == 0x5A,
                  "zero-length answer is one frame whose DATA[1] is the ck");

    /* the 64-byte message that used to corrupt the old transport */
    nf = mc_frame_answer(pay, 64, 0x11, 1281, fr, MAX_FRAMES);
    bad += expect(nf == 10 && fr[9].len == 3, "64-byte answer completes exactly");

    /* device model */
    dev_init(&d, 1, 1);
    n = gen_kanal(&d, pay, sizeof pay);
    bad += expect(n == 144 && pay[0x4D] == 0x01 &&
                  memcmp(pay + 0x4E, "VIBRATION", 9) == 0,
                  "SKanalRecV40 carries mask 0x01 VIBRATION at +0x4D");
    n = gen_merkmale(&d, 3, pay, sizeof pay);
    bad += expect(n == 3 * (4 * 2 + 2) + 1, "0x16 block is rows*stride+1 bytes");
    n = gen_trace(&d, 1, 1, pay, sizeof pay);
    bad += expect(n == 257, "0x1b trace is 257 bytes");

    /* checksum spans both directions */
    n = mc_canonical_request(0x0e, 1, 1, req, sizeof req);
    { unsigned char body[4]; int i;
      for (i = 0; i < 4; i++) body[i] = (unsigned char)(i + 1);
      bad += expect(p3_checksum(1, req, n, body, 4) ==
                    (unsigned char)(-(1 + req[0] + req[1] + 1 + 2 + 3 + 4)),
                    "answer checksum = -(unit + request-without-ck + payload)"); }

    printf("%s\n", bad ? "SELF TEST FAILED" : "all good");
    return bad ? 1 : 0;
}

/* ===========================================================================
 * SECTION 10 -- main
 * ========================================================================= */
static void usage(void)
{
    printf(
"promos3_sim - synthetic PROVIS3 / Promos3 MC_ unit + CAN-over-UDP gateway\n"
"\n"
"MODES\n"
"  --selftest            check the protocol core against the known real bytes\n"
"  --serve               bind a UDP port and answer requests like the unit\n"
"                        does. This is the default.\n"
"  --stream HOST:PORT    no requests needed: push the whole poll set at a\n"
"                        listener every --period ms\n"
"  --out FILE.cap        also write every datagram to a capture file that\n"
"                        promos3_view --replay can read\n"
"\n"
"OPTIONS\n"
"  --port N              port to bind in --serve mode        (default 1789)\n"
"  --units 1,2           unit ids to simulate                (default 1)\n"
"  --rows N              measurement rows per 0x16 answer    (default 3)\n"
"  --period MS           --stream cycle period               (default 250)\n"
"  --cycles N            stop after N cycles, 0 = forever    (default 0)\n"
"  --latency MS          answer delay, like a real unit      (default 3)\n"
"  --batch N             gateway records per datagram        (default 8)\n"
"  --seed N              PRNG seed; runs are reproducible    (default 1)\n"
"  --lax                 answer even when the request checksum is wrong\n"
"  --quiet / --verbose   less / more logging\n"
"\n"
"FAULT INJECTION - the reader has to survive all of these\n"
"  --fault badck         corrupt the answer checksum\n"
"  --fault badseq        corrupt a sequence number\n"
"  --fault drop=N        delete frame N of every answer\n"
"  --fault dup           duplicate a frame\n"
"  --fault deverr        reply with the device-error frame [00][01]\n"
"  --fault junk=N        prepend N junk bytes to every datagram\n"
"\n"
"EXAMPLES\n"
"  promos3_sim --selftest\n"
"  promos3_sim --serve --verbose\n"
"  promos3_sim --stream 127.0.0.1:1789 --period 200\n"
"  promos3_sim --out shift.cap --stream 127.0.0.1:9 --cycles 20\n"
"\n"
"NOTE  On the MC_ wire an answer carries no command and no length; it is only\n"
"      identifiable next to the request it answers. --stream therefore emits\n"
"      the canonical poll requests' answers in a fixed order, and the reader\n"
"      needs --assume to label them.\n");
}

typedef struct {
    int serve, port, rows, period, cycles, latency, verbose, quiet, lax;
    int unit_ids[MAX_UNITS], unit_n;
    unsigned seed;
    const char *out_path;
    const char *stream_target;
    fault_cfg fc;
} sim_cfg;

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

int main(int argc, char **argv)
{
    static const int POLL[] = { 0x06, 0x0e, 0x16, 0x08, 0x01, 0x1b };
    static unsigned char payload[MAX_MSG];
    static can_frame frames[MAX_FRAMES];
    sim_cfg cfg;
    sim_dev devs[MAX_UNITS];
    sink_ctx snk;
    fault_cfg *fc;
    int i, u;

    memset(&cfg, 0, sizeof cfg);
    memset(&snk, 0, sizeof snk);
    cfg.serve = 1; cfg.port = GW_PORT; cfg.rows = 3; cfg.period = 250;
    cfg.latency = 3; cfg.seed = 1;
    cfg.fc.batch = 8; cfg.fc.drop_frame = -1;
    cfg.unit_ids[0] = 1; cfg.unit_n = 1;
    fc = &cfg.fc;
    setvbuf(stdout, NULL, _IOLBF, 0);

    for (i = 1; i < argc; i++) {
        const char *a = argv[i];
        if      (!strcmp(a, "--help") || !strcmp(a, "-h")) { usage(); return 0; }
        else if (!strcmp(a, "--selftest")) return self_test();
        else if (!strcmp(a, "--serve"))    cfg.serve = 1;
        else if (!strcmp(a, "--verbose"))  cfg.verbose = 1;
        else if (!strcmp(a, "--quiet"))    cfg.quiet = 1;
        else if (!strcmp(a, "--lax"))      cfg.lax = 1;
        else if (!strcmp(a, "--port")    && i+1 < argc) cfg.port    = atoi(argv[++i]);
        else if (!strcmp(a, "--rows")    && i+1 < argc) cfg.rows    = atoi(argv[++i]);
        else if (!strcmp(a, "--period")  && i+1 < argc) cfg.period  = atoi(argv[++i]);
        else if (!strcmp(a, "--cycles")  && i+1 < argc) cfg.cycles  = atoi(argv[++i]);
        else if (!strcmp(a, "--latency") && i+1 < argc) cfg.latency = atoi(argv[++i]);
        else if (!strcmp(a, "--batch")   && i+1 < argc) fc->batch   = atoi(argv[++i]);
        else if (!strcmp(a, "--seed")    && i+1 < argc)
            cfg.seed = (unsigned)strtoul(argv[++i], NULL, 0);
        else if (!strcmp(a, "--out")     && i+1 < argc) cfg.out_path = argv[++i];
        else if (!strcmp(a, "--stream")  && i+1 < argc) {
            cfg.stream_target = argv[++i]; cfg.serve = 0;
        }
        else if (!strcmp(a, "--units")   && i+1 < argc) {
            const char *p = argv[++i];
            cfg.unit_n = 0;
            while (*p && cfg.unit_n < MAX_UNITS) {
                int v = atoi(p);
                if (v >= 1 && v < MAX_UNITS) cfg.unit_ids[cfg.unit_n++] = v;
                while (*p && *p != ',') p++;
                if (*p == ',') p++;
            }
            if (cfg.unit_n == 0) { cfg.unit_ids[0] = 1; cfg.unit_n = 1; }
        }
        else if (!strcmp(a, "--fault") && i+1 < argc) {
            const char *v = argv[++i];
            if      (!strcmp(v, "badck"))     fc->bad_ck    = 1;
            else if (!strcmp(v, "badseq"))    fc->bad_seq   = 1;
            else if (!strcmp(v, "dup"))       fc->dup_frame = 1;
            else if (!strcmp(v, "deverr"))    fc->dev_error = 1;
            else if (!strncmp(v, "drop=", 5)) fc->drop_frame  = atoi(v + 5);
            else if (!strncmp(v, "junk=", 5)) fc->junk_prefix = atoi(v + 5);
            else { fprintf(stderr, "unknown fault: %s\n", v); return 2; }
        }
        else { fprintf(stderr, "unknown argument: %s  (try --help)\n", a); return 2; }
    }

    for (u = 0; u < cfg.unit_n; u++)
        dev_init(&devs[u], cfg.unit_ids[u], cfg.seed + (unsigned)u * 7919u);

    if (cfg.out_path) {
        if (!cap_open(&snk.cap, cfg.out_path)) {
            fprintf(stderr, "cannot write %s\n", cfg.out_path);
            return 1;
        }
        printf("capture   : %s\n", cfg.out_path);
    }
    snk.verbose = cfg.verbose;
    signal(SIGINT, on_sigint);

#ifdef P3_NO_NET
    if (!cfg.out_path) {
        fprintf(stderr,
                "built with -DP3_NO_NET: only --out FILE.cap is available\n");
        return 2;
    }
    cfg.serve = 0;
    if (cfg.cycles <= 0) cfg.cycles = 10;
#else
    {
#  ifdef _WIN32
        WSADATA wsa;
        if (WSAStartup(MAKEWORD(2, 2), &wsa) != 0) {
            fprintf(stderr, "WSAStartup failed\n");
            return 1;
        }
#  endif
        snk.sock = socket(AF_INET, SOCK_DGRAM, 0);
        if (snk.sock == P3_BADSOCK) { fprintf(stderr, "socket() failed\n"); return 1; }
        if (cfg.serve) {
            struct sockaddr_in a;
            int one = 1;
            setsockopt(snk.sock, SOL_SOCKET, SO_REUSEADDR,
                       (const char *)&one, sizeof one);
            memset(&a, 0, sizeof a);
            a.sin_family = AF_INET;
            a.sin_addr.s_addr = htonl(INADDR_ANY);
            a.sin_port = htons((unsigned short)cfg.port);
            if (bind(snk.sock, (struct sockaddr *)&a, sizeof a) != 0) {
                fprintf(stderr, "bind :%d failed - port in use?\n", cfg.port);
                return 1;
            }
            printf("serving   : UDP :%d   units", cfg.port);
            for (u = 0; u < cfg.unit_n; u++) printf(" %d", cfg.unit_ids[u]);
            printf("   CAN ids");
            for (u = 0; u < cfg.unit_n; u++)
                printf(" 0x%03X", BASE_CAN_ID + cfg.unit_ids[u]);
            printf("\n");
        }
        if (cfg.stream_target) {
            char host[64];
            int p = 0;
            if (!parse_hostport(cfg.stream_target, host, (int)sizeof host, &p)) {
                fprintf(stderr, "--stream expects HOST:PORT\n");
                return 2;
            }
            memset(&snk.dst, 0, sizeof snk.dst);
            snk.dst.sin_family = AF_INET;
            snk.dst.sin_port = htons((unsigned short)p);
            snk.dst.sin_addr.s_addr = inet_addr(host);  /* portable everywhere */
            if (snk.dst.sin_addr.s_addr == INADDR_NONE) {
                fprintf(stderr, "--stream: bad address %s (use a numeric IP)\n", host);
                return 2;
            }
            snk.have_dst = 1; snk.live = 1;
            printf("streaming : -> %s:%d every %d ms\n", host, p, cfg.period);
        }
    }
#endif

    /* ---------------- push / capture mode -------------------------------- */
    if (!cfg.serve) {
        int cyc = 0;
        printf("mode      : push (nobody asked). MC_ answers are anonymous on\n"
               "            the wire, so the reader needs --assume to label them.\n");
        while (!g_stop && (cfg.cycles <= 0 || cyc < cfg.cycles)) {
            int k;
            for (u = 0; u < cfg.unit_n && !g_stop; u++) {
                for (k = 0; k < (int)(sizeof POLL / sizeof POLL[0]); k++) {
                    unsigned char req[8];
                    unsigned char ck;
                    int rn, pn, nf;
                    const cmd_desc *cd = cmd_find(POLL[k]);
                    if (!cd) continue;
                    rn = mc_canonical_request(POLL[k], devs[u].unit, 1, req, sizeof req);
                    if (rn < 0) continue;
                    pn = dev_answer(&devs[u], req, rn, cfg.rows, payload, MAX_MSG);
                    if (pn < 0) continue;
                    ck = p3_checksum(devs[u].unit, req, rn, payload, pn);
                    nf = mc_frame_answer(payload, pn, ck,
                                         BASE_CAN_ID + devs[u].unit,
                                         frames, MAX_FRAMES);
                    if (nf < 0) continue;
                    nf = faults_apply(fc, frames, nf);
                    if (!cfg.quiet)
                        printf("unit %d  %-22s payload %3d  frames %3d  ck %02x\n",
                               devs[u].unit, cd->name, pn, nf, ck);
                    sink_send(&snk, fc, frames, nf);
                }
            }
            cyc++;
            if (cfg.period > 0 && (cfg.cycles <= 0 || cyc < cfg.cycles))
                sleep_ms(cfg.period);
        }
        printf("done      : %ld datagrams, %ld records, %ld bytes\n",
               snk.dg_out, snk.rec_out, snk.bytes_out);
        if (snk.cap) fclose(snk.cap);
#ifndef P3_NO_NET
        if (snk.sock != P3_BADSOCK) p3_closesock(snk.sock);
#  ifdef _WIN32
        WSACleanup();
#  endif
#endif
        return 0;
    }

#ifndef P3_NO_NET
    /* ---------------- serve mode: behave like the unit ------------------- */
    {
        static unsigned char dg[65536];
        req_asm asmb[MAX_UNITS];
        long served = 0, ignored = 0;
        memset(asmb, 0, sizeof asmb);

        while (!g_stop) {
            struct sockaddr_in from;
            p3_socklen fl = (p3_socklen)sizeof from;
            fd_set rd;
            struct timeval tv;
            int n, off;

            FD_ZERO(&rd);
            FD_SET(snk.sock, &rd);
            tv.tv_sec = 0; tv.tv_usec = 100000;       /* 100 ms: Ctrl-C works */
            if (select((int)snk.sock + 1, &rd, NULL, NULL, &tv) <= 0) continue;

            n = (int)recvfrom(snk.sock, (char *)dg, (int)sizeof dg, 0,
                              (struct sockaddr *)&from, &fl);
            if (n <= 0) continue;
            snk.dst = from; snk.have_dst = 1; snk.live = 1;  /* answer where it came from */

            /* Scan4CANmsg: 36-byte records, the remainder trimmed from the FRONT */
            for (off = n % GW_REC; off + GW_REC <= n; off += GW_REC) {
                can_frame f;
                req_asm *ra;
                const cmd_desc *cd;
                unsigned char want_ck, ck;
                int unit, idx = -1, done, pn, nf;

                if (!gw_read(dg + off, &f)) continue;
                unit = f.id - BASE_CAN_ID;
                if (unit < 1 || unit >= MAX_UNITS) continue;
                for (u = 0; u < cfg.unit_n; u++)
                    if (cfg.unit_ids[u] == unit) idx = u;
                if (idx < 0) continue;                 /* not one of our units */

                done = req_feed(&asmb[unit], &f);
                if (done <= 0) continue;

                ra = &asmb[unit];
                cd = cmd_find(ra->buf[0]);
                want_ck = p3_ck_request(unit, ra->buf, ra->n - 1);
                if (cfg.verbose) {
                    int b;
                    printf("unit %d  request:", unit);
                    for (b = 0; b < ra->n; b++) printf(" %02x", ra->buf[b]);
                    printf("\n");
                }
                if (!cd) {
                    printf("unit %d  cmd 0x%02x not simulated - silent, like the "
                           "real unit would be\n", unit, ra->buf[0]);
                    ignored++; ra->n = 0; continue;
                }
                if (ra->n < 2 || (want_ck != ra->buf[ra->n - 1] && !cfg.lax)) {
                    printf("unit %d  %s: BAD REQUEST CHECKSUM (got %02x want %02x)"
                           " - staying silent\n", unit, cd->name,
                           ra->n ? ra->buf[ra->n - 1] : 0, want_ck);
                    ignored++; ra->n = 0; continue;
                }
                pn = dev_answer(&devs[idx], ra->buf, ra->n, cfg.rows,
                                payload, MAX_MSG);
                if (pn < 0) { ignored++; ra->n = 0; continue; }
                ck = p3_checksum(unit, ra->buf, ra->n, payload, pn);
                nf = mc_frame_answer(payload, pn, ck, BASE_CAN_ID + unit,
                                     frames, MAX_FRAMES);
                if (nf < 0) { ra->n = 0; continue; }
                nf = faults_apply(fc, frames, nf);
                if (cfg.latency > 0) sleep_ms(cfg.latency);
                if (!cfg.quiet)
                    printf("unit %d  %-22s -> %3d payload bytes, %3d frames, ck %02x\n",
                           unit, cd->name, pn, nf, ck);
                sink_send(&snk, fc, frames, nf);
                served++;
                ra->n = 0;
            }
        }
        printf("\nserved %ld requests, ignored %ld, sent %ld datagrams / %ld bytes\n",
               served, ignored, snk.dg_out, snk.bytes_out);
        if (snk.cap) fclose(snk.cap);
        if (snk.sock != P3_BADSOCK) p3_closesock(snk.sock);
#  ifdef _WIN32
        WSACleanup();
#  endif
    }
#endif
    return 0;
}

/* mc_frame_request is used by promos3_view; kept here so both programs carry
 * one identical definition of the request framing. Referencing it once keeps
 * -Wunused-function quiet without hiding it behind an #ifdef. */
int  p3_sim_frame_request_ref(const unsigned char *m, int n, int id,
                              can_frame *o, int max);
int  p3_sim_frame_request_ref(const unsigned char *m, int n, int id,
                              can_frame *o, int max)
{
    return mc_frame_request(m, n, id, o, max);
}
