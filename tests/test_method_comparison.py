"""Selection must not inspect external validity or silently omit failed candidates."""

import pytest

pytest.importorskip("sklearn")
from research.method_comparison import choose, dataset


def test_selection_direction_ties_and_failed_candidates():
    rows = [
        dict(candidate_k=k, status="ok", silhouette=1, ch=k, db=k, ari=100 - k) for k in range(2, 9)
    ]
    assert choose(rows, "silhouette")["candidate_k"] == 2
    assert choose(rows, "ch")["candidate_k"] == 8
    assert choose(rows, "db")["candidate_k"] == 2
    rows[-1]["status"] = "nonconverged"
    assert choose(rows, "ch") is None
    assert choose(rows[:-1], "ch") is None


def test_shared_signal_and_nuisance_prefix():
    import numpy as np

    full, y, _ = dataset(4, 0, 0.15, 8)
    short, labels, _ = dataset(4, 0, 0.15, 2)
    np.testing.assert_array_equal(full[:, :4], short)
    np.testing.assert_array_equal(y, labels)
