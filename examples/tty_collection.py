"""Ask only for missing values in a terminal, then save them explicitly."""

from upref import ConfigStore, Field, PromptCancelled, collect


store = ConfigStore("upref-tty-example")
schema = {
    "service_url": Field(
        "Service URL",
        description="For example: https://api.example.org",
    ),
    "timeout": Field(
        "Timeout in seconds",
        parser=int,
        validator=lambda value: isinstance(value, int) and value > 0,
    ),
}

try:
    values = collect(
        schema,
        initial=store.load(),
        interface="tty",
        mode="missing",
    )
except PromptCancelled:
    print("Input cancelled; the configuration was not changed.")
else:
    store.save(values)
    print(f"Configuration saved to: {store.path}")
