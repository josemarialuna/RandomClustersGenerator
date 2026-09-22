"""Verify manuscript evidence checksums using only Python's standard library."""

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAPER = ROOT / "paper"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    manifest = json.loads((PAPER / "evidence_manifest.json").read_text())
    if digest(PAPER / "build_evidence.py") != manifest["script_sha256"]:
        raise ValueError("evidence builder changed since the recorded analysis")
    for name, expected in manifest["source_manifests"].items():
        path = ROOT / "research" / "results" / f"validation-{name}-v1" / "manifest.json"
        if digest(path) != expected:
            raise ValueError(f"source manifest changed: {name}")
    for name, expected in manifest["artifacts"].items():
        if digest(PAPER / name) != expected:
            raise ValueError(f"manuscript artifact changed: {name}")
    print(f"Verified {len(manifest['artifacts'])} manuscript evidence artifacts.")


if __name__ == "__main__":
    main()
