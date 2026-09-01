/* xlsx.c — minimal .xlsx writer (stored ZIP + OOXML). Pure C. */
#include "xlsx.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>

/* -------- growable byte buffer -------- */
typedef struct { uint8_t *p; size_t len, cap; } buf_t;

static void buf_reserve(buf_t *b, size_t extra) {
    if (b->len + extra <= b->cap) return;
    size_t nc = b->cap ? b->cap : 4096;
    while (nc < b->len + extra) nc *= 2;
    b->p = realloc(b->p, nc);
    b->cap = nc;
}
static void buf_bytes(buf_t *b, const void *d, size_t n) {
    buf_reserve(b, n);
    memcpy(b->p + b->len, d, n);
    b->len += n;
}
static void buf_str(buf_t *b, const char *s) { buf_bytes(b, s, strlen(s)); }
static void buf_u16(buf_t *b, uint16_t v) { uint8_t t[2]={(uint8_t)v,(uint8_t)(v>>8)}; buf_bytes(b,t,2); }
static void buf_u32(buf_t *b, uint32_t v) { uint8_t t[4]={(uint8_t)v,(uint8_t)(v>>8),(uint8_t)(v>>16),(uint8_t)(v>>24)}; buf_bytes(b,t,4); }

static void buf_xml(buf_t *b, const char *s) {
    for (; *s; s++) switch (*s) {
        case '&': buf_str(b,"&amp;"); break;
        case '<': buf_str(b,"&lt;");  break;
        case '>': buf_str(b,"&gt;");  break;
        case '"': buf_str(b,"&quot;");break;
        default:  buf_reserve(b,1); b->p[b->len++]=(uint8_t)*s;
    }
}

/* -------- CRC32 (IEEE) -------- */
static uint32_t crc32_buf(const uint8_t *p, size_t n) {
    uint32_t c = 0xFFFFFFFFu;
    for (size_t i = 0; i < n; i++) {
        c ^= p[i];
        for (int k = 0; k < 8; k++) c = (c >> 1) ^ (0xEDB88320u & (uint32_t)(-(int32_t)(c & 1)));
    }
    return c ^ 0xFFFFFFFFu;
}

struct xlsx {
    char  path[512];
    char  sheet[64];
    buf_t rows;
    int   row;
    int   col;
    bool  in_row;
};

static void col_ref(int col0, int row1, char *out, size_t n) {
    char letters[4]; int li = 0, c = col0;
    do { letters[li++] = (char)('A' + (c % 26)); c = c / 26 - 1; } while (c >= 0 && li < 3);
    char rev[4]; for (int i = 0; i < li; i++) rev[i] = letters[li-1-i]; rev[li] = 0;
    snprintf(out, n, "%s%d", rev, row1);
}

xlsx_t *xlsx_open(const char *path, const char *sheet_name) {
    xlsx_t *x = calloc(1, sizeof *x);
    if (!x) return NULL;
    snprintf(x->path, sizeof x->path, "%s", path);
    snprintf(x->sheet, sizeof x->sheet, "%s", sheet_name ? sheet_name : "Log");
    return x;
}

void xlsx_row_begin(xlsx_t *x) {
    if (!x || x->in_row) return;
    x->row++; x->col = 0; x->in_row = true;
    char tmp[32]; snprintf(tmp, sizeof tmp, "<row r=\"%d\">", x->row);
    buf_str(&x->rows, tmp);
}
void xlsx_cell_str(xlsx_t *x, const char *s) {
    if (!x || !x->in_row) return;
    char ref[16]; col_ref(x->col++, x->row, ref, sizeof ref);
    char tmp[48]; snprintf(tmp, sizeof tmp, "<c r=\"%s\" t=\"inlineStr\"><is><t>", ref);
    buf_str(&x->rows, tmp);
    buf_xml(&x->rows, s ? s : "");
    buf_str(&x->rows, "</t></is></c>");
}
void xlsx_cell_num(xlsx_t *x, double v) {
    if (!x || !x->in_row) return;
    char ref[16]; col_ref(x->col++, x->row, ref, sizeof ref);
    char tmp[64]; snprintf(tmp, sizeof tmp, "<c r=\"%s\"><v>%.10g</v></c>", ref, v);
    buf_str(&x->rows, tmp);
}
void xlsx_row_end(xlsx_t *x) {
    if (!x || !x->in_row) return;
    buf_str(&x->rows, "</row>");
    x->in_row = false;
}

typedef struct { const char *name; buf_t data; uint32_t crc, off; } zentry_t;

static void zip_write(FILE *fp, zentry_t *e, int n) {
    uint32_t offset = 0;
    for (int i = 0; i < n; i++) {
        buf_t h = {0,0,0};
        e[i].off = offset;
        e[i].crc = crc32_buf(e[i].data.p, e[i].data.len);
        buf_u32(&h, 0x04034b50);
        buf_u16(&h, 20); buf_u16(&h, 0);
        buf_u16(&h, 0);
        buf_u16(&h, 0); buf_u16(&h, 0);
        buf_u32(&h, e[i].crc);
        buf_u32(&h, (uint32_t)e[i].data.len);
        buf_u32(&h, (uint32_t)e[i].data.len);
        buf_u16(&h, (uint16_t)strlen(e[i].name));
        buf_u16(&h, 0);
        buf_str(&h, e[i].name);
        fwrite(h.p, 1, h.len, fp);
        fwrite(e[i].data.p, 1, e[i].data.len, fp);
        offset += (uint32_t)(h.len + e[i].data.len);
        free(h.p);
    }
    uint32_t cd_start = offset, cd_size = 0;
    for (int i = 0; i < n; i++) {
        buf_t c = {0,0,0};
        buf_u32(&c, 0x02014b50);
        buf_u16(&c, 20); buf_u16(&c, 20);
        buf_u16(&c, 0); buf_u16(&c, 0);
        buf_u16(&c, 0); buf_u16(&c, 0);
        buf_u32(&c, e[i].crc);
        buf_u32(&c, (uint32_t)e[i].data.len);
        buf_u32(&c, (uint32_t)e[i].data.len);
        buf_u16(&c, (uint16_t)strlen(e[i].name));
        buf_u16(&c, 0); buf_u16(&c, 0);
        buf_u16(&c, 0); buf_u16(&c, 0);
        buf_u32(&c, 0);
        buf_u32(&c, e[i].off);
        buf_str(&c, e[i].name);
        fwrite(c.p, 1, c.len, fp);
        cd_size += (uint32_t)c.len;
        free(c.p);
    }
    buf_t z = {0,0,0};
    buf_u32(&z, 0x06054b50);
    buf_u16(&z, 0); buf_u16(&z, 0);
    buf_u16(&z, (uint16_t)n); buf_u16(&z, (uint16_t)n);
    buf_u32(&z, cd_size); buf_u32(&z, cd_start);
    buf_u16(&z, 0);
    fwrite(z.p, 1, z.len, fp);
    free(z.p);
}

bool xlsx_close(xlsx_t *x) {
    if (!x) return false;
    if (x->in_row) xlsx_row_end(x);

    buf_t sheet = {0,0,0};
    buf_str(&sheet,
        "<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"yes\"?>"
        "<worksheet xmlns=\"http://schemas.openxmlformats.org/spreadsheetml/2006/main\">"
        "<sheetData>");
    buf_bytes(&sheet, x->rows.p, x->rows.len);
    buf_str(&sheet, "</sheetData></worksheet>");

    buf_t ct = {0,0,0};
    buf_str(&ct,
        "<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"yes\"?>"
        "<Types xmlns=\"http://schemas.openxmlformats.org/package/2006/content-types\">"
        "<Default Extension=\"rels\" ContentType=\"application/vnd.openxmlformats-package.relationships+xml\"/>"
        "<Default Extension=\"xml\" ContentType=\"application/xml\"/>"
        "<Override PartName=\"/xl/workbook.xml\" ContentType=\"application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml\"/>"
        "<Override PartName=\"/xl/worksheets/sheet1.xml\" ContentType=\"application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml\"/>"
        "</Types>");

    buf_t rels = {0,0,0};
    buf_str(&rels,
        "<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"yes\"?>"
        "<Relationships xmlns=\"http://schemas.openxmlformats.org/package/2006/relationships\">"
        "<Relationship Id=\"rId1\" Type=\"http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument\" Target=\"xl/workbook.xml\"/>"
        "</Relationships>");

    buf_t wb = {0,0,0};
    buf_str(&wb,
        "<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"yes\"?>"
        "<workbook xmlns=\"http://schemas.openxmlformats.org/spreadsheetml/2006/main\" "
        "xmlns:r=\"http://schemas.openxmlformats.org/officeDocument/2006/relationships\">"
        "<sheets><sheet name=\"");
    buf_xml(&wb, x->sheet);
    buf_str(&wb, "\" sheetId=\"1\" r:id=\"rId1\"/></sheets></workbook>");

    buf_t wbr = {0,0,0};
    buf_str(&wbr,
        "<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"yes\"?>"
        "<Relationships xmlns=\"http://schemas.openxmlformats.org/package/2006/relationships\">"
        "<Relationship Id=\"rId1\" Type=\"http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet\" Target=\"worksheets/sheet1.xml\"/>"
        "</Relationships>");

    zentry_t entries[] = {
        { "[Content_Types].xml",        ct,    0, 0 },
        { "_rels/.rels",                rels,  0, 0 },
        { "xl/workbook.xml",            wb,    0, 0 },
        { "xl/_rels/workbook.xml.rels", wbr,   0, 0 },
        { "xl/worksheets/sheet1.xml",   sheet, 0, 0 },
    };
    int n = (int)(sizeof entries / sizeof entries[0]);

    FILE *fp = fopen(x->path, "wb");
    bool ok = fp != NULL;
    if (ok) { zip_write(fp, entries, n); fclose(fp); }

    for (int i = 0; i < n; i++) free(entries[i].data.p);
    free(x->rows.p);
    free(x);
    return ok;
}
