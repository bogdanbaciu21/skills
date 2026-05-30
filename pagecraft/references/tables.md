# Tables Subskill

## House Pattern

Use a wrapper plus a table class:

```html
<figure class="pc-table-figure">
  <figcaption class="pc-table-cap">
    <span class="pc-table-eb">Model output</span>
    <span class="pc-table-ti">Unit economics by case</span>
    <span class="pc-table-sub">Dollars in thousands unless noted.</span>
  </figcaption>
  <div class="pc-table-wrap">
    <table class="pc-table">
      <thead>
        <tr><th>Case</th><th class="num">Revenue</th><th class="num">Margin</th></tr>
      </thead>
      <tbody>
        <tr><td>Base</td><td class="num">$1,240</td><td class="num">18.2%</td></tr>
        <tr class="tot"><td>Total</td><td class="num">$1,240</td><td class="num">18.2%</td></tr>
      </tbody>
    </table>
  </div>
  <p class="pc-table-source"><span>Source:</span> Management case; Dan analysis.</p>
</figure>
```

## Required Conventions

- Use `.pc-table-wrap` for horizontal overflow; never make the table itself `display:block`.
- Use `.num` or `.r` on numeric cells and headers.
- Use `.tot` for total/subtotal rows.
- Use `.pc-table--synth` for dense comparison tables.
- Use `.pc-table--attr` for parent/leaf attribution tables.
- Use `.pc-table-source` for source notes, not a loose paragraph.
- Preserve `.bbt` / `.bbt-wrap` compatibility when working in Bogdan-derived repos.

## Auditing Rules

- A naked `<table>` in production content is suspicious unless the design system already handles it.
- Tables must have a caption, nearby heading, or explicit source/context line.
- Numeric columns should use tabular numerals and right alignment.
- Wide tables scroll inside a wrapper and print without clipping.
