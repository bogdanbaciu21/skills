# Flourishes Lift Inventory

Source inspected: a production site's `flourishes.css` stylesheet.

## Lifted Into Pagecraft

- Smooth scroll plus anchor offset for sticky headers.
- Branded selection color.
- `:focus-visible` rings and form focus affordance.
- OpenType basics: kerning, ligatures, tabular numerals for data.
- Animated inline link underlines.
- Ornament and thin section dividers.
- Cursor refinements.
- Editorial blockquote and pull-quote treatments.
- Print basics, including table wrapper print behavior.
- Drop caps and eyebrow labels.
- Header/title chrome: series tag, kicker, title rule, section break, chapter label, heading gutter bar.
- Canonical table system: caption block, wrapper fade, dark header, zebra, total rows, sources, footnotes, methodology drawer, group headers, attr/synth variants.
- Universal table safety net: wrappers, caption chrome, figure/table overflow safety.
- Callout, stat card, numeric emphasis, glossary/details/FAQ, and figure/exhibit patterns.

## Lift Carefully Or Keep Repo-Specific

- Justified editorial typography with auto-hyphenation and `text-wrap: pretty`; useful in Bogdan's editorial style, risky as a portable default.
- Full embed contract for `.db-artifact`, `.exhibit--fullbleed`, and LiveView/Univer internals; portable only after renaming and stripping project assumptions.
- Sticky post TOC rail and series navigation; useful for blog systems, not generic static pages.
- Draft banner and simulator CTA; project-specific.

## Pagecraft Position

Pagecraft elevates the reusable component contracts and safety nets. It does not copy the whole `flourishes.css` cascade, because that file intentionally contains site-specific overrides and historical patches.
