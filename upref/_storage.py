#!/usr/bin/env python
# -*- coding: utf-8 -*-
# =============================================================================
#                 Author: Florent TOURNOIS | License: MIT
# =============================================================================
"""Read, atomically write, and delete Upref YAML configuration files.

The persistence boundary accepts only the runtime data model validated by
:func:`upref._types.normalize_config`. Files are encoded as UTF-8, and writes
are staged beside the destination before an atomic replacement so invalid data
or an interrupted serialization cannot truncate an existing configuration.
"""

from __future__ import annotations

import os
import tempfile
from collections.abc import Mapping
from pathlib import Path

import yaml

from ._types import Config, ConfigValue, normalize_config
from .errors import ConfigFormatError, ConfigReadError, ConfigWriteError

PathLike = str | os.PathLike[str]


def _display_path(path: PathLike) -> Path:
    """Normalize a path for reading and diagnostic messages.

    Args:
        path: String or path-like object identifying a configuration file.

    Returns:
        An expanded absolute path. The target is not required to exist and
        symbolic links are not resolved.

    Raises:
        ConfigReadError: If ``path`` cannot be converted to a filesystem path.
    """
    try:
        return Path(path).expanduser().absolute()
    except (TypeError, ValueError, OSError, RuntimeError) as error:
        raise ConfigReadError(f"Invalid configuration path: {path!r}") from error


def _yaml_error_location(error: yaml.YAMLError) -> str:
    """Extract a human-readable source location from a YAML error.

    Args:
        error: Exception raised by PyYAML while parsing a document.

    Returns:
        A one-based ``" at line N, column M"`` suffix when PyYAML provides a
        problem mark, otherwise an empty string.
    """
    mark = getattr(error, "problem_mark", None)
    if mark is None:
        return ""
    return f" at line {mark.line + 1}, column {mark.column + 1}"


def load_yaml(path: PathLike, *, missing_ok: bool = True) -> Config:
    """Load and validate one UTF-8 YAML mapping.

    An empty or explicit YAML ``null`` document represents an empty
    configuration. A missing file does too when ``missing_ok`` is true. The
    returned value is normalized into an independent tree of supported
    configuration values by :func:`normalize_config`.

    Args:
        path: String or path-like object identifying the YAML file.
        missing_ok: Return an empty mapping when the file is absent. When
            false, absence is reported as :class:`ConfigReadError`.

    Returns:
        A detached, plain-dictionary configuration. Empty YAML documents, and
        missing files when ``missing_ok`` is true, return an empty dictionary.

    Raises:
        ConfigFormatError: If the file is not valid UTF-8 YAML or its decoded
            value does not conform to the Upref configuration model.
        ConfigReadError: If the path is invalid, the file is missing while
            ``missing_ok`` is false, or the file cannot otherwise be opened or
            read.
    """
    resolved = _display_path(path)

    try:
        with resolved.open("r", encoding="utf-8") as stream:
            loaded: object = yaml.safe_load(stream)
    except FileNotFoundError as error:
        if missing_ok:
            return {}
        raise ConfigReadError(
            f"Configuration file does not exist: {resolved}"
        ) from error
    except yaml.YAMLError as error:
        location = _yaml_error_location(error)
        raise ConfigFormatError(
            f"Invalid YAML configuration in {resolved}{location}: {error}"
        ) from error
    except UnicodeDecodeError as error:
        raise ConfigFormatError(
            f"Configuration file is not valid UTF-8: {resolved}"
        ) from error
    except (OSError, ValueError) as error:
        raise ConfigReadError(
            f"Unable to read configuration file {resolved}: {error}"
        ) from error

    if loaded is None:
        loaded = {}

    try:
        return normalize_config(loaded)
    except ConfigFormatError as error:
        raise ConfigFormatError(
            f"Invalid configuration data in {resolved}: {error}"
        ) from error


def save_yaml(path: PathLike, data: Mapping[str, ConfigValue]) -> None:
    """Validate and atomically save configuration data as UTF-8 YAML.

    The data is normalized and serialized before the filesystem is changed. A
    temporary file is then written and flushed in the destination directory
    before :func:`os.replace` installs it. On POSIX, the staged file receives
    mode ``0600``. If replacement succeeds, the complete new document is
    visible; if it fails, the previous destination is left intact whenever the
    operating system provides atomic replacement semantics.

    Args:
        path: String or path-like destination for the YAML file.
        data: Configuration mapping to validate and persist. The mapping and
            its mutable descendants are not modified.

    Raises:
        ConfigFormatError: If ``data`` violates the Upref configuration model
            or cannot be represented as safe YAML.
        ConfigWriteError: If ``path`` is invalid, the destination directory or
            temporary file cannot be created, data cannot be written or
            flushed, permissions cannot be set, or replacement fails.
    """
    try:
        resolved = Path(path).expanduser().absolute()
    except (TypeError, ValueError, OSError, RuntimeError) as error:
        raise ConfigWriteError(f"Invalid configuration path: {path!r}") from error

    # Normalize and serialize before creating a directory or temporary file, so
    # invalid caller data can never disturb an existing configuration.
    try:
        normalized = normalize_config(data)
    except ConfigFormatError as error:
        raise ConfigFormatError(
            f"Invalid configuration data for {resolved}: {error}"
        ) from error

    try:
        serialized = yaml.safe_dump(
            normalized,
            allow_unicode=True,
            sort_keys=False,
            default_flow_style=False,
        )
    except yaml.YAMLError as error:
        raise ConfigFormatError(
            f"Unable to serialize configuration data for {resolved}: {error}"
        ) from error

    temporary_path: Path | None = None
    try:
        resolved.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            newline="\n",
            prefix=f".{resolved.name}.",
            suffix=".tmp",
            dir=resolved.parent,
            delete=False,
        ) as stream:
            temporary_path = Path(stream.name)
            stream.write(serialized)
            stream.flush()
            os.fsync(stream.fileno())

        if os.name == "posix":
            os.chmod(temporary_path, 0o600)
        os.replace(temporary_path, resolved)
    except (OSError, ValueError, UnicodeError) as error:
        raise ConfigWriteError(
            f"Unable to write configuration file {resolved}: {error}"
        ) from error
    finally:
        if temporary_path is not None:
            try:
                temporary_path.unlink(missing_ok=True)
            except OSError:
                # The primary persistence error is more useful than a cleanup
                # error, and a uniquely named temporary file is never loaded.
                pass


def delete_file(path: PathLike) -> bool:
    """Delete a configuration file if it exists.

    Args:
        path: String or path-like object identifying the file to remove.

    Returns:
        ``True`` when a file was removed, or ``False`` when the path did not
        exist.

    Raises:
        ConfigWriteError: If ``path`` is invalid or the file cannot be deleted
            for any reason other than its absence.
    """
    try:
        resolved = Path(path).expanduser().absolute()
    except (TypeError, ValueError, OSError, RuntimeError) as error:
        raise ConfigWriteError(f"Invalid configuration path: {path!r}") from error

    try:
        resolved.unlink()
    except FileNotFoundError:
        return False
    except (OSError, ValueError) as error:
        raise ConfigWriteError(
            f"Unable to delete configuration file {resolved}: {error}"
        ) from error
    return True
