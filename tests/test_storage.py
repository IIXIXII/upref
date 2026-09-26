from __future__ import annotations

import os
from pathlib import Path

import pytest

from upref import _storage
from upref.errors import ConfigFormatError, ConfigReadError, ConfigWriteError


class InvalidPath:
    def __fspath__(self) -> str:
        raise OSError("invalid path")


def test_load_missing_file_returns_empty_mapping(tmp_path: Path) -> None:
    assert _storage.load_yaml(tmp_path / "missing.yaml") == {}


def test_required_load_reports_a_missing_file(tmp_path: Path) -> None:
    with pytest.raises(ConfigReadError, match="does not exist"):
        _storage.load_yaml(tmp_path / "missing.yaml", missing_ok=False)


@pytest.mark.parametrize("content", ["", "   \n# comment only\n", "null\n", "~\n"])
def test_load_empty_file_returns_empty_mapping(tmp_path: Path, content: str) -> None:
    path = tmp_path / "empty.yaml"
    path.write_text(content, encoding="utf-8")

    assert _storage.load_yaml(path) == {}


def test_invalid_yaml_reports_path_and_location(tmp_path: Path) -> None:
    path = tmp_path / "invalid.yaml"
    path.write_text("value: [unterminated\n", encoding="utf-8")

    with pytest.raises(ConfigFormatError) as caught:
        _storage.load_yaml(path)

    message = str(caught.value)
    assert str(path) in message
    assert "line" in message
    assert "column" in message


def test_yaml_errors_without_a_problem_mark_have_no_location() -> None:
    assert _storage._yaml_error_location(_storage.yaml.YAMLError("invalid")) == ""


def test_invalid_read_path_is_wrapped() -> None:
    with pytest.raises(ConfigReadError, match="Invalid configuration path"):
        _storage.load_yaml(InvalidPath())


def test_non_utf8_files_are_reported_as_format_errors(tmp_path: Path) -> None:
    path = tmp_path / "invalid-utf8.yaml"
    path.write_bytes(b"value: \xff\n")

    with pytest.raises(ConfigFormatError, match="not valid UTF-8"):
        _storage.load_yaml(path)


def test_read_errors_are_wrapped(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail_open(self: Path, *args: object, **kwargs: object) -> object:
        raise PermissionError("read denied")

    monkeypatch.setattr(Path, "open", fail_open)

    with pytest.raises(ConfigReadError, match="read denied"):
        _storage.load_yaml(tmp_path / "config.yaml")


@pytest.mark.parametrize("content", ["- one\n- two\n", "scalar\n", "42\n"])
def test_rejects_non_mapping_yaml_roots(tmp_path: Path, content: str) -> None:
    path = tmp_path / "non-mapping.yaml"
    path.write_text(content, encoding="utf-8")

    with pytest.raises(ConfigFormatError, match="non-mapping.yaml"):
        _storage.load_yaml(path)


def test_rejects_non_string_mapping_keys(tmp_path: Path) -> None:
    path = tmp_path / "invalid-key.yaml"
    path.write_text("1: value\n", encoding="utf-8")

    with pytest.raises(ConfigFormatError, match="invalid-key.yaml"):
        _storage.load_yaml(path)


@pytest.mark.parametrize(
    "key", ["!!str [a, b]", "!!str {a: b}", "!!merge [a, b]", "!!merge {a: b}"]
)
def test_non_scalar_keys_with_scalar_tags_report_format_errors(tmp_path, key):
    path = tmp_path / "invalid-key.yaml"
    content = f"? {key}\n: value\n"
    path.write_text(content, encoding="utf-8")

    with pytest.raises(
        ConfigFormatError, match="expected a string mapping key"
    ) as caught:
        _storage.load_yaml(path)

    assert str(path) in str(caught.value)
    assert "line 1, column 3" in str(caught.value)
    assert path.read_text(encoding="utf-8") == content


def test_failed_temporary_file_creation_preserves_existing_file(tmp_path, monkeypatch):
    path = tmp_path / "config.yaml"
    _storage.save_yaml(path, {"original": True})
    previous = path.read_bytes()

    def fail_create(*args, **kwargs):
        raise PermissionError("temporary file denied")

    monkeypatch.setattr(_storage.tempfile, "NamedTemporaryFile", fail_create)
    with pytest.raises(ConfigWriteError, match="temporary file denied"):
        _storage.save_yaml(path, {"replacement": True})

    assert path.read_bytes() == previous
    assert list(tmp_path.iterdir()) == [path]


def test_failed_fsync_preserves_existing_file_and_removes_closed_temp(
    tmp_path, monkeypatch
):
    path = tmp_path / "config.yaml"
    _storage.save_yaml(path, {"original": True})
    previous = path.read_bytes()

    def fail_fsync(descriptor):
        raise OSError("flush denied")

    monkeypatch.setattr(_storage.os, "fsync", fail_fsync)
    with pytest.raises(ConfigWriteError, match="flush denied"):
        _storage.save_yaml(path, {"replacement": True})
    assert path.read_bytes() == previous
    assert list(tmp_path.iterdir()) == [path]


def test_round_trip_unicode_and_supported_types(tmp_path: Path) -> None:
    path = tmp_path / "config.yaml"
    expected = {
        "none": None,
        "enabled": False,
        "attempts": 0,
        "ratio": 1.25,
        "message": "Préfère le café ☕",
        "items": ["alpha", 2, True, None],
        "nested": {"host": "localhost", "ports": [8000, 8001]},
    }

    _storage.save_yaml(path, expected)

    assert _storage.load_yaml(path) == expected
    assert "Préfère le café ☕" in path.read_text(encoding="utf-8")


def test_save_creates_parent_directories(tmp_path: Path) -> None:
    path = tmp_path / "deep" / "folder" / "config.yaml"

    _storage.save_yaml(path, {"created": True})

    assert _storage.load_yaml(path) == {"created": True}


@pytest.mark.parametrize("text", ["\x85", "a\x85b", "\x85\n\u2028\u2029", "café ☕"])
def test_unicode_line_breaks_round_trip_in_keys_and_values(tmp_path, text):
    path = tmp_path / "unicode.yaml"
    expected = {text: text, "nested": [text]}
    _storage.save_yaml(path, expected)
    assert _storage.load_yaml(path) == expected
    if "\x85" in text:
        assert "\\N" in path.read_text(encoding="utf-8")
    else:
        assert text in path.read_text(encoding="utf-8")


def test_validation_happens_before_filesystem_changes(tmp_path: Path) -> None:
    directory = tmp_path / "must-not-exist"
    path = directory / "config.yaml"

    with pytest.raises(ConfigFormatError):
        _storage.save_yaml(path, {"unsupported": object()})  # type: ignore[dict-item]

    assert not directory.exists()


def test_invalid_write_path_is_wrapped() -> None:
    with pytest.raises(ConfigWriteError, match="Invalid configuration path"):
        _storage.save_yaml(InvalidPath(), {"value": 1})


def test_yaml_serialization_errors_are_wrapped(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail_dump(*args: object, **kwargs: object) -> str:
        raise _storage.yaml.YAMLError("cannot serialize")

    monkeypatch.setattr(_storage.yaml, "dump", fail_dump)

    with pytest.raises(ConfigFormatError, match="cannot serialize"):
        _storage.save_yaml(tmp_path / "config.yaml", {"value": 1})


@pytest.mark.parametrize("os_name", ["posix", "nt"])
def test_save_sets_private_permissions_only_on_posix(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    os_name: str,
) -> None:
    chmod_calls: list[tuple[Path, int]] = []

    class OsProxy:
        name = os_name
        fsync = staticmethod(os.fsync)
        replace = staticmethod(os.replace)

        @staticmethod
        def chmod(path: Path, mode: int) -> None:
            chmod_calls.append((path, mode))

    monkeypatch.setattr(_storage, "os", OsProxy)
    path = tmp_path / "config.yaml"

    _storage.save_yaml(path, {"private": True})

    if os_name == "posix":
        assert len(chmod_calls) == 1
        assert chmod_calls[0][1] == 0o600
    else:
        assert chmod_calls == []
    assert _storage.load_yaml(path) == {"private": True}


def test_failed_replace_preserves_existing_file_and_cleans_temp(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    path = tmp_path / "config.yaml"
    _storage.save_yaml(path, {"version": "old"})
    previous_bytes = path.read_bytes()

    def fail_replace(source: Path, destination: Path) -> None:
        raise OSError("simulated replacement failure")

    monkeypatch.setattr(_storage.os, "replace", fail_replace)

    with pytest.raises(ConfigWriteError, match="simulated replacement failure"):
        _storage.save_yaml(path, {"version": "new"})

    assert path.read_bytes() == previous_bytes
    assert list(tmp_path.glob(".config.yaml.*.tmp")) == []


def test_cleanup_errors_do_not_hide_the_primary_write_error(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    path = tmp_path / "config.yaml"

    def fail_replace(source: Path, destination: Path) -> None:
        raise OSError("replacement failed")

    def fail_unlink(self: Path, missing_ok: bool = False) -> None:
        raise OSError("cleanup failed")

    monkeypatch.setattr(_storage.os, "replace", fail_replace)
    monkeypatch.setattr(Path, "unlink", fail_unlink)

    with pytest.raises(ConfigWriteError, match="replacement failed"):
        _storage.save_yaml(path, {"value": 1})

    monkeypatch.undo()
    for temporary_path in tmp_path.glob(".config.yaml.*.tmp"):
        temporary_path.unlink()


@pytest.mark.skipif(os.name != "posix", reason="POSIX permissions only")
def test_saved_file_has_private_posix_permissions(tmp_path: Path) -> None:
    path = tmp_path / "config.yaml"

    _storage.save_yaml(path, {"private": True})

    assert path.stat().st_mode & 0o777 == 0o600


def test_delete_file_reports_whether_file_existed(tmp_path: Path) -> None:
    path = tmp_path / "config.yaml"
    _storage.save_yaml(path, {"value": 1})

    assert _storage.delete_file(path) is True
    assert _storage.delete_file(path) is False


@pytest.mark.parametrize(
    "content",
    [
        "port: 80\nport: 9000\n",
        'nested:\n  port: 80\n  "port": 9000\n',
        "base: &base {port: 80, port: 90}\nserver: {<<: *base}\n",
        "base: &base {port: 80}\nserver: {<<: *base, <<: *base}\n",
    ],
)
def test_duplicate_yaml_keys_are_rejected_without_changing_file(tmp_path, content):
    path = tmp_path / "duplicate.yaml"
    path.write_text(content, encoding="utf-8")
    original = path.read_bytes()
    with pytest.raises(ConfigFormatError, match="duplicate mapping key") as caught:
        _storage.load_yaml(path)
    assert str(path) in str(caught.value)
    assert "line" in str(caught.value)
    assert path.read_bytes() == original


def test_yaml_merges_allow_explicit_overrides_and_repeated_aliases(tmp_path):
    path = tmp_path / "merged.yaml"
    path.write_text(
        "base: &base {host: localhost, port: 80}\n"
        "alternate: &alternate {port: 81, enabled: true}\n"
        "server: &server {<<: [*base, *alternate], port: 90}\n"
        "copy: *server\n"
        "other: {<<: *server, host: example.org}\n",
        encoding="utf-8",
    )
    values = _storage.load_yaml(path)
    assert values["server"] == {"host": "localhost", "port": 90, "enabled": True}
    assert values["copy"] == values["server"]
    assert values["copy"] is not values["server"]
    assert values["other"] == {"host": "example.org", "port": 90, "enabled": True}


@pytest.mark.parametrize("content", ["date: 2026-02-30", "number: !!int invalid"])
def test_invalid_yaml_scalar_is_a_format_error(tmp_path, content):
    path = tmp_path / "invalid.yaml"
    path.write_text(content, encoding="utf-8")
    with pytest.raises(ConfigFormatError, match="Invalid YAML value"):
        _storage.load_yaml(path)


def test_excessively_nested_yaml_is_a_format_error(tmp_path):
    path = tmp_path / "deep.yaml"
    path.write_text("items: " + "[" * 2000 + "0" + "]" * 2000, encoding="utf-8")
    with pytest.raises(ConfigFormatError, match="excessive nesting"):
        _storage.load_yaml(path)


def test_serializer_recursion_preserves_existing_file(tmp_path):
    path = tmp_path / "config.yaml"
    _storage.save_yaml(path, {"keep": "original"})
    original = path.read_bytes()
    data = {}
    for _ in range(400):
        data = {"child": data}
    # Normalization can succeed before the more deeply recursive YAML dumper fails.
    _storage.normalize_config(data)
    with pytest.raises(ConfigFormatError, match="Unable to serialize"):
        _storage.save_yaml(path, data)
    assert path.read_bytes() == original
    assert list(tmp_path.glob("*.tmp")) == []


def test_invalid_delete_path_and_delete_errors_are_wrapped(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with pytest.raises(ConfigWriteError, match="Invalid configuration path"):
        _storage.delete_file(InvalidPath())

    def fail_unlink(self: Path, missing_ok: bool = False) -> None:
        raise PermissionError("delete denied")

    monkeypatch.setattr(Path, "unlink", fail_unlink)

    with pytest.raises(ConfigWriteError, match="delete denied"):
        _storage.delete_file(tmp_path / "config.yaml")
