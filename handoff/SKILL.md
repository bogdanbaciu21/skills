---
name: handoff
description: Summarize the current session's work into a structured handoff block and a saved markdown artifact that a fresh Claude Code chat or other coding-agent session can execute on. Use whenever the user says "handoff", "hand off", "pass to next session", "wrap up for handoff", "session summary for next chat", "continue in new chat", or anything about transferring context to a new conversation or environment. Also use when the user is about to end a session with unfinished work. Includes the GitHub issue reference if one exists. Do NOT use for PR descriptions, commit messages, or release notes — those summarize code changes for reviewers, not session state for the next agent. Do NOT use to dispatch parallel agents — that's `parallel-dispatch`.
argument-hint: "What should the next session do with this handoff? Mention the target environment if known: Codex, Claude, VPS, local shell, etc."
---

# Session Handoff

Produce both:

1. A structured, copy-pasteable handoff block in the chat.
2. A saved markdown handoff artifact when filesystem access is available.

The goal is zero context loss between sessions and environments — the next chat should be able to read the handoff and immediately start working without re-exploring the codebase or asking clarifying questions. The chat block is the universal fallback. The saved file is a convenience artifact, and the response must make clear whether the next environment can access it.

## Why this matters

Claude Code sessions are stateless — each new chat starts fresh. CLAUDE.md and memory provide project-level context, but session-specific state (what you just tried, what failed, what decisions were made, what's half-done) is lost. A good handoff captures exactly that session-specific context.

## Workflow

### Step 1 — Gather session context

Collect these automatically (don't ask the user for them):

1. **GitHub issue**: Read `/tmp/.claude-session-issue-number`. If it exists, fetch the issue title and URL via `gh issue view <number> --json title,url`.
2. **Git diff since session start**: Read `/tmp/.claude-session-start-commit`. If it exists, run `git log --oneline <start-commit>..HEAD` and `git diff --stat <start-commit>..HEAD` to see what changed.
3. **Working tree state**: Run `git status --short` to catch uncommitted work.
4. **Conversation review**: Review the full conversation history to extract:
   - The original task/request
   - What was accomplished
   - What was attempted but didn't work (and why)
   - Key decisions or findings
   - What remains to be done
5. **Execution context**: Capture the current working directory, repo root if available, current branch if available, and the current execution environment if known (Codex, Claude Code, VPS, local shell, etc.).

### Step 2 — Ask targeted questions

After gathering automatic context, ask the user only what you can't infer:

- "Is there anything I missed or got wrong in this summary?"
- "Any specific instructions for the next session beyond what's here?"
- "Which environment will pick this up next?" only if the answer changes the transfer method.

Keep it to 1–2 questions max. Don't over-interview.

### Step 3 — Choose the artifact path

Save the handoff as markdown when filesystem writes are available. Prefer locations in this order:

1. **Repo-local durable path**: `<repo-root>/.agent-handoffs/YYYYMMDD-HHMMSS-brief-slug.md`
   - Use this when working in a repo or project folder.
   - This is the safest path for switching between Codex and Claude on the same machine or when the workspace is synced.
2. **Workspace-local durable path**: `<cwd>/.agent-handoffs/YYYYMMDD-HHMMSS-brief-slug.md`
   - Use this when there is no git repo but the working directory is meaningful.
3. **OS temp fallback**: `${TMPDIR:-/tmp}/agent-handoffs/YYYYMMDD-HHMMSS-brief-slug.md`
   - Use only when the project directory is not writable or no useful workspace exists.

Never imply that a local path is available from another machine. If the next session is on a VPS or another host, say explicitly that the chat block is the portable handoff unless the file is copied or committed.

### Step 4 — Generate the handoff content

Output the handoff inside a fenced code block so the user can copy it in one click. Use a fence long enough to contain any code fences inside the handoff; default to ````markdown when there is any chance the content includes triple-backtick snippets, logs, or commands. Use this structure:

````
## Session Handoff — [brief title]

### GitHub Issue
#[number] — [title]
[URL]

### Original Task
[What the user asked for, in their words or close to it]

### What Was Done
- [Completed item 1]
- [Completed item 2]
- ...

### What's Left
- [ ] [Remaining item 1]
- [ ] [Remaining item 2]
- ...

### Suggested Starting Point
- [Exact first command, file, issue, or repo area the next session should inspect]
- [Mention any relevant skills/tools/modes if known]

### Key Decisions & Findings
- [Decision or finding that the next session needs to know]
- [Why something was done a certain way]
- [What was tried and rejected, and why]

### Files Changed
[git diff --stat output or curated list]

### Uncommitted Work
[git status output, or "None — all committed and pushed"]

### Environment & Transfer Notes
- Current environment: [Codex / Claude Code / VPS / local shell / unknown]
- Current working directory: [absolute path]
- Repo root: [absolute path, or omitted if not in a repo]
- Saved handoff artifact: [absolute path, or "Not saved — reason"]
- Cross-environment note: [If changing machines, use the chat block or copy/commit the artifact; do not assume this local path exists elsewhere]

### Gotchas & Context
- [Anything non-obvious the next session should watch out for]
- [Test failures to be aware of]
- [Blocked dependencies]
````

### Output rules

- **Be specific, not vague.** "Fixed `calcOrigination()` to normalize Infinity in tier bounds" is useful. "Fixed a calculation bug" is not.
- **Include file paths and line numbers** where relevant so the next session can jump straight to the code.
- **Include the exact error messages** if the session ended with a failing test or unresolved bug.
- **Don't pad.** If a section is empty (e.g., no gotchas), omit it entirely rather than writing "None."
- **The "What's Left" section is the most important part.** The next session's first action will be to read this list and start executing. Make it actionable — each item should be something Claude can do without further clarification.
- **Include the GitHub issue** so the next session can pick it up rather than creating a duplicate tracking issue.
- **Do not treat temp files as portable.** If the handoff is saved outside the repo/workspace, the final response must say that the chat block is the reliable cross-environment copy.
- **Do not commit handoff artifacts by default.** If the user wants the saved file to travel through git, confirm it is sanitized first or state that the chat block is safer.
- **Redact secrets and sensitive personal data.** Include where to find secrets only by naming the expected env var, secret manager, or config path pattern; never paste secret values into the handoff.
- **Prefer pointers over duplicated artifacts.** Link to files, commits, issues, PRs, logs, and generated artifacts rather than pasting large content into the handoff.

### Step 5 — Remind the user

After outputting the handoff block, remind the user where the artifact was saved and how to use it:

> Paste the block above as the first message in the new chat, or give the next session the saved markdown artifact at [path]. If the next session is on another machine or VPS, use the pasted block unless you have copied or committed the file there.
