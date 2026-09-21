"""The single implementation of the data-generating model."""

from dataclasses import dataclass, replace
from numbers import Integral, Real
from secrets import randbits

import numpy as np
import pandas as pd


def _integer(name: str, value: int, minimum: int) -> None:
    if isinstance(value, bool) or not isinstance(value, Integral) or value < minimum:
        raise ValueError(f"{name} must be an integer >= {minimum}")


def _scale(name: str, value: float) -> None:
    if (
        isinstance(value, bool)
        or not isinstance(value, Real)
        or not np.isfinite(value)
        or value < 0
    ):
        raise ValueError(f"{name} must be a finite number >= 0")


def _seed(seed: int | None) -> int:
    if seed is None:
        return randbits(64)
    _integer("seed", seed, 0)
    return int(seed)


@dataclass(frozen=True)
class GeneratorConfig:
    """Parameters for balanced spherical Gaussian clusters plus uniform noise.

    ``samples`` is the number of observations PER cluster. Signal coordinates
    have means in {0.25, 0.75}; not every coordinate necessarily varies between
    the selected centers. A zero standard deviation is allowed.
    """

    clusters: int = 4
    samples: int = 100
    features: int = 2
    noise: int = 2
    std: float = 0.05
    seed: int | None = None
    shuffle: bool = True
    labels: bool = True

    def __post_init__(self) -> None:
        for name in ("clusters", "samples", "features"):
            _integer(name, getattr(self, name), 1)
        _integer("noise", self.noise, 0)
        _scale("std", self.std)
        # Avoid constructing 2**features for a potentially very wide dataset.
        if (int(self.clusters) - 1).bit_length() > self.features:
            raise ValueError("clusters must be <= 2**features (distinct binary centers)")
        if self.seed is not None:
            _seed(self.seed)
        for name in ("shuffle", "labels"):
            if not isinstance(getattr(self, name), bool):
                raise ValueError(f"{name} must be a boolean")
        # NumPy scalar inputs are common in experiments; keep metadata JSON-safe.
        for name in ("clusters", "samples", "features", "noise"):
            object.__setattr__(self, name, int(getattr(self, name)))
        object.__setattr__(self, "std", float(self.std))
        if self.seed is not None:
            object.__setattr__(self, "seed", int(self.seed))


@dataclass
class Dataset:
    """Generated table, centers in label order, and parameters with resolved seed."""

    data: pd.DataFrame
    centers: np.ndarray
    config: GeneratorConfig


def generate(config: GeneratorConfig | None = None) -> Dataset:
    """Generate a dataset in memory using one local PCG64 random generator.

    Centers are sampled uniformly without replacement from binary hypercube
    corners. The routine never changes NumPy's global random state.
    """
    config = GeneratorConfig() if config is None else config
    config = replace(config, seed=_seed(config.seed))
    rng = np.random.Generator(np.random.PCG64(config.seed))
    seen: set[bytes] = set()
    centers = []
    while len(centers) < config.clusters:
        bits = rng.integers(0, 2, size=config.features, dtype=np.int8)
        key = bits.tobytes()
        if key not in seen:
            seen.add(key)
            centers.append(0.25 + bits * 0.5)
    centers = np.asarray(centers)
    labels = np.repeat(np.arange(config.clusters), config.samples)
    signal = rng.normal(centers[labels], config.std)
    noise = rng.random((len(labels), config.noise))
    columns = [f"s{i}" for i in range(config.features)]
    columns += [f"d{i}" for i in range(config.noise)]
    data = pd.DataFrame(np.column_stack((signal, noise)), columns=columns)
    if config.labels:
        data["cluster"] = labels
    if config.shuffle:
        data = data.iloc[rng.permutation(len(data))].reset_index(drop=True)
    return Dataset(data, centers, config)


def add_noise(
    data: pd.DataFrame,
    count: int,
    *,
    seed: int | None = None,
    distribution: str = "uniform",
    mean: float = 1.0,
    std: float = 0.05,
) -> pd.DataFrame:
    """Return a copy with new dN columns, preserving all existing columns/rows.

    Uniform noise is in [0, 1). Normal noise uses ``mean`` and ``std``.
    """
    _integer("count", count, 1)
    _scale("std", std)
    if isinstance(mean, bool) or not isinstance(mean, Real) or not np.isfinite(mean):
        raise ValueError("mean must be a finite number")
    if distribution not in ("uniform", "normal"):
        raise ValueError("distribution must be 'uniform' or 'normal'")
    rng = np.random.Generator(np.random.PCG64(_seed(seed)))
    result = data.copy()
    index = 0
    for _ in range(count):
        while f"d{index}" in result.columns:
            index += 1
        values = (
            rng.random(len(data)) if distribution == "uniform" else rng.normal(mean, std, len(data))
        )
        result[f"d{index}"] = values
        index += 1
    return result
