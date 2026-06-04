# Finance Skills Scan - 2026-06-04

## Executive Conclusion

The best path is not to install every finance-looking skill. The strongest setup is a small finance skill suite:

1. `excel-wow` as the core workbook/model build and audit engine.
2. `fpna-variance-pack` as the first recurring FP&A workflow.
3. `accounting-data-quality` as the shared control/check layer.
4. `finance-reconciliation-agent` for GL, bank, subledger, AR/AP, and export-based tie-outs.
5. `qbo-close-control-board` for read-only close evidence when QBO access is available.
6. `sec-filing-analyst` and `xbrl-financials-normalizer` for public-company analysis and valuation support.

The local repo already has one finance-adjacent production skill: `pagecraft/skills/number-formats`. The obvious next build is still `excel-wow`, which is currently a placeholder and should become the modeling/audit engine rather than a generic Excel helper.

## What Was Searched

Six parallel Codex research agents were used, which hit the practical subagent cap for this session:

| Track | Scope |
|---|---|
| 1 | Public agent-skills ecosystem and installable packages |
| 2 | GitHub repositories and open-source finance skill bundles |
| 3 | FP&A and CFO workflow map |
| 4 | Spreadsheet/modeling standards |
| 5 | Accounting, close, audit, QBO/Xero/NetSuite, data quality |
| 6 | Investment banking, valuation, markets, SEC/EDGAR/XBRL |

The local deep-research harness also produced a dry-run plan for 15 paid provider calls: 5 angles x 3 providers: Claude Managed Agent, Gemini Deep Research, and Parallel.ai. Those paid calls were not launched because the skill requires explicit confirmation after showing provider count and total calls.

Local commands used included:

```bash
npx --yes skills find finance
npx --yes skills find excel
npx --yes skills find spreadsheet
npx --yes skills find accounting
npx --yes skills find "financial modeling"
npx --yes skills find valuation
npx --yes skills find forecast
npx --yes skills find quickbooks
npx --yes skills find "SEC filings"
npx --yes skills find edgar
npx --yes skills find xbrl
npx --yes skills find "data quality"
npx --yes skills find dbt
npx --yes skills find "variance analysis"
npx --yes skills find reconciliation
npx --yes skills find "close management"
npx --yes skills find SOX
npx --yes skills find dashboard
npx --yes skills find "market data"
npx --yes skills add anthropics/financial-services --list
npx --yes skills add anthropics/financial-services-plugins --list
npx --yes skills add anthropics/knowledge-work-plugins --list
npx --yes skills add openai/skills --list
npx --yes skills add dbt-labs/dbt-agent-skills --list
```

## Install Or Inspect Shortlist

| Decision | Skill or bundle | Why it matters | Source |
|---|---|---|---|
| Install / adapt first | `openai/skills@spreadsheet` | Best generic Codex spreadsheet baseline: `.xlsx`, `.csv`, formulas, formatting, charts, recalculation/rendering guidance, finance formatting, and model layout patterns. | [skills.sh](https://skills.sh/openai/skills/spreadsheet), [officialskills.sh](https://officialskills.sh/openai/skills/spreadsheet) |
| Inspect as quality bar | `anthropics/skills@xlsx` | Strong Excel model requirements: zero formula errors, formula recalculation, financial-model color coding, template preservation, and formula discipline. | [skills.sh](https://skills.sh/anthropics/skills/xlsx) |
| Inspect / selectively install | `anthropics/knowledge-work-plugins` | Best FP&A/accounting workflow coverage: `financial-statements`, `variance-analysis`, `reconciliation`, `close-management`, `audit-support`, `sox-testing`, `journal-entry`, `build-dashboard`, `validate-data`. | [bundle](https://skills.sh/anthropics/knowledge-work-plugins), [variance-analysis](https://skills.sh/anthropics/knowledge-work-plugins/variance-analysis), [reconciliation](https://skills.sh/anthropics/knowledge-work-plugins/reconciliation), [close-management](https://skills.sh/anthropics/knowledge-work-plugins/close-management), [audit-support](https://skills.sh/anthropics/knowledge-work-plugins/audit-support) |
| Inspect / adapt | `anthropics/financial-services-plugins` | Best institutional finance reference: `audit-xls`, `3-statement-model`, `dcf-model`, `comps-analysis`, `lbo-model`, `ib-check-deck`, `datapack-builder`, earnings and market skills. | [skills.sh](https://skills.sh/anthropics/financial-services-plugins) |
| Inspect / adapt | `anthropics/financial-services` | Similar professional finance suite, lower install signal than the plugin bundle but useful for banking, close, reconciliation, KYC, and fund-admin patterns. | [skills.sh](https://skills.sh/anthropics/financial-services) |
| Install when dbt projects exist | `dbt-labs/dbt-agent-skills` | Official dbt skills for analytics engineering, tests, semantic layer, MCP config, docs, job errors, migrations, and DAG diagrams. Very relevant to finance data marts. | [skills.sh](https://skills.sh/dbt-labs/dbt-agent-skills/using-dbt-for-analytics-engineering), [GitHub](https://github.com/dbt-labs/dbt-agent-skills) |
| Inspect | `claude-office-skills/skills@financial-modeling`, `@dcf-valuation`, `@excel-automation`, `@quickbooks-automation` | Useful references, but less compelling than Anthropic/OpenAI official spreadsheet and finance-service bundles. | [financial modeling](https://skills.sh/claude-office-skills/skills/financial-modeling), [DCF](https://skills.sh/claude-office-skills/skills/dcf-valuation), [Excel automation](https://skills.sh/claude-office-skills/skills/excel-automation), [QuickBooks](https://skills.sh/claude-office-skills/skills/quickbooks-automation) |
| Inspect for SEC workflows | `longbridge/skills@longbridge-sec-filings`, `dgunning/edgartools@edgartools` | Useful SEC/EDGAR references; do not rely on them before checking dependencies, auth, rate limits, and citation behavior. | [Longbridge SEC filings](https://skills.sh/longbridge/skills/longbridge-sec-filings), [edgartools skill](https://skills.sh/dgunning/edgartools/edgartools) |
| Skip for now | generic market-data and Yahoo Finance skills | Many have weak repo/audit signals or external proxy dependencies. Better to build public-data workflows around SEC APIs, edgartools, Arelle, and optional user exports. | [skills.sh docs warning](https://skills.sh/docs) |

## High-Value Local Build Backlog

| Priority | Skill | User job-to-be-done | Inputs | Output | Acceptance checks |
|---|---|---|---|---|---|
| 1 | `excel-wow` | Build, audit, clean, and review banker/CFO-grade Excel models. | Workbook, CSV exports, assumptions, model goal. | Audited or generated workbook plus model review report. | Zero `TBU`; workbook inspector catches hidden sheets/rows/columns, formula errors, hardcodes inside formulas, external links, volatile formulas, named ranges, merged cells, check cells, and style/provenance summary. |
| 2 | `fpna-variance-pack` | Produce recurring monthly actual vs budget/forecast variance package. | Actuals, budget, forecast, prior period, GL detail, mapping table, thresholds. | Variance bridge, exception table, CFO-ready commentary, optional waterfall/chart. | Source totals tie; variance math foots; thresholds applied; commentary only for flagged items; "Other" reconciles. |
| 3 | `accounting-data-quality` | Add finance-specific controls over raw exports/data marts. | CSV/XLSX/DuckDB/dbt/GX/Soda datasets. | Aggregate-safe QA evidence page and pass/warn/fail JSON. | Clean fixture passes; defect fixture fails expected checks; no row-level sensitive leakage; sign conventions and period completeness tested. |
| 4 | `finance-reconciliation-agent` | Reconcile bank, GL, AR/AP aging, invoices, revenue, subledgers, and exports. | GL, bank, aging, invoice, subledger, QBO/Xero/CSV exports. | Matched/unmatched/one-sided/timing/adjustment buckets plus recon summary. | Known fixture reconciles to zero; tolerances explicit; unmatched causes grouped; no accounting-system writes. |
| 5 | `qbo-close-control-board` | Build close evidence from read-only QBO data. | QBO Trial Balance, GL, P&L, Balance Sheet, AR/AP, customer/vendor detail. | Close status board, exceptions, source timestamps, QA evidence page. | Read-only mode only; TB debits equal credits; P&L/BS tie to source; GL roll-forward ties; no row-level sensitive leakage. |
| 6 | `sec-filing-analyst` | Pull filings and cite every public-company claim. | Ticker/CIK, form type, filing period, section request. | Cited filing memo with extracted facts and source ledger. | Uses SEC User-Agent; respects rate limits; every fact has CIK, accession, form, filing date, URL. |
| 7 | `xbrl-financials-normalizer` | Convert XBRL facts into banker-style historical financial statements. | SEC companyfacts/companyconcept, Arelle or edgartools extracts. | Normalized financials with concept/unit/period/source columns. | Balance sheet balances; cash flow roll-forward ties; custom tags flagged, not silently mapped. |
| 8 | `cfo-board-pack` | Convert validated financial outputs into board-ready narrative/deck structure. | Model outputs, KPI table, variance explanations, milestones, cash data. | Board memo/deck outline with exhibits and explicit asks. | Every number traces to a source; period labels align; open decisions explicit; no orphan metrics. |

## Recommended Build Order

1. Finish `excel-wow` first. It is the missing core skill and already has a prior handoff at `.agent-handoffs/20260531-130403-excel-wow-build.md`.
2. Build `fpna-variance-pack` second. It is frequent, painful, easy to validate, and creates a reusable pattern: ingest -> map -> calculate -> narrate -> verify.
3. Build `accounting-data-quality` third. It becomes the shared control layer for QBO, Canopy exports, dashboards, and future data marts.
4. Build `finance-reconciliation-agent` fourth. Keep it export-first and connector-optional.
5. Build `qbo-close-control-board` fifth, only after read-only QBO probing and environment guardrails are verified.
6. Build `sec-filing-analyst` and `xbrl-financials-normalizer` as the investment-banking/public-company lane.

## Boundaries That Matter

- Do not turn `excel-wow` into a source-system skill. It should own workbook architecture, formula integrity, model checks, scenario controls, and export review.
- Do not duplicate number formats. Reuse `pagecraft/skills/number-formats`.
- Do not pretend public packages replace CapIQ, PitchBook, or FactSet. Build optional ingestion paths for user-provided exports.
- Do not run accounting-system write actions by default. QBO/Xero/NetSuite skills should start read-only and require explicit approval before any write path exists.
- Do not install community finance skills just because install counts look high. `skills.sh` itself warns that listed skills still need quality and security review.
- Do not build Canopy API assumptions from marketing/integrations pages. Treat Canopy as export-first unless firm-specific API credentials/docs are verified.

## Quality Bar For Finance Skills

Every finance skill in this repo should have:

- A narrow trigger description with specific finance phrases.
- A short `SKILL.md` plus `references/` for detailed standards.
- Deterministic scripts for fragile operations such as workbook inspection, reconciliation, or data-quality checks.
- Fixture evals that intentionally include defects and prove the skill catches them.
- A source ledger for numbers, claims, assumptions, and external data.
- A professional review boundary: the agent can assist, but final reporting, audit, tax, legal, and investment decisions require qualified human review.
- Public-safe outputs by default: no client names, emails, row-level sensitive data, secrets, or credential fragments in reusable skills.

## First Implementation Brief: `excel-wow`

Turn `excel-wow/SKILL.md` from placeholder into a production skill with:

- `SKILL.md`: trigger-ready description for model build/review/audit/cleanup, operating models, budgets, forecasts, KPI bridges, variance analysis, scenarios, formula review, and "make this banker-grade".
- `agents/openai.yaml`: short display name and prompt.
- `references/modeling-standards.md`: sheet order, formula discipline, assumptions/drivers, checks, scenarios, outputs, row/column conventions.
- `references/model-review-checklist.md`: formula consistency, hidden content, external links, named ranges, stale formulas, circularity, balance checks, variance checks, presentation readiness.
- `scripts/inspect_workbook.py`: workbook audit report using `openpyxl`.
- `evals/workbook_audit_fixture_eval.py`: small workbook with intentional issues and assertions.

Minimum acceptance checks:

```bash
ruby -e 'require "yaml"; Dir.glob("**/SKILL.md").each{|f| t=File.read(f); fm=t[/\A---\n(.*?)\n---\n/m,1] or abort("missing frontmatter #{f}"); y=YAML.safe_load(fm); abort("missing name #{f}") unless y["name"]; abort("missing desc #{f}") unless y["description"]}; puts "frontmatter ok"'
find . -name '*.json' -not -path './.git/*' -not -path '*/__pycache__/*' -print0 | xargs -0 -I{} python3 -m json.tool {} >/dev/null
PYTHONDONTWRITEBYTECODE=1 python3 excel-wow/evals/workbook_audit_fixture_eval.py
sh sync-skills.sh --all --dry-run
git diff --check
```

