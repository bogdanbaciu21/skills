<!--
PR title contract (required): `type(scope): user-facing description`
Types: feat, fix, improve, refactor, docs, chore. Scope in parentheses only
when it adds clarity. For fixes, name the user-visible symptom and trigger,
not the code-level cause:
  good: fix(ingest): queue stalls when Slack returns 429
  bad:  fix: add null check to slack response

Linked context (required): keep the `## Item` section filled with the
build-queue item id (e.g. DVO-110), the Linear id (e.g. LG-12345), or the
GitHub issue (Fixes #123 / Closes #123). `Fixes`/`Closes` only when this PR
fully satisfies it; otherwise `Related: #123`.

Emergency path: if this is an emergency security fix and you cannot complete
the expanded sections, add a `Emergency-Override: <reason>` line under
`## Item` and fill the four core sections. The override is recorded by
bin/pr_template_enforcer.py and audited later; it is not a silent bypass.
-->

## Item

<!-- Required. Build-queue id (XXX-###), Linear id (LG-#####), or GitHub issue ref. -->
<ITEM-ID>

## What problem this solves

<!-- Required. The concrete user, product, or operational problem.
For fixes begin with: "Fixes an issue where <who> <does X> would
<experience Y> when <condition>." Name the affected surface or workflow;
do not describe the code-level cause here. -->

- User problem:
- Bounded outcome:
- Non-goals:

## Why this change was made

<!-- Required. One to three sentences: the shipped solution, key design
decisions, and boundaries. No file-by-file narration. -->

## User impact

<!-- Required. What users, operators, or agents can now do or expect.
If there is no user-visible impact, say so plainly and say why. -->

## Evidence

<!-- Required. The most useful proof that this change works: exact commands
and their results (OK_*/ERR_* tokens), focused tests, CI runs, screenshots,
redacted logs, or artifact links. Name what was NOT exercised and why.
Honest negative statements belong here ("no credential storage changes",
"provider calls are synthetic"). -->

### Proof

<!-- Required: the exact proof command(s) run and the observed result. -->
<proof command(s) + result>

### Gate evidence

<!-- Required: what the verify/land gates observed. -->
- compile: `python3 -m py_compile <changed files>`
- self-test: `python3 bin/<script>.py --self-test` -> `OK_*_SELF_TEST`
- preflight/land: <command + result, or "not applicable - <reason>">

| Command or manual flow | Environment | Result |
| --- | --- | --- |
|  |  |  |

- Paths not exercised and why:

### Screenshots or recording

<!-- Required for UI/interaction changes: before/after, viewport/device,
light/dark or accessibility state. Otherwise: "not applicable - no visual
change" with reasoning. Synthetic/sanitized data only. -->

<details>
<summary><b>Expanded sections — required when triggered; otherwise write "not applicable" with a one-line reason</b></summary>

## Privacy and security

<!-- Required when the change touches secrets, credentials, authn/z, data
boundaries, PII/customer data, network exposure, prompts, or session state. -->

- New or changed data collected, stored, logged, or transmitted:
- New external recipient, permission, secret, network exposure, or trust boundary:
- Threat/failure cases tested:
- Security review or private advisory link, if applicable:

## Migrations and compatibility

<!-- Required when the change touches schema, config, protocol, package, or
native contracts other systems depend on. -->

- Migration and forward/backward compatibility window:
- Idempotency and partial-failure behavior:

## Rollback

<!-- Required when the change is not trivially revertable or leaves
persistent state. -->

- Exact rollback or disable path:
- State that cannot be rolled back automatically:
- Signal that should trigger rollback:

## Documentation and release surface

<!-- Required when the change is user-visible or changes an operating
contract. -->

- Docs updated:
- Changelog category: <!-- breaking/security/migration/deprecation/added/changed/fixed/none -->
- License, NOTICE, third-party inventory, branding, or provenance impact:

</details>

<!-- Never paste live credentials, exploit details, prompts, identities,
customer data, or private filesystem paths into a PR. Report security
concerns privately to the repository owner. -->

## Author checklist

- [ ] The item id, acceptance criteria, and user impact are complete.
- [ ] The title follows `type(scope): user-facing description`.
- [ ] The change is focused; unrelated edits and private local artifacts are absent.
- [ ] I ran the commands above and reported failures or untested paths honestly.
- [ ] Triggered expanded sections are filled; untriggered ones say "not applicable" with a reason.
- [ ] No secret, token, device-link URL, prompt, identity, customer data, private path, or zero-day detail is exposed.
- [ ] I did not weaken tests, release gates, security controls, or repository visibility to make this pass.

## Reviewer checklist

- [ ] Acceptance evidence is reproducible from the stated revision.
- [ ] The changed path and nearest trust/compatibility boundary were exercised.
- [ ] Security, privacy, migration, rollback, and docs claims are supported.
- [ ] High-risk self-authored work has the independent review required by governance.
