# Code Ocean reproduction

Use Python 3.12.4 with the pinned packages in `codeocean/postInstall`.
These scientific package versions match `research/environment-paired-workflow.txt`.
The capsule imports the source package using `PYTHONPATH`.
All outputs go to `/results/reproduction`. No credentials or input data downloads
are needed during execution.

The default run checks the preserved archive, regenerates all 600 datasets,
recalculates scores and decisions from 24,000 saved partitions, rebuilds both
manuscript figures and numerical tables, and compares the numerical tables with
the archived versions. It also fits a new quickstart example and repeats the
operational experiment. New timing measurements describe the capsule machine
and are not expected to equal the original PC measurements.

The deep audit does **not** refit the 24,000 archived candidates. To additionally
refit the complete experiment, pass `--full-refit` to the run script. Those
outputs are stored separately and are not substituted for the original evidence.
Numerical differences across platforms are possible. Audit failures are fatal
and are never silently converted into successful checks.

## Outputs

- `figures-and-tables/paired_recovery.pdf`: manuscript Figure 1.
- `figures-and-tables/paired_gallery.pdf`: manuscript Figure 2.
- CSV files in that directory: descriptive tables and paired differences.
- `archived-experiments/`: preserved observations and partitions.
- `fresh-example/`: newly fitted example with its own audit manifest.
- `new-operational-measurements/`: newly measured trials and environment.
- `verification.json`: written only after every requested step passes.
- `environment.txt`: installed package versions.

Local execution from the repository root:

```bash
python codeocean/reproduce.py --output data/codeocean-check
```

Use a new output directory for each run. The manuscript and its historical
research-use claims are maintained in Overleaf. This capsule concerns the
current Python software and the paired-workflow demonstration, not the earlier
Scala/Spark experiments.

## Build a capsule upload

```bash
python codeocean/package.py data/capsule-upload
```

Upload the resulting `source.zip`, `run`, `README.md` and `source-manifest.json`
to the capsule's `/code` directory. Upload `evidence.zip` to `/data`.
Copy `codeocean/postInstall` into the
environment post-install script. The `run` file extracts the scoped source
into a temporary directory, invokes the driver and cleans up that temporary
directory after execution. Preserve the uploaded `run` content if the platform
offers to generate a replacement launcher. No network access is needed after
the environment has been built.

The source manifest records the SHA-256 of every packaged file. The packaging
step separates current source and paired examples from their frozen evidence,
without unrelated historical experiments or local environment files.
