from __future__ import annotations

import re
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from bs4 import BeautifulSoup

from docxwire.converter.base import Article, slugify
from docxwire.converter.docx import DocxConverter


@pytest.fixture(scope="class")
def converted_article(ruderkurs_doc: Path) -> Article:
    return DocxConverter().convert(ruderkurs_doc)


@pytest.fixture(scope="class")
def parsed_html(converted_article: Article) -> BeautifulSoup:
    return BeautifulSoup(converted_article.body, "html.parser")


class TestDocxConverter:
    def test_convert_populates_required_fields(
        self, converted_article: Article, ruderkurs_doc: Path
    ) -> None:
        assert converted_article.source_file == ruderkurs_doc
        assert converted_article.title
        assert len(converted_article.body) > 0
        assert converted_article.source_file.exists()

    def test_convert_derives_title_from_heading_in_body(
        self, converted_article
    ) -> None:
        assert converted_article.title == "Ruderkurse gestartet"

    def test_convert_derives_slug_from_filename(
        self, converted_article: Article
    ) -> None:
        assert converted_article.slug == "ruderkurs-2025-04"

    def test_convert_strips_first_heading_from_body(
        self, parsed_html: BeautifulSoup
    ) -> None:
        heading = parsed_html.find(re.compile(r"^h[1-6]$"))
        assert heading is None

    def test_convert_extracts_media(
        self, converted_article: Article, parsed_html: BeautifulSoup
    ) -> None:
        image = converted_article.images[0]
        assert image is not None
        assert image.media_filename == "media/image1.jpg"
        assert len(image.data) > 0
        # The single Ruderkurs image sits before the heading, so it is a lead
        # image: flagged as lead and removed from the body.
        assert image.is_lead is True
        assert parsed_html.find("img") is None

    @pytest.mark.parametrize(
        "exc",
        [
            OSError("pandoc binary missing"),
            ValueError("invalid format option"),
            RuntimeError("unexpected subprocess crash"),
        ],
    )
    def test_convert_wraps_errors(
        self, monkeypatch, ruderkurs_doc: Path, exc: Exception
    ) -> None:
        monkeypatch.setattr("pypandoc.convert_file", MagicMock(side_effect=exc))

        with pytest.raises(
            RuntimeError, match=f"conversion of {ruderkurs_doc.name} failed: {exc}"
        ):
            DocxConverter().convert(ruderkurs_doc)

    def test_convert_fallback_title_when_no_heading(
        self, monkeypatch, ruderkurs_doc: Path
    ) -> None:
        """When HTML has no heading, title falls back to filename stem."""
        monkeypatch.setattr(
            "pypandoc.convert_file", MagicMock(return_value="<p>no headings here</p>")
        )
        article = DocxConverter().convert(ruderkurs_doc)
        assert article.title == "2025.04 Ruderkurs"
        assert article.slug == "ruderkurs-2025-04"

    def test_convert_removes_single_preheading_image_and_marks_it_lead(
        self, ruderkurs_doc: Path
    ) -> None:
        article = DocxConverter().convert(ruderkurs_doc)
        soup = BeautifulSoup(article.body, "html.parser")
        assert soup.find("img") is None
        assert [img.is_lead for img in article.images] == [True]

    def test_convert_removes_all_preheading_images_and_marks_them_lead(
        self, lichterfest_doc: Path
    ) -> None:
        article = DocxConverter().convert(lichterfest_doc)
        soup = BeautifulSoup(article.body, "html.parser")
        assert soup.find("img") is None
        assert [img.is_lead for img in article.images] == [True, True]

    def test_convert_keeps_inbody_images_unmarked_when_lead_present(
        self, heineken_doc: Path
    ) -> None:
        article = DocxConverter().convert(heineken_doc)
        soup = BeautifulSoup(article.body, "html.parser")
        assert len(soup.find_all("img")) == 5
        assert sum(img.is_lead for img in article.images) == 1
        assert sum(not img.is_lead for img in article.images) == 5

    def test_convert_marks_no_image_lead_without_preheading_image(
        self, abrudern_doc: Path
    ) -> None:
        article = DocxConverter().convert(abrudern_doc)
        soup = BeautifulSoup(article.body, "html.parser")
        assert len(soup.find_all("img")) == 2
        assert all(img.is_lead is False for img in article.images)

    def test_convert_keeps_images_in_body_without_heading(
        self, monkeypatch, ruderkurs_doc: Path
    ) -> None:
        monkeypatch.setattr(
            "pypandoc.convert_file",
            MagicMock(return_value="<p>text</p><img src='media/x.jpg'>"),
        )
        article = DocxConverter().convert(ruderkurs_doc)
        soup = BeautifulSoup(article.body, "html.parser")
        assert soup.find("img") is not None
        assert all(img.is_lead is False for img in article.images)

    def test_convert_fails_when_lead_image_has_no_matching_media(
        self, monkeypatch, ruderkurs_doc: Path
    ) -> None:
        monkeypatch.setattr(
            "pypandoc.convert_file",
            MagicMock(return_value="<img src='media/missing.jpg'><h1>Title</h1>"),
        )
        with pytest.raises(RuntimeError):
            DocxConverter().convert(ruderkurs_doc)


class TestSlugify:
    @pytest.mark.parametrize(
        "filename, expected",
        [
            ("2025.04 Ruderkurs", "ruderkurs-2025-04"),
            ("2024-12_Year Review", "year-review-2024-12"),
            ("My---Article   Title", "my-article-title"),
            ("simple", "simple"),
            ("  spaced  title  ", "spaced-title"),
        ],
    )
    def test_slugify_formats_correctly(self, filename: str, expected: str) -> None:
        assert slugify(filename) == expected
