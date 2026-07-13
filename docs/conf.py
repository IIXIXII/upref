"""Sphinx configuration for the Upref documentation."""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

import upref  # noqa: E402  (the source tree must be importable first)

# Project information
project = "upref"
author = upref.__author__
copyright = f"2026, {author}"
release = upref.__version__
version = ".".join(release.split(".")[:2])

# General configuration
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.napoleon",
    "myst_parser",
]

autosummary_generate = True
autodoc_member_order = "bysource"
autodoc_typehints = "description"
nitpicky = True
nitpick_ignore_regex = [
    ("py:class", r"(collections\.abc\.)?(Callable|Mapping)"),
    ("py:class", r"(os\.)?PathLike"),
    ("py:class", r"pathlib\.Path"),
    ("py:class", r"(PrintFunction|ReadFunction)"),
    ("py:func", r"(getpass\.getpass|input|print)"),
    ("py:mod", r"platformdirs"),
]

source_suffix = {
    ".rst": "restructuredtext",
    ".md": "markdown",
}
root_doc = "index"
language = "en"
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

# HTML output
html_theme = "sphinx_rtd_theme"
html_static_path = ["layout"]
html_css_files = ["extra.css"]
