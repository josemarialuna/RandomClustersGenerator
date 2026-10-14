"""Structural support of the crossed endpoint, independent of observed fits."""

import itertools

import pandas as pd
import pytest

pytest.importorskip("scipy")
from paper.analyze_diagnostics import nested_interaction


def test_all_nested_outcomes_have_trinomial_interaction():
    possible = [(0, 0), (1, 0), (1, 1)]
    rows = [a + b for a, b in itertools.product(possible, repeat=2)]
    table = pd.DataFrame(
        rows, columns=pd.MultiIndex.from_tuples([(10, 8), (10, 16), (100, 8), (100, 16)])
    )
    assert set(nested_interaction(table)) == {-1, 0, 1}
    table.loc[0, (10, 16)] = 1
    with pytest.raises(ValueError, match="nesting invariant"):
        nested_interaction(table)
