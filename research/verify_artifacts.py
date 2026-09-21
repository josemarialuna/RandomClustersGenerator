"""Verify an archived pilot's hashes without installing research dependencies."""

import argparse
import hashlib
import json
from pathlib import Path


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify(directory):
    manifest_path = directory / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    analysis = json.loads((directory / "analysis_manifest.json").read_text(encoding="utf-8"))
    if manifest["status"] != "complete":
        raise ValueError("incomplete run")
    if digest(manifest_path) != analysis["source_manifest_sha256"]:
        raise ValueError("manifest integrity mismatch")
    count = 0
    for entries in (manifest["output_sha256"], analysis["artifacts"]):
        for name, expected in entries.items():
            if digest(directory / name) != expected:
                raise ValueError(f"artifact integrity mismatch: {name}")
            count += 1
    for name in ("datasets", "fits", "selections"):
        if manifest["observed"][name] != manifest[f"expected_{name}"]:
            raise ValueError(f"incomplete {name}")
    return count


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    args = parser.parse_args()
    print(f"Verified {verify(args.directory)} archived artifacts.")
