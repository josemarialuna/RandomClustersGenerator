"""Local operational comparison; no claims about human productivity."""

import gc
import itertools
import tempfile
import time
import tracemalloc
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.datasets import make_blobs
from threadpoolctl import threadpool_info, threadpool_limits

from random_clusters import GeneratorConfig, add_noise, generate
from random_clusters.research.design import Family

from .models import primary_study, rng
from .run import archive_finish, archive_start, write_json


def reference(config):
    """Explicit baseline for the same distribution, with its own random streams."""
    generator = np.random.default_rng(config.seed)
    seen, centers = set(), []
    while len(centers) < config.clusters:
        bits = generator.integers(0, 2, size=config.features, dtype=np.int8)
        if bits.tobytes() not in seen:
            seen.add(bits.tobytes())
            centers.append(0.25 + 0.5 * bits)
    values, labels = make_blobs(
        n_samples=[config.samples] * config.clusters,
        centers=np.asarray(centers),
        cluster_std=config.std,
        shuffle=False,
        random_state=int(generator.integers(0, 2**32 - 1)),
    )
    noise = generator.random((len(labels), config.noise))
    columns = [f"s{i}" for i in range(config.features)] + [f"d{i}" for i in range(config.noise)]
    result = pd.DataFrame(np.column_stack((values, noise)), columns=columns)
    result["cluster"] = labels
    return result.iloc[generator.permutation(len(result))].reset_index(drop=True)


def contract(table, config):
    assert table.shape == (config.samples * config.clusters, config.features + config.noise + 1)
    assert table.columns.tolist() == (
        [f"s{i}" for i in range(config.features)]
        + [f"d{i}" for i in range(config.noise)]
        + ["cluster"]
    )
    assert table.cluster.value_counts().sort_index().tolist() == [config.samples] * config.clusters
    assert np.isfinite(table.to_numpy()).all()
    if config.noise:
        noise = table[[f"d{i}" for i in range(config.noise)]].to_numpy()
        assert ((noise >= 0) & (noise < 1)).all()


def workflow_checks():
    config = GeneratorConfig(seed=7, samples=10)
    outputs = {}
    for name, method in {"package": lambda c: generate(c).data, "reference": reference}.items():
        table = method(config)
        contract(table, config)
        pd.testing.assert_frame_equal(table, method(config))
        outputs[name] = "schema, balanced labels, finite values, noise bounds and replay pass"
    table = generate(config).data
    augmented = add_noise(table, 2, seed=8)
    pd.testing.assert_frame_equal(table, augmented[table.columns])
    family = Family(primary_study(), 0)
    a, b = family.dataset(0.05, 1, "uniform"), family.dataset(0.05, 2, "uniform")
    np.testing.assert_array_equal(a, b[:, :3])
    outputs["package_add_noise"] = "all prior columns and row order preserved"
    outputs["paired_research"] = "signal and nested nuisance prefix exactly preserved"
    return outputs


def performance_run(output):
    manifest = archive_start(output, "performance")
    started = time.perf_counter()
    methods = {"package": lambda config: generate(config).data, "make_blobs_reference": reference}
    rows = []
    with threadpool_limits(limits=1):
        manifest["threadpools"] = [
            {key: (Path(value).name if key == "filepath" else value) for key, value in pool.items()}
            for pool in threadpool_info()
        ]
        write_json(output / "workflow_checks.json", workflow_checks())
        for method in methods.values():
            method(GeneratorConfig(seed=1, samples=250))
        for cell, (n, p, q) in enumerate(itertools.product([1000, 10000, 100000], [2, 8], [2, 16])):
            for repetition in range(5):
                seed = int(rng(2026092303, cell, repetition).integers(0, 2**32 - 1))
                config = GeneratorConfig(clusters=4, samples=n // 4, features=p, noise=q, seed=seed)
                order = list(methods)
                rng(2026092303, cell, repetition, 99).shuffle(order)
                for position, name in enumerate(order):
                    gc.collect()
                    wall, cpu = time.perf_counter(), time.process_time()
                    table = methods[name](config)
                    cpu_seconds = time.process_time() - cpu
                    wall_seconds = time.perf_counter() - wall
                    contract(table, config)
                    with tempfile.TemporaryDirectory(dir=output) as temporary:
                        target = Path(temporary) / "dataset.csv"
                        start = time.perf_counter()
                        table.to_csv(target, index=False, float_format="%.17g", lineterminator="\n")
                        export_seconds = time.perf_counter() - start
                        size = target.stat().st_size
                    del table
                    gc.collect()
                    tracemalloc.start()
                    allocated = methods[name](config)
                    _, peak = tracemalloc.get_traced_memory()
                    tracemalloc.stop()
                    del allocated
                    rows.append(
                        {
                            "cell": cell,
                            "n": n,
                            "p": p,
                            "q": q,
                            "repetition": repetition,
                            "seed": seed,
                            "order": position,
                            "method": name,
                            "generation_wall_seconds": wall_seconds,
                            "generation_cpu_seconds": cpu_seconds,
                            "csv_seconds": export_seconds,
                            "csv_bytes": size,
                            "tracked_peak_bytes": peak,
                            "status": "ok",
                        }
                    )
            print(f"performance: {cell + 1}/12 cells", flush=True)
    pd.DataFrame(rows).to_csv(
        output / "trials.csv", index=False, float_format="%.17g", lineterminator="\n"
    )
    manifest["trials"] = len(rows)
    assert len(rows) == 120
    archive_finish(output, manifest, started)
