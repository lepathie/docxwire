"""Tests for the single-document publishing flow."""

from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest

from docxwire.converter.base import Article, Image
from docxwire.joomla.client import JoomlaApiError
from docxwire.joomla.mapping import build_article_payload
from docxwire.publish import publish_article
from docxwire.settings import JoomlaSettings, Settings

CREATED = {
    "id": "503",
    "attributes": {"title": "2026.03 Regatta", "note": "Prüfe: Titel"},
}


def make_settings() -> Settings:
    return Settings(
        joomla=JoomlaSettings(
            base_url="https://example.org",
            base_path="/api/index.php/v1",
            token="test-token",
        )
    )


def make_article(**overrides) -> Article:
    base: dict = {
        "source_file": Path("2026.03 Regatta.docx"),
        "title": "2026.03 Regatta",
        "slug": "regatta-2026-03",
        "body": '<p>Text</p><img src="media/lead.jpg" /><img src="media/body.jpg" />',
        # A created date in a different month than the slug date: the slug
        # date must win.
        "created_date": "2026-10-01 10:00:00",
        "note": "Prüfe: Titel",
        "images": [
            # Pandoc's --extract-media layout: files under a media/ prefix.
            Image(media_filename="media/lead.jpg", data=b"lead", is_lead=True),
            Image(media_filename="media/body.jpg", data=b"body"),
        ],
    }
    base.update(overrides)
    return Article(**base)


def install_stubs(
    monkeypatch,
    *,
    article: Article | None = None,
    converter_error: Exception | None = None,
    upload_error: Exception | None = None,
    calls: list[str],
    payloads: list[dict],
) -> None:
    """Stub the flow's collaborators inside ``docxwire.publish``."""

    class StubConverter:
        def convert(self, src: Path) -> Article:
            if converter_error is not None:
                raise converter_error
            assert article is not None
            return article

    class StubClient:
        def __init__(self, settings: JoomlaSettings) -> None:
            pass

        def upload_image(self, data: bytes, rel_path: str) -> dict:
            if upload_error is not None:
                raise upload_error
            calls.append(f"upload:{rel_path}")
            return {}

        def create_article(self, payload: dict) -> dict:
            calls.append("create")
            payloads.append(payload)
            return CREATED

    monkeypatch.setattr("docxwire.publish.DocxConverter", StubConverter)
    monkeypatch.setattr("docxwire.publish.JoomlaClient", StubClient)


class TestPublishArticle:
    def test_converts_uploads_all_images_then_creates(self, monkeypatch) -> None:
        calls: list[str] = []
        payloads: list[dict] = []
        article = make_article()
        install_stubs(monkeypatch, article=article, calls=calls, payloads=payloads)

        created = publish_article(Path("2026.03 Regatta.docx"), make_settings())

        assert created == CREATED
        # Every image uploaded — with the media/ extraction prefix dropped
        # and the title date (2026/03) in the folder, not the created date
        # (2026/10) — and every upload before the create call.
        assert calls == [
            "upload:articles/2026/03/regatta-2026-03/lead.jpg",
            "upload:articles/2026/03/regatta-2026-03/body.jpg",
            "create",
        ]
        # Every image's upload_path is the site-relative path under images/.
        assert article.images[0].upload_path == (
            "/images/articles/2026/03/regatta-2026-03/lead.jpg"
        )
        assert article.images[1].upload_path == (
            "/images/articles/2026/03/regatta-2026-03/body.jpg"
        )
        # The create payload is the standard mapping of the article.
        assert payloads == [build_article_payload(article, make_settings().joomla)]

    def test_slug_date_drives_folder_when_title_is_dateless(self, monkeypatch):
        calls: list[str] = []
        payloads: list[dict] = []
        # The title (first heading) carries no date; the slug does.
        article = make_article(title="Regatta")
        install_stubs(monkeypatch, article=article, calls=calls, payloads=payloads)

        publish_article(Path("2026.03 Regatta.docx"), make_settings())

        assert calls == [
            "upload:articles/2026/03/regatta-2026-03/lead.jpg",
            "upload:articles/2026/03/regatta-2026-03/body.jpg",
            "create",
        ]

    def test_slug_date_wins_over_conflicting_title_date(self, monkeypatch) -> None:
        calls: list[str] = []
        payloads: list[dict] = []
        article = make_article(title="2026.05 Regatta")
        install_stubs(monkeypatch, article=article, calls=calls, payloads=payloads)

        publish_article(Path("2026.03 Regatta.docx"), make_settings())

        assert calls == [
            "upload:articles/2026/03/regatta-2026-03/lead.jpg",
            "upload:articles/2026/03/regatta-2026-03/body.jpg",
            "create",
        ]

    def test_dateless_slug_uses_created_date(self, monkeypatch) -> None:
        calls: list[str] = []
        payloads: list[dict] = []
        article = make_article(title="Regatta", slug="regatta")
        install_stubs(monkeypatch, article=article, calls=calls, payloads=payloads)

        publish_article(Path("2026.03 Regatta.docx"), make_settings())

        assert calls == [
            "upload:articles/2026/10/regatta/lead.jpg",
            "upload:articles/2026/10/regatta/body.jpg",
            "create",
        ]

    def test_dateless_slug_without_created_date_uses_current_date(self, monkeypatch):
        calls: list[str] = []
        payloads: list[dict] = []
        article = make_article(title="Regatta", slug="regatta", created_date="")
        install_stubs(monkeypatch, article=article, calls=calls, payloads=payloads)

        publish_article(Path("2026.03 Regatta.docx"), make_settings())

        today = date.today()
        folder = f"{today.year:04d}/{today.month:02d}"
        assert calls == [
            f"upload:articles/{folder}/regatta/lead.jpg",
            f"upload:articles/{folder}/regatta/body.jpg",
            "create",
        ]

    def test_conversion_failure_propagates_without_side_effects(
        self, monkeypatch
    ) -> None:
        calls: list[str] = []
        payloads: list[dict] = []
        install_stubs(
            monkeypatch,
            converter_error=RuntimeError(
                "conversion of 2026.03 Regatta.docx failed: pandoc error"
            ),
            calls=calls,
            payloads=payloads,
        )

        with pytest.raises(
            RuntimeError, match="conversion of 2026.03 Regatta.docx failed"
        ):
            publish_article(Path("2026.03 Regatta.docx"), make_settings())

        assert calls == []

    def test_upload_failure_propagates_without_create(self, monkeypatch) -> None:
        calls: list[str] = []
        payloads: list[dict] = []
        article = make_article()
        install_stubs(
            monkeypatch,
            article=article,
            upload_error=JoomlaApiError(500, [{"title": "storage full"}]),
            calls=calls,
            payloads=payloads,
        )

        with pytest.raises(JoomlaApiError, match="storage full"):
            publish_article(Path("2026.03 Regatta.docx"), make_settings())

        # The first upload fails; nothing is uploaded and no create is sent.
        assert calls == []
