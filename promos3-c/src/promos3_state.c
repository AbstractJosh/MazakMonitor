/* promos3_state.c — transforms over reader_state_t. I/O only in save/load. */
#include "promos3_state.h"
#include <stdio.h>
#include <string.h>

void reader_state_init(reader_state_t *st) {
    memset(st, 0, sizeof *st);
    st->magic   = STATE_MAGIC;
    st->version = STATE_VERSION;
    st->size    = (uint32_t)sizeof *st;
}

bool reader_state_save(const char *path, const reader_state_t *st) {
    FILE *fp = fopen(path, "wb");
    if (!fp) return false;
    size_t w = fwrite(st, 1, sizeof *st, fp);
    fclose(fp);
    return w == sizeof *st;
}

bool reader_state_load(const char *path, reader_state_t *st) {
    FILE *fp = fopen(path, "rb");
    if (!fp) return false;
    reader_state_t tmp;
    size_t r = fread(&tmp, 1, sizeof tmp, fp);
    fclose(fp);
    if (r != sizeof tmp) return false;
    if (tmp.magic != STATE_MAGIC || tmp.version != STATE_VERSION
        || tmp.size != (uint32_t)sizeof tmp) return false;   /* reject foreign */
    *st = tmp;
    return true;
}

bool reader_apply_pmd(reader_state_t *st, int unit, const char *pmd_path) {
    pmd_file_t f;
    if (!pmd_load_path(pmd_path, &f)) return false;
    geraet_t g = parse_geraet(pmd_block(&f, "SGeraetRec", 0));
    kanal_t  k = parse_kanal (pmd_block(&f, "SKanalRecV40", 0));
    if (!g.ok && !k.ok) return false;

    int lo = (unit < 0) ? 0 : unit;
    int hi = (unit < 0) ? MAX_UNITS : unit + 1;
    if (lo < 0 || hi > MAX_UNITS) return false;
    for (int u = lo; u < hi; u++) {
        st->units[u].configured = true;
        st->units[u].geraet = g;
        st->units[u].kanal  = k;
    }
    return true;
}

/* Map a SIGNALVERLAUF channel key (or feature mask) to a 0..3 feature index.
 * Handles the low-bit form (1/2/4/8) AND the high-bit/flag form (0x81/0x82/
 * 0x84/0x88) by stripping the 0x80 flag; falls back to index form (0..3).
 * Returns -1 if it fits neither (caller then shows the raw key). */
static int key_to_index(unsigned key) {
    switch (key & 0x7F) {                    /* drop the 0x80 flag bit        */
        case 1: return 0; case 2: return 1; case 4: return 2; case 8: return 3;
    }
    return (key < 4) ? (int)key : -1;        /* index form                    */
}

void reader_state_update(reader_state_t *st, const promos3_msg_t *m) {
    if (m->unit < 0 || m->unit >= MAX_UNITS) return;
    unit_state_t *u = &st->units[m->unit];
    u->msg_count++;

    if (!m->parsed) { u->unparsed_count++; return; }

    if (m->group == GROUP_MC && m->command == 0x1B) {          /* trace       */
        signalverlauf_t sv;
        if (decode_signalverlauf(m, &sv)) {
            int idx = key_to_index(sv.channel_key);
            if (idx >= 0) {
                u->trace[idx].valid = true;
                u->trace[idx].vmin  = sv.vmin;
                u->trace[idx].vmax  = sv.vmax;
                u->trace[idx].count = sv.sample_count;
            }
        }
    } else if (m->group == GROUP_MC3 && m->command == 0x0F) {   /* alarm       */
        u->alarm_count++;
    }
    /* KONFIG (0x06) intentionally NOT stored as decoded values while its wire
     * layout is unconfirmed (Phase 0). Promote here once calibrated. */
}

const char *reader_feature_name(const reader_state_t *st, int unit, unsigned key) {
    static char buf[24];
    int idx = key_to_index(key);
    if (idx >= 0 && unit >= 0 && unit < MAX_UNITS
        && st->units[unit].configured
        && st->units[unit].kanal.features[idx].present) {
        return st->units[unit].kanal.features[idx].name;   /* from config     */
    }
    if (idx >= 0) return feature_name(idx);                 /* built-in fallback */
    snprintf(buf, sizeof buf, "feat[key=0x%02X]", key);     /* unmappable key   */
    return buf;
}

void reader_state_dump(const reader_state_t *st) {
    int configured = 0, active = 0;
    for (int u = 0; u < MAX_UNITS; u++) {
        if (st->units[u].configured) configured++;
        if (st->units[u].msg_count)  active++;
    }
    printf("== reader state ==  configured units: %d   active units: %d\n", configured, active);

    for (int u = 0; u < MAX_UNITS; u++) {
        const unit_state_t *s = &st->units[u];
        if (s->msg_count == 0) continue;                 /* detail active units only */
        printf("unit %d: msgs %u  unparsed %u  alarms %u\n",
               u, s->msg_count, s->unparsed_count, s->alarm_count);
        if (s->configured)
            for (int i = 0; i < 4; i++)
                if (s->kanal.features[i].present) {
                    const char *nm = s->kanal.features[i].name;
                    if (s->trace[i].valid)
                        printf("   feature[%d] \"%s\"  last trace %d..%d (%d samples)\n",
                               i, nm, s->trace[i].vmin, s->trace[i].vmax, s->trace[i].count);
                    else
                        printf("   feature[%d] \"%s\"  (no trace yet)\n", i, nm);
                }
    }
}
