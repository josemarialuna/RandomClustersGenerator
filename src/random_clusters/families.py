"""Public paired Gaussian families with stable, component-specific random streams.

The legacy generator remains unchanged. This module defines a separate replay
contract, ``paired-gaussian-v1``. Changing sizes or signal dimension creates a
different family and is not covered by the pairing guarantees.
"""

from dataclasses import asdict, dataclass

import numpy as np
import pandas as pd

from .core import _integer, _scale, _seed


@dataclass(frozen=True)
class FamilyConfig:
    """Gaussian family specification.

    ``sizes`` contains positive observations per component. ``centers`` has
    shape (k, p). ``covariances`` has shape (k, p, p), or is omitted for identity
    matrices. Covariances must be finite, symmetric and positive definite.
    Condition ``scale`` multiplies standard deviations, not variances.
    """

    sizes: tuple[int, ...]
    centers: tuple[tuple[float, ...], ...]
    covariances: tuple | None = None
    seed: int = 42
    replicate: int = 0
    shuffle: bool = True

    def __post_init__(self):
        sizes = tuple(self.sizes)
        if not sizes:
            raise ValueError("sizes must contain at least one component")
        for size in sizes:
            _integer("size", size, 1)
        centers = np.asarray(self.centers, dtype=float)
        if centers.ndim != 2 or centers.shape[0] != len(sizes) or centers.shape[1] < 1:
            raise ValueError("centers must have shape (len(sizes), p), p >= 1")
        if not np.isfinite(centers).all():
            raise ValueError("centers must be finite")
        k, p = centers.shape
        cov = (
            np.repeat(np.eye(p)[None], k, axis=0)
            if self.covariances is None
            else np.asarray(self.covariances, dtype=float)
        )
        if cov.shape != (k, p, p) or not np.isfinite(cov).all():
            raise ValueError("covariances must be finite with shape (k, p, p)")
        if not np.allclose(cov, cov.transpose(0, 2, 1), rtol=0, atol=1e-12):
            raise ValueError("covariances must be symmetric")
        cov = (cov + cov.transpose(0, 2, 1)) / 2
        try:
            np.linalg.cholesky(cov)
        except np.linalg.LinAlgError as error:
            raise ValueError("covariances must be positive definite") from error
        _integer("seed", self.seed, 0)
        _integer("replicate", self.replicate, 0)
        if not isinstance(self.shuffle, bool):
            raise ValueError("shuffle must be a boolean")
        object.__setattr__(self, "sizes", tuple(int(x) for x in sizes))
        object.__setattr__(self, "centers", tuple(tuple(x) for x in centers.tolist()))
        object.__setattr__(
            self, "covariances", tuple(tuple(tuple(r) for r in c) for c in cov.tolist())
        )
        object.__setattr__(self, "seed", int(self.seed))
        object.__setattr__(self, "replicate", int(self.replicate))

    @classmethod
    def hypercube(cls, *, clusters=4, samples=100, features=2, seed=42, replicate=0):
        """Choose distinct centers uniformly from {0.25, 0.75}**features.

        This is a new stream convention, not a replay of ``GeneratorConfig``.
        For arbitrary centers or unequal sizes, use the regular constructor.
        """
        for name, value in (("clusters", clusters), ("samples", samples), ("features", features)):
            _integer(name, value, 1)
        _integer("replicate", replicate, 0)
        seed = _seed(seed)
        if (int(clusters) - 1).bit_length() > features:
            raise ValueError("clusters must be <= 2**features")
        rng = _stream(seed, replicate, 0)
        centers, seen = [], set()
        while len(centers) < clusters:
            bits = rng.integers(0, 2, features, dtype=np.int8)
            key = bits.tobytes()
            if key not in seen:
                seen.add(key)
                centers.append(0.25 + 0.5 * bits)
        return cls((samples,) * clusters, centers, seed=seed, replicate=replicate)


@dataclass(frozen=True)
class Condition:
    """Perturbation: nonnegative residual scale and number of nuisance columns.

    Uniform nuisance is U(0,1). Normal nuisance is N(0.5,1/12).
    The laws have equal population moments, not equal sample moments.
    """

    scale: float = 0.1
    noise: int = 0
    distribution: str = "uniform"

    def __post_init__(self):
        _scale("scale", self.scale)
        _integer("noise", self.noise, 0)
        if self.distribution not in ("uniform", "normal"):
            raise ValueError("distribution must be uniform or normal")
        object.__setattr__(self, "scale", float(self.scale))
        object.__setattr__(self, "noise", int(self.noise))


def _stream(seed, replicate, component, index=0):
    return np.random.Generator(
        np.random.PCG64(np.random.SeedSequence(seed, spawn_key=(replicate, component, index)))
    )


@dataclass
class PairedDataset:
    """Feature table, separate evaluation labels, row IDs and replay specification.

    ``X`` never includes labels or IDs. IDs refer to the original component-wise
    ordering and are stable across conditions within the same family.
    """

    X: pd.DataFrame
    y: np.ndarray
    row_ids: np.ndarray
    config: FamilyConfig
    condition: Condition

    @property
    def metadata(self):
        centers = np.asarray(self.config.centers)
        cov = np.asarray(self.config.covariances)
        return {
            "model": "paired-gaussian-v1",
            "family": asdict(self.config),
            "condition": asdict(self.condition),
            "mean_varying_features": np.flatnonzero(np.ptp(centers, axis=0) > 0).tolist(),
            "covariance_varying_features": np.flatnonzero(
                np.any(np.ptp(cov, axis=0) > 0, axis=0)
            ).tolist(),
            "stream_keys": {
                "centers": 0,
                "residuals": 1,
                "rows": 2,
                "uniform_noise": 3,
                "normal_noise": 4,
                "fitting": 5,
            },
        }


class PairedFamily:
    """Generate conditions independently of request order and grid size.

    Separate per-column streams preserve nuisance prefixes when columns are
    added. Normal and uniform noise use independent streams. Both preserve
    signal, labels and row order. Scaling reuses the same Gaussian residuals.
    """

    def __init__(self, config: FamilyConfig):
        self.config = config
        n, p = sum(config.sizes), len(config.centers[0])
        labels = np.repeat(np.arange(len(config.sizes)), config.sizes)
        residuals = _stream(config.seed, config.replicate, 1).standard_normal((n, p))
        factors = np.linalg.cholesky(np.asarray(config.covariances))
        self._residuals = np.einsum("nij,nj->ni", factors[labels], residuals)
        self._labels = labels
        self._order = (
            _stream(config.seed, config.replicate, 2).permutation(n)
            if config.shuffle
            else np.arange(n)
        )

    def dataset(self, condition: Condition = Condition()) -> PairedDataset:
        """Return an independent mutable result without changing family state."""
        config = self.config
        signal = np.asarray(config.centers)[self._labels] + condition.scale * self._residuals
        n, p = signal.shape
        noise = np.empty((n, condition.noise))
        for column in range(condition.noise):
            component = 3 if condition.distribution == "uniform" else 4
            rng = _stream(config.seed, config.replicate, component, column)
            noise[:, column] = (
                rng.random(n) if component == 3 else rng.normal(0.5, 1 / np.sqrt(12), n)
            )
        X = pd.DataFrame(
            np.column_stack((signal, noise))[self._order],
            columns=[f"s{i}" for i in range(p)] + [f"d{i}" for i in range(condition.noise)],
        )
        return PairedDataset(
            X, self._labels[self._order].copy(), self._order.copy(), config, condition
        )

    def fit_seed(self, method: int, candidate: int) -> int:
        """Stable 32-bit fitting seed, shared across conditions for paired fits."""
        _integer("method", method, 0)
        _integer("candidate", candidate, 1)
        sequence = np.random.SeedSequence(
            self.config.seed, spawn_key=(self.config.replicate, 5, int(method), int(candidate))
        )
        return int(sequence.generate_state(1)[0])
