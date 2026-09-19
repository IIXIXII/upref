"""Run deterministic collection through the public Prompter protocol."""

from collections.abc import Iterable

from upref import ConfigValue, Field, collect, parse_bool


class ScriptedPrompter:
    """Supply scripted answers, cancelling cleanly when they are exhausted."""

    def __init__(self, answers: Iterable[str | None]) -> None:
        """Keep an iterator without inspecting or logging answer values."""
        self._answers = iter(answers)
        self.errors: list[str] = []

    def ask(self, name: str, field: Field, current: ConfigValue) -> str | None:
        """Return the next raw answer without exposing current secret values."""
        return next(self._answers, None)

    def show_error(self, message: str) -> None:
        """Capture recoverable errors for the application's presentation layer."""
        self.errors.append(message)


def main() -> None:
    """Demonstrate parser retry and a detached structured result without a UI."""
    prompter = ScriptedPrompter(["maybe", "no", "3"])
    settings = collect(
        {
            "enabled": Field("Enabled", parser=parse_bool),
            "retries": Field("Retries", parser=int),
        },
        interface=prompter,
    )
    print(settings)
    print(f"Recoverable errors: {prompter.errors}")


if __name__ == "__main__":
    main()
