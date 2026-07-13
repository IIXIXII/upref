"""Define the stable public exception hierarchy raised by :mod:`upref`.

Keeping the exception hierarchy in a dependency-free module lets every layer
of Upref report a stable, public error without creating import cycles.
Callers may catch :class:`UprefError` for domain-specific package failures or
a specialized subclass when recovery depends on the failed operation.
"""

from __future__ import annotations


class UprefError(Exception):
    """Base class for Upref's domain-specific exceptions.

    Unexpected programming errors and third-party exceptions outside Upref's
    documented boundaries are not necessarily wrapped in this hierarchy.
    """


class ConfigPathError(UprefError, ValueError):
    """Indicate that a configuration name or path is invalid.

    This exception also subclasses :class:`ValueError`, allowing callers that
    treat invalid path arguments as ordinary value errors to catch either API.
    """


class ConfigFormatError(UprefError):
    """Indicate data that cannot be represented by Upref's data model.

    Typical causes include malformed YAML, a non-mapping document root,
    non-string keys, unsupported Python values, and recursive container cycles.
    """


class ConfigReadError(UprefError):
    """Indicate that a configuration file could not be read.

    Format and encoding failures use :class:`ConfigFormatError`; this exception
    represents path conversion and filesystem read failures.
    """


class ConfigWriteError(UprefError):
    """Indicate that a filesystem mutation could not be completed safely.

    The exception covers atomic saves and deletions. Invalid configuration data
    is reported separately through :class:`ConfigFormatError`.
    """


class MigrationError(UprefError):
    """Indicate that a legacy configuration could not be migrated.

    The original legacy file is intended to remain untouched when this error
    is raised.
    """


class PromptCancelled(UprefError):
    """Indicate that the user cancelled interactive value collection.

    Cancellation is an expected control-flow outcome and does not persist a
    partially collected configuration.
    """


class PromptUnavailableError(UprefError):
    """Indicate that the requested interactive interface is unavailable.

    This commonly means an optional GUI dependency is not installed or cannot
    be initialized in the current environment.
    """


__all__ = [
    "UprefError",
    "ConfigPathError",
    "ConfigFormatError",
    "ConfigReadError",
    "ConfigWriteError",
    "MigrationError",
    "PromptCancelled",
    "PromptUnavailableError",
]
