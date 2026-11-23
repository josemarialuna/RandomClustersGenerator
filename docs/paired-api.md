# Public paired experiment API

Install with `python -m pip install ".[research]"` for clustering. Generation
and bundle replay need only the core dependencies. This API supplements the
unchanged legacy `GeneratorConfig`, `generate`, `batch` and `add-noise` commands.

## A complete example

```python
from pathlib import Path
from random_clusters import FamilyConfig, PairedFamily, Condition
from random_clusters.bundles import save_paired, verify_paired

config = FamilyConfig(
    sizes=(50, 100), centers=((0., 0.), (1., 1.)), seed=42,
    covariances=(((1., 0.), (0., 1.)), ((2., .5), (.5, 1.))),
)
family = PairedFamily(config)
clean = family.dataset(Condition(scale=.1, noise=0))
noisy = family.dataset(Condition(scale=.1, noise=8))
assert clean.X.equals(noisy.X[clean.X.columns])
save_paired(noisy, Path("data/paired.csv"))
print(verify_paired(Path("data/paired.csv"), regenerate=True))
```

The input specifies 150 rows in two groups, two coordinates and eight nuisance
variables. `noisy.X` contains ten feature columns. `noisy.y` and `noisy.row_ids`
are separate arrays. Export writes 12 CSV columns (features plus `row_id` and
`cluster`) and a JSON replay sidecar. Never fit the last two columns.

## Reference

| Object/function | Inputs and defaults | Returns / errors |
|---|---|---|
| `FamilyConfig` | Required `sizes` (k positive integers) and `centers` (k by p). Optional `covariances` (k by p by p, identity by default), `seed=42`, `replicate=0`, `shuffle=True` | Immutable normalized configuration. Raises `ValueError` for invalid dimensions, nonfinite values, nonpositive sizes or non-positive-definite covariance |
| `FamilyConfig.hypercube` | `clusters=4`, `samples=100` per group, `features=2`, `seed=42`, `replicate=0` | Config with distinct centers from {0.25,0.75}^p and identity covariance. Requires k <= 2^p |
| `Condition` | `scale=.1` >= 0, `noise=0` integer, `distribution="uniform"` or `"normal"` | Immutable perturbation, `ValueError` on invalid settings |
| `PairedFamily(config)` | Valid family configuration | Cached residuals, labels and permutation |
| `family.dataset(condition)` | A `Condition`, default `Condition()` | Independent `PairedDataset` with `X`, `y`, `row_ids`, configuration, condition and metadata |
| `family.fit_seed(method, candidate)` | Nonnegative integer method ID, positive integer count | Stable 32-bit fitting seed |
| `save_paired(dataset, path, overwrite=False)` | Dataset and `.csv` path | CSV and JSON paths. Existing outputs raise `FileExistsError` |
| `replay_paired(metadata)` | Parsed JSON sidecar | Regenerated `PairedDataset`; rejects unsupported model identifiers |
| `verify_paired(path, regenerate=False)` | Saved CSV | Integrity status, optionally numerical replay. Raises `ValueError` on mismatch |
| `experiment.run(spec, output)` | Full JSON design, new directory | Manifest after successful completion. Requires research extra |
| `experiment.audit(output, deep=False)` | Completed archive | Hash verification, or regeneration and recalculation from partitions |

Covariance matrices may be spherical, diagonal or full. A condition with scale
a uses covariance a² Sigma_c. Zero scale produces deterministic centers but
does not make arbitrary validity indices meaningful. The base covariance must
still be positive definite. Equal centers are allowed, including components
distinguished by covariance alone. Labels identify mixture components, which
need not correspond to separated geometric clusters.

## Pairing contract

For fixed configuration and replicate:

* Changing nuisance count preserves signal, labels, IDs and existing nuisance
  columns exactly. Columns have independent streams.
* Changing nuisance law preserves signal, labels and IDs. It does not preserve
  the noise realizations. Uniform and normal laws use independent streams.
* Changing scale preserves standard Gaussian residuals, noise and row order.
* Reordering conditions or adding new conditions does not alter old datasets.
* Changing component sizes or signal dimension creates a new family. No
  observation-level pairing is promised across those changes.

PCG64 streams use SeedSequence with root seed and spawn keys
`(replicate, component, index)`: 0 centers, 1 residuals, 2 permutation,
3 uniform-noise columns, 4 normal-noise columns. Fitting uses
`(replicate, 5, method, candidate)`. It is independent of condition order.
Sharing fitting seeds controls initialization randomness but does not guarantee
identical initial centroids after changing data.

## Model and informative coordinates

Draw independent standard normal residuals z_i. With lower Cholesky factor
L_c of Sigma_c, set x_i = mu_c + scale L_c z_i. Append independent U(0,1)
or N(0.5,1/12) nuisance columns, then apply the shared row permutation.
Values are not clipped. Population moments are matched across noise laws,
finite-sample moments are not. The metadata separately report mean-varying
and covariance-varying coordinates. Constant means do not imply irrelevance
when component covariance matrices differ.

## Versions and reproducibility

The model identifier is `paired-gaussian-v1`. It is distinct from the legacy
core and historical research stream conventions. Equal seeds across these
interfaces do not imply equal datasets. Keep the recorded revision and exact
dependencies. Cross-platform bitwise replay of floating-point linear algebra
is not promised. CSV hashes detect changes in files, not scientific errors.
The deep experiment auditor recalculates metrics and decisions from archived
partitions. It does not refit models or independently validate the model.

All generation is in memory. Silhouette and hierarchical methods can need
quadratic resources. Full grids should start with small pilot configurations.
Filesystem failure can leave partial exports. A complete experiment has a
manifest, and the runner refuses to overwrite an existing directory.
