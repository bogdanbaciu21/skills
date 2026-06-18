# Visual Asset Workflows

Use this for logo/wordmark, CIP, slide deck, banner/social image, icon, and
fixed-canvas visual work. The upstream `ui-ux-pro-max-skill` is useful as a map
of possible asset types, but Dan's local brand and proof gates still decide what
ships.

## Shared Rules

- Existing brand systems win. Do not redesign Bogdan, Acme, or a client identity
  unless the user explicitly asks for identity redesign.
- For public/client-visible copy, use user-supplied words or `TBU`. Do not invent
  numbers, dates, quotes, CTAs, claims, alt text, or testimonials.
- Keep generated images and mockups labeled as generated/draft until approved.
- Do not publish to Typefully, X/Twitter, LinkedIn, social platforms, CMS live
  toggles, or external channels from this skill.
- Prefer repo-native icons/libraries for UI controls: lucide first when
  available, then existing project icon systems, then custom SVG.
- For exact-size exports, verify the output dimensions and inspect the rendered
  asset. A source file alone is not an exported asset.

## Logo / Wordmark Lane

Use only when the task is identity exploration, not ordinary UI polishing.

1. Check for an existing logo/mark and brand guidelines first.
2. Define brand name, usage context, audience, constraints, and required formats.
3. Generate or sketch variations only after the route is clear.
4. Favor SVG for marks and transparent PNG for raster delivery; white-background
   proofs are fine for review, but not a replacement for production assets.
5. Do not replace an existing brand mark in code without explicit approval.

Acceptance:

- at least one vector or source asset when the request needs reusable identity
- white/dark/transparent usage called out when relevant
- no trademark-like claims or copied third-party marks
- user approval before committing a new canonical identity

## CIP / Brand Package Lane

Use for business cards, letterheads, signage, apparel, office collateral,
mockup galleries, and brand-system presentations.

1. Start from the approved logo and token source.
2. Choose only deliverables the user asked for or that the brief requires.
3. Use HTML presentation output for review when many mockups are involved.
4. Label all generated mockups as mockups; do not imply vendor-ready print
   production unless bleed, resolution, and color-mode requirements were checked.

Acceptance:

- brand source named
- deliverable list explicit
- mockups separated from production-ready files
- HTML/PDF/PNG export path verified if requested

## Slide Deck / HTML Presentation Lane

Use for strategy decks, pitch decks, teaching decks, and decision walkthroughs.

- One idea per slide unless the deck is explicitly an appendix.
- Charts need source labels, units, and honest missing-data treatment.
- Use Chart.js or repo-native charting only when the data supports it.
- Keep typography and spacing tied to the active brand. Do not use generic
  presentation gradients unless the local brand authorizes them.
- Speaker notes and appendix detail are allowed, but visible slide copy must be
  user-supplied or source-backed.

Acceptance:

- slide outline maps to reader decision
- source/copy review completed
- responsive or export check run when delivering HTML slides

## Banner / Social Image Lane

Use for website hero images, social cards, headers, thumbnails, ads, and
fixed-canvas graphics.

Common sizes:

| Surface | Size |
|---|---|
| Website hero | 1920 x 600 to 1080 |
| Blog/social card | 1200 x 628 |
| LinkedIn post | 1200 x 627 |
| X/Twitter post | 1200 x 675 |
| Instagram post | 1080 x 1080 |
| Instagram story/Reel/TikTok cover | 1080 x 1920 |
| YouTube thumbnail | 1280 x 720 |

Design rules:

- Critical content stays inside the central 80 percent safe zone.
- One focal point and one CTA max.
- Text must remain readable at thumbnail size.
- Do not put client-confidential or internal-only content into public/social
  assets.
- Use real or generated bitmap imagery when a visual asset is needed; avoid
  decorative abstract-only filler for product/place/person inspection.

Export proof:

**VPS Hetzner -- ssh shell**

```bash
cd /root/dans-brain
python3 bin/pagecraft_qa.py --html path/to/fixed-canvas.html --no-brand-lint
```

If using Playwright or Chrome screenshots, verify output dimensions with an image
metadata tool and inspect the PNG before reporting it as exported.

## Icon Lane

Use for custom pictograms, product-specific marks, or icon sets. For standard UI
actions, use the existing icon library instead.

SVG rules:

- Use `viewBox="0 0 24 24"` unless the project uses another grid.
- Use `currentColor` for UI icons unless a brand illustration needs fixed color.
- Include an accessible `<title>` or ensure the consuming component supplies an
  accessible label.
- Test at 16px, 24px, and 48px.
- Keep path count reasonable; avoid embedded fonts and raster images inside SVG.

Acceptance:

- no hardcoded off-brand color unless intentional
- accessible label/title path
- legible at the smallest required size

## Optional Upstream Tooling

The upstream `nextlevelbuilder/ui-ux-pro-max-skill` includes script catalogs for
logo, CIP, and SVG icon generation. Those scripts are not bundled into this
skill. If a task explicitly benefits from them:

1. Clone or inspect the upstream repo in a temporary directory.
2. Confirm license and secret/billing scope.
3. Run generation outside the target repo first.
4. Review and curate outputs.
5. Copy only approved assets or adapted references into the target repo.

Do not add upstream dependencies or generated asset dumps to Dan repos as a side
effect of ordinary HTML/Pagecraft work.
