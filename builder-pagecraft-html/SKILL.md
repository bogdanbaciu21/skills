---
name: builder-pagecraft-html
description: Builder.io Fusion plus Pagecraft/UX OS workflow for creating or hardening high-quality branded HTML artifacts, reports, dashboards, portal pages, prototypes, and visual documents. Use when the user asks for "awesome HTML", Builder-backed HTML/UI generation, Fusion/Builder.io work, Pagecraft finishing, text-wrap fixes, number/table formatting, Bogdan Baciu branded HTML, LJB/client branded HTML, or review of Builder-generated visual output.
---

# Builder Pagecraft HTML

## Overview

Use this skill as the single lane for Builder-backed HTML work: Builder/Fusion is
the visual generation surface, Anthropic-style design direction is the pre-code
critique layer, brand systems own palette/type/voice, and Pagecraft owns layout
mechanics plus verification.

Builder does not replace Dan UX OS, Bogdan Baciu design, LJB/client brand
systems, Pagecraft, proof packets, or git review. It makes the first pass faster.

## Operating Contract

1. Treat Builder output as a draft PR, not finished work.
2. Run a design-director pass before code: define reader, decision, information
   hierarchy, artifact type, states, tables, numbers, and anti-patterns.
3. Route the brand before choosing colors or typography:
   - LJB/client-facing work uses the client brand first.
   - Dan-owned, personal, internal, or ambiguous work uses Bogdan Baciu.
   - Pagecraft never invents a competing palette.
4. Use Pagecraft for the hard parts: wrap-safe containers, real tables,
   financial number formatting, accessible HTML structure, and proof commands.
5. Do not claim "done" from screenshots, source inspection, or Builder quality
   review alone. Name the checks that passed and the checks not run.

## Workflow

1. **Load the local contract.** Read `DESIGN.md`, `docs/uxos.md`,
   `config/uxos/*.json`, `.builderrules`, `.builder/rules/*.mdc`, and this
   skill's references.
2. **Choose the path.** If Builder auth/workflow is available on the current
   machine, use Builder/Fusion on a branch or draft PR. If not, produce the
   Builder prompt/brief and make only repo-local edits you can verify.
   See `references/builder-workflow.md`.
3. **Route brand.** Load the relevant brand skill or token source before visual
   decisions. See `references/brand-routing.md`.
4. **Create or edit the artifact.** Keep it source-backed, self-contained where
   appropriate, and small enough to review. Preserve auth/data scripts in app
   pages. Do not invent numbers, claims, public copy, or client-facing strategy.
5. **Harden HTML.** Fix text wrap from the container outward, normalize tables
   and numeric columns, add states for data-bearing UI, and remove generic AI UI
   tells. See `references/html-quality-gates.md`.
6. **Verify and report.** Run the narrowest matching Builder/Pagecraft/brand
   checks, then report files changed, proof, and residual visual risk.

## Builder Prompt Shape

Give Builder a source-grounded brief instead of taste adjectives:

```text
Use the Builder Pagecraft HTML workflow.
Artifact: <report/dashboard/portal page/prototype>
Reader and decision: <who reads it and what decision/action it supports>
Brand route: <LJB client brand | Bogdan Baciu | other client brand>
Source files/data: <paths>
Required structure: <sections, tables, states, calls to action>
Must preserve: <auth/data loading/scripts/forms/claims>
Must avoid: generic AI palette, nested cards, decorative blobs, fake numbers,
unsupported copy, broken wrap, left-aligned numeric columns
Acceptance gates: pagecraft_qa, brand/client-brand check, builder_output_review,
targeted browser/render proof if layout risk is high
```

## Load References

- `references/builder-workflow.md` when Builder/Fusion, CLI auth, draft PRs, or
  workspace routing are in scope.
- `references/brand-routing.md` before applying Bogdan, LJB, or another client
  brand.
- `references/html-quality-gates.md` before final edits or closeout.

## Done Report

Report:

- Builder path used: Fusion/CLI/draft PR, or local fallback and why.
- Brand route and source files used.
- Pagecraft/UX/brand checks run, with status tokens where available.
- Whether browser/render inspection was run.
- Any unresolved `TBU`, placeholder data, unverified claims, or visual risk.
