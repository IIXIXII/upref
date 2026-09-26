#!/usr/bin/env python
# -*- coding: utf-8 -*-
# =============================================================================
#                 Author: Florent TOURNOIS | License: MIT
# =============================================================================
"""Public configuration store for Upref v2.

The core module deliberately contains no YAML, GUI, or terminal-specific
logic.  It coordinates the small internal services that implement those
details and exposes the stable :class:`ConfigStore` API.
"""

from __future__ import annotations

from collections.abc import Mapping
from os import PathLike
from pathlib import Path
from stat import S_ISREG
from typing import Literal

from ._merge import deep_merge
from ._paths import resolve_config_path
from ._storage import delete_file, load_yaml, save_yaml
from ._types import Config, ConfigValue
from .errors import ConfigReadError


class ConfigStore:
    """Read and persist one application's YAML configuration.

    A store is a lightweight, uncached handle to one configuration file. Its
    constructor resolves the path, including existing symbolic links, but does
    not read or write the configuration and creates no directory. Every
    :meth:`load` reads the file again, and every :meth:`save` validates and
    atomically replaces it.

    The optional ``directory`` override is intended for tests and portable
    applications. Without it, Upref selects the platform-specific user
    configuration directory.

    Every persisted value is readable plain-text YAML. A store provides file
    integrity, not encryption or credential-vault semantics.

    Example:
        >>> store = ConfigStore("my-application")
        >>> store.save({"theme": "dark", "retries": 3})
        >>> store.load()["theme"]
        'dark'
    """

    def __init__(
        self,
        app_name: str,
        *,
        filename: str = "config.yaml",
        app_author: str | None = None,
        directory: str | PathLike[str] | None = None,
        roaming: bool = False,
    ) -> None:
        """Resolve a store without reading or writing its configuration.

        Args:
            app_name: Portable application identifier used as the default
                configuration-directory name. It must be a safe, non-empty
                path component.
            filename: Configuration filename inside the selected directory.
                Directory separators, absolute paths, and unsafe Windows names
                are rejected.
            app_author: Optional publisher directory used by
                :mod:`platformdirs`. When omitted, the application directory
                is not nested below a duplicate author directory.
            directory: Absolute directory overriding the platform-specific
                location. The final file is ``directory / filename``.
            roaming: Whether Windows should prefer the roaming configuration
                directory. Other platforms pass this flag through to
                :mod:`platformdirs`.

        Raises:
            ConfigPathError: If an identifier, filename, author, or explicit
                directory is invalid or the resulting path escapes its base.
        """
        self._app_name = app_name
        self._filename = filename
        self._path = resolve_config_path(
            app_name,
            filename=filename,
            app_author=app_author,
            directory=directory,
            roaming=roaming,
        )

    @property
    def app_name(self) -> str:
        """Return the validated application identifier used by the store.

        Returns:
            The original validated ``app_name`` constructor argument.
        """
        return self._app_name

    @property
    def filename(self) -> str:
        """Return the configuration filename without directory components.

        Returns:
            The original validated ``filename`` constructor argument.
        """
        return self._filename

    @property
    def path(self) -> Path:
        """Return the resolved absolute configuration-file path.

        Returns:
            The confined path determined during construction.
        """
        return self._path

    def exists(self) -> bool:
        """Return whether the resolved path currently identifies a file.

        Returns:
            ``True`` for a regular file, including a symbolic link resolved at
            construction, otherwise ``False``.

        Raises:
            ConfigReadError: If the operating system cannot inspect the path.
        """
        try:
            return S_ISREG(self._path.stat().st_mode)
        except (FileNotFoundError, NotADirectoryError):
            return False
        except OSError as error:
            raise ConfigReadError(
                f"Unable to inspect configuration file {self._path}: {error}"
            ) from error

    def load(
        self,
        *,
        defaults: Mapping[str, ConfigValue] | None = None,
    ) -> Config:
        """Load a fresh configuration mapping.

        Missing, whitespace-only, comment-only, and explicit YAML ``null``
        documents behave like an empty mapping. When defaults are supplied,
        nested mappings are merged recursively and stored values override
        defaults. Lists and scalar values are replaced rather than combined.

        Neither ``defaults`` nor any mutable value inside it is shared with
        the returned configuration. Calling this method never writes defaults
        to disk.

        Args:
            defaults: Optional fallback configuration applied in memory below
                the stored values.

        Returns:
            A validated, detached dictionary containing the resolved values.

        Raises:
            ConfigReadError: If the file exists but cannot be read.
            ConfigFormatError: If YAML is malformed, is not UTF-8, has a
                non-mapping root, duplicate explicit keys, excessive nesting,
                or unsupported values or key types.
        """
        stored = load_yaml(self._path)
        if defaults is None:
            return stored
        return deep_merge(defaults, stored)

    def save(self, data: Mapping[str, ConfigValue]) -> None:
        """Validate and atomically replace the stored configuration.

        The complete document is serialized as safe UTF-8 YAML before any
        filesystem change. A temporary file in the destination directory is
        flushed and then installed with an atomic replacement. YAML comments,
        anchors, and custom formatting are not preserved.

        Values are written as readable plain text. This method provides no
        encryption or secret-store semantics.

        Args:
            data: Complete mapping to persist. Only :data:`ConfigValue` values
                and string mapping keys are supported.

        Raises:
            ConfigFormatError: If ``data`` cannot be represented by the Upref
                configuration model or serialized as safe YAML.
            ConfigWriteError: If a directory cannot be created or the atomic
                write cannot be completed.
        """
        save_yaml(self._path, data)

    def update(self, changes: Mapping[str, ConfigValue]) -> Config:
        """Recursively merge ``changes`` into stored data and save the result.

        Mappings merge recursively. Lists and scalars, including falsey values
        such as ``False``, ``0``, and ``None``, replace existing values.

        This method is a convenience read/merge/write sequence, not a locked
        transaction. Atomic replacement prevents partial YAML files, but
        concurrent writers remain last-writer-wins. Changes are persisted as
        readable plain-text YAML.

        Args:
            changes: Partial configuration whose values take precedence over
                the currently stored mapping.

        Returns:
            The detached merged configuration that was persisted.

        Raises:
            ConfigReadError: If the existing file cannot be read.
            ConfigFormatError: If existing or replacement data is invalid.
            ConfigWriteError: If the merged document cannot be written.
        """
        updated = deep_merge(load_yaml(self._path), changes)
        save_yaml(self._path, updated)
        return updated

    def delete(self) -> bool:
        """Delete only this store's configuration file.

        Returns:
            ``True`` when a file was removed, or ``False`` when it was already
            absent. Parent directories are never removed.

        Raises:
            ConfigWriteError: If the path exists but cannot be deleted.
        """
        return delete_file(self._path)

    def import_legacy(
        self,
        name: str,
        *,
        overwrite: bool = False,
        legacy_directory: str | PathLike[str] | None = None,
        source_format: Literal["auto", "raw", "descriptors"] = "auto",
        dry_run: bool = False,
    ) -> Config:
        """Import one historical v1 ``.conf`` file into this store.

        By default, v1's structural heuristic detects descriptor mappings and
        extracts their ``value`` entries. Select ``source_format="raw"`` to
        preserve an ambiguous mapping, or ``"descriptors"`` to force extraction.
        The source is never modified or deleted, and using it as the target is
        rejected. A dry run returns the conversion without writing anything.

        Migrated values, including historical password fields, are persisted
        as readable plain-text YAML.

        Target existence is checked before saving but is not protected by a
        lock. Concurrent migration writers must coordinate externally.

        Args:
            name: Legacy preference name without the ``.conf`` suffix.
            overwrite: Permit replacement when the v2 target already exists.
            legacy_directory: Absolute override for the legacy source
                directory, primarily for tests and controlled migrations.
            source_format: ``"auto"`` uses the historical heuristic; ``"raw"``
                retains every key; ``"descriptors"`` extracts values and drops
                metadata and descriptors without a value.
            dry_run: Preview only. Source and target preflight checks still
                apply, including ``overwrite``. No destination directory is
                created and write permissions are not tested.

        Returns:
            A detached dictionary containing the converted values, persisted
            unless ``dry_run`` is true.

        Raises:
            ConfigPathError: If the legacy name or directory is unsafe.
            ConfigReadError: If the legacy source cannot be read or the target
                path cannot be inspected.
            MigrationError: If source and target are the same file, the source
                is missing, the target already exists without ``overwrite``,
                or persistence fails.
            ConfigFormatError: If the legacy YAML cannot be parsed or contains
                unsupported configuration data.
            ValueError: If ``source_format`` is not a supported selector.
            TypeError: If ``dry_run`` is not a boolean.
        """
        # The lazy import keeps compatibility code out of the normal v2 path
        # and avoids a core/legacy import cycle.
        from .legacy import import_legacy

        return import_legacy(
            self,
            name,
            overwrite=overwrite,
            legacy_directory=legacy_directory,
            source_format=source_format,
            dry_run=dry_run,
        )

    def __repr__(self) -> str:
        """Return a diagnostic representation containing the app and path.

        Returns:
            An unambiguous constructor-like string for logs and debugging.
        """
        return f"{type(self).__name__}(app_name={self.app_name!r}, path={self.path!r})"


__all__ = ["ConfigStore"]
