"""Upgrade an application's own configuration schema independently of Upref v1."""

from copy import deepcopy
from pathlib import Path
from tempfile import TemporaryDirectory

from upref import Config, ConfigStore


def upgrade(data: Config) -> Config:
    """Return an upgraded copy, rejecting unknown or ambiguous schema versions."""
    result = deepcopy(data)
    version = result.get("schema_version", 1)
    if type(version) is not int or version not in (1, 2):
        raise ValueError(f"Unsupported schema version: {version!r}")
    if version == 1:
        if "network" in result:
            raise ValueError(
                "Version 1 unexpectedly contains network; inspect manually"
            )
        host = result.pop("host", "localhost")
        port = result.pop("port", 8080)
        if not isinstance(host, str) or type(port) is not int:
            raise ValueError("Version 1 requires a string host and an integer port")
        result["network"] = {"host": host, "port": port}
        result["schema_version"] = 2
    return result


def main() -> None:
    """Migrate a demonstration file and show that a second upgrade is harmless."""
    with TemporaryDirectory(prefix="upref-upgrade-") as directory:
        store = ConfigStore("upgrade-demo", directory=Path(directory).resolve())
        store.save({"host": "localhost", "port": 8080, "theme": "dark"})
        original = store.load()
        migrated = upgrade(original)
        # In production, retain a backup and coordinate with other writers.
        store.save(migrated)
        assert upgrade(store.load()) == migrated
        print(f"Before: {original}")
        print(f"After: {store.load()}")


if __name__ == "__main__":
    main()
