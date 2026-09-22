"""Statistical and generative invariants for the prospective extension."""

import numpy as np
import pytest

pytest.importorskip("scipy")
pytest.importorskip("sklearn")

from random_clusters import GeneratorConfig
from research.extension.inference import bounded_mean, paired_bounds
from research.extension.models import cells, factorial_data, partition_diagnostics, selections
from research.extension.performance import contract, reference


def test_factorial_controls_and_pairing():
    assert len(cells()) == 48
    for cell in cells():
        data, labels, diagnostics = factorial_data(cell, 9999)
        assert diagnostics["minimum_mahalanobis"] == pytest.approx(cell["separation"])
        covariance = np.array(diagnostics["covariance"])
        assert np.trace(covariance) == pytest.approx(cell["p"] * 0.01)
        assert np.linalg.eigvalsh(covariance).min() > 0
        np.testing.assert_array_equal(data["none"], data["normal"][:, : cell["p"]])
        np.testing.assert_array_equal(data["none"], data["uniform"][:, : cell["p"]])
        assert np.bincount(labels).tolist() == [cell["n"] // cell["k"]] * cell["k"]
        np.testing.assert_array_equal(data["normal"], factorial_data(cell, 9999)[0]["normal"])


def test_finite_sample_bounds_do_not_collapse_at_no_discordance():
    low, high = paired_bounds(0, 0, 50)
    assert low < 0 < high
    positive = paired_bounds(50, 0, 50)
    assert positive[0] < 1 and positive[1] == 1
    original = bounded_mean(np.ones(50), -1, 1)
    assert original["t_low"] == original["t_high"] == 1
    assert original["hoeffding_low"] < 1


def test_perfect_partition_explains_no_within_truth_variation():
    data = np.array([[0.0, 0.1], [0.1, 0.9], [1.0, 0.2], [1.1, 0.8]])
    truth = np.array([0, 0, 1, 1])
    result = partition_diagnostics(data, truth, truth, 1)
    np.testing.assert_allclose(result["within_truth_explained_by_feature"], 0)
    np.testing.assert_allclose(result["normalized_conditional_noise_information"], 0)
    refined = partition_diagnostics(data, truth, np.arange(4), 1)
    np.testing.assert_allclose(refined["within_truth_explained_by_feature"], 1)


def test_range_selection_uses_same_candidates_and_direction():
    fits = [
        {
            "starts": 10,
            "candidate_k": k,
            "ari": 0.5,
            "status": "ok",
            "silhouette": k,
            "calinski_harabasz": k,
            "davies_bouldin": k,
        }
        for k in range(2, 10)
    ]
    result = selections(fits, 4, [8, 9])
    assert [r["selected_k"] for r in result] == [8, 8, 2, 9, 9, 2]


def test_reference_distribution_contract():
    config = GeneratorConfig(clusters=3, samples=8, features=3, noise=2, seed=5)
    contract(reference(config), config)
