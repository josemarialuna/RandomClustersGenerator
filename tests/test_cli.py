import hashlib
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from random_clusters import GeneratorConfig, generate
from random_clusters.cli import main
from random_clusters.io import read_batch, save_dataset


def test_numpy_parameters_can_be_saved(tmp_path):
    config = GeneratorConfig(clusters=np.int64(2), samples=np.int64(3), std=np.float32(0.05))
    path = tmp_path / "numpy.csv"
    save_dataset(generate(config), path)
    document = json.loads(path.with_suffix(".json").read_text())
    assert document["parameters"]["clusters"] == 2
    assert document["rows"] == 6


def test_batch_cannot_overwrite_its_input(tmp_path):
    path = tmp_path / "dataset_001.csv"
    contents = "clusters,samples,features,noise,std,seed\n2,2,1,0,0,42\n"
    path.write_text(contents)
    with pytest.raises(SystemExit):
        main(["batch", str(path), "--output", str(tmp_path), "--overwrite"])
    assert path.read_text() == contents


def test_csv_metadata_and_replay(tmp_path):
    path = tmp_path / "folder with spaces" / "experiment.csv"
    assert main(["generate", "--seed", "42", "--output", str(path)]) == 0
    metadata = json.loads(path.with_suffix(".json").read_text())
    assert metadata["rows"] == 400
    assert metadata["parameters"]["seed"] == 42
    assert metadata["csv_sha256"] == hashlib.sha256(path.read_bytes()).hexdigest()
    assert metadata["rng"] == "PCG64"
    assert len(metadata["centers"]) == 4
    assert metadata["varying_signal_features"] == ["s0", "s1"]
    replay = tmp_path / "replay.csv"
    save_dataset(generate(GeneratorConfig(**metadata["parameters"])), replay)
    assert replay.read_bytes() == path.read_bytes()


def test_existing_outputs_are_preserved(tmp_path):
    path = tmp_path / "output.csv"
    main(["generate", "--seed", "42", "--output", str(path)])
    original = path.read_bytes()
    with pytest.raises(SystemExit) as error:
        main(["generate", "--seed", "43", "--output", str(path)])
    assert error.value.code == 2
    assert path.read_bytes() == original
    main(["generate", "--seed", "43", "--output", str(path), "--overwrite"])
    assert path.read_bytes() != original
    path.unlink()
    with pytest.raises(SystemExit):
        main(["generate", "--output", str(path)])
    assert not path.exists()


def test_batch_and_flags(tmp_path):
    config = Path(__file__).resolve().parents[1] / "examples" / "experiments.csv"
    assert main(["batch", str(config), "--output", str(tmp_path), "--ordered", "--no-labels"]) == 0
    assert len(list(tmp_path.glob("*.csv"))) == 3
    assert len(list(tmp_path.glob("*.json"))) == 3
    assert pd.read_csv(tmp_path / "dataset_003.csv").shape == (600, 5)
    assert "cluster" not in pd.read_csv(tmp_path / "dataset_001.csv")


@pytest.mark.parametrize("bad_row", ["5,10,2,0,0.05,42", "2,10,2,0,nan,42", "2,10"])
def test_batch_validates_all_rows_before_writing(tmp_path, bad_row, capsys):
    config = tmp_path / "config.csv"
    config.write_text("clusters,samples,features,noise,std,seed\n2,10,2,0,0.05,42\n" + bad_row)
    output = tmp_path / "results"
    with pytest.raises(SystemExit) as error:
        main(["batch", str(config), "--output", str(output)])
    assert error.value.code == 2
    assert "row 3" in capsys.readouterr().err
    assert not output.exists()


def test_batch_checks_all_output_collisions(tmp_path):
    config = Path(__file__).resolve().parents[1] / "examples" / "experiments.csv"
    (tmp_path / "dataset_003.json").write_text("preserve me")
    with pytest.raises(SystemExit):
        main(["batch", str(config), "--output", str(tmp_path)])
    assert not (tmp_path / "dataset_001.csv").exists()
    assert (tmp_path / "dataset_003.json").read_text() == "preserve me"


def test_semicolon_batch(tmp_path):
    config = tmp_path / "config.csv"
    config.write_text("clusters;samples;features;noise;std;seed\n2;10;2;0;0.05;42\n")
    assert read_batch(config)[0].samples == 10


@pytest.mark.parametrize(
    "contents",
    [
        "",
        "clusters,samples,features,noise,std,seed\n",
        "clusters,unknown\n2,3\n",
        "clusters,samples,features,noise,std,seed,seed\n2,10,2,0,0.05,42,42\n",
    ],
)
def test_invalid_batch_header_and_empty_batch(tmp_path, contents):
    config = tmp_path / "config.csv"
    config.write_text(contents)
    with pytest.raises(ValueError):
        read_batch(config)


def test_add_noise_cli_and_input_protection(tmp_path):
    source = tmp_path / "input.csv"
    source.write_text("s0,d0,cluster\n0.25,0.7,0\n0.75,0.2,1\n")
    original = source.read_bytes()
    output = tmp_path / "output.csv"
    main(["add-noise", str(source), "--count", "2", "--seed", "42", "--output", str(output)])
    assert source.read_bytes() == original
    pd.testing.assert_frame_equal(pd.read_csv(output)[["s0", "d0", "cluster"]], pd.read_csv(source))
    assert list(pd.read_csv(output)) == ["s0", "d0", "cluster", "d1", "d2"]
    metadata = json.loads(output.with_suffix(".json").read_text())
    assert metadata["input_sha256"] == hashlib.sha256(original).hexdigest()
    with pytest.raises(SystemExit):
        main(["add-noise", str(source), "--count", "1", "--output", str(source), "--overwrite"])
    assert source.read_bytes() == original


def test_invalid_cli_is_readable_and_writes_nothing(tmp_path, capsys):
    output = tmp_path / "invalid.csv"
    with pytest.raises(SystemExit) as error:
        main(["generate", "--clusters", "5", "--features", "2", "--output", str(output)])
    assert error.value.code == 2
    assert "clusters must be <= 2**features" in capsys.readouterr().err
    assert not output.exists()


def test_installed_module_entrypoint(tmp_path):
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "random_clusters",
            "generate",
            "--seed",
            "42",
            "--samples",
            "2",
            "--output",
            str(tmp_path / "cli.csv"),
        ],
        capture_output=True,
        text=True,
        check=True,
        cwd=tmp_path,
    )
    assert "8 rows x 5 columns" in completed.stdout
    assert (tmp_path / "cli.json").exists()
