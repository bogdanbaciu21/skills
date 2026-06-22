---
name: deep-decide
description: Run a high-thinking decision workflow that evaluates options through multiple independent model/provider perspectives, forces dissent, ranks the options, and returns one synthesized verdict with assumptions, evidence gaps, and an action plan. Bring your own API keys (Anthropic, OpenAI, and/or Gemini). Use when someone says "deep-decide", "mega decide", "pressure-test this decision", "evaluate options deeply", "which option should I pick", "rank these options", "stress-test this choice", or asks for a multi-model decision review. Do not use for pure factual research; use a deep-research skill for source discovery or long research reports, then feed its findings in here.
---

# Deep-Decide

Use this when someone needs a better decision, not just more information. The
workflow is: independent perspectives, then forced dissent, then one synthesized
verdict. It is portable and self-contained: a bundled Python script
(`scripts/deep_decide.py`, standard library only) makes the model calls using
keys you supply in your own environment.

## What it does NOT do

- It is not a research tool. For gathering facts, market data, or sources, run a
  deep-research skill first and paste the findings in as context. Deep-decide
  reasons over what it is given; it does not browse.
- It does not execute the decision. It recommends; it never sends, deploys,
  buys, or commits anything.
- Consensus is not proof. The verdict preserves dissent and TBU assumptions on
  purpose; it does not launder uncertainty into false confidence.

## Bring your own keys

The script reads credentials from the environment. Set at least one; set more
than one to get genuine cross-model dissent (perspectives are rotated across the
providers you configured):

Each default is that provider's current flagship, and the calls run at high
reasoning effort with adaptive thinking on where the provider supports it.
Override any model with its env var, or the depth with `DEEP_DECIDE_EFFORT`
(`low` | `medium` | `high` | `xhigh` | `max`, default `high`).

| Env var | Provider | Model env override | Default model |
|---|---|---|---|
| `ANTHROPIC_API_KEY` | Claude | `DEEP_DECIDE_ANTHROPIC_MODEL` | `claude-opus-4-8` |
| `OPENAI_API_KEY` | OpenAI | `DEEP_DECIDE_OPENAI_MODEL` | `gpt-5` |
| `GEMINI_API_KEY` | Gemini | `DEEP_DECIDE_GEMINI_MODEL` | `gemini-2.5-pro` |
| `OPENROUTER_API_KEY` | OpenRouter (any model) | `DEEP_DECIDE_OPENROUTER_MODEL` | `openai/gpt-5` |
| `CURSOR_API_KEY` (+ `CURSOR_API_BASE`) | Cursor | `DEEP_DECIDE_CURSOR_MODEL` | `gpt-5` |

A subscription (ChatGPT, Claude.ai, etc.) is not an API key. These calls bill
your API account. Check what is configured before running:

```bash
python3 scripts/deep_decide.py --providers
```

## User-facing contract

When someone says `deep-decide` or a nearby trigger, treat the skill as the
interface. Do not lead with a raw terminal command.

1. Restate the decision, options, and criteria if they are clear.
2. Run the no-cost plan and show the provider/perspective/call-count breakdown.
3. State the paid-call count, then run live only after the person approves paid
   calls in the current turn (or explicitly asked for a live run).
4. Return the verdict in plain language: recommendation, the dissent that
   matters, assumptions to verify, and next actions.

If options or criteria are missing but can be reasonably inferred, infer them
and mark them as inferred. Ask a question only when the decision would be
materially distorted without the missing information.

## Running it

No-cost plan (default: prints which providers it found and what it would do, and
makes no API calls):

```bash
python3 scripts/deep_decide.py "Should we do X or Y?" \
  --option "Do X" --option "Do Y"
```

Live run (paid):

```bash
python3 scripts/deep_decide.py "Should we do X or Y?" \
  --option "Do X" --option "Do Y" \
  --criterion "12-month cash impact" \
  --criterion "team adoption" \
  --execute
```

Run with no decision argument to be prompted for it interactively. Override the
four default perspectives with `--perspective "label: what this lens focuses on"`
(repeatable). Output bundles are written under `./deep-decide-runs/<slug>/`
(`verdict.md`, `combined.md`, `manifest.json`, one file per perspective);
override the location with `--out-dir`.

Status tokens (first stdout word; exit 0 only on `OK_*`): `OK_PLAN`,
`OK_DECIDE`, `OK_PROVIDERS`, `ERR_NO_PROVIDERS`, `ERR_NO_DECISION`, `ERR_RUN`.

## Default shape

The default bundle is five paid calls: four perspective passes plus one final
synthesis. The default perspectives are:

- `operator`: execution reality, dependencies, operational drag, what breaks.
- `skeptic`: red-team critique, hidden assumptions, failure modes.
- `finance`: ROI, cash/time cost, opportunity cost, operating leverage.
- `stakeholder`: adoption, incentives, trust, communication burden.

With several keys set, those four are spread across providers (e.g. operator on
Claude, skeptic on OpenAI) so the dissent is cross-model, not one model arguing
with itself. The synthesis "chair" defaults to Claude when available.

## The research arsenal (built in)

This skill ships its own evidence layer, `scripts/research_stack.py`: a catalog
of 17 research providers across three tiers, with live bring-your-own-keys
adapters for the search-capable ones. See the whole thing and what is configured:

```bash
python3 scripts/research_stack.py --stack    # or: python3 scripts/deep_decide.py --stack
```

Tiers:

- Deep web research: Exa, Firecrawl, Parallel.ai, Gemini Deep Research, Browserbase.
- Scholarly / academic: arXiv, OpenAlex, Crossref, PubMed, Semantic Scholar, CORE,
  Google Scholar (via SearchAPI/SerpAPI). arXiv, OpenAlex, Crossref, and PubMed
  work with no key at all.
- GitHub / code: GitHub code search, GitHub repo search, grep.app, Exa GitHub
  scan, Sourcegraph. grep.app needs no key.

Gather live, cited evidence on its own:

```bash
python3 scripts/research_stack.py "your question" -n 5 --tier academic
```

Or seed it straight into a decision so the perspectives reason over real sources
instead of guesses:

```bash
python3 scripts/deep_decide.py "Should we adopt approach X?" \
  --option "X" --option "status quo" \
  --research "evidence for and against approach X" --execute
```

Each finding is tagged with its source and URL and is injected as "treat as
leads to verify, not proven truth." Providers marked `catalog` in `--stack`
(Parallel, Gemini Deep Research, Browserbase, CORE, Google Scholar, Sourcegraph)
are part of the stack and shown with their env vars, but use async/job or
key-gated APIs out of scope for the synchronous evidence pass; the `live`
providers are queried directly. Always verify load-bearing claims against
current primary sources before acting on the verdict.

## Gotchas

- Pure standard library, no `pip install`. If `python3 scripts/deep_decide.py
  --providers` runs, you are ready.
- `--execute` is the only thing that spends money. Everything else is free and
  offline.
- One key is fine: the run becomes single-provider, multi-perspective. The
  cross-model dissent advantage only appears with two or more keys.
- A perspective that fails (bad key, rate limit) is recorded in `manifest.json`
  and the run continues with the rest; the run only fails if every perspective
  fails.
- Do not use this as a publishing or outbound-action gate. It produces a
  recommendation, nothing else.
