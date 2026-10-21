---
name: csv-to-html
description: Turn any CSV into a single self-contained, interactive HTML table (sort, per-column filters, search, column show/hide, download of the filtered rows) that opens offline in any browser and can be emailed. Use when asked to share, view, browse or publish a CSV or spreadsheet-style data as HTML, or when a script that produces a CSV should also produce a readable page.
---

# CSV to HTML

`scripts/csv2html.py` turns a CSV into one HTML page with:

- sorting on any column (shift-click to sort by several columns);
- a filter under each header:
  - a pick list for columns with few distinct values;
  - "contains" text filters for other text columns;
  - `=`, `>`, `<`, `>=`, `<=` for number columns;
- a search across all columns, a column show/hide menu, and Reset;
- **Download filtered CSV**, which exports the rows currently shown;
- long text capped at 3 lines; click a row to expand it.

```bash
CSV2HTML=<this skill's folder>/scripts/csv2html.py             # e.g. .cursor/skills/csv-to-html/...
python3 $CSV2HTML path/to/data.csv --title "My table"            # writes path/to/data.html
python3 $CSV2HTML a.csv b.csv                                    # several at once
python3 $CSV2HTML data.csv -o out/table.html                     # explicit output (one CSV only)
python3 $CSV2HTML data.csv --cdn                                 # small file, needs internet
```

It needs only the Python 3.9+ standard library. Columns and filter types come from the data.
The table is drawn by [Tabulator](https://tabulator.info) 6.3.1 (MIT licence), inlined from
`scripts/vendor/` by default so the page works offline (about 500 KB). `--cdn` loads it from
cdnjs instead.

The data is embedded at build time because browsers don't let a local page read a separate CSV
file. **Rebuild the HTML whenever the CSV changes.** When writing a script that generates a CSV,
call `csv2html.py` at its end so the HTML stays in step.

For CSVs meant to be opened in Excel, write them as UTF-8 with a BOM (`encoding="utf-8-sig"`) so
non-ASCII characters display correctly.
