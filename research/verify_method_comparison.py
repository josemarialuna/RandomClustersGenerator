"""Verify archive hashes, optionally regenerate datasets and audit all partitions."""

import argparse
import hashlib
import json
from pathlib import Path


def verify(directory, deep=False):
    manifest = json.loads((directory / "manifest.json").read_text())
    for name, expected in manifest["files"].items():
        if hashlib.sha256((directory / name).read_bytes()).hexdigest() != expected:
            raise ValueError(f"Artifact changed: {name}")
    if deep:
        root = Path(__file__).resolve().parents[1]
        for name, expected in manifest["sources"].items():
            if hashlib.sha256((root / name).read_bytes()).hexdigest() != expected:
                raise ValueError(f"Use the archived source revision for deep replay: {name}")
        import numpy as np
        import pandas as pd
        from method_comparison import choose, dataset, fingerprint, scores
        from sklearn.metrics import pairwise_distances
        from sklearn.preprocessing import StandardScaler
        from threadpoolctl import threadpool_limits

        fits = pd.read_csv(directory / "fits.csv")
        selected = pd.read_csv(directory / "selections.csv")
        records = pd.read_csv(directory / "datasets.csv")
        partitions = np.load(directory / "partitions.npz", allow_pickle=False)
        assert len(fits) == manifest["counts"]["fits"]
        assert len(selected) == manifest["counts"]["selections"]
        assert len(records) == manifest["counts"]["datasets"]
        with threadpool_limits(limits=1):
            for record in records.itertuples():
                raw, y, _ = dataset(record.true_k, record.replicate, record.sigma, record.q)
                x = StandardScaler().fit_transform(raw)
                assert fingerprint(raw) == record.raw_hash
                assert fingerprint(x) == record.x_hash
                assert fingerprint(y) == record.y_hash
                distances = pairwise_distances(x)
                np.fill_diagonal(distances, 0)
                frame = fits[fits.dataset == record.dataset]
                for row in frame.to_dict("records"):
                    if row["status"] == "failed":
                        continue
                    actual = scores(x, y, partitions[row["partition"]], distances)
                    for metric, value in actual.items():
                        np.testing.assert_allclose(value, row[metric], atol=1e-12, rtol=1e-10)
                for row in selected[selected.dataset == record.dataset].to_dict("records"):
                    candidates = frame[frame.method == row["method"]].to_dict("records")
                    best = choose(candidates, row["criterion"])
                    assert row["available"] == (best is not None)
                    if best:
                        assert row["selected_k"] == best["candidate_k"]
                        assert row["correct"] == (best["candidate_k"] == row["true_k"])
                        np.testing.assert_allclose(row["ari"], best["ari"], atol=1e-12)
                        np.testing.assert_allclose(row["ami"], best["ami"], atol=1e-12)
        print(f"Audited {len(records)} datasets and {len(fits)} candidate records")
    print("Verified method-comparison archive")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("directory", type=Path)
    parser.add_argument("--deep", action="store_true")
    args = parser.parse_args()
    verify(args.directory, args.deep)
