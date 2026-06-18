---
name: html-diagram
description: "Create self-contained HTML architecture, system, stack, flow, data-lineage, or operating-model diagrams with a full-screen SVG-first canvas, Pagecraft-safe layout, and brand-aware tokens. Use when the user asks for an architecture diagram, system diagram, stack map, sequence or flow visualization, data lineage map, 'diagram this', 'make the architecture click', or a visual explanation where the diagram is the primary artifact. Boundary: use html for report/prototype/plan pages; use pagecraft/verify-text-wrap to finish or validate existing HTML."
---

# HTML Diagram

Create a self-contained HTML file where the diagram is the primary artifact.
Use SVG for the main canvas and keep prose minimal.

## Workflow

1. Map the system before drawing: actors, systems, stores, trust boundaries,
   owners, inputs, outputs, side effects, and the flows or states the reader
   needs to understand. Mark unknowns as `TBU`; do not infer architecture that
   is not grounded in the source.
2. Load `references/diagram-patterns.md` and use
   `assets/templates/fullscreen-svg-diagram.html` as a starter when helpful.
3. Use repo/client/Bogdan design tokens first. Style SVG through CSS variables
   and classes. Do not hard-code hex values inside SVG nodes or paths.
4. Prefer a full-screen stage with zones, nodes, edges, labels, a compact legend,
   and optional flow chips that highlight one sequence at a time.
5. Verify like any other HTML artifact: brand lint when present, Pagecraft
   keystone check, browser inspection for desktop/mobile framing, and reduced
   motion behavior if animation is used.

## Gotchas

- The diagram is a model of a real system, not decoration. Show trust
  boundaries, write paths, retries, queues, stores, and human gates when they
  matter.
- Avoid spaghetti. If there are too many edges, split by flow state, lane, or
  zoom level instead of drawing every edge at once.
- Keep labels stable and short. Put detail in a side panel or legend, not in
  overflowing node text.
- Do not use Mermaid or screenshots as the final artifact when the user asked
  for a polished HTML diagram. SVG gives better control, theming, and review.
- Do not start a local server unless the artifact needs live runtime behavior.
  Static file checks are enough for ordinary diagrams.

## References

- `references/diagram-patterns.md` - diagram grammar, layout recipes,
  interaction rules, and verification gates.
- `assets/templates/fullscreen-svg-diagram.html` - original starter for a
  responsive, SVG-first, flow-highlighted diagram.
- `../html/SKILL.md` - general self-contained HTML artifact workflow.
- `../pagecraft/SKILL.md` - Pagecraft overview and verification workflow.
- `../verify-text-wrap/SKILL.md` - responsive/wrap validation.
