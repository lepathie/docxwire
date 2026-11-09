from __future__ import annotations

from pathlib import Path

import pytest
from bs4 import BeautifulSoup

from docxwire.converter.base import Article, Image
from docxwire.joomla.mapping import build_article_payload
from docxwire.settings import JoomlaSettings


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


def make_image(**overrides: object) -> Image:
    image = Image(media_filename="media/image1.png", data=b"\x89PNG")
    for key, value in overrides.items():
        setattr(image, key, value)
    return image


def make_settings(
    default_catid: int = 7, default_language: str = "*"
) -> JoomlaSettings:
    return JoomlaSettings(
        base_url="https://example.org",
        base_path="/api/index.php/v1",
        token="test-token",
        default_catid=default_catid,
        default_language=default_language,
    )


class TestPayloadBasics:
    def test_title_alias_and_category_are_mapped(self) -> None:
        payload = build_article_payload(make_article(catid=5), make_settings())
        assert payload["title"] == "Test Title"
        assert payload["alias"] == "test-title"
        assert payload["catid"] == 5

    def test_unset_category_falls_back_to_default(self) -> None:
        payload = build_article_payload(make_article(catid=0), make_settings())
        assert payload["catid"] == 7


class TestBodyField:
    def test_body_placed_in_single_body_field(self) -> None:
        payload = build_article_payload(make_article(), make_settings())
        assert payload["introtext"] == "<p>Body HTML</p>"
        assert payload["fulltext"] == ""

    def test_deprecated_field_not_used(self) -> None:
        payload = build_article_payload(make_article(), make_settings())
        assert "articletext" not in payload


class TestMetadataCarryOver:
    @pytest.mark.parametrize(
        ("overrides", "payload_key", "expected"),
        [
            # Default fields, carried from the make_article() fixture defaults
            ({}, "created_by_alias", "Jane Author"),
            ({}, "metadesc", "A description"),
            ({}, "metakey", "a, key"),
            ({}, "language", "*"),
            ({}, "created", "2026-03-01 12:00:00"),
            # Explicit overrides: note is not set by the make_article() defaults
            ({"note": "Prüfe: Titel"}, "note", "Prüfe: Titel"),
            ({"note": ""}, "note", ""),
        ],
        ids=[
            "carries_default_created_by_alias",
            "carries_default_metadesc",
            "carries_default_metakey",
            "carries_default_language",
            "carries_default_created_date",
            "carries_custom_note",
            "carries_empty_note",
        ],
    )
    def test_field_carried(
        self,
        overrides: dict[str, object],
        payload_key: str,
        expected: object,
    ) -> None:
        article = make_article(**overrides)
        settings = make_settings()
        payload = build_article_payload(article, settings)
        assert payload[payload_key] == expected

    def test_created_omitted_when_no_date(self) -> None:
        article = make_article(created_date="")
        settings = make_settings()
        payload = build_article_payload(article, settings)
        assert "created" not in payload


class TestLanguageResolution:
    def test_article_language_wins_over_settings(self) -> None:
        payload = build_article_payload(
            make_article(language="de-DE"),
            make_settings(default_language="en-GB"),
        )
        assert payload["language"] == "de-DE"

    def test_settings_language_used_when_article_has_none(self) -> None:
        payload = build_article_payload(
            make_article(), make_settings(default_language="de-DE")
        )
        assert payload["language"] == "de-DE"

    def test_sentinel_used_when_neither_is_set(self) -> None:
        payload = build_article_payload(make_article(), make_settings())
        assert payload["language"] == "*"


class TestBodyImageRewrite:
    def test_body_references_rewritten_to_upload_path(self) -> None:
        article = make_article(
            body='<p>Text <img src="media/image1.png" /> more</p>',
            images=[
                make_image(upload_path="/images/articles/2026/03/test-title/image1.png")
            ],
        )
        payload = build_article_payload(article, make_settings())
        soup = BeautifulSoup(payload["introtext"], "html.parser")
        img = soup.find("img")
        assert img is not None
        assert img["src"] == "/images/articles/2026/03/test-title/image1.png"

    def test_unuploaded_body_image_fails_build(self) -> None:
        article = make_article(
            body='<p><img src="media/image1.png"></p>',
            images=[make_image()],  # upload_path never populated
        )
        with pytest.raises(ValueError):
            build_article_payload(article, make_settings())

    def test_absolute_temp_path_reference_matched_by_basename(self) -> None:
        # Pandoc writes some body references as absolute paths into its
        # temporary media-extraction directory.
        article = make_article(
            body='<p><img src="/tmp/media-a9visq6k/media/image1.jpeg"></p>',
            images=[
                make_image(
                    media_filename="media/image1.jpeg",
                    upload_path="/images/articles/2026/07/test-title/image1.jpeg",
                )
            ],
        )
        payload = build_article_payload(article, make_settings())
        soup = BeautifulSoup(payload["introtext"], "html.parser")
        img = soup.find("img")
        assert img is not None
        assert img["src"] == "/images/articles/2026/07/test-title/image1.jpeg"

    def test_unmatched_basename_fails_build(self) -> None:
        article = make_article(
            body='<p><img src="/tmp/media-a9visq6k/media/other.jpeg"></p>',
            images=[
                make_image(upload_path="/images/articles/2026/07/test-title/image1.png")
            ],
        )
        with pytest.raises(ValueError):
            build_article_payload(article, make_settings())


class TestImagesObject:
    def test_lead_image_carried_in_both_slots(self) -> None:
        article = make_article(
            images=[
                make_image(
                    upload_path="/images/articles/2026/03/test-title/image1.png",
                    caption="Eine Caption",
                    is_lead=True,
                )
            ]
        )
        payload = build_article_payload(article, make_settings())
        assert payload["images"] == {
            "image_intro": "/images/articles/2026/03/test-title/image1.png",
            "image_intro_alt": "",
            "image_intro_caption": "Eine Caption",
            "image_fulltext": "/images/articles/2026/03/test-title/image1.png",
            "image_fulltext_alt": "",
            "image_fulltext_caption": "Eine Caption",
        }

    def test_only_first_lead_referenced(self) -> None:
        article = make_article(
            images=[
                make_image(
                    upload_path="/images/articles/2026/03/test-title/first.png",
                    caption="First",
                    is_lead=True,
                ),
                make_image(
                    media_filename="media/image2.png",
                    upload_path="/images/articles/2026/03/test-title/second.png",
                    caption="Second",
                    is_lead=True,
                ),
            ]
        )
        payload = build_article_payload(article, make_settings())
        assert (
            payload["images"]["image_intro"]
            == "/images/articles/2026/03/test-title/first.png"
        )
        assert (
            payload["images"]["image_fulltext"]
            == "/images/articles/2026/03/test-title/first.png"
        )
        assert (
            "/images/articles/2026/03/test-title/second.png"
            not in payload["images"].values()
        )

    def test_no_lead_image_means_no_images_key(self) -> None:
        article = make_article(
            images=[
                make_image(upload_path="/images/articles/2026/03/test-title/image1.png")
            ]
        )
        payload = build_article_payload(article, make_settings())
        assert "images" not in payload


class TestCombinedMapping:
    def test_lead_and_body_images_in_one_payload(self) -> None:
        article = make_article(
            body='<p><img src="media/image2.png"></p>',
            images=[
                make_image(
                    upload_path="/images/articles/2026/03/test-title/image1.png",
                    caption="Lead caption",
                    is_lead=True,
                ),
                make_image(
                    media_filename="media/image2.png",
                    upload_path="/images/articles/2026/03/test-title/image2.png",
                ),
            ],
        )
        payload = build_article_payload(article, make_settings())
        soup = BeautifulSoup(payload["introtext"], "html.parser")
        img = soup.find("img")
        assert img is not None
        assert img["src"] == "/images/articles/2026/03/test-title/image2.png"
        assert (
            payload["images"]["image_intro"]
            == "/images/articles/2026/03/test-title/image1.png"
        )
        assert (
            payload["images"]["image_fulltext"]
            == "/images/articles/2026/03/test-title/image1.png"
        )
