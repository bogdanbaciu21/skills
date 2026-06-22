# deep-decide: a decision engine, not a research dump

Most "AI for decisions" tools give you more information. That is rarely the
problem. When a decision is genuinely hard, you usually already have the facts.
What you are missing is a fair fight between the options, and an honest read of
the objection you are about to override.

`deep-decide` is a small, portable Claude skill that runs that fight for you.

## The shape of it

Give it a decision and a couple of options. It does three things:

1. **Independent perspectives.** Four lenses argue your options in parallel:
   an *operator* (what actually breaks first), a *skeptic* (hidden assumptions
   and failure modes), a *finance* view (cash, opportunity cost, reversibility),
   and a *stakeholder* view (incentives, trust, adoption). Each one is told not
   to be neutral. It makes the strongest honest case from its seat.

2. **Forced dissent.** Every perspective has to surface its single killer
   assumption and the best argument against its own recommendation. No lens gets
   to be quietly confident.

3. **One synthesized verdict.** A final pass ranks the options and, crucially,
   names the dissent that matters: the objection most likely to be right that the
   recommendation is overriding. Consensus is not laundered into false certainty.
   Anything it could not verify comes back marked TBU.

## Bring your own keys, and real cross-model dissent

The skill makes the model calls itself, reading your own API keys from the
environment. Set one key and it runs every perspective on that provider. Set two
or three (Claude, GPT, Gemini) and it rotates the perspectives across them, so
the disagreement is genuinely cross-model instead of one model nodding along with
itself.

It is pure Python standard library. No `pip install`, no framework, no hosted
service in the middle.

## A research arsenal, built in

A decision is only as good as the evidence under it. So the skill ships its own
evidence layer: a catalog of 17 research providers across three tiers, with live
bring-your-own-keys adapters for the search-capable ones.

- **Deep web research:** Exa, Firecrawl, Parallel.ai, Gemini Deep Research,
  Browserbase.
- **Scholarly and academic:** arXiv, OpenAlex, Crossref, PubMed, Semantic
  Scholar, CORE, Google Scholar. Four of those need no key at all.
- **GitHub and code:** GitHub code search, GitHub repo search, grep.app, Exa
  GitHub scan, Sourcegraph.

Run `--stack` to see the whole arsenal and exactly what is configured. Pass
`--research "<query>"` and the skill gathers real, cited findings across your
configured sources and seeds them into the decision, tagged as leads to verify
rather than proven truth, before the perspectives ever start reasoning.

## Why it is built this way

The hard rules are deliberate. It never invents a fact, number, or source. It
preserves disagreement instead of averaging it away. It recommends, but it never
sends, deploys, buys, or commits anything. And the no-cost plan is the default:
nothing spends money until you ask it to with `--execute`.

The goal is a better decision with its uncertainty intact, not a confident answer
that hides what it does not know.

Code and docs: https://github.com/bogdanbaciu21/skills/tree/main/deep-decide
