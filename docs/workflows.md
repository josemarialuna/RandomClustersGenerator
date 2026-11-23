# Three reproducible tasks

Use a fresh output directory for every run. Install with
`python -m pip install ".[research]"` from the recorded repository checkout.

## 1. Generate and inspect

Follow [the API example](paired-api.md#a-complete-example). Inspect the 150-row
feature table and the JSON parameters. Plot `noisy.X.s0` against `noisy.X.s1`
with `noisy.y` used only as plotting colors. A feature-only table has no labels
or row IDs. When reading the exported CSV, exclude `cluster` and `row_id`.

## 2. Run a paired experiment

```bash
python -m random_clusters.experiment examples/paired/quickstart.json data/quickstart
python -m random_clusters.experiment data/quickstart --audit --deep
```

The quickstart generates two 200-row datasets with the same two signal
coordinates and different nuisance counts. It evaluates K-means at 3, 4 and 5
groups after standardization. Expect six fit records and six selection records.
The labels are reserved for ARI/AMI, while Silhouette/CH/DB select without them.

```
data/quickstart/
  config.json       # complete resolved experimental input
  datasets/         # two CSV tables and two replay JSON files
  partitions/       # candidate labels saved as .npy
  fits.json         # scores, seeds, warnings and failures per candidate
  selections.json   # decisions per internal criterion
  manifest.json     # only written on completion, with hashes and versions
```

For each scenario in `balanced`, `unequal`, `anisotropic`, substitute its JSON
configuration to run the full [protocol](../research/PAIRED_WORKFLOW_PROTOCOL.md).
The configuration is authoritative. The runner does not silently reduce the
candidate grid or discard failed fits. It does not resume partial runs.

## 3. Recompute a figure

After running and deep-auditing the three scenarios into
`data/paired-workflow-v1/{balanced,unequal,anisotropic}`, run:

```bash
python research/summarize_paired.py data/paired-workflow-v1 data/paired-summary-v1
```

This reads saved scores and generates cellwise tables, paired differences and
two figures. It checks archive hashes first. For independent metric
recalculation, run the deep auditor on each scenario before summarizing.
The deep auditor does not rerun clustering. Refit with the original config and
recorded environment into a new directory to assess optimizer replay.

PDF bytes may differ with font/rendering versions. Use numerical tables and
partition checks to distinguish a rendering difference from a scientific one.
The gallery is replicate zero by design, not the most attractive outcome.

## Comparison with general-purpose tools

`research/paired_baseline.py` implements the same generation and replay task in
NumPy without importing the package's family sampler. It intentionally uses
separate streams, rather than an incorrect naive reseeding baseline.

```bash
python research/paired_operational.py data/operational-new
```

This runs generation, export and numerical replay for both implementations.
`trials.csv` contains every time and Python-traced allocation measurement.
Memory tracing is measured separately from timing. This is not total process
memory, a clustering scalability test or an independent user study.

## Migration

Existing `GeneratorConfig` and CLI behavior is retained. New families are
opt-in and use a different stream convention. Translate old `samples` into a
vector of group sizes and `std` into `Condition.scale` only when the base
covariances are identity matrices. This translation matches model parameters,
not historical numerical realizations. Historical results require historical
code, configurations and environments.
