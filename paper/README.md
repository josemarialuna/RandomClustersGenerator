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

## Post-validation sensitivity analysis

`research/SENSITIVITY_PROTOCOL.md` freezes two separate diagnostic changes:
candidate counts 2–16 with ten starts, or 100 starts with counts 2–8. Both reuse
the first 50 primary families: 300 evaluations of 150 distinct datasets, not
new independent replicates. Run `python paper/analyze_sensitivity.py` to audit
the pairing and rebuild `sensitivity_*.csv` and their manifest. Shared candidate
metrics must replay exactly when extending the range; Ward ARI must remain
unchanged in both diagnostics. The standard-library verifier also checks these
derived outputs. Raw archives retain all 7,200 fits and 1,800 selections.

## Crossed, factorial, operational and coverage revision

The pre-execution design is `research/EXTENSION_PROTOCOL.md`, frozen with the
experimental code at `d1ed040a02e3193601e03a4d80b91bdb958c23fd`. From that checkout:

```bash
python -m research.extension.run interaction --output data/extension-interaction
python -m research.extension.run generalization --output data/extension-generalization
python -m research.extension.run coverage --output data/extension-coverage
python -m research.extension.run performance --output data/extension-performance
```

Run performance sequentially, after other computational work has finished.
Each command refuses an existing directory. The archived executions are under
`research/results/extension-*-v1`; they contain all candidate labels as compressed
NumPy archives, not just aggregate scores. No pickle is required to load labels.
The factorial geometries are experimental constructions, not public API options.

```bash
python paper/analyze_extension.py
python research/verify_extension.py
```

The analyzer checks frozen source bytes against Git (requires the recorded commit
in local history), regenerates all 4,520 datasets, and checks all 36,240 saved
candidate label hashes and ARIs. It does not refit K-means. Outputs include:

| Output | Meaning |
| --- | --- |
| `extension_interaction.csv`, `extension_interaction_contrasts.csv` | Four crossed configurations; paired differences in differences |
| `extension_mechanisms.csv`, `extension_selected_k_counts.csv` | Selected-partition feature diagnostics and full count distribution |
| `extension_factorial_cells.csv` | Every factorial cell, law and index, including the no-noise baseline |
| `extension_factorial_noise_contrasts.csv` | Paired Gaussian-minus-uniform correct-count differences per cell |
| `extension_factorial_effects.csv` | Equal-cell-weight main contrasts of those differences; approximate Welch and conservative weighted Hoeffding intervals |
| `extension_performance.csv`, `extension_performance_ratios.csv` | Medians and paired ratios of the 120 operational trials |
| `extension_coverage_worst.csv` | Minimum exact coverage on the entire prespecified probability grid |

Raw coverage tables also contain expected widths. CP/Bonferroni and Hoeffding
intervals have conservative pointwise guarantees under their independence and
support assumptions; there is no simultaneous coverage claim across endpoints.
Mechanism summaries describe associations, not causal attribution. Performance
is local: tracked allocations are not RSS, and generation does not measure
clustering scalability or human effort. The standard-library verifier is in CI.

## Reviewer-driven supplementary analysis

`python paper/review_evidence.py` derives six additional tables without changing
any experimental archive or the earlier analysis. It uses the nesting of fixed
candidate fits to prove that the crossed correct-count interaction lies in
`{-1,0,1}`, checks that expansion never improves correct-count recovery, and
reports both the sharper Hoeffding and CP/Bonferroni bounds. The original wider
bound remains reproducible in `extension_interaction_contrasts.csv`.

Additional tables expose all three indices, compare signal/noise contributions
at fixed candidate counts, and report timing quartiles and ranges. The check
also confirms that 100 nested starts never increase best inertia relative to
ten starts. These are post-review summaries, not new prospective hypotheses.
`review_02_hardware.json` records the same PC's inventory during review; it is
not contemporaneous benchmark telemetry. Run `python paper/review_evidence.py
--check` on one line to verify the supplementary manifest; CI runs this check.
