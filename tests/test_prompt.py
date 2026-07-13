from __future__ import annotations

import sys
from dataclasses import FrozenInstanceError
from types import ModuleType

import pytest

from upref.errors import PromptCancelled
from upref.gui import GuiPrompter
from upref.prompt import Field, collect


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
            return fake_wx.ID_OK

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
    prompter.show_error("Wrong token")
    prompter.close()
    prompter.close()

    assert answer == "replacement"
    assert dialogs[0].args[3] == ""  # type: ignore[attr-defined]
    assert dialogs[0].args[4] & fake_wx.TE_PASSWORD  # type: ignore[attr-defined]
    assert dialogs[0].destroyed is True  # type: ignore[attr-defined]
    assert messages[0][0] == "Wrong token"
    assert apps[0].destroyed is True  # type: ignore[attr-defined]
