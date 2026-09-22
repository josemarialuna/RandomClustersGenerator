# Independent validation and robustness protocol

Frozen before running the validation datasets; the 20-replicate pilot informed
these choices. This is a prospective internal protocol, not a preregistration.
The software and estimators are those in PROTOCOL.md. No pilot observations are
pooled into the validation estimates. No optional stopping is permitted.

## Purpose and estimands

The software-paper case study asks whether a pipeline can distinguish recovery
with known k from internal-index selection of k under irrelevant features.
The primary validation uses 200 independent families with a new master seed,
four clusters, two signal features, 100 observations per cluster, sigma=0.05,
and q in {0,2}. Both matched-moment noise laws and preprocessing modes are used.
The primary estimand is the paired difference in probability of selecting k=4
by silhouette between normal and uniform noise after standardization at q=2.
For each family, subtract the two binary success indicators. Report the mean,
sample-SD/sqrt(R) Monte Carlo standard error, and a pointwise 95% t interval.
Also report each success proportion with a Wilson interval. The maximum MCSE
of an individual success proportion is 0.0354 at R=200. The paired difference
has a worst-case MCSE of approximately 0.071; its precision is not assumed equal
to that of either marginal proportion. This precision target motivates R=200.

Secondary estimands: paired normal-minus-uniform known-k K-means ARI, and
selected-k ARI minus known-k ARI, under each preprocessing mode. Selection loss
is signed: a selected partition can outperform a local known-k solution.
Report silhouette, Calinski--Harabasz and Davies--Bouldin selections, selected-k
frequencies and boundary selection. The primary direction was suggested by the
pilot, but estimates and intervals are reported regardless of direction.
No p-values, null-hypothesis acceptance, or family-wise claims are planned.

## Robustness scenarios

Each uses 50 independent families, sigma in {0.05,0.15,0.30}, q in {0,2,8,32},
both noise laws and raw/standardized preprocessing. Independent master seeds
are assigned to each scenario. They assess transport of the illustrative result,
not separate confirmatory hypotheses or population-representative performance.

| Configuration | k | Signal dimensions | Samples/group | Families | Candidate k |
| --- | --- | --- | --- | --- | --- |
| validation-primary.json | 4 | 2 | 100 | 200 | 2..8 |
| validation-small.json | 4 | 2 | 50 | 50 | 2..8 |
| validation-dimensions.json | 4 | 4 | 100 | 50 | 2..8 |
| validation-eight.json | 8 | 3 | 50 | 50 | 2..12 |

The last scenario extends the search above the generating k to avoid putting
truth at the upper boundary. Centers are distinct hypercube vertices. In the
four-dimensional scenario a coordinate can be constant across centers: report
the varying-coordinate count and do not call every supplied signal coordinate
informative. These scenarios do not isolate every factor: in the eight-group
scenario k and dimensionality change together at fixed total n=400.

All experiments remain balanced spherical mixtures; the eight-group full cube
and four-dimensional partial cube do not validate nonconvex/anisotropic claims.
Known-k Ward is an algorithm sensitivity check. We do not infer algorithm ranks
on real data. A software-capability comparison to make_blobs is descriptive;
no comparative runtime or superiority claims will be made without experiments.

## Execution and audit

Commit this protocol and all four JSON files before execution. Run each into a
new results directory using --protocol research/VALIDATION_PROTOCOL.md. Archive
raw outputs, full configuration, commit, environment, actual thread counts,
failures/warnings, checksums, gallery and derived figures. Do not retry failed
fits until a cause and amendment are recorded. Dataset/label hashes and paired
streams can be independently regenerated. Study summaries must not combine
distinct scenarios as if they were exchangeable replicates. CI checks archived
hashes; a separate source-based audit regenerates dataset fingerprints.

The manuscript separates exploratory pilot evidence, independent validation,
and robustness checks. It is a research-software case study, not a new clustering
method. Negative or inconsistent robustness findings remain in the paper.

Pre-execution correction: PowerShell serialized the singleton sigma list as a scalar. The first launch failed during configuration parsing, before any dataset or fit. Restore the JSON array; no design values or stopping rule changed.
