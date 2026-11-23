"""Build descriptive tables and figures from audited paired-workflow archives."""

import argparse
import hashlib
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from random_clusters.bundles import replay_paired
from random_clusters.experiment import audit


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archives", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    rows = []
    selected = []
    for scenario in ("balanced", "unequal", "anisotropic"):
        archive = args.archives / scenario
        audit(archive)
        spec = json.loads((archive / "config.json").read_text())
        for filename, destination in (("fits.json", rows), ("selections.json", selected)):
            for row in json.loads((archive / filename).read_text()):
                destination.append(
                    dict(scenario=scenario, **row, **spec["conditions"][row["condition"]])
                )
    fits = pd.DataFrame(rows)
    sels = pd.DataFrame(selected)
    keys = ["scenario", "scale", "noise", "distribution", "preprocessing", "method"]
    known = fits[(fits.k == 4) & (fits.status == "ok")]
    summary = (
        known.groupby(keys)
        .agg(mean_ari=("ari", "mean"), mcse_ari=("ari", "sem"), valid=("ari", "count"))
        .reset_index()
    )
    summary.to_csv(args.output / "known_count.csv", index=False)
    sels["recovered"] = (sels.status == "ok") & (sels.k == 4)
    selection = sels.groupby(keys + ["index"]).agg(
        recovery=("recovered", "mean"),
        mean_ari=("ari", "mean"),
        available=("ari", "count"),
        total=("status", "size"),
    )
    selection.to_csv(args.output / "selection.csv")
    # Condition differences are computed within replicate, not as independent means.
    base = known[known.noise == 0][
        ["scenario", "scale", "preprocessing", "method", "replicate", "ari"]
    ]
    paired = known[known.noise > 0].merge(
        base,
        on=["scenario", "scale", "preprocessing", "method", "replicate"],
        suffixes=("", "_base"),
    )
    paired["difference"] = paired.ari - paired.ari_base
    differences = (
        paired.groupby(keys)
        .agg(
            mean_difference=("difference", "mean"),
            mcse_difference=("difference", "sem"),
            valid_pairs=("difference", "count"),
        )
        .reset_index()
    )
    differences.to_csv(args.output / "paired_differences.csv", index=False)
    fits.groupby(["scenario", "status"]).size().to_csv(args.output / "fit_status.csv")
    plt.rcParams.update({"font.size": 9, "pdf.fonttype": 42})
    fig, axs = plt.subplots(2, 3, figsize=(9, 5.6), sharex=True, sharey=True)
    for j, scenario in enumerate(("balanced", "unequal", "anisotropic")):
        for i, prep in enumerate(("raw", "standardized")):
            ax = axs[i, j]
            subset = summary[
                (summary.scenario == scenario)
                & (summary.preprocessing == prep)
                & (summary.scale == 0.1)
                & (summary.distribution == "uniform")
            ]
            for method in ("kmeans", "ward", "average", "gmm"):
                curve = subset[subset.method == method].sort_values("noise")
                ax.errorbar(
                    curve.noise,
                    curve.mean_ari,
                    yerr=curve.mcse_ari,
                    marker="o",
                    markersize=3,
                    capsize=2,
                    label=method,
                )
            ax.set_title(f"{scenario}, {prep}")
            ax.set_xticks([0, 2, 8])
            ax.set_ylim(-0.05, 1.05)
            if i == 1:
                ax.set_xlabel("Nuisance dimensions")
            if j == 0:
                ax.set_ylabel("Known-count ARI")
    handles, labels = axs[0, 0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="lower center", ncol=4)
    fig.tight_layout(rect=(0, 0.07, 1, 1))
    fig.savefig(args.output / "paired_recovery.pdf")
    fig.savefig(args.output / "paired_recovery.png", dpi=150)
    plt.close(fig)
    # Replicate zero is fixed in the protocol. Show its strongest planned
    # nuisance condition with a contingency table, rather than duplicate truth panels.
    archive = args.archives / "balanced"
    ci = 3
    meta = json.loads((archive / "datasets" / f"family-0000-condition-{ci:03d}.json").read_text())
    data = replay_paired(meta)
    choice = next(
        r
        for r in selected
        if r["scenario"] == "balanced"
        and r["replicate"] == 0
        and r["condition"] == ci
        and r["method"] == "kmeans"
        and r["preprocessing"] == "standardized"
        and r["index"] == "silhouette"
    )
    if choice["status"] != "ok":
        raise ValueError("The fixed gallery example has no available selection")
    k = choice["k"]
    labels = np.load(
        archive / "partitions" / f"family-0000-condition-{ci:03d}-standardized-kmeans-{k}.npy"
    )
    fig, axs = plt.subplots(2, 2, figsize=(8, 6.6))
    for ax, x, y, color, title, xlabel, ylabel in (
        (axs[0, 0], data.X.s0, data.X.s1, data.y, "Generating components", "s0", "s1"),
        (
            axs[0, 1],
            data.X.s0,
            data.X.s1,
            labels,
            f"Selected partition: k={k}, ARI={choice['ari']:.3f}",
            "s0",
            "s1",
        ),
        (
            axs[1, 0],
            data.X.d0,
            data.X.d1,
            labels,
            "Same partition, two nuisance coordinates",
            "d0",
            "d1",
        ),
    ):
        ax.scatter(x, y, c=color, cmap="tab10", vmin=0, vmax=9, s=12, alpha=0.75)
        ax.set(title=title, xlabel=xlabel, ylabel=ylabel)
    counts = np.zeros((4, k), dtype=int)
    np.add.at(counts, (data.y, labels), 1)
    ax = axs[1, 1]
    ax.imshow(counts, cmap="Blues", aspect="auto", vmin=0, vmax=50)
    for (i, j), value in np.ndenumerate(counts):
        ax.text(
            j, i, str(value), ha="center", va="center", color="white" if value > 25 else "black"
        )
    ax.set(
        xticks=range(k),
        yticks=range(4),
        xlabel="Selected cluster",
        ylabel="Generating component",
        title="Contingency counts (n=200)",
    )
    fig.tight_layout()
    fig.savefig(args.output / "paired_gallery.pdf")
    fig.savefig(args.output / "paired_gallery.png", dpi=150)
    plt.close(fig)
    out = dict(
        datasets=len(fits[["scenario", "replicate", "condition"]].drop_duplicates()),
        fits=len(fits),
        selections=len(sels),
        invalid_fits=int((fits.status != "ok").sum()),
        unavailable_selections=int((sels.status != "ok").sum()),
        source_hash=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    )
    (args.output / "summary.json").write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps(out))


if __name__ == "__main__":
    main()
