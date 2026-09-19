from __future__ import annotations

import sys
from dataclasses import FrozenInstanceError
from types import ModuleType

import pytest

import upref.gui as gui_module
import upref.prompt as prompt_module
from upref.errors import PromptCancelled, PromptUnavailableError
from upref.gui import GuiPrompter
from upref.prompt import Field, collect, parse_bool


class StubPrompter:
    def __init__(self, answers: list[str | None] | None = None) -> None:
        self.answers = list(answers or [])
        self.asked: list[tuple[str, Field, object]] = []
        self.errors: list[str] = []

    def ask(self, name: str, field: Field, current: object) -> str | None:
        self.asked.append((name, field, current))
        return self.answers.pop(0)

    def show_error(self, message: str) -> None:
        self.errors.append(message)


def test_field_is_immutable() -> None:
    field = Field("Port", parser=int)

    with pytest.raises(FrozenInstanceError):
        field.label = "Other"  # type: ignore[misc]


@pytest.mark.parametrize(
    "options",
    [
        {"label": 1},
        {"description": None},
        {"required": "false"},
        {"secret": 1},
        {"parser": None},
        {"formatter": 42},
        {"validator": False},
    ],
)
def test_invalid_field_definitions_fail_at_construction(options):
    with pytest.raises(TypeError, match="Field\\."):
        Field(**{"label": "Value", **options})


@pytest.mark.parametrize("raw", ["yes", "Y", "true", " ON ", "1"])
def test_parse_bool_true(raw):
    assert parse_bool(raw) is True


@pytest.mark.parametrize("raw", ["no", "N", "false", " OFF ", "0"])
def test_parse_bool_false(raw):
    assert parse_bool(raw) is False


@pytest.mark.parametrize("raw", ["", "maybe", "2"])
def test_parse_bool_rejects_unknown_spelling(raw):
    with pytest.raises(ValueError, match="Enter yes/no"):
        parse_bool(raw)


def test_schema_and_custom_prompter_contract_fail_early():
    with pytest.raises(TypeError, match="schema must be a mapping"):
        collect([])

    class BrokenPrompter:
        ask = 42
        show_error = "not callable"

    with pytest.raises(TypeError, match="Prompter protocol"):
        collect({}, interface=BrokenPrompter())

    with pytest.raises(TypeError, match="must return a string or None"):
        collect({"value": Field("Value")}, interface=StubPrompter([42]))


def test_missing_mode_preserves_false_zero_and_optional_empty_string() -> None:
    schema = {
        "enabled": Field("Enabled"),
        "retries": Field("Retries"),
        "note": Field("Note", required=False),
    }
    prompter = StubPrompter()

    result = collect(
        schema,
        {"enabled": False, "retries": 0, "note": ""},
        interface=prompter,
    )

    assert result == {"enabled": False, "retries": 0, "note": ""}
    assert prompter.asked == []


def test_no_missing_field_does_not_initialize_an_optional_interface(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def unexpected_interface(interface: object) -> object:
        raise AssertionError(f"interface unexpectedly initialized: {interface}")

    monkeypatch.setattr("upref.prompt._make_prompter", unexpected_interface)

    assert collect(
        {"enabled": Field("Enabled")},
        {"enabled": False},
        interface="gui",
    ) == {"enabled": False}


def test_missing_mode_requests_absent_none_and_required_empty_values() -> None:
    schema = {
        "absent": Field("Absent"),
        "none": Field("None"),
        "empty": Field("Empty"),
    }
    prompter = StubPrompter(["one", "two", "three"])

    result = collect(
        schema,
        {"none": None, "empty": "", "untouched": "yes"},
        interface=prompter,
    )

    assert result == {
        "absent": "one",
        "none": "two",
        "empty": "three",
        "untouched": "yes",
    }
    assert [call[0] for call in prompter.asked] == ["absent", "none", "empty"]


def test_parser_and_validator_value_errors_are_shown_then_retried() -> None:
    def positive(value: object) -> None:
        if not isinstance(value, int) or value <= 0:
            raise ValueError("must be positive")

    prompter = StubPrompter(["not-a-number", "-2", "4"])

    result = collect(
        {"port": Field("Port", parser=int, validator=positive)},
        interface=prompter,
    )

    assert result == {"port": 4}
    assert len(prompter.errors) == 2
    assert "invalid literal" in prompter.errors[0]
    assert prompter.errors[1] == "must be positive"


def test_secret_parser_errors_do_not_echo_the_raw_value() -> None:
    prompter = StubPrompter(["do-not-disclose", "42"])

    result = collect(
        {"token": Field("Token", parser=int, secret=True)},
        interface=prompter,
    )

    assert result == {"token": 42}
    assert prompter.errors == ["Invalid value for Token"]


def test_validator_false_is_rejected() -> None:
    prompter = StubPrompter(["bad", "good"])

    result = collect(
        {"answer": Field("Answer", validator=lambda value: value == "good")},
        interface=prompter,
    )

    assert result == {"answer": "good"}
    assert prompter.errors == ["Invalid value for Answer"]


def test_required_empty_answer_is_retried_before_parser() -> None:
    calls: list[str] = []

    def parser(raw: str) -> str:
        calls.append(raw)
        return raw

    prompter = StubPrompter(["", "value"])

    assert collect(
        {"name": Field("Name", parser=parser)},
        interface=prompter,
    ) == {"name": "value"}
    assert calls == ["value"]
    assert prompter.errors == ["Name is required"]


def test_collect_returns_a_detached_copy_without_mutating_inputs() -> None:
    initial = {"nested": {"items": [1, 2]}, "name": "old"}
    prompter = StubPrompter(["new"])

    result = collect(
        {"name": Field("Name")},
        initial,
        interface=prompter,
        mode="all",
    )
    result["nested"]["items"].append(3)  # type: ignore[index,union-attr]

    assert initial == {"nested": {"items": [1, 2]}, "name": "old"}
    assert result["name"] == "new"


def test_cancellation_raises_and_does_not_mutate_initial() -> None:
    initial = {"name": None}

    with pytest.raises(PromptCancelled, match="name"):
        collect(
            {"name": Field("Name")},
            initial,
            interface=StubPrompter([None]),
        )

    assert initial == {"name": None}


@pytest.mark.parametrize("mode", ["", "everything", "MISSING"])
def test_invalid_mode_is_rejected(mode: str) -> None:
    with pytest.raises(ValueError, match="mode"):
        collect({}, interface=StubPrompter(), mode=mode)  # type: ignore[arg-type]


def test_invalid_interface_is_rejected() -> None:
    with pytest.raises(ValueError, match="interface"):
        collect({}, interface="web")

    with pytest.raises(ValueError, match="interface"):
        prompt_module._make_prompter("web")


def test_invalid_custom_interface_is_rejected() -> None:
    with pytest.raises(TypeError, match="interface"):
        collect({}, interface=object())  # type: ignore[arg-type]

    with pytest.raises(TypeError, match="interface"):
        prompt_module._make_prompter(object())  # type: ignore[arg-type]


def test_invalid_schema_entries_are_rejected() -> None:
    with pytest.raises(TypeError, match="keys must be strings"):
        collect({1: Field("Invalid")}, interface=StubPrompter())  # type: ignore[dict-item]

    with pytest.raises(TypeError, match="must be a Field"):
        collect({"invalid": object()}, interface=StubPrompter())  # type: ignore[dict-item]


def test_owned_bundled_prompters_are_created_and_closed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class OwnedPrompter(StubPrompter):
        def __init__(self) -> None:
            super().__init__(["value"])
            self.closed = False

        def close(self) -> None:
            self.closed = True

    tty_prompter = OwnedPrompter()
    gui_prompter = OwnedPrompter()
    monkeypatch.setattr("upref.tty.TTYPrompter", lambda: tty_prompter)
    monkeypatch.setattr("upref.gui.GuiPrompter", lambda: gui_prompter)

    assert collect({"name": Field("Name")}, interface="tty") == {"name": "value"}
    assert tty_prompter.closed is True
    assert prompt_module._make_prompter("gui") == (gui_prompter, True)


def test_gui_import_and_initialization_failures_are_wrapped(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail_import(name: str) -> ModuleType:
        raise ImportError("wx is unavailable")

    monkeypatch.setattr(gui_module, "import_module", fail_import)
    with pytest.raises(PromptUnavailableError, match="could not be imported"):
        GuiPrompter()

    fake_wx = ModuleType("wx")
    fake_wx.GetApp = lambda: None

    def fail_app(redirect: bool) -> object:
        raise RuntimeError("display is unavailable")

    fake_wx.App = fail_app
    monkeypatch.setattr(gui_module, "import_module", lambda name: fake_wx)
    with pytest.raises(PromptUnavailableError, match="could not be initialized"):
        GuiPrompter()


def test_gui_prompter_uses_fake_wx_and_masks_secret_default(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake_wx = ModuleType("wx")
    fake_wx.OK = 1
    fake_wx.CANCEL = 2
    fake_wx.TE_PASSWORD = 4
    fake_wx.ICON_ERROR = 8
    fake_wx.ID_OK = 10
    dialogs: list[object] = []
    apps: list[object] = []
    messages: list[tuple[object, ...]] = []
    modal_results = [fake_wx.ID_OK, 0, fake_wx.ID_OK]

    class FakeApp:
        def __init__(self, redirect: bool) -> None:
            self.redirect = redirect
            self.destroyed = False
            apps.append(self)

        def Destroy(self) -> None:
            self.destroyed = True

    class FakeDialog:
        def __init__(self, *args: object) -> None:
            self.args = args
            self.destroyed = False
            dialogs.append(self)

        def ShowModal(self) -> int:
            return modal_results.pop(0)

        def GetValue(self) -> str:
            return "replacement"

        def Destroy(self) -> None:
            self.destroyed = True

    fake_wx.GetApp = lambda: None
    fake_wx.App = FakeApp
    fake_wx.TextEntryDialog = FakeDialog
    fake_wx.MessageBox = lambda *args: messages.append(args)
    monkeypatch.setitem(sys.modules, "wx", fake_wx)

    prompter = GuiPrompter(title="Settings")
    answer = prompter.ask(
        "token",
        Field("Token", description="API token", secret=True),
        "do-not-display",
    )
    cancelled = prompter.ask("attempts", Field("Attempts"), 3)
    import json

    prompter.ask(
        "flags",
        Field("Flags", parser=json.loads, formatter=json.dumps, required=False),
        [True, None],
    )
    prompter.show_error("Wrong token")
    assert prompter.__enter__() is prompter
    prompter.__exit__(None, None, None)
    prompter.close()

    with pytest.raises(RuntimeError, match="closed"):
        prompter.ask("name", Field("Name"), None)
    with pytest.raises(RuntimeError, match="closed"):
        prompter.show_error("Too late")

    assert answer == "replacement"
    assert cancelled is None
    assert dialogs[0].args[3] == ""  # type: ignore[attr-defined]
    assert dialogs[0].args[4] & fake_wx.TE_PASSWORD  # type: ignore[attr-defined]
    assert dialogs[1].args[3] == "3"  # type: ignore[attr-defined]
    assert dialogs[2].args[3] == "[true, null]"
    assert dialogs[2].args[1] == "Flags (optional)"
    assert dialogs[0].destroyed is True  # type: ignore[attr-defined]
    assert messages[0][0] == "Wrong token"
    assert apps[0].destroyed is True  # type: ignore[attr-defined]
