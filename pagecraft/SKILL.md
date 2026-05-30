---
name: pagecraft
description: Portable HTML formatting, editorial polish, and visual-safety guardrails for static HTML, portal pages, dashboards, blog posts, and one-off deliverables. Use when Codex is creating or reviewing HTML/CSS that needs robust tables, financial number formatting, headers/section dividers, text-wrap prevention, reusable formatting primitives, or repo-wide installable checks.
---

# Pagecraft

Pagecraft is Dan's portable HTML finishing system: reusable patterns plus deterministic checks that keep static pages polished without hand-fixing the same table, header, number, and text-wrap bugs in every repo.

## Operating Model

1. **Install or inspect first.** If the repo does not have Pagecraft assets, use `scripts/install-pagecraft.sh <repo-root>` or copy the needed assets manually. If it has an existing design system, adapt the class names and variables instead of replacing the whole system.
2. **Use subskill references as needed.**
   - Tables: `references/tables.md`
   - Headers and section dividers: `references/headers.md`
   - Text wrap: `references/text-wrap.md`
   - Number formats: `references/number-formats.md`
   - Lifted flourish inventory: `references/flourishes-lift.md`
   - Future backlog: `references/future-ideas.md`
3. **Prefer Pagecraft primitives before new CSS.** Use `.pc-grid`, `.pc-card-grid`, `.pc-table`, `.pc-section-break`, `.pc-eyebrow`, `.pc-num`, etc. Raw grid and table CSS is a code smell unless the page has a real one-off layout need.
4. **Validate before calling it done.** Run the deterministic policy, then the browser probe when available:

```bash
sh scripts/check-pagecraft-policy.sh --full
python3 scripts/check-text-wrap.py --root <static-html-root>
```

For newly-created repos, make both strict from day one. For legacy repos, run once, normalize the obvious bad primitives, allowlist only confirmed non-defects, then ratchet.

## Key Rules

- Text wrap bugs are usually bad containers, not bad text. Fix grid/width primitives first.
- Do not use `repeat(3, 1fr)` or `repeat(3, minmax(0, 1fr))` for text-bearing cards. Use `repeat(auto-fit, minmax(220px, 1fr))` or wider.
- Do not cap ordinary prose with `max-width: NNch` inside wide page containers. Let the page/content container own width.
- Do not apply `hyphens: auto`, `word-break: break-all`, or `text-wrap: pretty/balance` to ordinary prose as a "fix".
- Tables get explicit wrappers, captions, numeric alignment, total rows, source lines, and print behavior.
- Header/divider flourishes should carry structure: eyebrow, title, deck, rule, section counter, anchor affordance. Avoid decorative marks that do not help scanning.
- All exceptions need a same-line reason comment such as `/* wrap-exempt: metric-only KPI grid */`.

## Bundled Assets

- `assets/css/pagecraft.css`: portable CSS primitives for tables, headers, numbers, callouts, figures, focus, print, and safe grids.
- `assets/wrapcheck-pagecraft.js`: stable browser probe for collapsed/narrow text boxes and long-page allowlisting.
- `assets/wrap-lab/*.html`: synthetic good/bad fixtures for testing the checker without preserving broken pages in production.

## Scripts

- `scripts/install-pagecraft.sh`: install CSS, wrap probe, fixtures, and checks into another repo.
- `scripts/check-pagecraft-policy.sh`: deterministic source-level guard for risky width, grid, typography, and table patterns.
- `scripts/check-text-wrap.py`: local Playwright sweep that injects the bundled wrap probe and checks right-edge alignment.

## Portability Discipline

When moving this into a repo:

1. Add the assets and scripts.
2. Add a small design-token shim if the repo lacks variables like `--ink`, `--paper`, `--rule`, `--accent`, `--navy`.
3. Convert tables and text-bearing grids to Pagecraft classes.
4. Add synthetic wrap lab fixtures but exclude failing `bad-*` fixtures from production sweeps.
5. Wire deterministic checks into pre-commit/pre-push/CI before the first serious page build.
