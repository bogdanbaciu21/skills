# HTML Quality Gates

Run these gates proportionally. A small internal artifact may need static checks
only; a public/client page or layout-risky dashboard needs browser/render proof.

## Text Wrap

Fix wrap bugs in this order:

1. Container ownership and grid/flex tracks.
2. Universal `min-width: 0` keystone.
3. Safe grid floors such as `repeat(auto-fit, minmax(220px, 1fr))`.
4. Prose reset: the page/container owns width, not individual paragraphs.

Do not use `word-break: break-all`, `hyphens: auto`, or `text-wrap: pretty` as
the first fix. They hide container bugs and create new ones.

## Tables

- Use real `<table>` markup for tabular data.
- Use a wrapper such as `.bbt-wrap` for dense tables.
- Include captions or nearby source/provenance lines.
- Keep status text-readable, not color-only.
- Use explicit headers, row labels, total/subtotal rows, and print behavior when
  the page is a report.

## Numbers

- Right-align numeric columns, including headers.
- Use tabular lining numerals, not monospace by default.
- State units once in the header/caption.
- Use consistent decimals down a column.
- Use parentheses for negatives, not red.
- Use red for errors only.
- Use provenance colors intentionally: blue means human input, green means linked
  source, default ink means formula/derived value.
- Use `n/a`, `n/m`, or a dash for missing/not-meaningful values. Do not leave
  numeric cells blank.

## UI States

Data-bearing UI must have explicit states:

- loading
- empty
- error
- populated
- edge case such as long text, zero rows, negative values, or stale source

Use existing Pagecraft/UX OS primitives before one-off boxes.

## Static Checks

For one or more generated HTML files:

**VPS Hetzner -- ssh shell**

```bash
cd /root/dans-brain
python3 bin/pagecraft_qa.py --html path/to/artifact.html
```

For a static root:

**VPS Hetzner -- ssh shell**

```bash
cd /root/dans-brain
python3 bin/pagecraft_qa.py --portal path/to/static-root --write
```

For a Builder branch or visual diff:

**VPS Hetzner -- ssh shell**

```bash
cd /root/dans-brain
python3 bin/builder_output_review.py --base origin/main --head HEAD --write
```

For Dan/Bogdan-branded HTML:

**VPS Hetzner -- ssh shell**

```bash
cd /root/dans-brain
python3 bin/brand_lint.py path/to/artifact.html
```

## Browser/Render Proof

Run browser or deployed-page proof when:

- the page is public or client-facing
- CSS/layout changed substantially
- a user reported wrap or overlap
- the page has tables, sticky controls, responsive panels, or charts
- Builder made visual edits that source checks cannot prove

If no browser runtime is available, say so directly and name the residual risk.
