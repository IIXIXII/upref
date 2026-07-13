from __future__ import annotations

from pathlib import Path

import pytest

from upref import _paths
from upref.errors import ConfigPathError


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


def test_rejects_non_boolean_roaming(tmp_path: Path) -> None:
    with pytest.raises(ConfigPathError, match="boolean"):
        _paths.resolve_config_path(
            "sample-app",
            directory=tmp_path,
            roaming=1,  # type: ignore[arg-type]
        )


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


def test_legacy_path_rejects_traversal(tmp_path: Path) -> None:
    with pytest.raises(ConfigPathError):
        _paths.legacy_config_path("../outside", directory=tmp_path)
