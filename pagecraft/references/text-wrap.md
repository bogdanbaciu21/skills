# Text Wrap Subskill

## Goal

Prevent unreadable "caterpillar" text, phantom right edges, and collapsed containers before they reach a live page.

## Safe Defaults

- Use `.pc-grid` / `.pc-card-grid` for text cards:

```css
grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
```

- Use wider floors for prose-heavy cards: `260px`, `280px`, or `320px`.
- Let page wrappers own width. Do not put `max-width: 72ch` on `p`, `li`, `.lede`, `.summary`, or `.prose` elements unless the entire page is intentionally a reading column.
- Keep ordinary prose predictable:

```css
overflow-wrap: break-word;
word-break: normal;
hyphens: manual;
text-wrap: wrap;
```

## Source-Level Bans

Flag these unless an inline `wrap-exempt:` reason exists:

- `grid-template-columns: repeat(3, 1fr)` or higher
- `repeat(3, minmax(0, 1fr))` or higher
- `repeat(auto-fit, minmax(<220px, 1fr))`
- `max-width: NNch` on ordinary page/prose CSS
- `word-break: break-all`
- `hyphens: auto`
- `text-wrap: pretty` or `text-wrap: balance` on ordinary prose

## Validation

Run:

```bash
sh scripts/check-pagecraft-policy.sh --full
python3 scripts/check-text-wrap.py --root <static-html-root>
```

Use `tests/pagecraft/wrap-known-issues.json` only for confirmed non-defects, such as intentionally long archive/transcript pages that trip a page-height heuristic.
