"""Regression tests for source-level documentation coverage."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DOCUMENTED_SOURCES = tuple(
    sorted(
        [*PROJECT_ROOT.joinpath("upref").rglob("*.py")]
        + [*PROJECT_ROOT.joinpath("scripts").rglob("*.py")]
    )
)


@pytest.mark.parametrize(
    "source_path",
    DOCUMENTED_SOURCES,
    ids=lambda path: str(path.relative_to(PROJECT_ROOT)),
)
def test_modules_classes_and_functions_have_docstrings(source_path: Path) -> None:
    """Require a non-empty docstring on every Python declaration."""
    syntax_tree = ast.parse(
        source_path.read_text(encoding="utf-8-sig"),
        filename=str(source_path),
    )
    documented_nodes = (
        ast.Module,
        ast.ClassDef,
        ast.FunctionDef,
        ast.AsyncFunctionDef,
    )
    missing = []

    for node in ast.walk(syntax_tree):
        if not isinstance(node, documented_nodes):
            continue
        if ast.get_docstring(node, clean=True):
            continue

        name = "<module>" if isinstance(node, ast.Module) else node.name
        missing.append(f"line {getattr(node, 'lineno', 1)}: {name}")

    assert not missing, "Missing docstrings:\n" + "\n".join(missing)
