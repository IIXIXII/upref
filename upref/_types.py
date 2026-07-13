"""Define and validate the values accepted by Upref configurations.

The public type aliases describe the recursive, YAML-safe data model used by
the package. Runtime validation additionally converts arbitrary mapping
implementations to plain dictionaries, rejects non-string keys and container
cycles, and detaches every mutable value from the caller's object graph.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import TypeAlias, cast

from .errors import ConfigFormatError


ConfigScalar: TypeAlias = bool | int | float | str | None
ConfigValue: TypeAlias = ConfigScalar | list["ConfigValue"] | dict[str, "ConfigValue"]
Config: TypeAlias = dict[str, ConfigValue]

_SCALAR_TYPES = (bool, int, float, str)
_PathPart: TypeAlias = str | int


def _format_path(path: tuple[_PathPart, ...]) -> str:
    """Format a configuration location for diagnostic messages.

    Args:
        path: Mapping keys and list indexes relative to the configuration root.

    Returns:
        An unambiguous JSONPath-like string beginning with ``$``. Mapping keys
        use their Python representation so dots and other punctuation cannot
        be mistaken for path separators.
    """
    result = "$"
    for part in path:
        if isinstance(part, int):
            result += f"[{part}]"
        else:
            result += f"[{part!r}]"
    return result


def _normalize_value(
    value: object,
    path: tuple[_PathPart, ...],
    active: dict[int, str],
) -> ConfigValue:
    """Validate and detach one value in a configuration object graph.

    Args:
        value: Candidate scalar or container to normalize.
        path: Location of ``value`` relative to the configuration root.
        active: Map from container identities on the current recursion stack to
            their formatted locations. The map is restored before this
            function returns or propagates an error.

    Returns:
        A supported scalar, a new list, or a new plain dictionary containing
        recursively normalized values.

    Raises:
        ConfigFormatError: If a mapping key is not a string, a value has an
            unsupported type, or a list or mapping contains a recursive cycle.

    Notes:
        Repeated references are valid when they do not form a cycle. Each
        occurrence is copied independently. Scalar subclasses are deliberately
        rejected so the result contains only the exact scalar types declared by
        :data:`ConfigScalar`.
    """
    if value is None or type(value) in _SCALAR_TYPES:
        return cast(ConfigScalar, value)

    if isinstance(value, Mapping):
        object_id = id(value)
        current_path = _format_path(path)
        if object_id in active:
            raise ConfigFormatError(
                f"Cyclic reference at {current_path}; "
                f"the same container is already active at {active[object_id]}"
            )

        active[object_id] = current_path
        try:
            result: Config = {}
            for key, item in value.items():
                if not isinstance(key, str):
                    raise ConfigFormatError(
                        f"Invalid mapping key at {current_path}: expected str, "
                        f"got {type(key).__name__} ({key!r})"
                    )
                result[key] = _normalize_value(item, path + (key,), active)
            return result
        finally:
            active.pop(object_id, None)

    if isinstance(value, list):
        object_id = id(value)
        current_path = _format_path(path)
        if object_id in active:
            raise ConfigFormatError(
                f"Cyclic reference at {current_path}; "
                f"the same container is already active at {active[object_id]}"
            )

        active[object_id] = current_path
        try:
            return [
                _normalize_value(item, path + (index,), active)
                for index, item in enumerate(value)
            ]
        finally:
            active.pop(object_id, None)

    raise ConfigFormatError(
        f"Invalid configuration value at {_format_path(path)}: expected "
        "None, bool, int, float, str, list, or mapping; "
        f"got {type(value).__name__}"
    )


def normalize_config(data: object) -> Config:
    """Validate *data* and return a detached, plain-dictionary copy.

    The returned graph contains only values from :data:`ConfigValue`. Every
    mutable occurrence is copied independently, even when the input contains
    repeated references. Recursive container cycles are rejected with a path
    identifying where the cycle was encountered.

    Args:
        data: Candidate configuration root. Any
            :class:`~collections.abc.Mapping` implementation is accepted at the
            root and at nested mapping positions.

    Returns:
        A new plain dictionary whose keys are strings and whose values conform
        to :data:`ConfigValue`. No mutable object is shared with ``data``.

    Raises:
        ConfigFormatError: If the root is not a mapping, a key is not a string,
            a value has an unsupported type, or the object graph contains a
            container cycle.
    """
    if not isinstance(data, Mapping):
        raise ConfigFormatError(
            "Invalid configuration root at $: expected a mapping, "
            f"got {type(data).__name__}"
        )

    normalized = _normalize_value(data, (), {})
    # The root check above and _normalize_value's Mapping branch guarantee this.
    assert isinstance(normalized, dict)
    return normalized


__all__ = ["Config", "ConfigScalar", "ConfigValue", "normalize_config"]
