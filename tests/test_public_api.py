"""Stable package-level API tests."""

from __future__ import annotations

from importlib.resources import files
import sys

import upref


def test_package_import_does_not_load_optional_wxpython():
    assert "wx" not in sys.modules


def test_v2_symbols_are_exported():
    expected = {
        "ConfigStore",
        "Field",
        "collect",
        "ConfigFormatError",
        "ConfigReadError",
        "ConfigWriteError",
        "PromptCancelled",
    }

    assert expected.issubset(upref.__all__)
    assert upref.__version__.startswith("2.")


def test_gui_icon_is_packaged_as_a_resource():
    icon = files("upref.resources").joinpath("tower.ico")

    assert icon.is_file()
