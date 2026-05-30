# Number Formats Reference — the Macabacus convention

Financial numbers are read for *credibility* before they're read for value. A
column where the decimals don't line up, negatives are red instead of
parenthesized, or units are repeated in every cell reads as amateur — regardless
of whether the math is right. This reference encodes the Macabacus / Excel
financial-exhibit standard so every table, KPI, and dashboard formats numbers
the same way, deterministically.

The governing idea: **format carries meaning.** Alignment encodes magnitude,
parentheses encode sign, and *color encodes provenance* — where a number came
from, not how it should look.

---

## 1. Color encodes provenance (the Macabacus palette)

This is the single most distinctive convention and the one most often dropped.
Color is **not** decoration — it tells the reader whether a cell is a hardcoded
assumption, a calculation, or a link. Use it in any exhibit a reader might audit.

| Slot | Meaning | Hex | Use |
|---|---|---|---|
| **Input** | hardcoded assumption a human typed | `#0000FF` (pure blue) | every hardcoded number/driver |
| **Driver fill** | an input cell highlighted for attention | `#FFFFCC` bg + blue text | key assumptions to stress-test |
| **Formula** | a calculation | `#1a2330` (primary ink) | derived values — the default |
| **Cross-sheet link** | pulled from another sheet/source | `#00B050` (green) | linked figures |
| **Error / broken** | a check failed or a link is dead | `#a23934` (red) | **errors only** |
| **Subtotal** | a roll-up line | `#6b7280` (Tufte grey) | subtotal/aggregate rows |

Hard rules that follow from this:

- **Blue means "a human typed this."** If a number is blue, a reader should be
  able to change it and watch everything recalculate. Never color a formula blue.
- **Red is reserved for errors**, never for negative values. A negative number
  is shown with parentheses, not red — see §2. Reaching for red to mean "bad
  number" destroys the provenance signal.
- **The driver convention is yellow fill + blue font**, not a third color.
- **Swatches in a legend are rectangles** (Excel-cell shape, `border-radius:2px`),
  never circles — they represent cells.

```css
.cell-input   { color:#0000FF; }
.cell-driver  { color:#0000FF; background:#FFFFCC; }
.cell-formula { color:#1a2330; }   /* default; usually no class needed */
.cell-link    { color:#00B050; }
.cell-error   { color:#a23934; }
.cell-subtle  { color:#6b7280; }   /* subtotal rows */
```

---

## 2. Negatives — parentheses, aligned

Accounting style: **negatives in parentheses, positives bare.** Never a leading
minus in a financial exhibit, never red-for-negative.

```
  1,240.0
   (340.0)
  5,150.0
```

The parentheses add width on only some rows, which throws the decimal alignment
off. Reserve the space on every row with invisible affixes so the digits line up
(the `.aff` trick, shared with `tables.md`):

```html
<td class="num"><span class="aff-l">(</span>1,240.0<span class="aff-r">)</span></td>
<td class="num">(340.0)</td>
```
```css
.aff-l, .aff-r { visibility:hidden; }
```

For a one-off inline value, `.pc-accounting` pairs with pre-formatted
parenthesized content: `<td class="num pc-accounting">($340)</td>`.

---

## 3. Precision — consistent down a column, scaled to magnitude

- **Same decimals for every cell in a column.** `$1,240.0` and `$3,910.5` in one
  column, `$1,240` and `$3,911` in another — never `$1,240` next to `$3,910.50`.
- **Scale precision to magnitude.** Billions → 1 decimal (`$4.2B`); millions → 0–1
  (`$340` / `$340.5mm`); per-unit / per-share → 2 (`$12.40`); percentages → 1
  (`18.2%`); multiples → 1 (`8.4x`); bps → 0 (`+320 bps`).
- **Round, don't truncate.** `$1,239.95M` → `$1,240.0M`.
- **One source of truth for rounding.** If subtotals are shown rounded, the
  displayed total should equal the sum of displayed parts, or carry a `*` note —
  never leave a visible `99.9 = 50 + 50` artifact unexplained.

---

## 4. Units and scale — state once, never repeat per cell

- **Declare the scale in the caption or column header**, not in every cell:
  *"Dollars in thousands unless noted"* or a `($mm)` header suffix. A column of
  `$1,240mm  $3,910mm  $5,150mm` is noise; `$ in millions` in the caption plus
  bare `1,240` is clean.
- **Currency symbol on the first row and the total**, optional in between, in a
  long column — or on every row if the table is short. Be consistent within the
  table.
- **Suffix scale** for mixed-magnitude one-liners only: `K`, `mm`/`M`, `B`,
  `T`. Pick one casing per repo (`mm` vs `M`) and never mix.

| Quantity | Format | Example |
|---|---|---|
| Currency | `$1,240` · `$1,240.0M` | thousands separator, scale in header |
| Percent | `18.2%` | one decimal, `%` attached |
| Multiple | `8.4x` | lowercase `x`, no space |
| Basis points | `+320 bps` | signed, space, `bps` |
| Change / delta | `+12.4%` · `(3.1%)` | sign explicit; parens if negative |
| Ratio | `2.1:1` or `2.1x` | pick one form per repo |

---

## 5. Zeros, dashes, and not-meaningful

- **True zero** in a financial exhibit is an em-dash `—`, not `0` or `0.0`, when
  it means "nothing here." Use a literal `0.0` only when zero is a real measured
  value that matters.
- **Not applicable** → `n/a`; **not meaningful** (e.g., a multiple off a negative
  base) → `n/m`. Both right-aligned like numbers, in the subtle grey.
- **Never leave a numeric cell empty** — it reads as a data error. Use `—`.

---

## 6. Type and alignment

- **Right-align every numeric column**, header included. Labels left, numbers
  right — always.
- **Tabular, lining numerals**, in the body sans font:
  `font-variant-numeric: tabular-nums lining-nums`. Tabular keeps digits in
  fixed columns so they stack; lining keeps them at cap height. This is what
  makes a column *look* like a column.
- **Do not default to monospace** for numbers. Tabular numerals in the body font
  read better than mono and match the surrounding type. Reserve `.mono` for
  codes, hashes, and IDs.
- **Slashed zero only when ambiguity genuinely matters** (an ID column mixing
  `0`/`O`), never on ordinary financial figures.

```css
.num, .pc-num { text-align:right; font-variant-numeric:tabular-nums lining-nums;
  font-feature-settings:"tnum","lnum"; }
```

---

## 7. CSS semantics (what `pagecraft.css` ships)

| Class | Purpose |
|---|---|
| `.num` / `.pc-num` | right-aligned tabular lining numerals (the base) |
| `.pc-money` | currency value |
| `.pc-pct` | percentage |
| `.pc-multiple` | multiples such as `8.4x` |
| `.pc-accounting` | financial-statement style; pair with `()` for negatives |
| `.pc-delta--pos` / `--neg` / `--flat` | semantic change values (up / down / flat) |
| `.cell-input` / `.cell-link` / `.cell-error` / `.cell-subtle` | provenance colors (§1) |
| `.aff-l` / `.aff-r` | invisible paren affixes for negative alignment |

```html
<td class="num pc-money cell-input">$1,240</td>   <!-- hardcoded assumption -->
<td class="num pc-money">$5,150</td>               <!-- formula (default ink) -->
<td class="num pc-accounting">($340)</td>          <!-- negative, accounting -->
<td class="num pc-pct">18.2%</td>
<td class="num pc-multiple">8.4x</td>
<td class="num pc-delta pc-delta--pos">+320 bps</td>
<td class="num cell-subtle">n/m</td>
```

---

## 8. Anti-patterns (the probe and review should flag these)

- Mixed decimal counts down a single column.
- Units (`mm`, `%`, `$`) repeated in every cell instead of stated once in the
  header/caption.
- Negative numbers shown in **red** or with a leading minus instead of parens.
- **Blue** applied to a formula, or **red** applied to a non-error — both break
  the provenance signal.
- Monospace on every number "to align them" — use tabular numerals instead.
- Left-aligned or center-aligned numeric columns.
- An empty numeric cell where `—` / `n/a` / `n/m` was meant.
- Slashed zeros on ordinary financial figures.

---

## Per-repo knobs (decide once, in the repo's style notes)

A few choices are genuinely house-preference rather than standard — fix them once
per repo and keep them consistent:

- Default currency **scale + suffix casing** (`$mm` vs `$M`; thousands vs millions).
- Whether the **currency symbol** repeats every row or only first/total.
- Decimal places for the repo's most common magnitude.

Everything else above is the standard and should not vary table to table.
