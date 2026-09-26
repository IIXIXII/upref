"""Generated behavioral checks for the recursive configuration model."""

from copy import deepcopy
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from upref import ConfigStore, ConfigWriteError
from upref._merge import deep_merge
from upref._types import normalize_config

TEXT = st.text(max_size=30)
SCALARS = st.one_of(
    st.none(), st.booleans(), st.integers(), st.floats(allow_nan=False), TEXT
)
VALUES = st.recursive(
    SCALARS,
    lambda children: st.one_of(
        st.lists(children, max_size=5), st.dictionaries(TEXT, children, max_size=5)
    ),
    max_leaves=20,
)
CONFIGS = st.dictionaries(TEXT, VALUES, max_size=5)


def container_ids(value):
    pending = [value]
    result = set()
    while pending:
        current = pending.pop()
        if isinstance(current, (dict, list)):
            result.add(id(current))
            pending.extend(current.values() if isinstance(current, dict) else current)
    return result


@settings(max_examples=60, deadline=None)
@given(CONFIGS)
def test_yaml_round_trip_preserves_values_and_inputs(data):
    original = deepcopy(data)
    with TemporaryDirectory(prefix="upref-roundtrip-") as directory:
        store = ConfigStore("generated", directory=Path(directory).resolve())
        store.save(data)
        loaded = store.load()
        assert loaded == original
        assert data == original
        assert container_ids(loaded).isdisjoint(container_ids(data))


@given(CONFIGS)
def test_normalization_detaches_repeated_containers(data):
    source = {"first": data, "second": data}
    normalized = normalize_config(source)
    assert normalized == source
    assert container_ids(normalized).isdisjoint(container_ids(source))
    assert container_ids(normalized["first"]).isdisjoint(
        container_ids(normalized["second"])
    )


@given(CONFIGS, CONFIGS)
def test_merge_does_not_mutate_or_share_containers(base, override):
    before = deepcopy((base, override))
    merged = deep_merge(base, override)
    assert (base, override) == before
    assert container_ids(merged).isdisjoint(
        container_ids(base) | container_ids(override)
    )
    assert deep_merge(base, {}) == base
    assert deep_merge({}, override) == override
    assert deep_merge(base, base) == base


@settings(max_examples=30, deadline=None)
@given(CONFIGS, CONFIGS)
def test_failed_replacement_preserves_file_for_generated_configs(original, replacement):
    with TemporaryDirectory(prefix="upref-failure-") as directory:
        store = ConfigStore("generated", directory=Path(directory).resolve())
        store.save(original)
        before = store.path.read_bytes()
        with patch(
            "upref._storage.os.replace", side_effect=OSError("replacement denied")
        ):
            with pytest.raises(ConfigWriteError, match="replacement denied"):
                store.save(replacement)
        assert store.path.read_bytes() == before
        assert store.load() == original
        assert list(store.path.parent.iterdir()) == [store.path]
