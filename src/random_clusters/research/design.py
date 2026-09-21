"""Paired datasets: changing noise never changes signal, labels or row order."""

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from scipy.spatial.distance import pdist
from scipy.special import ndtr, ndtri

from random_clusters import GeneratorConfig, generate


@dataclass(frozen=True)
class Study:
    study_id: str
    master_seed: int
    replicates: int
    clusters: int
    samples: int
    features: int
    standard_deviations: list[float]
    noise_counts: list[int]
    noise_distributions: list[str]
    preprocessing: list[str]
    candidate_k: list[int]
    kmeans_n_init: int
    kmeans_max_iter: int

    def __post_init__(self):
        GeneratorConfig(
            clusters=self.clusters,
            samples=self.samples,
            features=self.features,
            seed=self.master_seed,
        )
        for name in ("replicates", "kmeans_n_init", "kmeans_max_iter"):
            value = getattr(self, name)
            if type(value) is not int or value < 1:
                raise ValueError(f"{name} must be a positive integer")
        if self.replicates < 2 or self.clusters < 2 or self.samples < 2:
            raise ValueError("research requires >=2 replicates, clusters and samples per cluster")
        for name in (
            "standard_deviations",
            "noise_counts",
            "noise_distributions",
            "preprocessing",
            "candidate_k",
        ):
            values = getattr(self, name)
            if not values or len(set(values)) != len(values):
                raise ValueError(f"{name} must be nonempty and unique")
        if any(
            type(v) not in (int, float) or not np.isfinite(v) or v <= 0
            for v in self.standard_deviations
        ):
            raise ValueError("standard_deviations must be finite and >0")
        if (
            any(type(v) is not int or v < 0 for v in self.noise_counts)
            or 0 not in self.noise_counts
        ):
            raise ValueError("noise_counts must be nonnegative integers including 0")
        if not set(self.noise_distributions) <= {"uniform", "normal"}:
            raise ValueError("unknown noise distribution")
        if not set(self.preprocessing) <= {"raw", "standardized"}:
            raise ValueError("unknown preprocessing")
        if (
            any(
                type(k) is not int or not 2 <= k < self.clusters * self.samples
                for k in self.candidate_k
            )
            or self.clusters not in self.candidate_k
        ):
            raise ValueError("candidate_k must include generating k and satisfy 2 <= k < n")

    @classmethod
    def read(cls, path: Path):
        return cls(**json.loads(path.read_text(encoding="utf-8")))

    @property
    def dataset_count(self):
        return (
            self.replicates
            * len(self.standard_deviations)
            * (1 + (len(self.noise_counts) - 1) * len(self.noise_distributions))
        )


def stream(study: Study, replicate: int, component: int, index: int = 0):
    """Explicit stream keys stay stable if experiment ordering/grid changes."""
    sequence = np.random.SeedSequence(
        [study.master_seed, replicate, study.clusters, study.features, study.samples],
        spawn_key=(component, index),
    )
    return np.random.Generator(np.random.PCG64(sequence))


def fingerprint(array: np.ndarray) -> str:
    array = np.asarray(array, dtype="<f8", order="C")
    return hashlib.sha256(str(array.shape).encode() + array.tobytes()).hexdigest()


class Family:
    """One independent replicate with paired conditions and explicit components."""

    def __init__(self, study: Study, replicate: int):
        self.study = study
        self.replicate = replicate
        center_seed = int(stream(study, replicate, 0).integers(0, 2**63))
        self.centers = generate(
            GeneratorConfig(
                clusters=study.clusters,
                samples=1,
                features=study.features,
                noise=0,
                std=0,
                seed=center_seed,
                shuffle=False,
            )
        ).centers
        n = study.clusters * study.samples
        permutation = stream(study, replicate, 2).permutation(n)
        self.labels = np.repeat(np.arange(study.clusters), study.samples)[permutation]
        self.residuals = stream(study, replicate, 1).standard_normal((n, study.features))[
            permutation
        ]
        self.noise = {}
        max_noise = max(study.noise_counts)
        for distribution in study.noise_distributions:
            columns = []
            for column in range(max_noise):
                uniform = stream(study, replicate, 3, column).random(n)[permutation]
                if distribution == "normal":
                    uniform = 0.5 + ndtri(
                        np.clip(uniform, np.nextafter(0.0, 1.0), np.nextafter(1.0, 0.0))
                    ) / np.sqrt(12)
                columns.append(uniform)
            self.noise[distribution] = np.column_stack(columns) if columns else np.empty((n, 0))

    def dataset(self, std: float, noise: int, distribution: str):
        signal = self.centers[self.labels] + std * self.residuals
        if noise == 0:
            return signal
        return np.column_stack((signal, self.noise[distribution][:, :noise]))

    def diagnostics(self, data: np.ndarray, std: float):
        distance = float(pdist(self.centers).min())
        return {
            "data_sha256": fingerprint(data),
            "signal_sha256": fingerprint(data[:, : self.study.features]),
            "labels_sha256": fingerprint(self.labels),
            "centers": self.centers.tolist(),
            "minimum_center_distance": distance,
            "separation_over_std": distance / std,
            "closest_pair_bayes_error": float(ndtr(-distance / (2 * std))),
            "varying_signal_features": np.flatnonzero(np.ptp(self.centers, axis=0) > 0).tolist(),
            "empirical_means": data.mean(axis=0).tolist(),
            "empirical_variances": data.var(axis=0, ddof=1).tolist(),
        }

    def algorithm_seed(self, k: int):
        return int(stream(self.study, self.replicate, 4, k).integers(0, 2**32 - 1))
