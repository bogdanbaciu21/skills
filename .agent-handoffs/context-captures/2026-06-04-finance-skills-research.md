# Finance Skills Research Insight Lock

## Why This Matters

This capture preserves the decision logic from an extended finance-skills research run in `/Users/danb/Desktop/skills`. The session combined local repo scanning, public `skills.sh` searches, six Codex subagents, and a paid 15-call deep-research harness across Claude Managed Agent, Gemini Deep Research, and Parallel.ai.

Future sessions should not rerun that paid research by default. Start from the committed scan and raw bundle pointers below, then build or refine the next finance skill.

## Trigger / Deadline

No external meeting or deadline was named. The practical trigger is future work on finance-oriented skills, especially `excel-wow`, `fpna-variance-pack`, `finance-agent-guardrails`, `accounting-data-quality`, SEC/XBRL analysis, reconciliation, and QBO close evidence.

## Core Read

- **Observed:** The durable decision artifact is `agent-research/2026-06-04-finance-skills-scan.md`.
- **Observed:** The paid deep-research bundle completed 15/15 jobs successfully: 5 research angles x 3 providers.
- **Observed:** The latest committed update is `9fc49a0 Incorporate paid finance skills research`; the initial research artifact was `6fbcca4 Add finance skills research scan`.
- **Inferred:** The local finance skill suite should be built as a small system, not a single giant "finance expert" skill.
- **Actionable:** Start with `excel-wow`, then `fpna-variance-pack`, then `finance-agent-guardrails` or a shared guardrail reference, then `accounting-data-quality`, then SEC/XBRL skills.
- **Actionable:** Keep `pagecraft/skills/number-formats` as the formatting layer. Do not duplicate Macabacus-style format codes inside `excel-wow`.
- **Do not use externally:** Do not cite the paid provider reports directly in client-facing material without rechecking the underlying public sources.

## Fresh Insights

- **Guardrails moved up.** Paid research changed the roadmap by making finance guardrails a first-class layer. Source ledgers, pre-execution validation gates, role separation, user-permission inheritance, and approval thresholds should be reusable across finance skills.
- **SEC/XBRL is stronger than expected.** The research found strong open-source and MCP lanes around `edgartools[ai]`, `sec-api`, `tidyxbrl`, `xbrl-filings-api`, EdgarTools MCP, and `sec-edgar-mcp`. Build `sec-filing-analyst` and `xbrl-financials-normalizer` as a serious public-company/IB lane.
- **Data quality should have modes.** `accounting-data-quality` should start lightweight with `pandera` fixture checks and simple JSON/HTML evidence. Great Expectations, Soda, and dbt are better for production governance rather than the first local eval.
- **Commercial platforms are reference architectures.** Datarails/VenaAI, Rogo/Subset/Endex, FloQast/BlackLine/Safebooks, and V7/CapIQ/PitchBook/FactSet patterns should inform design, but local skills should not depend on proprietary data products unless the user supplies exports or credentials.
- **`excel-wow` remains first.** It should become a model build/review/audit skill with workbook inspection, formula integrity checks, source ledger, scenario controls, and guardrail references.

## Contradictions To Hold

- **Install vs build:** Some useful installable skills exist, but the user's edge is a custom FP&A/CFO-grade skill suite with deterministic checks, not simply installing community finance helpers.
- **Autonomy vs accountability:** Finance agents can automate ingestion, checks, and draft outputs, but humans must own judgment-heavy explanations, client-facing conclusions, filings, journal entries, and valuation calls.
- **Public data vs proprietary data:** SEC/XBRL public-data workflows are strong; CapIQ/PitchBook/FactSet-style workflows should accept user-provided exports rather than pretending public data is a full replacement.
- **Generic finance expert vs workflow skills:** Broad "finance expert" skills are less useful than narrow workflows with inputs, artifacts, checks, and residual-risk reporting.

## Evidence And Source Pointers

- Committed scan: `/Users/danb/Desktop/skills/agent-research/2026-06-04-finance-skills-scan.md`
- Raw paid deep-research bundle: `/Users/danb/src/dans-brain/state/deep-research/20260604T135410Z-find-reusable-agent-skills-and-skill-designs-for-fp-a-`
- Raw combined report: `/Users/danb/src/dans-brain/state/deep-research/20260604T135410Z-find-reusable-agent-skills-and-skill-designs-for-fp-a-/combined.md`
- Deep-research harness: `/Users/danb/src/dans-brain/bin/deep_research.py`
- Prior `excel-wow` build handoff: `/Users/danb/Desktop/skills/.agent-handoffs/20260531-130403-excel-wow-build.md`
- Commit: `6fbcca4 Add finance skills research scan`
- Commit: `9fc49a0 Incorporate paid finance skills research`

## Open Questions

- Should `finance-agent-guardrails` be a standalone skill, or should it be a shared reference consumed by each finance skill?
- Should the next session build `excel-wow` end to end, or first scaffold the guardrail reference so `excel-wow` can inherit it?
- Should any external skills be installed, or should they remain design references until the local suite exists?
- Which data path matters first for the user: FP&A workbooks, QBO close evidence, SEC/XBRL public-company analysis, or reconciliation from exports?
- Should the raw paid bundle remain only in `dans-brain/state`, or should a scrubbed excerpts file be added to this repo later?

## Downstream Hooks

Keywords and phrases that should retrieve this capture:

- finance skills scan
- finance skill roadmap
- paid deep research finance skills
- `excel-wow`
- `fpna-variance-pack`
- `finance-agent-guardrails`
- `accounting-data-quality`
- `sec-filing-analyst`
- `xbrl-financials-normalizer`
- `finance-reconciliation-agent`
- `qbo-close-control-board`
- `edgartools[ai]`
- `pandera`
- `pagecraft/skills/number-formats`
- `/Users/danb/Desktop/skills/agent-research/2026-06-04-finance-skills-scan.md`

## Future-Agent Note

Start by reading `agent-research/2026-06-04-finance-skills-scan.md`, then the relevant raw provider report only if the next build decision depends on it. Do not rerun the 15-call paid harness unless the user explicitly asks for a refresh or the ecosystem has materially changed.

If building `excel-wow`, use `.agent-handoffs/20260531-130403-excel-wow-build.md` plus the finance scan. Keep the first implementation concrete: `SKILL.md`, `agents/openai.yaml`, `references/modeling-standards.md`, `references/model-review-checklist.md`, `scripts/inspect_workbook.py`, and `evals/workbook_audit_fixture_eval.py`.

Preserve these design boundaries:

- `excel-wow` owns workbook logic, model architecture, scenario controls, and inspection.
- `number-formats` owns financial number formatting and provenance colors.
- source-system skills start read-only and require explicit approval for writes.
- SEC/XBRL skills must cite accession/form/date/source URL for every extracted fact.
- every finance skill needs a source ledger and deterministic validation gate.

## Privacy Boundary

This memo is safe as a repo-local planning artifact. It does not include API keys, credentials, client data, or a raw chat transcript. The raw provider outputs are local runtime evidence and should not be copied wholesale into public artifacts. Reuse the decisions and pointers freely inside this repo; recheck primary sources before quoting external claims in public or client-facing material.

## Capture Metadata

- Created at: 2026-06-04 19:07:41 +04 +0400
- Scope: current chat plus local repo artifacts and paid deep-research bundle pointers.
- Raw transcript saved: no.
- Source limitation: synthesized from visible conversation context, committed repo artifact, git history, and local raw provider bundle paths.

