"""Combine defaults, persist selected changes, then clean up the example."""

from upref import Config, ConfigStore


store = ConfigStore("upref-update-example")

defaults: Config = {
    "network": {
        "host": "localhost",
        "port": 8080,
    },
    "notifications": True,
}

config = store.load(defaults=defaults)
print("With defaults:", config)

# Loading defaults does not write them. Save the resolved configuration when
# the application wants those values to become persistent.
store.save(config)

updated = store.update(
    {
        "network": {"port": 9000},
        "notifications": False,
    }
)
print("Saved changes:", updated)

print("Configuration removed:", store.delete())
