# Tracker Providers

Use this reference after collecting git stats. The goal is always the same:
answer "what closed this week?" and "what is the all-time open/closed split by
milestone, project, cycle, epic, or sprint?"

## GitHub Issues

Default tracker when no other system is known.

```bash
gh issue list --state closed \
  --search "closed:>=<last Sunday YYYY-MM-DD>" \
  --limit 500 --json number,title,milestone,closedAt

gh issue list --state all --limit 2000 \
  --json number,state,milestone
```

Group by milestone. Treat missing milestone as `No milestone`.

## Linear

Use Linear when the project manages work there. Map GitHub milestones to Linear
projects for long-lived workstreams or cycles for sprint-shaped reporting.
Prefer the Linear MCP server if available; otherwise use the GraphQL API, a
local CLI wrapper, or a CSV export.

Required data:

| Dataset | Filter | Required fields | Grouping |
|---|---|---|---|
| Closed this week | `completedAt >= <week-start>` | `identifier`, `title`, `completedAt`, `state.name`, `state.type`, `project.name`, `cycle.name` | `project.name`, then `cycle.name`, then `No project/cycle` |
| All-time progress | Same team/project/cycle scope, no date filter | `identifier`, `state.name`, `state.type`, `project.name`, `project.targetDate`, `cycle.name`, `cycle.endsAt` | Same grouping |

Paginate until exhausted. Count `state.type = completed` as closed. Do not blend
canceled work into closed progress unless the stakeholder explicitly wants
canceled scope reported as removed.

## Jira

Best-effort via Atlassian MCP, `jira` CLI, or another JQL-capable client.
Validate the closed-this-week query against Jira UI before relying on numbers.

```bash
jira issue list --jql "resolved >= -7d AND statusCategory = Done" --limit 500
jira issue list --jql "project = <KEY>" --limit 2000
```

Group by epic/sprint when available. If Jira fields are inconsistent, report the
limitation and ask for the numbers manually instead of fabricating them.

## Degraded Mode

If the tracker is rate-limited, unavailable, or the session lacks access:

1. Keep git evidence.
2. Ask the user for closed/open issue counts and key ticket IDs.
3. Mark tracker data as manually supplied in the draft.
