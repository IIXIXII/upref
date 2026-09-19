"""Validate stored values against an application-specific dataclass."""

from dataclasses import asdict, dataclass
from pathlib import Path
from tempfile import TemporaryDirectory

from upref import Config, ConfigStore


@dataclass(frozen=True)
class Settings:
    """Describe the application model independently of the storage format."""

    host: str = "localhost"
    port: int = 8080
    enabled: bool = False

    @classmethod
    def from_config(cls, data: Config) -> "Settings":
        """Reject invalid saved values, including bool masquerading as int."""
        host, port, enabled = data["host"], data["port"], data["enabled"]
        if not isinstance(host, str) or not host.strip():
            raise ValueError("host must be non-empty text")
        if type(port) is not int or not 1 <= port <= 65535:
            raise ValueError("port must be an integer between 1 and 65535")
        if not isinstance(enabled, bool):
            raise ValueError("enabled must be a boolean")
        return cls(host=host, port=port, enabled=enabled)


def main() -> None:
    """Apply defaults, validate application constraints, and persist plain data."""
    with TemporaryDirectory(prefix="upref-typed-") as directory:
        store = ConfigStore("typed-demo", directory=Path(directory).resolve())
        raw = store.load(defaults=asdict(Settings()))
        settings = Settings.from_config(raw)
        store.save(asdict(settings))
        print(settings)


if __name__ == "__main__":
    main()
