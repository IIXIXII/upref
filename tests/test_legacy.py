"""Compatibility and explicit v1 migration tests."""

from __future__ import annotations

import pytest

from upref import ConfigStore, MigrationError, PromptCancelled
from upref import legacy
from upref._storage import save_yaml


def test_imports_descriptor_file_without_removing_source(tmp_path):
    legacy_dir = tmp_path / "v1"
    target_dir = tmp_path / "v2"
    source = legacy_dir / "old.conf"
    save_yaml(
        source,
        {
            "__gui__": {"title": "Old UI"},
            "login": {"label": "Login", "value": "florent"},
            "retries": {"label": "Retries", "value": 0},
        },
    )
    store = ConfigStore("sample", directory=target_dir)

    migrated = store.import_legacy("old", legacy_directory=legacy_dir)

    assert migrated == {"login": "florent", "retries": 0}
    assert store.load() == migrated
    assert source.is_file()


def test_imports_raw_v1_data_without_changing_its_shape(tmp_path):
    legacy_dir = tmp_path / "v1"
    source = legacy_dir / "raw.conf"
    raw = {"database": {"host": "localhost", "port": 5432}}
    save_yaml(source, raw)
    store = ConfigStore("sample", directory=tmp_path / "v2")

    assert store.import_legacy("raw", legacy_directory=legacy_dir) == raw
    assert store.load() == raw


def test_import_refuses_to_overwrite_existing_v2_file(tmp_path):
    legacy_dir = tmp_path / "v1"
    save_yaml(legacy_dir / "old.conf", {"value": 1})
    store = ConfigStore("sample", directory=tmp_path / "v2")
    store.save({"current": True})

    with pytest.raises(MigrationError):
        store.import_legacy("old", legacy_directory=legacy_dir)

    assert store.load() == {"current": True}


def test_import_never_uses_the_legacy_source_as_its_target(tmp_path):
    shared_directory = tmp_path / "shared"
    source = shared_directory / "old.conf"
    original = {"login": {"label": "Login", "value": "florent"}}
    save_yaml(source, original)
    store = ConfigStore(
        "sample",
        directory=shared_directory,
        filename="old.conf",
    )

    with pytest.raises(MigrationError, match="different files"):
        store.import_legacy(
            "old",
            legacy_directory=shared_directory,
            overwrite=True,
        )

    assert legacy.load_yaml(source) == original


def test_import_reports_a_missing_source(tmp_path):
    store = ConfigStore("sample", directory=tmp_path / "v2")

    with pytest.raises(MigrationError, match="does not exist"):
        store.import_legacy("missing", legacy_directory=tmp_path / "v1")


def test_raw_description_conversion_supports_nested_values():
    raw = {"database": {"host": "localhost"}, "enabled": False}

    description = legacy.conv_raw_to_description(raw)

    assert legacy.conv_description_to_raw(description) == raw


def test_v1_raw_wrappers_warn_and_use_the_legacy_location(tmp_path, monkeypatch):
    monkeypatch.setattr(
        legacy,
        "_path_for",
        lambda name: tmp_path / f"{name}.conf",
    )

    with pytest.warns(DeprecationWarning):
        saved = legacy.save_data({"answer": 42}, "sample")
    with pytest.warns(DeprecationWarning):
        loaded = legacy.load_data("sample", {"fallback": True})

    assert saved == {"answer": 42}
    assert loaded == {"fallback": True, "answer": 42}


def test_get_pref_collects_only_missing_values_and_persists_v1_shape(
    tmp_path,
    monkeypatch,
):
    preference_path = tmp_path / "interactive.conf"
    monkeypatch.setattr(legacy, "_path_for", lambda name: preference_path)
    calls = []

    def fake_collect(schema, initial, interface, mode):
        calls.append((schema, initial, interface, mode))
        return {"login": "florent", "retries": 0}

    monkeypatch.setattr(legacy, "collect", fake_collect)
    description = {
        "login": {"label": "Login"},
        "retries": {"label": "Retries"},
    }

    with pytest.warns(DeprecationWarning):
        values = legacy.get_pref(description, "interactive", interface="tty")

    assert values == {"login": "florent", "retries": 0}
    assert calls[0][1] == {}
    assert calls[0][2:] == ("tty", "missing")
    assert legacy.conv_description_to_raw(legacy.load_yaml(preference_path)) == values

    monkeypatch.setattr(
        legacy,
        "collect",
        lambda *args, **kwargs: pytest.fail("complete values were prompted again"),
    )
    with pytest.warns(DeprecationWarning):
        assert legacy.get_pref(description, "interactive", interface="tty") == values


def test_get_pref_cancellation_does_not_create_a_file(tmp_path, monkeypatch):
    preference_path = tmp_path / "cancelled.conf"
    monkeypatch.setattr(legacy, "_path_for", lambda name: preference_path)

    def cancel(*args, **kwargs):
        raise PromptCancelled("cancelled")

    monkeypatch.setattr(legacy, "collect", cancel)

    with pytest.warns(DeprecationWarning), pytest.raises(PromptCancelled):
        legacy.get_pref({"login": {"label": "Login"}}, "cancelled")

    assert not preference_path.exists()


def test_set_pref_supports_nested_raw_values(tmp_path, monkeypatch):
    preference_path = tmp_path / "set-pref.conf"
    monkeypatch.setattr(legacy, "_path_for", lambda name: preference_path)

    with pytest.warns(DeprecationWarning):
        legacy.set_pref(
            {"database": {"host": "localhost"}, "enabled": False},
            "set-pref",
        )

    stored = legacy.load_yaml(preference_path)
    assert legacy.conv_description_to_raw(stored) == {
        "database": {"host": "localhost"},
        "enabled": False,
    }
