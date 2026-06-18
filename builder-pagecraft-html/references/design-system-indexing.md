# Design System Indexing

Use this reference for Builder Design System Intelligence, `index-repo`, scoped
indexes, and index refinement.

## Dan-Specific Authority

Builder's design-system index is a retrieval layer over real local sources. It
does not replace these authorities:

- `DESIGN.md`
- `docs/uxos.md`
- `config/uxos/tokens.json`
- `config/uxos/components.json`
- `config/uxos/rules.json`
- `brain/_repos/Bogdan-Baciu-Design-System/colors_and_type.css`
- `.agents/skills/pagecraft/`
- `.agents/skills/bogdan-baciu-design/`

If Builder output conflicts with those files, fix Builder context or output; do
not loosen the design system.

## Index Lifecycle

1. Run indexing in the design-system/component repository when possible.
2. Include source, tokens, comments, examples, stories, tests, and usage docs.
3. Exclude runtime state, secrets, inboxes, logs, raw private data, generated
   dependency folders, and deprecated/internal items not meant for consumers.
4. Add the design-system name to `builder.config.json` when an index is real and
   available to the project.
5. Re-run indexing when components, tokens, architecture, or usage rules change.

In this repo, use the workflow wrapper so include/exclude lists and proof stay
consistent:

**LOCAL Mac -- zsh**

```bash
cd /Users/danb/src/dans-brain
python3 bin/builder_html_workflow.py --profile prepare --execute --allow-prompts --write-proof
```

If `index-repo` returns `builder_enterprise_subscription_required`, record that
Builder auth works but DSI is plan-blocked. Continue with explicit local source
files and do not claim index-backed generation.

## Scoped Indexes

Use scopes deliberately:

- Space scope: app-specific components or private experiments.
- Organization scope: shared design systems used across multiple Builder Spaces.
- Global scope: only for public/open libraries or Builder-managed content.

Name indexes with clear ownership and versions, for example
`bogdan-uxos-1.0.0` or `acme-client-ui-2026.06`. Before changing a scope, check
which projects reference the index in `builder.config.json` and coordinate any
breaking access change.

## Refinement Order

When Builder maps tokens or components incorrectly, fix in this order:

1. **Source material first.** Improve component comments, token names, prop
   types, examples, or docs so the truth is useful to humans and indexes.
2. **Correction rules second.** Add scoped `.builder/rules/*.mdc`,
   `.builderrules`, or `AGENTS.md` guidance when source edits are not feasible or
   the issue is a cross-cutting usage rule.
3. **Exclusions third.** Exclude deprecated, misleading, internal, or WIP files
   and document the replacement.

If only one component or token group changed, use the CLI's targeted component
indexing option when available rather than refreshing everything blindly.

## Naming Hygiene

Builder matches design-system context better when names are semantic and aligned:

- Figma/component names should map to real code component names where possible.
- Variant names should describe meaning, such as `primary`, `secondary`,
  `danger`, `small`, `medium`, and `large`.
- Avoid generic names like `Container`, `Text Component`, `style1`, or emoji-led
  labels that hide the component's role.
- Tokens should prefer semantic names over raw primitive leakage when the
  consumer should use a semantic token.

Dan does not use Figma as the source of truth, but the same naming rule applies
to local components, tokens, Pagecraft classes, and Builder prompts.

## Local Index Defaults

The local process indexes:

- `DESIGN.md`
- `docs/uxos.md`
- `config/uxos/**`
- `.builder/**`
- `.builderrules`
- `.builder/skills/builder-pagecraft-html/**`
- `.agents/skills/builder-pagecraft-html/**`
- `.agents/skills/pagecraft/**`
- `brain/_repos/Bogdan-Baciu-Design-System/**`

It excludes:

- `state/**`
- `logs/**`
- `inbox/**`
- `node_modules/**`
- `vendor/**`
- `budget/data/**`
- `**/.env`
- `**/.env.*`

## Review Gate

Use `builder-dsi-index-reviewer` when indexing config, design-system context, or
Builder rules change. It should verify that the index includes the right
authorities, excludes sensitive/runtime paths, and names any plan/auth blocker.
