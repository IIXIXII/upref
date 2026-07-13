"""Import values from an existing Upref v1 configuration."""

from upref import ConfigStore, UprefError


LEGACY_NAME = "my_personnal_data"
store = ConfigStore("upref-migration-example")

try:
    migrated = store.import_legacy(LEGACY_NAME)
except UprefError as error:
    print(f"Migration was not performed: {error}")
else:
    print("Migrated keys:", ", ".join(sorted(migrated)))
    print(f"New configuration: {store.path}")
