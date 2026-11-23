"""Verify packaged paired evidence without extracting or refitting."""

import argparse
import hashlib
import json
import zipfile
from pathlib import Path


def verify(directory):
    directory = Path(directory)
    manifest = json.loads((directory / "manifest.json").read_text())
    for name, expected in manifest["files"].items():
        if hashlib.sha256((directory / name).read_bytes()).hexdigest() != expected:
            raise ValueError(f"archive artifact changed: {name}")
    counts = {"fits": 0, "selections": 0}
    with zipfile.ZipFile(directory / "experiments.zip") as archive:
        for scenario in ("balanced", "unequal", "anisotropic"):
            record = json.loads(archive.read(f"{scenario}/manifest.json"))
            for name, expected in record["files"].items():
                if hashlib.sha256(archive.read(f"{scenario}/{name}")).hexdigest() != expected:
                    raise ValueError(f"experiment artifact changed: {scenario}/{name}")
            for key in counts:
                counts[key] += record[key]
    print(f"Verified packaged evidence: {counts}")
    return counts


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    verify(parser.parse_args().directory)
