# Bogdan Baciu Brand System

Use this reference after the skill triggers and the artifact needs more than the
quick rules in `SKILL.md`.

## Operating idea

The brand is an editorial personal site for a finance and technology operator.
It should read as restrained, literate, and hand-finished rather than SaaS-like
or decorative. The design works by narrowing the visual vocabulary:

- warm-cream paper
- ink text
- one Puddles sky-blue accent
- display serif moments
- mono utility labels
- flat borders and table rules
- a separate financial-artifact scope

## Source of truth

For web outputs, `assets/design-system/colors_and_type.css` is the portable
token file. Copy it with the sibling `fonts/` folder so the relative font URLs
continue to work.

Bundled paths:

| Path | Use |
|---|---|
| `assets/design-system/colors_and_type.css` | CSS tokens, font faces, table system, `.db-scope` |
| `assets/design-system/fonts/` | Geist, Instrument Serif, JetBrains Mono variable fonts |
| `assets/design-system/assets/` | Headshot, favicons, Puddles imagery, interest images, logos |
| `assets/design-system/preview/` | Small HTML reference swatches/components |
| `assets/design-system/ui_kits/` | Click-through website kit |

## Artifact modes

| Mode | Apply |
|---|---|
| Website/static HTML | Copy CSS and fonts; use semantic tokens/classes; verify rendered pages. |
| App UI | Map tokens into the app's design system; keep controls restrained and work-focused. |
| Slide deck | Translate palette/type hierarchy into master styles; use exact hex approximations where needed. |
| Document/report | Use the typography hierarchy and table rules; preserve the user's prose. |
| Financial exhibit | Use `.db-scope`, Macabacus color conventions, dense tables, and print-like surfaces. |
| Throwaway mock | Build static HTML first so the user can inspect the brand before production work. |

## Global palette

Use OKLCH from the CSS when the medium supports it. Use these hex approximations
when a tool requires hex:

| Token | Role | Approx hex |
|---|---|---|
| `--paper` | page background | `#f9f9fa` |
| `--ink` | primary text | `#262b34` |
| `--ink-soft` | secondary text | `#646b78` |
| `--ink-faint` | tertiary text | `#a3a8b1` |
| `--rule` | borders and hairlines | `#d8dadf` |
| `--sky-100` | hover row tint / soft fill | `#ecf3f7` |
| `--sky-300` | portrait/fill accent | `#aacde0` |
| `--sky-600` | primary accent / links | `#0a6e9a` |
| `--sky-700` | chrome bar / footer | `#0b4f76` |
| `--sky-900` | dark button / deep ink | `#152234` |

Rust exists for selection and focus only:

- selection: warm rust highlight
- focus ring: rust outline

Do not use rust as a general CTA color or decorative accent.

## Typography

| Role | Primary | Fallback |
|---|---|---|
| Display/name/section heads | Instrument Serif | Times New Roman, serif |
| Body/UI | Geist | system sans-serif |
| Eyebrows/chips/chrome/code | JetBrains Mono | ui-monospace, monospace |
| `.db-scope` body | Source Serif 4 | Iowan Old Style, Charter, Georgia, serif |

Rules:

- Display serif carries the brand. Use it for the name, section heads, ledes,
  and rare editorial emphasis.
- Italic `em` inside display text should use the sky accent sparingly.
- Body prose can be large and justified when the format supports it.
- Eyebrows and utility labels are uppercase mono with generous tracking.
- Tables use tabular lining numerals.

## Layout and shape

- Global rhythm: `6 / 10 / 14 / 20 / 28 / 40`.
- `.db-scope` rhythm: `4 / 8 / 12 / 16 / 24 / 32 / 48 / 64 / 96 / 128`.
- Reading caps: reading `65ch`, prose `74ch`, wide `80ch`, shell `1400px`.
- Fixed site chrome is `104px` high where the full website frame is used.
- Default radius is `2px`.
- Card radius is `16px` and should be rare.
- Pill radius is `999px` and belongs to chips/status pills.
- In `.db-scope`, card radius becomes `3px`.

When a composition feels tight, widen the container before reducing type size.

## Tables and financial artifacts

Use `div.bbt-wrap` around `table.bbt` for editorial tables.

Table behavior:

- dark navy header
- white uppercase header text
- 1px row separators
- light zebra rows
- hover on every row
- total rows use cream fill and a 2px navy top border
- source lines and footnotes are explicit
- numeric columns are right-aligned with tabular lining figures
- null values use dashes
- negatives use parentheses

Financial-model exhibits must stay inside `.db-scope`.

`.db-scope` token highlights:

| Token | Role | Hex |
|---|---|---|
| `--db-paper` | artifact background | `#faf7f2` |
| `--db-panel` | panel surface | `#fffdf8` |
| `--db-ink` | artifact text | `#1a2330` |
| `--db-rule` | artifact rules | `#d6cfc1` |
| `--db-accent-rust` | artifact rust | `#b85e3a` |
| `--db-accent-teal` | artifact teal | `#2c6e6e` |
| `--cell-input` | hardcoded inputs | `#0000FF` |
| `--cell-link` | cross-sheet links | `#00B050` |
| `--cell-driver-fill` | driver-cell fill | `#FFFFCC` |

Driver cells require both yellow fill and blue font. Do not treat yellow as a
standalone brand color.

## Voice and copy posture

The design system should not invent the owner's voice. If a new public-facing
sentence is missing, place `TBU` and make the gap visible.

Preferred tone when copy already exists:

- first-person when appropriate
- candid and technically literate
- editorial rather than hype-driven
- precise about finance, systems, and artifacts
- no emoji in public-facing chrome/body copy

Use sentence case for prose. Reserve title case for proper nouns and established
chrome labels. Mono labels are uppercase.

## Iconography and imagery

The brand is intentionally icon-poor.

Use, in order:

1. bundled logos or images that already exist
2. Unicode-style editorial ornaments only when already part of the surface
3. a restrained Lucide-style utility icon only when the interface genuinely
   needs an icon; flag that substitution in the handoff

Do not add a general icon font or broad icon library to a production site just
for decoration.

Imagery should be warm-cool and specific. Puddles images are the literal blue
accent. Avoid dark, blurred, stock-like, or purely atmospheric media.

## Verification

Before closing:

- confirm copied font paths resolve
- inspect mobile and desktop widths for overflow or cramped type
- verify `--sky-*` remains the global accent
- verify rust appears only in selection/focus unless an existing artifact
  intentionally uses it
- verify `.db-scope` rules do not leak globally
- inspect tables for captions, source lines, totals, numeric alignment, and
  scroll behavior
- report any substitutions or unresolved `TBU` placeholders
