"""Check user decisions and file preservation in preference application recipes."""

import json
import runpy
from pathlib import Path

import pytest

from upref import ConfigFormatError, ConfigStore, PromptCancelled

EXAMPLES = Path(__file__).resolve().parents[1] / "examples"


class ScriptedPrompter:
    def __init__(self, answers):
        self.answers = list(answers)
        self.asked = []
        self.errors = []

    def ask(self, name, field, current):
        self.asked.append(name)
        return self.answers.pop(0)

    def show_error(self, message):
        self.errors.append(message)


def test_first_run_saves_once_and_reuses_preferences(tmp_path):
    configure = runpy.run_path(str(EXAMPLES / "first_run_preferences.py"))["configure"]
    store = ConfigStore("example", directory=tmp_path)
    prompter = ScriptedPrompter(["dark", "fr", "18", "no"])
    configured = configure(store, prompter)
    assert configured == {
        "theme": "dark",
        "language": "fr",
        "font_size": 18,
        "notifications": False,
    }
    before = store.path.read_bytes()
    assert configure(store, prompter) == configured
    assert prompter.asked == ["theme", "language", "font_size", "notifications"]
    assert store.path.read_bytes() == before


@pytest.mark.parametrize(
    "answers", [[None], ["dark", None], ["dark", "fr", "18", None]]
)
def test_first_run_cancellation_leaves_setup_unfinished(tmp_path, answers):
    configure = runpy.run_path(str(EXAMPLES / "first_run_preferences.py"))["configure"]
    store = ConfigStore("example", directory=tmp_path / "not-created")
    with pytest.raises(PromptCancelled):
        configure(store, ScriptedPrompter(answers))
    assert not store.path.parent.exists()


@pytest.mark.parametrize("decision", ["yes", "no", None])
def test_apply_requires_confirmation_and_keeps_unrelated_values(tmp_path, decision):
    edit = runpy.run_path(str(EXAMPLES / "apply_preferences.py"))["edit_preferences"]
    store = ConfigStore("example", directory=tmp_path)
    store.save({"theme": "light", "font_size": 14, "language": "fr"})
    before = store.path.read_bytes()
    prompter = ScriptedPrompter(["dark", "20", decision])
    if decision is None:
        with pytest.raises(PromptCancelled):
            edit(store, prompter)
    else:
        assert edit(store, prompter) is (decision == "yes")
    if decision == "yes":
        assert store.load() == {"theme": "dark", "font_size": 20, "language": "fr"}
    else:
        assert store.path.read_bytes() == before


def test_recent_history_is_bounded_and_reopening_moves_to_front(tmp_path):
    remember = runpy.run_path(str(EXAMPLES / "recent_files.py"))["remember_file"]
    store = ConfigStore("example", directory=tmp_path)
    store.save({"theme": "dark"})
    for name in ("one.txt", "two.txt", "three.txt", "two.txt"):
        recent = remember(store, tmp_path / name, limit=2)
    assert recent == [str(tmp_path / "two.txt"), str(tmp_path / "three.txt")]
    assert store.load()["theme"] == "dark"
    assert len(list(tmp_path.iterdir())) == 1  # No recent document was created.


def test_invalid_recent_history_is_not_replaced(tmp_path):
    remember = runpy.run_path(str(EXAMPLES / "recent_files.py"))["remember_file"]
    store = ConfigStore("example", directory=tmp_path)
    store.save({"recent_files": [True]})
    before = store.path.read_bytes()
    with pytest.raises(ValueError, match="list of strings"):
        remember(store, tmp_path / "new.txt")
    with pytest.raises(ValueError, match="positive integer"):
        remember(store, tmp_path / "new.txt", limit=0)
    assert store.path.read_bytes() == before


@pytest.mark.parametrize(
    "saved",
    [
        {"x": 9000, "y": -100, "width": 4000, "height": 3000},
        {"x": True, "width": "900", "height": -1, "maximized": "false"},
        {},
    ],
)
def test_restored_window_stays_inside_display_and_input_is_unchanged(saved):
    restore = runpy.run_path(str(EXAMPLES / "window_preferences.py"))["restore_window"]
    before = dict(saved)
    restored = restore(saved, 1280, 720)
    assert 0 <= restored["x"] <= 1280 - restored["width"]
    assert 0 <= restored["y"] <= 720 - restored["height"]
    assert 0 < restored["width"] <= 1280
    assert 0 < restored["height"] <= 720
    assert restored["maximized"] is False
    assert saved == before


def test_account_preferences_are_independent_and_unknown_account_uses_defaults(
    tmp_path,
):
    preferences_for = runpy.run_path(str(EXAMPLES / "account_preferences.py"))[
        "preferences_for"
    ]
    store = ConfigStore("example", directory=tmp_path)
    store.save(
        {"accounts": {"work": {"theme": "dark"}, "personal": {"language": "fr"}}}
    )
    work = preferences_for(store, "work")
    work["theme"] = "light"
    assert preferences_for(store, "work")["theme"] == "dark"
    assert preferences_for(store, "personal") == {"theme": "system", "language": "fr"}
    assert preferences_for(store, "unknown") == {"theme": "system", "language": "en"}


@pytest.mark.parametrize("remember", [False, True])
def test_cli_overrides_are_transient_unless_remembered(tmp_path, remember):
    resolve = runpy.run_path(str(EXAMPLES / "session_overrides.py"))[
        "session_preferences"
    ]
    store = ConfigStore("example", directory=tmp_path)
    store.save({"theme": "light", "font_size": 16})
    before = store.path.read_bytes()
    assert resolve(store, {"theme": "dark"}, remember=remember) == {
        "theme": "dark",
        "font_size": 16,
        "language": "en",
    }
    if remember:
        assert store.load() == {"theme": "dark", "font_size": 16}
    else:
        assert store.path.read_bytes() == before


@pytest.mark.parametrize(
    "arguments",
    [["--theme", "unknown"], ["--font-size", "small"], ["--font-size", "0"]],
)
def test_cli_rejects_invalid_preferences(arguments):
    main = runpy.run_path(str(EXAMPLES / "session_overrides.py"))["main"]
    with pytest.raises(SystemExit) as caught:
        main(arguments)
    assert caught.value.code == 2


def test_json_export_excludes_local_data_and_preview_does_not_apply(tmp_path):
    recipe = runpy.run_path(str(EXAMPLES / "import_export_preferences.py"))
    store = ConfigStore("example", directory=tmp_path)
    store.save({"theme": "dark", "recent_files": ["local.txt"], "internal_flag": True})
    before = store.path.read_bytes()
    path = tmp_path / "export.json"
    recipe["export_preferences"](store, path)
    assert json.loads(path.read_text(encoding="utf-8")) == {"theme": "dark"}
    assert recipe["preview_import"](path) == {"theme": "dark"}
    assert store.path.read_bytes() == before


@pytest.mark.parametrize(
    "content",
    [
        '{"font_size": true}',
        '{"theme": "unknown"}',
        '{"language": "unknown"}',
        '{"recent_files": []}',
        "[]",
        '{"theme": "dark", "theme": "light"}',
        "{broken",
    ],
)
def test_json_import_rejects_invalid_or_ambiguous_preferences(tmp_path, content):
    preview = runpy.run_path(str(EXAMPLES / "import_export_preferences.py"))[
        "preview_import"
    ]
    source = tmp_path / "import.json"
    source.write_text(content, encoding="utf-8")
    with pytest.raises(ValueError):
        preview(source)
    assert source.read_text(encoding="utf-8") == content


@pytest.mark.parametrize("content", [None, "theme: [broken"])
def test_missing_or_invalid_backup_preserves_current_preferences(tmp_path, content):
    restore = runpy.run_path(str(EXAMPLES / "backup_restore.py"))["restore_backup"]
    store = ConfigStore("example", directory=tmp_path)
    backup = ConfigStore("example", filename="backup.yaml", directory=tmp_path)
    store.save({"theme": "dark"})
    original = store.path.read_bytes()
    if content is not None:
        backup.path.write_text(content, encoding="utf-8")
    with pytest.raises((FileNotFoundError, ConfigFormatError)):
        restore(store, backup)
    assert store.path.read_bytes() == original
