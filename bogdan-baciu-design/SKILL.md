---
name: bogdan-baciu-design
description: Apply Bogdan Baciu's personal editorial design system to websites, static HTML, prototypes, documents, slide decks, and financial-model artifacts. Use when the user asks for "Bogdan brand", "my brand", "personal branding", "brand this", "apply the design system", "rebrand this", "make this look like bogdanbaciu.com", or when building/reviewing bogdanbaciu.com-facing interfaces. Includes the Puddles sky-blue on warm-cream palette, Instrument Serif + Geist + JetBrains Mono typography, flat editorial layout rules, and the scoped .db-scope financial-artifact styling.
---

# Bogdan Baciu Design

Apply Bogdan Baciu's editorial personal-site brand to digital artifacts while
preserving the user's content and judgment. The brand should feel like a
hand-finished finance/technology editorial surface: warm paper, a single
sky-blue accent, display serif headlines, restrained mono chrome, flat borders,
and dense but readable financial exhibits.

## Source files

- Load `references/brand-system.md` when you need detailed rules, artifact-mode
  guidance, or a compact token summary.
- Copy from `assets/design-system/colors_and_type.css` for web/static HTML work.
- Copy `assets/design-system/fonts/` when the output can self-host fonts.
- Copy imagery, favicons, logos, previews, or UI kits from
  `assets/design-system/assets/`, `preview/`, and `ui_kits/` only when the
  artifact actually needs them.
- Use `fixtures/brand-regression/*.html` as visual regression fixtures when
  checking that the global brand and `.db-scope` financial-artifact styling
  still render separately.
- Use `fixtures/brand-regression/screenshot-contract.json` as the browser
  screenshot checklist for those fixtures; it stays public-safe and stores
  selectors/expectations instead of private screenshots.
- Use `reskin.example.json` as the compatibility example when wiring this brand
  into the `reskin` skill.

## Provenance

- Brand source: local `Bogdan-Baciu-Design-System` repo.
- Packaging pattern: adapted from the official Anthropic `brand-guidelines`
  skill's compact palette/type/fallback approach; brand values and rules here
  are Bogdan-specific.

## Workflow

1. Identify the artifact type: website/static HTML, app UI, slide deck,
   document, data table, or financial-model exhibit.
2. Preserve the user's substantive content. Do not invent public-facing body
   copy; use `TBU` for missing prose.
3. Apply the global brand outside financial exhibits:
   - warm cream paper, ink text, Puddles sky-blue accent
   - Instrument Serif for display and ledes
   - Geist for body/UI
   - JetBrains Mono for eyebrows, chips, chrome, code, and utility labels
   - flat borders and hairlines, not shadows
4. Keep financial-model artifacts inside `.db-scope` or a clearly equivalent
   local scope. Do not let `.db-scope` colors, shadows, or typography leak into
   the global site brand.
5. Prefer the existing token names and component classes before inventing new
   CSS. For tables, prefer `div.bbt-wrap` + `table.bbt`.
6. Translate the brand carefully for non-web artifacts:
   - use exact hex approximations where the target cannot use OKLCH
   - use available font fallbacks when self-hosted fonts are impossible
   - keep the same hierarchy, spacing, and palette separation
7. Verify the result. For web work, inspect across mobile and desktop widths,
   check text wrapping, confirm assets load, and confirm `.db-scope` stays
   scoped. For decks/docs, inspect rendered output rather than trusting source
   formatting alone.
8. Before final delivery, scan for unresolved `TBU` placeholders in the output
   artifact. `TBU` is acceptable while drafting missing owner-authored copy; it
   must be reported explicitly and should not remain in a final publishable file
   unless the user approves the gap.

## Core rules

- Two palettes coexist. Global Puddles governs normal brand surfaces;
  `.db-scope` governs embedded financial-model artifacts only.
- Use one global accent: sky-blue. Rust is reserved for text selection and focus
  treatment, not general fills or calls to action.
- Default radius is sharp `2px`. The only general radii are sharp `2px`, card
  `16px`, and pill `999px`.
- Body prose is justified with soft hyphenation where the medium supports it.
  Headings use balanced wrapping; long ledes use justified/pretty wrapping.
- Depth comes from borders, rules, tables, and spacing. Avoid global shadows,
  glassmorphism, gradients, decorative blobs, and stock-looking decoration.
- Icons are sparse. Use existing logos/assets or restrained utility icons only
  when the interface needs them.
- When a layout feels cramped, widen the container before shrinking the type.

## Output contract

When applying this skill, report:

- which source files/assets were used
- any token, font, image, or icon substitutions
- whether `.db-scope` was used
- any unresolved `TBU` placeholders and why they remain
- which checks were run or which rendered surfaces were inspected

## Skill maintenance checks

When editing packaged tokens, fixtures, or the reskin example, run:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 scripts/check_token_integrity.py
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests/test_brand_fixtures.py
```

The token checker protects the core palette/type/font contract; the fixture test
protects the public-safe screenshot contract and the `reskin.example.json`
manifest shape.

## What this skill does not do

- Do not author the owner's public voice from scratch.
- Do not merge the global and `.db-scope` palettes.
- Do not add a broad icon library, theme gradient, or shadow language unless the
  target repo already requires it.
- Do not replace a repo's existing production design system without first
  mapping the Bogdan tokens onto its local conventions.
