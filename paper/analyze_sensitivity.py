"""Audit post-validation diagnostic reruns against the same primary families."""

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

from random_clusters.research.report import interval, wilson

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "research" / "results"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def records(directory):
    manifest = json.loads((directory / "manifest.json").read_text())
    if manifest["status"] != "complete":
        raise ValueError(f"incomplete: {directory}")
    for name, expected in manifest["output_sha256"].items():
        if digest(directory / name) != expected:
            raise ValueError(f"modified artifact: {directory / name}")
    data = pd.read_json(directory / "datasets.jsonl", lines=True)
    fits = pd.read_csv(directory / "fits.csv")
    selected = pd.read_csv(directory / "selections.csv")
    if len(fits) != manifest["expected_fits"] or len(selected) != manifest["expected_selections"]:
        raise ValueError("incomplete record counts")
    if not fits.status.eq("ok").all() or not selected.status.eq("ok").all():
        raise ValueError("failed fit/selection requires explicit reporting")
    known = fits[(fits.method == "kmeans") & (fits.candidate_k == 4)]
    return manifest, data, fits, selected, known


def main():
    base_manifest, base_data, base_fits, base_selected, base_known = records(
        BASE / "validation-primary-v1"
    )
    base_data = base_data[base_data.replicate < 50]
    base_fits = base_fits[base_fits.replicate < 50]
    base_selected = base_selected[base_selected.replicate < 50]
    base_known = base_known[base_known.replicate < 50]
    summary, changes, histograms, counts = [], [], [], []
    keys = ["dataset_id", "preprocessing"]
    group_keys = ["noise", "distribution", "preprocessing"]
    manifests = {"primary": digest(BASE / "validation-primary-v1" / "manifest.json")}
    for name in ["range", "starts"]:
        directory = BASE / f"sensitivity-{name}-v1"
        manifest, data, fits, selected, known = records(directory)
        manifests[name] = digest(directory / "manifest.json")
        for field in ["data_sha256", "labels_sha256", "signal_sha256"]:
            actual = data.set_index("dataset_id")[field].sort_index()
            expected = base_data.set_index("dataset_id")[field].sort_index()
            pd.testing.assert_series_equal(actual, expected)
        # Range expansion must not change any shared candidate's non-timing result.
        if name == "range":
            fit_keys = keys + ["method", "candidate_k"]
            metrics = ["ari", "nmi", "silhouette", "calinski_harabasz", "davies_bouldin"]
            comparison = fits[fits.candidate_k <= 8].merge(
                base_fits, on=fit_keys, suffixes=("_new", "_old"), validate="one_to_one"
            )
            if len(comparison) != len(base_fits):
                raise ValueError("missing shared fits")
            for metric in metrics:
                np.testing.assert_array_equal(
                    comparison[metric + "_new"], comparison[metric + "_old"]
                )
        # Ward is unaffected by either diagnostic and must remain exactly reproducible.
        wards = fits[fits.method == "ward"].merge(
            base_fits[base_fits.method == "ward"],
            on=keys,
            suffixes=("_new", "_old"),
            validate="one_to_one",
        )
        np.testing.assert_array_equal(wards.ari_new, wards.ari_old)
        selected = selected.merge(
            known[keys + ["ari"]].rename(columns={"ari": "known_ari"}),
            on=keys,
            validate="many_to_one",
        )
        selected["selection_difference"] = selected.ari - selected.known_ari
        selected["upper_boundary"] = selected.selected_k.eq(max(manifest["config"]["candidate_k"]))
        for identity, frame in known.groupby(group_keys):
            summary.append(
                {
                    "diagnostic": name,
                    **dict(zip(group_keys, identity)),
                    "endpoint": "known_k_ari",
                    **interval(frame.ari),
                }
            )
        for identity, frame in selected.groupby(group_keys + ["criterion"]):
            row = {"diagnostic": name, **dict(zip(group_keys + ["criterion"], identity))}
            low, high = wilson(int(frame.correct_k.sum()), len(frame))
            summary.append(
                {
                    **row,
                    "endpoint": "correct_k",
                    "n": len(frame),
                    "mean": frame.correct_k.mean(),
                    "ci_low": low,
                    "ci_high": high,
                }
            )
            for metric in ["selection_difference", "upper_boundary"]:
                summary.append({**row, "endpoint": metric, **interval(frame[metric])})
            for k, count in frame.selected_k.value_counts().items():
                histograms.append({**row, "selected_k": k, "count": count})
        for new, old, metric, extra in [
            (known, base_known, "ari", []),
            (selected, base_selected, "correct_k", ["criterion"]),
        ]:
            joined = new.merge(
                old, on=keys + extra, suffixes=("_new", "_old"), validate="one_to_one"
            )
            joined["difference"] = joined[metric + "_new"] - joined[metric + "_old"]
            groups = [key + "_new" for key in group_keys if key != "preprocessing"]
            groups += ["preprocessing"] + extra
            for identity, frame in joined.groupby(groups):
                changes.append(
                    {
                        "diagnostic": name,
                        **dict(zip(group_keys + extra, identity)),
                        "endpoint": metric,
                        **interval(frame.difference),
                    }
                )
        counts.append({"diagnostic": name, **manifest["observed"]})
    for rows, filename in [
        (summary, "sensitivity_summary.csv"),
        (changes, "sensitivity_changes.csv"),
        (histograms, "sensitivity_counts.csv"),
        (counts, "sensitivity_runs.csv"),
    ]:
        pd.DataFrame(rows).to_csv(
            ROOT / "paper" / filename, index=False, float_format="%.17g", lineterminator="\n"
        )
    audit = {
        "source_manifests": manifests,
        "script_sha256": digest(Path(__file__)),
        "dataset_pairing": "all 300 evaluations match 150 distinct primary datasets",
        "shared_candidate_metrics": "exact replay for range expansion",
        "artifacts": {p.name: digest(p) for p in (ROOT / "paper").glob("sensitivity_*.csv")},
    }
    (ROOT / "paper" / "sensitivity_manifest.json").write_text(
        json.dumps(audit, indent=2) + "\n", encoding="utf-8", newline="\n"
    )
    frame = pd.DataFrame(summary)
    print(
        frame[
            (frame.noise == 2)
            & (frame.preprocessing == "standardized")
            & ((frame.endpoint == "known_k_ari") | (frame.criterion == "silhouette"))
        ].to_string(index=False)
    )
    print(pd.DataFrame(counts).to_string(index=False))


if __name__ == "__main__":
    main()
