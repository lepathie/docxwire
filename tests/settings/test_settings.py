from __future__ import annotations

import subprocess
import sys
import tomllib
from collections.abc import Callable
from pathlib import Path

import pytest

from docxwire.converter import DocxConverter
from docxwire.settings import SettingsError, load_settings

VALID_SETTINGS = """\
[joomla]
base_url = "https://example.org"
base_path = "/index.php/api/index.php"
token = "test-token"
default_catid = 7
"""


@pytest.fixture
def write_settings(tmp_path: Path) -> Callable[[str], Path]:
    """Write *content* to a scratch ``settings.toml`` and return its path."""

    def _write(content: str) -> Path:
        path = tmp_path / "settings.toml"
        path.write_text(content, encoding="utf-8")
        return path

    return _write


def test_load_settings_from_default_path_preserves_values(
    write_settings: Callable[[str], Path],
    monkeypatch,
) -> None:
    monkeypatch.chdir(write_settings(VALID_SETTINGS).parent)

    settings = load_settings()

    assert settings.joomla.base_url == "https://example.org"
    assert settings.joomla.base_path == "/index.php/api/index.php"
    assert settings.joomla.token == "test-token"
    assert settings.joomla.default_catid == 7


def test_load_settings_from_explicit_path_reads_given_file(
    write_settings: Callable[[str], Path],
) -> None:
    main = write_settings(VALID_SETTINGS)
    other = main.parent / "other.toml"
    other.write_text(
        "[joomla]\n"
        'base_url = "https://other.example"\n'
        'base_path = "/p"\n'
        'token = "t2"\n',
        encoding="utf-8",
    )

    settings = load_settings(other)

    assert settings.joomla.base_url == "https://other.example"
    assert settings.joomla.base_path == "/p"
    assert settings.joomla.token == "t2"


def test_load_settings_without_default_catid_is_zero(
    write_settings: Callable[[str], Path],
) -> None:
    path = write_settings(
        '[joomla]\nbase_url = "https://example.org"\nbase_path = "/p"\ntoken = "t"\n'
    )

    settings = load_settings(path)

    assert settings.joomla.default_catid == 0


def test_load_settings_without_file_points_at_example(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.chdir(tmp_path)

    with pytest.raises(SettingsError, match="settings.toml.example"):
        load_settings()


def test_load_settings_with_malformed_toml_raises_settings_error(
    write_settings: Callable[[str], Path],
) -> None:
    path = write_settings("[joomla\nbase_url = ")

    with pytest.raises(SettingsError) as excinfo:
        load_settings(path)

    assert not isinstance(excinfo.value, tomllib.TOMLDecodeError)


def test_load_settings_without_joomla_section_names_section(
    write_settings: Callable[[str], Path],
) -> None:
    path = write_settings('[other]\nkey = "value"\n')

    with pytest.raises(SettingsError, match="joomla"):
        load_settings(path)


def test_load_settings_without_token_names_key(
    write_settings: Callable[[str], Path],
) -> None:
    path = write_settings(
        '[joomla]\nbase_url = "https://example.org"\nbase_path = "/p"\n'
    )

    with pytest.raises(SettingsError, match="token"):
        load_settings(path)


@pytest.mark.parametrize("value", ['"abc"', "true"])
def test_load_settings_with_non_integer_default_catid_raises(
    write_settings: Callable[[str], Path],
    value: str,
) -> None:
    path = write_settings(
        "[joomla]\n"
        'base_url = "https://example.org"\n'
        'base_path = "/p"\n'
        'token = "t"\n'
        f"default_catid = {value}\n"
    )

    with pytest.raises(SettingsError, match="default_catid"):
        load_settings(path)


@pytest.mark.parametrize("field", ["base_url", "base_path", "basic_auth", "token"])
def test_load_settings_with_non_string_fields_raises(
    write_settings: Callable[[str], Path],
    field: str,
) -> None:
    values = {
        "base_url": '"https://example.org"',
        "base_path": '"/p"',
        "basic_auth": '"b64_encoded"',
        "token": '"t"',
    }
    values[field] = "123"
    toml = "[joomla]\n" + "".join(f"{key} = {value}\n" for key, value in values.items())

    path = write_settings(toml)

    with pytest.raises(SettingsError, match=field):
        load_settings(path)


def test_load_settings_with_basic_auth_loaded_verbatim(
    write_settings: Callable[[str], Path],
) -> None:
    path = write_settings(
        "[joomla]\n"
        'base_url = "https://example.org"\n'
        'base_path = "/p"\n'
        'basic_auth = "b64_encoded"\n'
        'token = "t"\n'
    )

    settings = load_settings(path)

    assert settings.joomla.basic_auth == "b64_encoded"


def test_load_settings_without_basic_auth_is_unset(
    write_settings: Callable[[str], Path],
) -> None:
    path = write_settings(
        '[joomla]\nbase_url = "https://example.org"\nbase_path = "/p"\ntoken = "t"\n'
    )

    settings = load_settings(path)

    assert settings.joomla.basic_auth is None


def test_convert_without_settings_file_succeeds(
    ruderkurs_doc: Path,
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.chdir(tmp_path)

    article = DocxConverter().convert(ruderkurs_doc)

    assert article.title


def test_converter_import_does_not_load_settings() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import sys\n"
                "import docxwire.converter\n"
                "assert 'docxwire.settings' not in sys.modules"
            ),
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr


@pytest.fixture
def joomla_settings() -> dict:
    """Load the [joomla] section from settings.toml.example."""
    example_path = Path(__file__).resolve().parents[2] / "settings.toml.example"
    return tomllib.loads(example_path.read_text(encoding="utf-8"))["joomla"]


def test_joomla_keys_are_complete(joomla_settings: dict) -> None:
    expected_keys = {
        "base_url",
        "base_path",
        "basic_auth",
        "token",
        "default_catid",
    }
    assert set(joomla_settings) == expected_keys


@pytest.mark.parametrize("key", ["base_url", "base_path", "basic_auth", "token"])
def test_joomla_placeholder_strings_are_valid(joomla_settings: dict, key: str) -> None:
    value = joomla_settings[key]
    assert isinstance(value, str), f"Expected '{key}' to be a string"
    assert value, f"Expected '{key}' to carry a non-empty placeholder"


def test_joomla_sentinels_and_defaults(joomla_settings: dict) -> None:
    # The Joomla 5 API path shape
    assert joomla_settings["base_path"] == "/api/index.php/v1"

    # 0 is the "no category set" sentinel (must be an integer)
    assert joomla_settings["default_catid"] == 0
    assert isinstance(joomla_settings["default_catid"], int)
