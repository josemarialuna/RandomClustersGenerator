# Paired noise pilot: protocol v1

Status: exploratory pilot, specified before inspecting its results. This is not a
registered preregistration or a completed paper. Date: 2026-09-21.
The executable design is [pilot.json](pilot.json). Changes after the initial run
must be recorded as amendments, not silently substituted for the original design.

## Aim and contribution under investigation

Assess whether a reusable, paired experimental workflow can help distinguish
changes in clustering recovery from changes in internal validation scores when
irrelevant dimensions are added. This is a software/benchmark contribution under
investigation, not a claim of a new Gaussian generator or a new clustering method.

McCrory and Thomas (2024) already investigate irrelevant Gaussian/uniform features,
K-means, scaling, and internal/external metrics. Merely repeating those ingredients
is not novel. This pilot emphasizes distribution comparisons with matched
population variance, invariant signal observations across noise levels, and errors
in selecting k. These are candidate differentiators, not verified priority claims.
See [RELATED_WORK.md](RELATED_WORK.md).

We use the ADEMP planning structure of Morris, White and Crowther (2019): aims,
data-generating mechanisms, estimands, methods, and performance measures.

## Research questions

- RQ1: How does adding irrelevant dimensions change ARI relative to the same
  observations without added noise, within each fixed dispersion and method?
- RQ2: Does the effect differ between uniform and normal noise after matching
  their population mean and variance, with/without standardization?
- RQ3: How often do Silhouette, Calinski–Harabasz, and Davies–Bouldin select the
  generating k, and how much ARI is lost relative to the best candidate partition?
- Diagnostic: how do internal scores change for the *unchanged ground-truth
  partition*? This separates geometric score changes from relabeling by a method.

All directions and all outcomes will be reported; no required positive result.

## Data-generating mechanism

The production `generate()` API is unchanged. The research module reuses it to
sample centers, then constructs paired observations using independent named RNG
streams. This experimental design has its own version and is not byte-equivalent
to the production generator's original single stream.

| Factor | Pilot levels |
| --- | --- |
| Generating groups | 4 |
| Signal dimensions | 2 (all four corners, hence both coordinates informative) |
| Observations per group | 100; total n=400 |
| Within-group standard deviation | 0.05, 0.15, 0.30 |
| Added noise dimensions q | 0, 2, 8, 32 |
| Noise distribution | Uniform(0,1); Normal(0.5, 1/12), second parameter is variance |
| Preprocessing | Raw; featurewise StandardScaler |
| Independent dataset families | 20 |

Centers are corners of {0.25, 0.75}². Thus minimum center distance is 0.5 for
every replicate. Conditional on group c, signal is Normal(center[c], σ² I).
The two noise distributions both have population mean 0.5 and variance 1/12.
Realized sample variances are recorded and are not forced to be identical.
At q=0 there is one baseline (distribution `none`), not two independent copies.

Counts: 20 × 3 × (1 + 3 × 2) = **420 datasets**, each analyzed with two
preprocessing choices. There are seven K-means candidate fits and one Ward fit
per analysis: **6,720 fits**. Ground-truth diagnostics are not algorithm fits.

### Pairing and randomness

A family is identified by master seed, replicate, k, signal dimensions, and n per
group. Separate SeedSequence/PCG64 streams control centers, standard-normal signal
residuals, row permutation, each noise column, and each K-means candidate seed.

Within a family:

- Same centers and labels for every σ and q.
- Same standard-normal signal residuals across σ; same signal values across q.
- Same row order across q and distributions.
- Noise column j is independent of the number of requested columns. Increasing q
  preserves every existing noise column exactly.
- Uniform/normal noise use shared quantiles, making a paired distribution contrast.
- K-means seeds are paired across q, distribution, σ, and preprocessing, for each
  candidate k. `n_init=10` is part of the method, not ten independent datasets.

Independent families, not individual rows or fits, are the replication units.
This is a conditional study of one square geometry; changing dimensions or sample
size is explicitly outside the first pilot.

### Separation is not the same as multiclass overlap

Record δ_min/σ. Also record Φ(-δ_min/(2σ)), the optimal equal-prior **two-class**
error for a closest pair of these isotropic Gaussians. This is a diagnostic,
not the four-class Bayes error or an overlap guarantee. At σ=0.05, 0.15, 0.30,
δ_min/σ is 10, 3.333..., 1.667..., respectively.

For two independent observations, q matched-variance noise coordinates add q/6
to expected squared Euclidean distance, irrespective of the two noise shapes.
Within a signal cluster, the expected squared signal distance is 2sσ². Between
centers a and b it is ||a-b||² + 2sσ². Matching these expectations does not make
the full distance distributions or clustering outcomes equal.

## Methods and estimands

### Track A: generating k supplied (oracle-k setting)

- K-means: k=4, k-means++ initialization, 10 starts, Lloyd algorithm,
  max_iter=300, tol=1e-4.
- Agglomerative clustering: k=4, Ward linkage, Euclidean distance.

This track measures recovery given the generating k. It does not estimate k.
Use the same fitted K-means k=4 partition as in Track B to avoid redundant fits.

### Track B: k selected without labels

Fit K-means with candidate k=2,...,8. Select independently by maximum Silhouette,
maximum Calinski–Harabasz, and minimum Davies–Bouldin. Ties choose smaller k.
No ARI/NMI or generating labels enter fitting, scaling, or selection.

ARI-best among candidates is an explicitly labeled, unattainable diagnostic
reference. Selection regret = max(candidate ARI) - selected ARI. Generating-k
recovery and ARI regret are distinct, especially when components overlap.

### Endpoints

- Primary: per-family paired difference ARI(q) - ARI(0), by σ, method, scaling,
  and noise shape. Include all recorded failures rather than silently dropping them.
- Secondary: ARI(normal) - ARI(uniform) at matched q; selection correctness
  `selected_k == generating_k`; ARI regret; normalized mutual information.
- Diagnostic: internal scores of fitted and generating partitions; exact centers,
  empirical feature means/variances, data fingerprints, fit time, warnings/failures.

All internal scores are computed on the same feature matrix used for fitting,
with full-data Euclidean Silhouette (no subsampling at n=400). StandardScaler is
fit on each dataset without labels; this is in-sample clustering evaluation,
not a held-out prediction experiment. No tuning on evaluation ARI is permitted.

Use one BLAS/OpenMP thread for consistent resource use. Fit timing includes the
estimator fit/predict only, excluding scaling, metrics, generation, and I/O. Timing
is descriptive and machine-specific; this pilot makes no speed superiority claim.

## Uncertainty, failure policy, and stopping

Summarize across the 20 independent families using mean, sample SD, and Monte Carlo
standard error SD/sqrt(R). Show approximate 95% t intervals for means and paired
differences; Wilson intervals for success proportions. These are pointwise,
exploratory intervals, not simultaneous or confirmatory significance tests.
With 20 families, estimates can be imprecise; a zero empirical MCSE does not
establish zero uncertainty. Do not treat nested noise levels as independent.

Capture failed fits and warnings explicitly. Invalid internal scores remain
missing. Selection requires all candidate fits to be valid; otherwise report a
failed selection. Produce expected/observed counts and failure tables before
interpreting results. Report both failure counts and the denominator of every
summary; incomplete contrasts are not imputed. A failed run does not count as a
scientific result. Unexpected programming errors abort with a traceback.

Run the fixed pilot once after software checks. Do not add replicas until an
interesting p-value appears. Any confirmatory study must use a new frozen protocol
and disjoint master seed, with repetition count justified from pilot variability
and desired Monte Carlo precision.

## Evidence package and next-stage decision

Archive config/protocol/source hashes, source commit and dirty state, environment,
dataset fingerprints, raw candidate/selection rows, summaries, figures, and the
report-generation code. Export a predetermined gallery (replicate 0 for all σ,
q=0 and q=max) rather than choosing visually attractive runs.

Proceed to a larger study only after checking: all pairing invariants; complete
result counts; no unexplained failures; settings spanning recoverable and hard
cases; and a defensible distinction from related work. These gates establish
feasibility, not originality or publishability.

Further work: additional geometries and dimensions with calibrated separation,
unequal sizes/covariances, more clustering families, baseline generator comparisons,
feature selection, external users, and an archived release. These are planned,
not implemented or experimentally validated by this pilot.

## References

- Morris, White & Crowther (2019), [Using simulation studies to evaluate statistical
  methods](https://doi.org/10.1002/sim.8086).
- Van Mechelen et al. (2023), [A white paper on good research practices in
  benchmarking: The case of cluster analysis](https://doi.org/10.1002/widm.1511).
- McCrory & Thomas (2024), [Cluster Metric Sensitivity to Irrelevant
  Features](https://arxiv.org/abs/2402.12008).
- Shand et al., [HAWKS: Evolving Challenging Benchmark Sets for Cluster
  Analysis](https://doi.org/10.1109/TEVC.2021.3137369).
