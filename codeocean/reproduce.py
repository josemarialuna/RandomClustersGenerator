"""Rebuild the manuscript outputs and execute a fresh clustering example."""

import argparse
import hashlib
import json
import os
import platform
import subprocess
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ARCHIVE = ROOT / "research/results/paired-workflow-v1"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--full-refit",
        action="store_true",
        help="Additionally refit all 24,000 candidates in a new archive.",
    )
    args = parser.parse_args()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    env = dict(
        os.environ,
        PYTHONPATH=str(ROOT / "src"),
        MPLBACKEND="Agg",
        OMP_NUM_THREADS="1",
        OPENBLAS_NUM_THREADS="1",
        MKL_NUM_THREADS="1",
    )

    def execute(*command):
        print("Running:", *map(str, command), flush=True)
        subprocess.run([sys.executable, *map(str, command)], cwd=ROOT, env=env, check=True)

    execute("research/verify_paired_archive.py", ARCHIVE)
    extracted = output / "archived-experiments"
    extracted.mkdir()
    with zipfile.ZipFile(ARCHIVE / "experiments.zip") as archive:
        for name in archive.namelist():
            if not (extracted / name).resolve().is_relative_to(extracted):
                raise ValueError("Archive member escapes extraction directory")
        archive.extractall(extracted)

    for scenario in ("balanced", "unequal", "anisotropic"):
        execute("-m", "random_clusters.experiment", extracted / scenario, "--audit", "--deep")
    execute(ARCHIVE / "analysis/summarize_paired.py", extracted, output / "figures-and-tables")

    # Compare numerical tables rather than PDF bytes (rendering metadata can vary).
    import pandas as pd

    for name in ("known_count.csv", "selection.csv", "paired_differences.csv", "fit_status.csv"):
        pd.testing.assert_frame_equal(
            pd.read_csv(output / "figures-and-tables" / name),
            pd.read_csv(ARCHIVE / "summary" / name),
            check_exact=False,
            rtol=1e-10,
            atol=1e-12,
        )
    execute(
        "-m",
        "random_clusters.experiment",
        "examples/paired/quickstart.json",
        output / "fresh-example",
    )
    execute("-m", "random_clusters.experiment", output / "fresh-example", "--audit", "--deep")
    execute("research/paired_operational.py", output / "new-operational-measurements")
    if args.full_refit:
        for scenario in ("balanced", "unequal", "anisotropic"):
            execute(
                "-m",
                "random_clusters.experiment",
                extracted / scenario / "config.json",
                output / "refitted-experiments" / scenario,
            )
        execute(
            ARCHIVE / "analysis/summarize_paired.py",
            output / "refitted-experiments",
            output / "refitted-figures-and-tables",
        )
    metadata = {
        "status": "complete",
        "python": platform.python_version(),
        "platform": platform.platform(),
        "scope": (
            "Archive integrity, full deep audit, manuscript tables/figures, "
            "fresh example and new timings"
        ),
        "full_refit": args.full_refit,
        "original_experiment_commit": "9e9560f52a995e53ceee0b61134f149edc102773",
        "driver_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    }
    (output / "verification.json").write_text(
        json.dumps(metadata, indent=2) + "\n", encoding="utf-8"
    )
    with (output / "environment.txt").open("w", encoding="utf-8") as handle:
        subprocess.run([sys.executable, "-m", "pip", "freeze"], stdout=handle, check=True)
    print(json.dumps(metadata, indent=2), flush=True)


if __name__ == "__main__":
    main()
