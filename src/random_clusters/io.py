"""CSV configuration and traceable output bundles."""

import csv
import hashlib
import json
import platform
from dataclasses import asdict
from pathlib import Path

import numpy as np
import pandas as pd

from . import __version__
from .core import Dataset, GeneratorConfig


def read_batch(path: Path) -> list[GeneratorConfig]:
    """Read strict comma- or semicolon-separated experiment configurations."""
    required = {"clusters", "samples", "features", "noise", "std", "seed"}
    with path.open(encoding="utf-8-sig", newline="") as stream:
        header = stream.readline()
        stream.seek(0)
        reader = csv.DictReader(stream, delimiter=";" if ";" in header else ",")
        if reader.fieldnames is None or set(reader.fieldnames) != required:
            raise ValueError("batch columns must be: clusters,samples,features,noise,std,seed")
        if len(reader.fieldnames) != len(required):
            raise ValueError("batch header contains duplicate columns")
        configs = []
        for line, row in enumerate(reader, start=2):
            try:
                if None in row or any(value is None for value in row.values()):
                    raise ValueError("wrong number of fields")
                configs.append(
                    GeneratorConfig(
                        **{key: int(row[key]) for key in required - {"std"}},
                        std=float(row["std"]),
                    )
                )
            except (ValueError, TypeError) as error:
                raise ValueError(f"{path}: row {line}: {error}") from error
    if not configs:
        raise ValueError("batch configuration must contain at least one experiment")
    return configs


def check_output(path: Path, overwrite: bool = False) -> tuple[Path, Path]:
    """Validate both output paths before any data is written."""
    if path.suffix.lower() != ".csv":
        raise ValueError("output must have a .csv extension")
    metadata = path.with_suffix(".json")
    for target in (path, metadata):
        if target.exists() and (not overwrite or not target.is_file()):
            raise FileExistsError(f"output already exists: {target} (use --overwrite to replace)")
    return path, metadata


def write_table(
    data: pd.DataFrame, path: Path, metadata: dict, *, overwrite: bool = False
) -> tuple[Path, Path]:
    """Save a CSV and a JSON sidecar containing its hash and software versions."""
    path, sidecar = check_output(path, overwrite)
    path.parent.mkdir(parents=True, exist_ok=True)
    # Stable newlines and a fixed float representation make file comparisons useful.
    data.to_csv(path, index=False, float_format="%.17g", lineterminator="\n")
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    document = {
        "schema_version": 1,
        "software": {
            "random_clusters_generator": __version__,
            "python": platform.python_version(),
            "numpy": np.__version__,
            "pandas": pd.__version__,
        },
        "rng": "PCG64",
        "rows": len(data),
        "columns": list(data.columns),
        "csv_sha256": digest.hexdigest(),
        **metadata,
    }
    sidecar.write_text(json.dumps(document, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    return path, sidecar


def save_dataset(dataset: Dataset, path: Path, *, overwrite: bool = False) -> tuple[Path, Path]:
    """Save the table together with the actual centers and replay parameters."""
    return write_table(
        dataset.data,
        path,
        {
            "operation": "generate",
            "model": "binary-hypercube-gaussian-v1",
            "parameters": asdict(dataset.config),
            "centers": dataset.centers.tolist(),
            "varying_signal_features": [
                f"s{i}"
                for i in range(dataset.config.features)
                if np.unique(dataset.centers[:, i]).size > 1
            ],
        },
        overwrite=overwrite,
    )
