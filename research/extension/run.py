"""Run one frozen revision study and archive every completed family."""

import argparse
import hashlib
import importlib.metadata
import json
import platform
import shutil
import subprocess
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

import numpy as np
import pandas as pd
from threadpoolctl import threadpool_limits

from random_clusters.research.design import fingerprint

from .inference import bounded_mean, exact_coverage, paired_bounds
from .models import cells, factorial_data, fit_candidates, interaction_data, rng, selections

ROOT = Path(__file__).resolve().parents[2]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def archive_start(output, kind):
    output.mkdir(parents=True, exist_ok=False)
    sources = sorted((ROOT / "research" / "extension").glob("*.py"))
    sources += sorted((ROOT / "src" / "random_clusters").rglob("*.py"))
    protocol = ROOT / "research" / "EXTENSION_PROTOCOL.md"
    shutil.copyfile(protocol, output / "protocol.md")
    result = {
        "kind": kind,
        "status": "running",
        "protocol_sha256": digest(protocol),
        "source_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
        "git_dirty": bool(subprocess.check_output(["git", "status", "--porcelain"], text=True)),
        "source_sha256": {p.relative_to(ROOT).as_posix(): digest(p) for p in sources},
        "python": platform.python_version(),
        "platform": platform.platform(),
        "versions": {
            name: importlib.metadata.version(name)
            for name in ["numpy", "pandas", "scipy", "scikit-learn", "threadpoolctl"]
        },
        "thread_limit": 1,
    }
    write_json(output / "manifest.json", result)
    return result


def write_json(path, value):
    path.write_text(
        json.dumps(value, indent=2, allow_nan=False) + "\n", encoding="utf-8", newline="\n"
    )


def archive_finish(output, manifest, started):
    manifest.update(status="complete", elapsed_seconds=time.perf_counter() - started)
    manifest["artifacts"] = {
        p.relative_to(output).as_posix(): digest(p)
        for p in sorted(output.rglob("*"))
        if p.is_file() and p.name != "manifest.json"
    }
    write_json(output / "manifest.json", manifest)


def work(task):
    kind, cell, replicate, label_directory = task
    with threadpool_limits(limits=1):
        if kind == "interaction":
            data, truth, family, _ = interaction_data(replicate)
            key = f"r{replicate:03d}"
            diagnostic = {
                "replicate": replicate,
                "k": 4,
                "p": 2,
                "n": 400,
                **family.diagnostics(data["uniform"], 0.05),
            }
            candidates, starts, ranges = range(2, 17), [10, 100], [8, 16]
            seed_for_k = family.algorithm_seed
        else:
            data, truth, diagnostic = factorial_data(cell, replicate)
            key = f"c{cell['cell']:02d}_r{replicate:03d}"
            candidates, starts, ranges = range(2, 9), [10], [8]

            def seed_for_k(k):
                return int(rng(2026092302, cell["cell"], replicate, 4, k).integers(0, 2**32 - 1))

        all_fits, all_selections, all_mechanisms, datasets, labels = [], [], [], [], {}
        for law, values in data.items():
            identity = {"family": key, "distribution": law, "replicate": replicate}
            if cell is not None:
                identity.update(cell)
            fit, assigned, mechanisms = fit_candidates(
                values,
                truth,
                diagnostic["p"],
                candidates,
                starts,
                seed_for_k,
                inspect=kind == "interaction",
            )
            all_fits.extend({**identity, **row} for row in fit)
            all_selections.extend(
                {**identity, **row} for row in selections(fit, diagnostic["k"], ranges)
            )
            all_mechanisms.extend({**identity, **row} for row in mechanisms)
            datasets.append({**identity, **diagnostic, "data_sha256": fingerprint(values)})
            labels.update({f"{law}_{name}": value for name, value in assigned.items()})
        labels["truth"] = truth.astype(np.int16)
        np.savez_compressed(Path(label_directory) / f"{key}.npz", **labels)
        return {
            "fits": all_fits,
            "selections": all_selections,
            "mechanisms": all_mechanisms,
            "datasets": datasets,
        }


def model_run(kind, output, workers):
    manifest = archive_start(output, kind)
    (output / "labels").mkdir()
    started = time.perf_counter()
    if kind == "interaction":
        tasks = [(kind, None, r, str(output / "labels")) for r in range(100)]
        expected = {"families": 100, "datasets": 200, "fits": 6000, "selections": 2400}
    else:
        tasks = [(kind, cell, r, str(output / "labels")) for cell in cells() for r in range(30)]
        write_json(output / "design.json", cells())
        expected = {"families": 1440, "datasets": 4320, "fits": 30240, "selections": 12960}
    manifest["expected"] = expected
    manifest["workers"] = workers
    write_json(output / "manifest.json", manifest)
    handles = {
        name: (output / f"{name}.jsonl").open("w", encoding="utf-8", newline="\n")
        for name in ["fits", "selections", "mechanisms", "datasets"]
    }
    counts = {name: 0 for name in handles}
    failures = warnings = 0
    try:
        with ProcessPoolExecutor(max_workers=workers) as pool:
            futures = [pool.submit(work, task) for task in tasks]
            for i, future in enumerate(as_completed(futures), 1):
                result = future.result()
                for name, rows in result.items():
                    for row in rows:
                        handles[name].write(json.dumps(row, allow_nan=False) + "\n")
                    handles[name].flush()
                    counts[name] += len(rows)
                failures += sum(r["status"] != "ok" for r in result["fits"])
                warnings += sum(bool(r["warnings"]) for r in result["fits"])
                if i % 10 == 0 or i == len(tasks):
                    print(
                        f"{kind}: {i}/{len(tasks)} families; {time.perf_counter() - started:.1f}s",
                        flush=True,
                    )
    finally:
        for handle in handles.values():
            handle.close()
    for name in ["datasets", "fits", "selections"]:
        if counts[name] != expected[name]:
            raise AssertionError(f"incomplete {name}")
    manifest.update(observed=counts, fit_failures=failures, fit_warnings=warnings)
    if failures:
        write_json(output / "manifest.json", manifest)
        raise ValueError("failed fits retained; requires explicit review")
    archive_finish(output, manifest, started)


def coverage_run(output):
    manifest = archive_start(output, "coverage")
    started = time.perf_counter()
    frame = pd.DataFrame(exact_coverage())
    frame.to_csv(output / "coverage.csv", index=False, float_format="%.17g", lineterminator="\n")
    old = pd.read_csv(ROOT / "research/results/validation-primary-v1/selections.csv")
    old = old[
        (old.noise == 2) & (old.preprocessing == "standardized") & (old.criterion == "silhouette")
    ]
    paired = old.pivot(index="replicate", columns="distribution", values="correct_k")
    differences = paired.normal - paired.uniform
    low, high = paired_bounds(
        int((differences == 1).sum()), int((differences == -1).sum()), len(differences)
    )
    result = {
        **bounded_mean(differences, -1, 1),
        "positive": int((differences == 1).sum()),
        "negative": int((differences == -1).sum()),
        "cp_low": float(low),
        "cp_high": float(high),
    }
    write_json(output / "primary_reanalysis.json", result)
    manifest["source_primary_selections_sha256"] = digest(
        ROOT / "research/results/validation-primary-v1/selections.csv"
    )
    manifest["coverage_rows"] = len(frame)
    archive_finish(output, manifest, started)
    print(frame.groupby(["families", "method"]).coverage.min().to_string(), flush=True)
    print(json.dumps(result), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "kind", choices=["interaction", "generalization", "coverage", "performance"]
    )
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--workers", type=int, default=2)
    args = parser.parse_args()
    if args.kind == "coverage":
        coverage_run(args.output)
    elif args.kind == "performance":
        from .performance import performance_run

        performance_run(args.output)
    else:
        model_run(args.kind, args.output, args.workers)


if __name__ == "__main__":
    main()
