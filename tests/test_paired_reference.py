"""Cross-check the sampler against a separate implementation of its specification."""

import json
from pathlib import Path

import numpy as np
import pytest

from random_clusters import Condition, FamilyConfig, PairedFamily
from research.paired_baseline import sample


@pytest.mark.parametrize("scenario", ["balanced", "unequal", "anisotropic"])
def test_independent_reference(scenario):
    root = Path(__file__).resolve().parents[1]
    spec = json.loads((root / "examples" / "paired" / f"{scenario}.json").read_text())
    config = FamilyConfig(**spec["family"])
    family = PairedFamily(config)
    for condition in spec["conditions"]:
        actual = family.dataset(Condition(**condition))
        X, y, ids = sample(spec["family"], condition)
        np.testing.assert_allclose(actual.X, X, rtol=0, atol=1e-15)
        np.testing.assert_array_equal(actual.y, y)
        np.testing.assert_array_equal(actual.row_ids, ids)
