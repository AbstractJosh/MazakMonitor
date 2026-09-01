/* promos3_decode.c — message header parse + body decoders + printing.
 * Bodies from report Part 4; header offsets are the second calibration hook. */
#include "promos3.h"
#include "promos3_state.h"
#include <stdio.h>
#include <string.h>

/* little-endian readers over a bounds-checked cursor */
static uint16_t rd_u16(const uint8_t *p) { return (uint16_t)(p[0] | (p[1] << 8)); }

/* >>> CALIBRATE (PHASE 0) <<<
 * Split a reassembled message into (group, command, body).
 *
 * KNOWN (report 2.4): in the parsed object, group is at +0x00 and command at
 * +0x28 (both u32). Those are OBJECT offsets; the raw ON-WIRE positions are
 * not yet confirmed. The layout below is a best-guess starter that assumes the
 * wire header begins with a small [group][command][len] preamble. Use the
 * MC_GIVEKONFIG anchor (decodes to "Version 229 Channels 1 Sensors 4") in your
 * first capture to fix these offsets, then this is the ONLY function to edit.
 *
 * Starter assumption (EDIT ME):
 *   +0x00  u8   group       (0/1/2)
 *   +0x01  u8   command
 *   +0x02  u16  body_len (LE)
 *   +0x04  body[...]
 */
bool parse_message_header(int unit, const uint8_t *buf, size_t len, promos3_msg_t *out) {
    if (len < 4) return false;
    uint8_t  g   = buf[0x00];
    uint8_t  cmd = buf[0x01];
    uint16_t blen = rd_u16(buf + 0x02);

    if (g > GROUP_MC3) return false;                 /* sanity gate         */
    size_t avail = len - 4;
    if (blen > avail) blen = (uint16_t)avail;        /* clamp to what we got */

    out->unit     = unit;
    out->group    = (promos3_group_t)g;
    out->command  = cmd;
    out->body     = buf + 4;
    out->body_len = blen;
    return true;
}

/* ---- SIGNALVERLAUF: 125 x int16 LE amplitude (report 4.1) ------------- *
 * This is the solid one for an MC_ box (shared decodeSignalTrace_B path).
 * Body: toolKey, channelKey, paramA, flag, mode, then samples[125], trailer. */
bool decode_signalverlauf(const promos3_msg_t *m, signalverlauf_t *sv) {
    const uint8_t *b = m->body;
    if (m->body_len < 5 + 2) return false;
    sv->tool_key = b[0]; sv->channel_key = b[1]; sv->param_a = b[2];
    sv->flag = b[3]; sv->mode = b[4];

    const uint8_t *p = b + 5;
    size_t remain = m->body_len - 5;
    int n = 0;
    sv->vmin = 32767; sv->vmax = -32768;
    while (n < SV_SAMPLES && remain >= 2) {
        int16_t v = (int16_t)rd_u16(p);
        sv->samples[n++] = v;
        if (v < sv->vmin) sv->vmin = v;
        if (v > sv->vmax) sv->vmax = v;
        p += 2; remain -= 2;
    }
    sv->sample_count = n;
    if (n == 0) { sv->vmin = sv->vmax = 0; }
    return n > 0;
}

/* ---- KONFIG summary (from MC_GIVEKONFIG log line) --------------------- *
 * NOTE: field offsets are a best guess (the log prints Version/Channels/
 * Sensors; exact body layout not in the report). Verify against a capture. */
bool decode_konfig(const promos3_msg_t *m, konfig_t *k) {
    if (m->body_len < 4) return false;
    k->version  = rd_u16(m->body + 0);   /* EDIT ME if it's a u8            */
    k->channels = m->body[2];
    k->sensors  = m->body[3];
    return true;
}

/* ---- ALARM entries (report 4.2) --------------------------------------- *
 * subcommand u8, u16 alarmId, then [u16 alarmNumber][31-byte record].
 * (MC3_-derived layout; confirm the MC_ variant against a capture.) */
int decode_alarms(const promos3_msg_t *m, alarm_entry_t *out, int max) {
    const uint8_t *b = m->body;
    size_t len = m->body_len;
    if (len < 3) return 0;
    size_t off = 1 + 2;                 /* skip subcommand + alarmId          */
    int n = 0;
    while (n < max && off + 2 + 31 <= len) {
        const uint8_t *e = b + off;
        out[n].alarm_number = rd_u16(e);
        const uint8_t *rec  = e + 2;
        out[n].entry_id     = rd_u16(rec + 0x00);
        out[n].status       = rd_u16(rec + 0x02);
        out[n].channel_key  = rec[0x1D];
        n++;
        off += 2 + 31;
    }
    return n;
}

/* ------------------------------- printing ------------------------------ */
void hexdump(const uint8_t *p, size_t n) {
    for (size_t i = 0; i < n; i++) {
        printf("%02x ", p[i]);
        if ((i & 0x0F) == 0x0F) printf("\n                 ");
    }
    printf("\n");
}

void print_can_frame(const can_frame_t *f) {
    printf("unit=%-3d id=0x%03X len=%u  data=", f->unit, f->can_id, f->len);
    for (int i = 0; i < f->len; i++) printf("%02x ", f->data[i]);
    printf("\n");
}

static const char *conf_tag(cmd_conf_t c) {
    switch (c) {
        case CONF_CONFIRMED:   return "confirmed";
        case CONF_PROVISIONAL: return "provisional";
        case CONF_NAMED:       return "named";
        default:               return "unknown";
    }
}

static void print_raw_indented(const uint8_t *p, size_t n) {
    size_t show = n < 32 ? n : 32;
    printf("                 ");
    hexdump(p, show);
    if (n > show) printf("                 ... (%zu bytes total)\n", n);
}

/* Every path here ends in a defined, honest line. We never printf a decoded
 * value whose byte layout is unconfirmed, and we never silently drop a
 * message the reassembler completed. */
void print_message(const promos3_msg_t *m, const struct reader_state *st) {
    if (!m->parsed) {                                          /* surfaced, not dropped */
        printf("Unit %-3d | [UNPARSED HEADER] raw %zu bytes\n", m->unit, m->raw_len);
        print_raw_indented(m->raw, m->raw_len);
        return;
    }

    const char *name = cmd_name(m->group, m->command);
    cmd_conf_t  conf = cmd_confidence(m->group, m->command);
    printf("Unit %-3d | %-24s | len %zu | %s\n", m->unit, name, m->body_len, conf_tag(conf));

    switch (conf) {
    case CONF_CONFIRMED: {                                     /* MC_ trace 0x1B */
        signalverlauf_t sv;
        if (decode_signalverlauf(m, &sv))
            printf("         | %s | %d samples  raw %d..%d (0..255, no scaling)\n",
                   reader_feature_name(st, m->unit, sv.channel_key),
                   sv.sample_count, sv.vmin, sv.vmax);
        else
            printf("         | [body too short to decode: %zu bytes]\n", m->body_len);
        break;
    }
    case CONF_PROVISIONAL:                                     /* layout unconfirmed */
        /* Deliberately NOT decoded to fields — show raw so we never present a
         * guessed offset as fact. Promote to CONFIRMED after Phase 0. */
        if (m->body_len) print_raw_indented(m->body, m->body_len);
        else             printf("         | (empty body)\n");
        break;

    case CONF_NAMED:
    case CONF_UNKNOWN:
    default:
        if (m->body_len) print_raw_indented(m->body, m->body_len);
        /* empty body: the header line above is the complete, correct output */
        break;
    }
}
