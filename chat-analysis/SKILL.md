---
name: chat-analysis
description: Analyze Claude Code session transcripts for failure patterns and propose CLAUDE.md improvements. Runs the four-stage pipeline (parse → filter → label → compile) via scripts/chat_analysis.py. Use when the user says "analyze my chats", "run chat analysis", "review my sessions", "what am I doing wrong", "chat analysis", or "/chat-analysis".
---

# Chat Analysis — Recursive Self-Improvement

Analyze session transcripts from `~/.claude/projects/` to surface failure
patterns, rule violations, and candidate improvements to `CLAUDE.md`.

The pipeline:
1. **Parse** — read `.jsonl` session files
2. **Filter** — regex pre-filter drops clean sessions (no friction signals)
3. **Label** — survivors go to Sonnet with a strict JSON schema
4. **Compile** — aggregate into tables, proposed deltas written to a review file

## When to use

- "Analyze my chats" / "run chat analysis"
- "What patterns are in my Claude sessions?"
- "What rules should I add to CLAUDE.md?"
- "How many sessions had verification failures?"
- Weekly improvement cadence: run on the last 50–100 sessions

## Setup (verify once)

```bash
# Check API key
echo $ANTHROPIC_API_KEY | head -c 10

# Install dependency (if needed)
pip install anthropic
# or: .venv/bin/pip install anthropic
```

If `ANTHROPIC_API_KEY` is not set, remind the user it's required and stop.

## Workflow

### Step 1 — Dry run first

Always do a dry run to confirm there are friction sessions worth labeling:

```bash
python3 scripts/chat_analysis.py --dry-run
```

This parses and pre-filters without spending any API tokens. Report what
the filter found. If zero friction sessions: tell the user and stop — the
sessions look clean.

### Step 2 — Cost check

Estimate cost before running. Each surviving session is one API call to
`claude-sonnet-4-6`. At current pricing, 50 labeled sessions ≈ $0.05–0.15.
For the default run (last 50 sessions), this is always in-budget — no need
to ask. For `--all` or `--n` values above 200, confirm with the user first.

### Step 3 — Run the analysis

```bash
# Default: current project, last 50 sessions
python3 scripts/chat_analysis.py

# Last 100 sessions
python3 scripts/chat_analysis.py --n 100

# All projects
python3 scripts/chat_analysis.py --all

# Custom output path
python3 scripts/chat_analysis.py --output /tmp/review.md

# Heuristic-only — no API calls, nothing leaves the machine
python3 scripts/chat_analysis.py --no-label
```

Stream output so the user sees progress. Report the final count:
`X sessions parsed → Y passed filter → Z labeled`.

### Step 4 — Surface findings

After the script completes, read `chat-analysis-review.md` and summarize the
top 3 findings to the user directly in the conversation:

```bash
# The report is self-contained, but surface the headline numbers
head -80 chat-analysis-review.md
```

Tell the user:
- The #1 failure mode by count
- The highest-cost failure mode (most rework cycles per incident)
- The most-violated rule (if any)
- How many candidate CLAUDE.md deltas are in the review file

### Step 5 — Review deltas (user decision)

The review file has a `## Proposed CLAUDE.md Deltas` section with checkbox
items. Walk the user through them one at a time if they want, or point them
to the file. **Never auto-apply any delta to CLAUDE.md** — the user decides.

If the user says "accept all" or "apply them", ask them to confirm which
specific items they want and make only those edits. The model does not edit
its own operating rules autonomously.

## Output file

`chat-analysis-review.md` (or the path passed via `--output`) contains:

- Summary stats table
- Top failure modes by count
- Highest-cost failure modes by avg rework cycles
- Communication antipatterns
- Rule violation rankings
- Proposed CLAUDE.md deltas (checkbox list, user must decide)
- Sample corrections and positive signals
- Per-session detail table

The file is ephemeral — not committed, not deployed. It's a scratchpad for
the improvement session. Delete it when done.

## What the pipeline looks for

Five friction patterns (from the blog post that describes this workflow):

1. **Corrections** — "no", "wrong", "stop", "that's not right"
2. **Repeated instructions** — same fix asked for across multiple turns
3. **Praise of non-obvious choices** — "yes, exactly, keep doing that"
4. **Tool loops** — same tool called 3+ times before switching
5. **Clarifying questions** — model had to ask because context was incomplete

## Privacy & data security

Transcripts can contain code, paths, customer data, and secrets. The
pipeline is hardened against leakage:

**Automatic redaction before any data leaves the machine:**
- API keys (Anthropic `sk-ant-…`, OpenAI `sk-…`, GitHub `ghp_/gho_/ghs_`,
  AWS `AKIA…`, Slack `xox[baprs]-…`)
- JWTs, Bearer tokens, `Authorization:` headers
- `password=`, `secret=`, `api_key=`, `access_token=` assignments
- Email addresses
- Absolute home paths (`/Users/<name>` → `/Users/[REDACTED]`)
- Credit-card-shaped numbers

Redaction runs in `redact()` (scripts/chat_analysis.py). Update the
`REDACTION_RULES` list to add patterns specific to your environment
(internal hostnames, customer IDs, project codenames, etc.).

**Other safeguards:**
- Session IDs in the report are SHA-256 hashed (8 chars), not raw filenames
- Sample corrections / positives are redacted AND truncated to 160 chars
- Default scope is current project only — never `--all` without auditing
- `--no-label` produces a heuristic-only report with **zero API calls**;
  use this for any project with stricter confidentiality requirements
- The output report is gitignored by default

**Before running on a sensitive project**, do a dry run and skim the friction
session list. If anything looks like it could leak, run with `--no-label`
or extend `REDACTION_RULES` first.

## Troubleshooting

**"Could not auto-detect project dir"**
The script maps CWD → `~/.claude/projects/` by hashing the path. If it
fails, pass the path explicitly:
```bash
ls ~/.claude/projects/     # find the right directory name
python3 scripts/chat_analysis.py --project ~/.claude/projects/<dir>
```

**"ANTHROPIC_API_KEY not set"**
```bash
export ANTHROPIC_API_KEY=sk-ant-...
python3 scripts/chat_analysis.py
```

**"anthropic package not installed"**
```bash
pip install anthropic
```

**Labeling errors / JSON parse failures**
These are logged as warnings and skipped. The report includes only sessions
that labeled successfully. A handful of failures is normal; if >20% fail,
check the model response in debug mode.
