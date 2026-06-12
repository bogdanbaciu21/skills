# Diagram Patterns

Use this reference when the primary deliverable is an HTML/SVG diagram.

## Source Map

Extract these before drawing:

- Actors: humans, agents, schedulers, services, clients.
- Systems: apps, workers, MCP servers, APIs, databases, files, queues.
- Boundaries: trust, network, repo, machine, client/internal, approval gates.
- Flows: read path, write path, failure path, retry path, manual override.
- Proof: source files, logs, commands, dashboards, or tickets that support the
  diagram.

Mark missing facts as `TBU`. Do not turn unknowns into plausible-looking boxes.

## Grammar

- Zones: large dashed or tinted regions for machine, repo, trust, or ownership
  boundaries.
- Nodes: one system/component per node. Use type labels for `actor`, `worker`,
  `api`, `store`, `queue`, `gate`, `external`, or `artifact`.
- Edges: directional paths. Label payload, protocol, cadence, or side effect
  when that changes how the system is understood.
- Flows: named sequences. A flow can dim unrelated edges and highlight only the
  path for create/read/sync/failure/recovery.
- Detail: selected node metadata belongs in a compact detail panel, not inside
  the node.

## Layout Recipes

- Layered stack: clients left, app/control plane center, stores/backends right,
  operations below.
- Sequence flow: actors across the top, lifecycle steps left-to-right, failure
  branch below the happy path.
- Data lineage: source systems left, normalization in the center, derived
  artifacts/reports right, freshness and ownership at the bottom.
- Agent operating model: sources, context cache, tool gates, execution lane,
  proof packet, human approval boundary.
- Incident map: symptom, blast radius, current guard, missing guard, proposed
  repair, proof path.

## Interaction

- Use buttons/chips for named flows only when they clarify the system.
- Keep one "Everything" or "Overview" state.
- Respect `prefers-reduced-motion`; animated edges should still be legible when
  animation is disabled.
- Keyboard focus should reach controls. Node click handlers should also support
  keyboard activation when nodes are interactive.

## Verification

- Check framing at desktop and mobile widths. The main diagram must be visible,
  not clipped into a tiny unreadable thumbnail.
- Check text labels for overflow inside nodes.
- Check light and dark mode if present.
- Run available Pagecraft/brand gates. For Dan-owned work, `brand_lint.py` should
  pass or every warning should be intentionally explained.
- Confirm the final diagram contains no unreported `TBU` placeholders.
