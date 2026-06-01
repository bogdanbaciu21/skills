# Headers & Section Dividers Reference

Section chrome — the markers that show a reader where they are in a long
document — is read as *navigation*, not decoration. Done well it is almost
invisible: the reader feels the structure without noticing the device. Done
badly it shifts layout on hover, competes with its own copy, decorates every
block equally, or strands a floating `#` that jumps the page when clicked. This
reference encodes a section-divider system that has been migrated out of exactly
those failure modes.

## The two laws

> **1. Quiet, always-on chrome beats loud, hover-only chrome.**
>
> **2. Chrome encodes hierarchy. If every block is decorated, nothing is.**

The first law is a layout-stability rule. A marker that appears on hover and
*pushes the text over* is jank — the click target moves while the reader reaches
for it. The fix is to put the marker **outside the prose box** (in the left
margin, absolutely positioned) so it can be always-visible without ever touching
the text's box model. Hover then only changes color, never geometry.

The second law is an information-design rule, the same idea as provenance color
in `number-formats.md`: the *presence and weight* of a divider should mean
something. Major parts get a heavier treatment; subsections get a whisper; body
blocks get nothing.

---

## 1. The hierarchy of dividers — match weight to depth

Three tiers, loud to quiet. Reach for the lightest one that still reads.

| Tier | Treatment | Use for |
|---|---|---|
| **Section break** | full-width rule top + label + display title + deck | major parts of a long page; a deliberate "new chapter" beat |
| **Chapter divider** | eyebrow + thin ink hairline above an `h2` | a section turn that needs a name but not a full band |
| **Subhead gutter bar** | a 3px bar in the left margin of an anchored `h3`/`h4` | every anchored subsection — the always-on, near-invisible marker |
| **Thin divider** | a single hairline rule, no text | a soft pause between small subsections |
| **Ornament** | a centered `* * *` | an editorial scene-break in prose, sparingly |

Do not stack them. A section break already announces itself; it does not also
need a gutter bar on its title. Picking the tier *is* the design decision.

### Section break (heaviest)

```html
<section class="pc-section-break pc-section-break--first">
  <p class="pc-section-label">Part I · Baseline</p>
  <h2 class="pc-section-title">What the current workflow costs</h2>
  <p class="pc-section-deck">One or two sentences framing why this part exists.</p>
</section>
```

### Chapter divider (medium) — eyebrow + hairline

An `h2` that turns the document a corner but doesn't warrant a full band. The
eyebrow is an italic serif line; a 2px ink hairline runs above the title.

```html
<h2 class="pc-chapter">
  <span class="pc-chapter-label">Where the time actually goes</span>
  The handoff is the bottleneck
</h2>
```

`pc-chapter-label` followed by the heading text on the next visual line; the
bundled CSS hides a stray `<br>` after the label so authors can write it either
way. (`<h2 class="pc-chapter">` and `<h2>` wrapping a `.pc-chapter-label` both
trigger the treatment, via `:has()`.)

### Subhead gutter bar (quietest) — the always-on marker

```html
<h3 id="the-handoff-tax" class="pc-heading-anchor">The handoff tax</h3>
```

A 3px bar sits at `left:-22px` — in the margin, outside the reading column. It
is always visible (it marks the anchor target), darkens on hover, and **never
reflows the prose** because it is `position:absolute`. On hover the heading also
gets a quiet underline. On viewports below 720px the bar moves inside to
`left:0` with a small `padding-left`, since there's no margin to live in.

---

## 2. Drive anchors off auto-injected `id`s, not per-heading markup

The single highest-leverage move. Inject heading `id`s **once, centrally** — at
build time or server-side render — by slugifying heading text, instead of asking
authors to hand-write `id="..."` and an anchor class on every heading.

```
"The handoff tax"  →  id="the-handoff-tax"
```

Why this matters:

- **Consistency for free.** Every anchored subheading gets the same gutter bar
  with zero per-post markup. Authors write `## The handoff tax` and the chrome,
  the deep-link target, and the table-of-contents entry all follow.
- **One place to change the rule.** Want to also anchor `h4`s, or change the slug
  algorithm? One edit, not a sweep across every document.
- **It composes with the TOC.** The same `id`s a TOC links to are the ones the
  gutter bar marks, so "scroll to section" lands exactly on the bar.

If you auto-apply the bar to **every** `h3[id]` (rather than an opt-in
`.pc-heading-anchor` class), you must scope the exceptions — see §3.

---

## 3. Exceptions are scoped, never global deletions

A numbered editorial sequence (sections that carry an ordinal counter via a
`::before`) already has its own ordinal system. Adding the gutter bar on top
makes two markers compete. The fix is to **exempt those headings**, not to
weaken the rule for everyone:

```css
/* opt-out class */
h3[id].pc-no-anchor::before { content: none; }

/* or scope the auto-rule against the numbered-id prefix */
.post-body h3[id]:not([id^="step-"])::before { /* gutter bar */ }
```

This is the same discipline as the `wrap-exempt:` escape hatch in
`text-wrap.md`: a *named, narrow* exception beats globally loosening the rule
and going blind.

---

## 4. Kill legacy floating-anchor chrome — and net it

The pattern this system replaces is the GitHub-style floating `#` (or a hover
`§`) that appears beside a heading on hover. It has two defects: it **reserves
layout space / shifts text**, and clicking it jumps the page. After migrating to
the gutter bar, suppress any leftover anchor link so a stale build can never
re-render it:

```css
a.pc-anchor-legacy,
.pc-heading-anchor > a[href^="#"].anchor { display: none; }
```

Keep the safety net even after you think the old markup is gone — a cached
template or an old JS hook re-injecting it is exactly the kind of regression that
slips back in months later.

---

## 5. Eyebrows and title rules (lighter accents)

```html
<p class="pc-eyebrow">Phase 01 · Discovery</p>      <!-- small metadata above a heading -->
<h1>AI readiness map</h1>
<hr class="pc-title-rule">                           <!-- compact rule under a page title -->
```

- The **eyebrow** is mono, uppercase, tracked — for small metadata (a phase, a
  kicker, a date), never for body emphasis.
- The **title rule** is a short fixed-width bar under a page/post title when a
  full section band would be too much.

---

## 6. Header safety — the anti-patterns

- **Hover-only markers that move text.** Any affordance that changes a heading's
  box on hover (a marker that pushes copy, a margin that appears) is jank. Put it
  in the margin or make it always-on.
- **Decorating every block.** A divider on every `h3` is wallpaper; the reader
  stops seeing structure. Reserve weight for real turns.
- **`text-wrap: balance` as a default on headings.** Acceptable only as an
  explicit display class *after* visual verification — it gives up on long
  headings and reflows unpredictably (see `text-wrap.md`). Never global.
- **Fixed multi-column TOCs.** A `repeat(3, 1fr)` table of contents caterpillars
  on mobile. Use `repeat(auto-fit, minmax(220px, 1fr))`.
- **A floating `#` anchor.** Shifts layout and competes with the heading. Use the
  always-on gutter bar and a clean deep-link target instead.
- **Per-post divider `<style>` blocks.** Same trap as per-post table classes —
  the divider system lives in one stylesheet, applied globally. A one-off divider
  in a single document is a smell; promote it to the shared system or drop it.

---

## 7. CSS semantics (what `pagecraft.css` ships)

| Class / selector | Purpose |
|---|---|
| `.pc-section-break` (+ `--first`) | heaviest: full-width band for a major part |
| `.pc-section-label` / `.pc-section-title` / `.pc-section-deck` | the parts of a section break |
| `.pc-chapter` / `h2:has(> .pc-chapter-label)` | medium: eyebrow + ink hairline chapter turn |
| `.pc-chapter-label` | the italic-serif eyebrow inside a chapter heading |
| `.pc-heading-anchor` on `h3[id]`/`h4[id]` | quietest: always-on left-margin gutter bar + hover underline |
| `.pc-no-anchor` | opt a numbered/ordinal heading out of the gutter bar |
| `.pc-title-rule` | short fixed-width rule under a page title |
| `.pc-section-divider` | a soft hairline pause between subsections |
| `hr.pc-ornament` | centered `* * *` editorial scene-break |
| `.pc-eyebrow` | mono uppercase kicker above a heading |
| `a.pc-anchor-legacy` / `… a[href^="#"].anchor` | suppressed legacy floating anchor (safety net) |

The gutter bar's mobile fallback (move inside at `left:0`, add `padding-left`
below 720px) ships in the same file's media query — don't re-solve it per page.

---

## 8. Migration & install posture

Capturing this on an existing site is a small, ordered migration — the same
shape as the table migration, scaled down:

1. **Inventory the current anchor chrome.** Floating `#`? Hover `§`? Per-post
   `<style>` dividers? Hand-written `id=`s? Name what's there before changing it.
2. **Centralize `id` injection** (build/server) so every heading is anchored
   without author markup.
3. **Apply the gutter bar** to anchored subheadings; **scope out** numbered
   sections with `.pc-no-anchor` / a `:not([id^="prefix-"])` guard.
4. **Pick chapter vs. section-break** for the major turns — don't auto-apply the
   heavy treatment; it's an editorial choice per document.
5. **Suppress and net the legacy anchor** so it can't re-render.
6. **Verify hover doesn't reflow** and the bar survives the mobile breakpoint —
   the `verify-text-wrap` runner already renders the ladder; eyeball the heading
   rows at 1280 and 390.

New repo: ship the gutter bar + chapter system from the first serious page.
Legacy repo: migrate the reported-noisy surface first, leave the rest until
touched, and keep the legacy-anchor safety net permanently.
