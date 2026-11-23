from dataclasses import replace

import numpy as np
import pandas as pd
import pytest

from random_clusters import Condition, FamilyConfig, PairedFamily
from random_clusters.bundles import replay_paired, save_paired, verify_paired


def config(**kwargs):
    return FamilyConfig(sizes=(31, 69), centers=((0, 0), (2, 0)), **kwargs)


def test_noise_prefix_and_order_independence():
    family = PairedFamily(config())
    large = family.dataset(Condition(noise=8))
    small = family.dataset(Condition(noise=2))
    normal = family.dataset(Condition(noise=2, distribution="normal"))
    pd.testing.assert_frame_equal(large.X[small.X.columns], small.X)
    pd.testing.assert_frame_equal(normal.X[["s0", "s1"]], small.X[["s0", "s1"]])
    np.testing.assert_array_equal(large.y, normal.y)
    np.testing.assert_array_equal(large.row_ids, normal.row_ids)
    assert not np.array_equal(normal.X.d0, small.X.d0)
    assert np.bincount(small.y).tolist() == [31, 69]
    assert small.metadata["mean_varying_features"] == [0]
    small.X.iloc[0, 0] = -999
    pd.testing.assert_frame_equal(family.dataset(Condition(noise=8)).X, large.X)


def test_scale_reuses_residuals():
    family = PairedFamily(config())
    a = family.dataset(Condition(scale=0.1, noise=2))
    b = family.dataset(Condition(scale=0.2, noise=2))
    centers = np.asarray(a.config.centers)[a.y]
    np.testing.assert_allclose(
        b.X[["s0", "s1"]] - centers, 2 * (a.X[["s0", "s1"]] - centers), atol=1e-15
    )
    pd.testing.assert_frame_equal(a.X[["d0", "d1"]], b.X[["d0", "d1"]])


def test_covariance_distribution_and_noninformative_means():
    cov = (((1, 0.7), (0.7, 2)), ((2, -0.4), (-0.4, 1)))
    spec = FamilyConfig((40000, 40000), ((0, 0), (0, 0)), covariances=cov)
    data = PairedFamily(spec).dataset(Condition(scale=1))
    for group in range(2):
        np.testing.assert_allclose(
            np.cov(data.X[data.y == group].to_numpy().T), cov[group], atol=0.045
        )
    assert data.metadata["mean_varying_features"] == []
    assert data.metadata["covariance_varying_features"] == [0, 1]


def test_replay_integrity_and_tampering(tmp_path):
    dataset = PairedFamily(config()).dataset(Condition(noise=2))
    pd.testing.assert_frame_equal(replay_paired(dataset.metadata).X, dataset.X)
    path = tmp_path / "example.csv"
    save_paired(dataset, path)
    assert verify_paired(path, regenerate=True) == {"integrity": True, "regenerated": True}
    with pytest.raises(FileExistsError):
        save_paired(dataset, path)
    path.write_text(path.read_text() + "\n")
    with pytest.raises(ValueError, match="integrity"):
        verify_paired(path)


def test_stream_isolation_and_fitting_seeds():
    a = PairedFamily(config())
    b = PairedFamily(replace(config(), replicate=1))
    assert a.fit_seed(0, 2) == PairedFamily(config()).fit_seed(0, 2)
    assert a.fit_seed(0, 2) != a.fit_seed(1, 2)
    assert a.fit_seed(0, 2) != b.fit_seed(0, 2)
    assert not a.dataset().X.equals(b.dataset().X)
    for distribution in ("uniform", "normal"):
        short = a.dataset(Condition(noise=1, distribution=distribution))
        long = a.dataset(Condition(noise=4, distribution=distribution))
        np.testing.assert_array_equal(short.X.d0, long.X.d0)


@pytest.mark.parametrize(
    "changes",
    [
        {"sizes": (0, 3)},
        {"sizes": (True, 3)},
        {"centers": ((0,),)},
        {"seed": -1},
        {"replicate": 0.5},
        {"shuffle": "yes"},
        {"centers": ((0, float("nan")), (1, 2))},
        {"covariances": (((1, 2), (0, 1)), ((1, 0), (0, 1)))},
        {"covariances": (((1, 2), (2, 1)), ((1, 0), (0, 1)))},
    ],
)
def test_invalid_family(changes):
    with pytest.raises(ValueError):
        replace(config(), **changes)


def test_hypercube_and_defensive_config_copy():
    spec = FamilyConfig.hypercube(clusters=8, features=3, samples=2)
    assert len(np.unique(spec.centers, axis=0)) == 8
    centers = [[0, 0], [1, 1]]
    cfg = FamilyConfig((2, 3), centers)
    centers[0][0] = 999
    assert cfg.centers[0][0] == 0


@pytest.mark.parametrize(
    "kwargs", [{"noise": -1}, {"scale": float("nan")}, {"distribution": "other"}]
)
def test_invalid_conditions(kwargs):
    with pytest.raises(ValueError):
        Condition(**kwargs)
