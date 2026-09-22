"""Derive complete, machine-readable revision evidence; no manuscript prose."""

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import t
from sklearn.metrics import adjusted_rand_score

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from random_clusters.research.design import fingerprint  # noqa: E402
from research.extension.inference import bounded_mean, paired_bounds  # noqa: E402
from research.extension.models import cells, factorial_data, interaction_data  # noqa: E402
from research.verify_extension import KINDS, digest, verify  # noqa: E402

OUTPUT = ROOT / "paper"
ARTIFACTS = []


def save(name, rows):
    path = OUTPUT / f"extension_{name}.csv"
    pd.DataFrame(rows).to_csv(path, index=False, float_format="%.17g", lineterminator="\n")
    ARTIFACTS.append(path)


def paired(values):
    result = bounded_mean(values, -1, 1)
    result["families"] = result.pop("n")
    positive, negative = int((values == 1).sum()), int((values == -1).sum())
    low, high = paired_bounds(positive, negative, len(values))
    return dict(
        result, positive=positive, negative=negative, cp_low=float(low), cp_high=float(high)
    )


def replay(directory, kind):
    manifest = json.loads((directory / "manifest.json").read_text())
    datasets = pd.read_json(directory / "datasets.jsonl", lines=True)
    fits = pd.read_json(directory / "fits.jsonl", lines=True)
    selected = pd.read_json(directory / "selections.jsonl", lines=True)
    for name, frame in [("datasets", datasets), ("fits", fits), ("selections", selected)]:
        assert len(frame) == manifest["expected"][name]
        assert frame.family.nunique() == manifest["expected"]["families"]
    assert not datasets.duplicated(["family", "distribution"]).any()
    assert not fits.duplicated(["family", "distribution", "starts", "candidate_k"]).any()
    assert not selected.duplicated(["family", "distribution", "starts", "upper", "criterion"]).any()
    assert fits.status.eq("ok").all() and selected.status.eq("ok").all()
    assert fits.warnings.eq("").all()
    indexed_fits = {
        identity: group.to_dict("records")
        for identity, group in fits.groupby(["family", "distribution", "starts"])
    }
    for row in selected.itertuples():
        candidates = indexed_fits[row.family, row.distribution, row.starts]
        candidates = [item for item in candidates if item["candidate_k"] <= row.upper]
        assert len(candidates) == row.upper - 1
        sign = 1 if row.criterion == "davies_bouldin" else -1
        chosen = min(candidates, key=lambda item: (sign * item[row.criterion], item["candidate_k"]))
        assert row.selected_k == chosen["candidate_k"]
        assert np.isclose(row.ari, chosen["ari"], atol=1e-12)
        true_k = 4 if kind == "interaction" else row.k
        known = next(item for item in candidates if item["candidate_k"] == true_k)
        assert np.isclose(row.known_ari, known["ari"], atol=1e-12)
        assert row.correct_k == int(row.selected_k == true_k)
        assert np.isclose(row.selection_difference, row.ari - row.known_ari, atol=1e-12)
    for family, group in datasets.groupby("family"):
        first = group.iloc[0]
        if kind == "interaction":
            data, truth, _, _ = interaction_data(int(first.replicate))
        else:
            data, truth, _ = factorial_data(cells()[int(first.cell)], int(first.replicate))
        assigned = np.load(directory / "labels" / f"{family}.npz", allow_pickle=False)
        np.testing.assert_array_equal(truth, assigned["truth"])
        for row in group.itertuples():
            assert fingerprint(data[row.distribution]) == row.data_sha256
        for row in fits[fits.family == family].itertuples():
            labels = assigned[f"{row.distribution}_s{row.starts}_k{row.candidate_k}"]
            assert fingerprint(labels) == row.label_sha256
            assert np.isclose(adjusted_rand_score(truth, labels), row.ari, atol=1e-12)
        assigned.close()
    return selected


def interaction(directory, selected):
    rows, contrasts = [], []
    keys = ["distribution", "criterion", "starts", "upper"]
    for values, frame in selected.groupby(keys):
        row = dict(zip(keys, values, strict=True))
        row.update(
            successes=int(frame.correct_k.sum()),
            boundary=int((frame.selected_k == frame.upper).sum()),
        )
        for metric in ["correct_k", "ari", "known_ari", "selection_difference"]:
            lo, hi = (
                (-2, 2)
                if metric == "selection_difference"
                else ((0, 1) if metric == "correct_k" else (-1, 1))
            )
            row.update({f"{metric}_{k}": v for k, v in bounded_mean(frame[metric], lo, hi).items()})
        rows.append(row)
    save("interaction", rows)
    for (law, criterion), frame in selected.groupby(["distribution", "criterion"]):
        table = frame.pivot(index="family", columns=["starts", "upper"], values="correct_k")
        values = (table[100, 16] - table[100, 8]) - (table[10, 16] - table[10, 8])
        contrasts.append(dict(distribution=law, criterion=criterion, **bounded_mean(values, -2, 2)))
    save("interaction_contrasts", contrasts)
    mechanism = pd.read_json(directory / "mechanisms.jsonl", lines=True)
    joined = selected.merge(
        mechanism,
        left_on=["family", "distribution", "starts", "selected_k"],
        right_on=["family", "distribution", "starts", "candidate_k"],
        validate="many_to_one",
    )
    joined["normalized_noise_information"] = joined.normalized_conditional_noise_information.map(
        np.mean
    )
    metrics = [
        "selected_k",
        "signal_within_truth_explained",
        "noise_within_truth_explained",
        "normalized_noise_information",
    ]
    save("mechanisms", joined.groupby(keys)[metrics].mean().reset_index())
    save(
        "selected_k_counts",
        selected.groupby(keys + ["selected_k"]).size().rename("count").reset_index(),
    )


def generalization(selected):
    rows, contrasts = [], []
    factors = ["cell", "k", "p", "n", "separation", "geometry", "criterion"]
    for identity, frame in selected.groupby(factors):
        base = dict(zip(factors, identity, strict=True))
        for law, subset in frame.groupby("distribution"):
            row = dict(base, distribution=law, successes=int(subset.correct_k.sum()))
            for metric in ["correct_k", "ari", "known_ari"]:
                row.update(
                    {
                        f"{metric}_{key}": value
                        for key, value in bounded_mean(
                            subset[metric], -1 if metric != "correct_k" else 0, 1
                        ).items()
                    }
                )
            rows.append(row)
        pivot = frame.pivot(index="family", columns="distribution", values="correct_k")
        contrasts.append(dict(base, **paired(pivot.normal - pivot.uniform)))
    save("factorial_cells", rows)
    save("factorial_noise_contrasts", contrasts)
    effects = []
    # Independent cells; equal cell weights. Welch intervals are approximate,
    # while weighted Hoeffding bounds use the known family outcome support.
    for criterion, frame in pd.DataFrame(contrasts).groupby("criterion"):
        for factor, low, high in [
            ("k", 3, 4),
            ("p", 3, 6),
            ("n", 240, 480),
            ("separation", 3, 8),
            ("geometry", "cube", "random"),
            ("geometry", "random", "anisotropic"),
        ]:
            a, b = frame[frame[factor] == low], frame[frame[factor] == high]
            estimate = b["mean"].mean() - a["mean"].mean()
            terms = np.r_[
                a.mcse.to_numpy() ** 2 / len(a) ** 2, b.mcse.to_numpy() ** 2 / len(b) ** 2
            ]
            variance = terms.sum()
            df = variance**2 / (terms**2 / 29).sum() if variance else np.inf
            radius = t.ppf(0.975, df) * np.sqrt(variance)
            h = np.sqrt(2 * np.log(40) * (1 / (30 * len(a)) + 1 / (30 * len(b))))
            effects.append(
                dict(
                    criterion=criterion,
                    factor=factor,
                    low=low,
                    high=high,
                    mean=estimate,
                    mcse=np.sqrt(variance),
                    welch_df=df,
                    t_low=estimate - radius,
                    t_high=estimate + radius,
                    hoeffding_low=max(-2, estimate - h),
                    hoeffding_high=min(2, estimate + h),
                )
            )
    save("factorial_effects", effects)


def performance(directory):
    frame = pd.read_csv(directory / "trials.csv")
    keys = ["cell", "n", "p", "q", "method"]
    metrics = [
        "generation_wall_seconds",
        "generation_cpu_seconds",
        "csv_seconds",
        "csv_bytes",
        "tracked_peak_bytes",
    ]
    save("performance", frame.groupby(keys)[metrics].median().reset_index())
    ratios = []
    for cell, subset in frame.groupby("cell"):
        for metric in metrics:
            pivot = subset.pivot(index="repetition", columns="method", values=metric)
            valid = pivot.make_blobs_reference > 0
            ratio = (pivot.package / pivot.make_blobs_reference)[valid]
            ratios.append(
                dict(
                    cell=cell,
                    metric=metric,
                    valid_ratios=int(valid.sum()),
                    zero_reference=int((~valid).sum()),
                    median_ratio=ratio.median() if len(ratio) else np.nan,
                    minimum_ratio=ratio.min() if len(ratio) else np.nan,
                    maximum_ratio=ratio.max() if len(ratio) else np.nan,
                )
            )
    save("performance_ratios", ratios)


def main():
    manifests = []
    for kind in KINDS:
        directory = ROOT / "research/results" / f"extension-{kind}-v1"
        manifest = verify(directory, git_sources=True)
        manifests.append(directory / "manifest.json")
        if kind in {"interaction", "generalization"}:
            selected = replay(directory, kind)
            assert len(selected) == manifest["expected"]["selections"]
            if kind == "interaction":
                interaction(directory, selected)
            else:
                generalization(selected)
        elif kind == "performance":
            performance(directory)
        else:
            frame = pd.read_csv(directory / "coverage.csv")
            save(
                "coverage_worst", frame.loc[frame.groupby(["families", "method"]).coverage.idxmin()]
            )
        print(f"Verified and analyzed {kind}", flush=True)
    sources = [Path(__file__), ROOT / "research/verify_extension.py", *manifests, *ARTIFACTS]
    result = {
        "files": {p.relative_to(ROOT).as_posix(): digest(p) for p in sources},
        "replay": "all 4520 datasets and 36240 cached candidate ARIs and label hashes verified",
    }
    (OUTPUT / "extension_manifest.json").write_text(
        json.dumps(result, indent=2) + "\n", encoding="utf-8", newline="\n"
    )


if __name__ == "__main__":
    main()
