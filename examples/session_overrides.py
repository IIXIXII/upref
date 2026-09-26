"""Apply CLI preferences for this session, persisting them only with --remember."""

import argparse
from collections.abc import Sequence
from pathlib import Path
from tempfile import TemporaryDirectory

from upref import Config, ConfigStore

DEFAULTS: Config = {"theme": "system", "font_size": 14, "language": "en"}


def font_size_argument(raw: str) -> int:
    """Parse a CLI font size in the application's supported range."""
    try:
        size = int(raw)
    except ValueError as error:
        raise argparse.ArgumentTypeError("font size must be an integer") from error
    if not 10 <= size <= 32:
        raise argparse.ArgumentTypeError("font size must be between 10 and 32")
    return size


def session_preferences(
    store: ConfigStore, overrides: Config, *, remember: bool = False
) -> Config:
    """Use defaults below saved values below already validated CLI overrides."""
    resolved = store.load(defaults=DEFAULTS)
    resolved.update(overrides)  # These preferences are flat scalar values.
    if remember and overrides:
        store.update(overrides)  # Persist only explicit overrides, not all defaults.
    return resolved


def main(argv: Sequence[str] | None = None) -> None:
    """Compare effective and saved preferences inside an isolated demo store."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--theme", choices=("system", "light", "dark"))
    parser.add_argument("--font-size", type=font_size_argument)
    parser.add_argument(
        "--remember", action="store_true", help="save CLI overrides in the demo store"
    )
    arguments = parser.parse_args(argv)
    overrides: Config = {}
    if arguments.theme is not None:
        overrides["theme"] = arguments.theme
    if arguments.font_size is not None:
        overrides["font_size"] = arguments.font_size
    with TemporaryDirectory(prefix="upref-session-") as directory:
        store = ConfigStore("session-demo", directory=Path(directory).resolve())
        store.save({"theme": "light", "font_size": 16})
        effective = session_preferences(store, overrides, remember=arguments.remember)
        print("This session:", effective)
        print("Saved overrides:", store.load())
        print("The demo directory is removed on exit, including with --remember.")


if __name__ == "__main__":
    main()
