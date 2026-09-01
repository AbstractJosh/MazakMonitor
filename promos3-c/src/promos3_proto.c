/* promos3_proto.c — name/enum lookups (report Part 3 + Part 6). */
#include "promos3.h"
#include <stdio.h>

/* ---- command names, keyed by (group, command) ------------------------ *
 * Known names come from embedded strings / runtime log / xref. Numbers
 * without a confirmed name are labelled generically; a passive reader
 * prints "cmd 0xNN" for those, which is fine. */

typedef struct { uint32_t cmd; const char *name; } cmd_row_t;

/* GROUP 1 = MC_ (this box). Report Part 3.1. */
static const cmd_row_t mc_cmds[] = {
    {0x06, "MC_GIVEKONFIG"},          /* confirmed from runtime log         */
    {0x15, "MC_PRESSEDKEYS"},         /* confirmed (qDebug only)            */
    {0x1B, "MC_GIVESIGNALVERLAUF"},   /* confirmed via xref -> trace decoder */
    /* remaining group-1 numbers are located handlers without confirmed
     * names yet; extend as you read each worker's mutex string:           */
    {0x01,"MC_cmd_01"},{0x02,"MC_cmd_02"},{0x04,"MC_cmd_04"},{0x05,"MC_cmd_05"},
    {0x08,"MC_cmd_08"},{0x0A,"MC_cmd_0A"},{0x0C,"MC_cmd_0C"},{0x0D,"MC_cmd_0D"},
    {0x0E,"MC_cmd_0E"},{0x0F,"MC_cmd_0F"},{0x12,"MC_cmd_12"},{0x14,"MC_cmd_14"},
    {0x16,"MC_cmd_16"},{0x18,"MC_cmd_18"},{0x1A,"MC_cmd_1A"},{0x1C,"MC_cmd_1C"},
    {0x1F,"MC_cmd_1F"},{0x21,"MC_cmd_21"},{0x23,"MC_cmd_23"},{0x24,"MC_cmd_24"},
    {0x25,"MC_cmd_25"},{0x27,"MC_cmd_27"},{0x28,"MC_cmd_28"},{0x29,"MC_cmd_29"},
    {0x2A,"MC_cmd_2A"},{0x2B,"MC_cmd_2B"},{0x2C,"MC_cmd_2C"},{0x2D,"MC_cmd_2D"},
    {0x30,"MC_cmd_30"},{0x32,"MC_cmd_32"},{0x33,"MC_cmd_33"},{0x34,"MC_cmd_34"},
    {0x35,"MC_cmd_35"},{0x36,"MC_cmd_36"},{0x37,"MC_cmd_37"},{0x38,"MC_cmd_38"},
    {0x39,"MC_cmd_39"},{0x3C,"MC_cmd_3C"},
};

/* GROUP 2 = MC3_ (not used by this box; kept for completeness). Part 3.2. */
static const cmd_row_t mc3_cmds[] = {
    {0x03,"MC3_GET_CB_VERSION"},{0x04,"MC3_SENSOR_INFO"},{0x05,"MC3_MERKMAL_INFO"},
    {0x06,"MC3_GERAETEREC"},{0x07,"MC3_SET_STREAMING"},{0x08,"MC3_LIMIT_INFO"},
    {0x09,"MC3_CYCLE_INFO"},{0x0F,"MC3_ALARM"},{0x10,"MC3_EVENT"},
    {0x11,"MC3_SENSOR_VFAKT(stub)"},{0x18,"MC3_SYSTEM_MODE"},{0x1A,"MC3_PATTERN_INFO"},
    {0x1B,"MC3_SET_OUTPUTS"},
};

/* GROUP 0 = handshake. Part 3.3. */
static const cmd_row_t hs_cmds[] = {
    {0x01,"MC_GIVEGTYPE"},{0x02,"HS_cmd_02"},
};

static const char *lookup(const cmd_row_t *t, size_t n, uint32_t cmd) {
    for (size_t i = 0; i < n; i++) if (t[i].cmd == cmd) return t[i].name;
    return NULL;
}

const char *cmd_name(promos3_group_t group, uint32_t command) {
    static char fallback[32];
    const char *s = NULL;
    switch (group) {
        case GROUP_HANDSHAKE: s = lookup(hs_cmds,  sizeof hs_cmds /sizeof*hs_cmds,  command); break;
        case GROUP_MC:        s = lookup(mc_cmds,  sizeof mc_cmds /sizeof*mc_cmds,  command); break;
        case GROUP_MC3:       s = lookup(mc3_cmds, sizeof mc3_cmds/sizeof*mc3_cmds, command); break;
    }
    if (s) return s;
    snprintf(fallback, sizeof fallback, "cmd_0x%02X(g%d)", command, (int)group);
    return fallback;
}

/* Is this (group,command) a named command (in a table), vs a generic fallback? */
bool cmd_known(promos3_group_t group, uint32_t command) {
    switch (group) {
        case GROUP_HANDSHAKE: return lookup(hs_cmds,  sizeof hs_cmds /sizeof*hs_cmds,  command) != NULL;
        case GROUP_MC:        return lookup(mc_cmds,  sizeof mc_cmds /sizeof*mc_cmds,  command) != NULL;
        case GROUP_MC3:       return lookup(mc3_cmds, sizeof mc3_cmds/sizeof*mc3_cmds, command) != NULL;
    }
    return false;
}

/* Confidence in a command's decoded field layout — governs whether print
 * shows decoded values or only a safe raw hexdump. Only genuinely confirmed
 * layouts get to print "meaning". */
cmd_conf_t cmd_confidence(promos3_group_t group, uint32_t command) {
    if (group == GROUP_MC  && command == 0x1B) return CONF_CONFIRMED;   /* trace */
    if (group == GROUP_MC  && command == 0x06) return CONF_PROVISIONAL; /* konfig: offsets guessed */
    if (group == GROUP_MC3 && command == 0x0F) return CONF_PROVISIONAL; /* alarm: MC3-derived      */
    return cmd_known(group, command) ? CONF_NAMED : CONF_UNKNOWN;
}

/* ---- ToolStatus (Part 6.1) ---- */
const char *tool_status_name(unsigned s) {
    static const char *n[] = {
        "empty","Overload","Underload","Contact","Missing","Work Over",
        "Work Under","Cut start","Cut end","Dynam. upper","Dynam. lower",
        "Pattern upper","Pattern lower","ACF contact","cutdetect contact","Tool wear"
    };
    return (s < 16) ? n[s] : "?";
}

/* ---- SensorType (Part 6.2), selected ---- */
const char *sensor_type_name(unsigned t) {
    switch (t) {
        case 0x01: return "PA-Box";   case 0x03: return "VB-Box";
        case 0x10: return "PA 111";   case 0x80: return "PROCUR-S";
        case 0x81: return "PROCUR-I"; case 0x82: return "PROCUR-B";
        case 0x83: return "ACFeed";   case 0x84: return "ACfeed OVR";
        case 0x90: return "Position"; case 0x91: return "Temperature";
        case 0xFF: return "Unknown";  default:   return "sensor?";
    }
}

/* ---- Alarm slot labels [AlarmNames] (Part 6.6, install-configurable) ---- */
const char *alarm_slot_name(unsigned n) {
    static const char *a[] = {"","Collision","Break","Wearout","Missing","Coolant"};
    return (n >= 1 && n <= 5) ? a[n] : "";
}

/* ---- Feature labels for THIS box, from SKanalRec (report Part 7.2).
 * NOTE: these are per-install. Ideally read them live from the device
 * (SKanalRec / config DB) instead of hardcoding. Order = feature index. */
const char *feature_name(int index) {
    static const char *f[] = { "VIBRATION", "M131 DEBI", "M131BASINC", "M08 DEBI" };
    return (index >= 0 && index < 4) ? f[index] : "feature?";
}
