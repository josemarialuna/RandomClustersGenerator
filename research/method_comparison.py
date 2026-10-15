"""Fixed-grid comparison using the public generation API. See adjacent protocol."""

import argparse
import hashlib
import importlib.metadata
import itertools
import json
import platform
import subprocess
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.cluster import AgglomerativeClustering, KMeans
from sklearn.exceptions import ConvergenceWarning
from sklearn.metrics import (
    adjusted_mutual_info_score,
    adjusted_rand_score,
    calinski_harabasz_score,
    davies_bouldin_score,
    pairwise_distances,
    silhouette_score,
)
from sklearn.mixture import GaussianMixture
from sklearn.preprocessing import StandardScaler
from threadpoolctl import threadpool_limits

from random_clusters import GeneratorConfig, generate

ROOT = Path(__file__).resolve().parents[1]
MASTER = 2026101501
METHODS = ("kmeans", "ward", "average", "gmm")
CRITERIA = ("silhouette", "ch", "db")
COUNTS = tuple(range(2, 9))


def seed(*keys):
    return int(np.random.SeedSequence([MASTER, *keys]).generate_state(1)[0])


def fingerprint(array):
    return hashlib.sha256(np.ascontiguousarray(array).tobytes()).hexdigest()


def dataset(k, replicate, sigma, q):
    result = generate(
        GeneratorConfig(
            clusters=k,
            samples=400 // k,
            features=2,
            noise=8,
            std=sigma,
            seed=seed(k, replicate, 0),
            shuffle=False,
        )
    )
    order = np.random.default_rng(seed(k, replicate, 1)).permutation(400)
    x = result.data.drop(columns="cluster").to_numpy()[order, : 2 + q]
    y = result.data.cluster.to_numpy()[order]
    return x, y, result.centers


def estimator(method, k, random_seed):
    if method == "kmeans":
        return KMeans(
            n_clusters=k,
            n_init=10,
            max_iter=300,
            tol=1e-4,
            algorithm="lloyd",
            random_state=random_seed,
        )
    if method == "gmm":
        return GaussianMixture(
            n_components=k,
            covariance_type="full",
            n_init=5,
            max_iter=300,
            tol=1e-3,
            reg_covar=1e-6,
            init_params="kmeans",
            random_state=random_seed,
        )
    return AgglomerativeClustering(n_clusters=k, linkage=method, metric="euclidean")


def scores(x, y, labels, distances):
    return dict(
        ari=adjusted_rand_score(y, labels),
        ami=adjusted_mutual_info_score(y, labels, average_method="arithmetic"),
        silhouette=silhouette_score(distances, labels, metric="precomputed"),
        ch=calinski_harabasz_score(x, labels),
        db=davies_bouldin_score(x, labels),
    )


def choose(rows, criterion):
    if len(rows) != len(COUNTS) or any(r["status"] != "ok" for r in rows):
        return None
    direction = 1 if criterion == "db" else -1
    return min(rows, key=lambda r: (direction * r[criterion], r["candidate_k"]))


def summarize(fits, selections, output):
    keys = ["true_k", "sigma", "q", "method"]
    known = fits[fits.candidate_k == fits.true_k]
    rows = []
    for group, frame in known.groupby(keys):
        row = dict(zip(keys, group, strict=True))
        row.update(families=len(frame), valid=int(frame.status.eq("ok").sum()))
        for metric in ("ari", "ami"):
            values = frame.loc[frame.status.eq("ok"), metric]
            row.update(
                {
                    metric: values.mean(),
                    f"{metric}_sd": values.std(ddof=1),
                    f"{metric}_mcse": values.std(ddof=1) / np.sqrt(len(values)),
                }
            )
        rows.append(row)
    pd.DataFrame(rows).to_csv(output / "known_k_summary.csv", index=False)
    grouped = selections.groupby(keys + ["criterion"])
    grouped.agg(
        families=("correct", "size"),
        valid=("available", "sum"),
        successes=("correct", "sum"),
        recovery=("correct", "mean"),
        ari=("ari", "mean"),
        ami=("ami", "mean"),
    ).reset_index().to_csv(output / "selection_summary.csv", index=False)
    rows = []
    for group, frame in selections.groupby(keys):
        pivot = frame.pivot(index="replicate", columns="criterion", values="selected_k")
        for a, b in itertools.combinations(CRITERIA, 2):
            valid = pivot[[a, b]].notna().all(axis=1)
            rows.append(
                dict(zip(keys, group, strict=True))
                | dict(
                    criterion_a=a,
                    criterion_b=b,
                    valid=int(valid.sum()),
                    disagreement=float((pivot.loc[valid, a] != pivot.loc[valid, b]).mean()),
                )
            )
    pd.DataFrame(rows).to_csv(output / "index_disagreement.csv", index=False)


def run(output, replicates):
    output.mkdir(parents=True, exist_ok=False)
    config = dict(
        master_seed=MASTER,
        replicates=replicates,
        n=400,
        p=2,
        groups=[2, 4],
        sigma=[0.05, 0.15, 0.30],
        q=[0, 2, 8],
        methods=METHODS,
        candidate_k=COUNTS,
        preprocessing="StandardScaler",
    )
    (output / "config.json").write_text(json.dumps(config, indent=2) + "\n")
    all_fits, selected, records, partitions = [], [], [], {}
    with threadpool_limits(limits=1):
        for k, replicate in itertools.product(config["groups"], range(replicates)):
            baseline, truth, centers = dataset(k, replicate, 0.05, 8)
            for sigma, q in itertools.product(config["sigma"], config["q"]):
                raw, y, current_centers = dataset(k, replicate, sigma, q)
                np.testing.assert_array_equal(y, truth)
                np.testing.assert_array_equal(current_centers, centers)
                np.testing.assert_array_equal(raw[:, 2:], baseline[:, 2 : 2 + q])
                np.testing.assert_allclose(
                    (raw[:, :2] - centers[y]) / sigma,
                    (baseline[:, :2] - centers[y]) / 0.05,
                    atol=1e-13,
                )
                x = StandardScaler().fit_transform(raw)
                distances = pairwise_distances(x)
                np.fill_diagonal(distances, 0)
                ident = f"k{k}_r{replicate}_s{sigma}_q{q}"
                common = dict(dataset=ident, true_k=k, replicate=replicate, sigma=sigma, q=q)
                records.append(
                    common
                    | dict(raw_hash=fingerprint(raw), x_hash=fingerprint(x), y_hash=fingerprint(y))
                )
                for mid, method in enumerate(METHODS):
                    candidates = []
                    for candidate in COUNTS:
                        key = f"{ident}_{method}_{candidate}"
                        row = common | dict(
                            method=method,
                            candidate_k=candidate,
                            partition=key,
                            status="ok",
                            warning="",
                        )
                        try:
                            model = estimator(
                                method, candidate, seed(k, replicate, 2, mid, candidate)
                            )
                            with warnings.catch_warnings(record=True) as caught:
                                warnings.simplefilter("always", ConvergenceWarning)
                                labels = model.fit_predict(x)
                            row["warning"] = " | ".join(str(w.message) for w in caught)
                            if any(issubclass(w.category, ConvergenceWarning) for w in caught):
                                row["status"] = "nonconverged"
                            partitions[key] = labels.astype(np.int16)
                            row.update(scores(x, y, labels, distances))
                        except (ValueError, FloatingPointError) as exc:
                            row.update(status="failed", warning=str(exc))
                        candidates.append(row)
                    all_fits.extend(candidates)
                    for criterion in CRITERIA:
                        best = choose(candidates, criterion)
                        selected.append(
                            common
                            | dict(
                                method=method,
                                criterion=criterion,
                                available=best is not None,
                                selected_k=best["candidate_k"] if best else np.nan,
                                correct=bool(best and best["candidate_k"] == k),
                                ari=best["ari"] if best else np.nan,
                                ami=best["ami"] if best else np.nan,
                            )
                        )
            print(f"Completed k={k}, family={replicate + 1}/{replicates}", flush=True)
    fits, selections = pd.DataFrame(all_fits), pd.DataFrame(selected)
    fits.to_csv(output / "fits.csv", index=False)
    selections.to_csv(output / "selections.csv", index=False)
    pd.DataFrame(records).to_csv(output / "datasets.csv", index=False)
    np.savez_compressed(output / "partitions.npz", **partitions)
    summarize(fits, selections, output)
    manifest = dict(
        revision=subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        environment={
            name: importlib.metadata.version(name)
            for name in ("numpy", "pandas", "scikit-learn", "scipy", "threadpoolctl")
        },
        python=platform.python_version(),
        platform=platform.platform(),
        counts=dict(datasets=len(records), fits=len(fits), selections=len(selections)),
        status_counts=fits.status.value_counts().to_dict(),
    )
    manifest["sources"] = {
        name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
        for name in (
            "research/method_comparison.py",
            "research/METHOD_COMPARISON_PROTOCOL.md",
            "src/random_clusters/core.py",
        )
    }
    manifest["files"] = {
        p.name: hashlib.sha256(p.read_bytes()).hexdigest()
        for p in sorted(output.iterdir())
        if p.is_file()
    }
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--replicates", type=int, default=30)
    args = parser.parse_args()
    if args.replicates < 1:
        parser.error("replicates must be positive")
    run(args.output, args.replicates)
