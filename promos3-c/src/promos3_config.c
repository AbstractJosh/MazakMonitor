/* promos3_config.c — PMD text -> blocks -> typed records.
 *
 * Structure follows the FP boundary discipline:
 *   pmd_load_path   : impure edge (reads a file)         -> calls pmd_load_text
 *   pmd_load_text   : pure transform (text -> blocks)
 *   parse_geraet    : pure (span -> geraet_t)
 *   parse_kanal     : pure (span -> kanal_t)
 * No globals, no shared mutable state. Records are returned by value.
 */
#include "promos3_config.h"
#include <string.h>
#include <ctype.h>
#include <stdlib.h>
#include <stdio.h>

/* ------------------------------ tokenizer ---------------------------------- */

static bool is_hex_byte(const char *t, size_t len) {
    if (len < 1 || len > 2) return false;
    for (size_t i = 0; i < len; i++)
        if (!isxdigit((unsigned char)t[i])) return false;
    return true;
}

bool pmd_load_text(const char *text, size_t n, pmd_file_t *out) {
    memset(out, 0, sizeof *out);
    int cur = -1;                                    /* index of open block     */

    size_t i = 0;
    while (i < n) {
        size_t j = i;                                /* find end of line        */
        while (j < n && text[j] != '\n') j++;
        size_t e = j;
        if (e > i && text[e - 1] == '\r') e--;

        size_t a = i;                                /* trim leading blanks     */
        while (a < e && (text[a] == ' ' || text[a] == '\t')) a++;

        if (a < e && text[a] == ';') {               /* ---- new named block    */
            a++;
            while (a < e && (text[a] == ' ' || text[a] == '\t')) a++;
            size_t ne = e;
            while (ne > a && (text[ne - 1] == ' ' || text[ne - 1] == '\t')) ne--;
            if (out->count < PMD_MAX_BLOCKS) {
                cur = out->count++;
                pmd_block_t *b = &out->blocks[cur];
                size_t ln = ne - a;
                if (ln > sizeof b->name - 1) ln = sizeof b->name - 1;
                memcpy(b->name, text + a, ln);
                b->name[ln] = 0;
                b->len = 0;
            } else {
                cur = -1;                            /* table full: drop        */
            }
        } else if (cur >= 0) {                        /* ---- hex bytes for block */
            size_t k = a;
            while (k < e) {
                while (k < e && (text[k] == ' ' || text[k] == '\t')) k++;
                size_t ts = k;
                while (k < e && text[k] != ' ' && text[k] != '\t') k++;
                size_t tl = k - ts;
                if (is_hex_byte(text + ts, tl)) {
                    char tmp[3] = {0};
                    memcpy(tmp, text + ts, tl);
                    pmd_block_t *b = &out->blocks[cur];
                    if (b->len < PMD_BLOCK_CAP)
                        b->bytes[b->len++] = (uint8_t)strtol(tmp, NULL, 16);
                }
            }
        }
        i = j + 1;
    }
    return out->count > 0;
}

bool pmd_load_path(const char *path, pmd_file_t *out) {
    FILE *fp = fopen(path, "rb");
    if (!fp) return false;
    fseek(fp, 0, SEEK_END);
    long sz = ftell(fp);
    fseek(fp, 0, SEEK_SET);
    if (sz <= 0) { fclose(fp); return false; }
    char *buf = malloc((size_t)sz);
    if (!buf) { fclose(fp); return false; }
    size_t rd = fread(buf, 1, (size_t)sz, fp);
    fclose(fp);
    bool ok = pmd_load_text(buf, rd, out);
    free(buf);
    return ok;
}

int pmd_count(const pmd_file_t *f, const char *name) {
    int c = 0;
    for (int i = 0; i < f->count; i++)
        if (strcmp(f->blocks[i].name, name) == 0) c++;
    return c;
}

span_t pmd_block(const pmd_file_t *f, const char *name, int nth) {
    int seen = 0;
    for (int i = 0; i < f->count; i++)
        if (strcmp(f->blocks[i].name, name) == 0 && seen++ == nth)
            return span_make(f->blocks[i].bytes, f->blocks[i].len);
    return span_make((const uint8_t *)"", 0);
}

/* ------------------------------ pure parsers ------------------------------- */

geraet_t parse_geraet(span_t s) {
    geraet_t g;
    memset(&g, 0, sizeof g);
    if (!span_has(s, 0x26, 2)) return g;             /* need through ReduzLim   */
    g.gtype          = span_u8(s, 0x00);
    g.gsubtype       = span_u8(s, 0x01);
    g.channel_amount = span_u8(s, 0x02);
    g.misens_amount  = span_u8(s, 0x03);
    for (int i = 0; i < 8; i++) g.misens_type[i] = span_u8(s, 0x1A + i);
    g.sample_div = span_u8(s, 0x22);
    g.reduz_lim  = span_u16le(s, 0x26);
    g.ok = true;
    return g;
}

kanal_t parse_kanal(span_t s) {
    kanal_t k;
    memset(&k, 0, sizeof k);
    if (!span_has(s, 0x4D, 4u * 12u)) return k;      /* need the feature block  */
    k.plc_type    = span_u8(s, 0x00);
    k.plc_version = span_u8(s, 0x01);
    k.channel_num = span_u8(s, 0x02);
    for (int i = 0; i < 4; i++) k.cdr_lim[i] = span_u8(s, 0x10 + i);

    int cnt = 0;
    for (int i = 0; i < 4; i++) {
        size_t off = 0x4D + (size_t)i * 12;
        feature_t *ft = &k.features[i];
        ft->mask = span_u8(s, off);
        span_cstr(s, off + 1, 11, ft->name, sizeof ft->name);
        ft->present = (ft->mask != 0);
        if (ft->present) cnt++;
    }
    k.feature_count = cnt;
    k.ok = true;
    return k;
}

zyklus_t parse_zyklus(span_t s) {
    zyklus_t z;
    memset(&z, 0, sizeof z);
    if (!span_has(s, 0, 170)) return z;                /* need a full record  */
    z.cycle_key = (int16_t)span_u16le(s, 0x00);
    z.sub_index = span_u8(s, 0x02);
    for (int i = 0; i < 4; i++) z.feature_idx[i] = span_u8(s, 0x26 + i);

    int n = 0;
    size_t o = 0x5D;                                   /* 7-byte limit entries */
    while (n < 8 && span_has(s, o, 7) && span_u8(s, o) == 0x01) {
        z.limits[n].level = span_u8(s, o + 1);
        z.limits[n].index = span_u8(s, o + 2);
        z.limits[n].term  = span_u8(s, o + 5);
        n++; o += 7;
    }
    z.limit_count = n;
    z.ok = true;
    return z;
}

int zyklus_channel_level(const zyklus_t *z) {
    return (z->limit_count > 0) ? z->limits[0].level : -1;   /* entry 0 = CDR  */
}

int zyklus_feature_level(const zyklus_t *z, int feat) {
    for (int i = 1; i < z->limit_count; i++)                 /* skip channel   */
        if (z->limits[i].index == (uint8_t)feat) return z->limits[i].level;
    return -1;
}
