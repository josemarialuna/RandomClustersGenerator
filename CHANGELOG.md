# Changelog

## 1.1.0

* Public paired Gaussian families with explicit centers, unequal group sizes
  and per-component positive-definite covariance matrices.
* Stable random streams for residuals, rows, nuisance columns and fitting.
* Separate features, labels and observation identities.
* Replay sidecars, dataset integrity checks and numerical regeneration.
* JSON experiment runner retaining candidate partitions, warnings, failures
  and internal-index decisions, plus a deep metric/selection auditor.
* Paired API reference, three task walkthroughs and an independent NumPy
  baseline. New studies use their own frozen protocol and configurations.

Legacy generation and historical research streams are unchanged. The new API
has its own `paired-gaussian-v1` convention. Equal seeds across interfaces do
not imply equal datasets. No published manuscript or independent user study
is implied by this software release.
