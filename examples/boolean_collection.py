"""Collect a boolean and an optional note without saving anything."""

from upref import Field, PromptCancelled, collect, parse_bool


def main() -> None:
    """Ask for two values, retry invalid input, and handle cancellation."""
    schema = {
        "notifications": Field("Enable notifications", parser=parse_bool),
        "note": Field("Optional note", required=False),
    }
    try:
        print(collect(schema))
    except PromptCancelled:
        print("Cancelled; no values saved.")


if __name__ == "__main__":
    main()
