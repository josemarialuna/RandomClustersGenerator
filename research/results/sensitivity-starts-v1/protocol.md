# Post-validation diagnostics: optimization and candidate-range sensitivity

Declared after inspecting primary and robustness validation, before these new
fits. This is a diagnostic follow-up, not independent replication or a new
confirmatory hypothesis. It addresses two limitations visible in the manuscript:
frequent upper-bound count selection and dependence on finite K-means starts.

Use exactly the first 50 primary validation families: master seed 2026092201,
k=4, p=2, m=100, sigma=0.05, q in {0,2}, uniform/normal noise, raw/standardized.
The family IDs and streams do not depend on candidate range or n_init, so all
dataset and label fingerprints must match the corresponding primary records.
Do not pool these repeated families with the 200 primary families.

Two one-factor changes are made separately:

1. `sensitivity-range.json`: candidate k=2..16, n_init=10. Original k=2..8
   fits and selections restricted to that subset must reproduce primary values,
   excluding timings. This tests the effect of extending the selection range.
2. `sensitivity-starts.json`: candidate k=2..8, n_init=100. This tests additional
   optimization effort with the original candidate range. It does not prove
   global optimality or replace the primary estimator after seeing results.

For each noise law and preprocessing mode, report known-k ARI, silhouette
correct-count rate, selected-count histogram, upper-bound frequency and signed
selected-minus-known-k ARI. Report paired changes against the same 50 primary
families with MCSE and pointwise t intervals; success proportions additionally
use Wilson intervals. Archive CH and DB results but do not change the primary
endpoint. Retain all failures/warnings. No stopping based on observed direction.

Interpretation must separate these effects. If more starts change recovery,
the manuscript must describe optimization sensitivity instead of attributing
the entire effect to the noise distribution. If extending k changes the selected
count, boundary dependence must be reported. If the main contrast persists,
the conclusion is limited to these tested perturbations and geometries.

Commit the protocol and JSON configurations before execution. Record and verify
source revision, configuration hashes, data fingerprints and exact archived
artifact bytes. These 300 datasets are repeated evaluations of primary data,
not 300 new independent datasets; archive counts must distinguish both notions.
