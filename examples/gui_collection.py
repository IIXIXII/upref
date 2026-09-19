"""Edit values in wxPython dialogs; install upref[gui] before running."""

import json

from upref import Field, PromptCancelled, PromptUnavailableError, collect, parse_bool
from upref.gui import GuiPrompter


def main() -> None:
    """Use a custom title, formatted current values, and explicit GUI ownership."""
    schema = {
        "enabled": Field("Enable notifications", parser=parse_bool),
        "tags": Field(
            "Tags",
            parser=json.loads,
            formatter=json.dumps,
            description="A JSON list of labels.",
            validator=lambda value: isinstance(value, list),
        ),
    }
    try:
        with GuiPrompter(title="Upref example preferences") as prompter:
            settings = collect(
                schema,
                {"enabled": False, "tags": ["work", "home"]},
                interface=prompter,
                mode="all",
            )
    except PromptUnavailableError:
        print('GUI unavailable. Install "upref[gui]" and run in a desktop session.')
    except PromptCancelled:
        print("Cancelled; no values saved.")
    else:
        print(settings)
        print("No file was written.")


if __name__ == "__main__":
    main()
