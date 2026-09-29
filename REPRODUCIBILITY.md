# Reproduce the software examples and research evidence

This guide distinguishes **checking saved files**, **regenerating datasets** and
**refitting models**. Passing a hash check verifies recorded bytes; it does not
independently validate a statistical conclusion or rerun every fitted model.
The manuscript and supplementary prose are authored and checkpointed in Overleaf.

## 1. Install a recorded version

```bash
git clone https://github.com/josemarialuna/RandomClustersGenerator.git
cd RandomClustersGenerator
git checkout v1.0.0
python -m venv .venv
```

Activate with `.venv\Scripts\Activate.ps1` in Windows PowerShell, or
`source .venv/bin/activate` on macOS/Linux. Install the research dependencies:

```bash
python -m pip install ".[research]"
```

The supported dependency ranges are in `pyproject.toml`. For the environment used
in the recorded studies, use **Python 3.12.4**, install
`research/environment-pilot.txt`, then install this checkout with
`python -m pip install --no-deps .`. Per-run manifests are authoritative for
versions, seeds and source hashes. Exact floating-point replay is not guaranteed
across numerical libraries or platforms.

## 2. Generate and inspect a small dataset

```bash
random-clusters generate --clusters 4 --samples 100 --features 2 --noise 2 --std 0.05 --seed 42 --output data/demo.csv
```

This writes `data/demo.csv` (400 rows; four input features and one label) and
`data/demo.json` (parameters, centers, resolved seed, versions and CSV checksum).
`samples` means observations **per group**. Remove `cluster` before fitting;
use it only for evaluation. See the [README](README.md) for a four-row worked
example, batch input, the Python API and metadata replay.

## 3. Check the archived evidence without fitting

Run these from the repository root. They require only the Python standard library:

```bash
python paper/verify_evidence.py
python research/verify_extension.py
python paper/review_evidence.py --check
```

The first verifies validation and sensitivity artifacts; the second verifies
extension source and artifact hashes; the third checks the supplementary review
analysis manifest. Keep full Git history: the scientific analyzers below compare
source bytes against frozen commits that a shallow clone might omit.

## 4. Regenerate datasets and derived tables, without refitting

With the research dependencies installed:

```bash
python paper/build_evidence.py
python paper/analyze_sensitivity.py
python paper/analyze_extension.py
python paper/review_evidence.py
python paper/softwarex_figures.py
```

These commands write the numerical artifacts under `paper/`; they do not edit
the manuscript. The validation builder regenerates 3,750 datasets and checks
fingerprints. The extension analyzer regenerates 4,520 datasets and audits
36,240 saved candidate partitions and 15,360 selection decisions. Figure 2 uses
replicate 0 from the primary protocol, fixed before inspecting fitted outcomes.
The figure manifest records its data and label fingerprints. PDF bytes can vary
with rendering-library versions; raw numerical fingerprints remain explicit.

## 5. Locate each study

| Study | Protocol / configuration | Saved results | Purpose |
| --- | --- | --- | --- |
| Pilot | `research/PROTOCOL.md`, `pilot.json` | `research/results/pilot-v1/` | Exploratory design, 20 families |
| Validation | `research/VALIDATION_PROTOCOL.md`, `validation-*.json` | `research/results/validation-*-v1/` | 200 primary + three sets of 50 robustness families |
| Early sensitivity | `research/SENSITIVITY_PROTOCOL.md` | See protocol and `paper/sensitivity_manifest.json` | Reuses 50 primary families; no new independent observations |
| Crossed design | `research/EXTENSION_PROTOCOL.md` | `research/results/extension-interaction-v1/` | 100 new families; candidate range × initialization budget |
| Factorial | Same extension protocol | `research/results/extension-generalization-v1/` | 48 cells × 30 families; 4,320 datasets |
| Operational | Same extension protocol | `research/results/extension-performance-v1/` | 120 generation/export trials; separate memory measurements |
| Coverage | Same extension protocol | `research/results/extension-coverage-v1/` | Exact enumeration on the declared probability grid |

Experimental code was frozen at `ec319056cc03f4c5ced0b3deb99d598dc8afd6c5`
for validation and `d1ed040a02e3193601e03a4d80b91bdb958c23fd` for the extension.
Each manifest identifies its own exact configuration and source hashes. Later
analysis code does not replace those revisions. The nesting-refined intervals
and fixed-count partition diagnostics are post-review analyses of unchanged fits.

## 6. Refit only when needed

For the original primary study, check out the revision recorded in its manifest,
install the recorded environment and run each command on one line:

```bash
python -m random_clusters.research.run --config research/validation-primary.json --protocol research/VALIDATION_PROTOCOL.md --output data/validation-primary
python -m random_clusters.research.report data/validation-primary
```

For the four extension studies, use their frozen revision and new output paths:

```bash
python -m research.extension.run interaction --output data/extension-interaction
python -m research.extension.run generalization --output data/extension-generalization
python -m research.extension.run coverage --output data/extension-coverage
python -m research.extension.run performance --output data/extension-performance
```

Run the performance study alone, after other computation finishes. Generation
timing excludes CSV export; peak Python-tracked allocations are measured in a
separate invocation and are not RSS. Archive every trial, including zero CPU
clock differences. Existing directories are rejected, protecting previous runs.

Full clustering runs are substantially more expensive than checking archives.
The runner materializes a dense pairwise distance matrix for silhouette, using
quadratic memory in the number of rows. The 100,000-row operational benchmark
measures **generation and export**, not clustering at that size.

## Interpretation and support

Independent families are the replication units. Conditions, starts and candidate
counts within a family are paired, not independent observations. Approximate
Student-t intervals are descriptive; conservative intervals are pointwise and
do not imply simultaneous coverage across all reported comparisons. Details and
all cellwise results are in the archived protocols and the Overleaf supplement.

Report a reproducibility issue through [GitHub Issues](https://github.com/josemarialuna/RandomClustersGenerator/issues)
or `jmluna@us.es`, including the command, revision, environment and complete error.
Do not replace the archived results to hide a discrepancy.
