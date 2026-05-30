# Tables Reference — the `.bbt` system

A production-grade HTML table system for finance, cost, vendor, audit, and
comparison tables: dense information without spreadsheet ugliness, readable on a
phone, and printable. This is the `.bbt` ("blackboard table") v6 pattern.
`pagecraft.css` bundles the core; every layer below ships its own CSS inline so
you can build the whole system from this file in any repo.

> **Canonical vocabulary is `.bbt` + `.bbt-wrap`.** `pagecraft.css` also exposes
> `.pc-table` / `.pc-table-wrap` as identical aliases for teams that want a
> neutral prefix. Pick one per repo and never mix — a table system with two
> names is the #1 source of table drift.

---

## The contract (memorize this shape)

```html
<div class="bbt-cap">
  <span class="eb">Annual run-rate · estimate</span>
  <span class="ti">Cost to serve, by tier</span>
  <span class="sub">Dollars in thousands unless noted.</span>
</div>

<div class="bbt-wrap">
  <table class="bbt">
    <colgroup>
      <col class="c-label"><col class="c-num"><col class="c-num">
    </colgroup>
    <thead>
      <tr><th>Tier</th><th class="num">Revenue</th><th class="num">Margin</th></tr>
    </thead>
    <tbody>
      <tr><td class="label">Base</td><td class="num">$1,240</td><td class="num">18.2%</td></tr>
      <tr><td class="label">Plus</td><td class="num">$3,910</td><td class="num">24.6%</td></tr>
      <tr class="tot"><td>Total</td><td class="num">$5,150</td><td class="num">22.9%</td></tr>
    </tbody>
  </table>
</div>

<p class="bbt-source">
  <span class="src-label">Source:</span>
  <span class="src-body">Management model; analyst estimates.</span>
</p>
```

Three parts, always in this order: **caption block → wrapped table → source
line.** The wrapper `div.bbt-wrap` is mandatory — it is the horizontal-scroll
container and the thing that lets a wide table exist without blowing out the
page. **Never wrap a data table in `<figure>`** (that element is reserved for
SVG diagrams and images; its default margin plus prose styles collapse the
table to the width of its longest cell).

---

## Core CSS

```css
/* Caption: eyebrow + serif title + italic subtitle, hairline divider */
.bbt-cap { margin-bottom:14px; padding-bottom:12px; border-bottom:1px solid var(--rule,#d8d1c0); }
.bbt-cap .eb  { display:block; font:700 10px/1.2 var(--sans,Inter,sans-serif); letter-spacing:.14em; text-transform:uppercase; color:var(--accent,#2f7a6a); margin-bottom:4px; }
.bbt-cap .ti  { display:block; font:500 22px/1.2 var(--serif,"EB Garamond",serif); color:var(--ink,#1a2330); }
.bbt-cap .sub { display:block; margin-top:4px; font:italic 14px var(--serif,"EB Garamond",serif); color:var(--ink-soft,#4a5260); }

/* Wrapper: horizontal scroll + a right-edge fade that signals "more →" */
.bbt-wrap { position:relative; overflow-x:auto; -webkit-overflow-scrolling:touch; }
.bbt-wrap::after { content:""; position:absolute; inset:0 0 0 auto; width:24px;
  background:linear-gradient(to right, transparent, var(--paper,#fbf8f1));
  pointer-events:none; opacity:0; transition:opacity .2s; }
.bbt-wrap.has-overflow::after { opacity:1; }   /* toggle via JS when scrollWidth > clientWidth */

/* The table */
table.bbt { width:100%; border-collapse:collapse; table-layout:fixed;
  font:14px/1.5 var(--sans,Inter,sans-serif); color:var(--ink,#1a2330); margin:0; }
table.bbt col.c-label { width:60%; }
table.bbt col.c-num   { width:20%; }

/* Header — dark, uppercase, LEFT-aligned (the explicit fix for <th>'s center default) */
table.bbt thead th { background:var(--navy,#1a2330); color:#fff;
  font:700 12px var(--sans,Inter,sans-serif); letter-spacing:.06em; text-transform:uppercase;
  text-align:left; padding:8px; vertical-align:bottom; white-space:nowrap; border:none; }
table.bbt thead th.num, table.bbt thead th.r { text-align:right; }

/* Body cells — wrap like prose; numeric cells are the exception */
table.bbt tbody td { padding:8px; border-top:1px solid var(--rule,#d8d1c0); vertical-align:top;
  overflow-wrap:break-word; word-break:normal; hyphens:manual; }
table.bbt tbody tr:first-child td { border-top:none; }
table.bbt tbody tr:nth-child(even) td { background:var(--paper-w,#fbf8f1); }        /* zebra */
table.bbt tbody tr:last-child:not(.tot) td { border-bottom:1px solid var(--rule,#d8d1c0); }
table.bbt tbody td.num, table.bbt tbody td.r {
  text-align:right; white-space:nowrap;
  font-variant-numeric:tabular-nums lining-nums; font-feature-settings:"tnum","lnum"; }

/* Total row — 2px rule above, cream fill, bold; same height as body */
table.bbt tbody tr.tot td { background:var(--paper-m,#f5efdf); color:var(--navy,#1a2330);
  font-weight:700; border-top:2px solid var(--navy,#1a2330); border-bottom:none; }

/* Row hover — applies to zebra and total rows too */
table.bbt tbody tr:hover td { background:rgba(26,35,48,.09); transition:background .1s; }

/* Source line — "Source:" upright, body italic, links underlined to the rule color */
.bbt-source { margin:12px 0 0; font:13px var(--serif,"EB Garamond",serif); color:var(--ink-soft,#4a5260); }
.bbt-source .src-label { font-style:normal; font-weight:500; }
.bbt-source .src-body  { font-style:italic; }
.bbt-source a { color:inherit; text-decoration:underline; text-decoration-color:var(--rule,#d8d1c0); text-underline-offset:2px; }
```

**Layout law:** `table-layout: fixed` + a `<colgroup>` for any table with ≥ 4
columns, or any table where one cell's content would otherwise stretch a column.
Fixed layout is what makes the table fill its wrapper instead of collapsing to
the longest cell. Numeric columns get `.num` (right-aligned, tabular, no-wrap);
label/prose columns wrap normally. **Never** put `white-space: nowrap` on a
cost / vendor / prose column — that is what makes a table sprawl horizontally.

---

## Numeric alignment — the Macabacus paren trick

Negatives in accounting style `($340)` misalign against positives `$1,240`
because the parentheses add width on only some rows. Reserve the space on every
row with invisible affixes so the digits line up:

```html
<td class="num"><span class="aff-l">(</span>$1,240<span class="aff-r"> </span></td>
<td class="num">(<span>$340</span>)</td>
```
```css
.aff-l, .aff-r { visibility:hidden; }   /* reserves width without printing the glyph */
```

See `number-formats.md` for the full numeric convention (negatives, units,
multiples, bps, zeros/NA, Macabacus color semantics).

---

## Annotation layers (add only when the table needs them)

**L1 — footnotes.** Superscript marker in a row label, numbered list below:
```html
<td class="label">Adjusted EBITDA<sup class="bbt-fn">1</sup></td>
…
<ol class="bbt-footnotes"><li>Excludes one-time restructuring.</li></ol>
```
```css
.bbt-fn { font:italic 500 10.5px var(--serif,"EB Garamond",serif); color:var(--accent,#2f7a6a); vertical-align:super; line-height:0; margin-left:2px; }
ol.bbt-footnotes { margin:16px 0 0; padding-left:22px; font-size:13.5px; line-height:1.6; color:var(--ink-soft,#4a5260); }
```

**L4 — methodology note.** A narrative box under the table:
```css
.bbt-methodology { margin-top:16px; padding:14px 18px; background:var(--paper-deep,#f3ecd8);
  border-left:3px solid var(--accent,#2f7a6a); border-radius:0 6px 6px 0; font-size:14px; line-height:1.7; color:var(--ink-soft,#4a5260); }
.bbt-methodology .label { display:block; font:700 10px var(--sans,Inter,sans-serif); letter-spacing:.12em; text-transform:uppercase; color:var(--accent,#2f7a6a); margin-bottom:5px; }
```

**Multi-period group headers.** A spanning band over period sub-columns:
```html
<thead>
  <tr class="grp-row"><th></th><th class="grp" colspan="2">FY2024</th><th class="grp" colspan="2">FY2025</th></tr>
  <tr><th>Metric</th><th class="num">Q3</th><th class="num">Q4</th><th class="num">Q3</th><th class="num">Q4</th></tr>
</thead>
```
```css
table.bbt thead tr.grp-row th.grp { background:var(--navy,#1a2330); color:#fff; text-align:center;
  font:700 12px var(--sans,Inter,sans-serif); text-transform:uppercase; letter-spacing:.06em; padding:8px 8px 4px; }
table.bbt thead tr.grp-row + tr th { background:var(--navy,#1a2330); padding-top:4px; }
```

---

## Long tables after a callout — collapse, don't dump

When a summary card or short answer already answers the question, the full
vendor-by-vendor table is *detail*, not the page. Collapse it by default in a
native `<details>` (no JavaScript), with a row-count hint in the toggle:

```html
<details class="bbt-fold">
  <summary>
    <span><b>Detailed cost table</b><span>Collapsed by default — open for the full vendor-by-vendor detail.</span></span>
    <span class="bbt-fold-pill">34 rows</span>
  </summary>
  <div class="bbt-wrap"><table class="bbt">…</table></div>
</details>
```
```css
.bbt-fold { margin:16px 0; border:1px solid var(--rule,#d8d1c0); border-radius:10px; overflow:hidden; }
.bbt-fold > summary { cursor:pointer; list-style:none; display:grid; grid-template-columns:minmax(0,1fr) auto; gap:12px; align-items:center; padding:13px 15px; }
.bbt-fold > summary::-webkit-details-marker { display:none; }
.bbt-fold > summary b { display:block; font-size:14px; color:var(--ink,#1a2330); }
.bbt-fold > summary span span { display:block; margin-top:3px; font-size:12px; color:var(--ink-soft,#4a5260); }
.bbt-fold-pill { border:1px solid var(--rule,#d8d1c0); border-radius:999px; padding:4px 8px; font:700 10px/1.2 var(--mono,ui-monospace,monospace); letter-spacing:.08em; text-transform:uppercase; white-space:nowrap; color:var(--accent,#2f7a6a); }
```

---

## Modifiers

- **`.bbt--attr`** — parent/leaf attribution (decompositions, bridges). `tr.par`
  is bold navy on a tinted row; `tr.leaf td:first-child` indents 22px; `td.pp`
  (positive %) is green, `td.pn` (negative %) is the accent.
- **`.bbt--synth`** — dense comparison / synthesis strip. `table-layout:auto`,
  `min-width:540px`, smaller (9.5px) softer header, bottom borders instead of
  top, middle-aligned cells with an optional `.c` center utility. Use for a
  many-column cross-entity reference, not a primary numeric table.

Cell helpers, never utility-class soup: `.num` (right, tabular), `.r` (right),
`.label` (emphasized first column), `.mono` (monospace), `.nowrap`. A
section-divider row is `<tr class="section-row">`; a total is `<tr class="tot">`.

---

## Hard rules

1. **Never `<figure>` around a data table.** Use `.bbt-wrap`. `<figure>` is for
   diagrams and images only.
2. **Never invent a per-post `.foo-tbl` class** in a page `<style>` block. If the
   system is missing something, add the modifier to the shared CSS so every
   future table inherits it.
3. **If a table reads narrow with dead space on the right, the bug is the
   wrapper or `table-layout`, not the data.** Fix `table-layout: fixed`, the
   `<colgroup>`, and the `.bbt-wrap` div — do not reflow or pad the content.
4. **Wider-than-wrapper content scrolls**, it never escapes the column:
   `.bbt-wrap` has `overflow-x:auto`. A `min-width:1500px` table inside a
   1144px column scrolls horizontally; it does not blow out the page.
5. **Embedded in an article?** The host wrapper sizes the table; no `100vw` /
   `margin-left:50%` / `translateX(-50%)` viewport math inside an embedded
   table — that breaks in a centered article and is neutralized anyway.

---

## Validate

- Right-align + tabular numerals on every numeric column; no monospace numerics
  by default; no slashed zero unless ambiguity genuinely matters.
- A table has a caption (or nearby heading) and a source/context line — a naked
  `<table>` in production content is suspicious.
- Run the wrap probe (see `text-wrap.md`): a table must not caterpillar, must
  scroll (not overflow) when wider than its column, and must print without
  clipping. Mount one fixture per table shape — content table, numeric exhibit,
  grouped-header, total row, `--synth` — so a change for one never silently
  breaks another.
