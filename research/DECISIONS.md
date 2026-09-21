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
