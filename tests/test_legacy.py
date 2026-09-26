"""Compatibility and explicit v1 migration tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from upref import (
    ConfigReadError,
    ConfigStore,
    ConfigWriteError,
    MigrationError,
    PromptCancelled,
    legacy,
)
from upref._storage import save_yaml


class InvalidPath:
    def __fspath__(self) -> str:
        raise OSError("invalid path")


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


@pytest.mark.parametrize(
    ("source_format", "expected"),
    [
        ("auto", {"timeout": 30}),
        ("descriptors", {"timeout": 30}),
        ("raw", {"timeout": {"value": 30, "unit": "seconds"}}),
    ],
)
def test_explicit_migration_format_resolves_ambiguous_data(
    tmp_path, source_format, expected
):
    source = tmp_path / "ambiguous.conf"
    save_yaml(source, {"timeout": {"value": 30, "unit": "seconds"}})
    original = source.read_bytes()
    store = ConfigStore("sample", directory=tmp_path / "v2")

    assert (
        store.import_legacy(
            "ambiguous", legacy_directory=tmp_path, source_format=source_format
        )
        == expected
    )
    assert store.load() == expected
    assert source.read_bytes() == original


def test_explicit_descriptors_can_convert_documents_without_values(tmp_path):
    save_yaml(tmp_path / "empty.conf", {"field": {"label": "Field"}, "__gui__": {}})
    store = ConfigStore("sample", directory=tmp_path / "v2")
    assert (
        store.import_legacy(
            "empty", legacy_directory=tmp_path, source_format="descriptors"
        )
        == {}
    )
    assert store.load() == {}


def test_dry_run_does_not_create_directory_and_matches_committed_conversion(tmp_path):
    source = tmp_path / "preview.conf"
    save_yaml(source, {"tags": {"value": ["one"]}})
    original = source.read_bytes()
    store = ConfigStore("sample", directory=tmp_path / "absent")

    preview = store.import_legacy(
        "preview", legacy_directory=tmp_path, source_format="descriptors", dry_run=True
    )
    assert preview == {"tags": ["one"]}
    assert not store.path.parent.exists()
    committed = store.import_legacy(
        "preview", legacy_directory=tmp_path, source_format="descriptors"
    )
    assert committed == preview
    preview["tags"].append("preview-only")
    assert store.load() == committed
    assert source.read_bytes() == original


def test_dry_run_keeps_target_checks_without_overwriting(tmp_path):
    save_yaml(tmp_path / "old.conf", {"imported": True})
    store = ConfigStore("sample", directory=tmp_path / "v2")
    store.save({"keep": True})
    original = store.path.read_bytes()
    with pytest.raises(MigrationError, match="already exists"):
        store.import_legacy("old", legacy_directory=tmp_path, dry_run=True)
    assert store.import_legacy(
        "old", legacy_directory=tmp_path, dry_run=True, overwrite=True
    ) == {"imported": True}
    assert store.path.read_bytes() == original

    same = ConfigStore("sample", directory=tmp_path, filename="old.conf")
    with pytest.raises(MigrationError, match="different files"):
        same.import_legacy(
            "old", legacy_directory=tmp_path, dry_run=True, overwrite=True
        )
    with pytest.raises(MigrationError, match="does not exist"):
        store.import_legacy("missing", legacy_directory=tmp_path, dry_run=True)


@pytest.mark.parametrize("source_format", ["RAW", "unknown", None, 1])
def test_invalid_migration_format_fails_before_reading(tmp_path, source_format):
    store = ConfigStore("sample", directory=tmp_path / "v2")
    with pytest.raises(ValueError, match="source_format"):
        store.import_legacy(
            "absent", source_format=source_format, legacy_directory=tmp_path
        )


@pytest.mark.parametrize("dry_run", ["false", None, 1])
def test_invalid_dry_run_fails_before_reading(tmp_path, dry_run):
    store = ConfigStore("sample", directory=tmp_path / "v2")
    with pytest.raises(TypeError, match="dry_run"):
        store.import_legacy("absent", dry_run=dry_run, legacy_directory=tmp_path)


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


def test_v1_path_oriented_helpers_and_invalid_paths(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    path = tmp_path / "legacy.conf"
    monkeypatch.setattr(legacy, "legacy_config_path", lambda name: path)

    with pytest.warns(DeprecationWarning):
        assert legacy.upref_filename("legacy") == str(path)
    with pytest.warns(DeprecationWarning):
        assert legacy.save_conf({"value": 1}, path) == {"value": 1}
    with pytest.warns(DeprecationWarning):
        assert legacy.load_conf(path) == {"value": 1}
    with pytest.warns(DeprecationWarning):
        assert legacy.current_upref("legacy") == {"value": 1}
    with pytest.warns(DeprecationWarning):
        assert legacy.load_data("legacy") == {"value": 1}
    with pytest.warns(DeprecationWarning):
        legacy.remove_pref("legacy")
    assert not path.exists()

    with pytest.warns(DeprecationWarning), pytest.raises(ConfigReadError):
        legacy.load_conf(InvalidPath())
    with pytest.warns(DeprecationWarning), pytest.raises(ConfigWriteError):
        legacy.save_conf({}, InvalidPath())


def test_v1_pure_compatibility_helpers_return_detached_results() -> None:
    first = legacy.default_conf()
    first["__gui__"]["title"] = "Changed"  # type: ignore[index]
    assert legacy.default_conf()["__gui__"]["title"] == "Personal information"  # type: ignore[index]

    assert legacy.dict_merge({"nested": {"one": 1}}, {"nested": {"two": 2}}) == {
        "nested": {"one": 1, "two": 2}
    }


def test_descriptor_edge_cases_are_handled() -> None:
    assert legacy.all_values_are_set({"__gui__": {}, "name": {"value": ""}}) is False

    overlaid = legacy._description_with_saved_values(
        {"name": "malformed"},
        {"name": {"value": "saved"}},
    )
    assert overlaid == {"name": {"value": "saved"}}

    field = legacy._field_from_descriptor("name", "malformed")
    assert field.label == "name"
    assert field.secret is False


def test_get_pref_nonmandatory_and_malformed_descriptors(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    path = tmp_path / "preferences.conf"
    monkeypatch.setattr(legacy, "_path_for", lambda name: path)
    save_yaml(path, {"saved": {"value": 1}})

    with pytest.warns(DeprecationWarning):
        assert legacy.get_pref({}, "preferences", mandatory=False) == {"saved": 1}

    path.unlink()
    monkeypatch.setattr(
        legacy,
        "collect",
        lambda *args, **kwargs: {"name": "collected"},
    )
    with pytest.warns(DeprecationWarning):
        assert legacy.get_pref(
            {"name": "malformed"},
            "preferences",
            interface="tty",
        ) == {"name": "collected"}
    assert legacy.load_yaml(path) == {"name": {"value": "collected"}}


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

    with pytest.warns(DeprecationWarning):
        legacy.set_pref({"enabled": True}, "set-pref")
    assert (
        legacy.conv_description_to_raw(legacy.load_yaml(preference_path))["enabled"]
        is True
    )


def test_description_detection_handles_metadata_only_documents() -> None:
    assert legacy._looks_like_description({"__gui__": {}}) is False


def test_import_propagates_non_missing_read_errors(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    store = ConfigStore("sample", directory=tmp_path / "v2")
    monkeypatch.setattr(
        legacy,
        "load_yaml",
        lambda *args, **kwargs: (_ for _ in ()).throw(ConfigReadError("denied")),
    )

    with pytest.raises(ConfigReadError, match="denied"):
        legacy.import_legacy(store, "source", legacy_directory=tmp_path / "v1")


def test_import_wraps_destination_persistence_errors(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    legacy_dir = tmp_path / "v1"
    save_yaml(legacy_dir / "source.conf", {"value": 1})
    store = ConfigStore("sample", directory=tmp_path / "v2")

    def fail_save(self: ConfigStore, data: object) -> None:
        raise ConfigWriteError("write denied")

    monkeypatch.setattr(ConfigStore, "save", fail_save)

    with pytest.raises(MigrationError, match="Could not migrate") as caught:
        legacy.import_legacy(store, "source", legacy_directory=legacy_dir)

    assert isinstance(caught.value.__cause__, ConfigWriteError)
