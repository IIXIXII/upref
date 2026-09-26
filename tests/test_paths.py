from __future__ import annotations

from pathlib import Path

import pytest

from upref import _paths
from upref.errors import ConfigPathError


class InvalidPath:
    def __fspath__(self) -> str:
        raise OSError("invalid path")


def test_explicit_directory_returns_absolute_child(tmp_path: Path) -> None:
    path = _paths.resolve_config_path(
        "sample-app",
        filename="settings.yaml",
        directory=tmp_path,
    )

    assert path == tmp_path.resolve() / "settings.yaml"
    assert path.is_absolute()


def test_explicit_directory_bypasses_platformdirs(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def unexpected_call(**kwargs: object) -> Path:
        raise AssertionError(f"platformdirs was unexpectedly called with {kwargs}")

    monkeypatch.setattr(_paths, "user_config_path", unexpected_call)

    assert (
        _paths.resolve_config_path("sample-app", directory=tmp_path).parent == tmp_path
    )


def test_platform_path_uses_no_author_duplication_by_default(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    received: dict[str, object] = {}

    def fake_user_config_path(**kwargs: object) -> Path:
        received.update(kwargs)
        return tmp_path

    monkeypatch.setattr(_paths, "user_config_path", fake_user_config_path)

    path = _paths.resolve_config_path("sample-app", roaming=True)

    assert path == tmp_path / "config.yaml"
    assert received == {
        "appname": "sample-app",
        "appauthor": False,
        "roaming": True,
    }


def test_platform_path_forwards_explicit_author(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    received: dict[str, object] = {}

    def fake_user_config_path(**kwargs: object) -> Path:
        received.update(kwargs)
        return tmp_path

    monkeypatch.setattr(_paths, "user_config_path", fake_user_config_path)

    _paths.resolve_config_path("sample-app", app_author="Example Corp")

    assert received["appauthor"] == "Example Corp"


@pytest.mark.parametrize(
    "filename",
    [
        "",
        "   ",
        ".",
        "..",
        "../outside.yaml",
        "..\\outside.yaml",
        "folder/config.yaml",
        "folder\\config.yaml",
        "/absolute.yaml",
        "C:\\absolute.yaml",
        "C:drive-relative.yaml",
        "config.yaml:stream",
        "bad?.yaml",
        "NUL.yaml",
        "COM1",
        "CON .txt",
        "NUL .txt",
        "COM1 .txt",
        "COM¹.yaml",
        "LPT³",
        "trailing.",
        " leading.yaml",
        "bad\x00name.yaml",
        "bad\x01name.yaml",
        "bad\nname.yaml",
        "bad\tname.yaml",
    ],
)
def test_rejects_unsafe_filenames(tmp_path: Path, filename: str) -> None:
    with pytest.raises(ConfigPathError):
        _paths.resolve_config_path("sample-app", filename=filename, directory=tmp_path)


@pytest.mark.parametrize(
    "app_name",
    [
        "",
        "   ",
        ".",
        "..",
        "vendor/app",
        "vendor\\app",
        "bad\x00name",
        "bad\nname",
    ],
)
def test_rejects_unsafe_application_names(tmp_path: Path, app_name: str) -> None:
    with pytest.raises(ConfigPathError):
        _paths.resolve_config_path(app_name, directory=tmp_path)


def test_rejects_relative_explicit_directory() -> None:
    with pytest.raises(ConfigPathError, match="absolute"):
        _paths.resolve_config_path("sample-app", directory=Path("relative"))


@pytest.mark.parametrize("as_path", [False, True])
def test_rejects_null_characters_in_directories(tmp_path, as_path):
    directory = str(tmp_path / "invalid") + "\x00"
    if as_path:
        directory = Path(directory)
    with pytest.raises(ConfigPathError, match="null character"):
        _paths.resolve_config_path("sample", directory=directory)
    with pytest.raises(ConfigPathError, match="null character"):
        _paths.legacy_config_path("sample", directory=directory)


def test_wraps_value_errors_during_directory_resolution(tmp_path, monkeypatch):
    def fail_resolve(self, strict=False):
        raise ValueError("invalid filesystem path")

    monkeypatch.setattr(Path, "resolve", fail_resolve)
    with pytest.raises(ConfigPathError, match="Unable to resolve directory"):
        _paths.resolve_config_path("sample", directory=tmp_path)


def test_rejects_non_string_components(tmp_path: Path) -> None:
    with pytest.raises(ConfigPathError, match="must be a string"):
        _paths.resolve_config_path(42, directory=tmp_path)  # type: ignore[arg-type]


def test_rejects_paths_detected_as_absolute_by_portable_check(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class AbsolutePurePath:
        def __init__(self, value: str) -> None:
            self.value = value

        def is_absolute(self) -> bool:
            return True

    monkeypatch.setattr(_paths, "PurePosixPath", AbsolutePurePath)

    with pytest.raises(ConfigPathError, match="absolute or drive-qualified"):
        _paths._validate_component("safe-name", label="name")


def test_wraps_invalid_and_unresolvable_directories(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with pytest.raises(ConfigPathError, match="Invalid directory"):
        _paths.resolve_config_path("sample-app", directory=InvalidPath())

    def fail_resolve(self: Path, strict: bool = False) -> Path:
        raise OSError("cannot resolve")

    monkeypatch.setattr(Path, "resolve", fail_resolve)
    with pytest.raises(ConfigPathError, match="Unable to resolve directory"):
        _paths._absolute_directory(tmp_path, label="directory")


def test_wraps_confined_path_resolution_failures(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail_resolve(self: Path, strict: bool = False) -> Path:
        raise OSError("cannot resolve child")

    monkeypatch.setattr(Path, "resolve", fail_resolve)
    with pytest.raises(ConfigPathError, match="escapes"):
        _paths._confined_child(tmp_path, "config.yaml")


def test_confined_child_requires_exactly_one_component(tmp_path: Path) -> None:
    with pytest.raises(ConfigPathError, match="identify one file"):
        _paths._confined_child(tmp_path, "nested/config.yaml")


def test_rejects_non_boolean_roaming(tmp_path: Path) -> None:
    with pytest.raises(ConfigPathError, match="boolean"):
        _paths.resolve_config_path(
            "sample-app",
            directory=tmp_path,
            roaming=1,  # type: ignore[arg-type]
        )


def test_wraps_platform_directory_discovery_errors(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail_user_config_path(**kwargs: object) -> Path:
        raise OSError("platform lookup failed")

    monkeypatch.setattr(_paths, "user_config_path", fail_user_config_path)

    with pytest.raises(ConfigPathError, match="determine the configuration"):
        _paths.resolve_config_path("sample-app")


def test_rejects_existing_symlink_that_escapes_directory(tmp_path: Path) -> None:
    directory = tmp_path / "config"
    directory.mkdir()
    outside = tmp_path / "outside.yaml"
    outside.write_text("outside: true\n", encoding="utf-8")
    link = directory / "config.yaml"
    try:
        link.symlink_to(outside)
    except OSError as error:
        pytest.skip(f"Symlinks are not available: {error}")

    with pytest.raises(ConfigPathError, match="escapes"):
        _paths.resolve_config_path("sample-app", directory=directory)


def test_legacy_explicit_directory_appends_conf_extension(tmp_path: Path) -> None:
    assert _paths.legacy_config_path("old-settings", directory=tmp_path) == (
        tmp_path / "old-settings.conf"
    )


def test_legacy_default_uses_documented_v1_data_directory(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    received: dict[str, object] = {}

    class FakePlatformDirs:
        def __init__(
            self,
            *,
            appname: str,
            appauthor: str | bool,
            roaming: bool,
        ) -> None:
            received.update(
                appname=appname,
                appauthor=appauthor,
                roaming=roaming,
            )

        @property
        def user_data_path(self) -> Path:
            return tmp_path

    monkeypatch.setattr(_paths, "PlatformDirs", FakePlatformDirs)

    assert _paths.legacy_config_path("old-settings") == tmp_path / "old-settings.conf"
    assert received == {
        "appname": ".upref",
        "appauthor": False,
        "roaming": True,
    }


def test_wraps_legacy_platform_directory_errors(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FailingPlatformDirs:
        def __init__(self, **kwargs: object) -> None:
            raise OSError("legacy lookup failed")

    monkeypatch.setattr(_paths, "PlatformDirs", FailingPlatformDirs)

    with pytest.raises(ConfigPathError, match="legacy Upref directory"):
        _paths.legacy_config_path("old-settings")


def test_legacy_path_rejects_traversal(tmp_path: Path) -> None:
    with pytest.raises(ConfigPathError):
        _paths.legacy_config_path("../outside", directory=tmp_path)
