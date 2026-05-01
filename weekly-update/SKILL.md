---
name: weekly-update
description: Draft a weekly stakeholder update for any software project. Use when the user asks for a weekly update, Friday email, status report, sprint summary, or stakeholder progress report. Pulls commits and closed issues automatically from git and gh, asks a short set of clarifying questions, and produces a draft markdown file in docs/weekly-updates/. Optionally renders an HTML email using a brand template if one is configured.
---

# Weekly Update

Draft a weekly stakeholder update email for an ongoing software project. This skill replaces ad-hoc drafting with a repeatable workflow that pulls real data from the repo, asks only the questions that require human judgment, and enforces a tight, evidence-driven tone.

## Audience

Before drafting, confirm (or recall from memory) the recipient list and what each person cares about. A simple framing:

| Recipient | Role | What They Care About |
|---|---|---|
| **Author** | You | Owns the update; final call on tone, asks, and status color |
| **Primary stakeholder** | Sponsor / decision-maker | Strategic progress, "is this on track," what they need to decide |
| **Secondary stakeholders** | CC list | Cost posture, risk, compliance, dependencies |
| **Conditional CCs** | e.g. IT, security, legal | Add only when the week's blocker or ask involves them |

Optimize every framing decision for: *"What does the primary stakeholder need to know in 60 seconds?"*

## Tone — Institutional Confident (enforced, not optional)

Think quarterly board update from a competent operator. Not a startup blog post. Not a legal memo. Not a personal Substack.

**Rules:**
1. **Lead with the number.** "839 issues closed" not "significant progress."
2. **Active voice.** "We shipped X" not "X was shipped."
3. **Zero adjective filler.** Strip these on sight: *exciting, pleased to report, significant, continue to, great news, massive, robust, leverage, seamlessly, world-class, truly, really.*
4. **Technical specificity over hand-waving.** "Fixed boundary condition in tier calculation" beats "fixed a calculation bug."
5. **Institutional pronouns.** Prefer "the project" / "the platform" over "we/I" — feels like an update from a project, not a person.
6. **Explicit asks.** "Owner: confirm provisioning timeline by [date]" not "help would be appreciated."
7. **Evidence over claims.** Link to PRs, commits, specific fixes. Include ticket numbers where available.
8. **Structured for 30-second skim.** Short paragraphs. Bold sub-headers. Tables for anything quantitative.

Before drafting any section, mentally check: *Would the primary stakeholder need to re-read this sentence? Would a skeptical reader cut this for filler?*

## Workflow

### Step 1 — Determine the Week Number and Date Range

Weeks are numbered sequentially from the start of the project. Default week-end is **Sunday**; the update is typically drafted Thursday or Friday for the upcoming Sunday. (Adjust if the project uses a different cadence.)

1. Count files in `docs/weekly-updates/week-*.md`. The next week number is that count + 1 (unless a draft for this week already exists — update it instead).
2. Calculate the **week-ending day** based on today's date:
   - If today is the week-end day → today
   - Otherwise → the next upcoming week-end day
3. Filename format: `docs/weekly-updates/week-{NN}-{YYYY-MM-DD}.md` where `NN` is zero-padded and the date is the week-ending day.

### Step 2 — Pull Data Automatically

Before asking anything, run these and cache the results:

```bash
# Commits in the current week (since last week-end midnight)
git log --since="<last Sunday>" --pretty=format:"%h %s" --no-merges

# Line-changed stats for the week
git log --since="<last Sunday>" --shortstat --pretty=format:"" | \
  awk '/files? changed/{f+=$1; i+=$4; d+=$6} END {print f, i, d}'

# Total commits since repo creation
git rev-list --count HEAD

# Closed issues by milestone (this week)
gh issue list --state closed \
  --search "closed:>=<last Sunday YYYY-MM-DD>" \
  --limit 500 --json number,title,milestone,closedAt

# Open + closed issues by milestone (all time) — for the cumulative table
gh issue list --state all --limit 2000 \
  --json number,state,milestone
```

Aggregate raw output into the tables the skill renders. If `gh` is rate-limited or errors, degrade gracefully: ask for the numbers manually rather than fabricating them.

### Step 3 — Ask the Four Questions

These require human judgment and must not be guessed:

1. **Status color + justification** — Green / Yellow / Red, plus a one-sentence reason. Example: *"Yellow — provisioning has slipped 3 weeks past the original ask."*
2. **Three pillar themes for this week** — Dynamic, not fixed. Pick three narrative threads describing what the week was about. Examples: `Security / Safety / Usefulness`, `Accuracy / Delivery / Trust`, `Pipeline / Engine / Review`.
3. **Blockers** — For each: item, owner, days blocked (calculate from git/issue history if linked), and what's needed to unblock. Confirm the list.
4. **The Ask** — Numbered, specific, dated. Each ask names a person and a deadline. If no ask this week, say so explicitly.

Optionally ask (only if relevant):
- Any "Decision of the Week" to document as an ADR-style note?
- Any "Bug of the Week" worth calling out with impact?
- Screenshot to embed as a hero shot?

### Step 4 — Draft the Markdown File

Write to `docs/weekly-updates/week-{NN}-{YYYY-MM-DD}.md` using the structure below. This is the primary output — review and edit it before sending.

### Step 5 — Render the HTML Email (on request)

After the markdown is approved, optionally render a branded HTML email to `docs/weekly-updates/week-{NN}-{YYYY-MM-DD}.html`. If the project has a brand skill or email template (e.g. `references/email-template.html`), use it. Otherwise generate a clean, minimal HTML email with sensible defaults.

### Step 6 — Do NOT Auto-Send

Never send the email. The author sends it manually. The skill's job ends at the HTML file.

## Draft Structure

```markdown
# {Project Name} — Weekly Update #{N}
*Week ending {Date} · To: {Primary}, {CCs}*

---

**Status: {Green/Yellow/Red}** — {one-sentence justification}

**TL;DR:** {under 40 words — the single most important thing the primary stakeholder needs to know}

---

## {Pillar 1 Theme}

{2–4 bullets or short paragraphs. Bold sub-headers for each concrete item. Specific numbers, specific fixes, linkable references.}

## {Pillar 2 Theme}

{same pattern}

## {Pillar 3 Theme}

{same pattern}

---

## Closed This Week by Milestone

| Milestone | Closed This Week | Trend | Still Open | % Done | Due |
|---|---|---|---|---|---|
| ... | ... | ... | ... | ... | ... |

*Trend arrows: ↑ more than last week · → same · ↓ fewer*

---

## All-Time Milestone Progress

| Milestone | Closed | Open | Total | Progress | Due |
|---|---|---|---|---|---|
| ... | ... | ... | ... | ██████░░░░ XX% | ... |
| **Total** | | | | | |

*Progress bars use 10-block Unicode: each block = 10%. In HTML, convert to CSS gradient bars.*

---

## Velocity Trend — Last 4 Weeks

| Week ending | Commits | Issues Closed | Lines +/− |
|---|---|---|---|
| Week N-3 | ... | ... | ... |
| Week N-2 | ... | ... | ... |
| Week N-1 | ... | ... | ... |
| **This week** | **X** | **Y** | **+A / −B** |

---

## Progress by the Numbers

- **{X} commits** this week / **{Y} total** since repo created
- **{A} lines added / {B} lines removed** (net {+/- delta}) across {N} files
- **{T} total test cases** across {S} suites
- **{D} deploys**, {G} CI runs green

---

## Blockers & Risks

| Status | Item | Owner | Days Blocked | What's Needed |
|---|---|---|---|---|
| BLOCKED | ... | ... | ... | ... |
| WAITING | ... | ... | ... | ... |

---

## Deliverable Roadmap

| Deliverable | Scope | Status | Target |
|---|---|---|---|
| ... | ... | ✓ Delivered / On Track / At Risk / Off Track | {date} |

---

## The Ask

1. **{Person}**: {specific ask with deadline}
2. **{Person}**: {specific ask with deadline}

---

## Next Week's Focus

- {Item 1}
- {Item 2}
- {Item 3}
```

## Status Semantics

- **Green** — On track. All blockers owned and moving. No scope cuts needed.
- **Yellow** — Delivery is at risk for at least one reason. State the reason in one sentence. Yellow is not a failure — it is early risk communication.
- **Red** — Off plan. Will miss at least one commitment without intervention (scope cut, resource addition, or timeline extension). Used sparingly. Always paired with an explicit ask.

Move to Yellow at the **first** sign of risk, not when the fire is already burning. Move back to Green only when the risk is resolved, not just paused.

## Progress Bar Rendering

### Markdown / Plain Text
10-block Unicode bars: `█` filled, `░` empty. Formula: `filled = round(pct / 10)`, `empty = 10 - filled`. Example: 47% → `████░░░░░░ 47%`.

### HTML Email
Two-div CSS bar:
```html
<div class="progress-bar"><div class="progress-fill" style="width: 47%"></div></div>
```

## Blocker Days-Counter

Calculate days blocked from the earliest of:
1. The linked issue's `createdAt` date
2. The first commit that mentions the blocker by label
3. A manual override

Render as `{N} days` for N < 14, `{N} days ⚠` for N ≥ 14, `{N} days 🚨` for N ≥ 28. (Emoji only in plain-text draft; in HTML use color coding — amber for 14+, red for 28+.)

## Brand Application

If the project has a brand skill or template, apply it for any visual output. Otherwise:
- **Markdown draft**: plain GitHub-flavored markdown, no styling
- **HTML email**: minimal, accessible defaults — system fonts, generous spacing, single-column layout, no external assets

Common email template tokens to support:
- `{{SUBJECT}}` — `{Project} Weekly Update #{N} — Week Ending {Date}`
- `{{EYEBROW}}` — `{PROJECT} — WEEKLY UPDATE`
- `{{TITLE}}` — `Weekly Development Progress — Week #{N}`
- `{{DATE_RANGE}}` — `Week ending {Date}, {Year}`
- `{{STATUS_COLOR}}` — `green` / `yellow` / `red`
- `{{STATUS_LABEL}}` — `ON TRACK` / `AT RISK` / `OFF TRACK`
- `{{STATUS_REASON}}` — one-sentence justification
- `{{TLDR}}` — under 40 words
- `{{BODY}}` — rendered HTML of the pillars, tables, blockers, ask, next week
- `{{YEAR}}` — current year

## File Naming Convention

- Draft markdown: `docs/weekly-updates/week-{NN}-{YYYY-MM-DD}.md`
- HTML email: `docs/weekly-updates/week-{NN}-{YYYY-MM-DD}.html`
- `NN` is zero-padded (01, 02, 03, ...)
- Date is the **week-ending day**
- Do NOT rename or delete prior weeks

## What This Skill Will Never Do

- **Never send the email.** Output file only.
- **Never fabricate numbers.** If git/gh data is missing, ask.
- **Never use adjective filler.** See tone rules.
- **Never invent blockers or asks.** The author must confirm them.
- **Never commit the draft** unless explicitly asked.
- **Never change milestone dates** without confirmation.

## Invocation

Invoke by asking for the "weekly update," "Friday email," "status report," or "stakeholder update." The skill acknowledges, pulls data, asks the four questions, drafts the file, and reports the filename back.
