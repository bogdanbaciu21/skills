---
name: pagecraft
description: Portable HTML formatting and visual-safety bundle for static HTML, portal pages, dashboards, blog posts, and one-off deliverables. Use when creating or reviewing HTML/CSS that needs robust tables, financial number formatting, headers/section dividers, or text-wrap prevention. Bundles the real wrap-safe probe + verify-text-wrap runner + keystone guard so you validate with proven tools, not hand-rolled checks.
---

# Pagecraft

Pagecraft is a portable HTML finishing **bundle**: a comprehensive stylesheet
plus the *real, proven* verifiers — vendored in so one install gives you the
whole toolchain. It exists so you stop hand-fixing the same table, number,
header, and text-wrap bugs in every repo.

It does not reinvent the checks. It bundles them:

- **`wrap-safe`** — the CSS keystone/reset and the `wrapcheck.js` runtime probe.
- **`verify-text-wrap`** — the `runner.py` browser verifier (8 viewports + the
  right-edge "magician's divider" check) and the deterministic `check-keystone.py`.
- For migrating a messy table estate to one canonical component, reach for the
  **`table-system-migration`** skill alongside this bundle.

## Operating model

1. **Install or inspect first.** `sh install-pagecraft.sh <repo-root>`
   copies the CSS, probe, and verifiers in, writes
   `tests/pagecraft/pagecraft-install.json`, and runs a deterministic
   `check-keystone.py` self-test against the copied CSS. The manifest records
   the source git commit when the installer is run from a git checkout. If the
   repo already has a design system, adapt class names/variables instead of
   replacing it.
2. **Use the references as needed.**
   - Tables: `references/tables.md` (the `.bbt` system + when to use `table-system-migration`)
   - Text wrap: `references/text-wrap.md`
   - Number formats: `references/number-formats.md`
   - Headers / section dividers: `references/headers.md`
   - Lifted flourish inventory: `references/flourishes-lift.md` · Backlog: `references/future-ideas.md`
3. **Prefer the bundled primitives before new CSS.** `.pc-grid`, `.pc-card-grid`,
   `.bbt` (+ `.pc-table` alias), `.pc-section-break`, `.pc-chapter`,
   `.pc-heading-anchor` (the always-on gutter bar), `.pc-eyebrow`, `.num`, the
   `.cell-*` Macabacus provenance colors, etc. Raw grid/table CSS is a code smell.
4. **Validate with the bundled tools — two layers, both required.** The probe and
   verifiers live in the sibling `verify-text-wrap` skill (see its SKILL.md for
   full options):

```bash
# Deterministic root-cause guard (no browser, CI-safe, never flakes):
python3 ../verify-text-wrap/check-keystone.py --portal <static-html-root>

# Real-browser probe across 8 viewports + right-edge alignment:
python3 ../verify-text-wrap/runner.py --local --portal <static-html-root> \
  --known-issues tests/pagecraft/wrap-known-issues.json
```

New repos: both strict from day one. Legacy repos: run once, normalize the
obvious bad primitives, allowlist only confirmed non-defects, then ratchet.

## Minimal adoption path for legacy repos

When a repo already has substantial HTML/CSS debt, do the smallest useful
installation first:

1. Install Pagecraft and commit only the copied assets, scripts, manifest, and
   known-issues scaffold.
2. Add only `wrap-safe.css` or the single keystone rule to the existing global
   stylesheet.
3. Run `check-keystone.py` and fix missing-root-cause failures.
4. Run `runner.py` on 1-3 priority pages and allowlist only confirmed non-defects.
5. Convert tables/grids opportunistically as pages are touched; do not attempt a
   full estate migration unless `table-system-migration` is explicitly in scope.

## Update or uninstall

- **Update:** rerun `sh install-pagecraft.sh <repo-root>` from the latest skills
  checkout, then review `tests/pagecraft/pagecraft-install.json` and the copied
  asset diff. Keep local known-issues files unless you intentionally reset the
  ratchet.
- **Uninstall:** remove the copied paths listed in
  `tests/pagecraft/pagecraft-install.json`, remove stylesheet/script references
  from the target app, and then delete `tests/pagecraft/pagecraft-install.json`.
  Do not delete the target repo's own table CSS or known-issues file unless you
  confirmed they were created solely for Pagecraft.

## Which subskill should I use?

| Need | Use | Start here |
|---|---|---|
| Install the bundle or finish one static HTML surface | `pagecraft` | `install-pagecraft.sh`, then these references |
| Prove wrap/container safety after CSS or deploy | `verify-text-wrap` | `../verify-text-wrap/SKILL.md` |
| Normalize many ad hoc tables into one system | `table-system-migration` | `../table-system-migration/SKILL.md` |
| Format financial numbers in HTML or Excel | `number-formats` | `../number-formats/SKILL.md` |
| Apply an existing repo design system across pages | `reskin` | `../reskin/SKILL.md` |

## Key rules

- **The keystone is the #1 wrap rule:** `* { min-width: 0 }` (shipped in
  `pagecraft.css`). Text-wrap bugs are bad containers, not bad text.
- Don't use `repeat(3, 1fr)` / `repeat(3, minmax(0,1fr))` for text cards — use
  `repeat(auto-fit, minmax(220px, 1fr))` or a wider floor.
- Don't cap ordinary prose with `max-width: NNch`; the page container owns width.
- Don't apply `hyphens: auto`, `word-break: break-all`, or `text-wrap: pretty/balance`
  to ordinary prose as a "fix" — the probe fails them.
- Tables get explicit `.bbt-wrap` wrappers, captions, numeric alignment, total
  rows, source lines, and print behavior — never `<figure>`, never per-post classes.
- Numbers follow the Macabacus convention: color encodes provenance, negatives
  use parentheses (not red), units stated once in the header.
- Every exception needs a same-line reason: `/* wrap-exempt: metric-only KPI grid */`.

## What's in the bundle

Pagecraft is a multi-skill plugin. Each member skill is self-contained (it owns
its own tools — no copies shared or vendored between skills):

```
pagecraft/                          the plugin
├─ .claude-plugin/plugin.json       plugin manifest
└─ skills/
   ├─ pagecraft/                    THIS overview skill
   │  ├─ SKILL.md
   │  ├─ install-pagecraft.sh       install the bundle into another repo
   │  ├─ assets/css/pagecraft.css   comprehensive stylesheet: keystone, .bbt
   │  │                             tables, number formats + Macabacus colors,
   │  │                             safe grids, headers, callouts, focus, print
   │  ├─ assets/wrap-lab/*.html     synthetic good/bad fixtures for the checker
   │  └─ references/*.md            tables, text-wrap, number-formats, headers, …
   ├─ verify-text-wrap/             the wrap probe + verifiers (canonical home)
   │  ├─ runner.py                  browser verifier (8 viewports + right-edge)
   │  ├─ check-keystone.py          deterministic keystone guard (no browser)
   │  ├─ browserbase.py             optional Browserbase backend for runner.py
   │  ├─ wrap-safe.css              minimal drop-in reset (the wrap-safe library)
   │  └─ wrapcheck.js               the wrap-safe runtime probe
   ├─ table-system-migration/       audit/migrate a messy table estate to `.bbt`
   └─ number-formats/               Macabacus financial number-format standard
      ├─ apply-number-formats.py    openpyxl applicator
      └─ formats.json               byte-exact Excel format codes
```

The probe and verifiers have a single canonical home in `verify-text-wrap/` —
`install-pagecraft.sh` copies from there. Nothing is vendored or duplicated, so
nothing can drift.

Installed into a target repo, the default paths are:

```
assets/css/pagecraft.css              Pagecraft stylesheet
assets/css/wrap-safe.css              minimal keystone reset
assets/wrapcheck.js                   page-load/runtime probe copy
scripts/wrapcheck.js                  verifier-local probe copy
scripts/check-keystone.py             deterministic keystone guard
scripts/runner.py                     browser verifier
scripts/browserbase.py                optional Browserbase backend
tests/pagecraft/wrap-lab/*.html       synthetic good/bad fixtures, if present
tests/pagecraft/wrap-known-issues.json allowlist scaffold
tests/pagecraft/pagecraft-install.json copied asset manifest + self-test command
```

## Portability

1. Add the assets and scripts (`install-pagecraft.sh`).
2. Add a token shim if the repo lacks `--ink`, `--paper`, `--rule`, `--accent`,
   `--navy` (every bundled rule has a hardcoded fallback, so this is optional).
3. Convert tables and text-bearing grids to the bundled classes.
4. Keep `bad-*` wrap-lab fixtures out of production sweeps.
5. Wire `check-keystone.py` into pre-commit/CI and `runner.py` into the
   post-deploy check before the first serious page build.

## Skill maintenance

When editing the installer, run:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 evals/install_pagecraft_eval.py
```
