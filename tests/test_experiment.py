import json

import pytest

from random_clusters.experiment import audit, run, select


def test_end_to_end_and_corruption(tmp_path):
    spec = dict(
        family=dict(sizes=[15, 20], centers=[[0, 0], [1, 1]], seed=7),
        replicates=2,
        conditions=[dict(scale=0.1, noise=0), dict(scale=0.1, noise=2)],
        methods=["kmeans", "ward", "average", "gmm"],
        candidates=[2, 3],
        preprocessing=["raw", "standardized"],
        n_init=2,
        max_iter=100,
    )
    output = tmp_path / "run"
    manifest = run(spec, output)
    assert manifest["fits"] == 64
    assert manifest["selections"] == 96
    assert audit(output, deep=True)["deep"]
    with pytest.raises(FileExistsError):
        run(spec, output)
    (output / "selections.json").write_text("[]")
    with pytest.raises(ValueError, match="integrity"):
        audit(output)


def test_selection_ties_and_failed_grid():
    rows = [dict(k=k, status="ok", silhouette=0.5, ch=10, db=1, ari=0.3, ami=0.2) for k in (3, 2)]
    assert all(r["k"] == 2 for r in select(rows))
    rows[0]["status"] = "failed"
    assert all(
        r == {"index": i, "status": "unavailable"}
        for r, i in zip(select(rows), ("silhouette", "ch", "db"))
    )


def test_validation_precedes_output(tmp_path):
    with pytest.raises(ValueError):
        run(json.loads('{"family": {}}'), tmp_path / "bad")
    assert not (tmp_path / "bad").exists()
