# Technical figures

These SVGs are deterministic renderings of checked-in experiment artifacts. They use
no stock imagery, decorative illustration, or manually adjusted result values.

| Figure | Source |
|---|---|
| `accuracy-compliance-tradeoff.svg` | Group metrics in `results/qwen2.5-7b/primary/combined/summary_clean.json` |
| `paired-effects.svg` | Paired estimates, bootstrap intervals, and exact McNemar p-values in the same summary |
| `evaluation-design.svg` | Frozen design recorded in `docs/methodology.md` |

Regenerate them from the repository root:

```bash
python scripts/build_figures.py
```

The generator uses only Python's standard library and writes accessible SVG title and
description elements.
