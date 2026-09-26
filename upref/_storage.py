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
from contextlib import ExitStack
from pathlib import Path
from typing import TextIO

import yaml

from ._types import Config, ConfigValue, normalize_config
from .errors import ConfigFormatError, ConfigReadError, ConfigWriteError

PathLike = str | os.PathLike[str]


class _ConfigLoader(yaml.SafeLoader):
    """Reject duplicate explicit keys while preserving YAML merge semantics."""

    def __init__(self, stream: TextIO) -> None:
        """Track checked nodes because aliases may revisit flattened mappings."""
        super().__init__(stream)
        self._checked_mappings: set[yaml.MappingNode] = set()

    def flatten_mapping(self, node: yaml.MappingNode) -> None:
        """Check explicit keys before recursively resolving merge directives."""
        if node in self._checked_mappings:
            return
        self._checked_mappings.add(node)
        seen: set[tuple[str, str]] = set()
        for key_node, _ in node.value:
            # Merge keys are directives; their inherited keys may be overridden.
            if not isinstance(key_node, yaml.ScalarNode) or key_node.tag not in {
                "tag:yaml.org,2002:str",
                "tag:yaml.org,2002:merge",
            }:
                raise yaml.constructor.ConstructorError(
                    "while reading a configuration mapping",
                    node.start_mark,
                    "expected a string mapping key",
                    key_node.start_mark,
                )
            key = (key_node.tag, key_node.value)
            if key in seen:
                raise yaml.constructor.ConstructorError(
                    "while reading a configuration mapping",
                    node.start_mark,
                    f"duplicate mapping key {key_node.value!r}",
                    key_node.start_mark,
                )
            seen.add(key)
        super().flatten_mapping(node)


class _ConfigDumper(yaml.SafeDumper):
    """Preserve Unicode NEL characters that YAML otherwise folds into spaces."""

    def represent_str(self, data: str) -> yaml.ScalarNode:
        """Escape NEL using double quotes while keeping other Unicode readable."""
        return self.represent_scalar(
            "tag:yaml.org,2002:str", data, style='"' if "\x85" in data else None
        )


_ConfigDumper.add_representer(str, _ConfigDumper.represent_str)


def _remove_temporary_file(path: Path) -> None:
    """Attempt cleanup without masking the original persistence failure."""
    try:
        path.unlink(missing_ok=True)
    except OSError:
        # A uniquely named temporary file is never loaded as configuration.
        pass


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
            # Keep decoding/construction errors separate from filesystem errors.
            try:
                loaded: object = yaml.load(stream, Loader=_ConfigLoader)
            except UnicodeDecodeError:
                raise
            except (ValueError, OverflowError, RecursionError) as error:
                raise ConfigFormatError(
                    f"Invalid YAML value or excessive nesting in {resolved}: {error}"
                ) from error
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
        serialized = yaml.dump(
            normalized,
            Dumper=_ConfigDumper,
            allow_unicode=True,
            sort_keys=False,
            default_flow_style=False,
        )
    except (yaml.YAMLError, ValueError, OverflowError, RecursionError) as error:
        raise ConfigFormatError(
            f"Unable to serialize configuration data for {resolved}: {error}"
        ) from error

    try:
        resolved.parent.mkdir(parents=True, exist_ok=True)
        with ExitStack() as cleanup:
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
                cleanup.callback(_remove_temporary_file, temporary_path)
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
