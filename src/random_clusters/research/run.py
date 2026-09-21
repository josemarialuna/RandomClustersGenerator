"""Run the frozen pilot; outputs are refused if their directory already exists."""

import argparse
import csv
import hashlib
import importlib.metadata
import json
import platform
import subprocess
import time
import warnings
from dataclasses import asdict
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.cluster import AgglomerativeClustering, KMeans
from sklearn.metrics import (
    adjusted_rand_score,
    calinski_harabasz_score,
    davies_bouldin_score,
    normalized_mutual_info_score,
    pairwise_distances,
    silhouette_score,
)
from sklearn.preprocessing import StandardScaler
from threadpoolctl import threadpool_info, threadpool_limits

from . import DESIGN_VERSION
from .design import Family, Study

METRICS = ["ari", "nmi", "silhouette", "calinski_harabasz", "davies_bouldin"]
KEYS = ["dataset_id", "replicate", "std", "noise", "distribution", "preprocessing"]
FIT_FIELDS = (
    KEYS + ["method", "candidate_k", "seed", "fit_seconds", "status", "warnings", "error"] + METRICS
)
SELECTION_FIELDS = KEYS + [
    "criterion",
    "selected_k",
    "ari",
    "nmi",
    "correct_k",
    "ari_regret",
    "status",
]


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git_value(*args):
    result = subprocess.run(["git", *args], capture_output=True, text=True, check=False)
    return result.stdout.strip() if result.returncode == 0 else None


def scores(data, distances, truth, labels):
    if not 2 <= len(np.unique(labels)) < len(data):
        raise ValueError("internal scores require 2 <= number of clusters < n")
    return {
        "ari": float(adjusted_rand_score(truth, labels)),
        "nmi": float(normalized_mutual_info_score(truth, labels, average_method="arithmetic")),
        "silhouette": float(silhouette_score(distances, labels, metric="precomputed")),
        "calinski_harabasz": float(calinski_harabasz_score(data, labels)),
        "davies_bouldin": float(davies_bouldin_score(data, labels)),
    }


def fit_partition(data, distances, truth, *, k, method, seed, study):
    row = {
        "method": method,
        "candidate_k": k,
        "seed": seed,
        "fit_seconds": None,
        "status": "ok",
        "warnings": "",
        "error": "",
        **dict.fromkeys(METRICS),
    }
    model = (
        KMeans(
            n_clusters=k,
            n_init=study.kmeans_n_init,
            max_iter=study.kmeans_max_iter,
            random_state=seed,
            init="k-means++",
            algorithm="lloyd",
            tol=1e-4,
        )
        if method == "kmeans"
        else AgglomerativeClustering(n_clusters=k, linkage="ward", metric="euclidean")
    )
    caught = []
    try:
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            start = time.perf_counter()
            labels = model.fit_predict(data)
            row["fit_seconds"] = time.perf_counter() - start
            if len(np.unique(labels)) != k:
                raise ValueError("fitted partition did not produce the requested k")
            row.update(scores(data, distances, truth, labels))
            if not all(np.isfinite(row[name]) for name in METRICS):
                raise ValueError("nonfinite metric")
            if method == "kmeans" and model.n_iter_ >= study.kmeans_max_iter:
                row["status"] = "iteration_limit"
    except (ValueError, FloatingPointError, np.linalg.LinAlgError) as error:
        row.update(status="failed", error=f"{type(error).__name__}: {error}")
    row["warnings"] = " | ".join(str(item.message) for item in caught)
    return row


def select_partitions(rows, true_k):
    """Only internal criteria choose a partition; truth is used afterwards."""
    results = []
    valid = all(row["status"] == "ok" for row in rows)
    for criterion in ("silhouette", "calinski_harabasz", "davies_bouldin"):
        row = {
            "criterion": criterion,
            "selected_k": None,
            "ari": None,
            "nmi": None,
            "correct_k": None,
            "ari_regret": None,
            "status": "failed",
        }
        if valid:
            direction = 1 if criterion == "davies_bouldin" else -1
            selected = min(
                rows, key=lambda item: (direction * item[criterion], item["candidate_k"])
            )
            row.update(
                selected_k=selected["candidate_k"],
                ari=selected["ari"],
                nmi=selected["nmi"],
                correct_k=int(selected["candidate_k"] == true_k),
                ari_regret=max(item["ari"] for item in rows) - selected["ari"],
                status="ok",
            )
        results.append(row)
    return results


def provenance(study, config_path, protocol):
    package_root = Path(__file__).resolve().parents[1]
    sources = {
        str(path.relative_to(package_root)).replace("\\", "/"): sha256(path)
        for path in sorted(package_root.rglob("*.py"))
    }
    versions = {
        name: importlib.metadata.version(name)
        for name in (
            "random-clusters-generator",
            "numpy",
            "pandas",
            "scipy",
            "scikit-learn",
            "matplotlib",
            "threadpoolctl",
        )
    }
    return {
        "status": "running",
        "design_version": DESIGN_VERSION,
        "config": asdict(study),
        "config_sha256": sha256(config_path),
        "protocol_sha256": sha256(protocol),
        "source_commit": git_value("rev-parse", "HEAD"),
        "git_dirty": bool(git_value("status", "--porcelain")),
        "source_sha256": sources,
        "versions": versions,
        "python": platform.python_version(),
        "platform": platform.platform(),
        "thread_limit": 1,
        "threadpools": [],  # Recorded inside the actual thread-limited execution.
        "expected_datasets": study.dataset_count,
        "expected_fits": study.dataset_count
        * len(study.preprocessing)
        * (len(study.candidate_k) + 1),
        "expected_selections": study.dataset_count * len(study.preprocessing) * 3,
    }


def run(study, output: Path, config_path: Path, protocol: Path):
    # Read required inputs before making an output directory.
    manifest = provenance(study, config_path, protocol)
    output.mkdir(parents=True, exist_ok=False)
    (output / "config.json").write_bytes(config_path.read_bytes())
    (output / "protocol.md").write_bytes(protocol.read_bytes())
    manifest_path = output / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8", newline="\n")
    gallery = output / "gallery"
    gallery.mkdir()
    started = time.perf_counter()
    counts = {
        "datasets": 0,
        "fits": 0,
        "selections": 0,
        "fit_failures": 0,
        "selection_failures": 0,
        "fit_warnings": 0,
    }
    with (
        (output / "fits.csv").open("w", newline="", encoding="utf-8") as fit_stream,
        (output / "selections.csv").open("w", newline="", encoding="utf-8") as selection_stream,
        (output / "truth_scores.csv").open("w", newline="", encoding="utf-8") as truth_stream,
        (output / "datasets.jsonl").open("w", encoding="utf-8", newline="\n") as datasets,
    ):
        fit_writer = csv.DictWriter(fit_stream, fieldnames=FIT_FIELDS, lineterminator="\n")
        selection_writer = csv.DictWriter(
            selection_stream, fieldnames=SELECTION_FIELDS, lineterminator="\n"
        )
        truth_writer = csv.DictWriter(truth_stream, fieldnames=KEYS + METRICS, lineterminator="\n")
        for writer in (fit_writer, selection_writer, truth_writer):
            writer.writeheader()
        with threadpool_limits(limits=1):
            manifest["threadpools"] = [
                {
                    key: (Path(value).name if key == "filepath" else value)
                    for key, value in pool.items()
                }
                for pool in threadpool_info()
            ]
            for replicate in range(study.replicates):
                family = Family(study, replicate)
                for std in study.standard_deviations:
                    for noise in sorted(study.noise_counts):
                        distributions = study.noise_distributions if noise else ["none"]
                        for distribution in distributions:
                            data = family.dataset(std, noise, distribution)
                            dataset_id = f"r{replicate:03d}_sd{std:g}_q{noise}_{distribution}"
                            identity = dict(
                                dataset_id=dataset_id,
                                replicate=replicate,
                                std=std,
                                noise=noise,
                                distribution=distribution,
                            )
                            diagnostic = {**identity, **family.diagnostics(data, std)}
                            datasets.write(json.dumps(diagnostic, allow_nan=False) + "\n")
                            counts["datasets"] += 1
                            if replicate == 0 and noise in (0, max(study.noise_counts)):
                                columns = [f"s{i}" for i in range(study.features)]
                                columns += [f"d{i}" for i in range(noise)]
                                table = pd.DataFrame(data, columns=columns)
                                table["cluster"] = family.labels
                                table.to_csv(
                                    gallery / f"{dataset_id}.csv",
                                    index=False,
                                    float_format="%.17g",
                                    lineterminator="\n",
                                )
                            for preprocessing in study.preprocessing:
                                keys = {**identity, "preprocessing": preprocessing}
                                values = (
                                    StandardScaler().fit_transform(data)
                                    if preprocessing == "standardized"
                                    else data
                                )
                                distances = pairwise_distances(values, metric="euclidean")
                                np.fill_diagonal(distances, 0)
                                truth_writer.writerow(
                                    {
                                        **keys,
                                        **scores(values, distances, family.labels, family.labels),
                                    }
                                )
                                candidates = []
                                for k in sorted(study.candidate_k):
                                    candidates.append(
                                        fit_partition(
                                            values,
                                            distances,
                                            family.labels,
                                            k=k,
                                            method="kmeans",
                                            seed=family.algorithm_seed(k),
                                            study=study,
                                        )
                                    )
                                ward = fit_partition(
                                    values,
                                    distances,
                                    family.labels,
                                    k=study.clusters,
                                    method="ward",
                                    seed=None,
                                    study=study,
                                )
                                for row in candidates + [ward]:
                                    fit_writer.writerow({**keys, **row})
                                    counts["fits"] += 1
                                    counts["fit_failures"] += row["status"] != "ok"
                                    counts["fit_warnings"] += bool(row["warnings"])
                                for row in select_partitions(candidates, study.clusters):
                                    selection_writer.writerow({**keys, **row})
                                    counts["selections"] += 1
                                    counts["selection_failures"] += row["status"] != "ok"
                for handle in (fit_stream, selection_stream, truth_stream, datasets):
                    handle.flush()
                print(
                    f"Replicate {replicate + 1}/{study.replicates}; "
                    f"{counts['datasets']} datasets; {time.perf_counter() - started:.1f}s",
                    flush=True,
                )
    for name in ("datasets", "fits", "selections"):
        if counts[name] != manifest[f"expected_{name}"]:
            raise RuntimeError(f"incomplete {name}: {counts[name]}")
    manifest.update(
        status="complete", observed=counts, elapsed_seconds=time.perf_counter() - started
    )
    manifest["output_sha256"] = {
        str(path.relative_to(output)).replace("\\", "/"): sha256(path)
        for path in sorted(output.rglob("*"))
        if path.is_file() and path != manifest_path
    }
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8", newline="\n")
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=Path("research/pilot.json"))
    parser.add_argument("--protocol", type=Path, default=Path("research/PROTOCOL.md"))
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        run(Study.read(args.config), args.output, args.config, args.protocol)
    except (ValueError, OSError) as error:
        parser.exit(2, f"error: {error}\n")


if __name__ == "__main__":
    main()
