---
name: number-formats
description: Apply the Macabacus financial number-format standard to Excel models and HTML tables — en-dash zeros, parenthesized negatives with decimal-aligned positives, currency symbol only on the top row, blue inputs, green cross-sheet links, red errors, grey-italic margins, bold totals, plus percent/multiple/toggle formats. Use when formatting a financial model, operating model, or numeric table; when the user says "format these numbers", "make the numbers look right", "Macabacus formatting", "apply number formats", or hands over an .xlsx model to clean up. Ships byte-exact Excel format codes (formats.json) and an openpyxl applicator.
---

# Number Formats

The house standard for formatting financial numbers, captured byte-exact from a
reference model. It covers two surfaces — **Excel** (the custom format codes in
`formats.json`) and **HTML tables** (the CSS equivalent below) — so a number
looks the same whether it's in a model or on a page.

The governing idea: **format carries meaning.** Parentheses encode sign,
alignment encodes magnitude, and *color encodes provenance* — where a number came
from. None of it is decoration.

---

## The six formats (exact Excel codes)

Each is a 4-section custom code: `positive ; negative ; zero ; text`.

| Type | Positive | Zero | Negative | Excel custom format |
|---|---|---|---|---|
| **Number** | `1.0` | `–` | `(1.0)` | `_(#,##0.0_);_(\(#,##0.0\);_("–"_);@_(` |
| **Percent** | `100.0%` | `–` | `(100.0%)` | `_(0.0%_);\(0.0%\);_("–"_)_%;_(@_)_%` |
| **Multiple** | `1.0x` | `–` | `(1.0x)` | `_(0.0\x_)_)_';_(\(0.0\x\)_'_';_("–"_)_%;_(@_)_%` |
| **Toggle Yes/No** | `Yes` | `No` | `ERROR` | `"Yes";"ERROR";"No";"ERROR"` |
| **Toggle Y/N** | `Y` | `N` | `ERROR` | `"Y";"ERROR";"N";"ERROR"` |
| **Toggle On/Off** | `On` | `Off` | `ERROR` | `"On";"ERROR";"Off";"ERROR"` |

What the codes encode (this is *why* they look right):

- **Zero is an en-dash `–`, never `0.0`.** The `_("–"_)` zero section prints a dash.
- **Negatives are parenthesized; positives are bare** — and the `_(` … `_)`
  spacers reserve the width of the parentheses on positives, so the decimal
  points line up down the column.
- **Toggles force a real boolean.** Positive → the on-word, zero → the off-word,
  anything else → `ERROR`. A toggle cell that isn't exactly 1 or 0 screams.
- The production model uses an equivalent zero variant `_(\–_)` (unquoted dash);
  both render `–`. `formats.json` carries both under `number` and `number_zero_dash`.

---

## Color = provenance (exact hexes)

| Role | Font | Fill | Meaning |
|---|---|---|---|
| **Input** | `#0000FF` blue | `#FFFFCC` yellow | a hardcoded assumption a human typed |
| **Hardcode** | `#0000FF` blue | — | a hardcoded value inline |
| **Formula** | default ink | — | a calculation (no special color) |
| **Cross-sheet link** | `#00B050` green | — | pulled from another sheet |
| **Error / check** | `#FF0000` red | — | a failed check or broken link **only** |

Rules: **blue means "a human typed this"** (a reader can change it and watch the
model recalc). **Red is errors only** — a *negative* number uses parentheses, never
red. The driver convention is blue font on yellow fill. **Green is `#00B050`** —
the Macabacus link standard (Excel `FF00B050` + web `#00B050`), authoritative
across every surface; a generic `#008000` is superseded.

## Row styles

- **Totals** → **bold** (optionally a subtle top rule).
- **Margins** (the `%` rows) → **grey + italic** (`#808080`).
- **Section separators** → a **grey hairline** border, not a heavy rule.
- **`$` appears at most on the top row** of a column; the scale is stated **once**
  in the header/caption (e.g. *"$'s in '000s"*), never repeated per cell.

---

## Apply it to a workbook

`apply-number-formats.py` reads the exact codes from `formats.json` and applies them:

```bash
# Number-format a range:
python3 apply-number-formats.py model.xlsx --range "Operating Model!F15:J40" --format number
python3 apply-number-formats.py model.xlsx --range "Sheet1!F21:J21"          --format percent
python3 apply-number-formats.py model.xlsx --range "Sheet1!F17:J17"          --format multiple
python3 apply-number-formats.py model.xlsx --range "Sheet1!C2"               --format yes-no

# Provenance / row styles:
python3 apply-number-formats.py model.xlsx --range "Sheet1!C39"     --style input    # blue on yellow
python3 apply-number-formats.py model.xlsx --range "Sheet1!F18:J18" --style total    # bold
python3 apply-number-formats.py model.xlsx --range "Sheet1!F21:J21" --style margin   # grey italic

# Auto-color by provenance across a sheet
# (hardcoded number -> blue input; cross-sheet formula -> green link; other formulas left as-is):
python3 apply-number-formats.py model.xlsx --sheet "Operating Model" --auto-color
```

Writes `model-formatted.xlsx` by default; pass `--in-place` to overwrite. The
exact codes live in `formats.json` — use it directly from any tool so nothing is
re-transcribed (a stray `_` or `;` breaks an Excel format).

---

## The same standard, on the web

For HTML tables (pairs with the `pagecraft` / `.bbt` table system):

```css
.num            { text-align:right; font-variant-numeric:tabular-nums lining-nums; white-space:nowrap; }
.aff-l, .aff-r  { visibility:hidden; }            /* reserve paren width so negatives align */
.cell-input     { color:#0000FF; }                /* blue input  */
.cell-input.fill{ background:#FFFFCC; }            /* + yellow driver fill */
.cell-link      { color:#00B050; }                /* green cross-sheet link */
.cell-error     { color:#FF0000; }                /* red, errors only */
tr.tot td       { font-weight:700; }              /* bold totals */
.margin         { color:#808080; font-style:italic; }   /* grey-italic margins */
```

- Zero → render the literal `–` (en-dash), not `0`.
- Negative → `(340.0)`, wrapped with `.aff-l`/`.aff-r` on positives to align.
- `$` on the first row + total only; scale once in the caption.

---

## What this skill does NOT do

- It does **not** invent values or change cell contents — it only applies
  *formatting* (number formats, fonts, fills, borders).
- It does **not** auto-decide a cell's *type* (number vs percent vs multiple) —
  pass the range + `--format`. `--auto-color` only infers *provenance*
  (hardcode vs formula vs cross-sheet link), which is unambiguous from the
  formula.
- It is not a modeling or calculation skill — for building models, use the
  relevant financial-modeling skill; use this to make the output read correctly.
