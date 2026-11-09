"""Tests for the docxwire command."""

from __future__ import annotations

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
