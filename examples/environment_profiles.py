"""Select a saved environment profile and apply temporary runtime overrides."""

import os

from upref import Config, ConfigStore, ConfigValue


def require_mapping(value: ConfigValue, *, name: str) -> Config:
    """Return a configuration mapping or report an invalid saved shape."""
    if not isinstance(value, dict):
        raise TypeError(f"{name} must be a mapping")
    return value


def require_string(value: ConfigValue, *, name: str) -> str:
    """Return a string setting or report an invalid saved type."""
    if not isinstance(value, str):
        raise TypeError(f"{name} must be a string")
    return value


def require_integer(value: ConfigValue, *, name: str) -> int:
    """Return an integer setting while rejecting booleans."""
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{name} must be an integer")
    return value


def require_boolean(value: ConfigValue, *, name: str) -> bool:
    """Return a boolean setting or report an invalid saved type."""
    if not isinstance(value, bool):
        raise TypeError(f"{name} must be a boolean")
    return value


DEFAULTS: Config = {
    "active_profile": "development",
    "profiles": {
        "development": {
            "service_url": "http://localhost:8000",
            "timeout": 10,
            "debug": True,
        },
        "testing": {
            "service_url": "http://localhost:8001",
            "timeout": 5,
            "debug": False,
        },
        "production": {
            "service_url": "https://api.example.org",
            "timeout": 30,
            "debug": False,
        },
    },
}

store = ConfigStore("upref-profiles-example")
settings = store.load(defaults=DEFAULTS)
if not store.exists():
    store.save(settings)

profiles = require_mapping(settings["profiles"], name="profiles")
saved_profile = require_string(settings["active_profile"], name="active_profile")
profile_name = os.environ.get("UPREF_PROFILE", saved_profile)
if profile_name not in profiles:
    choices = ", ".join(sorted(profiles))
    raise ValueError(f"Unknown profile {profile_name!r}; choose one of: {choices}")

profile = require_mapping(profiles[profile_name], name=f"profiles.{profile_name}")
saved_service_url = require_string(profile["service_url"], name="service_url")
service_url = os.environ.get("UPREF_SERVICE_URL", saved_service_url)

saved_timeout = require_integer(profile["timeout"], name="timeout")
timeout_text = os.environ.get("UPREF_TIMEOUT")
timeout = saved_timeout if timeout_text is None else int(timeout_text)
if timeout <= 0:
    raise ValueError("UPREF_TIMEOUT must be greater than zero")
debug = require_boolean(profile["debug"], name="debug")

print(f"Profile: {profile_name}")
print(f"Service URL: {service_url}")
print(f"Timeout: {timeout} seconds")
print(f"Debug logging: {debug}")
print(f"Persistent configuration: {store.path}")
print("Environment-variable overrides were not persisted.")
