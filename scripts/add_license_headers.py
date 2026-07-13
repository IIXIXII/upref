#!/usr/bin/env python
# -*- coding: utf-8 -*-
# =============================================================================
#                 Author: Florent TOURNOIS | License: MIT
# =============================================================================
"""Inject a consistent MIT license marker into supported text files.

- Scans recursively from ../ (relative to this script location)
- Adds a centered MIT header when the first 150 lines contain no marker or MIT notice
- Supports multiple file types with appropriate comment syntax
- Preserves a UTF-8 BOM, Python shebang/coding cookie, and shell shebang
- Default: dry-run. Use --write to apply changes.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Iterable, Tuple

MARKER = "Author: Florent TOURNOIS | License: MIT"
SCAN_LINES = 150

# PEP 263 coding cookie (must be in line 1 or 2 of file, after optional shebang)
CODING_RE = re.compile(r"^[ \t\f]*#\s*.*coding[:=]\s*([-\w.]+)", re.IGNORECASE)


# -----------------------------------------------------------------------------
# Comment style registry
# -----------------------------------------------------------------------------
# Each entry defines how to build a header and where to insert it.
# - line_comment: prefix used for line comment headers ("# ", "REM ", etc.)
# - block_comment: (open, close) for block comment headers ("/*", "*/", "<!--", "-->")
# - keep_shebang: preserve "#!" line at top if present
# - keep_coding: preserve coding cookie after shebang (Python only)
# - keep_echo_off: preserve "@ECHO OFF" (bat/cmd)
SUPPORTED = {
    # Python
    ".py": dict(
        line_comment="#",
        block_comment=None,
        keep_shebang=True,
        keep_coding=True,
        keep_echo_off=False,
    ),
    # Windows batch
    ".bat": dict(
        line_comment="REM",
        block_comment=None,
        keep_shebang=False,
        keep_coding=False,
        keep_echo_off=True,
    ),
    ".cmd": dict(
        line_comment="REM",
        block_comment=None,
        keep_shebang=False,
        keep_coding=False,
        keep_echo_off=True,
    ),
    # Config/text with # comments
    ".conf": dict(
        line_comment="#",
        block_comment=None,
        keep_shebang=False,
        keep_coding=False,
        keep_echo_off=False,
    ),
    ".ini": dict(
        line_comment="#",
        block_comment=None,
        keep_shebang=False,
        keep_coding=False,
        keep_echo_off=False,
    ),
    ".cfg": dict(
        line_comment="#",
        block_comment=None,
        keep_shebang=False,
        keep_coding=False,
        keep_echo_off=False,
    ),
    ".toml": dict(
        line_comment="#",
        block_comment=None,
        keep_shebang=False,
        keep_coding=False,
        keep_echo_off=False,
    ),
    ".yaml": dict(
        line_comment="#",
        block_comment=None,
        keep_shebang=False,
        keep_coding=False,
        keep_echo_off=False,
    ),
    ".yml": dict(
        line_comment="#",
        block_comment=None,
        keep_shebang=False,
        keep_coding=False,
        keep_echo_off=False,
    ),
    # PowerShell
    ".ps1": dict(
        line_comment="#",
        block_comment=None,
        keep_shebang=False,
        keep_coding=False,
        keep_echo_off=False,
    ),
    # Shell scripts
    ".sh": dict(
        line_comment="#",
        block_comment=None,
        keep_shebang=True,
        keep_coding=False,
        keep_echo_off=False,
    ),
    # Markdown (HTML comment block)
    ".md": dict(
        line_comment=None,
        block_comment=("<!--", "-->"),
        keep_shebang=False,
        keep_coding=False,
        keep_echo_off=False,
    ),
    # # JS/TS/CSS (block comment)
    # ".js": dict(line_comment=None, block_comment=("/*", "*/"), keep_shebang=False, keep_coding=False, keep_echo_off=False),
    # ".ts": dict(line_comment=None, block_comment=("/*", "*/"), keep_shebang=False, keep_coding=False, keep_echo_off=False),
    # ".css": dict(line_comment=None, block_comment=("/*", "*/"), keep_shebang=False, keep_coding=False, keep_echo_off=False),
}


def centered_line(prefix: str, text: str, width: int = 79) -> str:
    """Build one fixed-width, centered line-comment line.

    Args:
        prefix: Comment token, such as ``#`` or ``REM``. Surrounding
            whitespace is removed before a single trailing space is added.
        text: Text to center in the available width.
        width: Desired total line width, including the comment prefix.

    Returns:
        A string containing exactly ``width`` characters. Text that is too
        long is truncated on the right.

    Raises:
        ValueError: If the normalized prefix leaves no room for content.
    """
    prefix = prefix.strip()
    prefix = f"{prefix} "  # ensure single trailing space
    available = width - len(prefix)
    if available <= 0:
        raise ValueError("Prefix too long for requested width")

    left_pad = max(0, (available - len(text)) // 2)
    line = prefix + (" " * left_pad) + text

    if len(line) < width:
        line += " " * (width - len(line))
    else:
        line = line[:width]
    return line


def line_header(prefix: str, width: int = 79) -> Tuple[str, ...]:
    """Build a three-line header using line-comment syntax.

    Args:
        prefix: Supported line-comment token, normally ``#`` or ``REM``.
        width: Desired width of the centered marker line. The historical
            separator lines remain fixed at 79 characters.

    Returns:
        Separator, centered marker, and closing-separator lines.

    Raises:
        ValueError: If ``width`` leaves no room for the marker-line prefix.
    """
    if prefix.upper() == "REM":
        sep = "REM " + ("=" * 75)  # 4 + 75 = 79
        mid = centered_line("REM", MARKER, width)
        return (sep, mid, sep)

    # default '#'
    sep = "# " + ("=" * 77)  # 2 + 77 = 79
    mid = centered_line("#", MARKER, width)
    return (sep, mid, sep)


def block_header(open_tok: str, close_tok: str, width: int = 79) -> Tuple[str, ...]:
    """Build a compact five-line block-comment header.

    The opening and closing tokens keep their natural length. Separator lines
    use ``width`` characters. The marker receives enough leading whitespace
    to be centered within that width and is truncated when necessary; it is
    not padded on the right.

    Args:
        open_tok: Block-comment opening token, for example ``<!--``.
        close_tok: Matching block-comment closing token.
        width: Width of separator lines and the marker's centering boundary.

    Returns:
        Opening token, separator, marker, separator, and closing token.
    """
    # For block formats, we keep the centered content line with a neutral prefix
    # Example:
    # <!--
    # =============================================================================
    #                 Author: ... | License: MIT
    # =============================================================================
    # -->
    sep = "=" * width
    mid = (" " * max(0, (width - len(MARKER)) // 2)) + MARKER
    mid = mid[:width]
    return (open_tok, sep, mid, sep, close_tok)


def header_for(ext: str) -> Tuple[str, ...]:
    """Build the registered header style for a file extension.

    Args:
        ext: Lowercase extension, including its leading dot.

    Returns:
        Header lines without newline characters.

    Raises:
        KeyError: If ``ext`` is not registered in :data:`SUPPORTED`.
        ValueError: If the registered entry has no usable comment style.
    """
    spec = SUPPORTED[ext]
    if spec["line_comment"]:
        return line_header(spec["line_comment"])
    if spec["block_comment"]:
        o, c = spec["block_comment"]
        return block_header(o, c)
    raise ValueError(f"No header style for extension: {ext}")


def is_text_file(path: Path) -> bool:
    """Return whether a readable path appears to contain text.

    The check is intentionally conservative: unreadable files and files with
    a NUL byte in their first 4096 bytes are rejected.

    Args:
        path: Candidate filesystem path.

    Returns:
        ``True`` for readable files without an early NUL byte.
    """
    try:
        data = path.read_bytes()
    except OSError:
        return False
    if b"\x00" in data[:4096]:
        return False
    return True


def marker_present(lines: Iterable[str]) -> bool:
    """Return whether any supplied line contains the exact license marker.

    Args:
        lines: Lines to scan, typically the beginning of a text file.

    Returns:
        ``True`` as soon as :data:`MARKER` is found.
    """
    return any(MARKER in line for line in lines)


def compute_insertion_index(ext: str, lines: list[str]) -> int:
    """Compute where a header may be inserted without breaking file preambles.

    The registered policy preserves a shebang, a Python coding cookie, and an
    early ``@ECHO OFF`` statement when applicable. All other formats insert at
    the beginning.

    Args:
        ext: Registered lowercase extension, including its leading dot.
        lines: Original lines with line endings preserved.

    Returns:
        Zero-based insertion index into ``lines``.

    Raises:
        KeyError: If ``ext`` is not registered in :data:`SUPPORTED`.
    """
    spec = SUPPORTED[ext]
    i = 0

    if spec.get("keep_shebang") and lines and lines[0].startswith("#!"):
        i = 1

    if ext == ".py" and spec.get("keep_coding"):
        if len(lines) > i and CODING_RE.match(lines[i].rstrip("\r\n")):
            i += 1
        elif (
            i == 0
            and len(lines) > 1
            and (not lines[0].strip() or lines[0].lstrip().startswith("#"))
            and CODING_RE.match(lines[1].rstrip("\r\n"))
        ):
            # PEP 263 permits a cookie on line two when line one is blank or
            # a comment. Preserve both lines so insertion cannot move the
            # cookie outside the interpreter-recognized preamble.
            i = 2

    if spec.get("keep_echo_off"):
        # Find @ECHO OFF early (some files start with blanks)
        for j in range(min(5, len(lines))):
            if lines[j].strip() == "":
                continue
            if lines[j].strip().lower() == "@echo off":
                return j + 1
            break

    return i


def ensure_newline(s: str) -> str:
    r"""Return ``s`` with exactly the existing or one added trailing newline.

    Args:
        s: Generated header line.

    Returns:
        ``s`` unchanged when it already ends in ``\n``; otherwise ``s`` plus
        one newline.
    """
    return s if s.endswith("\n") else s + "\n"


def process_file(path: Path, write: bool) -> Tuple[bool, str]:
    """Inspect one file and optionally insert its registered license header.

    Markers and conservative ``License: MIT`` matches within the first
    :data:`SCAN_LINES` lines are not duplicated. Read and write failures are
    converted to status strings so a recursive scan can continue processing
    other files.

    Write mode rewrites the source path directly without locking or atomic
    replacement. Callers should review dry-run output and keep source files in
    version control. An existing UTF-8 BOM remains the first bytes of the file.

    Args:
        path: Candidate file to inspect.
        write: Apply the modification when true; otherwise perform a dry run.

    Returns:
        A ``(changed, status)`` pair. ``changed`` indicates a planned or
        completed modification. ``status`` begins with ``keep:``, ``skip:``,
        ``dryrun:``, ``write:``, or ``error:``.
    """
    ext = path.suffix.lower()
    if ext not in SUPPORTED:
        return (False, "skip:unsupported")

    if not is_text_file(path):
        return (False, "skip:binary")

    try:
        raw = path.read_text(encoding="utf-8", errors="surrogateescape")
    except Exception as e:
        return (False, f"skip:read_error:{e}")

    has_utf8_bom = raw.startswith("\ufeff")
    content = raw[1:] if has_utf8_bom else raw
    lines = content.splitlines(keepends=True)
    head = [line.rstrip("\n") for line in lines[:SCAN_LINES]]

    # Marker already present => keep
    if marker_present(head):
        return (False, "keep:marker_present")

    # Conservative: if any MIT mention exists, keep (avoid partial duplicates)
    if any("License: MIT" in line for line in head):
        return (False, "keep:license_detected")

    hdr = header_for(ext)
    hdr_lines = [ensure_newline(h) for h in hdr] + [ensure_newline("")]

    idx = compute_insertion_index(ext, lines)
    new_raw = ("\ufeff" if has_utf8_bom else "") + "".join(
        lines[:idx] + hdr_lines + lines[idx:]
    )

    if not write:
        return (True, "dryrun:would_modify")

    try:
        path.write_text(new_raw, encoding="utf-8", errors="surrogateescape", newline="")
    except Exception as e:
        return (False, f"error:write_error:{e}")

    return (True, "write:modified")


def iter_targets(root: Path, include_hidden: bool) -> Iterable[Path]:
    """Yield supported text-file candidates below a root directory.

    Args:
        root: Directory traversed recursively.
        include_hidden: Include normally skipped VCS, environment, cache,
            build, dependency, and test directories when true.

    Yields:
        Non-symlink files whose lowercase suffix is present in
        :data:`SUPPORTED`.

    Raises:
        OSError: If recursive traversal or file inspection fails before an
            individual candidate reaches :func:`process_file`.
    """
    skip_dirs = {
        ".git",
        ".venv",
        ".eggs",
        "__pycache__",
        "node_modules",
        "dist",
        "build",
        ".mypy_cache",
        ".pytest_cache",
        ".ruff_cache",
        "tests",
    }
    for p in root.rglob("*"):
        if not p.is_file() or p.is_symlink():
            continue
        if not include_hidden:
            parts = {part.lower() for part in p.relative_to(root).parts}
            if any(d in parts for d in skip_dirs):
                continue
        if p.suffix.lower() in SUPPORTED:
            yield p


def main(argv: list[str]) -> int:
    """Run the command-line scanner.

    Args:
        argv: Command-line arguments excluding the executable name.

    Returns:
        ``0`` when scanning completes without write errors, ``1`` when at
        least one file fails to write, or ``2`` when the root is not an
        existing directory.
    """
    parser = argparse.ArgumentParser(
        description="Scan ../ and add MIT header if missing (multi-format). Default is dry-run."
    )
    parser.add_argument(
        "--root",
        default=str((Path(__file__).resolve().parent / "..").resolve()),
        help="Root directory to scan (default: ../ relative to this script).",
    )
    parser.add_argument(
        "--write",
        action="store_true",
        help="Apply changes (default: dry-run only).",
    )
    parser.add_argument(
        "--include-hidden",
        action="store_true",
        help="Include hidden/build dirs (.git, .venv, dist, build...).",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Verbose output (print all processed files).",
    )
    args = parser.parse_args(argv)

    root = Path(args.root).resolve()
    if not root.is_dir():
        print(f"ERROR: root is not an existing directory: {root}", file=sys.stderr)
        return 2

    mode = "WRITE" if args.write else "DRY-RUN"
    exts = ", ".join(sorted(SUPPORTED.keys()))
    print(f"[START] mode={mode} root={root}")
    print(f"[INFO] supported extensions: {exts}")

    found = kept = modified = skipped = errors = 0

    for path in iter_targets(root, args.include_hidden):
        found += 1
        changed, status = process_file(path, write=args.write)

        if status.startswith("keep:"):
            kept += 1
        elif status.startswith("skip:"):
            skipped += 1
        elif status.startswith("error:"):
            errors += 1
        else:
            modified += 1

        if args.verbose or status.startswith(("error:", "dryrun:", "write:")):
            print(f"{status:18} {path}")

    print("[SUMMARY]")
    print(f"  files matched : {found}")
    print(f"  kept          : {kept}")
    print(f"  modified      : {modified}")
    print(f"  skipped       : {skipped}")
    print(f"  errors        : {errors}")

    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
