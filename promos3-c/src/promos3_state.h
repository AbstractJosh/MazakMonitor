/* promos3_state.h — the reader's whole state as plain data.
 *
 * Data-oriented: reader_state_t is one POD aggregate (no pointers), so it
 * serializes by value. Config (from PMD) and the live snapshot both live here.
 * Updates are explicit transforms of this data; nothing hides in globals.
 */
#ifndef PROMOS3_STATE_H
#define PROMOS3_STATE_H

#include "promos3.h"
#include "promos3_config.h"

#define STATE_MAGIC   0x50335354u      /* "P3ST"                              */
#define STATE_VERSION 1u

typedef struct {
    bool     configured;               /* config loaded for this unit         */
    geraet_t geraet;                   /* device summary (POD)                */
    kanal_t  kanal;                    /* channel + feature labels (POD)      */

    bool     have_konfig;              /* live: last MC_GIVEKONFIG seen        */
    konfig_t konfig;
    struct {                           /* live: last trace summary per feature */
        bool    valid;
        int16_t vmin, vmax;
        int     count;
    } trace[4];

    uint32_t msg_count;                /* counters                            */
    uint32_t unparsed_count;
    uint32_t alarm_count;
} unit_state_t;

typedef struct reader_state {
    uint32_t     magic;
    uint32_t     version;
    uint32_t     size;                 /* sizeof(reader_state) guard          */
    unit_state_t units[MAX_UNITS];
} reader_state_t;

/* lifecycle */
void reader_state_init(reader_state_t *st);
bool reader_state_save(const char *path, const reader_state_t *st);
bool reader_state_load(const char *path, reader_state_t *st);   /* false = no/invalid file */

/* config wiring: load a PMD export into a unit (unit < 0 = apply to all) */
bool reader_apply_pmd(reader_state_t *st, int unit, const char *pmd_path);

/* transform: fold one completed message into the snapshot */
void reader_state_update(reader_state_t *st, const promos3_msg_t *m);

/* config-aware feature label; falls back to the built-in table. Safe for any key. */
const char *reader_feature_name(const reader_state_t *st, int unit, unsigned key);

/* one-line summary of what the reader currently knows (for --state dumps) */
void reader_state_dump(const reader_state_t *st);

#endif /* PROMOS3_STATE_H */
