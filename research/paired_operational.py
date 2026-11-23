"""Execute the prespecified paired workflow operational comparison."""

import argparse
import hashlib
import json
import platform
import tempfile
import time
import tracemalloc
from dataclasses import asdict
from pathlib import Path

import numpy as np
import pandas as pd
from paired_baseline import sample, save, verify

from random_clusters import Condition, FamilyConfig, PairedFamily
from random_clusters.bundles import save_paired, verify_paired


def task(config, conditions, implementation, directory):
    if implementation == "package":
        family = PairedFamily(FamilyConfig(**config))
        for i, condition in enumerate(conditions):
            path = directory / f"{i}.csv"
            save_paired(family.dataset(Condition(**condition)), path)
            verify_paired(path, regenerate=True)
    else:
        for i, condition in enumerate(conditions):
            path = directory / f"{i}.csv"
            save(config, condition, path)
            verify(path)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    records = []
    conditions = [dict(scale=0.1, noise=0), dict(scale=0.1, noise=2), dict(scale=0.25, noise=8)]
    checks = []
    for n in (200, 2000):
        config = asdict(
            FamilyConfig((n // 4,) * 4, ((0, 0), (0, 1), (1, 0), (1, 1)), seed=20261123)
        )
        family = PairedFamily(FamilyConfig(**config))
        for condition in conditions:
            data = family.dataset(Condition(**condition))
            X, y, ids = sample(config, condition)
            np.testing.assert_array_equal(data.X, X)
            np.testing.assert_array_equal(data.y, y)
            np.testing.assert_array_equal(data.row_ids, ids)
            checks.append(dict(n=n, condition=condition, exact_equality=True))
        for trial in range(7):
            order = ("package", "baseline") if trial % 2 == 0 else ("baseline", "package")
            for implementation in order:
                # Trace allocations in a separate run so tracing does not bias timings.
                with tempfile.TemporaryDirectory() as tmp:
                    start = time.perf_counter()
                    task(config, conditions, implementation, Path(tmp))
                    elapsed = time.perf_counter() - start
                with tempfile.TemporaryDirectory() as tmp:
                    tracemalloc.start()
                    task(config, conditions, implementation, Path(tmp))
                    _, peak = tracemalloc.get_traced_memory()
                    tracemalloc.stop()
                records.append(
                    dict(
                        n=n,
                        trial=trial,
                        implementation=implementation,
                        seconds=elapsed,
                        python_peak_bytes=peak,
                    )
                )
    pd.DataFrame(records).to_csv(args.output / "trials.csv", index=False)
    summary = (
        pd.DataFrame(records)
        .groupby(["n", "implementation"])
        .agg(
            median_seconds=("seconds", "median"),
            min_seconds=("seconds", "min"),
            max_seconds=("seconds", "max"),
            median_python_peak_bytes=("python_peak_bytes", "median"),
        )
    )
    summary.to_csv(args.output / "summary.csv")
    metadata = dict(
        platform=platform.platform(),
        processor=platform.processor(),
        python=platform.python_version(),
        numpy=np.__version__,
        pandas=pd.__version__,
        checks=checks,
        conditions=conditions,
        scope="generation, CSV/JSON export, hashes, numerical replay; no clustering",
        sources={
            p.name: hashlib.sha256(p.read_bytes()).hexdigest()
            for p in (Path(__file__), Path(__file__).with_name("paired_baseline.py"))
        },
    )
    (args.output / "manifest.json").write_text(json.dumps(metadata, indent=2) + "\n")
    print(summary.to_string())


if __name__ == "__main__":
    main()
