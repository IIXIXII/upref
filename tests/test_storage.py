from __future__ import annotations

import os
from pathlib import Path

import pytest

from upref import _storage
from upref.errors import ConfigFormatError, ConfigReadError, ConfigWriteError


def test_load_missing_file_returns_empty_mapping(tmp_path: Path) -> None:
    assert _storage.load_yaml(tmp_path / "missing.yaml") == {}


def test_required_load_reports_a_missing_file(tmp_path: Path) -> None:
    with pytest.raises(ConfigReadError, match="does not exist"):
        _storage.load_yaml(tmp_path / "missing.yaml", missing_ok=False)


@pytest.mark.parametrize("content", ["", "   \n# comment only\n", "null\n", "~\n"])
def test_load_empty_file_returns_empty_mapping(tmp_path: Path, content: str) -> None:
    path = tmp_path / "empty.yaml"
    path.write_text(content, encoding="utf-8")

    assert _storage.load_yaml(path) == {}


def test_invalid_yaml_reports_path_and_location(tmp_path: Path) -> None:
    path = tmp_path / "invalid.yaml"
    path.write_text("value: [unterminated\n", encoding="utf-8")

    with pytest.raises(ConfigFormatError) as caught:
        _storage.load_yaml(path)

    message = str(caught.value)
    assert str(path) in message
    assert "line" in message
    assert "column" in message


@pytest.mark.parametrize("content", ["- one\n- two\n", "scalar\n", "42\n"])
def test_rejects_non_mapping_yaml_roots(tmp_path: Path, content: str) -> None:
    path = tmp_path / "non-mapping.yaml"
    path.write_text(content, encoding="utf-8")

    with pytest.raises(ConfigFormatError, match="non-mapping.yaml"):
        _storage.load_yaml(path)


def test_rejects_non_string_mapping_keys(tmp_path: Path) -> None:
    path = tmp_path / "invalid-key.yaml"
    path.write_text("1: value\n", encoding="utf-8")

    with pytest.raises(ConfigFormatError, match="invalid-key.yaml"):
        _storage.load_yaml(path)


def test_round_trip_unicode_and_supported_types(tmp_path: Path) -> None:
    path = tmp_path / "config.yaml"
    expected = {
        "none": None,
        "enabled": False,
        "attempts": 0,
        "ratio": 1.25,
        "message": "Préfère le café ☕",
        "items": ["alpha", 2, True, None],
        "nested": {"host": "localhost", "ports": [8000, 8001]},
    }

    _storage.save_yaml(path, expected)

    assert _storage.load_yaml(path) == expected
    assert "Préfère le café ☕" in path.read_text(encoding="utf-8")


def test_save_creates_parent_directories(tmp_path: Path) -> None:
    path = tmp_path / "deep" / "folder" / "config.yaml"

    _storage.save_yaml(path, {"created": True})

    assert _storage.load_yaml(path) == {"created": True}


def test_validation_happens_before_filesystem_changes(tmp_path: Path) -> None:
    directory = tmp_path / "must-not-exist"
    path = directory / "config.yaml"

    with pytest.raises(ConfigFormatError):
        _storage.save_yaml(path, {"unsupported": object()})  # type: ignore[dict-item]

    assert not directory.exists()


def test_failed_replace_preserves_existing_file_and_cleans_temp(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    path = tmp_path / "config.yaml"
    _storage.save_yaml(path, {"version": "old"})
    previous_bytes = path.read_bytes()

    def fail_replace(source: Path, destination: Path) -> None:
        raise OSError("simulated replacement failure")

    monkeypatch.setattr(_storage.os, "replace", fail_replace)

    with pytest.raises(ConfigWriteError, match="simulated replacement failure"):
        _storage.save_yaml(path, {"version": "new"})

    assert path.read_bytes() == previous_bytes
    assert list(tmp_path.glob(".config.yaml.*.tmp")) == []


@pytest.mark.skipif(os.name != "posix", reason="POSIX permissions only")
def test_saved_file_has_private_posix_permissions(tmp_path: Path) -> None:
    path = tmp_path / "config.yaml"

    _storage.save_yaml(path, {"private": True})

    assert path.stat().st_mode & 0o777 == 0o600


def test_delete_file_reports_whether_file_existed(tmp_path: Path) -> None:
    path = tmp_path / "config.yaml"
    _storage.save_yaml(path, {"value": 1})

    assert _storage.delete_file(path) is True
    assert _storage.delete_file(path) is False
