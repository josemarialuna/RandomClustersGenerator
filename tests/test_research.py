import json
from dataclasses import asdict, replace

import numpy as np
import pandas as pd
import pytest

pytest.importorskip("sklearn")
pytest.importorskip("matplotlib")

from random_clusters.research.design import Family, Study  # noqa: E402
from random_clusters.research.report import interval, report, wilson  # noqa: E402
from random_clusters.research.run import run, select_partitions  # noqa: E402


def small_study():
    return Study(
        study_id="test-only",
        master_seed=12345,
        replicates=2,
        clusters=2,
        samples=8,
        features=1,
        standard_deviations=[0.05],
        noise_counts=[0, 1],
        noise_distributions=["uniform", "normal"],
        preprocessing=["raw", "standardized"],
        candidate_k=[2, 3],
        kmeans_n_init=2,
        kmeans_max_iter=300,
    )


def test_paired_signal_labels_noise_prefix_and_grid_order():
    study = replace(small_study(), noise_counts=[0, 2, 8])
    family = Family(study, 0)
    no_noise = family.dataset(0.05, 0, "none")
    uniform = family.dataset(0.05, 8, "uniform")
    normal = family.dataset(0.05, 8, "normal")
    np.testing.assert_array_equal(no_noise, uniform[:, : study.features])
    np.testing.assert_array_equal(no_noise, normal[:, : study.features])
    np.testing.assert_array_equal(family.dataset(0.05, 2, "uniform"), uniform[:, :3])
    smaller_grid = Family(replace(study, noise_counts=[2, 0]), 0)
    np.testing.assert_array_equal(smaller_grid.dataset(0.05, 2, "uniform"), uniform[:, :3])
    np.testing.assert_array_equal(family.labels, smaller_grid.labels)
    np.testing.assert_allclose(
        (family.dataset(0.2, 0, "none") - family.centers[family.labels]) / 0.2,
        (no_noise - family.centers[family.labels]) / 0.05,
    )
    other = Family(study, 1)
    assert not np.array_equal(no_noise, other.dataset(0.05, 0, "none"))


def test_noise_distributions_share_quantiles():
    from scipy.special import ndtr

    family = Family(replace(small_study(), noise_counts=[0, 4]), 0)
    normal = family.dataset(0.05, 4, "normal")[:, 1:]
    uniform = family.dataset(0.05, 4, "uniform")[:, 1:]
    np.testing.assert_allclose(ndtr((normal - 0.5) * np.sqrt(12)), uniform)


def test_selection_does_not_use_truth_and_ties_choose_smaller_k():
    candidates = [
        dict(
            candidate_k=k,
            status="ok",
            silhouette=0.5,
            calinski_harabasz=10,
            davies_bouldin=2,
            ari=ari,
            nmi=ari,
        )
        for k, ari in [(4, 1), (2, 0.2)]
    ]
    selected = select_partitions(candidates, true_k=4)
    assert all(row["selected_k"] == 2 for row in selected)
    assert all(row["ari_regret"] == pytest.approx(0.8) for row in selected)
    assert all(row["correct_k"] == 0 for row in selected)
    candidates[0]["status"] = "failed"
    assert all(row["status"] == "failed" for row in select_partitions(candidates, 4))


def test_uncertainty_and_missing_observations():
    result = interval([1, 2, 3, np.nan])
    assert result["n"] == 3
    assert result["mean"] == 2
    assert result["mcse"] == pytest.approx(1 / np.sqrt(3))
    low, high = wilson(20, 20)
    assert low < 1 and high == pytest.approx(1)
    assert interval([])["n"] == 0


@pytest.mark.parametrize(
    "kwargs",
    [
        {"replicates": 1},
        {"noise_counts": [1]},
        {"candidate_k": [3]},
        {"noise_counts": [0, 0]},
        {"standard_deviations": [float("nan")]},
        {"noise_distributions": ["unknown"]},
        {"preprocessing": ["unknown"]},
    ],
)
def test_reject_invalid_study(kwargs):
    with pytest.raises(ValueError):
        replace(small_study(), **kwargs)


def test_runner_replay_counts_reporting_and_integrity(tmp_path):
    study = small_study()
    config = tmp_path / "config.json"
    config.write_text(json.dumps(asdict(study)), encoding="utf-8")
    protocol = tmp_path / "protocol.md"
    protocol.write_text("Test fixture, not the scientific pilot.", encoding="utf-8")
    first = tmp_path / "first"
    second = tmp_path / "second"
    one = run(study, first, config, protocol)
    two = run(study, second, config, protocol)
    assert one["observed"]["datasets"] == 6
    assert one["observed"]["fits"] == 36
    assert one["observed"]["selections"] == 36
    assert one["observed"]["fit_failures"] == 0
    assert one["observed"] == two["observed"]
    pd.testing.assert_frame_equal(
        pd.read_csv(first / "fits.csv").drop(columns="fit_seconds"),
        pd.read_csv(second / "fits.csv").drop(columns="fit_seconds"),
    )
    assert (first / "datasets.jsonl").read_bytes() == (second / "datasets.jsonl").read_bytes()
    with pytest.raises(FileExistsError):
        run(study, first, config, protocol)
    report(first)
    assert (first / "REPORT.es.md").exists()
    assert (first / "figures/recovery.pdf").exists()
    success = pd.read_csv(first / "k_recovery.csv")
    assert (success.attempted == 2).all()
    assert (success.ci_low <= success.proportion).all()
    with (first / "fits.csv").open("a") as stream:
        stream.write("tampered")
    with pytest.raises(ValueError, match="integrity"):
        report(first)
