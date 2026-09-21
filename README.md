# Random Clusters Generator

[![CI](https://github.com/josemarialuna/RandomClustersGenerator/actions/workflows/ci.yml/badge.svg)](https://github.com/josemarialuna/RandomClustersGenerator/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

**Create reproducible synthetic datasets for clustering experiments.** Choose the
number of clusters, observations, signal features, and noise features. Get a CSV
with known cluster labels and a JSON file describing how it was generated.

**[Guía en español](README.es.md)** · [Example input](examples/experiments.csv) ·
[Example output](examples/tiny.csv) · [Experiment metadata](examples/tiny.json)

```text
INPUT                          GENERATION                    OUTPUT
4 clusters                     Pick 4 distinct centers       dataset.csv
100 samples PER cluster   →    Sample Gaussian points   →    400 rows × 5 columns
2 signal + 2 noise features     Add uniform noise             s0,s1,d0,d1,cluster
std=0.05, seed=42               Shuffle rows                  dataset.json
                                                             parameters + centers + seed
```

Use it to test cluster recovery, feature selection, or sensitivity to irrelevant
features and overlap. This is a controlled synthetic model; it does not reproduce
every property of real-world datasets.

## 1. Install

Requires **Python 3.10 or newer**. Works on Windows, macOS, and Linux.
Install from this repository; no PyPI publication is assumed.

```bash
git clone https://github.com/josemarialuna/RandomClustersGenerator.git
cd RandomClustersGenerator
python -m venv .venv
```

Activate the environment:

| Terminal | Command |
| --- | --- |
| Windows PowerShell | `.venv\Scripts\Activate.ps1` |
| Windows Command Prompt | `.venv\Scripts\activate.bat` |
| macOS / Linux | `source .venv/bin/activate` |

Then install:

```bash
python -m pip install .
random-clusters --help
```

If your system uses `python3`, use it instead of `python` when creating the
environment. If PowerShell blocks activation, use
`.venv\Scripts\python.exe -m pip install .` and run commands as
`.venv\Scripts\python.exe -m random_clusters ...`; activation is optional.

## 2. Generate your first dataset

Run this single-line command:

```bash
random-clusters generate --clusters 4 --samples 100 --features 2 --noise 2 --std 0.05 --seed 42 --output data/demo.csv
```

It creates the output directory if needed and writes:

```text
data/
├── demo.csv     # 400 observations, 4 input features, 1 ground-truth label
└── demo.json    # parameters, seed, centers, versions, and CSV SHA-256
```

The terminal reports `400 rows x 5 columns; seed=42` and the two paths.
Existing CSV **or** JSON files are protected: use a new output name, or explicitly
add `--overwrite` to replace them.

### What goes in?

| Option | Meaning | Default |
| --- | --- | --- |
| `--clusters` | Number of groups; positive and at most `2**features` | `4` |
| `--samples` | Observations **per cluster**, not total | `100` |
| `--features` | Number of signal coordinates; positive | `2` |
| `--noise` | Number of independent uniform noise columns; can be zero | `2` |
| `--std` | Standard deviation within each cluster; finite and nonnegative | `0.05` |
| `--seed` | Nonnegative integer controlling all randomness | Auto-generated and recorded |
| `--output` | CSV destination; JSON uses the same basename | `data/dataset.csv` |
| `--ordered` | Keep observations grouped by cluster | Rows are shuffled |
| `--no-labels` | Omit the `cluster` column | Labels are included |

**Rows = clusters × samples. Columns = features + noise + 1 label.**
With `--no-labels`, subtract one column. All data is generated in memory.

### What comes out?

| Column | Content | Use |
| --- | --- | --- |
| `s0`, `s1`, … | Gaussian signal coordinates | Input features |
| `d0`, `d1`, … | Independent uniform values in `[0, 1)` | Irrelevant input features |
| `cluster` | Integer ground truth, from `0` to `clusters - 1` | Evaluation only |

**Do not include `cluster` in the input to a clustering algorithm.**

For an easily inspected example, remove random spread and noise:

```bash
random-clusters generate --clusters 2 --samples 2 --features 1 --noise 0 --std 0 --seed 42 --ordered --output data/tiny.csv
```

This writes:

```csv
s0,cluster
0.75,0
0.75,0
0.25,1
0.25,1
```

Each cluster has two identical observations at its center. See the committed
[actual CSV](examples/tiny.csv) and [matching JSON](examples/tiny.json).
Zero spread is useful for inspection; use a positive `--std` for normal experiments.

## 3. Load the result

```python
import pandas as pd

data = pd.read_csv("data/demo.csv")
X = data.drop(columns="cluster")  # 400 × 4 input matrix
y_true = data["cluster"]  # 400 ground-truth labels

print(data.head())
print(X.shape, y_true.value_counts().sort_index())
# Fit your clustering algorithm on X; compare its labels with y_true.
```

The CSV uses commas, a header, and no pandas index. Labels follow the center order
in the JSON: `centers[0]` is the mean vector for cluster `0`.

## 4. Run several experiments from one CSV

Start with [examples/experiments.csv](examples/experiments.csv):

```csv
clusters,samples,features,noise,std,seed
4,100,2,2,0.05,42
4,100,2,8,0.05,42
6,100,3,2,0.10,123
```

```bash
random-clusters batch examples/experiments.csv --output data/experiments
```

| Input row | Generated files | CSV size, including labels |
| --- | --- | --- |
| 1 | `dataset_001.csv` + `dataset_001.json` | 400 × 5 |
| 2 | `dataset_002.csv` + `dataset_002.json` | 400 × 11 |
| 3 | `dataset_003.csv` + `dataset_003.json` | 600 × 6 |

Files go inside `data/experiments/`. Every row must provide all six fields,
including a seed. Commas and semicolons are accepted. All rows and destination
collisions are checked before generation begins. Invalid rows report their line
number. Filesystem failures during writing can still leave a partial batch.

Repeat a configuration with different seeds for independent replicates. Reusing
the same seed reproduces an experiment, not an independent replicate. `--ordered`,
`--no-labels`, and `--overwrite` also work with `batch`.

## 5. Understand the model

For `k` clusters, `s` signal features, and standard deviation `σ`:

1. Sample `k` **distinct** binary vectors of length `s`, uniformly without
   replacement. Each vector defines one center.
2. Map bit `0` to mean `0.25` and bit `1` to mean `0.75`.
3. Draw the same number of observations from each Gaussian cluster:
   **X | cluster=c ~ Normal(center[c], σ² I)**.
4. Add independent noise coordinates from **Uniform(0, 1)**.
5. Attach ground truth and shuffle observations unless `--ordered` is given.

For two signal features, the four possible centers are:

```text
         s1
  0.75    ● (0.25, 0.75)       ● (0.75, 0.75)

  0.25    ● (0.25, 0.25)       ● (0.75, 0.25)
         0.25                 0.75             s0
```

Increasing `std` increases spread and usually makes recovery harder. Centers are
distinct, but that does **not** guarantee well-separated samples. Gaussian values
are not clipped and can fall outside `[0, 1]`.

All clusters are balanced, spherical, and share the same variance. There are no
outliers, categorical features, correlated within-cluster coordinates, or
arbitrary center locations. A chosen signal coordinate can have the same mean in
all selected clusters, particularly when `k` is small. The JSON field
`varying_signal_features` identifies coordinates whose means actually differ.
With one cluster, that list is empty.

## 6. Reproduce and record an experiment

Every generated CSV has a JSON sidecar containing:

- Complete parameters, including the actual seed, label and shuffle settings.
- Actual center coordinates in label order and the model identifier.
- Python, NumPy, pandas, and generator versions; random generator (`PCG64`).
- Row count, column names, and SHA-256 of the CSV for integrity checks.

To regenerate from that metadata:

```python
import json
from pathlib import Path
from random_clusters import GeneratorConfig, generate
from random_clusters.io import save_dataset

metadata = json.loads(Path("data/demo.json").read_text(encoding="utf-8"))
result = generate(GeneratorConfig(**metadata["parameters"]))
save_dataset(result, Path("data/replayed.csv"))
```

For exact replay, keep the same code revision and dependency versions. A seed alone
is not a cross-version guarantee. Archive the CSV and JSON alongside your analysis,
record the Git commit (`git rev-parse HEAD`), and save installed dependencies with
`python -m pip freeze > environment.txt`.

## Python API

No files are written unless you explicitly save the result:

```python
from random_clusters import GeneratorConfig, generate

result = generate(GeneratorConfig(clusters=4, samples=100, features=2, noise=2, std=0.05, seed=42))
X = result.data.drop(columns="cluster")
y_true = result.data["cluster"]
centers = result.centers
```

## Add noise to an existing dataset

```bash
random-clusters add-noise data/demo.csv --count 3 --seed 42 --output data/demo_extra.csv
```

This adds **three new columns**, preserves existing values and row order, and
writes a separate CSV and JSON. Existing `dN` columns are never replaced. For
example, if `d0` and `d1` exist, new columns are `d2`, `d3`, and `d4`.

Uniform noise is the default. For the normal noise used by the old utility:

```bash
random-clusters add-noise data/demo.csv --count 3 --distribution normal --mean 1 --std 0.05 --seed 42 --output data/demo_normal.csv
```

The input must be a comma-separated CSV with a header. pandas infers input types,
so this command targets numeric research tables; it does not preserve original
CSV formatting or textual identifiers such as leading-zero codes. Metadata records
the source file hash and noise parameters. Input and output must be different files.

## Migrating from the original scripts

| Previous workflow | Current workflow |
| --- | --- |
| Edit constants in `src/main_generator.py` | `random-clusters generate ...` |
| Run `main_generator_parameters.py` | `random-clusters batch experiments.csv` |
| Generate a large hard-coded configuration grid | Edit the small `examples/experiments.csv` template |
| Run `add_dummy_columns.py` over a directory | Explicit `add-noise INPUT --count N --output OUTPUT` |

The duplicated scripts and old configuration grids were removed. For old CSV
configurations, rename `clusters_num → clusters`, `significant_num → features`,
`dummy_num → noise`, `standard_dev → std`, and add `samples` and `seed` columns.
Correct rows where `clusters > 2**features` before running them.

**Scientific behavior changed:** centers are now selected from the entire binary
hypercube instead of only the first `k` binary integers. Invalid configurations
are rejected, rows are shuffled by default, and randomness uses one seeded PCG64
generator. New runs are not numerically equivalent to historical runs. Existing
datasets are not rewritten automatically. Use the original code revision when
reproducing historical results.

## Troubleshooting

| Message / symptom | What to do |
| --- | --- |
| `random-clusters` not found | Activate the environment, or use `python -m random_clusters` |
| `clusters must be <= 2**features` | Increase features or reduce clusters; six clusters need at least three features |
| `output already exists` | Choose a new path, or add `--overwrite` intentionally |
| Unexpected total row count | `--samples` means observations per cluster |
| Batch row error | Check all six fields, integer counts, finite std, and seed |

## Development and contributions

An exploratory paired-noise study is available in [research/](research/README.md),
with its protocol, related-work audit, optional dependencies and reproducible runner.
It does not alter the production generator or establish a publication claim.

```bash
python -m pip install -e ".[dev]"
python -m pytest
python -m ruff check .
python -m ruff format --check .
python -m build
```

`src/random_clusters/core.py` owns the model, `io.py` handles configuration/output,
and `cli.py` handles commands. Tests cover reproducibility, model properties,
validation, file protection, and CLI workflows. CI runs on Windows, macOS, and
Linux with Python 3.10, 3.12, and 3.13.

For bugs, include your command, versions, and a minimal configuration. For model
changes, explain their effect on scientific interpretation and reproducibility.
Do not commit generated research datasets; `data/` is ignored.

## License and attribution

[MIT License](LICENSE). Created by José María Luna-Romera.
When using the generator in research, reference this repository and the exact
commit/version used, and report your parameters and seeds. No publication or DOI
is implied.
