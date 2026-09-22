"""Check frozen extension archives, including the source at the recorded commit."""

import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
KINDS = ("interaction", "generalization", "performance", "coverage")


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify(directory, git_sources=False):
    manifest = json.loads((directory / "manifest.json").read_text())
    if manifest["status"] != "complete":
        raise ValueError(f"incomplete archive: {directory}")
    for name, expected in manifest["artifacts"].items():
        if digest(directory / name) != expected:
            raise ValueError(f"artifact changed: {directory / name}")
    for name, expected in manifest["source_sha256"].items():
        if digest(ROOT / name) != expected:
            raise ValueError(f"experimental source changed: {name}")
        if git_sources:
            blob = subprocess.check_output(
                ["git", "show", f"{manifest['source_commit']}:{name}"], cwd=ROOT
            )
            if hashlib.sha256(blob).hexdigest() != expected:
                raise ValueError(f"source differs from frozen commit: {name}")
    if digest(directory / "protocol.md") != manifest["protocol_sha256"]:
        raise ValueError("protocol changed")
    return manifest


def main():
    for kind in KINDS:
        manifest = verify(ROOT / "research/results" / f"extension-{kind}-v1")
        print(f"Verified {kind}: {len(manifest['artifacts'])} artifacts")
    derived = json.loads((ROOT / "paper/extension_manifest.json").read_text())
    for name, expected in derived["files"].items():
        if digest(ROOT / name) != expected:
            raise ValueError(f"derived evidence or input changed: {name}")
    print("Verified extension analyses and input manifests")


if __name__ == "__main__":
    main()
