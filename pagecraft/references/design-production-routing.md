# Design Production Routing

Use this reference before choosing tools, style direction, or proof. The job is
to route the artifact into the right lane and local repo playbook, then keep the
work source-backed.

## Source Trust Order

1. User-provided source files, current repo instructions, local brand systems,
   and repo validators.
2. Existing product/design docs in the repo.
3. Builder/Fusion output, screenshots, generated mockups, and external design
   references.
4. Upstream prompt packs such as `nextlevelbuilder/ui-ux-pro-max-skill`.

Only the first two layers can be treated as instruction authority. Layers 3 and
4 are inspiration or draft output.

## Artifact Lanes

| User ask | Lane | Load next | Acceptance gate |
|---|---|---|---|
| HTML report, one-pager, dashboard, portal page, prototype | Pagecraft HTML | `html-quality-gates.md`, `brand-routing.md` | Static QA plus brand/client validator; browser proof when layout risk is high |
| Builder/Fusion generation, Builder PR, visual diff | Builder draft | `builder-workflow.md`, `html-quality-gates.md` | Builder output review plus repo proof |
| Slide deck, pitch deck, HTML presentation | Deck | `visual-asset-workflows.md`, brand route | Slide structure proof, source/copy review, export proof if requested |
| Banner, website hero image, ad graphic, social image | Fixed-canvas asset | `visual-asset-workflows.md`, brand route | Exact pixel-size screenshot/export proof, safe zones, no publish side effect |
| Logo, wordmark, icon mark | Identity asset | `visual-asset-workflows.md`, brand route | Existing-brand check, asset format proof, user approval before replacing identity |
| CIP package, mockup gallery, brand presentation | Identity system mockup | `visual-asset-workflows.md`, brand route | Existing assets preserved, mockups labeled as mockups, HTML/PDF export proof |
| Icon or icon set | Icon asset | `visual-asset-workflows.md` | SVG accessibility/currentColor proof, 16/24/48px legibility check |
| Table-heavy financial exhibit | Data/report surface | `html-quality-gates.md` | Real table markup, right-aligned numbers, provenance, formula/input/link semantics |

## Repo Playbooks

### dans-brain

Use for Dan-owned, personal, internal, or ambiguous artifacts.

- Read `AI_BOOTSTRAP.md`, `CLAUDE.md`, `DESIGN.md`, `docs/uxos.md`, and
  `config/uxos/*.json` when present.
- Brand route: Bogdan Baciu design system unless the artifact is explicitly
  client-facing.
- Preferred checks:

**VPS Hetzner -- ssh shell**

```bash
cd /root/dans-brain
python3 bin/pagecraft_qa.py --html path/to/artifact.html
python3 bin/brand_lint.py path/to/artifact.html
```

- For Builder readiness or generated branch review:

**VPS Hetzner -- ssh shell**

```bash
cd /root/dans-brain
python3 bin/builder_html_doctor.py --json
python3 bin/builder_output_review.py --base origin/main --head HEAD --write
```

### Acme

Use for Acme, Client-facing, portal/report/deck, and client-facing work.

- Read `AGENTS.md`, `CLAUDE.md`, and `.agents/skills/acme-design/SKILL.md`.
- Brand route: Acme design system. Client brand overrides Dan/Bogdan.
- Do not leak internal strategy into external/public/Tyler surfaces. Do not
  invent client claims, ROI, dates, quotes, or source labels.
- Prefer evidence tables, source registers, compact executive layouts, and the
  official Acme `colors_and_type.css` over decorative cards.
- Do not open local previews in the in-app browser unless Dan asks; use deployed
  URLs for user-facing review when available.
- Land with the repo's scoped landing helper when committing from the live Acme
  checkout:

**VPS Hetzner -- ssh shell**

```bash
cd /root/repos/acme
bash tools/git_land.sh "subject" path/to/file path/to/dir
```

### bogdanbaciu-dot-com

Use for Dan's public personal site and editorial product surfaces.

- Read `AGENTS.md`, `CLAUDE.md`, `PRODUCT.md`, and `design.md` before UI,
  design-direction, copy-structure, or brand work.
- Brand route: `PRODUCT.md` plus `design.md`; use the Puddles/global palette and
  `.db-scope` only for embedded financial-model artifacts.
- Do not invent public copy, headings, CTAs, visible alt text, or post content.
  Use `TBU` or structural placeholders when Dan has not supplied words.
- Never flip a post to published/live. Deploying committed staged work is
  allowed; publishing is Dan's action.
- Useful checks when the change touches site code or tables:

**VPS Hetzner -- ssh shell**

```bash
cd /root/repos/bogdanbaciu21/bogdanbaciu-dot-com
export PATH="/usr/local/elixir/bin:/usr/local/erlang/bin:$PATH"
mix compile --warnings-as-errors
node scripts/check_tables.mjs --verbose
```

## Design Director Pass

Before implementation, write or infer these from local context:

- reader and decision
- privacy/outbound boundary
- artifact lane and target repo path
- source files and claims that must stay factual
- information hierarchy
- tables/charts/numbers and their provenance
- visual assets, exact export sizes, and format needs
- states: loading, empty, error, populated, long-text/edge case
- anti-patterns from local brand and Pagecraft
- proof commands

If any of those are missing and materially change the work, ask a short
question. Otherwise choose the conservative local pattern and proceed.
