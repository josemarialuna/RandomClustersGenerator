"""Public JSON-driven paired experiment runner and saved-partition auditor.

Run ``python -m random_clusters.experiment CONFIG OUTPUT``. Requires the
``research`` extra. External labels never enter preprocessing, fitting or ICVI
selection. All candidates and failures are retained.
"""

import argparse
import hashlib
import json
import platform
import warnings
from dataclasses import replace
from pathlib import Path

import numpy as np
import pandas as pd
import sklearn
from sklearn.cluster import AgglomerativeClustering, KMeans
from sklearn.exceptions import ConvergenceWarning
from sklearn.metrics import (
    adjusted_mutual_info_score,
    adjusted_rand_score,
    calinski_harabasz_score,
    davies_bouldin_score,
    silhouette_score,
)
from sklearn.mixture import GaussianMixture
from sklearn.preprocessing import StandardScaler
from threadpoolctl import threadpool_limits

from . import __version__
from .bundles import replay_paired, save_paired, verify_paired
from .core import _integer
from .families import Condition, FamilyConfig, PairedFamily

METHODS = ("kmeans", "ward", "average", "gmm")
INDICES = ("silhouette", "ch", "db")


def scores(X, labels, truth):
    """Compute internal indices and external agreement for a saved partition."""
    if not 2 <= len(np.unique(labels)) < len(labels):
        raise ValueError("validity indices require 2 <= observed clusters < n")
    return dict(
        silhouette=float(silhouette_score(X, labels)),
        ch=float(calinski_harabasz_score(X, labels)),
        db=float(davies_bouldin_score(X, labels)),
        ari=float(adjusted_rand_score(truth, labels)),
        ami=float(adjusted_mutual_info_score(truth, labels)),
    )


def validate(spec):
    """Validate the full design before creating output files."""
    expected = {
        "family",
        "replicates",
        "conditions",
        "methods",
        "candidates",
        "preprocessing",
        "n_init",
        "max_iter",
    }
    if set(spec) != expected:
        raise ValueError(f"configuration keys must be {sorted(expected)}")
    family = FamilyConfig(**spec["family"])
    for name in ("replicates", "n_init", "max_iter"):
        _integer(name, spec[name], 1)
    for name in ("methods", "candidates", "preprocessing"):
        values = spec[name]
        if not values or len(set(values)) != len(values):
            raise ValueError(f"{name} must be nonempty and unique")
    if not set(spec["methods"]) <= set(METHODS):
        raise ValueError("unsupported method")
    if not set(spec["preprocessing"]) <= {"raw", "standardized"}:
        raise ValueError("unsupported preprocessing")
    for k in spec["candidates"]:
        _integer("candidate", k, 2)
        if k >= sum(family.sizes):
            raise ValueError("candidate must be smaller than n")
    conditions = [Condition(**item) for item in spec["conditions"]]
    if not conditions or len(set(conditions)) != len(conditions):
        raise ValueError("conditions must be nonempty and unique")
    return family, conditions


def _fit(X, method, k, seed, spec):
    if method == "kmeans":
        model = KMeans(
            n_clusters=k, n_init=spec["n_init"], max_iter=spec["max_iter"], random_state=seed
        )
    elif method == "gmm":
        model = GaussianMixture(
            n_components=k, n_init=spec["n_init"], max_iter=spec["max_iter"], random_state=seed
        )
    else:
        model = AgglomerativeClustering(n_clusters=k, linkage=method)
    return model.fit_predict(X)


def select(records):
    """Conservative selection: any invalid candidate invalidates its entire grid."""
    complete = all(row["status"] == "ok" for row in records)
    results = []
    for index in INDICES:
        row = {"index": index, "status": "ok" if complete else "unavailable"}
        if complete:
            best = min(records, key=lambda r: (r[index] if index == "db" else -r[index], r["k"]))
            row.update(k=best["k"], ari=best["ari"], ami=best["ami"])
        results.append(row)
    return results


def _json(path, data):
    path.write_text(json.dumps(data, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def run(spec, output):
    """Write datasets, candidate partitions, scores, selections and source hashes.

    Refuses an existing directory. An interrupted run can leave partial files,
    but only a completed run receives manifest.json.
    """
    family_config, conditions = validate(spec)
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    _json(output / "config.json", spec)
    fits, selections = [], []
    with threadpool_limits(limits=1):
        for replicate in range(spec["replicates"]):
            family = PairedFamily(
                replace(family_config, replicate=family_config.replicate + replicate)
            )
            for ci, condition in enumerate(conditions):
                dataset = family.dataset(condition)
                stem = f"family-{replicate:04d}-condition-{ci:03d}"
                save_paired(dataset, output / "datasets" / f"{stem}.csv")
                for preprocessing in spec["preprocessing"]:
                    X = dataset.X.to_numpy()
                    if preprocessing == "standardized":
                        X = StandardScaler().fit_transform(X)
                    for method in spec["methods"]:
                        key = dict(
                            replicate=replicate,
                            condition=ci,
                            preprocessing=preprocessing,
                            method=method,
                        )
                        candidates = []
                        for k in sorted(spec["candidates"]):
                            seed = family.fit_seed(METHODS.index(method), k)
                            row = dict(**key, k=k, seed=seed, status="ok", warnings=[])
                            try:
                                with warnings.catch_warnings(record=True) as caught:
                                    warnings.simplefilter("always")
                                    labels = _fit(X, method, k, seed, spec)
                                row["warnings"] = [str(w.message) for w in caught]
                                partition = f"{stem}-{preprocessing}-{method}-{k}.npy"
                                (output / "partitions").mkdir(exist_ok=True)
                                np.save(
                                    output / "partitions" / partition, labels, allow_pickle=False
                                )
                                row["partition"] = partition
                                row.update(scores(X, labels, dataset.y))
                                if any(issubclass(w.category, ConvergenceWarning) for w in caught):
                                    row["status"] = "convergence_warning"
                            except (ValueError, np.linalg.LinAlgError) as error:
                                row.update(status="failed", error=str(error))
                            candidates.append(row)
                            fits.append(row)
                        selections.extend(dict(**key, **r) for r in select(candidates))
    _json(output / "fits.json", fits)
    _json(output / "selections.json", selections)
    sources = {}
    for filename in (
        "families.py",
        "bundles.py",
        "experiment.py",
        "io.py",
        "core.py",
        "__init__.py",
    ):
        sources[filename] = hashlib.sha256(
            Path(__file__).with_name(filename).read_bytes()
        ).hexdigest()
    manifest = {
        "schema": "paired-experiment-v1",
        "software": __version__,
        "python": platform.python_version(),
        "numpy": np.__version__,
        "pandas": pd.__version__,
        "sklearn": sklearn.__version__,
        "sources": sources,
        "fits": len(fits),
        "selections": len(selections),
        "invalid_fits": sum(r["status"] != "ok" for r in fits),
        "files": {
            p.relative_to(output).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(output.rglob("*"))
            if p.is_file()
        },
    }
    _json(output / "manifest.json", manifest)
    return manifest


def audit(output, *, deep=False):
    """Check hashes, then optionally regenerate data, metrics and selection decisions."""
    output = Path(output)
    manifest = json.loads((output / "manifest.json").read_text(encoding="utf-8"))
    for name, digest in manifest["files"].items():
        path = (output / name).resolve()
        if not path.is_relative_to(output.resolve()):
            raise ValueError("manifest path escapes archive")
        if hashlib.sha256(path.read_bytes()).hexdigest() != digest:
            raise ValueError(f"integrity mismatch: {name}")
    if not deep:
        return {"integrity": True, "deep": False}
    fits = json.loads((output / "fits.json").read_text(encoding="utf-8"))
    selections = json.loads((output / "selections.json").read_text(encoding="utf-8"))
    groups, cache = {}, {}
    with threadpool_limits(limits=1):
        for row in fits:
            key = tuple(row[name] for name in ("replicate", "condition", "preprocessing", "method"))
            groups.setdefault(key, []).append(row)
            if "partition" not in row or "ari" not in row:
                continue
            data_key = key[:3]
            if data_key not in cache:
                stem = f"family-{row['replicate']:04d}-condition-{row['condition']:03d}"
                path = output / "datasets" / f"{stem}.csv"
                verify_paired(path, regenerate=True)
                dataset = replay_paired(json.loads(path.with_suffix(".json").read_text()))
                X = dataset.X.to_numpy()
                if row["preprocessing"] == "standardized":
                    X = StandardScaler().fit_transform(X)
                cache[data_key] = X, dataset.y
            X, y = cache[data_key]
            partition_path = (output / "partitions" / row["partition"]).resolve()
            if not partition_path.is_relative_to((output / "partitions").resolve()):
                raise ValueError("partition path escapes archive")
            actual = scores(X, np.load(partition_path, allow_pickle=False), y)
            for metric, value in actual.items():
                if not np.isclose(value, row[metric], rtol=1e-10, atol=1e-12):
                    raise ValueError(f"metric mismatch: {metric}")
        expected = []
        for key, records in groups.items():
            header = dict(zip(("replicate", "condition", "preprocessing", "method"), key))
            expected.extend(dict(**header, **r) for r in select(records))
        if expected != selections:
            raise ValueError("selection mismatch")
    return {"integrity": True, "deep": True, "fits": len(fits), "selections": len(selections)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("config", type=Path, help="JSON configuration, or archive with --audit")
    parser.add_argument("output", type=Path, nargs="?")
    parser.add_argument("--audit", action="store_true")
    parser.add_argument("--deep", action="store_true")
    args = parser.parse_args()
    if args.audit:
        print(json.dumps(audit(args.config, deep=args.deep), indent=2))
    else:
        if args.output is None or args.deep:
            parser.error("run requires CONFIG OUTPUT; --deep is only valid with --audit")
        print(json.dumps(run(json.loads(args.config.read_text()), args.output), indent=2))


if __name__ == "__main__":
    main()
