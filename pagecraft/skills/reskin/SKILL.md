---
name: reskin
description: Apply a repo's design system across its HTML pages — a "reskin." Detects the design system a repo has (an installed *-design / *-brand skill, a tokens stylesheet, or a reskin.json manifest), syncs its tokens + assets into the served dir, and reframes each page with the design system's nav / hero / footer (stripping the old chrome, injecting the brand frame, idempotently). Use when the user says "reskin", "apply the design system", "apply the brand", "rebrand this site", "frame these pages", or is working in a repo that has a design/brand skill installed. Part of the pagecraft bundle.
---

# Reskin

Apply the design system a repo already carries across its pages — the generalized
version of the per-repo "apply brand frame" scripts (e.g. LJB's
`apply-brand-frame-v3.py`). Repo-aware: it works off whatever design system the
current repo exposes, so the same `reskin apply` command brands an LJB portal, an
SLG comp portal, or a bogdanbaciu site.

## Hybrid model — one command, two engines

- **Bespoke applier present** → reskin **runs the repo's own script** per page
  (declared as `apply_command` in `reskin.json`, or auto-detected like
  `apply-brand-frame-*.py`). Repos that already invested in a custom framer keep it.
- **No bespoke applier** → reskin uses its **built-in generic injector**, driven
  by the design system's `frame/` templates. New repos work the moment they expose
  the contract.

Either way: `reskin apply`.

## Workflow

```bash
python3 reskin.py detect --repo .          # what design system + applier exists here?
python3 reskin.py init   --repo .          # scaffold a reskin.json from what's detected
#   …fill in served_root, assets_target, and the pages[] list…
python3 reskin.py validate --repo .        # validate manifest shape + referenced files
python3 reskin.py apply  --repo . --dry-run    # preview every reframe + asset sync, write nothing
python3 reskin.py apply  --repo .              # do it (idempotent — already-framed pages are skipped)
python3 reskin.py verify --repo .              # pagecraft keystone guard + brand-asset presence
```

`apply --page path/to/one.html` reskins a single page. Re-running is safe: a page
that already contains the `framed_marker` is skipped.

## The contract — `reskin.json` (repo root)

```json
{
  "design_system": {
    "source": ".claude/skills/ljbcpa-design",   // dir holding the brand (skill or standalone repo)
    "tokens_css": "colors_and_type.css",         // relative to source
    "assets": "assets",                          // relative to source — logos, icons, fonts
    "frame": "frame"                             // OPTIONAL — dir of nav.html/hero.html/footer.html
  },
  "served_root": "brian-portal",                 // dir whose HTML pages get reskinned ("." for repo root)
  "assets_target": "assets/ljb-brand",           // where assets land under served_root
  "framed_marker": "class=\"brand-nav\"",        // presence on a page = already framed (idempotency)

  // EITHER declare a bespoke applier (hybrid run-path):
  "apply_command": "python3 brian-portal/scripts/apply-brand-frame-v3.py {page} \"{eyebrow}|{headline_pre}|{headline_em}|{subhead}|{page_label}\"",

  // …OR rely on design_system.frame templates (generic injector).

  "strip_patterns": [ "...optional regex overrides; defaults are the proven set..." ],
  "pages": [
    { "path": "brian-portal/use-cases/uc-01.html",
      "eyebrow": "use case", "headline_pre": "Document extraction",
      "headline_em": "at scale", "subhead": "One-line deck.", "page_label": "UC-01" }
  ]
}
```

`reskin init` pre-fills `design_system`, `apply_command` (if a bespoke applier was
found), and a `pages[]` stub; you fill in `served_root`, `assets_target`, and the
per-page copy.

`apply_command` is parsed into argv and run without a shell, so manifest strings
cannot execute shell metacharacters like `;` or `&&`. Keep commands simple:
executable, script path, page path, and one quoted metadata payload.

## Frame templates (generic path)

When there's no bespoke applier, put three files in `design_system.frame/`:
`nav.html`, `hero.html`, `footer.html`. The injector substitutes these
placeholders per page: `{{eyebrow}}`, `{{headline_pre}}`, `{{headline_em}}`,
`{{subhead}}`, `{{page_label}}`, `{{page_file}}`, `{{page_path}}`. It strips the
page's existing nav/hero/`<h1>`/lede/meta (the proven strip set, overridable via
`strip_patterns`) and injects `nav` + `hero` at the top of `<body>` and `footer`
before `</body>` — exactly the v3 mechanism, generalized.

## What it does NOT do

- It does **not** invent brand assets, colors, or copy — those come from the
  repo's design system. Per-page headline/eyebrow/subhead come from `pages[]`.
- It does **not** guess a repo has a design system — `detect` reports honestly,
  and `apply` refuses without a `reskin.json`.
- It does **not** restructure page *content* — only the surrounding frame +
  synced assets. Verify with `reskin verify` (the bundled pagecraft keystone guard)
  and the full `runner.py` wrap probe after a reskin.

## Skill maintenance

When editing the manifest contract or apply path, run:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests/test_reskin.py
```

The test fixtures include a public-safe screenshot-diff contract under
`tests/fixtures/screenshot-diff/` so browser checks can compare selector geometry
without storing private page screenshots.
