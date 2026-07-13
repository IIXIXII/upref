"""Behavioral tests for the license-header maintenance utility."""

from __future__ import annotations

import pytest

from scripts.add_license_headers import (
    MARKER,
    compute_insertion_index,
    iter_targets,
    main,
    process_file,
)


def test_preserves_python_shebang_and_coding_cookie() -> None:
    """Insert after a shebang followed by a PEP 263 coding cookie."""
    lines = ["#!/usr/bin/env python\n", "# -*- coding: latin-1 -*-\n", "value = 1\n"]

    assert compute_insertion_index(".py", lines) == 2


def test_preserves_second_line_coding_cookie_without_shebang() -> None:
    """Keep a valid second-line cookie within Python's two-line preamble."""
    lines = ["# module comment\n", "# coding: latin-1\n", "value = 1\n"]

    assert compute_insertion_index(".py", lines) == 2


def test_recognizes_an_indented_python_coding_cookie() -> None:
    """Honor the leading whitespace accepted by Python's PEP 263 parser."""
    lines = ["  # coding: latin-1\n", "value = 1\n"]

    assert compute_insertion_index(".py", lines) == 1


def test_does_not_preserve_invalid_late_coding_cookie() -> None:
    """Insert at the top when executable code makes a later cookie invalid."""
    lines = ["value = 1\n", "# coding: latin-1\n"]

    assert compute_insertion_index(".py", lines) == 0


def test_target_scan_does_not_follow_file_symlinks(tmp_path) -> None:
    """Keep write-mode candidates confined to real files below the root."""
    target = tmp_path / "target.py"
    target.write_text("value = 1\n", encoding="utf-8")
    link = tmp_path / "link.py"
    try:
        link.symlink_to(target)
    except OSError as error:
        pytest.skip(f"Symlinks are not available: {error}")

    candidates = set(iter_targets(tmp_path, include_hidden=False))

    assert target in candidates
    assert link not in candidates


def test_exclusions_are_relative_to_the_scan_root(tmp_path) -> None:
    """Do not skip a project merely because an ancestor is named build."""
    root = tmp_path / "build" / "project"
    root.mkdir(parents=True)
    source = root / "module.py"
    source.write_text("value = 1\n", encoding="utf-8")

    assert list(iter_targets(root, include_hidden=False)) == [source]


def test_write_preserves_a_utf8_bom_as_the_first_bytes(tmp_path) -> None:
    """Keep a UTF-8 BOM before an inserted Python comment header."""
    source = tmp_path / "module.py"
    source.write_bytes(b"\xef\xbb\xbfvalue = 1\n")

    changed, status = process_file(source, write=True)
    written = source.read_bytes()

    assert changed is True
    assert status == "write:modified"
    assert written.startswith(b"\xef\xbb\xbf")
    assert MARKER.encode() in written


def test_cli_rejects_a_file_as_the_scan_root(tmp_path, capsys) -> None:
    """Report command-line misuse instead of succeeding with zero targets."""
    source = tmp_path / "module.py"
    source.write_text("value = 1\n", encoding="utf-8")

    result = main(["--root", str(source)])

    assert result == 2
    assert "not an existing directory" in capsys.readouterr().err
