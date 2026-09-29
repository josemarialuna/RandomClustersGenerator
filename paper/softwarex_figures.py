"""Render software architecture and a fixed, unselected paired-data example.

Run from the repository root: python paper/softwarex_figures.py
No model fitting or changes to archived scientific evidence are performed.
"""

import hashlib
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

from random_clusters.research.design import Family, Study, fingerprint

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "paper" / "softwarex"
COLORS = ["#0072B2", "#D55E00", "#009E73", "#CC79A7"]
plt.rcParams.update({"font.size": 10, "pdf.fonttype": 42, "ps.fonttype": 42})


def save(fig, stem):
    fig.savefig(OUTPUT / f"{stem}.pdf", bbox_inches="tight", metadata={"CreationDate": None})
    fig.savefig(OUTPUT / f"{stem}.png", bbox_inches="tight", dpi=200)
    plt.close(fig)


def architecture():
    fig, ax = plt.subplots(figsize=(7.1, 3.8))
    ax.set(xlim=(0, 10), ylim=(0, 5))
    ax.axis("off")
    boxes = [
        (0.05, 3.0, "INPUT\nParameters + seed\nCLI / Python / batch CSV"),
        (3.5, 3.0, "GENERATOR\nValidated configuration\nSignal + nuisance\n+ labels"),
        (6.95, 3.0, "OUTPUT\nCSV + JSON metadata\nCenters, versions\n+ SHA-256"),
        (0.05, 0.35, "RESEARCH INPUT\nJSON design + protocol\nIndependent family seeds"),
        (3.5, 0.35, "PAIRED EVALUATION\nSignal + labels fixed\nNoise / fit settings vary"),
        (
            6.95,
            0.35,
            "AUDITABLE RESULTS\nFits + selections\nManifests + partitions*",
        ),
    ]
    for x, y, label in boxes:
        ax.add_patch(
            FancyBboxPatch(
                (x, y),
                2.95,
                1.5,
                boxstyle="round,pad=0.03",
                facecolor="#F2F6FA",
                edgecolor="#284B63",
            )
        )
        ax.text(x + 1.475, y + 0.75, label, ha="center", va="center", fontsize=9)
    for y in (3.75, 1.1):
        for left in (3.05, 6.50):
            ax.add_patch(
                FancyArrowPatch(
                    (left, y), (left + 0.4, y), arrowstyle="-|>", mutation_scale=13, color="#284B63"
                )
            )
    ax.text(5, 2.47, "Core library and optional research workflow", ha="center", fontsize=10)
    save(fig, "Figure_1")


def example():
    study = Study.read(ROOT / "research" / "validation-primary.json")
    family = Family(study, 0)
    uniform = family.dataset(0.05, 2, "uniform")
    normal = family.dataset(0.05, 2, "normal")
    assert np.array_equal(uniform[:, :2], normal[:, :2])
    fig, axes = plt.subplots(1, 3, figsize=(7.1, 2.65), layout="constrained")
    views = [
        (uniform[:, :2], "(a) Shared signal", "s0", "s1"),
        (uniform[:, 2:], "(b) Uniform nuisance", "d0", "d1"),
        (normal[:, 2:], "(c) Gaussian nuisance", "d0", "d1"),
    ]
    for ax, (data, title, xlab, ylab) in zip(axes, views, strict=True):
        for group, color, marker in zip(range(4), COLORS, ["o", "s", "^", "D"], strict=True):
            selected = family.labels == group
            ax.scatter(
                data[selected, 0],
                data[selected, 1],
                s=9,
                color=color,
                marker=marker,
                alpha=0.7,
                linewidths=0,
                label=str(group),
            )
        ax.set(title=title, xlabel=xlab, ylabel=ylab, xlim=(-0.5, 1.5), ylim=(-0.5, 1.5))
        ax.set_aspect("equal")
        ax.spines[["top", "right"]].set_visible(False)
    fig.legend(
        *axes[0].get_legend_handles_labels(),
        loc="outside lower center",
        ncol=4,
        title="Generating label (evaluation only)",
        frameon=False,
        fontsize=8,
    )
    save(fig, "Figure_2")
    return {
        "configuration": "research/validation-primary.json",
        "replicate": 0,
        "selection_rule": "First prespecified primary family; no fitted-result selection",
        "uniform_sha256": fingerprint(uniform),
        "normal_sha256": fingerprint(normal),
        "labels_sha256": fingerprint(family.labels),
        "std": 0.05,
        "noise": 2,
    }


def main():
    OUTPUT.mkdir(exist_ok=True)
    architecture()
    manifest = example()
    manifest["files"] = {
        path.name: hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(OUTPUT.glob("Figure_*"))
    }
    manifest["builder_sha256"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    (OUTPUT / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"Two figures and provenance written to {OUTPUT}")


if __name__ == "__main__":
    main()
