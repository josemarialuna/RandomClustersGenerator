# Revision study: four complementary checks

Prospective internal protocol, specified after the previous validation and
editorial review. Earlier results are preserved and are not retrospectively
replaced. No optional stopping or filtering by outcome. New code lives under
research/extension, leaving the frozen production/research implementation intact.

## 1. Crossed candidate range and initialization budget

100 NEW primary-geometry families, master seed 2026092301; k=4, p=2,
n=400, sigma=.05, q=2, paired uniform/normal noise, standardization.
For every dataset fit candidates 2..16 at n_init=10 and 100. Select over
2..8 and 2..16 from these same fits, for silhouette, CH and DB. Thus range
expansion cannot change a shared fit. Retain every candidate label vector,
inertia, iteration count, scores, warnings and failure status.

Primary diagnostic endpoint: within-family difference-in-differences of
correct-count indicators: (wide100 - narrow100) - (wide10 - narrow10), separately
for each noise law, silhouette first. Report mean, MCSE, pointwise t interval
and a conservative Hoeffding interval using support [-2,2]. These 100 families
are independent of earlier seeds; they remain conditional on the primary model.
Secondary: signed selected-minus-known ARI and selected-count frequencies.

Mechanism diagnostics for every candidate: per-feature between/total sum of
squares, normalized conditional mutual information I(pred; noise-half | truth),
fraction of within-true-group SSE explained separately in signal and noise,
and label contingency tables. Noise-half is each irrelevant coordinate split
at its population median .5 before standardization. These are descriptive
associations, not causal attribution or proof of an optimal partition.
Archive labels and per-feature diagnostics to permit direct inspection.

## 2. Factorial generalization

Fully cross k={3,4}, p={3,6}, total n={240,480}, minimum pairwise Mahalanobis
center separation={3,8}, geometry={cube,random,anisotropic}: 48 cells,
30 independent families per cell, seed 2026092302. Evaluate q=0 and paired
q=2 uniform/normal noise, standardization, K-means candidates2..8, ten starts.
Total 1,440 independent families, 4,320 datasets and 30,240 fits.
Each cell is independently seeded; its noise conditions are paired. The total
sample count is held fixed when k changes; samples/group necessarily changes.

Cube uses random distinct vertices. Random uses Gaussian-distributed centers.
Anisotropic uses random centers and a shared rotated covariance with eigenvalue
ratio9. All covariance traces are p*.01. Normalize centers using their minimum
Mahalanobis distance to achieve the requested separation, with covariance fixed
when separation changes. This controls the nearest pair's separation, not all
mixture overlap. Store centers, covariance, pairwise-distance diagnostics,
observed varying-coordinate counts and fingerprints. Non-cube constructions are
experimental extensions, NOT new capabilities of the public generation API.

Report every cell, no pooling of datasets as independent. Estimate uniform vs
normal correct-count differences within families; report factorial main contrasts
as equal-weight averages over the remaining design cells, with independent-cell
variance propagation. These are averages over this fixed factorial design, not
population-wide rankings. Show conditional cells to expose interactions. No
claims about unequal group sizes, nonconvex clusters or correlated noise.

## 3. Operational comparison

Compare core generate with an explicit make_blobs-based reference constructing
the SAME distributional model: balanced groups, sampled cube centers, spherical
Gaussian residuals, uniform nuisance columns, labels and shuffled pandas table.
The numerical realizations need not match because RNG implementations differ.
Both return identical schemas and satisfy documented invariants. The reference
includes center generation and data-frame construction. Public API validation
and reference checks are included. Neither timed method exports provenance.

Cross n={1000,10000,100000}, p={2,8}, q={2,16}, k4, sigma.05;
5 repetitions per cell, seed2026092303. Randomize method order within each
repetition, run sequentially with one numerical thread. Warm each method once
at n1000 outside the measurements. Measure generation wall and CPU time and
common CSV export time/bytes; CSV uses the same pandas writer for both.
Measure tracemalloc peak tracked allocation in a SEPARATE generation call;
it is not peak RSS and must be labelled accordingly. Save all per-trial records,
environment and failures. Ratios are descriptive on this PC, not universal
speed claims. No user study, developer-time savings or adoption is asserted.
Additional automated workflow checks cover deterministic replay, preservation
when adding noise, output schema/balance and nested paired research columns.

## 4. Inference and coverage

Keep the original t/Wilson results. Add a conservative finite-sample alternative
for paired binary differences D in {-1,0,1}: construct two-sided Clopper-Pearson
intervals at 97.5% individually for counts D=+1 and D=-1; difference interval
[L_plus-U_minus,U_plus-L_minus] has at least95% coverage by the union bound.
Counts are dependent; independence between these counts is NOT assumed.
For general bounded means provide Hoeffding95% intervals, clipped to known
support. For ARI use conservative [-1,1], differences [-2,2].

Evaluate EXACT multinomial coverage and expected width for the paired-difference
t interval, CP/Bonferroni difference interval and Hoeffding interval at
R={20,50,200}. Enumerate all counts for p_plus,p_minus in
{0,.005,.025,.1,.3,.5,.9,.975,.995,1} with sum<=1. No Monte Carlo coverage error.
Report all grid points, including boundaries. A grid is not a universal proof;
the conservative methods' guarantee comes from their construction under iid
bounded families. Apply the alternatives to existing primary paired outcomes
without redefining the original analysis, and to the new interaction outcomes.

## Execution and audit

Commit this protocol and code before scientific execution. Unit tests may use
tiny synthetic cases and are not scientific evidence. Fixed seeds, stable keys,
single-thread numerical libraries. Long modeling sections may run with two
worker processes; timing comparison runs only when other experiments finish.
Archive source/protocol hashes, exact config, environment, raw observations,
labels, aggregate tables, timing and statuses in a fresh output directory.
Fail explicitly on missing/failed cells; do not silently drop them. Any amendment
must be recorded before rerunning affected fits. Stop only at planned counts.
