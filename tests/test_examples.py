"""Exercise example behavior in isolated directories without real user prompts."""

from __future__ import annotations

import runpy
import sys
import tempfile
from pathlib import Path

import pytest

EXAMPLES = Path(__file__).resolve().parents[1] / "examples"


@pytest.fixture
def isolated_examples(tmp_path, monkeypatch):
    monkeypatch.setattr(sys, "argv", ["upref-example"])
    monkeypatch.setattr(tempfile, "tempdir", str(tmp_path))
    monkeypatch.setattr(
        "upref._paths.user_config_path",
        lambda appname, **kwargs: tmp_path / appname,
    )
    for name in ("UPREF_PROFILE", "UPREF_SERVICE_URL", "UPREF_TIMEOUT"):
        monkeypatch.delenv(name, raising=False)
    return tmp_path


@pytest.mark.parametrize(
    ("script", "expected"),
    [
        ("portable_store.py", "9000"),
        ("custom_interface.py", "'enabled': False, 'retries': 3"),
        ("typed_settings.py", "Settings(host='localhost', port=8080, enabled=False)"),
        ("schema_upgrade.py", "'schema_version': 2"),
        ("handle_errors.py", "The original file was preserved."),
        ("basic_store.py", ""),
        ("defaults_and_update.py", ""),
        ("multiple_projects.py", ""),
        ("reset_preferences.py", "Appearance reset; notifications retained:"),
        ("recent_files.py", "Recent documents: ['notes.txt', 'draft.md']"),
        ("window_preferences.py", "'width': 1280, 'height': 720"),
        ("account_preferences.py", "Signed out; account preferences retained."),
        (
            "session_overrides.py",
            "Saved overrides: {'theme': 'light', 'font_size': 16}",
        ),
        ("import_export_preferences.py", "Local history retained: ['target-only.txt']"),
        (
            "backup_restore.py",
            "Restored preferences: {'theme': 'dark', 'font_size': 16, 'notifications': False}",
        ),
        ("migration_preview.py", "Migration applied; legacy file unchanged."),
        (
            "environment_profiles.py",
            "Environment-variable overrides were not persisted.",
        ),
    ],
)
def test_noninteractive_examples_run(isolated_examples, script, expected, capsys):
    runpy.run_path(str(EXAMPLES / script), run_name="__main__")
    assert expected in capsys.readouterr().out


@pytest.mark.parametrize(
    ("script", "answers", "expected"),
    [
        ("boolean_collection.py", ["maybe", "no", ""], "'notifications': False"),
        ("edit_settings.py", ["", "[]"], "'tags': []"),
        ("nested_collection.py", ["", "70000", "9000"], "'port': 9000"),
        (
            "first_run_preferences.py",
            ["purple", "dark", "fr", "9", "18", "no"],
            "Second startup: preferences reused without prompting.",
        ),
        ("apply_preferences.py", ["dark", "20", "yes"], "Changes applied."),
        ("apply_preferences.py", ["", "", ""], "Draft discarded."),
    ],
)
def test_interactive_examples_retry_and_accept_values(
    isolated_examples, monkeypatch, capsys, script, answers, expected
):
    responses = iter(answers)
    monkeypatch.setattr("builtins.input", lambda prompt: next(responses))
    runpy.run_path(str(EXAMPLES / script), run_name="__main__")
    assert expected in capsys.readouterr().out


@pytest.mark.parametrize(
    "script",
    [
        "boolean_collection.py",
        "edit_settings.py",
        "nested_collection.py",
        "first_run_preferences.py",
    ],
)
def test_interactive_examples_cancel_without_saving(
    isolated_examples, monkeypatch, capsys, script
):
    def cancel(prompt):
        raise KeyboardInterrupt

    def unexpected_save(*args):
        raise AssertionError("Cancelled examples must not save")

    monkeypatch.setattr("builtins.input", cancel)
    monkeypatch.setattr("upref.ConfigStore.save", unexpected_save)
    runpy.run_path(str(EXAMPLES / script), run_name="__main__")
    assert "cancel" in capsys.readouterr().out.lower()


def test_typed_settings_rejects_a_boolean_port():
    namespace = runpy.run_path(str(EXAMPLES / "typed_settings.py"))
    with pytest.raises(ValueError, match="port must be an integer"):
        namespace["Settings"].from_config(
            {"host": "localhost", "port": True, "enabled": False}
        )


@pytest.mark.parametrize(
    "data", [{"schema_version": 3}, {"schema_version": True}, {"network": {}}]
)
def test_schema_upgrade_rejects_unknown_and_ambiguous_data(data):
    namespace = runpy.run_path(str(EXAMPLES / "schema_upgrade.py"))
    before = dict(data)
    with pytest.raises(ValueError):
        namespace["upgrade"](data)
    assert data == before


def test_schema_upgrade_is_detached_and_idempotent():
    namespace = runpy.run_path(str(EXAMPLES / "schema_upgrade.py"))
    upgrade = namespace["upgrade"]
    original = {"host": "localhost", "port": 8080, "extras": ["keep"]}
    upgraded = upgrade(original)
    assert upgrade(upgraded) == upgraded
    upgraded["extras"].append("new")
    assert original == {"host": "localhost", "port": 8080, "extras": ["keep"]}


def test_gui_example_explains_missing_dependency(monkeypatch, capsys):
    def unavailable(name):
        raise ImportError("wx unavailable")

    monkeypatch.setattr("upref.gui.import_module", unavailable)
    runpy.run_path(str(EXAMPLES / "gui_collection.py"), run_name="__main__")
    assert "GUI unavailable" in capsys.readouterr().out
