## Serial Landing Queue (default)

Use this section in every coordinator playbook unless Dan explicitly opts into
parallel push.

### File Ownership Matrix

Fill before launch. One owner per path; blank means CANNOT touch for all runners.

| File / area | Owner track |
|-------------|-------------|
| [path or glob] | [Track name] |
| ... | ... |

### Runner contract (code tracks)

Each runner:

1. `git wt <track-slug>` from fresh `main` (never the canonical dirty checkout).
2. Touch ONLY files in its CAN touch list.
3. Commit locally in the worktree; run track verification gates there.
4. Return a **landing packet** to the coordinator:
   - Summary (root cause, residual risk)
   - Worktree path or branch name
   - `git log -1 --oneline` and `git log -1 --stat`
   - Verification command output
   - Issue numbers ready to close (coordinator closes after land, unless runner is sole integrator)
5. **Do not push to `main`.**

### Coordinator landing order

| Order | Track | Depends on | Land command / notes |
|------:|-------|------------|----------------------|
| 1 | [name] | none | `cd <worktree> && git land` |
| 2 | [name] | 1 landed | ... |
| ... | ... | ... | ... |

Rules:

1. Only the coordinator lands. One track at a time.
2. After each land: `git pull origin main` in the repo root; re-run that track's gates on landed `main`.
3. `git log -1 --stat` must match expected file scope before closing issues.
4. Stop on merge conflict, scope drift, or a red gate. Do not start the next land.
5. Capture push exit code directly (`rc=$?`); do not pipe through `tail`.
6. To verify a file is on `main`, use a fresh detached worktree checkout, not
   `git ls-tree origin/main` alone on a shared `.git`.

### After all lands

Run the coordinator playbook's Final Gate, issue closure checklist, and any
optional add-on passes (pagecraft, combined insight).
