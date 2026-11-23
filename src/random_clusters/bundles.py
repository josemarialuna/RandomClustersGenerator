"""Export, integrity checking and regeneration of public paired datasets."""

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

from .families import Condition, FamilyConfig, PairedDataset, PairedFamily
from .io import write_table


def save_paired(dataset: PairedDataset, path: Path, *, overwrite=False):
    """Write CSV + replay JSON. Labels and row_id are evaluation-only columns."""
    table = dataset.X.copy()
    table["row_id"] = dataset.row_ids
    table["cluster"] = dataset.y
    return write_table(table, Path(path), dataset.metadata, overwrite=overwrite)


def replay_paired(metadata: dict) -> PairedDataset:
    """Regenerate from a JSON sidecar, without reading saved observation values."""
    if metadata.get("model") != "paired-gaussian-v1":
        raise ValueError("unsupported paired model")
    return PairedFamily(FamilyConfig(**metadata["family"])).dataset(
        Condition(**metadata["condition"])
    )


def verify_paired(path: Path, *, regenerate=False) -> dict:
    """Check saved bytes and optionally exact numerical replay in this environment.

    Raises ValueError on mismatches. Hash agreement is an integrity check, not
    statistical validation. Cross-platform numerical replay is not promised.
    """
    path = Path(path)
    metadata = json.loads(path.with_suffix(".json").read_text(encoding="utf-8"))
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    if digest != metadata["csv_sha256"]:
        raise ValueError("CSV integrity mismatch")
    result = {"integrity": True, "regenerated": False}
    if regenerate:
        replay = replay_paired(metadata)
        saved = pd.read_csv(path, float_precision="round_trip")
        expected_columns = list(replay.X) + ["row_id", "cluster"]
        if list(saved) != expected_columns:
            raise ValueError("column schema mismatch")
        for actual, expected in (
            (saved[replay.X.columns].to_numpy(), replay.X.to_numpy()),
            (saved.cluster.to_numpy(), replay.y),
            (saved.row_id.to_numpy(), replay.row_ids),
        ):
            if not np.array_equal(actual, expected):
                raise ValueError("numerical replay mismatch")
        result["regenerated"] = True
    return result
