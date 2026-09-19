"""Edit current terminal values with Enter to keep and JSON list parsing."""

import json

from upref import Field, PromptCancelled, collect, parse_bool
from upref.tty import TTYPrompter


def main() -> None:
    """Edit an in-memory configuration using a caller-owned terminal interface."""
    schema = {
        "enabled": Field("Enabled", parser=parse_bool),
        "tags": Field(
            "Tags",
            description='Enter a JSON list, for example ["work", "personal"].',
            parser=json.loads,
            formatter=json.dumps,
            validator=lambda value: (
                isinstance(value, list) and all(isinstance(tag, str) for tag in value)
            ),
        ),
    }
    try:
        settings = collect(
            schema,
            initial={"enabled": False, "tags": ["work"]},
            interface=TTYPrompter(keep_current=True),
            mode="all",
        )
    except PromptCancelled:
        print("Editing cancelled.")
    else:
        print(settings)
        print("Values are in memory only; call store.save(settings) to persist them.")


if __name__ == "__main__":
    main()
