"""Restore usable window geometry after a display size changes, without a GUI."""

from pathlib import Path
from tempfile import TemporaryDirectory

from upref import Config, ConfigStore, ConfigValue


def integer_or(value: ConfigValue, default: int) -> int:
    """Use an integer preference while excluding booleans and invalid types."""
    return value if type(value) is int else default


def restore_window(saved: Config, screen_width: int, screen_height: int) -> Config:
    """Fit geometry inside a primary display whose usable origin is (0, 0)."""
    if screen_width <= 0 or screen_height <= 0:
        raise ValueError("Screen dimensions must be positive")
    width = min(max(integer_or(saved.get("width"), 900), 320), screen_width)
    height = min(max(integer_or(saved.get("height"), 600), 240), screen_height)
    return {
        "x": min(max(integer_or(saved.get("x"), 0), 0), screen_width - width),
        "y": min(max(integer_or(saved.get("y"), 0), 0), screen_height - height),
        "width": width,
        "height": height,
        "maximized": saved.get("maximized") is True,
    }


def main() -> None:
    """Adapt saved geometry from a larger monitor to a 1280 by 720 display."""
    with TemporaryDirectory(prefix="upref-window-") as directory:
        store = ConfigStore("window-demo", directory=Path(directory).resolve())
        store.save({"window": {"x": 2500, "y": -200, "width": 1600, "height": 900}})
        saved = store.load()["window"]
        if not isinstance(saved, dict):
            raise ValueError("window must be a mapping")
        restored = restore_window(saved, 1280, 720)
        print("Visible window geometry:", restored)
        # In a real GUI, capture normal (not minimized) bounds on window close.
        store.update({"window": restored})


if __name__ == "__main__":
    main()
