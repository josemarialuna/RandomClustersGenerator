"""Author-side checks for the independent-use case. Not a participant solution."""

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from random_clusters import FamilyConfig
from random_clusters.experiment import audit


def check_design(spec):
    actual = FamilyConfig(**spec["family"])
    expected = FamilyConfig(
        sizes=(20, 40, 60, 80),
        centers=((0, 0), (0, 1), (1, 0), (1, 1)),
        seed=20261123,
    )
    if actual != expected:
        raise ValueError("Family differs from the participant task")
    required = dict(
        replicates=3,
        methods=["kmeans", "ward"],
        candidates=[3, 4, 5],
        preprocessing=["raw", "standardized"],
        n_init=10,
        max_iter=300,
    )
    for name, value in required.items():
        if spec[name] != value:
            raise ValueError(f"Unexpected design value: {name}")
    conditions = spec["conditions"]
    if len(conditions) != 3:
        raise ValueError("Expected three conditions")
    for row, noise in zip(conditions, (0, 4, 8)):
        if (
            row.get("scale") != 0.1
            or row.get("noise") != noise
            or row.get("distribution", "uniform") != "uniform"
        ):
            raise ValueError("Unexpected perturbation condition")


def check(archive, output):
    archive, output = Path(archive), Path(output)
    spec = json.loads((archive / "config.json").read_text())
    check_design(spec)
    result = audit(archive, deep=True)
    if result["fits"] != 108 or result["selections"] != 108:
        raise ValueError("Unexpected candidate/selection counts")
    if len(list((archive / "datasets").glob("*.csv"))) != 9:
        raise ValueError("Expected nine datasets")
    for replicate in range(3):
        tables = [
            pd.read_csv(
                archive / "datasets" / f"family-{replicate:04d}-condition-{ci:03d}.csv",
                float_precision="round_trip",
            )
            for ci in range(3)
        ]
        for table, noise in zip(tables, (0, 4, 8)):
            assert table.shape == (200, 2 + noise + 2)
            assert table.cluster.value_counts().sort_index().tolist() == [20, 40, 60, 80]
            assert sorted(table.row_id) == list(range(200))
            pd.testing.assert_frame_equal(table[tables[0].columns], tables[0])
        pd.testing.assert_frame_equal(tables[2][tables[1].columns], tables[1])

    fits = pd.DataFrame(json.loads((archive / "fits.json").read_text()))
    fits["noise"] = fits.condition.map(lambda ci: spec["conditions"][ci]["noise"])
    rows = []
    for keys, cell in fits[fits.k == 4].groupby(["noise", "method", "preprocessing"]):
        valid = cell[cell.status == "ok"]
        rows.append(
            dict(
                zip(("noise", "method", "preprocessing"), keys),
                mean_ari=valid.ari.mean() if len(valid) else np.nan,
                mean_ami=valid.ami.mean() if len(valid) else np.nan,
                valid=len(valid),
                total=len(cell),
            )
        )
    selection = pd.DataFrame(json.loads((archive / "selections.json").read_text()))
    selection = selection[
        (selection.condition == 1)
        & (selection.method == "kmeans")
        & (selection.preprocessing == "standardized")
    ].reindex(columns=["replicate", "index", "status", "k", "ari", "ami"])
    output.mkdir(parents=True, exist_ok=False)
    pd.DataFrame(rows).to_csv(output / "resumen-referencia.csv", index=False)
    selection.to_csv(output / "seleccion-referencia.csv", index=False)
    result["pairing"] = True
    result["note"] = (
        "Author-side audit only. Participant independence requires separate assessment."
    )
    (output / "verificacion.json").write_text(json.dumps(result, indent=2) + "\n")
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", type=Path)
    parser.add_argument(
        "--output", required=True, type=Path, help="New author-side output directory"
    )
    args = parser.parse_args()
    print(json.dumps(check(args.archive, args.output), indent=2))
