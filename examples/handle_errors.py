"""Report a malformed YAML file without silently replacing the user's data."""

from pathlib import Path
from tempfile import TemporaryDirectory

from upref import ConfigFormatError, ConfigReadError, ConfigStore


def main() -> None:
    """Demonstrate actionable diagnostics and preservation of the original file."""
    with TemporaryDirectory(prefix="upref-errors-") as directory:
        store = ConfigStore("errors-demo", directory=Path(directory).resolve())
        store.path.write_text("port: 8080\nport: 9000\n", encoding="utf-8")
        original = store.path.read_bytes()
        try:
            store.load()
        except ConfigFormatError as error:
            print(f"Fix the YAML file before retrying: {error}")
        except ConfigReadError as error:
            print(f"Check the file path and access rights: {error}")
        assert store.path.read_bytes() == original
        print("The original file was preserved.")


if __name__ == "__main__":
    main()
