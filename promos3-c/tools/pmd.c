/* tools/pmd.c — load a PROVIS3 PMD export, decode config, optionally self-test.
 *
 *   promos3_pmd <file.pmd>            pretty-print decoded device/channel/cycles
 *   promos3_pmd --check <file.pmd>    same, plus assert file-agnostic invariants
 *
 * Presentation only lives here (the I/O edge). Decoding is pure (promos3_config).
 */
#include "promos3.h"          /* sensor_type_name() */
#include "promos3_config.h"
#include <stdio.h>
#include <string.h>

static void print_config(const pmd_file_t *f) {
    geraet_t g = parse_geraet(pmd_block(f, "SGeraetRec", 0));
    kanal_t  k = parse_kanal (pmd_block(f, "SKanalRecV40", 0));
    int cycles = pmd_count(f, "SZykRecV4802");

    printf("== Device (SGeraetRec) ==\n");
    if (g.ok) {
        printf("  GType 0x%02X  SubType %u  Channels %u  MI-Sensors %u  SampleDiv %u  ReduzLim %u\n",
               g.gtype, g.gsubtype, g.channel_amount, g.misens_amount, g.sample_div, g.reduz_lim);
        printf("  MiSensType:");
        for (int i = 0; i < 8; i++) printf(" %s", sensor_type_name(g.misens_type[i]));
        printf("\n");
    } else printf("  (missing / short)\n");

    printf("== Channel (SKanalRecV40) ==\n");
    if (k.ok) {
        printf("  PLC_Type 0x%02X  PLC_Version 0x%02X  Channel_Num %u  CDRLim %u/%u/%u/%u\n",
               k.plc_type, k.plc_version, k.channel_num,
               k.cdr_lim[0], k.cdr_lim[1], k.cdr_lim[2], k.cdr_lim[3]);
        printf("  Features (%d):\n", k.feature_count);
        for (int i = 0; i < 4; i++)
            if (k.features[i].present)
                printf("    [%d] bit 0x%02X  \"%s\"\n", i, k.features[i].mask & 0x0F, k.features[i].name);
    } else printf("  (missing / short)\n");

    printf("== Cycles (%d x SZykRecV4802) ==\n", cycles);
    for (int c = 0; c < cycles; c++) {
        zyklus_t z = parse_zyklus(pmd_block(f, "SZykRecV4802", c));
        if (!z.ok) continue;
        int ch = zyklus_channel_level(&z);
        printf("  cycle %d: key=%d sub=%u  channelLim=%s",
               c, z.cycle_key, z.sub_index, ch < 0 ? "-" : "");
        if (ch >= 0) printf("%d", ch);
        printf("  featLim=[");
        for (int i = 0; i < 4; i++) {
            int lv = zyklus_feature_level(&z, i);
            printf("%s%s", i ? "," : "", lv < 0 ? "-" : "");
            if (lv >= 0) printf("%d", lv);
        }
        printf("]\n");
    }
}

/* File-agnostic invariants: hold for every valid GType-0x44 export regardless
 * of feature names or per-cycle levels. Feature names are printed, not asserted. */
static int check_invariants(const pmd_file_t *f) {
    int fails = 0;
    #define CK(cond, msg) do { int _c=(cond); \
        printf("  [%s] %s\n", _c?"ok":"FAIL", msg); if(!_c) fails++; } while(0)

    geraet_t g = parse_geraet(pmd_block(f, "SGeraetRec", 0));
    kanal_t  k = parse_kanal (pmd_block(f, "SKanalRecV40", 0));

    CK(g.ok,                  "SGeraetRec parsed");
    CK(g.gtype == 0x44,       "GType == 0x44");
    CK(g.gsubtype == 5,       "GSubType == 5");
    CK(g.channel_amount == 1, "Channel_Amount == 1");
    CK(g.misens_amount == 4,  "MiSens_Amount == 4");
    int all80 = 1; for (int i = 0; i < 8; i++) all80 &= (g.misens_type[i] == 0x80);
    CK(all80,                 "MiSensType all 0x80 (PROCUR-S)");
    CK(g.sample_div == 1,     "SampleDiv == 1");
    CK(g.reduz_lim == 6612,   "ReduzLim == 6612");

    CK(k.ok,                  "SKanalRecV40 parsed");
    CK(k.plc_type == 0x10,    "PLC_Type == 0x10");
    CK(k.plc_version == 0x20, "PLC_Version == 0x20");
    int allAA = 1; for (int i = 0; i < 4; i++) allAA &= (k.cdr_lim[i] == 0xAA);
    CK(allAA,                 "CDRLim all 0xAA");
    CK(k.feature_count == 4,  "4 features present");
    printf("       feature names: \"%s\" \"%s\" \"%s\" \"%s\"\n",
           k.features[0].name, k.features[1].name, k.features[2].name, k.features[3].name);

    int cyc = pmd_count(f, "SZykRecV4802");
    CK(cyc == 9,              "9 cycle records");
    int feat_ok = 1, chan170 = 0;
    for (int c = 0; c < cyc; c++) {
        zyklus_t z = parse_zyklus(pmd_block(f, "SZykRecV4802", c));
        for (int i = 0; i < 4; i++) feat_ok &= (z.feature_idx[i] == i);
        if (zyklus_channel_level(&z) == 170) chan170 = 1;
    }
    CK(feat_ok,               "every cycle feature_idx == {0,1,2,3}");
    CK(chan170,               "a cycle carries channel limit 170 (=CDRLim)");

    #undef CK
    return fails;
}

int main(int argc, char **argv) {
    const char *path = NULL; int check = 0;
    for (int i = 1; i < argc; i++) {
        if (!strcmp(argv[i], "--check")) check = 1;
        else path = argv[i];
    }
    if (!path) { fprintf(stderr, "usage: promos3_pmd [--check] <file.pmd>\n"); return 2; }

    pmd_file_t f;
    if (!pmd_load_path(path, &f)) { fprintf(stderr, "cannot load %s\n", path); return 1; }

    print_config(&f);
    if (check) {
        printf("\n== SELF-TEST (invariants) ==\n");
        int fails = check_invariants(&f);
        printf("\nSELF-TEST: %s (%d failing)\n", fails ? "FAIL" : "PASS", fails);
        return fails ? 1 : 0;
    }
    return 0;
}
