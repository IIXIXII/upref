"""Tests for the pure v2 recursive merge."""

from __future__ import annotations

import pytest

from upref._merge import deep_merge
from upref.errors import ConfigFormatError


def test_deep_merge_recurses_and_adds_keys_by_default() -> None:
    base = {
        "network": {"host": "localhost", "port": 8080},
        "theme": "dark",
    }
    override = {
        "network": {"port": 9000, "tls": True},
        "new": None,
    }

    assert deep_merge(base, override) == {
        "network": {"host": "localhost", "port": 9000, "tls": True},
        "theme": "dark",
        "new": None,
    }


def test_deep_merge_replaces_lists_and_scalars_including_falsey_values() -> None:
    base = {
        "items": [1, 2],
        "enabled": True,
        "retries": 3,
        "label": "default",
    }
    override = {
        "items": [],
        "enabled": False,
        "retries": 0,
        "label": "",
    }

    assert deep_merge(base, override) == override


def test_deep_merge_does_not_mutate_or_alias_either_input() -> None:
    base = {"base": {"items": ["base"]}}
    override = {
        "base": {"extra": ["override"]},
        "new": {"items": ["new"]},
    }

    result = deep_merge(base, override)
    result["base"]["items"].append("result")
    result["base"]["extra"].append("result")
    result["new"]["items"].append("result")

    assert base == {"base": {"items": ["base"]}}
    assert override == {
        "base": {"extra": ["override"]},
        "new": {"items": ["new"]},
    }
    assert result["base"] is not base["base"]
    assert result["base"]["extra"] is not override["base"]["extra"]
    assert result["new"] is not override["new"]


def test_deep_merge_filters_unknown_keys_at_every_mapping_level() -> None:
    base = {
        "known": {
            "nested": {
                "value": 1,
            },
            "preserved": "yes",
        },
    }
    override = {
        "known": {
            "nested": {
                "value": 2,
                "unknown_deep": 3,
            },
            "unknown_nested": 4,
        },
        "unknown_root": 5,
    }

    assert deep_merge(base, override, add_keys=False) == {
        "known": {
            "nested": {"value": 2},
            "preserved": "yes",
        },
    }


def test_deep_merge_replaces_different_value_kinds() -> None:
    base = {
        "scalar_to_mapping": 1,
        "mapping_to_list": {"old": True},
        "list_to_scalar": [1],
    }
    override = {
        "scalar_to_mapping": {"new": True},
        "mapping_to_list": [False],
        "list_to_scalar": "done",
    }

    assert deep_merge(base, override, add_keys=False) == override


@pytest.mark.parametrize(
    ("base", "override"),
    [
        ({"bad": (1, 2)}, {}),
        ({}, {"bad": (1, 2)}),
        ({1: "bad"}, {}),
    ],
)
def test_deep_merge_validates_both_inputs(
    base: object,
    override: object,
) -> None:
    with pytest.raises(ConfigFormatError):
        deep_merge(base, override)  # type: ignore[arg-type]


def test_deep_merge_rejects_non_mapping_roots() -> None:
    with pytest.raises(ConfigFormatError, match=r"root at \$"):
        deep_merge({}, [])  # type: ignore[arg-type]
