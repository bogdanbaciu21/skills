# Engagement binding — TEMPLATE (copy into the CLIENT repo, never the shared skill)

> ⚠️ This filled-in file is **client-confidential**. Create it inside the client's
> own repo (e.g. that engagement's `deliverables-private/` or warehouse config), not
> in `dans-brain`, the shared `skills` source repo, or anywhere the skill-propagation
> secret/sensitive gate scans. The `fpa-analyst` skill references this file by role;
> it must never contain the values inline.

Replace every `<...>` and delete the guidance lines once filled.

```yaml
engagement: <engagement slug>
binding_version: 1
data_owner: <who may see named-entity rows>
warehouse: <warehouse / data-hub name or connection alias>

# Tier 1 — canonical / semantic metric layer (definition-locked headline metrics)
canonical:
  realization_view: <physical object>
  recurring_revenue_view: <physical object>
  utilization_view: <physical object>

# Tier 2 — governed business-question marts
marts:
  service_line_margin_view: <physical object>
  ar_aging_view: <physical object>
  client_cohort_revenue_view: <physical object>

# Tier 3 — named-entity drilldowns (redacted by default)
drilldowns:
  client_detail_view: <physical object>
  staff_detail_view: <physical object>
  vendor_detail_view: <physical object>

# Metric input bindings
recurring_revenue_exclusions:
  one_time_or_credit_accounts: [<gl account>, ...]   # e.g. tax-credit programs that run off
  wip_accrual_accounts: [<gl account>, ...]
utilization_denominator: <scheduled | calendar | paid>   # which "available hours" means here
overhead_treatment: contribution_excludes_overhead       # keep overhead as a separate loaded sensitivity

# Redaction
redacted_entities: [client, staff, vendor]
reveal_requires: data_owner_explicit_request
```

## Checklist for a complete binding

- [ ] Every source-tier view resolved to a real physical object in this warehouse.
- [ ] Recurring-revenue exclusion accounts confirmed with the engagement's controller
      (one-time/credit **and** WIP accrual).
- [ ] Utilization denominator agreed and documented.
- [ ] Data owner named; redacted entity list set.
- [ ] `binding_version` bumped whenever any mapping changes (the provenance footer
      cites it).
