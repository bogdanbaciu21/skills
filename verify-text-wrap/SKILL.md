---
name: verify-text-wrap
description: Verify a static-HTML portal has no caterpillar text-wrap, ugly hyphenation, display-text orphan lines, narrow-card prose, horizontal overflow, or container-collapse bugs, both locally and against the deployed URL. Use after any CSS edit, after any deploy, or when the user reports "the text wrapping is broken" / "this looks off" / "random text wrapping" / "phantom right edge" / "magician divider". Runs the wrap-safe runtime probe across desktop/tablet/mobile viewports plus a right-edge alignment check that catches container-vs-element max-width mismatches. Compares findings against a per-repo `tests/wrap-known-issues.json` allowlist if present. Do NOT use for generic CSS bugs unrelated to text wrapping or container width.
---

# verify-text-wrap

A protocol for confirming a static-HTML portal renders correctly across viewport widths after CSS or markup changes. Pairs with the `wrap-safe` library (CSS reset + runtime probe) — same author, expected to be installed alongside under `skills/wrap-safe/`.

Default runner coverage is intentionally strict: `wide` 1440x900, `laptop` 1024x900, `tablet` 768x900, and `mobile` 390x844. One viewport is not enough; many ugly wrap bugs appear only when a two-column card is squeezed at laptop width or when a mobile header gets too narrow.

## When to invoke

- **After any CSS edit** touching `display`, `width`, `max-width`, `flex`, `grid`, `padding`, `margin`, `text-wrap`, `hyphens`, `word-break`, `overflow-wrap`, or any selector containing `p`, `li`, `h1-h6`, `td`, `th`, `article`, `main`, `section`, `.doc`, `.article`, `.prose`, `.tile`, `.kpi`.
- **After deploying to any host** (Netlify, Vercel, etc.). Build-time tests pass against local; the deployed render is where CDN cache, font race conditions, and real network conditions show up.
- **When the user reports** any of: "text wrapping", "wraps weird", "random text wrap", "phantom right edge", "magician divider", "caterpillar text", "h2 underline runs past my paragraphs", "text stops in a weird place".

## Hard rule — don't reach for text-wrap / hyphens / word-break

The root cause of visible text-wrap weirdness is almost always upstream container collapse, a too-narrow component column, or container-vs-element max-width mismatch. It is not fixed by clever browser typography. Do NOT add `text-wrap: balance`, `text-wrap: pretty`, `hyphens: auto`, or `word-break: break-all` as a fix. They create new bugs and the hardened probe now fails them.

Correct diagnostic order:

1. **Run the wrap-safe probe across default viewports** (`window.__wrapcheck()` in the browser console for a single page, or this runner for real work). Catches caterpillar paragraphs, narrow prose containers, short-text-in-narrow-box wraps, heading line-count anomalies, display-text orphan lines, banned typography rules, dense prose in narrow columns, and horizontal overflow.
2. **Measure right-edge alignment.** Main-flow prose elements (h1-h6, p, li, blockquote) should share a single right-X coordinate. If they don't, the container is wider than the prose cap and the user perceives a phantom vertical line where text wraps but section dividers or h2 underlines extend further. Framed cards/panels/notes are skipped because they own their own padding box.
3. **Look at the deployed page**, not just the local test. Tests catch the known bug classes; the user's eye catches everything else. Always open the live URL after pushing.

## Invocation

The runner is parametrized — no project-specific values in this skill. The consuming repo supplies its own gate session-storage key, password (for deployed mode), and known-issues path.

### Local mode

```
python3 <skill-dir>/runner.py --local \
  --portal <relative-or-absolute-path-to-static-html-dir> \
  --gate-key <sessionStorage-key-the-portal-gate-uses> \
  --known-issues <path-to-tests/wrap-known-issues.json>
```

Spins up an in-process `http.server` over the portal directory so `fetch()`-based pages (markdown renderers, etc.) work — `file://` blocks fetch and produces false-clean results. Headless Chromium via Playwright. The runner sets the gate key in both `sessionStorage` and `localStorage`, because portals vary.

Navigation waits for `domcontentloaded` by default, then the probe waits briefly before measuring. That keeps portal-wide static sweeps fast while still letting charts/images settle enough for wrap measurement. Use `--wait-until load` or `--wait-until networkidle` only for a page that truly needs it. Use `--settle-ms 0` or `--settle-ms 250` for a fast full-estate static ratchet; use a higher value for chart-heavy pages.

### Deployed mode

```
python3 <skill-dir>/runner.py --deployed <deployed-url> \
  --gate-key <sessionStorage-key-the-portal-gate-uses> \
  --gate-password <password> \
  --known-issues <path-to-tests/wrap-known-issues.json>
```

Drives the live URL — pre-unlocks the gate via `sessionStorage`, runs the probe, runs the right-edge check, screenshots each page. Catches deploy-vs-local drift.

To narrow coverage while debugging, pass viewport presets or explicit sizes:

```
python3 <skill-dir>/runner.py --deployed <deployed-url> \
  --pages /target.html \
  --viewports laptop mobile

python3 <skill-dir>/runner.py --local --portal portal \
  --pages target.html \
  --viewports 1280x900,390x844
```

Default `wrapcheck.js` source is the local sibling file at `../wrap-safe/wrapcheck.js` so skill edits take effect immediately even against deployed URLs. Pass `--wrapcheck-url https://.../wrapcheck.js` only when intentionally testing the CDN copy.

For a full-estate ratchet where screenshots would be too heavy, disable them:

```
python3 <skill-dir>/runner.py --local --portal portal --screenshot-dir '' --settle-ms 250
```

If Browserbase MCP is configured (`BROWSERBASE_API_KEY` + `BROWSERBASE_PROJECT_ID` + an LLM provider key for Stagehand), deployed mode opens a Browserbase session in parallel as additional incremental check coverage. Falls back transparently to local Playwright if any Browserbase step fails. See `browserbase.py` for graceful-degradation details.

## The magician's divider check (right-edge alignment)

Beyond the standard wrap-safe probe, this skill measures the right-X coordinate of every main-flow prose element on the page. If the spread exceeds ~24px (inline-box natural variance), it flags a finding: container width is wider than the prose cap, and the user sees a phantom vertical line where prose wraps but section dividers or h2 underlines extend further.

Common causes:
- Container with no per-element prose cap, but `.doc p { max-width: <N>ch }` while h1/h2/h3 are uncapped — paragraphs cap at ~N×fontwidth pixels, headings cap at container.
- `ch` units evaluated cross-element: `110ch` produces wildly different pixel widths depending on the element's font-size, so a single rule produces inconsistent caps.
- Section divider rules (e.g., `h2 { border-top: 1px solid }`) that span the element's full width — when the element isn't capped, the divider runs past every paragraph.

Fix is one of:
- **Pixel-cap all main-flow prose elements at the same width** with explicit opt-outs for tables, workbooks, and `.table-scroll`.
- **Narrow the container to match the prose** so the container IS the bound.

The probe automatically skips elements that are intentionally outside the main flow: tables, table-scroll wrappers, workbook embeds, multi-column grid/flex children (scenario cards, KPI grids), horizontally-centered elements (`margin: auto`), and `text-align: center` elements.

## Output

A structured per-page report:

```
  <page-path-or-url>
    ✓ wrap-safe probe: 0 NEW findings (N known-issue match(es))
    ✓ right-edge alignment: all prose within 24px
    📸 <screenshot-path>
```

Or for a failure:

```
  <page-path-or-url>
    ✗ right-edge spread: 504px across 3 distinct edges
        right=856px (×30)  <h1.> max-width:800px "..."
        right=1361px (×8)  <h2.> max-width:none "..."
        right=687px (×6)   <li> w=588 max-width:800px "..."
    ✗ wrap-safe probe: N NEW finding(s)
        short-text-many-lines: <p.label> w=85px lines=3 "<short-label-text>"
        typography-anti-pattern: <p.note> w=287px rules=hyphens:auto, text-wrap:pretty "..."
        dense-prose-in-narrow-column: <p.note> w=287px lines=5 "..."
        element-horizontal-overflow: <code> overflow=34px "..."
```

Exit code: 0 if all pages pass (or only known-issue matches), 1 if any new finding, 2 if operational failure (URL unreachable, Playwright not installed, etc.).

## What this skill does NOT do

- Does NOT modify CSS or HTML. Pure observation.
- Does NOT update `wrap-known-issues.json` automatically. A new finding requires the consuming repo's owner to either fix it in code OR add an explicit allowlist entry.
- Does NOT run during `pytest` unless the consuming repo wires it in — the consuming repo's own `tests/test_wrap.py` is the CI-time check. This skill is the interactive-and-post-deploy check.
- Does NOT diagnose bugs unrelated to text wrap / container width (color contrast, JS errors, accessibility, etc.).
- Does NOT bake in any project-specific URLs, gate keys, or passwords. All consumer-specific values come from CLI args.

## Why this skill exists

A recurring failure mode in static-HTML portal work: declare "text wrap is fixed" without verifying the deployed page across real breakpoints, and miss bug classes the probe was not tuned for (label wraps in narrow grid cells, auto-hyphenated prose in a narrow side note, magician's divider from `ch`-unit cross-element mismatches, false positives in row-height-inherited table cells). This skill is the discipline that should be in place from the start: never claim "fixed" without running both (a) the wrap-safe probe across the default viewports and (b) the right-edge alignment check on the actual deployed URL.
