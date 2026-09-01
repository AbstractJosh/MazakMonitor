/* xlsx.h — minimal Office Open XML (.xlsx) writer, pure C, no dependencies.
 *
 * Secondary feature (logging). Produces a single-sheet workbook that Excel 2016
 * opens. Rows are buffered in memory and written on close (a monitoring log is
 * modest; rotate files for very long runs). Values are numbers or inline
 * strings — no shared-string table, no styles.
 */
#ifndef XLSX_H
#define XLSX_H

#include <stdbool.h>

typedef struct xlsx xlsx_t;

xlsx_t *xlsx_open(const char *path, const char *sheet_name);
void    xlsx_row_begin(xlsx_t *x);
void    xlsx_cell_str(xlsx_t *x, const char *s);
void    xlsx_cell_num(xlsx_t *x, double v);
void    xlsx_row_end(xlsx_t *x);
bool    xlsx_close(xlsx_t *x);          /* writes the file; frees x */

#endif /* XLSX_H */
