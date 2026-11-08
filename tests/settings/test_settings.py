from __future__ import annotations

import subprocess
import sys
import tomllib
from pathlib import Path

import pytest

from docxwire.converter import DocxConverter
from docxwire.settings import Settings, SettingsError, load_settings

VALID_SETTINGS = """\
[joomla]
base_url = "https://example.org"
base_path = "/index.php/api/index.php"
token = "test-token"
default_catid = 7
"""


def test_load_settings_from_default_path_preserves_values(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / "settings.toml").write_text(VALID_SETTINGS, encoding="utf-8")

    settings = load_settings()

    assert settings.joomla.base_url == "https://example.org"
    assert settings.joomla.base_path == "/index.php/api/index.php"
    assert settings.joomla.token == "test-token"
    assert settings.joomla.default_catid == 7


def test_load_settings_from_explicit_path_reads_given_file(tmp_path: Path) -> None:
    (tmp_path / "settings.toml").write_text(VALID_SETTINGS, encoding="utf-8")
    other = tmp_path / "other.toml"
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


def test_load_settings_without_default_catid_is_zero(tmp_path: Path) -> None:
    (tmp_path / "settings.toml").write_text(
        '[joomla]\nbase_url = "https://example.org"\nbase_path = "/p"\ntoken = "t"\n',
        encoding="utf-8",
    )

    settings = load_settings(tmp_path / "settings.toml")

    assert settings.joomla.default_catid == 0


def test_load_settings_without_file_points_at_example(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.chdir(tmp_path)

    with pytest.raises(SettingsError, match="settings.toml.example"):
        load_settings()


def test_load_settings_with_malformed_toml_raises_settings_error(
    tmp_path: Path,
) -> None:
    (tmp_path / "settings.toml").write_text("[joomla\nbase_url = ", encoding="utf-8")

    with pytest.raises(SettingsError) as excinfo:
        load_settings(tmp_path / "settings.toml")

    assert not isinstance(excinfo.value, tomllib.TOMLDecodeError)


def test_load_settings_without_joomla_section_names_section(tmp_path: Path) -> None:
    (tmp_path / "settings.toml").write_text(
        '[other]\nkey = "value"\n', encoding="utf-8"
    )

    with pytest.raises(SettingsError, match="joomla"):
        load_settings(tmp_path / "settings.toml")


def test_load_settings_without_token_names_key(tmp_path: Path) -> None:
    (tmp_path / "settings.toml").write_text(
        '[joomla]\nbase_url = "https://example.org"\nbase_path = "/p"\n',
        encoding="utf-8",
    )

    with pytest.raises(SettingsError, match="token"):
        load_settings(tmp_path / "settings.toml")


@pytest.mark.parametrize("value", ['"abc"', "true"])
def test_load_settings_with_non_integer_default_catid_raises(
    tmp_path: Path, value: str
) -> None:
    (tmp_path / "settings.toml").write_text(
        "[joomla]\n"
        'base_url = "https://example.org"\n'
        'base_path = "/p"\n'
        'token = "t"\n'
        f"default_catid = {value}\n",
        encoding="utf-8",
    )

    with pytest.raises(SettingsError, match="default_catid"):
        load_settings(tmp_path / "settings.toml")


def test_load_settings_with_non_string_base_url_raises(tmp_path: Path) -> None:
    (tmp_path / "settings.toml").write_text(
        '[joomla]\nbase_url = 123\nbase_path = "/p"\ntoken = "t"\n',
        encoding="utf-8",
    )

    with pytest.raises(SettingsError, match="base_url"):
        load_settings(tmp_path / "settings.toml")


def test_load_settings_with_basic_auth_loaded_verbatim(tmp_path: Path) -> None:
    (tmp_path / "settings.toml").write_text(
        "[joomla]\n"
        'base_url = "https://example.org"\n'
        'base_path = "/p"\n'
        'token = "t"\n'
        'basic_auth = "b64_encoded"\n',
        encoding="utf-8",
    )

    settings = load_settings(tmp_path / "settings.toml")

    assert settings.joomla.basic_auth == "b64_encoded"


def test_load_settings_without_basic_auth_is_unset(tmp_path: Path) -> None:
    (tmp_path / "settings.toml").write_text(
        '[joomla]\nbase_url = "https://example.org"\nbase_path = "/p"\ntoken = "t"\n',
        encoding="utf-8",
    )

    settings = load_settings(tmp_path / "settings.toml")

    assert settings.joomla.basic_auth is None


def test_load_settings_with_non_string_basic_auth_raises(tmp_path: Path) -> None:
    (tmp_path / "settings.toml").write_text(
        "[joomla]\n"
        'base_url = "https://example.org"\n'
        'base_path = "/p"\n'
        'token = "t"\n'
        "basic_auth = 123\n",
        encoding="utf-8",
    )

    with pytest.raises(SettingsError, match="basic_auth"):
        load_settings(tmp_path / "settings.toml")


def test_convert_without_settings_file_succeeds(
    ruderkurs_doc: Path, tmp_path: Path, monkeypatch
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


@pytest.fixture(scope="session")
def example_settings() -> Settings:
    """The committed settings.toml.example, loaded through the real loader."""
    example = Path(__file__).resolve().parents[2] / "settings.toml.example"
    return load_settings(example)


def test_example_file_documents_all_joomla_keys(
    example_settings: Settings,
) -> None:
    joomla = example_settings.joomla

    assert joomla.base_url
    assert joomla.base_path
    assert joomla.token
    assert joomla.basic_auth
    assert joomla.default_catid == 0


def test_example_file_pins_joomla5_base_path(example_settings: Settings) -> None:
    assert example_settings.joomla.base_path == "/api/index.php/v1"
