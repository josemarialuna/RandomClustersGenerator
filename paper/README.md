# Computational evidence for the Overleaf manuscript

The manuscript is written and checkpointed directly in Overleaf. This folder
contains analysis code and generated scientific evidence, not manuscript prose.
Earlier draft sources have been removed from the active Git tree at the author's
request; historical commits are preserved. Do not edit or version a manuscript
copy here. Numerical LaTeX tables are program outputs for import into Overleaf.

## Reproduce the evidence

From the repository root, install `.[research]` and run:

```bash
python paper/build_evidence.py
python paper/verify_evidence.py
```

The builder checks raw artifact hashes, regenerates all 3,750 validation
dataset/label fingerprints, confirms identical experimental source hashes across
the four runs, and derives tables and figures without refitting models. It
records its source hash and input/output hashes in `evidence_manifest.json`.
CSV files retain unrounded estimates. PDF metadata may vary between rendering
dates; numerical tables are deterministic. The standard-library verifier checks
the recorded artifacts without optional scientific dependencies.

The frozen run designs are in `research/VALIDATION_PROTOCOL.md` and
`research/validation-*.json`. Four output directories are under
`research/results/validation-*-v1`. Each has a report, raw data, configuration,
environment and source hashes. `research/environment-pilot.txt` pins the Python
3.12 dependencies used for both pilot and validation.

## Outputs

| Output | Meaning |
| --- | --- |
| `validation_summary.csv` | All conditions: known-k ARI, selected ARI, signed selection difference, count recovery and boundary selection |
| `validation_contrasts.csv` | Paired normal-minus-uniform differences with MCSE and pointwise t intervals |
| `selected_counts.csv` | Full distribution of selected k, including boundary choices |
| `geometry.csv` | Number of varying signal coordinates per independent family |
| `run_counts.csv` | Completed datasets, fits, selections, failures and observed elapsed times |
| `primary_table.tex`, `numbers.tex` | Automatically formatted numerical inputs for the manuscript |
| `validation.pdf`, `validation.png` | Cross-scenario illustration with uncertainty |

Success rates use Wilson intervals. Mean and contrast intervals are untruncated
Student-t intervals, so bounds can extend outside the parameter range. The
`selection_difference` endpoint is selected-k ARI minus known-k ARI; it differs
from raw `ari_regret`, which is best-candidate ARI minus selected-candidate ARI.

Timing is not a performance benchmark. A long wall-clock interruption occurred
during the eight-group run; elapsed time is retained unchanged. No model was
rerun or discarded because of this interruption. See the research decision log.
