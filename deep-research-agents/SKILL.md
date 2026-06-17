---
name: deep-research-agents
description: "Use Dan's paid deep-research providers as one capability: Claude Managed Agent, Gemini Deep Research, Parallel.ai, Exa, and Firecrawl Research Index. Trigger when the user asks for deep research, a research harness, multi-angle research fan-out, five angles, Workflow tool unavailable, Gemini API deep research, Claude managed agent research, Parallel.ai research, or wants the same research methodology to work across repos such as dans-brain, bogdanbaciu-dot-com, and Acme."
---

# Deep Research Agents

## Overview

Dan has five research backends that should be treated as one shared capability:
Claude Managed Agent, Gemini Deep Research, Parallel.ai, Exa Agent, and Firecrawl
Research Index. If a requested methodology expects a missing `Workflow` tool, do
not stop there; use the local provider harness or the repo-specific surface
instead.

## Default Flow (local preprocess first)

For a raw research question, **do not** send the question straight to paid
providers. `bin/deep_research.py` now runs the GEX44 local preprocessor by
default: discover URLs, scrape in parallel, dedupe chunks, embed-rank, then bill
providers only on the curated prompt.

```bash
DANS_BRAIN_ROOT="${DANS_BRAIN_ROOT:-$HOME/src/dans-brain}"
cd "$DANS_BRAIN_ROOT"

# 1) No-cost: provider status + preprocess discovery + planned paid runs
uv run python bin/deep_research.py "research question" --dry-run

# 2) Live: preprocess locally, then fan out paid providers on curated prompt
uv run python bin/deep_research.py "research question"

# Escape hatches
uv run python bin/deep_research.py "research question" --no-preprocess
uv run python bin/deep_research.py --prompt-file state/research-preprocess/<bundle>/curated_prompt.md --no-preprocess
```

Preprocessor-only (no paid calls):

```bash
cd "$DANS_BRAIN_ROOT" && uv run python bin/research_preprocess.py "research question" --dry-run
cd "$DANS_BRAIN_ROOT" && uv run python bin/research_preprocess.py "research question"
```

If preprocess fails (embed tunnel down), `deep_research.py` **fails open** to the
raw question and prints `WARN_DEEP_RESEARCH_PREPROCESS_SKIPPED`. Prefer running
on the VPS with the GEX44 scheduler tunnel up (`EMBED_API_BASE` on `:18081`).

## Canonical Harness

Prefer the local `dans-brain` checkout when you need a repo-neutral research
run. Do not assume a Linux/root home path; resolve the project root explicitly:

```bash
DANS_BRAIN_ROOT="${DANS_BRAIN_ROOT:-$HOME/src/dans-brain}"
test -f "$DANS_BRAIN_ROOT/bin/deep_research.py"
cd "$DANS_BRAIN_ROOT" && uv run python bin/deep_research.py --list-providers
cd "$DANS_BRAIN_ROOT" && uv run python bin/deep_research.py "research question" --dry-run
```

The harness writes provider outputs to `state/deep-research/<timestamp>-<slug>/`
with one markdown file per provider plus `combined.md` and `manifest.json`.
When preprocess ran, `manifest.json` also records the local bundle under
`state/research-preprocess/` and token reduction stats. `state/` is git-ignored
runtime data.

Before any live provider call, check local provider availability:

```bash
python3 /Users/danb/src/skills/deep-research-agents/scripts/check_provider_env.py
```

Then run a no-cost harness check:

```bash
cd "$DANS_BRAIN_ROOT" && uv run python bin/deep_research.py "research question" --dry-run
```

Only run the paid call after the user confirms the provider count and expected
call count. ChatGPT, Claude, Gemini, or Parallel subscriptions do not imply API
credits for these harness calls.

For multi-angle research, use repeated `--angle` flags. The harness requires
`--allow-many` when the plan exceeds three upstream runs because five angles
times three providers is fifteen paid calls:

```bash
cd "$DANS_BRAIN_ROOT" && uv run python bin/deep_research.py "overall question" \
  --angle "market map" \
  --angle "technical feasibility" \
  --angle "risks and counter-evidence" \
  --allow-many
```

## Repo Surfaces

- `dans-brain`: `bin/deep_research.py` (default `--preprocess`), local grunt work in
  `bin/research_preprocess.py`, provider plumbing in `bin/deep_research_agents.py`;
  `bin/discover_sources.py` reuses that provider layer and defaults to all engines.
  Use `--plan-only` for a no-API check.
- `bogdanbaciu-dot-com`: Phoenix modules under `lib/bogdan/research/` and the
  admin `/admin/research` surface.
- `acme`: client portal research functions under
  `client-portal/netlify/functions/research-*`, with provider `"all"` fanning out to
  Claude, Gemini, and Parallel.ai.

## Operating Rules

- Keep secrets local: `ANTHROPIC_API_KEY`, `GEMINI_API_KEY`, and
  `PARALLEL_API_KEY` belong in untracked env/config, never in repo files.
- Confirm paid-call scope before execution: provider set, angle count, total
  upstream calls, and whether `--allow-many` is required. If the user has not
  confirmed cost exposure, stop at `--dry-run`.
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
