"""Post-review analyses of unchanged archives; no new fits or manuscript prose."""

import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from research.extension.inference import bounded_mean, paired_bounds  # noqa: E402
from research.verify_extension import digest, verify  # noqa: E402


def nested_interaction(table):
    """Fixed fits and tie rule imply Y(wide)<=Y(narrow) at either budget."""
    for starts in [10, 100]:
        if not table[starts, 16].le(table[starts, 8]).all():
            raise ValueError("range expansion violates the fixed-fit nesting invariant")
    return (table[100, 16] - table[100, 8]) - (table[10, 16] - table[10, 8])


def build():
    inputs, outputs = [], []

    def read(kind, file):
        directory = ROOT / "research/results" / f"extension-{kind}-v1"
        verify(directory)
        inputs.append(directory / "manifest.json")
        path = directory / file
        return pd.read_json(path, lines=True) if file.endswith("jsonl") else pd.read_csv(path)

    def save(name, rows):
        path = ROOT / "paper" / f"review_02_{name}.csv"
        pd.DataFrame(rows).to_csv(path, index=False, float_format="%.17g", lineterminator="\n")
        outputs.append(path)

    selected = read("interaction", "selections.jsonl")
    fits = read("interaction", "fits.jsonl")
    inertia = fits.pivot(
        index=["family", "distribution", "candidate_k"], columns="starts", values="inertia"
    )
    if not (inertia[100] <= inertia[10] + 1e-10).all():
        raise ValueError("larger nested initialization budget increased best inertia")
    rows = []
    for (law, criterion), frame in selected.groupby(["distribution", "criterion"]):
        table = frame.pivot(index="family", columns=["starts", "upper"], values="correct_k")
        values = nested_interaction(table)
        positive, negative = int(values.eq(1).sum()), int(values.eq(-1).sum())
        low, high = paired_bounds(positive, negative, len(values))
        rows.append(
            dict(
                distribution=law,
                criterion=criterion,
                positive=positive,
                negative=negative,
                cp_low=float(low),
                cp_high=float(high),
                **bounded_mean(values, -1, 1),
            )
        )
    save("interaction", rows)
    save(
        "indices",
        selected.groupby(["criterion", "distribution", "starts", "upper"])
        .agg(
            successes=("correct_k", "sum"),
            families=("family", "count"),
            selected_ari=("ari", "mean"),
        )
        .reset_index(),
    )

    mechanisms = read("interaction", "mechanisms.jsonl")
    rows = []
    # Fixed counts remove the changing-number-of-groups explanation for the
    # signal/noise comparison. These remain descriptive, post-review diagnostics.
    fixed = mechanisms[(mechanisms.starts == 100) & mechanisms.candidate_k.isin([4, 8, 16])]
    for (law, k), frame in fixed.groupby(["distribution", "candidate_k"]):
        difference = frame.noise_within_truth_explained - frame.signal_within_truth_explained
        rows.append(
            dict(
                distribution=law,
                candidate_k=k,
                signal_mean=frame.signal_within_truth_explained.mean(),
                noise_mean=frame.noise_within_truth_explained.mean(),
                **bounded_mean(difference, -1, 1),
            )
        )
    save("fixed_partition_diagnostics", rows)

    factorial = read("generalization", "selections.jsonl")
    cell = factorial.groupby(["criterion", "cell", "distribution"]).correct_k.mean().unstack()
    cell["difference"] = cell.normal - cell.uniform
    save(
        "factorial_indices",
        cell.groupby("criterion")
        .agg(
            minimum=("difference", "min"),
            maximum=("difference", "max"),
            mean=("difference", "mean"),
            positive_cells=("difference", lambda s: int((s > 0).sum())),
            negative_cells=("difference", lambda s: int((s < 0).sum())),
        )
        .reset_index(),
    )

    trials = read("performance", "trials.csv")
    rows = []
    for (cell, method), frame in trials.groupby(["cell", "method"]):
        for metric in ["generation_wall_seconds", "csv_seconds", "tracked_peak_bytes"]:
            values = frame[metric]
            rows.append(
                dict(
                    cell=cell,
                    method=method,
                    metric=metric,
                    trials=len(values),
                    minimum=values.min(),
                    q25=values.quantile(0.25),
                    median=values.median(),
                    q75=values.quantile(0.75),
                    maximum=values.max(),
                )
            )
    save("performance_spread", rows)
    sources = set(inputs + outputs + [Path(__file__), ROOT / "paper/review_02_hardware.json"])
    manifest = {
        "analysis": "post-review supplement; original records and analyses unchanged",
        "files": {p.relative_to(ROOT).as_posix(): digest(p) for p in sorted(sources)},
    }
    (ROOT / "paper/review_02_manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8", newline="\n"
    )
    print("Built six post-review evidence tables from verified archives")


def check():
    manifest = json.loads((ROOT / "paper/review_02_manifest.json").read_text())
    for name, expected in manifest["files"].items():
        if digest(ROOT / name) != expected:
            raise ValueError(f"post-review evidence changed: {name}")
    print("Verified post-review evidence")


if __name__ == "__main__":
    check() if "--check" in sys.argv else build()
