# Research decisions

## 2026-09-21 — Pilot v1, before scientific execution

- Start with an exploratory milestone rather than a journal manuscript. No novelty
  or acceptance claim; closely overlapping prior work identified and cited.
- Keep the production generator unchanged. Add an optional paired research layer.
- Fix k=4 and two signal coordinates so every family uses the complete square
  geometry. This avoids conflating growing dimension with increasing separation.
- Match uniform and normal noise population moments. The normal variance is 1/12,
  not the production add-noise utility's historical variance of 0.05².
- Freeze 20 independent families, three spreads, four noise levels, raw/scaled
  tracks, K-means candidates 2–8 and Ward at generating k.
- Treat generating-k recovery and geometric score preference as distinct targets.
- Use full-data internal scores, paired differences, Monte Carlo errors, t and
  Wilson intervals; no confirmatory hypothesis tests in this pilot.
- Use component-specific random streams and stable per-column noise generation.
- Test replay, pairing, selection without ground truth, output integrity and a
  reduced end-to-end run before scientific execution. Reduced test fixtures do
  not use the scientific pilot's master seed or represent reported results.
- Freeze a source commit before running the scientific configuration. Any
  post-run amendments must be logged below and distinguished from planned work.

## 2026-09-21 — Artifact portability amendment

During the first execution's provenance audit, identified Windows newline
translation that would invalidate byte hashes after Git normalizes text files.
Standardized CSV/JSON/JSONL/report newlines to LF and added regression coverage.
Also moved threadpool metadata capture inside the thread limit and omitted local
directory names from library paths. These are instrumentation corrections; no
parameters, seeds, models, endpoints or selection rules changed. Repeat the exact
same pilot in a new output directory and compare every non-timing fit value with
the initial execution before archiving the portable evidence package.

## 2026-09-21 — Completed pilot and presentation audit

Portable run completed: 420 datasets, 6,720 fits, 2,520 selections; zero failed
fits/selections and zero warnings. Every non-timing fit/selection/diagnostic value
matched the first execution exactly. Regenerated all dataset and label hashes.
Both executions represent the same 20 families, not 40 independent replicates.

Visual inspection prompted shorter y-axis labels and shared axis scales for
comparability. Only report rendering changed after the run; analysis source hashes
are separately recorded. No model, metric, endpoint or experimental setting changed.
Interpretation and candidate next-stage questions are recorded in FINDINGS.es.md.

Copied the protocol's two referenced files next to its archived snapshot so its
relative links resolve. The added context copies are covered by the analysis
manifest; no original run artifact was edited. Future runs copy them automatically.

## 2026-09-22 — Independent validation audit

The separately seeded primary validation (200 families) and three robustness
scenarios (50 each) completed 3,750 datasets, 68,400 fits and 22,500 selections.
All fit/selection statuses are successful and no warnings were recorded. All
3,750 dataset/label fingerprints were regenerated. Experimental source hashes
are identical across the four runs and match the frozen implementation.

The primary run started from clean commit ec319056. Later runs record a dirty
working tree because manuscript drafts and preceding run outputs were being
created. No experimental Python source changed: nine source hashes are recorded
and were checked against the current implementation. Later run source commits
also include manuscript work, not model or design changes.

A long wall-clock interruption occurred between progress outputs for families
46 and 47 of the eight-group run. Its elapsed time is preserved, not corrected
or treated as an algorithm benchmark. All families completed; no fit was
removed, restarted or counted twice.

The large primary silhouette count-recovery contrast did not transfer to the
partial four-dimensional cube (20/50 vs 19/50). This remains in the manuscript
and evidence rather than being excluded. The study does not claim universal
superiority of Gaussian nuisance variables or standardization.

At the author's request, manuscript authoring and checkpoints now take place
in Overleaf. Git retains code, executable protocols and computational evidence;
manuscript prose is removed from the active tree without rewriting history.
