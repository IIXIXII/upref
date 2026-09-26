"""Preview an ambiguous v1 file and explicitly preserve its raw preference data."""

from pathlib import Path
from tempfile import TemporaryDirectory

from upref import ConfigStore


def main() -> None:
    """Compare auto and raw conversions without touching real legacy settings."""
    with TemporaryDirectory(prefix="upref-migration-preview-") as directory:
        root = Path(directory).resolve()
        legacy = ConfigStore("migration-demo", filename="old.conf", directory=root)
        legacy.save({"reminder_interval": {"value": 30, "unit": "minutes"}})
        original = legacy.path.read_bytes()
        store = ConfigStore("migration-demo", directory=root / "v2")
        automatic = store.import_legacy("old", legacy_directory=root, dry_run=True)
        preview = store.import_legacy(
            "old",
            legacy_directory=root,
            source_format="raw",
            dry_run=True,
        )
        print("Auto preview loses the unit:", automatic)
        print("Raw preview preserves the unit:", preview)
        assert not store.path.parent.exists()
        imported = store.import_legacy(
            "old", legacy_directory=root, source_format="raw"
        )
        assert imported == preview
        assert legacy.path.read_bytes() == original
        print("Migration applied; legacy file unchanged.")


if __name__ == "__main__":
    main()
