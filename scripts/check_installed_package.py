# =============================================================================
#                 Author: Florent TOURNOIS | License: MIT
# =============================================================================
"""Verify installed resources and persistence without importing the checkout."""

from importlib.resources import files
from pathlib import Path
from tempfile import TemporaryDirectory

from upref import ConfigStore


def main() -> None:
    """Exercise the public storage API and resources of an installed wheel."""
    assert files("upref").joinpath("py.typed").is_file()
    assert (
        files("upref.resources").joinpath("tower.ico").read_bytes()[:4]
        == b"\x00\x00\x01\x00"
    )
    with TemporaryDirectory(prefix="upref-wheel-") as directory:
        store = ConfigStore("wheel-check", directory=Path(directory).resolve())
        assert not store.exists()
        assert store.load() == {}
        original = {"network": {"host": "localhost", "port": 8000}, "enabled": False}
        store.save(original)
        assert store.exists()
        assert store.load() == original
        updated = store.update({"network": {"port": 9000}})
        assert updated == {
            "network": {"host": "localhost", "port": 9000},
            "enabled": False,
        }
        assert store.load() == updated
        assert store.delete()
        assert not store.exists()
        assert not store.delete()
    print("Installed package: persistence and resources passed")


if __name__ == "__main__":
    main()
