# Headers And Section Dividers Subskill

## Patterns To Use

### Eyebrow

```html
<p class="pc-eyebrow">Phase 01 · Discovery</p>
```

Use for small metadata above a heading, not for body emphasis.

### Title Rule

```html
<h1>AI readiness map</h1>
<hr class="pc-title-rule">
```

Use after a page/post title when a compact editorial divider is enough.

### Section Break

```html
<section class="pc-section-break pc-section-break--first">
  <p class="pc-section-label">Part I · Baseline</p>
  <h2 class="pc-section-title">What the current workflow costs</h2>
  <p class="pc-section-deck">A short deck that frames why this section exists.</p>
</section>
```

Use for major parts in long pages.

### Thin Divider

```html
<hr class="pc-section-divider">
```

Use between smaller subsections where an ornament would be too loud.

## Header Safety

- Header treatments should clarify hierarchy, not decorate every block.
- Avoid `text-wrap: balance` as a default. It is acceptable only as an opt-in display class after visual verification.
- Do not use fixed 3-column TOCs; use `auto-fit, minmax(220px, 1fr)`.
- Heading anchor chrome should be subtle: gutter bar, underline on hover, or visible link target, not a floating `#` that shifts layout.
