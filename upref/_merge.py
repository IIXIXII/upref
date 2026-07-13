#!/usr/bin/env python
# -*- coding: utf-8 -*-
# =============================================================================
#                 Author: Florent TOURNOIS | License: MIT
# =============================================================================
"""Provide pure, recursive merging for Upref configuration mappings.

Mappings are merged by key, while lists and scalar values are replaced as
complete values. All public inputs are normalized before merging, and the
result owns every mutable container it contains.
"""

from __future__ import annotations

from collections.abc import Mapping

from ._types import Config, ConfigValue, normalize_config


def _copy_value(value: ConfigValue) -> ConfigValue:
    """Copy a previously normalized configuration value.

    Args:
        value: A value that already conforms to :data:`ConfigValue` and contains
            only plain dictionaries for mappings.

    Returns:
        The scalar itself, or a recursive copy of every list and dictionary.
        The returned value shares no mutable container with ``value``.
    """
    if isinstance(value, dict):
        return {key: _copy_value(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_copy_value(item) for item in value]
    return value


def _merge_normalized(
    base: Config,
    override: Config,
    *,
    add_keys: bool,
) -> Config:
    """Merge two already normalized configurations without mutating them.

    Args:
        base: Normalized configuration providing the initial key set and
            fallback values.
        override: Normalized configuration whose matching values take
            precedence over ``base``.
        add_keys: Whether keys absent from ``base`` may be copied from
            ``override``. The rule applies independently at every mapping level
            reached by recursive merging.

    Returns:
        A new configuration with recursively merged dictionaries and replaced
        lists or scalar values. No mutable container is shared with either
        input.

    Notes:
        This private helper assumes both inputs have passed
        :func:`~upref._types.normalize_config`; callers requiring validation
        should use :func:`deep_merge`.
    """
    result = {key: _copy_value(value) for key, value in base.items()}

    for key, override_value in override.items():
        if key not in base:
            if add_keys:
                result[key] = _copy_value(override_value)
            continue

        base_value = base[key]
        if isinstance(base_value, dict) and isinstance(override_value, dict):
            result[key] = _merge_normalized(
                base_value,
                override_value,
                add_keys=add_keys,
            )
        else:
            # Lists and scalar values are intentionally replaced, not combined.
            result[key] = _copy_value(override_value)

    return result


def deep_merge(
    base: Mapping[str, ConfigValue],
    override: Mapping[str, ConfigValue],
    add_keys: bool = True,
) -> Config:
    """Return ``base`` recursively merged with ``override``.

    Mappings are merged recursively, while lists and scalar values from
    ``override`` replace their counterparts. When ``add_keys`` is false,
    unknown keys are ignored at every recursively merged mapping level.

    Both inputs are validated and neither inputs nor mutable values contained
    in them are shared with the result.

    Args:
        base: Mapping providing fallback keys and values.
        override: Mapping whose matching keys take precedence.
        add_keys: Whether to include keys found only in ``override``. When
            false, unknown keys are ignored at every recursively merged mapping
            level.

    Returns:
        A detached plain dictionary containing the merged configuration.

    Raises:
        ConfigFormatError: If either input is not a valid Upref configuration,
            including when it contains an unsupported value, a non-string key,
            or a container cycle.
    """
    normalized_base = normalize_config(base)
    normalized_override = normalize_config(override)
    return _merge_normalized(
        normalized_base,
        normalized_override,
        add_keys=add_keys,
    )


__all__ = ["deep_merge"]
