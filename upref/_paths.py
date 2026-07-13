"""Validate names and resolve confined Upref configuration paths.

Names are checked against both POSIX and Windows path rules so configurations
remain portable across operating systems. Resolved file paths are always
absolute and are verified to be direct children of their selected directory.
"""

from __future__ import annotations

import os
from pathlib import Path, PurePosixPath, PureWindowsPath

from platformdirs import PlatformDirs, user_config_path

from .errors import ConfigPathError

PathLike = str | os.PathLike[str]


def _validate_component(value: str, *, label: str) -> str:
    """Validate a portable, single-component filename value.

    Args:
        value: Candidate component to validate.
        label: Human-readable parameter name used in error messages.

    Returns:
        ``value`` unchanged when it is a safe, non-empty component.

    Raises:
        ConfigPathError: If ``value`` is not a string, is blank, contains a path
            separator or unsafe filename character, names a Windows device, or
            is absolute or drive-qualified under POSIX or Windows semantics.
    """
    if not isinstance(value, str):
        raise ConfigPathError(f"{label} must be a string")
    if not value or not value.strip():
        raise ConfigPathError(f"{label} must not be empty")
    if value in {".", ".."}:
        raise ConfigPathError(f"{label} must not be {value!r}")
    if any(ord(character) < 32 for character in value):
        raise ConfigPathError(f"{label} must not contain control characters")
    if "/" in value or "\\" in value:
        raise ConfigPathError(f"{label} must be a simple name, not a path")
    if any(character in value for character in '<>:"|?*'):
        raise ConfigPathError(
            f"{label} contains a character that is unsafe in filenames"
        )
    if value != value.strip() or value.endswith("."):
        raise ConfigPathError(
            f"{label} must not have leading/trailing whitespace or a trailing dot"
        )

    windows_stem = value.split(".", 1)[0].rstrip(" ").upper()
    device_prefix = windows_stem[:3]
    device_suffix = windows_stem[3:]
    is_numbered_device = device_prefix in {"COM", "LPT"} and device_suffix in {
        "1",
        "2",
        "3",
        "4",
        "5",
        "6",
        "7",
        "8",
        "9",
        "¹",
        "²",
        "³",
    }
    if (
        windows_stem
        in {
            "CON",
            "PRN",
            "AUX",
            "NUL",
            "CONIN$",
            "CONOUT$",
        }
        or is_numbered_device
    ):
        raise ConfigPathError(f"{label} uses a reserved Windows filename")

    # Check both path syntaxes so a configuration remains portable when it is
    # created on one operating system and consumed on another.
    posix_name = PurePosixPath(value)
    windows_name = PureWindowsPath(value)
    if posix_name.is_absolute() or windows_name.is_absolute() or windows_name.drive:
        raise ConfigPathError(
            f"{label} must not be an absolute or drive-qualified path"
        )

    return value


def _absolute_directory(directory: PathLike, *, label: str) -> Path:
    """Normalize an explicitly absolute directory path.

    Args:
        directory: String or path-like object identifying the directory.
        label: Human-readable parameter name used in error messages.

    Returns:
        An expanded and resolved absolute :class:`~pathlib.Path`. Existing
        symbolic links are resolved; the final directory need not exist.

    Raises:
        ConfigPathError: If ``directory`` cannot be converted to a path, is not
            absolute, or cannot be resolved.
    """
    try:
        path = Path(directory)
    except (TypeError, ValueError, OSError) as error:
        raise ConfigPathError(f"Invalid {label}: {directory!r}") from error

    if not path.is_absolute():
        raise ConfigPathError(f"{label} must be an absolute path: {path}")

    try:
        return path.expanduser().resolve(strict=False)
    except (OSError, RuntimeError) as error:
        raise ConfigPathError(f"Unable to resolve {label}: {path}") from error


def _confined_child(directory: Path, filename: str) -> Path:
    """Resolve a filename while confining it to one directory.

    Args:
        directory: Absolute parent directory for the configuration file.
        filename: Validated filename expected to identify one direct child.

    Returns:
        The resolved absolute path of the child file.

    Raises:
        ConfigPathError: If path resolution fails, the candidate escapes
            ``directory``, or ``filename`` resolves to more than one component.
    """
    try:
        base = directory.resolve(strict=False)
        candidate = (base / filename).resolve(strict=False)
        relative = candidate.relative_to(base)
    except (OSError, RuntimeError, ValueError) as error:
        raise ConfigPathError(
            f"Configuration path escapes its directory: {directory / filename}"
        ) from error

    if len(relative.parts) != 1:
        raise ConfigPathError(
            f"Configuration filename must identify one file: {filename!r}"
        )
    return candidate


def resolve_config_path(
    app_name: str,
    filename: str = "config.yaml",
    app_author: str | None = None,
    directory: PathLike | None = None,
    roaming: bool = False,
) -> Path:
    """Resolve the absolute path of a v2 configuration file.

    ``directory`` is an explicit final configuration directory, primarily for
    tests and portable applications. When omitted, the platform-specific user
    configuration directory is selected with :mod:`platformdirs`.

    Args:
        app_name: Application name used to select the platform directory.
        filename: Simple filename within the configuration directory.
        app_author: Optional application author passed to :mod:`platformdirs`.
            It is ignored as a directory layer when omitted.
        directory: Optional absolute directory overriding platform discovery.
        roaming: Whether Windows should use its roaming configuration location.
            The value must be a boolean.

    Returns:
        An absolute path confined to the selected configuration directory. No
        directory or file is created.

    Raises:
        ConfigPathError: If a name is unsafe, ``directory`` is invalid or
            relative, ``roaming`` is not a boolean, platform discovery fails,
            or the resulting filename is not confined to its directory.
    """
    app_name = _validate_component(app_name, label="app_name")
    filename = _validate_component(filename, label="filename")
    if app_author is not None:
        app_author = _validate_component(app_author, label="app_author")
    if not isinstance(roaming, bool):
        raise ConfigPathError("roaming must be a boolean")

    if directory is None:
        try:
            platform_directory = user_config_path(
                appname=app_name,
                appauthor=False if app_author is None else app_author,
                roaming=roaming,
            )
        except (TypeError, ValueError, OSError) as error:
            raise ConfigPathError(
                f"Unable to determine the configuration directory for {app_name!r}"
            ) from error
        base = _absolute_directory(
            platform_directory,
            label="platform configuration directory",
        )
    else:
        base = _absolute_directory(directory, label="directory")

    return _confined_child(base, filename)


def legacy_config_path(name: str, directory: PathLike | None = None) -> Path:
    """Resolve the path of a legacy v1 ``.conf`` file.

    Args:
        name: Simple legacy configuration name, without the ``.conf`` suffix.
        directory: Optional absolute legacy directory. When omitted, the v1
            Upref data directory is selected through :class:`PlatformDirs`.

    Returns:
        An absolute ``<name>.conf`` path confined to the legacy directory. The
        file is neither read nor modified.

    Raises:
        ConfigPathError: If ``name`` is unsafe, ``directory`` is invalid or
            relative, platform discovery fails, or the result cannot be
            confined to one direct child.
    """
    name = _validate_component(name, label="name")
    filename = f"{name}.conf"

    if directory is None:
        try:
            legacy_directory = PlatformDirs(
                appname=".upref",
                appauthor=False,
                roaming=True,
            ).user_data_path
        except (TypeError, ValueError, OSError) as error:
            raise ConfigPathError(
                "Unable to determine the legacy Upref directory"
            ) from error
        base = _absolute_directory(legacy_directory, label="legacy Upref directory")
    else:
        base = _absolute_directory(directory, label="directory")

    return _confined_child(base, filename)
