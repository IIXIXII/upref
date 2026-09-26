"""Collect user preferences once, then reuse them on later application starts."""

from pathlib import Path
from tempfile import TemporaryDirectory

from upref import (
    Config,
    ConfigStore,
    Field,
    PromptCancelled,
    Prompter,
    collect,
    parse_bool,
)
from upref.tty import TTYPrompter

DEFAULTS: Config = {
    "theme": "system",
    "language": "en",
    "font_size": 14,
    "notifications": True,
}
SCHEMA = {
    "theme": Field(
        "Theme: system, light, or dark",
        parser=str.strip,
        validator=lambda value: value in ("system", "light", "dark"),
    ),
    "language": Field(
        "Language: en or fr",
        parser=str.strip,
        validator=lambda value: value in ("en", "fr"),
    ),
    "font_size": Field(
        "Font size: 10 to 32",
        parser=int,
        validator=lambda value: type(value) is int and 10 <= value <= 32,
    ),
    "notifications": Field("Enable notifications", parser=parse_bool),
}


def configure(store: ConfigStore, prompter: Prompter) -> Config:
    """Ask on first launch; file presence marks a completed setup."""
    initial = store.load(defaults=DEFAULTS)
    if store.exists():
        return initial
    values = collect(SCHEMA, initial=initial, interface=prompter, mode="all")
    store.save(values)
    return values


def main() -> None:
    """Simulate two launches in one temporary application directory."""
    with TemporaryDirectory(prefix="upref-first-run-") as directory:
        store = ConfigStore("first-run-demo", directory=Path(directory).resolve())
        prompter = TTYPrompter(keep_current=True)
        try:
            print("First startup: Enter accepts each suggested preference.")
            print(configure(store, prompter))
        except PromptCancelled:
            print("Cancelled; setup will be offered again on the next startup.")
            return
        print("Second startup: preferences reused without prompting.")
        print(configure(store, prompter))


if __name__ == "__main__":
    main()
