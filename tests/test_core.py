import numpy as np
import pandas as pd
import pytest

from random_clusters import GeneratorConfig, add_noise, generate


def test_shape_labels_centers_and_noise():
    result = generate(GeneratorConfig(clusters=6, samples=17, features=3, noise=2, std=0, seed=7))
    assert result.data.shape == (102, 6)
    assert list(result.data) == ["s0", "s1", "s2", "d0", "d1", "cluster"]
    assert result.data.cluster.value_counts().to_dict() == dict.fromkeys(range(6), 17)
    assert len(np.unique(result.centers, axis=0)) == 6
    np.testing.assert_array_equal(
        result.data[["s0", "s1", "s2"]], result.centers[result.data.cluster]
    )
    assert result.data[["d0", "d1"]].ge(0).all().all()
    assert result.data[["d0", "d1"]].lt(1).all().all()


def test_replay_and_different_seeds():
    first = generate(GeneratorConfig(seed=42))
    second = generate(GeneratorConfig(seed=42))
    pd.testing.assert_frame_equal(first.data, second.data)
    np.testing.assert_array_equal(first.centers, second.centers)
    assert not first.data.equals(generate(GeneratorConfig(seed=43)).data)
    unseeded = generate()
    assert isinstance(unseeded.config.seed, int)
    pd.testing.assert_frame_equal(unseeded.data, generate(unseeded.config).data)


def test_full_hypercube_and_wide_features():
    full = generate(GeneratorConfig(clusters=16, features=4, samples=1, seed=42))
    assert len(np.unique(full.centers, axis=0)) == 16
    wide = generate(GeneratorConfig(clusters=2, features=100, samples=1, seed=42))
    assert wide.centers.shape == (2, 100)


def test_ordered_unlabelled_and_zero_noise():
    config = GeneratorConfig(clusters=2, features=1, samples=3, noise=0, seed=1, shuffle=False)
    result = generate(config)
    assert result.data.cluster.tolist() == [0, 0, 0, 1, 1, 1]
    assert result.data.shape == (6, 2)
    result = generate(GeneratorConfig(clusters=1, features=1, noise=0, labels=False, samples=1))
    assert list(result.data) == ["s0"]
    assert result.data.shape == (1, 1)


def test_gaussian_statistics():
    result = generate(GeneratorConfig(clusters=2, features=1, samples=20000, std=0.1, seed=42))
    for label, group in result.data.groupby("cluster"):
        assert abs(group.s0.mean() - result.centers[label, 0]) < 0.004
        assert abs(group.s0.std() - 0.1) < 0.003
        assert abs(group.d0.mean() - 0.5) < 0.01


def test_global_rng_is_untouched():
    before = np.random.get_state()
    generate(GeneratorConfig(seed=2))
    after = np.random.get_state()
    assert before[0] == after[0]
    np.testing.assert_array_equal(before[1], after[1])
    assert before[2:] == after[2:]


@pytest.mark.parametrize(
    "kwargs",
    [
        {"clusters": 0},
        {"clusters": 5, "features": 2},
        {"features": 0},
        {"samples": -1},
        {"noise": -1},
        {"samples": 1.5},
        {"clusters": True},
        {"std": -0.1},
        {"std": float("nan")},
        {"std": float("inf")},
        {"seed": -1},
        {"seed": 1.5},
        {"seed": True},
        {"labels": "false"},
        {"shuffle": 1},
    ],
)
def test_invalid_parameters(kwargs):
    with pytest.raises(ValueError):
        GeneratorConfig(**kwargs)


def test_noise_preserves_input_columns_and_index():
    source = pd.DataFrame({"s0": [0.2, 0.8], "d0": [9, 8], "cluster": [0, 1]}, index=[4, 7])
    original = source.copy(deep=True)
    output = add_noise(source, 2, seed=42)
    pd.testing.assert_frame_equal(source, original)
    pd.testing.assert_frame_equal(output[source.columns], original)
    assert list(output) == ["s0", "d0", "cluster", "d1", "d2"]
    pd.testing.assert_frame_equal(output, add_noise(source, 2, seed=42))
    normal = add_noise(source, 1, seed=1, distribution="normal", mean=5, std=0)
    assert normal.d1.tolist() == [5, 5]


@pytest.mark.parametrize(
    "kwargs",
    [
        {"count": 0},
        {"count": -1},
        {"count": True},
        {"count": 1, "std": -1},
        {"count": 1, "distribution": "other"},
        {"count": 1, "mean": float("nan")},
    ],
)
def test_invalid_noise(kwargs):
    with pytest.raises(ValueError):
        add_noise(pd.DataFrame({"a": [1]}), **kwargs)
