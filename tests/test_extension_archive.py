"""Archived scientific evidence must reject partial runs and changed bytes."""

import json

import pytest

from research.verify_extension import digest, verify


def test_extension_archive_rejects_tampering_and_incomplete_status(tmp_path):
    protocol = tmp_path / "protocol.md"
    protocol.write_text("Frozen protocol\n", encoding="utf-8")
    data = tmp_path / "data.csv"
    data.write_text("value\n1\n", encoding="utf-8")
    manifest = {
        "status": "complete",
        "artifacts": {"data.csv": digest(data)},
        "source_sha256": {},
        "protocol_sha256": digest(protocol),
    }
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps(manifest), encoding="utf-8")
    verify(tmp_path)
    data.write_text("value\n2\n", encoding="utf-8")
    with pytest.raises(ValueError, match="artifact changed"):
        verify(tmp_path)
    manifest["status"] = "running"
    path.write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(ValueError, match="incomplete archive"):
        verify(tmp_path)
