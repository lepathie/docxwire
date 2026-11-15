"""Tests for the docxwire command."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from docxwire.cli import main
from docxwire.joomla.client import JoomlaApiError

CREATED = {
    "id": "503",
    "attributes": {"title": "2026.03 Regatta", "note": "Prüfe: Titel"},
}


def write_docx(folder: Path, name: str = "2026.03 Regatta.docx") -> Path:
    path = folder / name
    path.write_bytes(b"PK fake docx")
    return path


def write_settings(folder: Path) -> None:
    (folder / "settings.toml").write_text(
        "[joomla]\n"
        'base_url = "https://example.org"\n'
        'base_path = "/api/index.php/v1"\n'
        'token = "test-token"\n',
        encoding="utf-8",
    )


def stub_publish(
    monkeypatch, *, result: dict = CREATED, error: Exception | None = None
) -> list[str]:
    """Stub ``publish_article`` in ``docxwire.cli``; returns the call log."""
    calls: list[str] = []

    def fake_publish(docx_path: Path, settings) -> dict:
        if error is not None:
            raise error
        calls.append("publish")
        return result

    monkeypatch.setattr("docxwire.cli.publish_article", fake_publish)
    return calls


def stub_publish_capturing_settings(monkeypatch) -> list:
    """Stub ``publish_article``; returns the settings it received."""
    seen: list = []

    def fake_publish(docx_path: Path, settings) -> dict:
        seen.append(settings)
        return CREATED

    monkeypatch.setattr("docxwire.cli.publish_article", fake_publish)
    return seen


def write_env_settings(monkeypatch, **values: str) -> None:
    """Set the given ``DOXXWIRE_JOOMLA_*`` variables (keyed by setting)."""
    for key, value in values.items():
        monkeypatch.setenv(f"DOXXWIRE_JOOMLA_{key.upper()}", value)


@pytest.fixture
def clear_joomla_env(monkeypatch) -> None:
    """Remove any inherited DOXXWIRE_JOOMLA_* variables."""
    for key in (
        "base_url",
        "base_path",
        "basic_auth",
        "token",
        "default_catid",
        "default_language",
    ):
        monkeypatch.delenv(f"DOXXWIRE_JOOMLA_{key.upper()}", raising=False)


class TestCliSuccess:
    def test_reports_id_title_and_note(self, monkeypatch, capsys, tmp_path) -> None:
        write_docx(tmp_path)
        write_settings(tmp_path)
        monkeypatch.chdir(tmp_path)
        calls = stub_publish(monkeypatch)

        code = main(["2026.03 Regatta.docx"])

        out = capsys.readouterr().out
        assert code == 0
        assert calls == ["publish"]
        assert "Created draft article 503: 2026.03 Regatta" in out
        assert "Prüfe: Titel" in out

    def test_empty_note_reports_nothing_to_review(self, monkeypatch, capsys, tmp_path):
        write_docx(tmp_path)
        write_settings(tmp_path)
        monkeypatch.chdir(tmp_path)
        stub_publish(
            monkeypatch,
            result={"id": "504", "attributes": {"title": "Titel", "note": ""}},
        )

        code = main(["2026.03 Regatta.docx"])

        out = capsys.readouterr().out
        assert code == 0
        assert "Created draft article 504: Titel" in out
        assert "Nothing to review." in out


class TestCliUsage:
    def test_missing_argument_exits_2_with_usage(self, monkeypatch, capsys) -> None:
        stub_publish(monkeypatch)

        with pytest.raises(SystemExit) as excinfo:
            main([])

        assert excinfo.value.code == 2
        assert "usage" in capsys.readouterr().err

    def test_missing_file_exits_1_naming_file(self, monkeypatch, capsys, tmp_path):
        calls = stub_publish(monkeypatch)

        code = main([str(tmp_path / "nope.docx")])

        err = capsys.readouterr().err
        assert code == 1
        assert "nope.docx" in err
        # No conversion or network activity.
        assert calls == []

    def test_help_lists_json_and_settings_env_flags(self, monkeypatch, capsys) -> None:
        stub_publish(monkeypatch)

        with pytest.raises(SystemExit) as excinfo:
            main(["--help"])

        out = capsys.readouterr().out
        assert excinfo.value.code == 0
        assert "--json" in out
        assert "--settings-env" in out

    def test_unknown_option_exits_2_with_usage(self, monkeypatch, capsys) -> None:
        stub_publish(monkeypatch)

        with pytest.raises(SystemExit) as excinfo:
            main(["--bogus", "2026.03 Regatta.docx"])

        assert excinfo.value.code == 2
        assert "usage" in capsys.readouterr().err


class TestCliFailures:
    def test_missing_settings_file_exits_1_pointing_to_example(
        self, monkeypatch, capsys, tmp_path
    ) -> None:
        write_docx(tmp_path)
        monkeypatch.chdir(tmp_path)
        calls = stub_publish(monkeypatch)

        code = main(["2026.03 Regatta.docx"])

        err = capsys.readouterr().err
        assert code == 1
        assert "settings.toml.example" in err
        # No conversion or network activity.
        assert calls == []

    def test_payload_build_failure_exits_1_with_message(
        self, monkeypatch, capsys, tmp_path
    ) -> None:
        write_docx(tmp_path)
        write_settings(tmp_path)
        monkeypatch.chdir(tmp_path)
        stub_publish(
            monkeypatch,
            error=ValueError(
                "Body image '/tmp/media-a9visq6k/media/image1.jpeg' has no upload path"
            ),
        )

        code = main(["2026.03 Regatta.docx"])

        err = capsys.readouterr().err
        assert code == 1
        assert "no upload path" in err

    def test_api_error_exits_1_with_message(self, monkeypatch, capsys, tmp_path):
        write_docx(tmp_path)
        write_settings(tmp_path)
        monkeypatch.chdir(tmp_path)
        stub_publish(
            monkeypatch,
            error=JoomlaApiError(409, [{"title": "Alias already in use"}]),
        )

        code = main(["2026.03 Regatta.docx"])

        err = capsys.readouterr().err
        assert code == 1
        assert "Alias already in use" in err


class TestCliJson:
    def test_success_reports_single_json_object(
        self, monkeypatch, capsys, tmp_path
    ) -> None:
        write_docx(tmp_path)
        write_settings(tmp_path)
        monkeypatch.chdir(tmp_path)
        stub_publish(monkeypatch)

        code = main(["2026.03 Regatta.docx", "--json"])

        out = capsys.readouterr().out
        assert code == 0
        assert json.loads(out) == {
            "id": "503",
            "title": "2026.03 Regatta",
            "note": "Prüfe: Titel",
        }

    def test_empty_note_reports_empty_string(
        self, monkeypatch, capsys, tmp_path
    ) -> None:
        write_docx(tmp_path)
        write_settings(tmp_path)
        monkeypatch.chdir(tmp_path)
        stub_publish(
            monkeypatch,
            result={"id": "504", "attributes": {"title": "Titel", "note": ""}},
        )

        code = main(["2026.03 Regatta.docx", "--json"])

        out = capsys.readouterr().out
        assert code == 0
        assert json.loads(out) == {"id": "504", "title": "Titel", "note": ""}

    def test_api_error_reports_single_json_object_on_stdout(
        self, monkeypatch, capsys, tmp_path
    ) -> None:
        write_docx(tmp_path)
        write_settings(tmp_path)
        monkeypatch.chdir(tmp_path)
        stub_publish(
            monkeypatch,
            error=JoomlaApiError(409, [{"title": "Alias already in use"}]),
        )

        code = main(["2026.03 Regatta.docx", "--json"])

        out, err = capsys.readouterr()
        assert code == 1
        assert json.loads(out) == {
            "error": "Joomla API error 409: Alias already in use"
        }
        # JSON goes to stdout, never to stderr.
        assert err == ""


class TestCliSettingsEnv:
    def test_flag_uses_environment_variables_without_settings_file(
        self, monkeypatch, capsys, tmp_path, clear_joomla_env
    ) -> None:
        write_docx(tmp_path)
        # No settings.toml in the working directory.
        monkeypatch.chdir(tmp_path)
        seen = stub_publish_capturing_settings(monkeypatch)
        write_env_settings(
            monkeypatch,
            base_url="https://env.example",
            base_path="/api/index.php/v1",
            token="env-token",
        )

        code = main(["2026.03 Regatta.docx", "--settings-env"])

        assert code == 0
        assert len(seen) == 1
        assert seen[0].joomla.base_url == "https://env.example"
        assert seen[0].joomla.token == "env-token"

    def test_flag_with_missing_variable_exits_1_naming_variable(
        self, monkeypatch, capsys, tmp_path, clear_joomla_env
    ) -> None:
        write_docx(tmp_path)
        monkeypatch.chdir(tmp_path)
        calls = stub_publish(monkeypatch)
        write_env_settings(
            monkeypatch, base_url="https://env.example", base_path="/api/index.php/v1"
        )

        code = main(["2026.03 Regatta.docx", "--settings-env"])

        err = capsys.readouterr().err
        assert code == 1
        assert "DOXXWIRE_JOOMLA_TOKEN" in err
        # No conversion or network activity.
        assert calls == []

    def test_flag_combines_with_json(
        self, monkeypatch, capsys, tmp_path, clear_joomla_env
    ) -> None:
        write_docx(tmp_path)
        monkeypatch.chdir(tmp_path)
        stub_publish(monkeypatch)
        write_env_settings(
            monkeypatch,
            base_url="https://env.example",
            base_path="/api/index.php/v1",
            token="env-token",
        )

        code = main(["2026.03 Regatta.docx", "--settings-env", "--json"])

        out = capsys.readouterr().out
        assert code == 0
        assert json.loads(out) == {
            "id": "503",
            "title": "2026.03 Regatta",
            "note": "Prüfe: Titel",
        }
