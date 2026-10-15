# Multi-method dataset demonstration

Protocol fixed before execution, 15 October 2026.

## Aim and scope

Demonstrate how the public generator supports controlled clustering experiments.
This is not a general ranking of algorithms. Balanced spherical Gaussian groups
favor some methods. Dispersion is an input factor, not an outcome-based difficulty
label. No geometric capability is added to the public generator.

## Design

Cross k = 2, 4, sigma = 0.05, 0.15, 0.30 and q = 0, 2, 8 independent uniform
nuisance features. Hold n = 400 and p = 2 fixed. Use 30 independently seeded
families within each k stratum (master seed 2026101501). There are 18 cells,
540 datasets and 60 independent families. The nine conditions within a family
are paired, not independent replications. Families across k are independent.

Call the public GeneratorConfig/generate API with eight nuisance coordinates and
shuffle=False. Reuse the seed across dispersion levels, take nuisance prefixes,
and apply a separately seeded common permutation. This preserves centers,
standardized Gaussian residuals and nuisance draws across conditions. Assert
these invariants. StandardScaler fits each dataset without labels. All methods
use the same standardized matrix. No raw-feature comparison is part of this study.

## Methods and selection

Fit candidate counts 2 through 8 inclusive for K-means (k-means++, 10 starts,
300 iterations, tolerance 1e-4), Ward linkage, average linkage (Euclidean),
and Gaussian mixtures (full covariance, kmeans initialization, 5 starts,
300 iterations, tolerance 1e-3, reg_covar=1e-6). Fix seeds by family, method and
candidate, shared across conditions. Limit numerical libraries to one thread.
No parameter is tuned with generating labels. Computational budgets are explicit
but are not equal-cost budgets, so no efficiency superiority claim is planned.

Compute exact Euclidean silhouette, Calinski-Harabasz (CH), Davies-Bouldin (DB),
adjusted Rand index (ARI) and adjusted mutual information (AMI, arithmetic
normalization) for each partition. Maximize silhouette and CH, minimize DB,
breaking exact ties toward smaller candidate counts. ECVI never select candidates.
Record convergence warnings and failures. Nonconverged fits remain inspectable
but are excluded from selection. If any candidate is invalid, mark the entire
selection unavailable instead of silently using a reduced candidate set.

## Endpoints and reporting

Primary descriptive endpoints: mean known-k ARI/AMI per cell and method, correct
selected-k fraction, mean selected ARI/AMI, and pairwise disagreement in selected
k between ICVI. Report SD and MCSE across 30 families for continuous endpoints.
Failures retain their place in the 30-family denominator for correct-k recovery.
Report the number of valid partitions next to continuous summaries. No hypothesis
tests or simultaneous-coverage claims. Equal-cell summaries describe this fixed
grid only. Save all fit labels, scores, selection decisions, dataset hashes,
configuration, environment and source revision. Verify metrics from saved labels.

## Figures

Use replicate 0, k=4 and q=2 at all three dispersions for the data gallery,
selected before observing performance. Plot signal and nuisance projections with
generating labels, with common limits. Show known-k recovery by dispersion and q
for both k strata, including MCSE. A compact table summarizes the ICVI selection
task over the fixed grid. Full cellwise outputs remain in the repository.

## Commands

From the repository root with the research dependencies installed:

```bash
python research/method_comparison.py --output research/results/method-comparison-v1
python research/verify_method_comparison.py research/results/method-comparison-v1
python paper/method_comparison_figures.py
```

The runner refuses an existing output directory. A smoke run uses --replicates 2
and a separate output directory. It checks execution only and is not part of the
reported study. The registered 30-family design is unchanged by smoke outcomes.
