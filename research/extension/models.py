"""Independent factorial construction and inspectable candidate partitions."""

import itertools
import warnings
from dataclasses import replace

import numpy as np
from scipy.spatial.distance import pdist
from scipy.special import ndtri
from sklearn.cluster import KMeans
from sklearn.metrics import mutual_info_score, pairwise_distances
from sklearn.preprocessing import StandardScaler

from random_clusters import GeneratorConfig, generate
from random_clusters.research.design import Family, Study, fingerprint
from random_clusters.research.run import scores


def rng(seed, *keys):
    return np.random.default_rng(np.random.SeedSequence([seed, *keys]))


def primary_study():
    return Study(
        study_id="crossed-independent-v1",
        master_seed=2026092301,
        replicates=100,
        clusters=4,
        samples=100,
        features=2,
        standard_deviations=[0.05],
        noise_counts=[0, 2],
        noise_distributions=["uniform", "normal"],
        preprocessing=["standardized"],
        candidate_k=list(range(2, 17)),
        kmeans_n_init=10,
        kmeans_max_iter=300,
    )


def cells():
    return [
        dict(cell=i, k=k, p=p, n=n, separation=sep, geometry=geometry)
        for i, (k, p, n, sep, geometry) in enumerate(
            itertools.product([3, 4], [3, 6], [240, 480], [3, 8], ["cube", "random", "anisotropic"])
        )
    ]


def factorial_data(cell, replicate):
    k, p, n = cell["k"], cell["p"], cell["n"]
    key = (cell["cell"], replicate)
    center_rng = rng(2026092302, *key, 0)
    if cell["geometry"] == "cube":
        seed = int(center_rng.integers(0, 2**32 - 1))
        centers = generate(
            GeneratorConfig(
                clusters=k, samples=1, features=p, noise=0, std=0, seed=seed, shuffle=False
            )
        ).centers
    else:
        centers = center_rng.normal(size=(k, p))
    covariance = np.eye(p) * 0.01
    if cell["geometry"] == "anisotropic":
        rotation, _ = np.linalg.qr(rng(2026092302, *key, 5).normal(size=(p, p)))
        eigenvalues = np.geomspace(1, 9, p)
        eigenvalues *= p * 0.01 / eigenvalues.sum()
        covariance = (rotation * eigenvalues) @ rotation.T
    inverse = np.linalg.inv(covariance)
    centers = centers - centers.mean(axis=0)
    minimum = pdist(centers, metric="mahalanobis", VI=inverse).min()
    centers = centers * (cell["separation"] / minimum) + 0.5
    labels = np.repeat(np.arange(k), n // k)
    residuals = rng(2026092302, *key, 1).normal(size=(n, p))
    signal = centers[labels] + residuals @ np.linalg.cholesky(covariance).T
    uniform = rng(2026092302, *key, 3).random((n, 2))
    normal = 0.5 + ndtri(
        np.clip(uniform, np.nextafter(0.0, 1.0), np.nextafter(1.0, 0.0))
    ) / np.sqrt(12)
    permutation = rng(2026092302, *key, 2).permutation(n)
    signal, labels = signal[permutation], labels[permutation]
    data = {
        "none": signal,
        "uniform": np.column_stack((signal, uniform[permutation])),
        "normal": np.column_stack((signal, normal[permutation])),
    }
    diagnostic = {
        **cell,
        "replicate": replicate,
        "centers": centers.tolist(),
        "covariance": covariance.tolist(),
        "minimum_mahalanobis": float(pdist(centers, metric="mahalanobis", VI=inverse).min()),
        "minimum_euclidean": float(pdist(centers).min()),
        "varying_signal_features": int((np.ptp(centers, axis=0) > 1e-12).sum()),
        "signal_sha256": fingerprint(signal),
        "labels_sha256": fingerprint(labels),
    }
    return data, labels, diagnostic


def partition_diagnostics(data, truth, predicted, p):
    total = ((data - data.mean(axis=0)) ** 2).sum(axis=0)
    within = np.zeros(data.shape[1])
    truth_within = np.zeros(data.shape[1])
    refined_within = np.zeros(data.shape[1])
    for value in np.unique(predicted):
        subset = data[predicted == value]
        within += ((subset - subset.mean(axis=0)) ** 2).sum(axis=0)
    conditional_information = np.zeros(data.shape[1] - p)
    conditional_entropy = 0.0
    contingency = []
    for group in np.unique(truth):
        mask = truth == group
        subset, assigned = data[mask], predicted[mask]
        truth_within += ((subset - subset.mean(axis=0)) ** 2).sum(axis=0)
        weight = mask.mean()
        conditional_entropy += weight * mutual_info_score(assigned, assigned)
        for j in range(data.shape[1] - p):
            conditional_information[j] += weight * mutual_info_score(
                assigned, subset[:, p + j] >= 0.5
            )
        counts = []
        for value in np.unique(predicted):
            part = subset[assigned == value]
            counts.append(len(part))
            if len(part):
                refined_within += ((part - part.mean(axis=0)) ** 2).sum(axis=0)
        contingency.append(counts)
    explained = 1 - np.divide(
        refined_within, truth_within, out=np.zeros_like(total), where=truth_within > 0
    )
    between_fraction = 1 - np.divide(within, total, out=np.zeros_like(total), where=total > 0)
    return {
        "between_total_by_feature": between_fraction.tolist(),
        "within_truth_explained_by_feature": explained.tolist(),
        "signal_within_truth_explained": float(explained[:p].mean()),
        "noise_within_truth_explained": float(explained[p:].mean()) if len(explained) > p else None,
        "conditional_noise_information": conditional_information.tolist(),
        "normalized_conditional_noise_information": (
            conditional_information / conditional_entropy
            if conditional_entropy > 0
            else np.zeros_like(conditional_information)
        ).tolist(),
        "contingency": contingency,
    }


def fit_candidates(data, truth, p, candidates, starts, seed_for_k, inspect):
    values = StandardScaler().fit_transform(data)
    distances = pairwise_distances(values)
    np.fill_diagonal(distances, 0)
    fits, labels, mechanisms = [], {}, []
    for budget in starts:
        for k in candidates:
            model = KMeans(
                n_clusters=k,
                n_init=budget,
                init="k-means++",
                algorithm="lloyd",
                tol=1e-4,
                max_iter=300,
                random_state=seed_for_k(k),
            )
            with warnings.catch_warnings(record=True) as caught:
                warnings.simplefilter("always")
                predicted = model.fit_predict(values)
            status = "ok" if len(np.unique(predicted)) == k and model.n_iter_ < 300 else "failed"
            metrics = scores(values, distances, truth, predicted)
            row = {
                "candidate_k": k,
                "starts": budget,
                "status": status,
                "warnings": " | ".join(str(w.message) for w in caught),
                "inertia": float(model.inertia_),
                "iterations": int(model.n_iter_),
                "label_sha256": fingerprint(predicted),
                **metrics,
            }
            fits.append(row)
            labels[f"s{budget}_k{k}"] = predicted.astype(np.int16)
            if inspect:
                mechanisms.append(
                    {
                        "starts": budget,
                        "candidate_k": k,
                        **partition_diagnostics(data, truth, predicted, p),
                    }
                )
    return fits, labels, mechanisms


def selections(fits, true_k, ranges):
    output = []
    for budget in sorted({r["starts"] for r in fits}):
        known = next(r for r in fits if r["starts"] == budget and r["candidate_k"] == true_k)
        for upper in ranges:
            subset = [r for r in fits if r["starts"] == budget and r["candidate_k"] <= upper]
            for metric in ["silhouette", "calinski_harabasz", "davies_bouldin"]:
                sign = 1 if metric == "davies_bouldin" else -1
                chosen = min(subset, key=lambda r: (sign * r[metric], r["candidate_k"]))
                output.append(
                    {
                        "starts": budget,
                        "upper": upper,
                        "criterion": metric,
                        "selected_k": chosen["candidate_k"],
                        "correct_k": int(chosen["candidate_k"] == true_k),
                        "ari": chosen["ari"],
                        "known_ari": known["ari"],
                        "selection_difference": chosen["ari"] - known["ari"],
                        "status": "ok" if all(r["status"] == "ok" for r in subset) else "failed",
                    }
                )
    return output


def interaction_data(replicate):
    study = primary_study()
    family = Family(study, replicate)
    data = {law: family.dataset(0.05, 2, law) for law in study.noise_distributions}
    return data, family.labels, family, replace(study, replicates=100)
