"""Expose Upref's stable per-user configuration API.

The package-level API centers on :class:`ConfigStore` for explicit YAML
persistence and :func:`collect` for optional interactive value collection.
Importing :mod:`upref` never imports wxPython, reads configuration, or opens
an interactive interface.

Historical v1 functions remain importable during the v2 transition. They emit
:class:`DeprecationWarning` and are documented in :mod:`upref.legacy`.
"""

from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version

from ._types import Config, ConfigValue
from .core import ConfigStore
from .errors import (
    ConfigFormatError,
    ConfigPathError,
    ConfigReadError,
    ConfigWriteError,
    MigrationError,
    PromptCancelled,
    PromptUnavailableError,
    UprefError,
)
from .legacy import (
    current_upref,
    get_pref,
    load_conf,
    load_data,
    remove_pref,
    save_conf,
    save_data,
    set_pref,
    upref_filename,
)
from .prompt import Field, Prompter, collect


try:
    __version__ = version("upref")
except PackageNotFoundError:
    # Source trees that are not installed still expose a useful v2 version.
    __version__ = "2.0.0"

__author__ = "Florent Tournois"
__copyright__ = "Copyright 2018-2026, Florent Tournois"
__license__ = "MIT"


__all__ = [
    "Config",
    "ConfigFormatError",
    "ConfigPathError",
    "ConfigReadError",
    "ConfigStore",
    "ConfigValue",
    "ConfigWriteError",
    "Field",
    "MigrationError",
    "Prompter",
    "PromptCancelled",
    "PromptUnavailableError",
    "UprefError",
    "collect",
    # Deprecated v1 compatibility API.
    "current_upref",
    "get_pref",
    "load_conf",
    "load_data",
    "remove_pref",
    "save_conf",
    "save_data",
    "set_pref",
    "upref_filename",
]
