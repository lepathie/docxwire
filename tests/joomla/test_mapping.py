from __future__ import annotations

from pathlib import Path

import pytest

from docxwire.converter.base import Article
from docxwire.joomla.mapping import build_article_payload


def make_article(**overrides: object) -> Article:
    article = Article(
        source_file=Path("2026.03 Test.docx"),
        title="Test Title",
        slug="test-title",
        body="<p>Body HTML</p>",
        catid=0,
        created_date="2026-03-01 12:00:00",
        created_by_alias="Jane Author",
        metadesc="A description",
        metakey="a, key",
    )
    for key, value in overrides.items():
        setattr(article, key, value)
    return article


class TestPayloadBasics:
    def test_title_alias_and_category_are_mapped(self) -> None:
        payload = build_article_payload(make_article(catid=5), default_catid=7)
        assert payload["title"] == "Test Title"
        assert payload["alias"] == "test-title"
        assert payload["catid"] == 5

    def test_unset_category_falls_back_to_default(self) -> None:
        payload = build_article_payload(make_article(catid=0), default_catid=7)
        assert payload["catid"] == 7


class TestBodyField:
    def test_body_placed_in_single_body_field(self) -> None:
        payload = build_article_payload(make_article(), default_catid=7)
        assert payload["introtext"] == "<p>Body HTML</p>"
        assert payload["fulltext"] == ""

    def test_deprecated_field_not_used(self) -> None:
        payload = build_article_payload(make_article(), default_catid=7)
        assert "articletext" not in payload


class TestMetadataCarryOver:
    @pytest.mark.parametrize(
        ("payload_key", "expected"),
        [
            ("created_by_alias", "Jane Author"),
            ("metadesc", "A description"),
            ("metakey", "a, key"),
            ("language", "*"),
        ],
    )
    def test_field_carried(self, payload_key: str, expected: object) -> None:
        payload = build_article_payload(make_article(), default_catid=7)
        assert payload[payload_key] == expected

    def test_creation_date_is_carried(self) -> None:
        payload = build_article_payload(make_article(), default_catid=7)
        assert payload["created"] == "2026-03-01 12:00:00"

    def test_created_omitted_when_no_date(self) -> None:
        payload = build_article_payload(make_article(created_date=""), default_catid=7)
        assert "created" not in payload
