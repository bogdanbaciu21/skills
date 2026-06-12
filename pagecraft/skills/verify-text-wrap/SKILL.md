---
name: verify-text-wrap
description: Pagecraft sub-skill — load via pagecraft, not as a standalone skill. Verify a static-HTML portal has no caterpillar text-wrap, ugly hyphenation, display-text orphan lines, narrow-card prose, horizontal overflow, or container-collapse bugs, both locally and against the deployed URL. Use after any CSS edit, after any deploy, or when the user reports "the text wrapping is broken" / "this looks off" / "random text wrapping" / "phantom right edge" / "magician divider". Runs the wrap-safe runtime probe across desktop/tablet/mobile viewports plus a right-edge alignment check. Compares findings against a per-repo `tests/wrap-known-issues.json` allowlist if present. Do NOT use for generic CSS bugs unrelated to text wrapping or container width.
---

# verify-text-wrap

> **Pagecraft sub-skill.** Installed at `pagecraft/verify-text-wrap/` — invoke through
> `pagecraft`, not as a top-level skill.

A protocol for confirming a static-HTML portal renders correctly across viewport widths after CSS or markup changes. The `wrap-safe` runtime library (the `wrap-safe.css` reset + the `wrapcheck.js` probe) is **bundled in this skill** — `runner.py` loads `./wrapcheck.js` by default, and `check-keystone.py` recognizes `wrap-safe.css` as the keystone source. See [The bundled wrap-safe library](#the-bundled-wrap-safe-library) below.

Default runner coverage is intentionally strict: `wide` 1440x900, `desktop` 1280x900, `laptop` 1024x900, `tablet-wide` 820x900, `tablet` 768x900, `phone-wide` 430x844, `mobile` 390x844, and `phone-narrow` 360x780. One viewport is not enough; many ugly wrap bugs appear only between named breakpoints or when a mobile header gets too narrow.

## When to invoke

- **After any CSS edit** touching `display`, `width`, `max-width`, `flex`, `grid`, `padding`, `margin`, `text-wrap`, `hyphens`, `word-break`, `overflow-wrap`, or any selector containing `p`, `li`, `h1-h6`, `td`, `th`, `article`, `main`, `section`, `.doc`, `.article`, `.prose`, `.tile`, `.kpi`.
- **After deploying to any host** (Netlify, Vercel, etc.). Build-time tests pass against local; the deployed render is where CDN cache, font race conditions, and real network conditions show up.
- **When the user reports** any of: "text wrapping", "wraps weird", "random text wrap", "phantom right edge", "magician divider", "caterpillar text", "h2 underline runs past my paragraphs", "text stops in a weird place".

## Deterministic keystone guard (no browser) — run this FIRST

`runner.py` detects wrap bugs *after* they render, and only at the viewports it
happens to test. `check-keystone.py` catches the most common *root cause* before
anything renders — no browser, no flake — so it belongs in pre-commit / CI:

```
python3 <skill-dir>/check-keystone.py --portal <static-html-dir>
```

It fails (exit 1) when a repo uses flex/grid layout but is missing the wrap-safe
keystone `*, *::before, *::after { min-width: 0 }` — the single rule that stops a
flex/grid sibling from collapsing a paragraph into caterpillar text ("text
wrapping when it shouldn't"). A repo satisfies it by having the keystone in any
stylesheet, or by linking `wrap-safe.css` (which ships it). Exit 0 = present or
no flex/grid found; exit 2 = nothing to scan. This is the guard that keeps "I
forgot the keystone" from ever reaching a deploy; `runner.py` stays the
post-edit / post-deploy *render* check for everything the keystone alone can't
prove.

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

Navigation waits for `domcontentloaded` by default, waits up to 5 seconds for `document.fonts` to report loaded, then the probe waits briefly before measuring. That keeps portal-wide static sweeps fast while reducing false-clean results caused by fallback-font line breaks. Use `--wait-until load` or `--wait-until networkidle` only for a page that truly needs it. Use `--font-timeout-ms 0` only when debugging a font problem itself. Use `--settle-ms 0` or `--settle-ms 250` for a fast full-estate static ratchet; use a higher value for chart-heavy pages.

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

Default `wrapcheck.js` source is the copy bundled in this skill directory (`./wrapcheck.js`) so skill edits take effect immediately even against deployed URLs. Pass `--wrapcheck-url https://.../wrapcheck.js` only when intentionally testing the CDN copy.

For a full-estate ratchet where screenshots would be too heavy, disable them:

```
python3 <skill-dir>/runner.py --local --portal portal --screenshot-dir '' --settle-ms 250
```

To keep a machine-readable artifact for auditing or a CI annotation step:

```
python3 <skill-dir>/runner.py --local --portal portal \
  --pages target.html \
  --json-report /tmp/verify-text-wrap-report.json
```

The JSON report schema is versioned with `schema_version: 1`; downstream CI
annotations should key off that field before assuming report shape.

### CI examples

Local static build gate:

```yaml
- name: Verify text wrap locally
  run: |
    python3 pagecraft/skills/verify-text-wrap/check-keystone.py --portal dist
    python3 pagecraft/skills/verify-text-wrap/runner.py --local --portal dist \
      --screenshot-dir '' \
      --json-report /tmp/verify-text-wrap-local.json
```

Post-deploy smoke gate:

```yaml
- name: Verify deployed text wrap
  run: |
    python3 pagecraft/skills/verify-text-wrap/runner.py \
      --deployed "$DEPLOY_URL" \
      --screenshot-dir /tmp/verify-text-wrap \
      --json-report /tmp/verify-text-wrap-deployed.json
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
        display-text-orphan-line: <p.ns-target> w=258px final="margin." lines="Run on clean rails. / Harvest your own / margin."
        display-text-short-final-line: <p.sub> w=980px final="control." lines="... on a clock you / control."
        clipped-text: <p.note> hiddenX=0px hiddenY=18px "..."
        element-horizontal-overflow: <code> overflow=34px "..."
```

Exit code: 0 if all pages pass (or only known-issue matches), 1 if any new finding, 2 if operational failure (URL unreachable, Playwright not installed, etc.).

## Worked examples

### Example 1: Static local portal

User: "Check this portal before I send it."

Run the keystone check first. If it passes, run the local browser sweep across
default viewports. Report both the deterministic result and any browser findings.

### Example 2: Deployed page after a push

User: "Verify the live page; it looked weird on mobile."

Use deployed mode against the live URL, pass any gate key/password through the
consuming repo's normal secret path, and keep screenshots for the failing
viewport. Do not rely on local `file://` inspection.

### Example 3: Known issue handling

User: "This one finding is intentional."

Only add a known-issue entry after inspecting it and writing the reason. A known
issue is an audited exception, not a way to make the report green.

## What this skill does NOT do

- Does NOT modify CSS or HTML. Pure observation.
- Does NOT update `wrap-known-issues.json` automatically. A new finding requires the consuming repo's owner to either fix it in code OR add an explicit allowlist entry.
- Does NOT run during `pytest` unless the consuming repo wires it in — the consuming repo's own `tests/test_wrap.py` is the CI-time check. This skill is the interactive-and-post-deploy check.
- Does NOT diagnose bugs unrelated to text wrap / container width (color contrast, JS errors, accessibility, etc.).
- Does NOT bake in any project-specific URLs, gate keys, or passwords. All consumer-specific values come from CLI args.

## Skill maintenance

When editing the runner CLI, viewport parsing, or JSON report shape, run:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests/test_runner.py
```

## The bundled wrap-safe library

Two files ship in this skill directory and are the runtime half of the protocol —
`runner.py` and `check-keystone.py` are the verification half. They can also be
dropped straight into a site so the guarantees hold at runtime, not only at
verify time.

**Install into a live page** (two lines in `<head>`):

```html
<link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/bogdanbaciu21/skills@main/pagecraft/skills/verify-text-wrap/wrap-safe.css">
<script src="https://cdn.jsdelivr.net/gh/bogdanbaciu21/skills@main/pagecraft/skills/verify-text-wrap/wrapcheck.js" defer></script>
```

Pin a commit SHA (`@<sha>`) instead of `@main` for production. Or `@import` the
CSS from an existing stylesheet. License: MIT.

### `wrap-safe.css` — the reset

- `*, *::before, *::after { min-width: 0 }` — the **keystone**; defeats the #1
  cause of flex/grid container collapse (`check-keystone.py` enforces it).
- `box-sizing: border-box` on all elements (restated).
- `overflow-wrap: break-word` + `word-break: normal` + `hyphens: manual` on prose
  (`h1-h6`, `p`, `li`, `td`, `th`, `a`, …).
- `overflow-wrap: anywhere` on `code`, `kbd`, `samp`, `pre` so long unbreakable
  tokens (URLs, hashes) break instead of overflowing; `pre { white-space: pre-wrap }`.
- `img, svg, video, canvas, iframe { max-width: 100%; height: auto }`; `table { max-width: 100% }`.

It is **not** a full reset (does not zero margins/padding), does not pick fonts,
and deliberately does **not** set `max-width` on prose — that belongs to the
site's design.

### `wrapcheck.js` — the probe

No dependencies. Exposes `window.__wrapcheck()` for manual use and auto-runs when
the URL carries `?wrapcheck=1`. Pure observation — never mutates the DOM.
Playwright/Selenium can call `__wrapcheck({silent: true})` to assert in CI.
Checks: nuclear scroll height, narrow prose containers (<200px), caterpillar
elements (>12 lines), short-text-many-lines (≤40 chars over ≥3 lines),
heading-many-lines (>3), typography anti-patterns, dense prose in narrow columns,
display-text orphan / short-final lines, clipped text, and horizontal overflow.

### Anti-patterns the library deliberately avoids

`text-wrap: balance`, `text-wrap: pretty`, `hyphens: auto`, and
`word-break: break-all` are **not** used and are **flagged** by the probe. If you
reach for one as a "fix" for visible wrap weirdness, run `__wrapcheck()` first —
the bug is almost always an upstream container collapse, not a text rule.

## Why this skill exists

A recurring failure mode in static-HTML portal work: declare "text wrap is fixed" without verifying the deployed page across real breakpoints, and miss bug classes the probe was not tuned for (label wraps in narrow grid cells, auto-hyphenated prose in a narrow side note, magician's divider from `ch`-unit cross-element mismatches, false positives in row-height-inherited table cells). This skill is the discipline that should be in place from the start: never claim "fixed" without running both (a) the wrap-safe probe across the default viewports and (b) the right-edge alignment check on the actual deployed URL.
