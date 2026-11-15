"""Load and validate per-environment settings from a TOML file.

The per-developer ``settings.toml`` is gitignored — copy
``settings.toml.example`` to create it. Only the publishing step reads
settings; the converter works without a settings file.
"""

from __future__ import annotations

import os
import tomllib
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

__all__ = [
    "JoomlaSettings",
    "Settings",
    "SettingsError",
    "load_settings",
    "load_settings_from_env",
]

DEFAULT_SETTINGS_FILE = "settings.toml"
EXAMPLE_SETTINGS_FILE = "settings.toml.example"

ENV_PREFIX = "DOXXWIRE_JOOMLA_"

_JOOMLA_KEYS = (
    "base_url",
    "base_path",
    "basic_auth",
    "token",
    "default_catid",
    "default_language",
)
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
    default_language: str = "*"


@dataclass(frozen=True)
class Settings:
    """Top-level settings, one section per publishing target."""

    joomla: JoomlaSettings


def _validate_joomla_section(
    section: Mapping[str, Any],
    *,
    source: str,
    ref: Callable[[str], str],
) -> JoomlaSettings:
    """Validate one ``[joomla]`` section mapping and build the settings.

    *source* prefixes every error message (the TOML file's path, or
    ``environment``); *ref* renders how a setting is referenced in those
    messages (the TOML key, or the ``DOXXWIRE_JOOMLA_*`` variable name).
    The TOML loader and the environment loader share this single rule
    set, so the two sources cannot drift.
    """
    missing = [key for key in _REQUIRED_JOOMLA_KEYS if key not in section]
    if missing:
        raise SettingsError(
            f"{source}: [joomla] is missing required key(s): "
            f"{', '.join(ref(key) for key in missing)}"
        )

    for key in _REQUIRED_JOOMLA_KEYS:
        if not isinstance(section[key], str):
            raise SettingsError(f"{source}: {ref(key)} must be a string")

    default_catid = section.get("default_catid", 0)
    if isinstance(default_catid, bool) or not isinstance(default_catid, int):
        raise SettingsError(f"{source}: {ref('default_catid')} must be an integer")

    basic_auth = section.get("basic_auth")
    if basic_auth is not None and not isinstance(basic_auth, str):
        raise SettingsError(f"{source}: {ref('basic_auth')} must be a string")

    default_language = section.get("default_language", "*")
    if not isinstance(default_language, str):
        raise SettingsError(f"{source}: {ref('default_language')} must be a string")

    return JoomlaSettings(
        base_url=section["base_url"],
        base_path=section["base_path"],
        basic_auth=basic_auth,
        token=section["token"],
        default_catid=default_catid,
        default_language=default_language,
    )


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

    joomla = _validate_joomla_section(
        joomla_data,
        source=str(file_path),
        ref=lambda key: f"[joomla].{key}",
    )
    return Settings(joomla=joomla)


def load_settings_from_env() -> Settings:
    """Load and validate settings from the ``DOXXWIRE_JOOMLA_*`` environment.

    ``DOXXWIRE_JOOMLA_BASE_URL``, ``DOXXWIRE_JOOMLA_BASE_PATH``, and
    ``DOXXWIRE_JOOMLA_TOKEN`` are required; ``DOXXWIRE_JOOMLA_DEFAULT_CATID``,
    ``DOXXWIRE_JOOMLA_BASIC_AUTH``, and ``DOXXWIRE_JOOMLA_DEFAULT_LANGUAGE``
    are optional and keep the same defaults as the TOML source.
    Raises :class:`SettingsError` with an actionable message naming the
    variable when a required variable is missing or a value fails
    validation.
    """
    section: dict[str, Any] = {}
    for key in _JOOMLA_KEYS:
        raw = os.environ.get(ENV_PREFIX + key.upper())
        if raw is None:
            continue
        if key == "default_catid":
            try:
                section[key] = int(raw)
            except ValueError:
                # Keep the raw value so the shared validator raises the
                # error naming the variable.
                section[key] = raw
        else:
            section[key] = raw

    joomla = _validate_joomla_section(
        section,
        source="environment",
        ref=lambda key: ENV_PREFIX + key.upper(),
    )
    return Settings(joomla=joomla)
