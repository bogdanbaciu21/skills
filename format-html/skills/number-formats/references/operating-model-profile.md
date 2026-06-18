# Operating Model Profile

The `--profile operating-model` helper is a whole-sheet shortcut for a standard
FP&A operating model:

- Format every numeric value and formula in the used range with the house
  `number` format first.
- Auto-color hardcoded numeric assumptions blue and cross-sheet formulas green.
- Treat rows whose first cell contains `margin` or ends in `%` as percent rows
  and style them grey/italic.
- Treat rows labeled `total`, `ebitda`, `fcf`, or `free cash flow` as bold
  total rows.

Use this profile for first-pass cleanup of a model tab. Then apply narrower
`--range` calls for rows that need percent, multiple, toggle, or custom labels.
