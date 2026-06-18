# Brand Routing Reference

Choose brand before layout. Brand owns palette, type, voice, and visual density.
Pagecraft supplies mechanics and gates.

## Decision Table

| Context | Brand route | Source |
|---|---|---|
| Acme client-facing, Client-facing, Acme portal/report/deck | Acme brand | `/root/repos/acme/.agents/skills/acme-design/SKILL.md` or the same skill inside the Acme repo |
| Dan-owned, personal, internal, ambiguous | Bogdan Baciu | `.agents/skills/bogdan-baciu-design/SKILL.md`, `DESIGN.md`, `config/uxos/*.json` |
| bogdanbaciu.com public/editorial/site UI | bogdanbaciu.com product design | `PRODUCT.md`, `design.md`, existing Phoenix components/CSS |
| Other client | That client's design system | inspect the client repo first |
| Pure mechanics review with no visual output | Pagecraft only | `.agents/skills/pagecraft/SKILL.md` |

## Acme

Use the `acme-design` skill when available. Its high-order constraints:

- Import `colors_and_type.css` first and reference tokens.
- Use Open Sans and official Acme assets/logos.
- Use the real Acme brand gradient only for hero/cover moments.
- Prefer evidence tables and source registers over decorative cards.
- No emoji, fake numbers, localhost/file links, or internal strategy leakage in
  client-facing artifacts.
- Validate with the Acme skill's validator when editing inside the Acme repo.

For Acme/client-branded HTML in `dans-brain`, do not run Dan's personal
`brand_lint.py` as if the page should be Bogdan-branded. Use:

**VPS Hetzner -- ssh shell**

```bash
cd /root/dans-brain
python3 bin/pagecraft_qa.py --html path/to/client.html --no-brand-lint
```

## Bogdan Baciu / Dan UX OS

Use Bogdan for Dan-owned, personal, internal, or ambiguous visual artifacts.

- Start from `.agents/skills/bogdan-baciu-design/SKILL.md`.
- Use `DESIGN.md`, `docs/uxos.md`, and `config/uxos/*.json` for agent-readable
  rules.
- Use `colors_and_type.css` and local fonts/assets when making portable HTML.
- Keep the global brand warm paper, ink, one Puddles sky-blue accent, flat
  borders, and restrained type.
- Reserve `.db-scope` for embedded financial-model exhibits.
- Do not use generic purple AI palettes, broad gradients, glassmorphism,
  nested cards, decorative blobs, or invented chip colors.

## bogdanbaciu.com

Use the personal-site product system for public site work.

- Read `PRODUCT.md` first for audience, purpose, anti-references, and
  accessibility stance.
- Read `design.md` before changing UI, layout, tables, typography, or token use.
- Use the global Puddles palette for the site; reserve `.db-scope` for embedded
  financial-model artifacts.
- Do not invent public copy, headings, CTA labels, visible alt text, or article
  prose. Use `TBU` when Dan has not supplied the words.
- Never publish or flip a post live from this skill. Deploying committed staged
  work is separate from publishing.

## Copy And Claims

- Preserve user-provided copy and source-backed facts.
- Use `TBU` for missing Dan-authored public prose.
- Never invent metrics, dates, ROI, quotes, client claims, or source labels.
- Put provenance close to tables, charts, KPIs, and claims.
