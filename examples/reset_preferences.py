"""Remove saved overrides to restore one preference, a section, or all defaults."""

from pathlib import Path
from tempfile import TemporaryDirectory

from upref import Config, ConfigStore

DEFAULTS: Config = {
    "appearance": {"theme": "system", "font_size": 14},
    "notifications": True,
}


def main() -> None:
    """Show why deleting an override differs from saving a resolved default."""
    with TemporaryDirectory(prefix="upref-reset-") as directory:
        store = ConfigStore("reset-demo", directory=Path(directory).resolve())
        store.save(
            {
                "appearance": {"theme": "dark", "font_size": 20},
                "notifications": False,
            }
        )
        saved = store.load()  # Do not merge defaults into the data being edited.
        appearance = saved["appearance"]
        if not isinstance(appearance, dict):
            raise ValueError("appearance must be a mapping")
        appearance.pop("font_size", None)
        store.save(saved)
        print("One preference reset:", store.load(defaults=DEFAULTS))

        saved = store.load()
        saved.pop("appearance", None)
        store.save(saved)  # update({'appearance': {}}) would retain old nested keys.
        print(
            "Appearance reset; notifications retained:", store.load(defaults=DEFAULTS)
        )
        assert store.load() == {"notifications": False}

        store.delete()
        print("All defaults restored:", store.load(defaults=DEFAULTS))
        assert not store.exists()  # Loading defaults does not recreate the file.


if __name__ == "__main__":
    main()
