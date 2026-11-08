"""Load and validate per-environment settings from a TOML file.

The per-developer ``settings.toml`` is gitignored — copy
``settings.toml.example`` to create it. Only the publishing step reads
settings; the converter works without a settings file.
"""

from __future__ import annotations

import tomllib
from dataclasses import dataclass
from pathlib import Path

__all__ = ["JoomlaSettings", "Settings", "SettingsError", "load_settings"]

DEFAULT_SETTINGS_FILE = "settings.toml"
EXAMPLE_SETTINGS_FILE = "settings.toml.example"

_REQUIRED_JOOMLA_KEYS = ("base_url", "base_path", "token")


class SettingsError(Exception):
    """The settings file is missing, malformed, or fails validation."""


@dataclass(frozen=True, kw_only=True)
class JoomlaSettings:
    """Connection settings for the Joomla publishing target."""

    base_url: str
    base_path: str
    basic_auth: str | None = None
    token: str
    default_catid: int = 0


@dataclass(frozen=True)
class Settings:
    """Top-level settings, one section per publishing target."""

    joomla: JoomlaSettings


def load_settings(path: Path | str = DEFAULT_SETTINGS_FILE) -> Settings:
    """Load and validate settings from the TOML file at *path*.

    Defaults to ``settings.toml`` in the current working directory.
    Raises :class:`SettingsError` with an actionable message when the
    file is missing, not valid TOML, or fails validation.
    """
    file_path = Path(path)
    try:
        with open(file_path, "rb") as file:
            raw = tomllib.load(file)
    except FileNotFoundError as exc:
        raise SettingsError(
            f"settings file {file_path} not found; create it from {EXAMPLE_SETTINGS_FILE}"
        ) from exc
    except tomllib.TOMLDecodeError as exc:
        raise SettingsError(
            f"settings file {file_path} is not valid TOML: {exc}"
        ) from exc

    joomla_data = raw.get("joomla")
    if not isinstance(joomla_data, dict):
        raise SettingsError(f"{file_path}: missing [joomla] section")

    missing = [key for key in _REQUIRED_JOOMLA_KEYS if key not in joomla_data]
    if missing:
        raise SettingsError(
            f"{file_path}: [joomla] is missing required key(s): {', '.join(missing)}"
        )

    for key in _REQUIRED_JOOMLA_KEYS:
        if not isinstance(joomla_data[key], str):
            raise SettingsError(f"{file_path}: [joomla].{key} must be a string")

    default_catid = joomla_data.get("default_catid", 0)
    if isinstance(default_catid, bool) or not isinstance(default_catid, int):
        raise SettingsError(f"{file_path}: [joomla].default_catid must be an integer")

    basic_auth = joomla_data.get("basic_auth")
    if basic_auth is not None and not isinstance(basic_auth, str):
        raise SettingsError(f"{file_path}: [joomla].basic_auth must be a string")

    return Settings(
        joomla=JoomlaSettings(
            base_url=joomla_data["base_url"],
            base_path=joomla_data["base_path"],
            basic_auth=basic_auth,
            token=joomla_data["token"],
            default_catid=default_catid,
        )
    )
