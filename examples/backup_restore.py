"""Keep a configuration snapshot and restore it after an unwanted settings change."""

from pathlib import Path
from tempfile import TemporaryDirectory

from upref import ConfigStore


def restore_backup(store: ConfigStore, backup: ConfigStore) -> None:
    """Validate an existing backup completely before replacing the current file."""
    if not backup.exists():
        raise FileNotFoundError(f"No preferences backup: {backup.path}")
    # The demo assumes one writer; coordinate backup and restore in shared apps.
    restored = backup.load()
    store.save(restored)


def main() -> None:
    """Back up values, change them, and recover the earlier snapshot."""
    with TemporaryDirectory(prefix="upref-backup-") as directory:
        root = Path(directory).resolve()
        store = ConfigStore("backup-demo", directory=root)
        backup = ConfigStore("backup-demo", filename="backup.yaml", directory=root)
        store.save({"theme": "dark", "font_size": 16, "notifications": False})
        backup.save(store.load())  # A value snapshot, not a copy of YAML comments.
        before = backup.path.read_bytes()
        store.update({"theme": "light", "font_size": 30})
        print("Changed preferences:", store.load())
        restore_backup(store, backup)
        print("Restored preferences:", store.load())
        assert backup.path.read_bytes() == before


if __name__ == "__main__":
    main()
