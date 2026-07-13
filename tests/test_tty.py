from __future__ import annotations

import pytest

from upref.prompt import Field
from upref.tty import TTYPrompter


def test_regular_field_shows_context_and_current_value() -> None:
    output: list[str] = []
    prompts: list[str] = []

    def read(prompt: str) -> str:
        prompts.append(prompt)
        return "new-value"

    prompter = TTYPrompter(input_func=read, print_func=output.append)

    assert (
        prompter.ask(
            "url",
            Field("Server URL", description="Base endpoint"),
            "https://old.example",
        )
        == "new-value"
    )
    assert output == [
        "Server URL",
        "Base endpoint",
        "Current value: https://old.example",
    ]
    assert prompts == ["> "]


def test_false_and_zero_current_values_are_displayed() -> None:
    output: list[str] = []
    prompter = TTYPrompter(
        input_func=lambda prompt: "unchanged",
        print_func=output.append,
    )

    prompter.ask("enabled", Field("Enabled"), False)
    prompter.ask("count", Field("Count"), 0)

    assert "Current value: False" in output
    assert "Current value: 0" in output


def test_secret_uses_getpass_and_never_displays_current_value() -> None:
    output: list[str] = []
    ordinary_calls: list[str] = []
    secret_calls: list[str] = []

    prompter = TTYPrompter(
        input_func=lambda prompt: ordinary_calls.append(prompt) or "ordinary",
        getpass_func=lambda prompt: secret_calls.append(prompt) or "secret",
        print_func=output.append,
    )

    assert (
        prompter.ask(
            "password",
            Field("Password", description="Account password", secret=True),
            "old-secret",
        )
        == "secret"
    )
    assert ordinary_calls == []
    assert secret_calls == ["> "]
    assert "old-secret" not in "\n".join(output)


@pytest.mark.parametrize("error", [EOFError(), KeyboardInterrupt()])
def test_regular_input_interrupt_is_treated_as_cancellation(
    error: BaseException,
) -> None:
    def interrupted(prompt: str) -> str:
        raise error

    prompter = TTYPrompter(input_func=interrupted, print_func=lambda value: None)

    assert prompter.ask("name", Field("Name"), None) is None


@pytest.mark.parametrize("error", [EOFError(), KeyboardInterrupt()])
def test_secret_input_interrupt_is_treated_as_cancellation(
    error: BaseException,
) -> None:
    def interrupted(prompt: str) -> str:
        raise error

    prompter = TTYPrompter(
        getpass_func=interrupted,
        print_func=lambda value: None,
    )

    assert prompter.ask("password", Field("Password", secret=True), None) is None


def test_show_error_has_a_clear_prefix() -> None:
    output: list[str] = []
    prompter = TTYPrompter(print_func=output.append)

    prompter.show_error("must be positive")

    assert output == ["Error: must be positive"]
