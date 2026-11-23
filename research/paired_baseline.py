"""Independent NumPy reference for the public paired sampling specification.

Does not import random_clusters. Deliberately implements the same competent
per-component stream design, not a naive reseeding baseline.
"""

import hashlib
import json
import platform
from pathlib import Path

import numpy as np
import pandas as pd


def sample(config, condition):
    """Return table, labels and IDs from explicit centers and covariances."""
    seed, replicate = config["seed"], config.get("replicate", 0)

    def rng(component, index=0):
        return np.random.Generator(
            np.random.PCG64(np.random.SeedSequence(seed, spawn_key=(replicate, component, index)))
        )

    sizes = config["sizes"]
    centers = np.asarray(config["centers"], dtype=float)
    n, p = sum(sizes), centers.shape[1]
    cov = np.asarray(config.get("covariances", [np.eye(p).tolist()] * len(sizes)))
    y = np.repeat(np.arange(len(sizes)), sizes)
    z = rng(1).standard_normal((n, p))
    transformed = np.empty_like(z)
    for c in range(len(sizes)):
        # Independent expression of the same triangular transformation.
        L = np.linalg.cholesky(cov[c])
        for j in range(p):
            transformed[y == c, j] = sum(z[y == c, h] * L[j, h] for h in range(j + 1))
    signal = centers[y] + condition.get("scale", 0.1) * transformed
    columns = []
    for j in range(condition.get("noise", 0)):
        if condition.get("distribution", "uniform") == "uniform":
            columns.append(rng(3, j).random(n))
        else:
            columns.append(rng(4, j).normal(0.5, 1 / np.sqrt(12), n))
    X = np.column_stack([signal, *columns])
    order = rng(2).permutation(n) if config.get("shuffle", True) else np.arange(n)
    return (
        pd.DataFrame(
            X[order], columns=[f"s{j}" for j in range(p)] + [f"d{j}" for j in range(len(columns))]
        ),
        y[order],
        order,
    )


def save(config, condition, path):
    """Export and record provenance for the independently implemented baseline."""
    path = Path(path)
    if path.exists() or path.with_suffix(".json").exists():
        raise FileExistsError(path)
    X, y, ids = sample(config, condition)
    X["row_id"], X["cluster"] = ids, y
    X.to_csv(path, index=False, float_format="%.17g", lineterminator="\n")
    metadata = dict(
        family=config,
        condition=condition,
        sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
        python=platform.python_version(),
        numpy=np.__version__,
        pandas=pd.__version__,
    )
    path.with_suffix(".json").write_text(json.dumps(metadata, indent=2) + "\n")


def verify(path):
    path = Path(path)
    metadata = json.loads(path.with_suffix(".json").read_text())
    assert hashlib.sha256(path.read_bytes()).hexdigest() == metadata["sha256"]
    X, y, ids = sample(metadata["family"], metadata["condition"])
    saved = pd.read_csv(path, float_precision="round_trip")
    np.testing.assert_array_equal(saved[X.columns], X)
    np.testing.assert_array_equal(saved.cluster, y)
    np.testing.assert_array_equal(saved.row_id, ids)
