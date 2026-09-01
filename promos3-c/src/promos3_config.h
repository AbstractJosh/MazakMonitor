/* promos3_config.h — offline device configuration from PMD export files.
 *
 * Data-oriented: the types below are plain values (no methods, no pointers to
 * owned memory). Parsers are pure: (span) -> record value. I/O (reading the
 * file) is isolated in pmd_load_path(); everything else is a transform.
 *
 * Record layouts are the VERIFIED fields from report Part 7 (cross-checked
 * byte-for-byte against 1974.txt). Unverified bytes are left untouched.
 */
#ifndef PROMOS3_CONFIG_H
#define PROMOS3_CONFIG_H

#include "span.h"

/* ---------- raw PMD file: a flat, ordered list of named byte blocks -------- */
#define PMD_MAX_BLOCKS 64
#define PMD_BLOCK_CAP  512

typedef struct {
    char     name[24];               /* section name, ';' stripped (e.g. "SGeraetRec") */
    uint8_t  bytes[PMD_BLOCK_CAP];
    uint16_t len;
} pmd_block_t;

typedef struct {
    pmd_block_t blocks[PMD_MAX_BLOCKS];
    int         count;
} pmd_file_t;

/* Pure text transform: PMD text -> blocks. No file I/O. */
bool   pmd_load_text(const char *text, size_t n, pmd_file_t *out);
/* I/O boundary: read a file, then pmd_load_text(). */
bool   pmd_load_path(const char *path, pmd_file_t *out);
/* Pure accessors over parsed blocks. */
int    pmd_count(const pmd_file_t *f, const char *name);
span_t pmd_block(const pmd_file_t *f, const char *name, int nth);

/* ---------------------------- decoded records ------------------------------ */
typedef struct {
    uint8_t mask;                    /* feature-select bits; 0x80 = flag (ignore for index) */
    char    name[12];                /* operator label, per-install (VIBRATION, ...)        */
    bool    present;                 /* mask != 0                                           */
} feature_t;

typedef struct {                     /* SGeraetRec (66 bytes) */
    bool     ok;
    uint8_t  gtype, gsubtype;        /* +0x00 +0x01                                          */
    uint8_t  channel_amount;         /* +0x02                                                */
    uint8_t  misens_amount;          /* +0x03                                                */
    uint8_t  misens_type[8];         /* +0x1A..0x21 (SensorType codes; 0x80 = PROCUR-S)      */
    uint8_t  sample_div;             /* +0x22                                                */
    uint16_t reduz_lim;              /* +0x26 (LE)                                           */
} geraet_t;

typedef struct {                     /* SKanalRecV40 (144 bytes) */
    bool      ok;
    uint8_t   plc_type, plc_version; /* +0x00 +0x01                                          */
    uint8_t   channel_num;           /* +0x02                                                */
    uint8_t   cdr_lim[4];            /* +0x10..0x13                                          */
    feature_t features[4];           /* +0x4D, 4 x 12-byte [mask][name11]                    */
    int       feature_count;
} kanal_t;

/* Pure parsers: span -> value. Missing/short input yields {.ok=false}. */
geraet_t parse_geraet(span_t s);
kanal_t  parse_kanal(span_t s);

/* ---- SZykRecV4802 (cycle record, 170 bytes) ---- *
 * Verified fields + a scanned limit list. Entry stride 7 from +0x5D:
 *   [0]=0x01 flag  [1]=level  [2]=feature index  [5]=term (0xFB/0xFF)
 * Entry 0 is the channel/CDR limit; the rest are per-feature by index. */
typedef struct { uint8_t level, index, term; } zlimit_t;

typedef struct {
    bool     ok;
    int16_t  cycle_key;                /* +0x00 (s16)                         */
    uint8_t  sub_index;                /* +0x02                               */
    uint8_t  feature_idx[4];           /* +0x26 = {0,1,2,3} (verified)        */
    zlimit_t limits[8];
    int      limit_count;
    /* everything else stays raw/inferred — not fabricated */
} zyklus_t;

zyklus_t parse_zyklus(span_t s);
int      zyklus_channel_level(const zyklus_t *z);          /* -1 if none      */
int      zyklus_feature_level(const zyklus_t *z, int feat);/* -1 if none      */

#endif /* PROMOS3_CONFIG_H */
