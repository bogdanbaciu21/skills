# Canonical FP&A metric definitions (client-agnostic)

These are the stable definitions the `fpa-analyst` skill enforces. They do **not**
name any engagement, GL account, or physical view — those are supplied per
engagement by the binding file. The intent here is that two analysts answering the
same question against the same warehouse get the **same number**.

## Realization

- **Definition:** value-weighted `billed amount ÷ billable (standard) amount` over a
  stated period and population.
- **Weighting:** by dollars, not a mean of per-engagement/per-job percentages. A
  simple average lets a tiny job move the headline rate; dollar-weighting does not.
- **Common error:** averaging the per-job realization column. Reject it.
- **Report with:** period, population (which clients/jobs), and whether write-offs
  and write-ups are both in the numerator.

## Utilization

- **Definition:** `billable hours ÷ total available hours`.
- **Denominator discipline:** "available hours" is engagement-defined — scheduled,
  calendar, or paid hours produce materially different numbers. The chosen
  denominator lives in the binding; always state which one was used.
- **Common error:** mixing a billable-hours numerator with a calendar-hours
  denominator from a different source. Keep numerator and denominator from the same
  governed object.

## Recurring core revenue

- **Definition:** revenue from ongoing, repeatable service relationships.
- **Exclusions (mandatory):** one-time / credit-program revenue (e.g. tax-credit
  programs that run off) and WIP-accrual movement. The **specific GL accounts** for
  these exclusions are engagement-specific and are read from the binding — never
  inline an account number into this skill or this reference.
- **Failure mode:** if the exclusion list can't be confirmed from the binding, label
  the figure **"unfiltered revenue,"** not "recurring." Do not imply durability you
  can't substantiate.

## Service-line / client contribution margin

- **Definition:** revenue minus the **direct** costs of delivering that service line
  or client.
- **Overhead:** excluded from the contribution-margin headline. If overhead matters
  for the decision, show a **separate, clearly-labeled "loaded" sensitivity** beside
  it — never fold an allocation into the headline number.
- **Failure mode:** presenting a fully-loaded margin as if it were contribution
  margin, which makes service lines look unprofitable for reasons unrelated to their
  direct economics.

## AR / collections / cash

- **Definition:** AR aging and collections describe **working-capital timing**, not
  earnings.
- **Hard rule:** a collection releases cash; it is **not EBITDA and not revenue.**
  Never let a collections figure inflate a margin or appear in an earnings bridge.
- **Useful framing:** collections answer "when does cash arrive," DSO answers "how
  slow is the cash cycle," neither answers "are we profitable."

## Source-tier routing matrix (template)

Fill the right-hand column per engagement in the binding file. The left two columns
are universal.

| Question type | Source tier | Physical object (per binding) |
|---|---|---|
| Official headline metric (realization, recurring revenue, utilization) | 1 — canonical/semantic | `<bind>` |
| Governed business question (service-line margin, AR buckets, client cohort) | 2 — marts | `<bind>` |
| Named client / staff / vendor row | 3 — drilldown (redacted) | `<bind>` |
| Reconciliation / "why is the canonical number that" | base/raw (explain only) | `<bind>` |

## Redaction policy

- Tier-3 named-entity rows are **redacted by default**: answer at the aggregate or
  ranked-but-anonymized level.
- Only reveal a named individual/client/vendor row when the requester is the **data
  owner** (named in the binding) and asks for it explicitly.
- Never volunteer a named entity's numbers inside an answer to a general question.
