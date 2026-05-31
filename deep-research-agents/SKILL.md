---
name: deep-research-agents
description: "Use Dan's three paid deep-research providers as one capability: Claude Managed Agent, Gemini Deep Research, and Parallel.ai. Trigger when the user asks for deep research, a research harness, multi-angle research fan-out, five angles, Workflow tool unavailable, Gemini API deep research, Claude managed agent research, Parallel.ai research, or wants the same research methodology to work across repos such as dans-brain, bogdanbaciu-dot-com, and Acme."
---

# Deep Research Agents

## Overview

Dan has three research backends that should be treated as one shared capability:
Claude Managed Agent, Gemini Deep Research, and Parallel.ai. If a requested
methodology expects a missing `Workflow` tool, do not stop there; use the local
provider harness or the repo-specific surface instead.

## Canonical Harness

Prefer `/root/dans-brain` when you need a repo-neutral research run:

```bash
cd /root/dans-brain && uv run python bin/deep_research.py --list-providers
cd /root/dans-brain && uv run python bin/deep_research.py "research question" --dry-run
cd /root/dans-brain && uv run python bin/deep_research.py "research question"
```

The harness writes provider outputs to `state/deep-research/<timestamp>-<slug>/`
with one markdown file per provider plus `combined.md` and `manifest.json`.
`state/` is git-ignored runtime data.

For multi-angle research, use repeated `--angle` flags. The harness requires
`--allow-many` when the plan exceeds three upstream runs because five angles
times three providers is fifteen paid calls:

```bash
cd /root/dans-brain && uv run python bin/deep_research.py "overall question" \
  --angle "market map" \
  --angle "technical feasibility" \
  --angle "risks and counter-evidence" \
  --allow-many
```

## Repo Surfaces

- `dans-brain`: `bin/deep_research.py` and provider plumbing in
  `bin/deep_research_agents.py`; `bin/discover_sources.py` reuses that provider
  layer and defaults to all three engines. Use `--plan-only` for a no-API check.
- `bogdanbaciu-dot-com`: Phoenix modules under `lib/bogdan/research/` and the
  admin `/admin/research` surface.
- `acme`: client portal research functions under
  `client-portal/netlify/functions/research-*`, with provider `"all"` fanning out to
  Claude, Gemini, and Parallel.ai.

## Operating Rules

- Keep secrets local: `ANTHROPIC_API_KEY`, `GEMINI_API_KEY`, and
  `PARALLEL_API_KEY` belong in untracked env/config, never in repo files.
- Treat provider reports as source material, not verified final truth. Synthesize
  conflicts explicitly and verify important, time-sensitive, legal, medical, or
  financial claims with current primary sources.
- Use Gemini for broad landscape/source discovery, Parallel.ai for heavily cited
  source coverage, and Claude Managed Agent for synthesis, skeptical review, and
  contradiction checks.
- If running in `dans-brain`, check
  `docs/capabilities/deep-research-agents.md` and
  `config/capabilities.json` before inventing a new harness or searching old
  transcripts for setup details.
