/* promos3.h — Prometec PROVIS3 monitoring reader (read-only observer)
 *
 * Reconstructed from the PROVIS3 RE report (v2). This is a CLEAN-ROOM
 * reimplementation from the byte-level spec — NOT pasted decompiler output.
 *
 * Scope: the Prometec CAN-over-UDP receive path only (device -> app).
 * Target box is a Provis2 / legacy "MC_" unit (dispatch group 1).
 *
 * Two things in this codebase are marked  >>> CALIBRATE (PHASE 0) <<<  because
 * they depend on seeing one real capture:
 *   1) reasm_expected_len()      — where the total length lives in the stream
 *   2) parse_message_header()    — where group/command/length sit on the wire
 * Everything else (record split, CAN-ID, unit routing, enums, body decoders,
 * printing) is derived directly from verified findings and works now.
 */
#ifndef PROMOS3_H
#define PROMOS3_H

#include <stdint.h>
#include <stddef.h>
#include <stdbool.h>

/* ------------------------------------------------------------------ */
/* Transport constants (PROVISsettings.ini [CAN])                     */
/* ------------------------------------------------------------------ */
#define PROMOS3_UDP_PORT        1789      /* GatewayPort                     */
#define PROMOS3_BASE_CAN_ID     1280      /* BaseCanIDTransfer               */
#define GW_RECORD_SIZE          0x24      /* 36 bytes per gateway CAN record */
#define CAN_MAX_DATA            8
#define REASM_MAX_MSG           4096      /* max reassembled Promos3 message */
#define MAX_UNITS               16        /* FirstDevice..LastDevice = 1..15 */

/* ------------------------------------------------------------------ */
/* Dispatch groups (msg object field @+0x00) and generations          */
/* ------------------------------------------------------------------ */
typedef enum {
    GROUP_HANDSHAKE = 0,   /* MC_GIVEGTYPE etc.            */
    GROUP_MC        = 1,   /* legacy Provis2  (THIS BOX)   */
    GROUP_MC3       = 2    /* modern Promos3              */
} promos3_group_t;

/* getTargetType(): unit generation. This box == 1. */
#define GEN_MC   1
#define GEN_MC3  2

/* ------------------------------------------------------------------ */
/* Decoder rings (report Part 6)                                      */
/* ------------------------------------------------------------------ */
typedef enum {                       /* ToolStatus, status byte 0x00..0x0F  */
    TS_EMPTY=0x0, TS_OVERLOAD, TS_UNDERLOAD, TS_CONTACT, TS_MISSING,
    TS_WORK_OVER, TS_WORK_UNDER, TS_CUT_START, TS_CUT_END, TS_DYN_UPPER,
    TS_DYN_LOWER, TS_PAT_UPPER, TS_PAT_LOWER, TS_ACF_CONTACT, TS_CUTDETECT,
    TS_TOOL_WEAR=0xF
} tool_status_t;

/* One 36-byte gateway record, decoded into a CAN frame. */
typedef struct {
    uint16_t can_id;                 /* (buf[0x1A]<<8)|buf[0x1B]  BIG-ENDIAN */
    uint8_t  len;                    /* buf[0x15], 0..8                      */
    uint8_t  data[CAN_MAX_DATA];     /* buf[0x1C..0x23]                      */
    int      unit;                   /* can_id - BASE_CAN_ID (may be <0)     */
} can_frame_t;

/* Per-unit reassembly buffer. */
typedef struct {
    bool     active;
    uint8_t  buf[REASM_MAX_MSG];
    size_t   len;                    /* bytes accumulated                    */
} unit_reasm_t;

typedef struct {
    unit_reasm_t units[MAX_UNITS];
} reasm_ctx_t;

/* A fully reassembled message. `raw` is ALWAYS valid (points into the unit
 * buffer). If the header parsed, `parsed` is true and group/command/body are
 * set; otherwise the caller still sees the raw bytes and can surface them
 * instead of silently dropping. */
typedef struct {
    int             unit;
    bool            parsed;
    promos3_group_t group;
    uint32_t        command;
    const uint8_t  *raw;             /* full reassembled message              */
    size_t          raw_len;
    const uint8_t  *body;            /* parsed body (valid iff parsed)        */
    size_t          body_len;
} promos3_msg_t;

/* How much we trust a decoder's field layout for a given command. Governs
 * whether print shows decoded values or only a safe raw hexdump — so we never
 * printf a "meaning" whose byte layout is unconfirmed. */
typedef enum {
    CONF_UNKNOWN = 0,   /* no name, no decoder     -> id + hex                */
    CONF_NAMED,         /* known name, no decoder  -> name + hex              */
    CONF_PROVISIONAL,   /* decoder exists, layout unconfirmed -> name + hex   */
    CONF_CONFIRMED      /* decoder + layout confirmed -> show decoded values  */
} cmd_conf_t;

cmd_conf_t cmd_confidence(promos3_group_t group, uint32_t command);
bool       cmd_known(promos3_group_t group, uint32_t command);

/* Decoded SIGNALVERLAUF (report Part 4.1) — THE amplitude trace. */
#define SV_SAMPLES 125
typedef struct {
    uint8_t tool_key, channel_key, param_a, flag, mode;
    int16_t samples[SV_SAMPLES];     /* raw 0..255, NO scaling               */
    int     sample_count;            /* actual decoded (<=125)               */
    int16_t vmin, vmax;
} signalverlauf_t;

/* Decoded ALARM entry (report Part 4.2). */
typedef struct {
    uint16_t alarm_number;
    uint16_t entry_id;
    uint16_t status;                 /* low byte = ToolStatus                */
    uint8_t  channel_key;            /* 0xFF = none                          */
} alarm_entry_t;

/* Decoded KONFIG summary (from MC_GIVEKONFIG log line). */
typedef struct { uint16_t version; uint8_t channels; uint8_t sensors; } konfig_t;

/* ---- proto.c : name / enum lookups ---- */
const char *cmd_name(promos3_group_t group, uint32_t command);
const char *tool_status_name(unsigned s);
const char *sensor_type_name(unsigned t);
const char *alarm_slot_name(unsigned n);      /* [AlarmNames] 1..5          */
const char *feature_name(int index);          /* this box's SKanalRec labels */

/* ---- transport.c : split + routing + reassembly ---- */
int  gw_parse_record(const uint8_t *rec36, can_frame_t *out);
void reasm_init(reasm_ctx_t *ctx);
/* Feed one CAN frame; if it completes a message, returns 1 and fills *out
 * (out->body/body_len point into the unit buffer, valid until next feed). */
int  reasm_feed(reasm_ctx_t *ctx, const can_frame_t *f, promos3_msg_t *out);

/* ---- decode.c : header + bodies + printing ---- */
bool parse_message_header(int unit, const uint8_t *buf, size_t len, promos3_msg_t *out);
bool decode_signalverlauf(const promos3_msg_t *m, signalverlauf_t *sv);
bool decode_konfig(const promos3_msg_t *m, konfig_t *k);
int  decode_alarms(const promos3_msg_t *m, alarm_entry_t *out, int max);

struct reader_state;                                  /* fwd (promos3_state.h) */
void print_can_frame(const can_frame_t *f);          /* RAW mode            */
void print_message(const promos3_msg_t *m, const struct reader_state *st); /* DECODE */
void hexdump(const uint8_t *p, size_t n);

#endif /* PROMOS3_H */
