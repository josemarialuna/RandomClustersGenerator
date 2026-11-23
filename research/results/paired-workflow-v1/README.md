# Paired workflow evaluation v1

Executed on 23 November 2026 from source and protocol commit
`9e9560f52a995e53ceee0b61134f149edc102773`. This is a new experiment, not an
update to historical evidence. The sampler and runner were committed before
execution. The summary script was developed after execution.

## Contents

- `experiments.zip`: three complete scenario archives with 600 datasets,
  their metadata, 24,000 candidate partitions and 14,400 selection records.
- `summary/`: cellwise ARI summaries, paired differences, count recovery,
  selected-partition ARI, failure counts and two figures.
- `operational/`: every timing and allocation trial, summary and machine details.
- `environment.txt`: the environment used for this execution.
- `manifest.json`: artifact hashes and audit outcomes.

All three deep audits passed. They regenerated every dataset and recalculated
metrics and selection decisions from saved partitions. They did not refit the
optimizers. No candidate failed or produced a convergence warning. Each cell
has 20 independent families, not 200 independent condition rows.

The operational run was executed after the scientific runs and their audits
finished. An earlier concurrent timing run was excluded because competing
computation made it unsuitable for this purpose. No scientific records were
excluded. Timing ranges describe seven trials on one machine, not confidence
intervals or portability guarantees. Python-traced allocations are not RSS.

The gallery uses the prespecified first balanced family at scale 0.1 and eight
uniform nuisance coordinates. Its four-panel presentation was chosen after
execution to show the generating partition, selected partition, a nuisance
projection and contingency counts without repeating identical signal panels.
It is an illustration, not a representative estimate of all families.

## Verify and reproduce

From the repository root:

```bash
python research/verify_paired_archive.py research/results/paired-workflow-v1
python -m zipfile -e research/results/paired-workflow-v1/experiments.zip data/paired-archived
python -m random_clusters.experiment data/paired-archived/balanced --audit --deep
python -m random_clusters.experiment data/paired-archived/unequal --audit --deep
python -m random_clusters.experiment data/paired-archived/anisotropic --audit --deep
python research/summarize_paired.py data/paired-archived data/paired-summary-rebuilt
```

To refit, use the recorded source revision and environment with the JSON
configurations in each extracted archive. Choose a new output directory.
See `docs/workflows.md` for the complete task-oriented instructions.

Historical extension verification uses its own original source revision.
Do not replace historical hashes or relabel old evidence as version 1.1.
