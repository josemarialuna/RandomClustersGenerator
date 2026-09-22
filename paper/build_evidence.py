"""Derive manuscript evidence from verified raw records, without refitting models."""

import hashlib
import json
from pathlib import Path

import matplotlib
import numpy as np
import pandas as pd

from random_clusters.research.design import Family, Study, fingerprint
from random_clusters.research.report import interval, wilson

matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "paper"
SCENARIOS = ["primary", "small", "dimensions", "eight"]
LABELS = [
    "Primary\nn=400\nk=4, p=2",
    "Smaller sample\nn=200\nk=4, p=2",
    "More coordinates\nn=400\nk=4, p=4",
    "Eight groups\nn=400\nk=8, p=3",
]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_run(name):
    folder = ROOT / "research" / "results" / f"validation-{name}-v1"
    manifest = json.loads((folder / "manifest.json").read_text())
    if manifest["status"] != "complete":
        raise ValueError(f"incomplete run: {name}")
    for file, expected in manifest["output_sha256"].items():
        if digest(folder / file) != expected:
            raise ValueError(f"raw artifact mismatch: {name}/{file}")
    study = Study.read(folder / "config.json")
    datasets = [json.loads(line) for line in (folder / "datasets.jsonl").read_text().splitlines()]
    family = None
    last = None
    for row in datasets:
        if row["replicate"] != last:
            family = Family(study, row["replicate"])
            last = row["replicate"]
        data = family.dataset(row["std"], row["noise"], row["distribution"])
        if (
            fingerprint(data) != row["data_sha256"]
            or fingerprint(family.labels) != row["labels_sha256"]
        ):
            raise ValueError(f"dataset replay mismatch: {name}/{row['dataset_id']}")
    fits = pd.read_csv(folder / "fits.csv")
    selections = pd.read_csv(folder / "selections.csv")
    if not fits.status.eq("ok").all() or not selections.status.eq("ok").all():
        raise ValueError("Report failed fits explicitly before publishing aggregate results")
    if (
        len(datasets) != study.dataset_count
        or len(fits) != manifest["expected_fits"]
        or len(selections) != manifest["expected_selections"]
    ):
        raise ValueError("unexpected record count")
    oracle = fits[(fits.method == "kmeans") & (fits.candidate_k == study.clusters)]
    keys = ["dataset_id", "replicate", "std", "noise", "distribution", "preprocessing"]
    selections = selections.merge(
        oracle[keys + ["ari"]].rename(columns={"ari": "known_k_ari"}),
        on=keys,
        validate="many_to_one",
    )
    selections["selection_difference"] = selections.ari - selections.known_k_ari
    selections["boundary"] = selections.selected_k.isin(
        [min(study.candidate_k), max(study.candidate_k)]
    ).astype(int)
    return study, manifest, fits, oracle, selections, datasets


def csv(frame, name):
    frame.to_csv(OUT / name, index=False, float_format="%.17g", lineterminator="\n")


def main():
    summary, contrasts, counts, selected_counts, geometry = [], [], [], [], []
    source_manifests = {}
    source_hashes = None
    for name in SCENARIOS:
        study, manifest, fits, oracle, selections, datasets = load_run(name)
        if source_hashes is None:
            source_hashes = manifest["source_sha256"]
        elif source_hashes != manifest["source_sha256"]:
            raise ValueError("experimental source files differ across validation runs")
        source_manifests[name] = digest(
            ROOT / "research" / "results" / f"validation-{name}-v1" / "manifest.json"
        )
        counts.append(
            {
                "scenario": name,
                **manifest["observed"],
                "families": study.replicates,
                "seconds": manifest["elapsed_seconds"],
            }
        )
        geometries = {row["replicate"]: len(row["varying_signal_features"]) for row in datasets}
        for replicate, varying in geometries.items():
            geometry.append(
                {"scenario": name, "replicate": replicate, "varying_signal_features": varying}
            )
        groups = ["std", "noise", "distribution", "preprocessing"]
        for keys, frame in oracle.groupby(groups):
            identity = {"scenario": name, **dict(zip(groups, keys))}
            summary.append({**identity, "endpoint": "known_k_ari", **interval(frame.ari)})
        for keys, frame in selections.groupby(groups + ["criterion"]):
            identity = {"scenario": name, **dict(zip(groups + ["criterion"], keys))}
            for metric in ["ari", "selection_difference", "boundary"]:
                summary.append({**identity, "endpoint": metric, **interval(frame[metric])})
            low, high = wilson(int(frame.correct_k.sum()), len(frame))
            summary.append(
                {
                    **identity,
                    "endpoint": "correct_k",
                    "n": len(frame),
                    "mean": frame.correct_k.mean(),
                    "successes": frame.correct_k.sum(),
                    "mcse": np.sqrt(
                        frame.correct_k.mean() * (1 - frame.correct_k.mean()) / len(frame)
                    ),
                    "ci_low": low,
                    "ci_high": high,
                }
            )
            for selected_k, total in frame.selected_k.value_counts().items():
                selected_counts.append({**identity, "selected_k": selected_k, "count": total})
        for frame, metric, extra in [(oracle, "ari", []), (selections, "correct_k", ["criterion"])]:
            keys = ["replicate", "std", "noise", "preprocessing"] + extra
            matched = frame[frame.distribution == "normal"].merge(
                frame[frame.distribution == "uniform"],
                on=keys,
                suffixes=("_normal", "_uniform"),
                validate="one_to_one",
            )
            matched["difference"] = matched[metric + "_normal"] - matched[metric + "_uniform"]
            for key, pair in matched.groupby(keys[1:]):
                contrasts.append(
                    {
                        "scenario": name,
                        **dict(zip(keys[1:], key)),
                        "endpoint": metric,
                        **interval(pair.difference),
                    }
                )
    summary = pd.DataFrame(summary)
    contrasts = pd.DataFrame(contrasts)
    csv(summary, "validation_summary.csv")
    csv(contrasts, "validation_contrasts.csv")
    csv(pd.DataFrame(counts), "run_counts.csv")
    csv(pd.DataFrame(selected_counts), "selected_counts.csv")
    csv(pd.DataFrame(geometry), "geometry.csv")

    primary = summary[(summary.scenario == "primary") & (summary.noise == 2)]
    rows = []
    for preprocessing in ["raw", "standardized"]:
        for distribution in ["uniform", "normal"]:
            frame = primary[
                (primary.preprocessing == preprocessing) & (primary.distribution == distribution)
            ]
            known = frame[frame.endpoint == "known_k_ari"].iloc[0]
            rate = frame[frame.endpoint == "correct_k"].set_index("criterion")
            rows.append(
                f"{preprocessing.title()} & {distribution.title()} & "
                f"{known['mean']:.3f} [{known.ci_low:.3f}, {known.ci_high:.3f}] & "
                + " & ".join(
                    f"{int(rate.loc[c, 'successes'])}/200"
                    for c in ["silhouette", "calinski_harabasz", "davies_bouldin"]
                )
                + r" \\"
            )
    table = (
        r"""\begin{table}[htbp]
\centering\footnotesize
\setlength{\tabcolsep}{3pt}
\caption{Independent validation at $q=2$, $\sigma=0.05$. Known-count K-means
ARI is reported as mean [pointwise 95\% interval]. Other columns count correct
selections of $k=4$ out of 200 families (Sil: silhouette; CH: Calinski--Harabasz;
DB: Davies--Bouldin). Values rounded to 1.000 need not equal one exactly;
unrounded estimates are archived.}
\label{tab:primary}
\begin{tabular}{llrrrr}
\toprule
Scale & Noise & Known-count ARI & Sil & CH & DB \\
\midrule
"""
        + "\n".join(rows)
        + r"""
\bottomrule
\end{tabular}
\end{table}
"""
    )
    (OUT / "primary_table.tex").write_text(table, encoding="utf-8", newline="\n")

    contrast = contrasts[
        (contrasts.scenario == "primary")
        & (contrasts.preprocessing == "standardized")
        & (contrasts.endpoint == "correct_k")
        & (contrasts.criterion == "silhouette")
    ].iloc[0]
    numbers = {
        "PrimaryDifference": contrast["mean"],
        "PrimaryMCSE": contrast.mcse,
        "PrimaryLower": contrast.ci_low,
        "PrimaryUpper": contrast.ci_high,
    }
    commands = "\n".join(rf"\newcommand{{\{key}}}{{{value:.3f}}}" for key, value in numbers.items())
    (OUT / "numbers.tex").write_text(commands + "\n", encoding="utf-8", newline="\n")

    plt.rcParams.update({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False})
    fig, axes = plt.subplots(1, 2, figsize=(10.5, 4.2), constrained_layout=True)
    for ax, endpoint, criterion, ylabel in [
        (axes[0], "known_k_ari", None, "Known-count K-means ARI"),
        (axes[1], "correct_k", "silhouette", "Silhouette selects generating k"),
    ]:
        for dist, offset, color in [("uniform", -0.09, "#c66b1f"), ("normal", 0.09, "#167d9a")]:
            frame = summary[
                (summary["std"] == 0.05)
                & (summary.noise == 2)
                & (summary.preprocessing == "standardized")
                & (summary.distribution == dist)
                & (summary.endpoint == endpoint)
            ]
            if criterion:
                frame = frame[frame.criterion == criterion]
            frame = frame.set_index("scenario").loc[SCENARIOS]
            means = frame["mean"].to_numpy()
            ax.errorbar(
                np.arange(4) + offset,
                means,
                yerr=np.maximum(0, np.vstack([means - frame.ci_low, frame.ci_high - means])),
                fmt="o",
                color=color,
                capsize=3,
                label=dist.title(),
            )
        ax.set(xticks=np.arange(4), xticklabels=LABELS, ylim=(-0.035, 1.065), ylabel=ylabel)
        ax.grid(axis="y", alpha=0.2)
    axes[0].legend(loc="lower left", frameon=False)
    fig.suptitle("Standardized data · two irrelevant coordinates · σ = 0.05")
    for ext in ["pdf", "png"]:
        fig.savefig(OUT / f"validation.{ext}", dpi=200)
    plt.close(fig)
    artifacts = [
        "validation_summary.csv",
        "validation_contrasts.csv",
        "run_counts.csv",
        "selected_counts.csv",
        "geometry.csv",
        "primary_table.tex",
        "numbers.tex",
        "validation.pdf",
        "validation.png",
    ]
    audit = {
        "source_manifests": source_manifests,
        "dataset_replay": "all fingerprints match",
        "experimental_source_consistency": "identical source hashes across all four runs",
        "script_sha256": digest(Path(__file__)),
        "artifacts": {file: digest(OUT / file) for file in artifacts},
    }
    (OUT / "evidence_manifest.json").write_text(
        json.dumps(audit, indent=2) + "\n", encoding="utf-8"
    )
    print(pd.DataFrame(counts).to_string(index=False))
    print(
        contrasts[
            (contrasts.scenario == "primary") & (contrasts.preprocessing == "standardized")
        ].to_string(index=False)
    )


if __name__ == "__main__":
    main()
