"""Export portable preferences and validate an import before explicitly applying it."""

import json
from pathlib import Path
from tempfile import TemporaryDirectory

from upref import Config, ConfigStore

PORTABLE_KEYS = ("theme", "font_size", "language")


def validate_portable(data: object) -> Config:
    """Accept a partial, known preference mapping and reject invalid values."""
    if not isinstance(data, dict) or any(key not in PORTABLE_KEYS for key in data):
        raise ValueError("Import must contain only theme, font_size, and language")
    result: Config = {}
    if "theme" in data:
        theme = data["theme"]
        if not isinstance(theme, str) or theme not in ("system", "light", "dark"):
            raise ValueError("Unsupported theme")
        result["theme"] = theme
    if "font_size" in data:
        font_size = data["font_size"]
        if type(font_size) is not int or not 10 <= font_size <= 32:
            raise ValueError("font_size must be an integer between 10 and 32")
        result["font_size"] = font_size
    if "language" in data:
        language = data["language"]
        if not isinstance(language, str) or language not in ("en", "fr"):
            raise ValueError("Unsupported language")
        result["language"] = language
    return result


def export_preferences(store: ConfigStore, destination: Path) -> None:
    """Write only portable preferences, excluding machine-local and private keys."""
    saved = store.load()
    portable = validate_portable(
        {key: saved[key] for key in PORTABLE_KEYS if key in saved}
    )
    destination.write_text(
        json.dumps(portable, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def unique_keys(pairs: list[tuple[str, object]]) -> dict[str, object]:
    """Reject repeated JSON keys rather than silently choosing the last value."""
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"Duplicate preference key: {key}")
        result[key] = value
    return result


def preview_import(source: Path) -> Config:
    """Read and validate a JSON import without changing any saved preference."""
    return validate_portable(
        json.loads(source.read_text(encoding="utf-8"), object_pairs_hook=unique_keys)
    )


def main() -> None:
    """Transfer appearance preferences while retaining local document history."""
    with TemporaryDirectory(prefix="upref-transfer-") as directory:
        root = Path(directory).resolve()
        source = ConfigStore("transfer-demo", filename="source.yaml", directory=root)
        target = ConfigStore("transfer-demo", filename="target.yaml", directory=root)
        source.save(
            {
                "theme": "dark",
                "font_size": 18,
                "language": "fr",
                "recent_files": ["source-only.txt"],
            }
        )
        target.save({"theme": "light", "recent_files": ["target-only.txt"]})
        export = root / "preferences.json"
        export_preferences(source, export)
        before = target.path.read_bytes()
        preview = preview_import(export)
        print("Validated import preview:", preview)
        assert target.path.read_bytes() == before
        target.update(preview)  # The application explicitly chooses to apply it.
        print("Local history retained:", target.load()["recent_files"])


if __name__ == "__main__":
    main()
