# Correction log — fpa-analyst

The wrong-answer correction loop. When an `fpa-analyst` answer is corrected — by the
user, a controller, or a later reconciliation — log it here so the same mistake is
caught next time. Each entry should be **client-agnostic**: capture the *pattern* and
the *rule*, not the confidential numbers. If a correction is engagement-specific
(a particular view or account was wrong), fix it in that engagement's binding file in
the client repo and record only the generic lesson here.

## How to use

1. When an answer is corrected, add a row below.
2. If the root cause is a missing/ambiguous rule, also strengthen `SKILL.md` or
   `references/metric-definitions.md`, and (if it's testable) add an eval to
   `evals/questions.jsonl`.
3. If the root cause is a bad physical mapping, fix the engagement binding and bump its
   `binding_version`.

## Format

```
### <date> — <short title>
- **Question pattern:** <the kind of question that was asked>
- **Wrong answer:** <what the skill produced / the failure mode>
- **Correct answer / rule:** <the right number's definition or routing>
- **Root cause:** <definition gap | routing error | bad binding | redaction miss | provenance miss>
- **Fix applied:** <skill edit | metric-def edit | new eval id | binding vN bump>
```

## Entries

### 2026-06-04 — seed: realization averaged instead of dollar-weighted
- **Question pattern:** "average realization across engagements"
- **Wrong answer:** simple mean of the per-engagement realization percentages
- **Correct answer / rule:** realization is value-weighted (billed ÷ billable in dollars); small jobs must not swing the rate
- **Root cause:** definition gap
- **Fix applied:** encoded in `references/metric-definitions.md` (Realization); eval `fpa-002`

### 2026-06-04 — seed: collection presented as EBITDA
- **Question pattern:** "how much did collecting an old receivable add to EBITDA"
- **Wrong answer:** treated a collection as earnings
- **Correct answer / rule:** AR collection is a working-capital cash release, not EBITDA or revenue
- **Root cause:** definition gap
- **Fix applied:** encoded in `references/metric-definitions.md` (AR/collections/cash); evals `fpa-010`, `fpa-023`

### 2026-06-04 — seed: 'recurring' reported without exclusions
- **Question pattern:** "how much recurring revenue"
- **Wrong answer:** included one-time/credit-program and WIP-accrual amounts
- **Correct answer / rule:** recurring excludes one-time/credit + WIP accrual per the binding; if unconfirmed, label 'unfiltered revenue'
- **Root cause:** definition gap / binding not loaded
- **Fix applied:** encoded in `SKILL.md` + `metric-definitions.md`; evals `fpa-005`, `fpa-006`, `fpa-007`
