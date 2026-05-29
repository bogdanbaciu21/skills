# wrap-safe

Drop-in CSS reset + JS runtime probe that prevents the recurring static-HTML text-wrap failure classes: paragraphs that wrap one or two words per line, pages that render 50,000 pixels tall, prose containers that resolve to 36 pixels wide, automatic mid-word hyphenation, unstable `text-wrap` rules, dense prose trapped in narrow card/sidebar columns, and horizontal overflow.

Designed to live alongside the [`verify-text-wrap`](../verify-text-wrap/SKILL.md) skill: this is the runtime library, that is the verification protocol.

## Install

Add two lines to your HTML `<head>`:

```html
<link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/bogdanbaciu21/skills@main/wrap-safe/wrap-safe.css">
<script src="https://cdn.jsdelivr.net/gh/bogdanbaciu21/skills@main/wrap-safe/wrapcheck.js" defer></script>
```

Pin a commit SHA in the URL if you need stricter version control (jsDelivr supports `@<sha>` in place of `@main`).

Or `@import` the CSS from an existing stylesheet:

```css
@import url("https://cdn.jsdelivr.net/gh/bogdanbaciu21/skills@main/wrap-safe/wrap-safe.css");
```

## What `wrap-safe.css` does

- `* { min-width: 0 }` — defeats the #1 cause of flex/grid container collapse.
- `*, *::before, *::after { box-sizing: border-box }` — standard but restated.
- `overflow-wrap: break-word` + `word-break: normal` + `hyphens: manual` on prose elements (`h1-h6`, `p`, `li`, `td`, `th`, `a`, etc.).
- `overflow-wrap: anywhere` on `code`, `kbd`, `samp`, `pre` so long unbreakable tokens (URLs, hashes) break instead of overflowing.
- `pre { white-space: pre-wrap }` so block code wraps long lines.
- `img, svg, video, canvas, iframe { max-width: 100%; height: auto }`.
- `table { max-width: 100% }`.

What it does NOT do:

- Not a CSS reset (does not zero margins/padding).
- Does not pick fonts.
- Does not set `max-width` on prose. That belongs to your site's design.

## What `wrapcheck.js` does

A small probe with no dependencies. Exposes `window.__wrapcheck()` for manual use and auto-runs when the URL has `?wrapcheck=1`.

Checks:

1. **Nuclear scroll height** — body scrollHeight > 30× viewport height (the canonical caterpillar symptom).
2. **Narrow prose containers** — any `article`/`main`/`section`/`.doc`/`.article`/`.prose` with computed width below 200 px.
3. **Caterpillar elements** — text wrapping to > 12 visual lines as measured by `Range.getClientRects()`.
4. **Short-text-many-lines** — ≤ 40 chars wrapping to ≥ 3 lines (the narrow-grid-cell label class).
5. **Heading-many-lines** — h1–h6 wrapping to > 3 lines.
6. **Typography anti-patterns** — `hyphens:auto`, `text-wrap:pretty`, `text-wrap:balance`, and `word-break:break-all` on visible prose.
7. **Dense prose in narrow columns** — long text trapped below 320px on tablet/desktop widths.
8. **Horizontal overflow** — body or element scroll width exceeding its container.

Returns a structured report. Playwright/Selenium can call `__wrapcheck({silent: true})` to assert on CI.

It does NOT modify the DOM. Pure observation.

## Anti-patterns deliberately AVOIDED in this library

- `text-wrap: balance` — produces uneven heading line lengths.
- `text-wrap: pretty` — redistributes whitespace unpredictably.
- `hyphens: auto` — inserts visible mid-word hyphens that read as typos.
- `word-break: break-all` — produces one-character-per-line wrapping.

If you find yourself reaching for any of these as a "fix" for visible wrap weirdness, run `__wrapcheck()` first. The bug is almost always a container collapse upstream, not a text rule.

## Versioning

Pinned by commit SHA or by tag. `@main` follows the latest commit on this branch — use only for development; production should pin. The canonical hosted path is:

```text
https://cdn.jsdelivr.net/gh/bogdanbaciu21/skills@<ref>/wrap-safe/
```

## License

MIT.
