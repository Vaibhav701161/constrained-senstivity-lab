# Technical figures

These PNG and SVG files are deterministic Matplotlib renderings of checked-in
experiment artifacts. They use no stock imagery, decorative illustration, or
manually adjusted result values.

| Figure | Source |
|---|---|
| `accuracy-compliance-tradeoff.{png,svg}` | Group metrics in `results/qwen2.5-7b/primary/combined/summary_clean.json` |
| `paired-effects.{png,svg}` | Paired estimates, bootstrap intervals, and exact McNemar p-values in the same summary |
| `paired-transitions.{png,svg}` | Concordant and discordant item counts in the paired comparisons from the same summary |
| `field-order-sensitivity.{png,svg}` | Recoverable accuracy, strict accuracy, and schema compliance by output-field order |
| `evaluation-design.{png,svg}` | Frozen design recorded in `docs/methodology.md` |

Regenerate them from the repository root:

```bash
python scripts/build_figures.py
```

The generator requires Matplotlib and writes both browser-ready PNG files and
publication-ready vector SVG files.
