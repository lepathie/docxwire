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
        img = parsed_html.find("img")
        assert img is not None
        src = img.get("src")
        assert src is not None
        assert image.media_filename in src

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
