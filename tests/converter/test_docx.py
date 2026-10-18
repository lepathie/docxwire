from __future__ import annotations

import re
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from bs4 import BeautifulSoup

from docxwire.converter.base import Article
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
        assert converted_article.title == "2025.04 Ruderkurs"
        assert len(converted_article.body) > 0
        assert converted_article.source_file.exists()

    def test_convert_includes_heading(self, parsed_html) -> None:
        heading = parsed_html.find(re.compile(r"^h[1-6]$"))
        assert heading is not None
        assert heading.get_text() == "Ruderkurse gestartet"

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
