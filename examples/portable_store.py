"""Try storage in an isolated directory that is removed when the demo ends."""

from pathlib import Path
from tempfile import TemporaryDirectory

from upref import ConfigStore


def main() -> None:
    """Demonstrate defaults, nested updates, and detached snapshots."""
    with TemporaryDirectory(prefix="upref-portable-") as directory:
        store = ConfigStore("portable-demo", directory=Path(directory).resolve())
        settings = store.load(defaults={"theme": "dark", "network": {"port": 8080}})
        assert not store.exists()  # Loading defaults never writes a file.
        store.save(settings)
        store.update({"network": {"port": 9000}})
        print(store.load())
        print(f"Original snapshot: {settings}")
        print(f"Temporary configuration: {store.path}")


if __name__ == "__main__":
    main()
