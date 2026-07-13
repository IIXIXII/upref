"""Provide temporary v1 compatibility and explicit migration helpers.

Upref v1 mixed interactive field descriptions with persisted values and kept
all files below a shared ``.upref`` data directory. The v2 API separates those
concerns. This module preserves the historical call signatures during the v2
series while directing new code toward :class:`upref.ConfigStore` and
:func:`upref.collect`.

Every historical package-level wrapper emits :class:`DeprecationWarning`.
Pure conversion helpers remain available for migration tooling but are not
part of the recommended v2 workflow.
"""

from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from os import PathLike
from pathlib import Path
from typing import TYPE_CHECKING, Any
import warnings

from ._merge import deep_merge
from ._paths import legacy_config_path
from ._storage import delete_file, load_yaml, save_yaml
from ._types import Config, ConfigValue, normalize_config
from .errors import ConfigReadError, ConfigWriteError, MigrationError, UprefError
from .prompt import Field, collect

if TYPE_CHECKING:
    from .core import ConfigStore


_GUI_DEFAULTS: Config = {
    "__gui__": {
        "title": "Personal information",
        "button_label": "OK",
        "not_complete_title": "Information",
        "not_complete_msg": "All required values must be completed.",
    }
}


def _warn_v1(name: str) -> None:
    """Emit a consistently located warning for a deprecated v1 function.

    Args:
        name: Public function name displayed in the warning message.

    Returns:
        None.
    """
    warnings.warn(
        f"upref.{name}() is a v1 compatibility API; use ConfigStore instead",
        DeprecationWarning,
        stacklevel=3,
    )


def _is_metadata_key(key: str) -> bool:
    """Return whether a v1 key belongs to reserved metadata.

    Args:
        key: Legacy top-level key to classify.

    Returns:
        ``True`` when ``key`` begins or ends with two underscores.
    """
    return key.startswith("__") or key.endswith("__")


def _path_for(name: str) -> Path:
    """Resolve a validated preference name in the historical v1 directory.

    Args:
        name: Legacy preference name without the ``.conf`` suffix.

    Returns:
        The absolute, confined legacy file path.

    Raises:
        ConfigPathError: If ``name`` is unsafe or platform path discovery
            fails.
    """
    return legacy_config_path(name)


def load_conf(filename: str | PathLike[str]) -> Config:
    """Load a YAML mapping through the deprecated path-oriented v1 API.

    .. deprecated:: 2.0
        Use :meth:`ConfigStore.load <upref.ConfigStore.load>` for managed
        per-application configuration files.

    Args:
        filename: File path to expand, resolve, and read.

    Returns:
        A detached validated configuration, or an empty dictionary when the
        file does not exist or is empty.

    Raises:
        ConfigReadError: If ``filename`` is invalid or cannot be resolved, or
            an existing file cannot be read.
        ConfigFormatError: If its YAML or configuration values are invalid.
    """
    _warn_v1("load_conf")
    try:
        path = Path(filename).expanduser().resolve(strict=False)
    except (TypeError, ValueError, OSError, RuntimeError) as error:
        raise ConfigReadError(f"Invalid configuration path: {filename!r}") from error
    return load_yaml(path)


def save_conf(
    conf: Mapping[str, ConfigValue],
    filename: str | PathLike[str],
) -> Config:
    """Save a YAML mapping through the deprecated path-oriented v1 API.

    .. deprecated:: 2.0
        Use :meth:`ConfigStore.save <upref.ConfigStore.save>`.

    Args:
        conf: Complete configuration mapping to validate and persist.
        filename: Destination path to expand and resolve.

    Returns:
        A detached normalized copy of the saved mapping.

    Raises:
        ConfigFormatError: If ``conf`` contains unsupported data.
        ConfigWriteError: If the destination cannot be written atomically.
    """
    _warn_v1("save_conf")
    normalized = normalize_config(conf)
    try:
        path = Path(filename).expanduser().resolve(strict=False)
    except (TypeError, ValueError, OSError, RuntimeError) as error:
        raise ConfigWriteError(f"Invalid configuration path: {filename!r}") from error
    save_yaml(path, normalized)
    return normalized


def upref_filename(name: str) -> str:
    """Return the historical ``.upref/<name>.conf`` location.

    .. deprecated:: 2.0
        Use :attr:`ConfigStore.path <upref.ConfigStore.path>`.

    Args:
        name: Legacy preference name without a suffix.

    Returns:
        The absolute legacy filename as a string.

    Raises:
        ConfigPathError: If ``name`` is empty, reserved, or unsafe.
    """
    _warn_v1("upref_filename")
    return str(_path_for(name))


def default_conf() -> Config:
    """Return detached GUI defaults formerly stored in ``default.conf``.

    Returns:
        A new descriptor mapping that callers may mutate safely.

    Note:
        This helper exists for direct v1-module compatibility. New prompt
        front ends define their own presentation defaults.
    """
    return deepcopy(_GUI_DEFAULTS)


def current_upref(name: str) -> Config:
    """Load a descriptor or raw mapping from the historical v1 location.

    .. deprecated:: 2.0
        Use :meth:`ConfigStore.load <upref.ConfigStore.load>` or explicitly
        migrate the file with :meth:`upref.ConfigStore.import_legacy`.

    Args:
        name: Legacy preference name without the ``.conf`` suffix.

    Returns:
        The detached stored mapping, or an empty dictionary when absent.

    Raises:
        ConfigPathError: If ``name`` is unsafe.
        ConfigReadError: If the file cannot be read.
        ConfigFormatError: If the file contains invalid configuration data.
    """
    _warn_v1("current_upref")
    return load_yaml(_path_for(name))


def load_data(
    name: str,
    default_data: Mapping[str, ConfigValue] | None = None,
) -> Config:
    """Load raw v1 data and optionally merge application defaults.

    .. deprecated:: 2.0
        Use :meth:`ConfigStore.load <upref.ConfigStore.load>`.

    Args:
        name: Legacy preference name without the ``.conf`` suffix.
        default_data: Optional fallback values. Stored values take precedence
            and nested mappings merge recursively.

    Returns:
        A detached resolved configuration.

    Raises:
        ConfigPathError: If ``name`` is unsafe.
        ConfigReadError: If the stored file cannot be read.
        ConfigFormatError: If defaults or stored values are invalid.
    """
    _warn_v1("load_data")
    stored = load_yaml(_path_for(name))
    if default_data is None:
        return stored
    return deep_merge(default_data, stored)


def save_data(data: Mapping[str, ConfigValue], name: str) -> Config:
    """Save raw values in the historical v1 location.

    .. deprecated:: 2.0
        Use :meth:`ConfigStore.save <upref.ConfigStore.save>`.

    Args:
        data: Complete raw configuration mapping.
        name: Legacy preference name without the ``.conf`` suffix.

    Returns:
        A detached normalized copy of ``data``.

    Raises:
        ConfigPathError: If ``name`` is unsafe.
        ConfigFormatError: If ``data`` is invalid.
        ConfigWriteError: If the file cannot be persisted.
    """
    _warn_v1("save_data")
    normalized = normalize_config(data)
    save_yaml(_path_for(name), normalized)
    return normalized


def dict_merge(
    dct: Mapping[str, ConfigValue],
    merge_dct: Mapping[str, ConfigValue],
    add_keys: bool = True,
) -> Config:
    """Merge two mappings with the corrected alias-free v2 implementation.

    Args:
        dct: Base mapping copied into the result.
        merge_dct: Higher-priority mapping merged over ``dct``.
        add_keys: Include keys not already present in ``dct`` when true.

    Returns:
        A detached recursively merged mapping.

    Raises:
        ConfigFormatError: If either input violates the configuration model.
    """
    return deep_merge(dct, merge_dct, add_keys=add_keys)


def conv_raw_to_description(data: Mapping[str, ConfigValue]) -> Config:
    """Wrap raw values in the descriptor format used by Upref v1.

    Args:
        data: Raw configuration values keyed by preference name.

    Returns:
        A detached mapping where each value is stored below ``"value"``.

    Raises:
        ConfigFormatError: If ``data`` is not a supported configuration.
    """
    normalized = normalize_config(data)
    return {key: {"value": value} for key, value in normalized.items()}


def conv_description_to_raw(
    data_description: Mapping[str, ConfigValue],
) -> Config:
    """Extract raw values from a v1 descriptor mapping.

    Metadata keys beginning or ending with ``__`` and descriptors without a
    ``value`` member are omitted.

    Args:
        data_description: Historical descriptor mapping.

    Returns:
        A detached mapping of preference names to raw values.

    Raises:
        ConfigFormatError: If the descriptor tree contains unsupported data.
    """
    normalized = normalize_config(data_description)
    result: Config = {}
    for key, descriptor in normalized.items():
        if _is_metadata_key(key):
            continue
        if isinstance(descriptor, dict) and "value" in descriptor:
            result[key] = deepcopy(descriptor["value"])
    return result


def all_values_are_set(data_description: Mapping[str, ConfigValue]) -> bool:
    """Return whether every non-metadata descriptor contains a usable value.

    A descriptor is incomplete when it is not a mapping, lacks ``value``, or
    stores ``None`` or an empty string. Falsey non-string values such as
    ``False`` and ``0`` are complete.

    Args:
        data_description: Historical descriptor mapping to inspect.

    Returns:
        ``True`` when all preference descriptors are complete.

    Raises:
        ConfigFormatError: If the descriptor tree itself is invalid.
    """
    normalized = normalize_config(data_description)
    for key, descriptor in normalized.items():
        if _is_metadata_key(key):
            continue
        if not isinstance(descriptor, dict) or "value" not in descriptor:
            return False
        value = descriptor["value"]
        if value is None or (isinstance(value, str) and not value):
            return False
    return True


def _description_with_saved_values(
    data_description: Mapping[str, ConfigValue],
    saved: Mapping[str, ConfigValue],
) -> Config:
    """Overlay saved raw values onto a fresh descriptor definition.

    Args:
        data_description: Current application-owned field descriptions.
        saved: Previously persisted v1 descriptors.

    Returns:
        A detached descriptor mapping that retains current metadata and saved
        values.
    """
    description = normalize_config(data_description)
    saved_values = conv_description_to_raw(saved)
    for key, value in saved_values.items():
        descriptor = description.get(key)
        if not isinstance(descriptor, dict):
            descriptor = {}
            description[key] = descriptor
        descriptor["value"] = deepcopy(value)
    return description


def _field_from_descriptor(name: str, descriptor: Any) -> Field:
    """Convert one permissive v1 descriptor into a v2 :class:`Field`.

    Args:
        name: Preference key used as a fallback label.
        descriptor: Historical descriptor value, possibly malformed.

    Returns:
        A required text field with password masking when requested by v1
        ``type`` metadata.
    """
    if not isinstance(descriptor, Mapping):
        descriptor = {}
    field_type = str(descriptor.get("type", "")).strip().upper()
    return Field(
        label=str(descriptor.get("label", name)),
        description=str(descriptor.get("description", "")),
        required=True,
        secret=field_type in {"PASSWORD", "PASSWD", "PASS"},
    )


def get_pref(
    data_description: Mapping[str, ConfigValue],
    name: str,
    interface: str = "gui",
    force_renew: bool = False,
    mandatory: bool = True,
) -> Config:
    """Collect v1 descriptor values through the separated v2 prompt layer.

    A v1 password descriptor requests masked presentation from the selected
    interface, but accepted values are saved as readable plain-text YAML.

    .. deprecated:: 2.0
        Define :class:`upref.Field` objects, call :func:`upref.collect`, and
        persist the returned raw values with :class:`upref.ConfigStore`.

    Args:
        data_description: Historical mapping of preference descriptors.
        name: Legacy preference filename stem.
        interface: ``"gui"`` or ``"tty"`` prompt implementation.
        force_renew: Ask for every field even when saved values are complete.
        mandatory: When false, extract currently stored descriptor values
            without prompting or applying ``data_description``.

    Returns:
        A detached mapping of collected raw values.

    Raises:
        ConfigPathError: If ``name`` is unsafe.
        ConfigReadError: If existing preferences cannot be read.
        ConfigFormatError: If descriptors or saved data are invalid.
        PromptCancelled: If the user cancels collection.
        PromptUnavailableError: If the selected front end is unavailable.
        ConfigWriteError: If collected descriptor values cannot be persisted.
        ValueError: If ``interface`` is unsupported.
        Exception: Unexpected front-end errors propagate unchanged.
    """
    _warn_v1("get_pref")
    saved = load_yaml(_path_for(name))
    if not mandatory:
        return conv_description_to_raw(saved)

    description = _description_with_saved_values(data_description, saved)
    schema = {
        key: _field_from_descriptor(key, descriptor)
        for key, descriptor in description.items()
        if not _is_metadata_key(key)
    }
    initial = conv_description_to_raw(description)
    should_collect = force_renew or not all_values_are_set(description)
    if not should_collect:
        return initial

    values = collect(
        schema,
        initial=initial,
        interface=interface,
        mode="all" if force_renew else "missing",
    )
    for key, value in values.items():
        descriptor = description.get(key)
        if not isinstance(descriptor, dict):
            descriptor = {}
            description[key] = descriptor
        descriptor["value"] = deepcopy(value)
    save_yaml(_path_for(name), description)
    return values


def set_pref(
    data: Mapping[str, ConfigValue],
    name: str,
    data_description: Mapping[str, ConfigValue] | None = None,
) -> None:
    """Update values stored in a historical v1 descriptor file.

    .. deprecated:: 2.0
        Use :meth:`ConfigStore.update <upref.ConfigStore.update>` for raw v2
        values.

    Args:
        data: Raw preference values to wrap and replace.
        name: Legacy preference filename stem.
        data_description: Optional descriptor base. When omitted, the current
            legacy file is loaded first.

    Raises:
        ConfigPathError: If ``name`` is unsafe.
        ConfigReadError: If the current descriptor file cannot be read.
        ConfigFormatError: If descriptions or values are invalid.
        ConfigWriteError: If the updated file cannot be persisted.
    """
    _warn_v1("set_pref")
    description = (
        load_yaml(_path_for(name))
        if data_description is None
        else normalize_config(data_description)
    )
    for key, value in normalize_config(data).items():
        descriptor = description.get(key)
        if not isinstance(descriptor, dict):
            descriptor = {}
            description[key] = descriptor
        descriptor["value"] = deepcopy(value)
    save_yaml(_path_for(name), description)


def remove_pref(name: str) -> None:
    """Delete a historical v1 preference file if it exists.

    .. deprecated:: 2.0
        Use :meth:`ConfigStore.delete <upref.ConfigStore.delete>`.

    Args:
        name: Legacy preference filename stem.

    Raises:
        ConfigPathError: If ``name`` is unsafe.
        ConfigWriteError: If an existing file cannot be deleted.
    """
    _warn_v1("remove_pref")
    delete_file(_path_for(name))


def _looks_like_description(data: Config) -> bool:
    """Return whether a mapping appears to use the v1 descriptor format.

    Args:
        data: Validated legacy configuration.

    Returns:
        ``True`` when every non-metadata field has descriptor keys and at least
        one field contains a persisted value.
    """
    fields = [value for key, value in data.items() if not _is_metadata_key(key)]
    if not fields:
        return False
    descriptor_keys = {"label", "description", "type", "value"}
    return all(
        isinstance(value, dict) and bool(descriptor_keys.intersection(value))
        for value in fields
    ) and any(isinstance(value, dict) and "value" in value for value in fields)


def import_legacy(
    store: "ConfigStore",
    name: str,
    *,
    overwrite: bool = False,
    legacy_directory: str | PathLike[str] | None = None,
) -> Config:
    """Import one v1 file into ``store`` while leaving the source untouched.

    Documents recognized by the structural descriptor heuristic are converted
    to raw values; other mappings retain their shape. A raw document whose
    fields resemble descriptors is therefore ambiguous. The target is written
    only after the source has been parsed and normalized successfully.

    The source and target identity check prevents self-overwrite. The separate
    target-existence check and save are not locked, so concurrent migrations
    require external coordination.

    Args:
        store: Destination v2 store.
        name: Legacy preference filename stem.
        overwrite: Permit replacing an existing v2 destination.
        legacy_directory: Absolute override for the legacy source directory.

    Returns:
        A detached copy of the values written to ``store``.

    Raises:
        ConfigPathError: If the source name or directory is unsafe.
        ConfigReadError: If the source cannot be read or the target path cannot
            be inspected.
        ConfigFormatError: If the source contains invalid YAML or values.
        MigrationError: If source and target are the same file, the source is
            missing, the target already exists without ``overwrite``, or the
            destination store reports an Upref persistence error.
    """
    source = legacy_config_path(name, directory=legacy_directory)
    if source == store.path:
        raise MigrationError(
            f"Legacy source and v2 target must be different files: {source}"
        )
    try:
        legacy_data = load_yaml(source, missing_ok=False)
    except ConfigReadError as error:
        if isinstance(error.__cause__, FileNotFoundError):
            raise MigrationError(
                f"Legacy configuration does not exist: {source}"
            ) from error
        raise
    if store.exists() and not overwrite:
        raise MigrationError(f"Target configuration already exists: {store.path}")

    migrated = (
        conv_description_to_raw(legacy_data)
        if _looks_like_description(legacy_data)
        else normalize_config(legacy_data)
    )
    try:
        store.save(migrated)
    except UprefError as error:
        raise MigrationError(f"Could not migrate {source} to {store.path}") from error
    return migrated


__all__ = [
    "all_values_are_set",
    "conv_description_to_raw",
    "conv_raw_to_description",
    "current_upref",
    "default_conf",
    "dict_merge",
    "get_pref",
    "import_legacy",
    "load_conf",
    "load_data",
    "remove_pref",
    "save_conf",
    "save_data",
    "set_pref",
    "upref_filename",
]
