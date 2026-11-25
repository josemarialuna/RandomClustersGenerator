"""Build the scoped Code Ocean upload from tracked source and paired evidence."""

import argparse
import hashlib
import json
import shutil
import subprocess
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    paths = subprocess.check_output(["git", "ls-files", "-z"], cwd=ROOT).decode().split("\0")
    selected = [
        p
        for p in paths
        if p
        and (
            p.startswith(("src/", "examples/paired/", "research/results/paired-workflow-v1/"))
            or p
            in {
                "pyproject.toml",
                "README.md",
                "LICENSE",
                "LICENSE.txt",
                "research/verify_paired_archive.py",
                "research/paired_operational.py",
                "research/paired_baseline.py",
                "research/PAIRED_WORKFLOW_PROTOCOL.md",
                "research/environment-paired-workflow.txt",
            }
        )
    ]
    selected += [
        p.relative_to(ROOT).as_posix()
        for p in (ROOT / "codeocean").iterdir()
        if p.is_file() and p.suffix != ".zip"
    ]
    evidence_prefix = "research/results/paired-workflow-v1/"
    with (
        zipfile.ZipFile(args.output / "source.zip", "w", zipfile.ZIP_DEFLATED) as archive,
        zipfile.ZipFile(args.output / "evidence.zip", "w", zipfile.ZIP_DEFLATED) as evidence,
    ):
        for name in sorted(set(selected)):
            if name.startswith(evidence_prefix):
                evidence.write(ROOT / name, name.removeprefix(evidence_prefix))
            else:
                archive.write(ROOT / name, name)
    shutil.copyfile(ROOT / "codeocean/capsule-run", args.output / "run")
    shutil.copyfile(ROOT / "codeocean/README.md", args.output / "README.md")
    manifest = {
        name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
        for name in sorted(set(selected))
    }
    (args.output / "source-manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    print(args.output.resolve())


if __name__ == "__main__":
    main()
