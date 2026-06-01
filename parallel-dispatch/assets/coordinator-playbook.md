## Coordinator Playbook

### Pre-Launch Sanity Check
1. Confirm every track has one independent problem domain and a self-contained goal/evidence package
2. Confirm no prompt depends on the coordinator's private chat context
3. Confirm file scopes and shared resources do not overlap unless a dependency is listed
4. If failures look related or share a likely root cause, collapse them into one investigation or make them sequential

### Launch Order
| Phase | Tracks | Can start |
|-------|--------|-----------|
| 1 | [tracks with no dependencies] | Now |
| 2 | [tracks waiting on phase 1] | After [dependencies] merge |
| ... | ... | ... |

### After Each Track Merges
1. `git pull origin main`
2. Scan for merge conflicts (should be none if file scopes are clean)
3. Verify commit scope matches expected files: `git log -1 --stat` — flag if the commit only touched docs when code changes were expected
4. Verify issue closures: `for i in <expected issue numbers>; do echo -n "#$i: "; gh issue view $i --json state -q .state; done`
5. If any expected issues are still OPEN, close them now with the track's findings
6. Spot-check the agent summary against the diff for systematic errors or scope drift
7. [Track-specific verification if any]

### Final Gate (after ALL tracks merge)
```bash
npm run verify                    # Full CI mirror
node scripts/dead-code-check.js   # Dead code scan
# Verify ALL expected issues are closed
gh issue list --label <workflow-label> --state open --limit 50
```

After the final gate, read all agent summaries together and check that the combined result still makes sense. Independent fixes can each be correct locally while producing an integration problem together.

### Issue Closure Checklist
- **[Track Name] closes:** [issue numbers]
- **[Track Name] comments on:** [issue numbers]
- ...

**Coordinator responsibility:** If agents leave issues open (common — see Common Pitfalls), the coordinator closes them during the "After Each Track Merges" step. Do not defer to the Final Gate.
