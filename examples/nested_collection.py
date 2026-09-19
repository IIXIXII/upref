"""Collect a nested section and save only after the whole interaction succeeds."""

from pathlib import Path
from tempfile import TemporaryDirectory

from upref import ConfigStore, Field, PromptCancelled, collect
from upref.tty import TTYPrompter


def main() -> None:
    """Edit a network section while preserving unrelated preferences."""
    with TemporaryDirectory(prefix="upref-nested-") as directory:
        store = ConfigStore("nested-demo", directory=Path(directory).resolve())
        settings = store.load(
            defaults={"theme": "dark", "network": {"host": "localhost", "port": 8080}}
        )
        network = settings["network"]
        if not isinstance(network, dict):
            raise ValueError("network must be a mapping")
        try:
            settings["network"] = collect(
                {
                    "host": Field(
                        "Host",
                        parser=str.strip,
                        validator=lambda value: isinstance(value, str) and bool(value),
                    ),
                    "port": Field(
                        "Port",
                        parser=int,
                        validator=lambda value: (
                            type(value) is int and 1 <= value <= 65535
                        ),
                    ),
                },
                initial=network,
                interface=TTYPrompter(keep_current=True),
                mode="all",
            )
        except PromptCancelled:
            print("Cancelled; no file was written.")
        else:
            store.save(settings)
            print(store.load())
            print("This demonstration file is removed on exit.")


if __name__ == "__main__":
    main()
