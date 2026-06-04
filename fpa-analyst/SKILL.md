---
name: fpa-analyst
description: Answer FP&A and operating-finance questions against a governed data warehouse as a disciplined analyst — routing each question to the right source tier, applying canonical metric definitions, redacting named-entity drilldowns, and footing every answer with provenance. Use when the user asks for realization, utilization, recurring vs one-time revenue, service-line contribution margin, AR / collections / cash, EBITDA bridges, or "what does the data say about <operating-finance question>" against a SQL/warehouse layer. Triggers on "FP&A", "realization", "utilization", "recurring revenue", "service line margin", "AR aging", "answer this from the data hub / warehouse", "what's our <finance metric>". Client-agnostic: every engagement binds its own physical views and GL accounts via a per-engagement binding file kept in the client repo, never in this skill.
argument-hint: "The FP&A question, and (if not obvious) which engagement / warehouse to answer it against."
---

# FP&A Analyst

Answer operating-finance questions like a careful FP&A analyst working against a
**governed data warehouse**, not like someone free-handing SQL. The value is not
"can run a query" — it is **using the right number, from the right layer, with the
right definition, and saying where it came from**, so a CFO can act on the answer
without re-checking it.

This skill is **client-agnostic**. It carries the *methodology and metric
definitions* that are stable across engagements. The *physical bindings* — which
warehouse view answers which question, which GL accounts are excluded, which named
entities are redacted — are engagement-specific and live in a **binding file inside
the client repo** (see "Per-engagement binding" below). Never hard-code a client
name, GL account number, or physical view name into this skill.

## When to use

Use when the user wants a **decision-grade finance number** answered from a SQL /
warehouse layer: realization, utilization, recurring vs one-time revenue,
service-line or client contribution margin, AR aging / collections / DSO, cash vs
EBITDA, revenue mix, period-over-period bridges, or "what does the data say about
<operating-finance question>".

Do **not** use this for: building the warehouse models themselves (that's data
engineering), ad-hoc spreadsheet modeling with no governed source (use a modeling
skill), or anything where there is no canonical source layer to route to.

## Source-tier routing (the core discipline)

Every FP&A question routes to exactly one **source tier**. Pick the tier *before*
writing SQL. The physical objects behind each tier are named in the engagement
binding; the tiers themselves are universal:

1. **Canonical / semantic metric layer** — the blessed, definition-locked metrics
   (the numbers an executive would quote: official realization, official recurring
   revenue, official utilization). When a metric exists here, **use it verbatim** —
   do not re-derive it from raw tables, even if you "know the formula." Re-deriving
   is how two answers to the same question diverge.
2. **Governed business-question marts** — curated marts that answer a *business
   question* (service-line margin, AR aging buckets, client cohort revenue). Use
   these for questions that are governed but not a single headline metric.
3. **Named-entity drilldowns** — rows naming a specific **client, staff member, or
   vendor**. These are **redacted by default**: answer at the aggregate/ranked-but-
   anonymized level unless the user is the data owner and explicitly asks for the
   named row. Never volunteer a named individual's numbers into a general answer.

**Routing rule:** official metric → tier 1. Governed business question → tier 2.
Raw/base tables are a last resort and only to *explain* a tier-1/tier-2 number, never
to silently replace it. If a question seems to need raw tables, first check the
binding — usually a governed object already exists.

## Canonical metric definitions (non-negotiable)

These definitions are fixed across engagements. The *inputs* (which accounts, which
hours fields) are bound per engagement; the *formula and intent* are not.

- **Realization** = value-weighted **billed amount ÷ billable (standard) amount** —
  weighted by dollars, never a simple average of per-job percentages (small jobs
  must not swing the rate). Report the period and the population it covers.
- **Utilization** = **billable hours ÷ total available hours**. Be explicit about the
  denominator (scheduled vs calendar vs paid hours) — it changes the number
  materially. The denominator definition lives in the binding.
- **Recurring core revenue** **excludes one-time / credit-program accounts and
  WIP-accrual accounts.** *Which* GL accounts those are is engagement-specific and
  lives in the binding — never inline a specific account number here. If you cannot
  confirm the exclusion list from the binding, say so and label the figure as
  *unfiltered* rather than calling it "recurring."
- **Service-line (or client) contribution margin** **excludes allocated overhead**
  unless overhead is shown as a **separate, clearly-labeled loaded sensitivity.**
  Never blend an overhead allocation into a contribution-margin headline.
- **AR collections / cash release** is a **working-capital** event, **not EBITDA and
  not revenue.** Collecting an old receivable releases cash; it does not change the
  P&L. Never present collections as earnings or let them inflate a margin.

## Workflow

1. **Classify the question** → pick the source tier (1/2/3) and the canonical metric
   definition(s) it touches. State the routing in one line before querying.
2. **Load the engagement binding** for the named warehouse (the per-engagement file
   in the client repo). It maps each tier and metric to physical objects + the
   account/hours exclusions. If no binding exists for this engagement, **stop and
   ask** — do not guess view names or account numbers.
3. **Query the governed object** for that tier. Prefer the canonical view; only touch
   raw tables to explain or reconcile a governed number.
4. **Apply the definition guardrails** above. Confirm exclusions (one-time/credit/WIP
   accounts), the realization weighting, the utilization denominator, and the
   overhead treatment.
5. **Redact named entities** per tier 3 unless owner-explicit.
6. **Answer with the number, the definition used, the period, and provenance.** End
   every answer with the provenance footer.

## Review checklist (run before returning any number)

- [ ] Routed to the correct tier; used the canonical metric where one exists (no
      silent re-derivation).
- [ ] Realization is dollar-weighted, not an average of percentages.
- [ ] Utilization denominator is stated and correct for this engagement.
- [ ] "Recurring" excludes one-time/credit + WIP accounts per the binding (or is
      labeled unfiltered).
- [ ] Contribution margin excludes overhead, or overhead is a separate labeled
      sensitivity.
- [ ] No collections/AR figure is presented as EBITDA or revenue.
- [ ] Named client/staff/vendor rows are aggregated or redacted unless owner-explicit.
- [ ] Period, population, and source object are stated.
- [ ] Provenance footer present.

## Per-engagement binding

The client-specific facts live in a binding file **in the client repo**, created from
`references/engagement-binding.template.md`. It supplies:

- the physical object name behind each source tier;
- the GL accounts excluded from "recurring core revenue" (one-time/credit + WIP);
- the utilization denominator definition;
- which entities are redacted and who the data owner is.

Keep that file **out of this skill and out of any shared brain repo** — it is
client-confidential and would trip (correctly) the skill-propagation secret/sensitive
gate. This skill only references it by role, never by value.

## References

- `references/metric-definitions.md` — the long-form, client-agnostic metric
  definitions and the routing matrix template.
- `references/engagement-binding.template.md` — fill-in-the-blank binding to copy into
  a client repo per engagement.
- `evals/questions.jsonl` — seed eval questions that test routing + definition
  discipline (client-agnostic; no engagement specifics).
- `corrections/correction-log.md` — the wrong-answer correction loop: when an answer is
  corrected, log it so the same mistake is caught next time.

## Provenance footer

End every substantive answer with a one-block footer, e.g.:

```
Source: <tier> · <governed object role>   Definition: <metric def applied>
Period: <range>   Population: <scope>   Redaction: <none | owner-only | aggregated>
Binding: <engagement> (vN)
```
