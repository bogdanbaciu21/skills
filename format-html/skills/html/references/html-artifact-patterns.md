# HTML Artifact Patterns

Use this reference when creating a new self-contained HTML artifact rather than
finishing an existing page.

## Routing

- Report, explainer, comparison, plan, status page, dashboard slice, or
  prototype: use `html`.
- Architecture, stack, system, sequence, lineage, or flow map where the diagram
  is the primary artifact: use `html-diagram`.
- Existing page with wrapping/table/CSS debt: use `pagecraft` plus
  `verify-text-wrap`.
- Financial model or numeric exhibit: render with `html`, but load
  `number-formats` before writing tables.
- New non-trivial artifact with unclear structure: run the Pagecraft
  `design-intelligence.md` pass before choosing layout or writing CSS.

## Intelligence Pass

Use `../pagecraft/references/design-intelligence.md` when the artifact needs
more than a simple prose page. The pass forces these choices before code:

- Artifact class and reader job.
- Source trust and unknowns to mark as `TBU`.
- Active brand contract and any page-specific token overrides.
- Density, first viewport, primary interaction, and data/exhibit contract.
- Anti-patterns to avoid and verification gates to run.

## Artifact Contract

- Preserve source truth. Use `TBU` for unknowns instead of guessing.
- Name sources near the relevant section, not only in a final footnote.
- Use the repo's design tokens first. For Dan-owned or ambiguous work, use the
  Bogdan Baciu design system. For client-facing work, use the client brand.
- Build full-width sections with constrained inner content. Use cards for
  repeated items, tools, and modals, not as nested page chrome.
- Keep the first viewport useful. The reader should see the artifact's subject
  and the start of the next section without a marketing detour.
- Prefer Pagecraft primitives for dense tables, safe grids, section dividers,
  eyebrows, captions, numeric cells, and source lines.

## Layout Recipes

- Decision brief: title, one-line decision, evidence grid, risks, next actions,
  source footer.
- Comparison: criteria rows, alternatives as columns, recommendation band,
  caveats, source notes.
- Status/report: current state, deltas, exceptions, owners, dates, proof links.
- Prototype surface: real controls, empty/loading/error states, compact notes,
  no explanatory feature-tour text inside the UI.
- Plan page: objective, acceptance criteria, work bands, blockers, validator
  questions, proof plan.
- Landing/offer page: literal offer, proof, CTA, objections, real imagery or
  product surface; never generic marketing filler.
- Knowledge/docs page: search or TOC, task groups, examples, deep links,
  version/source notes.
- Data exhibit: chart/table pair, unit and period labels, legend, source line,
  accessible fallback.

## Verification

Run what exists in the target repo:

- Brand: `brand_lint.py <artifact.html>` when present.
- Static wrap root cause: `verify-text-wrap/check-keystone.py --portal <dir>`.
- Browser rendering: `verify-text-wrap/runner.py --local --portal <dir>` for
  visual, responsive, or recently changed pages.
- Manual scan: no placeholder `TBU` unless reported, no off-palette ad hoc
  colors, no horizontal overflow, no unreadable long labels, no orphaned source
  claims.
