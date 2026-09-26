"""Maintain a bounded, most-recent-first history without opening any files."""

from os.path import normcase
from pathlib import Path
from tempfile import TemporaryDirectory

from upref import ConfigStore


def remember_file(store: ConfigStore, path: Path, *, limit: int = 5) -> list[str]:
    """Record an absolute path once, preserving unrelated preferences."""
    if type(limit) is not int or limit <= 0:
        raise ValueError("limit must be a positive integer")
    recent = store.load().get("recent_files", [])
    if not isinstance(recent, list) or not all(
        isinstance(item, str) for item in recent
    ):
        raise ValueError("recent_files must be a list of strings")
    candidate = str(path.expanduser().resolve())
    # Existing entries were normalized by earlier calls to this function.
    retained = [
        item
        for item in recent
        if isinstance(item, str) and normcase(item) != normcase(candidate)
    ]
    updated = [candidate, *retained][:limit]
    store.update({"recent_files": list(updated)})
    return updated


def main() -> None:
    """Move a reopened document to the front and trim the history."""
    with TemporaryDirectory(prefix="upref-recent-") as directory:
        root = Path(directory).resolve()
        store = ConfigStore("recent-demo", directory=root)
        store.save({"theme": "dark"})
        for name in ("notes.txt", "budget.csv", "draft.md", "notes.txt"):
            recent = remember_file(store, root / name, limit=2)
        print("Recent documents:", [Path(item).name for item in recent])
        print("Unrelated theme retained:", store.load()["theme"])


if __name__ == "__main__":
    main()
