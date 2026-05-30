# Text-Wrap Reference

Prevent the "caterpillar text," phantom-right-edge, and container-collapse class
of layout bugs **before they reach a live page** — and catch them
deterministically when they slip in. This is the most-fixed, most-recurring bug
class in static-HTML work, and almost none of it is a typography problem.

## The one law

> **Bad wrapping is almost always a bad container, not bad text.**

A paragraph that wraps one or two words per line is rarely too narrow because of
its own CSS — it's narrow because a *parent* flex/grid track collapsed, or a
sibling stole the width, or a `ch`/`px` cap fights the container. So the fix
order is always **container → width ownership → prose defaults**, and *never*
"reach for a clever `text-wrap` value." Auto-hyphenation, `text-wrap: balance`,
`text-wrap: pretty`, and `word-break: break-all` do not fix collapse; they
disguise it and add new bugs.

---

## 1. The keystone — `min-width: 0` (do this first, everywhere)

```css
*, *::before, *::after { min-width: 0; }
```

This is the single highest-leverage rule in the entire system. **A flex or grid
item's default `min-width` is `auto`, not `0`.** That means an unbreakable child
— a long word, a URL, a hash, an `<img>`, a `<pre>` — can force its track wider
than the parent's budget. The browser makes room by shrinking the *other*
tracks, and the text in those tracks collapses to one or two words per line.
That is the caterpillar bug, and it is invisible until exactly the wrong content
shows up.

Setting `min-width: 0` universally lets flex/grid children shrink to fit, which
is what authors expect ~99% of the time. It is the first rule in `pagecraft.css`
(right after `box-sizing`) and it is checked by `check-text-wrap.py` so a repo
can never ship flex/grid layout without it.

**Symptom it cures:** "text wraps when it shouldn't," "random narrow column,"
"one card in the row went skinny," "the sidebar squished the article."

If you adopt only one rule from this document, adopt this one. A repo that has
wrap-safe's prose rules but is missing the keystone is the most common failure
mode in the wild — it *looks* protected and isn't.

---

## 2. Layout primitives — never hand-count text columns

Text-bearing card grids must be able to reflow. Hard-counted column tracks are
the second-biggest source of caterpillar text.

```css
/* SAFE — tracks add/drop themselves; each is never narrower than its floor */
grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));

/* Prose-heavy cards want a wider floor */
grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));   /* or 260 / 320 */
```

**Banned for text-bearing layouts** (flag unless a same-line `wrap-exempt:`
reason is present):

- `grid-template-columns: repeat(3, 1fr)` (or any fixed count ≥ 3 carrying prose)
- `repeat(3, minmax(0, 1fr))` — the `minmax(0,…)` floor lets text crush to nothing
- `repeat(auto-fit, minmax(<220px>, 1fr))` — floors under ~220px caterpillar on mobile
- Any flex row of text cards without `flex-wrap: wrap` + a sane `flex-basis`

A `minmax(0, 1fr)` floor is *correct* for a numeric/icon strip (KPI tiles, a
sparkline row) — mark those `/* wrap-exempt: metric-only, no prose */` so the
guard stays quiet without going blind.

---

## 3. Width ownership — the page owns width, not the paragraph

```css
/* Let prose fill its container; the PAGE caps the reading width, once. */
:where(p, li, blockquote, figcaption, dd, dt, summary) { max-width: none; }
```

- **Do not** put `max-width: NNch` on `p`, `li`, `.lede`, `.summary`, `.prose`,
  or any ordinary prose element. A `ch` cap evaluates per-element (a `72ch` cap
  is a different pixel width on an `h2` than on a `p`), producing the
  "magician's divider": prose wraps at one X while section rules / `h2`
  underlines run to a wider X. The user sees a phantom vertical line.
- Cap the reading column **once**, on the page/article container, and let every
  descendant fill it. Use `:where()` (zero specificity) for the reset so a
  deliberate callout can still narrow itself without an `!important` war.
- Wide tables and code scroll inside their own wrapper — they never set the
  page's width (see `tables.md` → `.bbt-wrap`).

---

## 4. Prose, code, and replaced-element defaults

```css
/* Ordinary prose: greedy wrap, break only at the boundary, NO auto-hyphens. */
h1,h2,h3,h4,h5,h6, p,li,dd,dt,blockquote,figcaption,summary,label, td,th {
  overflow-wrap: break-word;
  word-break: normal;     /* defends against an upstream break-all */
  hyphens: manual;        /* auto-hyphens read as typos in UI copy */
  text-wrap: wrap;        /* never balance/pretty on body prose */
}

/* Inline code / identifiers may hold long unbreakable tokens. */
a, code, kbd, samp { overflow-wrap: anywhere; word-break: break-word; }
pre, code, kbd, samp { hyphens: none; }          /* a hyphen in code IS the code */
pre { white-space: pre-wrap; overflow-wrap: anywhere; }   /* don't push parent wide */

/* Replaced elements stay inside their box. */
img, svg, video, canvas, iframe { max-width: 100%; height: auto; }
table { max-width: 100%; }
```

**Why `hyphens: manual`, not `auto`:** auto-hyphenation inserts visible mid-word
hyphens that read as typos in product UI, and it papers over the real
container-collapse bug (a too-narrow box "looks fine" once hyphenated, so the
collapse never gets fixed). The wrap probe **fails** `hyphens: auto` on ordinary
prose for this reason. Long-form editorial body copy that genuinely wants
justified hyphenation is a deliberate, separate opt-in — not a default.

---

## 5. The banned list (source-level guard)

Flag each of these unless the same line carries a `wrap-exempt: <reason>` comment:

| Pattern | Why it's banned |
|---|---|
| `repeat(3, 1fr)` / `repeat(N≥3, …)` on prose | hand-counted columns caterpillar |
| `repeat(…, minmax(0, 1fr))` carrying prose | zero floor lets text crush |
| `repeat(auto-fit, minmax(<220px, 1fr))` | sub-220 floors caterpillar on mobile |
| `max-width: NNch` on page/prose CSS | per-element cap → magician's divider |
| `word-break: break-all` | one-character-per-line wrapping |
| `hyphens: auto` on ordinary prose | typo-like mid-word hyphens; hides collapse |
| `text-wrap: pretty` / `text-wrap: balance` on body prose | unpredictable line redistribution |

The escape hatch is always an inline reason, never deletion of the rule:
`/* wrap-exempt: KPI grid is metric-only, no prose */`.

---

## 6. Validation — two layers, both required

**Layer 1 — deterministic keystone guard (no browser, CI-safe, never flakes):**

```bash
python3 scripts/check-text-wrap.py --portal <static-html-root>   # or check-keystone
```

Fails when a repo uses flex/grid but is missing `* { min-width: 0 }`, or when a
banned primitive appears without a `wrap-exempt:` reason. This is the gate that
keeps the root cause out of a deploy. It needs no rendering, so it belongs in
pre-commit and CI on every push.

**Layer 2 — real-browser probe across viewports** (catches what only renders):

Render each page at the full breakpoint ladder — **1440, 1280, 1024, 820, 768,
430, 390, 360** — and run two checks per page:

1. **Wrap probe.** Flags `caterpillar-element`, `short-text-many-lines`,
   `heading-many-lines`, `narrow-container`, `dense-prose-in-narrow-column`,
   `display-text-orphan-line`, `clipped-text`, and `element-horizontal-overflow`.
2. **Right-edge alignment ("magician's divider").** Measures the right-X of every
   main-flow prose element; a spread > ~24px means the container is wider than
   the prose cap. Cards, panels, hero bands, and `text-align:center` elements are
   skipped by design.

One viewport is never enough — most ugly wraps live *between* named breakpoints
or appear only when a mobile header gets too narrow.

**Allowlist, don't suppress.** Real, accepted exceptions (an archive page that
trips a page-height heuristic; a deliberately dense reference strip) go in
`tests/pagecraft/wrap-known-issues.json` with a reason — never silenced by
loosening the probe.

---

## 7. Failure taxonomy — name it, then fix the container

| What the user sees | Real cause | Fix |
|---|---|---|
| Caterpillar text (1–2 words/line) | flex/grid sibling collapsed | **keystone** `min-width:0`; widen the track floor |
| Phantom vertical line / divider runs past text | per-element `ch` cap vs uncapped headings | cap the **container** once; drop the `ch` cap |
| One card went skinny in a row | unbreakable child stole width | keystone; `overflow-wrap:anywhere` on the offender |
| Page is 50,000px tall | a child forced horizontal overflow → reflow blowup | keystone; `img/pre max-width:100%` |
| Heading orphan / stranded last word | display text in a too-tight box | widen the box; do **not** reach for `balance` |
| Horizontal scrollbar on `<body>` | an element overflows the viewport | find it with the probe; cap or wrap it |

---

## 8. Install posture

- **New repo:** keystone + prose defaults from day one; both validation layers
  strict. There is no legacy debt to baseline.
- **Legacy repo:** add the keystone, run the probe once, **normalize the obvious
  bad primitives**, allowlist only confirmed non-defects, then ratchet — new
  violations fail, the historical baseline is grandfathered until touched.
- **Always** open the deployed URL after a push. Build-time tests pass against
  local; CDN cache, font races, and real network conditions only show on the
  edge. "Green build" is not "looks right in production."
