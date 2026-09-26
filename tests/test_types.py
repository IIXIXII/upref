"""Tests for the v2 configuration value model."""

from __future__ import annotations

from collections import OrderedDict
from enum import Enum

import pytest

from upref import ConfigStore
from upref._types import normalize_config
from upref.errors import ConfigFormatError


def test_normalize_config_accepts_all_supported_values() -> None:
    source = OrderedDict(
        [
            ("none", None),
            ("boolean", False),
            ("integer", 0),
            ("float", 1.5),
            ("text", "café"),
            ("list", [None, True, 2, 3.5, "value", {"nested": []}]),
            ("mapping", OrderedDict([("key", "value")])),
        ]
    )

    result = normalize_config(source)

    assert result == source
    assert type(result) is dict
    assert type(result["mapping"]) is dict


def test_normalize_config_detaches_every_mutable_value() -> None:
    shared = ["initial"]
    source = {
        "first": {"items": shared},
        "second": shared,
    }

    result = normalize_config(source)

    assert result is not source
    assert result["first"] is not source["first"]
    assert result["first"]["items"] is not shared
    assert result["second"] is not shared
    assert result["first"]["items"] is not result["second"]

    result["first"]["items"].append("result-only")
    source["second"].append("source-only")

    assert result["second"] == ["initial"]
    assert source["first"]["items"] == ["initial", "source-only"]


def test_string_subclass_keys_use_underlying_text_and_round_trip(tmp_path):
    class Key(str, Enum):
        THEME = "theme"

    class DisplayKey(str):
        def __str__(self):
            return "display-only"

    source = {Key.THEME: {DisplayKey("name"): "dark"}}
    result = normalize_config(source)
    assert result == {"theme": {"name": "dark"}}
    assert type(next(iter(result))) is str
    assert type(next(iter(result["theme"]))) is str
    assert type(next(iter(source))) is Key

    store = ConfigStore("keys", directory=tmp_path)
    store.save(source)
    assert store.load() == result


def test_scalar_subclasses_remain_invalid_as_values():
    class Value(str, Enum):
        DARK = "dark"

    with pytest.raises(ConfigFormatError, match="Invalid configuration value"):
        normalize_config({"theme": Value.DARK})


def test_normalizing_string_keys_cannot_silently_discard_values():
    class DistinctKey(str):
        __hash__ = object.__hash__

        def __eq__(self, other):
            return self is other

    data = {"theme": "dark", DistinctKey("theme"): "light"}
    assert len(data) == 2
    with pytest.raises(
        ConfigFormatError, match="Duplicate mapping key after string normalization"
    ):
        normalize_config(data)
    assert len(data) == 2


@pytest.mark.parametrize("root", [None, [], "text", 1, ("value",)])
def test_normalize_config_rejects_non_mapping_roots(root: object) -> None:
    with pytest.raises(ConfigFormatError, match=r"root at \$"):
        normalize_config(root)


@pytest.mark.parametrize(
    ("value", "type_name"),
    [
        (("tuple",), "tuple"),
        ({1, 2}, "set"),
        (object(), "object"),
    ],
)
def test_normalize_config_rejects_unsupported_nested_values(
    value: object,
    type_name: str,
) -> None:
    with pytest.raises(ConfigFormatError) as caught:
        normalize_config({"section": {"items": [value]}})

    message = str(caught.value)
    assert "$['section']['items'][0]" in message
    assert type_name in message


def test_normalize_config_rejects_non_string_keys_with_mapping_path() -> None:
    with pytest.raises(ConfigFormatError) as caught:
        normalize_config({"section": {1: "invalid"}})

    message = str(caught.value)
    assert "$['section']" in message
    assert "expected str" in message


def test_normalize_config_rejects_a_mapping_cycle_with_both_paths() -> None:
    cyclic: dict[str, object] = {}
    cyclic["self"] = cyclic

    with pytest.raises(ConfigFormatError) as caught:
        normalize_config(cyclic)

    message = str(caught.value)
    assert "$['self']" in message
    assert "already active at $" in message


def test_normalize_config_rejects_a_list_cycle_with_path() -> None:
    cyclic: list[object] = []
    cyclic.append(cyclic)

    with pytest.raises(ConfigFormatError, match=r"\$\['items'\]\[0\]"):
        normalize_config({"items": cyclic})


def test_excessively_nested_data_is_a_format_error():
    nested = {}
    for _ in range(2000):
        nested = {"child": nested}
    with pytest.raises(ConfigFormatError, match="nesting is too deep"):
        normalize_config(nested)
