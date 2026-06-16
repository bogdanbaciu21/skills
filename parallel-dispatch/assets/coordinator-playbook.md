## Coordinator Playbook

### Pre-Launch Sanity Check
1. Confirm every track has one independent problem domain and a self-contained goal/evidence package
2. Confirm no prompt depends on the coordinator's private chat context
3. Confirm file scopes and shared resources do not overlap; publish the File Ownership Matrix
4. Confirm code tracks use serial landing (runners do not push to `main`) unless Dan opted into parallel push
5. If failures look related or share a likely root cause, collapse them into one investigation or make them sequential


### Serial landing queue (default)

Runners work in `git wt <slug>` and do **not** push to `main`. Only the
coordinator lands, one track at a time. Fill the File Ownership Matrix and
landing-order table from `assets/serial-landing-queue.md` before launch.

| Land order | Track | Worktree | Blocked until |
|-----------:|-------|----------|---------------|
| 1 | [name] | [path] | none |
| 2 | [name] | [path] | track 1 landed |

### Launch Order
| Phase | Tracks | Can start |
|-------|--------|-----------|
| 1 | [tracks with no dependencies] | Now |
| 2 | [tracks waiting on phase 1] | After [dependencies] merge |
| ... | ... | ... |

### After Each Track Lands
1. From the track worktree: `git land` (or repo-specific land path). Capture push exit code with `rc=$?`; do not pipe push output.
2. In repo root: `git pull origin main`
3. Scan for merge conflicts (should be none if file scopes are clean)
4. Verify commit scope matches expected files: `git log -1 --stat` — flag if the commit only touched docs when code changes were expected (when the capture add-on is on, the track's one capture file under `<capture-dir>/<run-slug>/` is also expected — do not flag it as scope drift)
5. Verify issue closures: `for i in <expected issue numbers>; do echo -n "#$i: "; gh issue view $i --json state -q .state; done`
6. If any expected issues are still OPEN, close them now with the track's findings
7. Spot-check the agent summary against the diff for systematic errors or scope drift
8. [Track-specific verification if any]

### Final Gate (after ALL tracks merge)
```bash
npm run verify                    # Full CI mirror
node scripts/dead-code-check.js   # Dead code scan
# Verify ALL expected issues are closed
gh issue list --label <workflow-label> --state open --limit 50
```

After the final gate, read all agent summaries together and check that the combined result still makes sense. Independent fixes can each be correct locally while producing an integration problem together.

### Add-on pass: HTML polish with pagecraft (only if tracks produced HTML deliverables)

Run only when at least one merged track created or changed static HTML deliverables (check the merged file scopes). Skip entirely otherwise.

1. Identify the HTML output root(s) from the track file scopes.
2. Install if absent, or reuse the repo's existing install: `sh <skills>/pagecraft/skills/pagecraft/install-pagecraft.sh <repo-root>`.
3. Deterministic keystone guard (no browser, never flakes): `python3 scripts/check-keystone.py --portal <html-root>`.
4. Real-browser probe (8 viewports + right-edge alignment): `python3 scripts/runner.py --local --portal <html-root> --known-issues tests/pagecraft/wrap-known-issues.json`.
5. Fix keystone/wrap failures; allowlist only confirmed non-defects. Do not silently truncate output.
6. Commit the polished HTML plus any known-issues updates.

### Add-on pass: Combined insight digest (only if per-runner capture was enabled)

Each runner wrote a capture to `<capture-dir>/<run-slug>/<track-slug>.md` and committed it with its work. After the Final Gate:

1. `git pull origin main` so every track's capture is present locally.
2. List them: `ls <capture-dir>/<run-slug>/*.md`. If a track that had capture enabled is missing its file, note the gap — do not fabricate it.
3. Read ALL captures together and write a condensed cross-track memo to `<capture-dir>/<run-slug>/_combined.md` using the combined-insight template (`assets/combined-insight.md`): Headline, Convergent Findings, Contradictions To Hold, Integration Risks, Cross-Track Open Questions, Per-Track index, Provenance.
4. The cross-track value is in the disagreements: lift every track's "Contradictions / Integration Risks" up into the combined memo. A risk only one track saw is exactly what the others were blind to — and what the per-track summaries miss when read in isolation.
5. Commit `_combined.md`.

### Surface the result

End your final report to the user with:

- The **Headline** from `_combined.md` (one or two sentences), inline.
- A link to the combined memo artifact and, if the pagecraft pass ran, the polished HTML root.
- Anything in Contradictions / Integration Risks that should change the next decision.

### Issue Closure Checklist
- **[Track Name] closes:** [issue numbers]
- **[Track Name] comments on:** [issue numbers]
- ...

**Coordinator responsibility:** If agents leave issues open (common — see Common Pitfalls), the coordinator closes them during the "After Each Track Lands" step. Do not defer to the Final Gate.
