## Issue and outcome

- Tracking issue: <!-- Required. Use Fixes/Closes only when this PR fully satisfies it. -->
- User problem:
- Bounded outcome:
- Non-goals:

## User impact

<!-- Who is affected? What observable behavior changes? Include compatibility, performance, accessibility, and failure-mode impact. State "none" with evidence rather than leaving blank. -->

## Evidence

### Tests and commands run

| Command or manual flow | Environment | Result |
| --- | --- | --- |
|  |  |  |

- Paths not exercised and why:
- Clean-checkout/install evidence:

### Screenshots or recording

<!-- Required for UI/interaction changes. Include before/after, viewport/device, light/dark or accessibility state, and synthetic-data confirmation. Write "not applicable - no visual change" with reasoning when appropriate. -->

- Evidence links/files:
- Synthetic or sanitized data confirmed: <!-- yes/no -->

## Privacy and security

- New or changed data collected, stored, logged, or transmitted:
- New external recipient, permission, secret, network exposure, or trust boundary:
- Authentication, authorization, encryption, sandbox, prompt/session, path, or attachment impact:
- Threat/failure cases tested:
- Security review or private advisory link, if applicable:

<!-- Never paste live credentials, exploit details, prompts, identities, customer data, or private filesystem paths into a PR. Use SECURITY.md for vulnerabilities. -->

## Migrations and compatibility

- Database/schema/config/protocol/package/native migration:
- Forward and backward compatibility window:
- Idempotency and partial-failure behavior:
- Backup/restore or data-loss risk:

## Rollback

- Exact rollback or disable path:
- State that cannot be rolled back automatically:
- Signal that should trigger rollback:

## Documentation and release surface

- Docs updated:
- Changelog category: <!-- breaking/security/migration/deprecation/added/changed/fixed/none -->
- README/status/architecture/privacy/security/support changes:
- License, NOTICE, third-party inventory, branding, or provenance impact:

## Author checklist

- [ ] The issue link, acceptance criteria, and user impact are complete.
- [ ] The change is focused; unrelated edits and private local artifacts are absent.
- [ ] I ran the commands above and reported failures or untested paths honestly.
- [ ] UI evidence uses synthetic/sanitized data and covers affected breakpoints/states.
- [ ] Privacy/security effects and new data recipients are explicit.
- [ ] Migrations, compatibility, and rollback are tested or marked not applicable with evidence.
- [ ] Documentation and changelog are updated for user-visible behavior.
- [ ] I preserved upstream/third-party notices and identified copied, adapted, or generated material.
- [ ] No secret, token, device-link URL, prompt, identity, customer data, private path, or zero-day detail is exposed.
- [ ] I did not weaken tests, release gates, security controls, or repository visibility to make this pass.

## Reviewer checklist

- [ ] Acceptance evidence is reproducible from the stated revision.
- [ ] The changed path and nearest trust/compatibility boundary were exercised.
- [ ] Screenshots/recording match the implementation and contain no private data.
- [ ] Security, privacy, migration, rollback, docs, and notice claims are supported.
- [ ] High-risk self-authored work has the independent review required by governance.
