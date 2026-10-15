"""Render prespecified gallery and per-cell recovery, without refitting."""

import hashlib
import json
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from research.method_comparison import dataset  # noqa: E402
from research.verify_method_comparison import verify  # noqa: E402

INPUT = ROOT / "research/results/method-comparison-v1"
OUTPUT = ROOT / "paper/method-comparison"
COLORS = ["#0072B2", "#D55E00", "#009E73", "#CC79A7"]
METHODS = [
    ("kmeans", "K-means"),
    ("ward", "Ward"),
    ("average", "Average linkage"),
    ("gmm", "Gaussian mixture"),
]
plt.rcParams.update({"font.size": 9, "pdf.fonttype": 42, "ps.fonttype": 42})


def save(fig, name):
    fig.savefig(OUTPUT / f"{name}.pdf", bbox_inches="tight", metadata={"CreationDate": None})
    fig.savefig(OUTPUT / f"{name}.png", bbox_inches="tight", dpi=200)
    plt.close(fig)


def main():
    verify(INPUT)
    OUTPUT.mkdir(exist_ok=True)
    fig, axes = plt.subplots(2, 3, figsize=(7.1, 4.4), layout="constrained")
    for column, sigma in enumerate([0.05, 0.15, 0.30]):
        x, y, _ = dataset(4, 0, sigma, 2)
        for row, offset in enumerate([0, 2]):
            ax = axes[row, column]
            for label, color, marker in zip(range(4), COLORS, ["o", "s", "^", "D"], strict=True):
                points = x[y == label]
                ax.scatter(
                    points[:, offset],
                    points[:, offset + 1],
                    s=8,
                    alpha=0.65,
                    c=color,
                    marker=marker,
                    linewidths=0,
                    label=str(label),
                )
            ax.set(xlim=(-1.1, 2.0), ylim=(-1.1, 2.0), aspect="equal")
            ax.set_xlabel("s0" if row == 0 else "d0")
            if column == 0:
                ax.set_ylabel("Signal: s1" if row == 0 else "Nuisance: d1")
            if row == 0:
                ax.set_title(rf"$\sigma={sigma:.2f}$")
    save(fig, "dataset_gallery")

    known = pd.read_csv(INPUT / "known_k_summary.csv")
    fig, axes = plt.subplots(2, 3, figsize=(7.1, 4.5), sharex=True, sharey=True)
    for row, k in enumerate([2, 4]):
        for col, q in enumerate([0, 2, 8]):
            ax = axes[row, col]
            for mid, ((method, label), color, marker) in enumerate(
                zip(METHODS, COLORS, ["o", "s", "^", "D"], strict=True)
            ):
                frame = known[
                    (known.true_k == k) & (known.q == q) & (known.method == method)
                ].sort_values("sigma")
                ax.errorbar(
                    frame.sigma + (mid - 1.5) * 0.002,
                    frame.ari,
                    yerr=frame.ari_mcse,
                    color=color,
                    marker=marker,
                    markersize=3.5,
                    capsize=2,
                    linewidth=1.2,
                    label=label,
                )
            ax.set_title(f"k = {k}, q = {q}")
            ax.set(ylim=(-0.05, 1.05), xticks=[0.05, 0.15, 0.30])
            ax.grid(axis="y", alpha=0.2)
            if col == 0:
                ax.set_ylabel("Mean known-k ARI")
            if row == 1:
                ax.set_xlabel(r"Dispersion $\sigma$")
    handles, labels = axes[0, 0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="lower center", ncol=4, frameon=False)
    fig.tight_layout(rect=(0, 0.07, 1, 1))
    save(fig, "method_recovery")

    selections = pd.read_csv(INPUT / "selections.csv")
    summary = selections.groupby(["method", "criterion"]).agg(
        datasets=("correct", "size"),
        valid=("available", "sum"),
        successes=("correct", "sum"),
        recovery=("correct", "mean"),
        selected_ari=("ari", "mean"),
        selected_ami=("ami", "mean"),
    )
    summary.to_csv(OUTPUT / "selection_grid_summary.csv")
    # Exploratory diagnostic after inspecting the prespecified results. This is
    # not an additional prospective endpoint or a causal mechanism test.
    fits = pd.read_csv(INPUT / "fits.csv")
    partitions = np.load(INPUT / "partitions.npz", allow_pickle=False)
    diagnostics = []
    for replicate in range(30):
        _, _, centers = dataset(2, replicate, 0.05, 0)
        key = f"k2_r{replicate}_s0.05_q0_average_2"
        counts = np.unique(partitions[key], return_counts=True)[1]
        diagnostics.append(
            dict(
                replicate=replicate,
                varying_center_coordinates=int((np.ptp(centers, axis=0) > 0).sum()),
                smallest_fitted_group=int(counts.min()),
                ari=float(fits.loc[fits.partition == key, "ari"].iloc[0]),
            )
        )
    pd.DataFrame(diagnostics).to_csv(OUTPUT / "exploratory_geometry_diagnostic.csv", index=False)
    manifest = {
        "input_manifest_sha256": hashlib.sha256((INPUT / "manifest.json").read_bytes()).hexdigest(),
        "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "files": {
            p.name: hashlib.sha256(p.read_bytes()).hexdigest()
            for p in OUTPUT.iterdir()
            if p.is_file() and p.name != "manifest.json"
        },
    }
    (OUTPUT / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")


if __name__ == "__main__":
    main()
