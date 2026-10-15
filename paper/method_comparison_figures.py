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


def latex_figures(known):
    """Editable Overleaf figures from the same arrays, without binary uploads."""
    colors = ["0072B2", "D55E00", "009E73", "CC79A7"]
    definitions = "\n".join(
        rf"\definecolor{{study{i}}}{{HTML}}{{{color}}}" for i, color in enumerate(colors)
    )
    gallery = [
        definitions,
        r"\begin{tikzpicture}",
        r"\begin{groupplot}[group style={group size=3 by 2,horizontal sep=0.6cm,"
        r"vertical sep=1cm},width=0.31\textwidth,height=0.30\textwidth,"
        r"xmin=-1.1,xmax=2,ymin=-1.1,ymax=2,xtick={-1,0,1,2},ytick={-1,0,1,2},"
        r"tick label style={font=\scriptsize},label style={font=\small},"
        r"title style={font=\small}]",
    ]
    for row in range(2):
        for column, sigma in enumerate([0.05, 0.15, 0.30]):
            x, y, _ = dataset(4, 0, sigma, 2)
            options = [f"xlabel={{{'s0' if row == 0 else 'd0'}}}"]
            if column == 0:
                options.append(f"ylabel={{{'Signal: s1' if row == 0 else 'Nuisance: d1'}}}")
            if row == 0:
                options.append(rf"title={{$\sigma={sigma:.2f}$}}")
            gallery.append(r"\nextgroupplot[" + ",".join(options) + "]")
            for label, marker in enumerate(["*", "square*", "triangle*", "diamond*"]):
                points = x[y == label, row * 2 : row * 2 + 2]
                coords = " ".join(f"({a:.8f},{b:.8f})" for a, b in points)
                gallery.append(
                    rf"\addplot[only marks,color=study{label},mark={marker},"
                    rf"mark size=0.65pt,opacity=0.65] coordinates {{{coords}}};"
                )
    gallery.extend([r"\end{groupplot}", r"\end{tikzpicture}"])
    (OUTPUT / "dataset_gallery.tex").write_text("\n".join(gallery) + "\n", encoding="utf-8")
    recovery = [
        definitions,
        r"\begin{tikzpicture}",
        r"\begin{groupplot}[group style={group size=3 by 2,horizontal sep=0.65cm,"
        r"vertical sep=1cm},width=0.31\textwidth,height=0.29\textwidth,"
        r"xmin=0.03,xmax=0.32,ymin=-0.05,ymax=1.05,xtick={0.05,0.15,0.30},"
        r"ytick={0,0.5,1},tick label style={font=\scriptsize},"
        r"label style={font=\small},title style={font=\small},"
        r"legend style={font=\scriptsize,draw=none},legend columns=2]",
    ]
    for k in [2, 4]:
        for q in [0, 2, 8]:
            options = [f"title={{$k={k},q={q}$}}"]
            if q == 0:
                options.append("ylabel={Mean known-count ARI}")
            if k == 4:
                options.append(r"xlabel={Dispersion $\sigma$}")
            if k == 2 and q == 0:
                options.append("legend to name=methodlegend")
            recovery.append(r"\nextgroupplot[" + ",".join(options) + "]")
            for mid, (method, name) in enumerate(METHODS):
                frame = known[
                    (known.true_k == k) & (known.q == q) & (known.method == method)
                ].sort_values("sigma")
                coords = " ".join(
                    f"({r.sigma + (mid - 1.5) * 0.002:.6f},{r.ari:.8f}) +- (0,{r.ari_mcse:.8f})"
                    for r in frame.itertuples()
                )
                marker = ["*", "square*", "triangle*", "diamond*"][mid]
                recovery.append(
                    rf"\addplot[color=study{mid},mark={marker},mark size=1.5pt,"
                    rf"error bars/.cd,y dir=both,y explicit] coordinates {{{coords}}};"
                )
                if k == 2 and q == 0:
                    recovery.append(rf"\addlegendentry{{{name}}}")
    recovery.extend([r"\end{groupplot}", r"\end{tikzpicture}", r"\par\smallskip\ref{methodlegend}"])
    (OUTPUT / "method_recovery.tex").write_text("\n".join(recovery) + "\n", encoding="utf-8")


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
    latex_figures(known)
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
