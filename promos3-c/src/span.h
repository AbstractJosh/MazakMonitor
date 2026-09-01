/* span.h — a bounds-checked view over bytes, with pure readers.
 *
 * This is the data-oriented core: nothing here owns memory, allocates, or
 * mutates shared state. A span is just {pointer, length}. Every reader is a
 * pure function (span, offset) -> value, safe on out-of-range (returns 0 /
 * empty), so parsers never index past the buffer. Header-only + inline.
 */
#ifndef SPAN_H
#define SPAN_H

#include <stdint.h>
#include <stddef.h>
#include <stdbool.h>

typedef struct { const uint8_t *p; size_t n; } span_t;

static inline span_t span_make(const uint8_t *p, size_t n) { span_t s = {p, n}; return s; }

/* true iff [off, off+len) is fully inside the span (overflow-safe) */
static inline bool span_has(span_t s, size_t off, size_t len) {
    return off <= s.n && len <= s.n - off;
}

static inline uint8_t span_u8(span_t s, size_t o) {
    return span_has(s, o, 1) ? s.p[o] : 0;
}
static inline uint16_t span_u16le(span_t s, size_t o) {
    return span_has(s, o, 2) ? (uint16_t)(s.p[o] | (s.p[o + 1] << 8)) : 0;
}
static inline uint16_t span_u16be(span_t s, size_t o) {
    return span_has(s, o, 2) ? (uint16_t)((s.p[o] << 8) | s.p[o + 1]) : 0;
}
static inline uint32_t span_u32le(span_t s, size_t o) {
    if (!span_has(s, o, 4)) return 0;
    return (uint32_t)s.p[o] | ((uint32_t)s.p[o + 1] << 8)
         | ((uint32_t)s.p[o + 2] << 16) | ((uint32_t)s.p[o + 3] << 24);
}

/* Copy an ASCII field of up to `field` bytes (stopping at NUL) into dst,
 * always NUL-terminating within `max`. Returns the string length. Pure. */
static inline size_t span_cstr(span_t s, size_t o, size_t field, char *dst, size_t max) {
    size_t k = 0;
    for (size_t i = 0; i < field && k + 1 < max; i++) {
        uint8_t c = span_u8(s, o + i);
        if (c == 0) break;
        dst[k++] = (char)c;
    }
    if (max) dst[k] = 0;
    return k;
}

/* A sub-view; empty if out of range. Pure. */
static inline span_t span_sub(span_t s, size_t o, size_t len) {
    return span_has(s, o, len) ? span_make(s.p + o, len) : span_make(s.p, 0);
}

#endif /* SPAN_H */
