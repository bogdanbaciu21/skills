# Number Formats Subskill

This is intentionally a starter surface. Dan's final preferences are TBD, but every repo should already reserve clean semantics for numeric formatting.

## CSS Semantics

- `.pc-num` / `.num`: tabular lining numerals.
- `.pc-money`: right-aligned currency value.
- `.pc-pct`: right-aligned percentage.
- `.pc-multiple`: multiples such as `8.4x`.
- `.pc-delta--pos`, `.pc-delta--neg`, `.pc-delta--flat`: semantic deltas.
- `.pc-accounting`: financial statement style; pair with parentheses for negatives when content is preformatted.

## HTML Examples

```html
<td class="pc-num pc-money">$1,240</td>
<td class="pc-num pc-accounting">($340)</td>
<td class="pc-num pc-pct">18.2%</td>
<td class="pc-num pc-multiple">8.4x</td>
<td class="pc-num pc-delta pc-delta--pos">+320 bps</td>
```

## Rules

- Align numeric columns right.
- Use tabular numerals for tables, KPIs, and dashboards.
- Do not use monospace for every number by default; tabular numerals in the body font usually look better.
- Use slashed zero only when ambiguity matters.
- Put units in headers or captions when possible, not repeated in every cell.
