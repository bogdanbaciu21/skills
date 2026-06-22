#!/usr/bin/env python3
"""deep_decide.py: a self-contained, bring-your-own-keys decision workflow.

Runs a high-thinking decision review. It evaluates your options through several
independent "perspectives" (operator, skeptic, finance, stakeholder), forces
each one to surface its killer assumption and best counterargument, then a final
"chair" pass synthesizes one verdict with ranked options, the dissent that
matters, assumptions to verify, and an action plan.

It is portable: pure Python standard library (no pip install), no hard-coded
paths, and it reads ALL credentials from your own environment. If you set more
than one provider key, the perspectives are rotated across providers so you get
genuine cross-model dissent; with one key it runs every perspective on that one
provider.

Bring your own keys (set whichever you have; at least one is required):

    ANTHROPIC_API_KEY   to Claude   (model: $DEEP_DECIDE_ANTHROPIC_MODEL, default claude-opus-4-8)
    OPENAI_API_KEY      to OpenAI   (model: $DEEP_DECIDE_OPENAI_MODEL,    default gpt-4o)
    GEMINI_API_KEY      to Gemini   (model: $DEEP_DECIDE_GEMINI_MODEL,    default gemini-2.0-flash)

By default the script prints a NO-COST plan (which providers it found, the
perspectives it will run, and the total paid-call count). Pass --execute to make
the real paid calls.

Usage:
    python3 deep_decide.py --providers                 # show which keys are configured
    python3 deep_decide.py "Should we do X or Y?"      # no-cost plan
    python3 deep_decide.py "Should we do X or Y?" \\
        --option "Do X" --option "Do Y" --execute      # live run (paid)
    python3 deep_decide.py                              # interactive: prompts for the decision

Status tokens (first stdout word; exit 0 only on OK_*):
    OK_PLAN              printed a no-cost plan
    OK_DECIDE            ran a live decision and wrote a bundle
    OK_PROVIDERS         printed provider status
    ERR_NO_PROVIDERS     no provider key is set in the environment
    ERR_NO_DECISION      no decision text supplied
    ERR_RUN              a live run failed (details on stderr)
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import textwrap
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass

# Optional research arsenal (sibling module). Absent is fine: deep-decide still
# runs decision-only without it.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    import research_stack
except Exception:  # noqa: BLE001
    research_stack = None


# --------------------------------------------------------------------------- #
# Providers. Each entry is (env-var, model-env, default-model, call-fn).
# Add a provider by writing a call_<name>(prompt, model) that returns text.
# --------------------------------------------------------------------------- #

ANTHROPIC_VERSION = "2023-06-01"
HTTP_TIMEOUT = 600  # top reasoning models at high effort can take minutes

# Reasoning depth applied to every provider that supports it. Override per run
# with DEEP_DECIDE_EFFORT. Anthropic scale: low | medium | high | xhigh | max.
DEFAULT_EFFORT = os.environ.get("DEEP_DECIDE_EFFORT", "high")
_OPENAI_EFFORT = DEFAULT_EFFORT if DEFAULT_EFFORT in {"low", "medium", "high"} else "high"


def _http_post_json(url: str, headers: dict, payload: dict) -> dict:
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    with urllib.request.urlopen(req, timeout=HTTP_TIMEOUT) as resp:
        return json.loads(resp.read().decode("utf-8"))


def call_anthropic(prompt: str, model: str) -> str:
    """Anthropic flagship with adaptive thinking + effort dialed up."""
    key = os.environ.get("ANTHROPIC_API_KEY", "")
    body = {
        "model": model,
        "max_tokens": 16000,
        "messages": [{"role": "user", "content": prompt}],
        "thinking": {"type": "adaptive"},
        "output_config": {"effort": DEFAULT_EFFORT},
    }
    out = _http_post_json(
        "https://api.anthropic.com/v1/messages",
        {"x-api-key": key, "anthropic-version": ANTHROPIC_VERSION, "content-type": "application/json"},
        body,
    )
    parts = [b.get("text", "") for b in out.get("content", []) if b.get("type") == "text"]
    return "\n".join(p for p in parts if p).strip()


def _openai_compatible(prompt: str, model: str, *, base: str, key: str) -> str:
    """Any OpenAI-compatible chat endpoint (OpenAI, OpenRouter, Cursor, ...)."""
    body = {
        "model": model,
        "max_completion_tokens": 16000,
        "messages": [{"role": "user", "content": prompt}],
        "reasoning_effort": _OPENAI_EFFORT,
    }
    out = _http_post_json(base, {"Authorization": f"Bearer {key}", "content-type": "application/json"}, body)
    return (out["choices"][0]["message"]["content"] or "").strip()


def call_openai(prompt: str, model: str) -> str:
    return _openai_compatible(prompt, model, base="https://api.openai.com/v1/chat/completions",
                              key=os.environ.get("OPENAI_API_KEY", ""))


def call_openrouter(prompt: str, model: str) -> str:
    return _openai_compatible(prompt, model, base="https://openrouter.ai/api/v1/chat/completions",
                              key=os.environ.get("OPENROUTER_API_KEY", ""))


def call_cursor(prompt: str, model: str) -> str:
    # Cursor's OpenAI-compatible endpoint. Set CURSOR_API_BASE to its chat URL.
    base = os.environ.get("CURSOR_API_BASE", "")
    if not base:
        raise RuntimeError("set CURSOR_API_BASE to Cursor's OpenAI-compatible chat endpoint")
    return _openai_compatible(prompt, model, base=base, key=os.environ.get("CURSOR_API_KEY", ""))


def call_gemini(prompt: str, model: str) -> str:
    key = os.environ.get("GEMINI_API_KEY", "")
    url = (
        f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"
    )
    body = {"contents": [{"parts": [{"text": prompt}]}]}
    out = _http_post_json(url, {"content-type": "application/json"}, body)
    cand = out.get("candidates", [{}])[0]
    parts = cand.get("content", {}).get("parts", [])
    return "\n".join(p.get("text", "") for p in parts).strip()


# (key-env, model-env, default flagship model, call-fn). Models are each
# provider's current top model; override any with its DEEP_DECIDE_*_MODEL env var.
PROVIDERS = {
    "claude":     ("ANTHROPIC_API_KEY",  "DEEP_DECIDE_ANTHROPIC_MODEL",  "claude-opus-4-8", call_anthropic),
    "openai":     ("OPENAI_API_KEY",     "DEEP_DECIDE_OPENAI_MODEL",     "gpt-5",           call_openai),
    "gemini":     ("GEMINI_API_KEY",     "DEEP_DECIDE_GEMINI_MODEL",     "gemini-2.5-pro",  call_gemini),
    "openrouter": ("OPENROUTER_API_KEY", "DEEP_DECIDE_OPENROUTER_MODEL", "openai/gpt-5",    call_openrouter),
    "cursor":     ("CURSOR_API_KEY",     "DEEP_DECIDE_CURSOR_MODEL",     "gpt-5",           call_cursor),
}
PROVIDER_ORDER = ["claude", "openai", "gemini", "openrouter", "cursor"]


def configured_providers() -> list[str]:
    return [name for name in PROVIDER_ORDER if os.environ.get(PROVIDERS[name][0])]


def model_for(provider: str) -> str:
    _, model_env, default_model, _ = PROVIDERS[provider]
    return os.environ.get(model_env, default_model)


def run_provider(provider: str, prompt: str) -> str:
    _, _, _, fn = PROVIDERS[provider]
    return fn(prompt, model_for(provider))


# --------------------------------------------------------------------------- #
# Perspectives and prompts
# --------------------------------------------------------------------------- #

DEFAULT_PERSPECTIVES = [
    ("operator", "Execution reality: implementation path, operational drag, sequencing, dependencies, and what breaks first."),
    ("skeptic", "Red-team critique: hidden assumptions, failure modes, adverse selection, second-order risks, and why the favorite option could be wrong."),
    ("finance", "Capital allocation: ROI, cash/time cost, opportunity cost, operating leverage, reversibility, and how you would measure success."),
    ("stakeholder", "Adoption: the incentives, trust, and communication burden of the people affected, and the social path to making the decision stick."),
]

FINAL_VERDICT_SCHEMA = """# Decision Verdict

## Bottom Line
- Decision:
- Confidence (low / medium / high):
- Why now:

## Ranked Options
| Rank | Option | Strongest case for | Strongest case against | What would reverse this |
|---:|---|---|---|---|

## Dissent That Matters
(The objection most likely to be right that the recommendation overrides. Do not average it away.)

## Assumptions To Verify
(Mark anything you could not confirm as TBU. Never invent a fact, number, or source.)

## Action Plan (next 48 hours)

## Residual Risk
"""


def perspective_prompt(decision: str, options: list[str], criteria: list[str],
                       label: str, focus: str) -> str:
    opt_block = (
        "## Options\n\n" + "\n".join(f"{i}. {o}" for i, o in enumerate(options, 1))
        if options else "## Options\n\nIdentify the realistic options from the decision text."
    )
    crit_block = (
        "## Criteria\n\n" + "\n".join(f"{i}. {c}" for i, c in enumerate(criteria, 1))
        if criteria else "## Criteria\n\nInfer the decision criteria, but label inferred criteria clearly."
    )
    return textwrap.dedent(f"""\
        You are the `{label}` perspective in a multi-perspective decision review.

        Focus: {focus}

        Evaluate the decision below. Do not try to be neutral. Make the strongest
        useful case from your assigned perspective while staying accurate.

        ## Decision

        {decision}

        {opt_block}

        {crit_block}

        ## Output

        Return concise markdown with these sections:

        1. Recommendation: your preferred option, confidence, and why.
        2. Option scores: score each option 1-5 from your perspective.
        3. Killer assumption: the single assumption most likely to invalidate your answer.
        4. Best counterargument: the strongest case against your own recommendation.
        5. Evidence needed: what must be verified before acting.
        6. Reversal triggers: what new fact would change your mind.

        Rules:
        - Preserve uncertainty. Mark any unverified factual claim as TBU.
        - Do not average away tradeoffs; force the hard choice from this perspective.
        - If you cite a source, give enough detail to verify it later.
        """)


def synthesis_prompt(decision: str, options: list[str], criteria: list[str],
                     perspectives: list[tuple[str, str]]) -> str:
    blocks = []
    for label, text in perspectives:
        blocks.append(f"### Perspective: {label}\n\n{text}")
    joined = "\n\n".join(blocks)
    opt_line = ("\nOptions under consideration: " + "; ".join(options)) if options else ""
    crit_line = ("\nStated criteria: " + "; ".join(criteria)) if criteria else ""
    return textwrap.dedent(f"""\
        You are the chair of a decision review. Several independent perspectives have
        evaluated the same decision. Synthesize them into ONE verdict.

        ## Decision

        {decision}{opt_line}{crit_line}

        ## Perspectives

        {joined}

        ## Your job

        Produce the verdict in EXACTLY the structure below. Preserve real
        disagreement instead of splitting the difference; the "Dissent That Matters"
        section must name the objection most likely to be right that your
        recommendation overrides. Never invent a fact, number, name, or source. If a
        perspective asserted something unverified, carry it forward as TBU.

        {FINAL_VERDICT_SCHEMA}
        """)


# --------------------------------------------------------------------------- #
# Run plan
# --------------------------------------------------------------------------- #

@dataclass
class Job:
    label: str
    focus: str
    provider: str


def plan_jobs(perspectives: list[tuple[str, str]], providers: list[str]) -> list[Job]:
    jobs = []
    for i, (label, focus) in enumerate(perspectives):
        jobs.append(Job(label=label, focus=focus, provider=providers[i % len(providers)]))
    return jobs


def pick_chair(providers: list[str]) -> str:
    return "claude" if "claude" in providers else providers[0]


def slugify(text: str, max_len: int = 40) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return (s[:max_len].rstrip("-")) or "decision"


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #

def print_provider_status() -> None:
    configured = configured_providers()
    for name in PROVIDER_ORDER:
        env_var, _, _, _ = PROVIDERS[name]
        state = "set" if os.environ.get(env_var) else "missing"
        print(f"  {name:8s} {env_var:18s} {state:8s} model={model_for(name)}")
    print(f"\nConfigured providers: {', '.join(configured) if configured else '(none)'}")


def main() -> int:
    p = argparse.ArgumentParser(
        description="Multi-perspective decision review with forced dissent and one synthesized verdict.",
    )
    p.add_argument("decision", nargs="*", help="The decision/question. Omit to be prompted interactively.")
    p.add_argument("--option", action="append", default=[], help="A decision option. Repeatable.")
    p.add_argument("--criterion", action="append", default=[], help="A decision criterion. Repeatable.")
    p.add_argument("--perspective", action="append", default=[],
                   help="Custom perspective as 'label: focus'. Repeatable; overrides the default four.")
    p.add_argument("--execute", action="store_true", help="Make the real paid calls. Omit for a no-cost plan.")
    p.add_argument("--providers", action="store_true", help="Show which decision-model keys are configured, then exit.")
    p.add_argument("--stack", action="store_true", help="Show the full research arsenal (deep, academic, GitHub), then exit.")
    p.add_argument("--research", metavar="QUERY", help="Gather live cited evidence across the research stack and seed it into the decision.")
    p.add_argument("--out-dir", default="deep-decide-runs", help="Where to write run bundles (default: ./deep-decide-runs).")
    args = p.parse_args()

    if args.stack:
        if research_stack is None:
            print("ERR_RUN research_stack.py not found next to this script.", file=sys.stderr)
            return 2
        print("OK_PROVIDERS")
        print_provider_status()
        print(research_stack.render_stack())
        return 0

    if args.providers:
        print("OK_PROVIDERS")
        print_provider_status()
        return 0

    configured = configured_providers()
    if not configured:
        print("ERR_NO_PROVIDERS no provider key set. Set at least one of "
              "ANTHROPIC_API_KEY / OPENAI_API_KEY / GEMINI_API_KEY.", file=sys.stderr)
        return 2

    decision = " ".join(args.decision).strip()
    if not decision and sys.stdin.isatty():
        try:
            decision = input("Decision/question: ").strip()
        except (EOFError, KeyboardInterrupt):
            decision = ""
    if not decision:
        print("ERR_NO_DECISION provide the decision text (positional) or run interactively.", file=sys.stderr)
        return 2

    # Optional: seed the decision with live, cited evidence from the research stack.
    evidence_brief = ""
    if args.research:
        if research_stack is None:
            print("ERR_RUN research_stack.py not found next to this script.", file=sys.stderr)
            return 2
        print(f"Gathering evidence: {args.research}", file=sys.stderr)
        findings, rerrors = research_stack.gather(args.research, n=5)
        evidence_brief = research_stack.findings_brief(findings)
        print(f"  gathered {len(findings)} finding(s)"
              + (f", {len(rerrors)} source error(s)" if rerrors else ""), file=sys.stderr)
        if findings:
            decision = (decision
                        + "\n\n## Research evidence (gathered live; treat as leads to verify, not proven truth)\n\n"
                        + evidence_brief)

    perspectives: list[tuple[str, str]] = []
    for raw in args.perspective:
        if ":" not in raw:
            print(f"ERR_RUN --perspective must be 'label: focus', got: {raw}", file=sys.stderr)
            return 2
        label, focus = raw.split(":", 1)
        perspectives.append((label.strip(), focus.strip()))
    if not perspectives:
        perspectives = list(DEFAULT_PERSPECTIVES)

    jobs = plan_jobs(perspectives, configured)
    chair = pick_chair(configured)
    paid_calls = len(jobs) + 1

    if not args.execute:
        print("OK_PLAN")
        print(f"\nDecision: {decision}")
        if args.option:
            print("Options: " + "; ".join(args.option))
        if args.criterion:
            print("Criteria: " + "; ".join(args.criterion))
        print(f"\nConfigured providers: {', '.join(configured)}")
        print("\nPerspective passes:")
        for j in jobs:
            print(f"  - {j.label:12s} via {j.provider} ({model_for(j.provider)})")
        print(f"Final synthesis: chair = {chair} ({model_for(chair)})")
        print(f"\nThis would be {paid_calls} paid model calls. Re-run with --execute to make them.")
        return 0

    # Live run.
    print(f"Running {len(jobs)} perspective pass(es) across {len(configured)} provider(s)...", file=sys.stderr)
    results: dict[str, str] = {}
    errors: list[str] = []

    def run_one(job: Job) -> tuple[str, str]:
        prompt = perspective_prompt(decision, args.option, args.criterion, job.label, job.focus)
        return job.label, run_provider(job.provider, prompt)

    with ThreadPoolExecutor(max_workers=max(1, len(jobs))) as pool:
        futures = {pool.submit(run_one, j): j for j in jobs}
        for fut in as_completed(futures):
            j = futures[fut]
            try:
                label, text = fut.result()
                results[label] = text
                print(f"  {label}: ok ({j.provider})", file=sys.stderr)
            except urllib.error.HTTPError as e:
                detail = e.read().decode("utf-8", "replace")[:300]
                errors.append(f"{j.label}/{j.provider}: HTTP {e.code} {detail}")
                print(f"  {j.label}: ERROR ({j.provider}) HTTP {e.code}", file=sys.stderr)
            except Exception as e:  # noqa: BLE001 (surface any provider failure, do not crash the run)
                errors.append(f"{j.label}/{j.provider}: {e}")
                print(f"  {j.label}: ERROR ({j.provider}) {e}", file=sys.stderr)

    ordered = [(label, results[label]) for label, _ in perspectives if label in results]
    if not ordered:
        print("ERR_RUN every perspective pass failed:", file=sys.stderr)
        for e in errors:
            print("  " + e, file=sys.stderr)
        return 1

    print(f"Synthesizing final verdict (chair = {chair})...", file=sys.stderr)
    try:
        verdict = run_provider(chair, synthesis_prompt(decision, args.option, args.criterion, ordered))
    except Exception as e:  # noqa: BLE001
        print(f"ERR_RUN synthesis failed: {e}", file=sys.stderr)
        return 1

    # Write a portable bundle under ./<out-dir>/<slug>/.
    out_root = os.path.abspath(args.out_dir)
    run_dir = os.path.join(out_root, slugify(decision))
    os.makedirs(run_dir, exist_ok=True)

    for label, text in ordered:
        with open(os.path.join(run_dir, f"perspective-{slugify(label, 24)}.md"), "w", encoding="utf-8") as f:
            f.write(f"# Perspective: {label}\n\n{text}\n")
    with open(os.path.join(run_dir, "verdict.md"), "w", encoding="utf-8") as f:
        f.write(verdict + "\n")
    combined = [f"# Decision\n\n{decision}\n"]
    if args.option:
        combined.append("## Options\n\n" + "\n".join(f"- {o}" for o in args.option) + "\n")
    for label, text in ordered:
        combined.append(f"---\n\n# Perspective: {label}\n\n{text}\n")
    combined.append("---\n\n" + verdict + "\n")
    with open(os.path.join(run_dir, "combined.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(combined))
    with open(os.path.join(run_dir, "manifest.json"), "w", encoding="utf-8") as f:
        json.dump({
            "decision": decision,
            "options": args.option,
            "criteria": args.criterion,
            "providers": configured,
            "chair": chair,
            "perspectives": [{"label": l, "provider": j.provider, "model": model_for(j.provider)}
                             for (l, _), j in zip(perspectives, jobs)],
            "errors": errors,
        }, f, indent=2)

    print(f"OK_DECIDE wrote {len(ordered)} perspective(s) + verdict -> {run_dir}")
    if errors:
        print(f"  ({len(errors)} perspective pass(es) failed; see manifest.json)", file=sys.stderr)
    print()
    print(verdict)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
