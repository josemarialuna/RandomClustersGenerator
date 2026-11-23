# Paired workflow evaluation, version 1

Defined on 2026-11-23 before running the new evaluation. Earlier studies and
their source references remain historical evidence and are not overwritten.

## Questions and scope

1. Does the public API preserve the declared pairing invariants under changes
   in nuisance count, nuisance law and residual scale?
2. Can an independently implemented NumPy baseline perform the same task?
   Compare numerical output and complete workflow cost, not only sampling.
3. Can a third party regenerate data and audit all metrics and selections from
   the saved archive without fitting again?
4. How do example pipelines respond to the stated perturbations in balanced,
   unequal-size and anisotropic Gaussian scenarios? This is a software
   demonstration, not a universal ranking of algorithms.

## Scientific demonstration

Four explicit centers (0,0), (0,1), (1,0), (1,1). Three scenarios:
balanced spherical (50 observations per component), unequal sizes
(20,40,60,80), and balanced anisotropic (50 each). Anisotropic covariance
matrices have determinant one and eigenvalues 4 and 0.25, with alternating
orientations of 0 and 45 degrees. Thus n=200, p=2 and k=4 stay fixed.
Scenario comparisons change group-size allocation or covariance shape only.
They do not constitute equal-overlap comparisons.

Twenty independent family replicates per scenario (master seed 20261123).
The same replicate stream keys across scenarios couple residual draws, but
changes in sizes alter group membership. Row/label pairing guarantees apply
within a scenario, not across unequal-size scenarios.

Cross residual scales 0.10 and 0.25 with nuisance counts 0,2,8. For positive
counts use both uniform and normal laws, giving 10 conditions per family,
600 datasets total. Both noise laws have mean 0.5 and variance 1/12.
Use raw and standardized features. Candidate counts 2,3,4,5,6. Four methods:
K-means, Ward, average linkage and full-covariance Gaussian mixture. Ten
initializations for K-means/GMM, maximum 300 iterations. Fit seeds depend on
family, method and count, not condition or preprocessing. One numerical thread.
Total: 24,000 candidate fits and 14,400 ICVI selection records.

Select by maximum Silhouette/CH or minimum DB, breaking exact ties toward
smaller k. Any invalid candidate or convergence warning makes that grid's
selection unavailable. Keep failures in denominators. Report failure counts
and summarize valid agreement separately. Labels and row IDs never enter
preprocessing, fitting or ICVI selection. ARI/AMI evaluate the selected
partition and the candidate at k=4.

Report cellwise means, paired differences across noise counts within family,
and Monte Carlo standard errors across the 20 independent families. Do not
treat condition rows as independent replicates. No p-values or simultaneous
coverage claims. Summaries and the first family gallery are fixed in advance.
The two scales are illustrative conditions, not an overlap calibration.

## Operational comparison

Independent NumPy baseline implements the same stream specification without
importing family-generation code. NumPy rather than make_blobs is used because
arbitrary covariances and reusable residuals require additional sampling logic.
This compares complete paired tasks, not superiority over NumPy.

For n=200 and n=2,000, four balanced groups, two coordinates and three conditions
(scale=.1,q=0), (.1,2), (.25,8), perform seven trials per implementation in
alternating order. Measure generation, CSV+JSON export, checksum verification
and numerical regeneration. Clustering timing is reported separately by the
scientific workflow if measured, not hidden within a generator timing.
Record each trial, median and range, Python-traced peak allocations (not total
process RSS), machine, package versions and source hashes. Disk cache and
interpreter startup are not controlled/included. No human time savings claim.
Both methods must pass the same signal, prefix, labels, row identity, replay
and covariance checks. Compare numerical equality independently of timings.

## External use

No independent user study has been conducted. A separate task protocol can be
prepared, but author-executed examples are not independent adoption evidence.

## Reproduction

The committed configuration files are authoritative. Archive source commit,
dependency freeze, raw candidate partitions, fit records and selection records.
Run the deep auditor on each completed archive. A failed or interrupted run is
not complete until its manifest exists. Changes to this protocol after execution
must be identified as amendments, not described as prespecified.
