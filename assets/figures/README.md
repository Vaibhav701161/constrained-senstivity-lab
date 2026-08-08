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
| `contract-alignment-pipeline.{png,svg}` | Implemented Qwen-era signed-string to integer pipeline documented in `docs/representation-alignment-results.md` |
| `corrected-replication-effect.{png,svg}` | Corrected 7B decision, exact paired summary, and artifact validation |
| `corrected-replication-transitions.{png,svg}` | Full 2 by 2 paired correctness table from the corrected 49-item analysis |
| `corrected-replication-item-map.{png,svg}` | Item-level correctness derived from the corrected Outlines rows after verified byte equivalence with XGrammar |
| `canonical-schema-correction.{png,svg}` | Final canonical Llama paired summary plus all 22 manual discordance attributions |
| `cross-family-evidence.{png,svg}` | Accepted paired effects and exact bootstrap intervals from corrected Qwen, canonical Llama, and the bounded executable pilot |
| `tool-call-pilot-result.{png,svg}` | Component success rates and paired transition matrix from the frozen 30-case executable primary sample |
| `validity-semantics-separation.{png,svg}` | Baseline group metrics plus the three accepted representation-pair summaries, shown without pooling task domains |
| `paired-outcome-composition.{png,svg}` | Exact paired state counts from corrected Qwen, canonical Llama, and executable summaries |
| `llama-paired-item-map.{png,svg}` | All 150 canonical Llama item transitions, with discordances labeled by frozen GSM8K source index |
| `canonical-correction-delta.{png,svg}` | Direct row comparison between broad and canonical Llama controls, including raw, normalized-answer, and correctness changes |
| `research-system-architecture.{png,svg}` | Model-agnostic architecture documented in `docs/architecture.md` and the current research methodology |

Regenerate them from the repository root:

```bash
python scripts/build_figures.py
python scripts/build_corrected_replication_figures.py
python scripts/build_replication_gate_figures.py
python scripts/build_evidence_dashboard_figures.py
python scripts/sync_docs_figures.py
```

The generator requires Matplotlib and writes both browser-ready PNG files and
publication-ready vector SVG files.
