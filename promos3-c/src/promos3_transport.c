/* promos3_transport.c — split 36-byte records, route by unit, reassemble.
 * Report Part 2 (transport) + Part 8.1/8.2 + Part 9.1.
 *
 * The RECORD SPLIT and CAN-ID/unit routing are fully known and correct.
 * The REASSEMBLY COMPLETION rule depends on the on-wire framing, which is the
 * one thing still to confirm from a capture -> see reasm_expected_len().
 */
#include "promos3.h"
#include <string.h>

/* Decode one 36-byte gateway record into a CAN frame.
 * Layout (report 2.2): +0x15 len, +0x1A..1B CAN-ID (BE), +0x1C..23 data. */
int gw_parse_record(const uint8_t *r, can_frame_t *out) {
    uint8_t len = r[0x15];
    if (len > CAN_MAX_DATA) len = CAN_MAX_DATA;      /* clamp defensively   */
    out->can_id = (uint16_t)((r[0x1A] << 8) | r[0x1B]);   /* BIG-ENDIAN     */
    out->len    = len;
    memcpy(out->data, r + 0x1C, CAN_MAX_DATA);
    out->unit   = (int)out->can_id - PROMOS3_BASE_CAN_ID; /* may be < 0     */
    return 0;
}

void reasm_init(reasm_ctx_t *ctx) { memset(ctx, 0, sizeof *ctx); }

/* >>> CALIBRATE (PHASE 0) <<<
 * Return the expected TOTAL length of the message currently accumulating in
 * this unit buffer, or 0 if "not known yet / keep accumulating".
 *
 * From the report we know a length field governs completion
 * (unitBuffer_hasCompleteMessage), but not its exact byte position in the
 * reassembled stream. Until a capture pins it, we use a safe heuristic:
 * treat a short final CAN frame (len < 8) as the end-of-message marker
 * (a common multi-frame CAN convention). Replace this function once the
 * capture shows the real length field (e.g. a u16 at a fixed offset). */
static size_t reasm_expected_len(const unit_reasm_t *u, const can_frame_t *last) {
    (void)u;
    /* Heuristic default: unknown here; completion decided in reasm_feed()
     * by the short-frame rule below. Return 0 = "use frame-based rule". */
    (void)last;
    return 0;
}

int reasm_feed(reasm_ctx_t *ctx, const can_frame_t *f, promos3_msg_t *out) {
    if (f->unit < 0 || f->unit >= MAX_UNITS) return 0;   /* not a unit ID   */
    unit_reasm_t *u = &ctx->units[f->unit];

    if (!u->active) { u->active = true; u->len = 0; }

    /* append this frame's data bytes */
    size_t take = f->len;
    if (u->len + take > sizeof u->buf) take = sizeof u->buf - u->len; /* guard */
    memcpy(u->buf + u->len, f->data, take);
    u->len += take;

    /* completion test */
    size_t need = reasm_expected_len(u, f);
    bool complete = false;
    if (need > 0) {
        complete = (u->len >= need);
    } else {
        /* frame-based fallback: a short frame ends the message */
        complete = (f->len < CAN_MAX_DATA);
    }

    if (!complete) return 0;

    /* Always emit the completed message. raw/raw_len are always valid; the
     * header parse may fail (out->parsed == false), in which case the caller
     * surfaces the raw bytes instead of dropping them. */
    memset(out, 0, sizeof *out);
    out->unit    = f->unit;
    out->raw     = u->buf;
    out->raw_len = u->len;
    out->parsed  = parse_message_header(f->unit, u->buf, u->len, out);

    u->active = false;                 /* reset buffer for next message      */
    u->len    = 0;
    return 1;                          /* a message completed (parsed or not) */
}
