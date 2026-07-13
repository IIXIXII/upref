"""Save and reload a small per-user configuration."""

from upref import ConfigStore


store = ConfigStore("upref-basic-example")

store.save(
    {
        "theme": "dark",
        "notifications": True,
    }
)

config = store.load()
print(config)
print(f"Configuration saved to: {store.path}")
