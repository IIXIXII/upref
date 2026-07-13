"""Public ConfigStore contract tests."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path

import pytest

from upref import ConfigReadError, ConfigStore


def test_missing_file_returns_an_independent_empty_config(tmp_path):
    store = ConfigStore("sample", directory=tmp_path)

    first = store.load()
    second = store.load()

    assert first == {}
    assert second == {}
    assert first is not second
    assert not store.exists()


def test_stored_values_override_defaults_recursively(tmp_path):
    store = ConfigStore("sample", directory=tmp_path)
    defaults = {
        "network": {"host": "localhost", "port": 8080},
        "enabled": True,
    }
    original_defaults = deepcopy(defaults)
    store.save({"network": {"port": 9000}, "enabled": False})

    loaded = store.load(defaults=defaults)

    assert loaded == {
        "network": {"host": "localhost", "port": 9000},
        "enabled": False,
    }
    assert defaults == original_defaults


def test_save_load_update_and_delete(tmp_path):
    store = ConfigStore("sample", filename="settings.yaml", directory=tmp_path)

    store.save({"message": "été", "nested": {"one": 1}})
    assert store.exists()
    assert store.filename == "settings.yaml"
    assert store.path == (tmp_path / "settings.yaml").resolve()
    assert store.load() == {"message": "été", "nested": {"one": 1}}

    updated = store.update({"nested": {"two": 2}, "disabled": False})
    assert updated == {
        "message": "été",
        "nested": {"one": 1, "two": 2},
        "disabled": False,
    }
    assert store.load() == updated

    assert store.delete() is True
    assert store.delete() is False
    assert store.load() == {}


def test_store_does_not_retain_mutable_input_references(tmp_path):
    store = ConfigStore("sample", directory=tmp_path)
    source = {"nested": {"items": [1, 2]}}
    store.save(source)

    source["nested"]["items"].append(3)
    loaded = store.load()
    loaded["nested"]["items"].append(4)

    assert store.load() == {"nested": {"items": [1, 2]}}


def test_repr_contains_application_and_path(tmp_path):
    store = ConfigStore("sample", directory=tmp_path)

    representation = repr(store)

    assert "sample" in representation
    assert repr(store.path) in representation


def test_exists_wraps_filesystem_inspection_errors(tmp_path, monkeypatch):
    store = ConfigStore("sample", directory=tmp_path)

    def fail_is_file(path: Path) -> bool:
        raise OSError("inspection failed")

    monkeypatch.setattr(Path, "is_file", fail_is_file)

    with pytest.raises(ConfigReadError, match="inspection failed"):
        store.exists()
