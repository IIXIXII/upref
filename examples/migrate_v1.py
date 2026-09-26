"""Import values from an existing Upref v1 configuration."""

from upref import ConfigStore, UprefError

LEGACY_NAME = "my_personnal_data"
store = ConfigStore("upref-migration-example")

try:
    preview = store.import_legacy(LEGACY_NAME, source_format="auto", dry_run=True)
    print("Proposed keys:", ", ".join(sorted(preview)))
    # Use source_format="raw" when keys such as "value" are application data.
    # The import below reads the source again and repeats the target checks.
    migrated = store.import_legacy(LEGACY_NAME)
except UprefError as error:
    print(f"Migration was not performed: {error}")
else:
    print("Migrated keys:", ", ".join(sorted(migrated)))
    print(f"New configuration: {store.path}")
