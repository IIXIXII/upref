"""Edit a draft and require an explicit Apply decision before saving it."""

from pathlib import Path
from tempfile import TemporaryDirectory

from upref import ConfigStore, Field, PromptCancelled, Prompter, collect, parse_bool
from upref.tty import TTYPrompter


def edit_preferences(store: ConfigStore, prompter: Prompter) -> bool:
    """Return whether the complete draft was applied; cancellation propagates."""
    draft = collect(
        {
            "theme": Field(
                "Theme: system, light, or dark",
                parser=str.strip,
                validator=lambda value: value in ("system", "light", "dark"),
            ),
            "font_size": Field(
                "Font size: 10 to 32",
                parser=int,
                validator=lambda value: type(value) is int and 10 <= value <= 32,
            ),
        },
        initial=store.load(),
        interface=prompter,
        mode="all",
    )
    decision = collect(
        {"apply": Field("Apply these changes", parser=parse_bool)},
        initial={"apply": False},
        interface=prompter,
        mode="all",
    )
    if decision["apply"] is not True:
        return False
    # This load/edit/save sequence assumes a single writer for these preferences.
    store.save(draft)
    return True


def main() -> None:
    """Demonstrate Apply, discard, and cancellation with existing preferences."""
    with TemporaryDirectory(prefix="upref-apply-") as directory:
        store = ConfigStore("apply-demo", directory=Path(directory).resolve())
        store.save({"theme": "system", "font_size": 14, "language": "fr"})
        try:
            applied = edit_preferences(store, TTYPrompter(keep_current=True))
        except PromptCancelled:
            print("Cancelled; saved preferences unchanged.")
        else:
            print("Changes applied." if applied else "Draft discarded.")
        print("Saved preferences:", store.load())


if __name__ == "__main__":
    main()
