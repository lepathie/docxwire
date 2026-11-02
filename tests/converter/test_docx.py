from __future__ import annotations

import re
import tempfile
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from bs4 import BeautifulSoup

from docxwire.converter.base import Article
from docxwire.converter.docx import DocxConverter


@pytest.fixture(scope="module")
def converted_article(ruderkurs_doc: Path) -> Article:
    return DocxConverter().convert(ruderkurs_doc)


@pytest.fixture(scope="module")
def parsed_html(converted_article: Article) -> BeautifulSoup:
    return BeautifulSoup(converted_article.body, "html.parser")


@pytest.fixture
def pandoc_media_x(monkeypatch) -> None:
    """Point pypandoc's extract-media dir at one containing media/x.jpg."""
    real_mkdtemp = tempfile.mkdtemp

    def mkdtemp_with_x(
        suffix: str | None = None,
        prefix: str | None = None,
        dir: str | None = None,
    ) -> str:
        media_dir = real_mkdtemp(suffix=suffix, prefix=prefix, dir=dir)
        media = Path(media_dir) / "media"
        media.mkdir()
        (media / "x.jpg").write_bytes(b"\xff\xd8\x8egallery-placeholder")
        return media_dir

    monkeypatch.setattr(tempfile, "mkdtemp", mkdtemp_with_x)


class TestDocxConverter:
    def test_populates_required_fields(
        self, converted_article: Article, ruderkurs_doc: Path
    ) -> None:
        assert converted_article.source_file == ruderkurs_doc
        assert converted_article.title
        assert len(converted_article.body) > 0
        assert converted_article.source_file.exists()

    def test_derives_slug_from_filename(self, converted_article: Article) -> None:
        assert converted_article.slug == "ruderkurs-2025-04"

    def test_extracts_media(self, converted_article: Article) -> None:
        image = converted_article.images[0]
        assert image.media_filename == "media/image1.jpg"
        assert len(image.data) > 0

    @pytest.mark.parametrize(
        "exc",
        [
            OSError("pandoc binary missing"),
            ValueError("invalid format option"),
            RuntimeError("unexpected subprocess crash"),
        ],
    )
    def test_wraps_errors(
        self, monkeypatch, ruderkurs_doc: Path, exc: Exception
    ) -> None:
        monkeypatch.setattr("pypandoc.convert_file", MagicMock(side_effect=exc))

        with pytest.raises(
            RuntimeError, match=f"conversion of {ruderkurs_doc.name} failed: {exc}"
        ):
            DocxConverter().convert(ruderkurs_doc)


class TestHeading:
    def test_derives_title_from_heading_in_body(
        self, converted_article: Article
    ) -> None:
        assert converted_article.title == "Ruderkurse gestartet"

    def test_strips_first_heading_from_body(self, parsed_html: BeautifulSoup) -> None:
        heading = parsed_html.find(re.compile(r"^h[1-6]$"))
        assert heading is None

    def test_fallback_title_when_no_heading(
        self, monkeypatch, ruderkurs_doc: Path
    ) -> None:
        """When HTML has no heading, title falls back to filename stem."""
        monkeypatch.setattr(
            "pypandoc.convert_file", MagicMock(return_value="<p>no headings here</p>")
        )
        article = DocxConverter().convert(ruderkurs_doc)
        assert article.title == "2025.04 Ruderkurs"
        assert article.slug == "ruderkurs-2025-04"


class TestLeadImages:
    def test_removes_single_preheading_image_and_marks_it_lead(
        self, ruderkurs_doc: Path
    ) -> None:
        article = DocxConverter().convert(ruderkurs_doc)
        soup = BeautifulSoup(article.body, "html.parser")
        assert soup.find("img") is None
        assert [img.is_lead for img in article.images] == [True]

    def test_removes_all_preheading_images_and_marks_them_lead(
        self, lichterfest_doc: Path
    ) -> None:
        article = DocxConverter().convert(lichterfest_doc)
        soup = BeautifulSoup(article.body, "html.parser")
        assert soup.find("img") is None
        assert [img.is_lead for img in article.images] == [True, True]

    def test_keeps_inbody_images_unmarked_when_lead_present(
        self, heineken_doc: Path
    ) -> None:
        article = DocxConverter().convert(heineken_doc)
        soup = BeautifulSoup(article.body, "html.parser")
        assert len(soup.find_all("img")) == 5
        assert sum(img.is_lead for img in article.images) == 1
        assert sum(not img.is_lead for img in article.images) == 5

    def test_marks_no_image_lead_without_preheading_image(
        self, abrudern_doc: Path
    ) -> None:
        article = DocxConverter().convert(abrudern_doc)
        soup = BeautifulSoup(article.body, "html.parser")
        assert len(soup.find_all("img")) == 2
        assert all(img.is_lead is False for img in article.images)

    def test_keeps_images_in_body_without_heading(
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

    def test_fails_when_lead_image_has_no_matching_media(
        self, monkeypatch, ruderkurs_doc: Path
    ) -> None:
        monkeypatch.setattr(
            "pypandoc.convert_file",
            MagicMock(return_value="<img src='media/missing.jpg'><h1>Title</h1>"),
        )
        with pytest.raises(RuntimeError):
            DocxConverter().convert(ruderkurs_doc)


class TestImageCaptions:
    """Caption capture: lead cut, in-body figure rewrite, guess flagging."""

    def test_lead_image_caption_captured_and_cut_from_body(
        self, converted_article: Article, parsed_html: BeautifulSoup
    ) -> None:
        caption = (
            "Unter Anleitung geht es für die Teilnehmenden das erste Mal aufs Wasser"
        )
        assert converted_article.images[0].caption == caption
        assert caption not in converted_article.body
        assert all(p.get_text(strip=True) for p in parsed_html.find_all("p"))

    def test_all_lead_image_captions_captured_and_cut_from_body(
        self, lichterfest_doc: Path
    ) -> None:
        article = DocxConverter().convert(lichterfest_doc)
        soup = BeautifulSoup(article.body, "html.parser")
        captions = {img.media_filename: img.caption for img in article.images}
        assert captions["media/image1.jpeg"] == (
            "Bunt erstrahlt wirkt unser Ruderrevier nochmal ganz besonders"
        )
        assert captions["media/image3.jpg"] == (
            "Hingucker beim Lichterfest: Verzierte Ruderboote erleuchten den Neckar"
        )
        assert "Bunt erstrahlt wirkt unser Ruderrevier" not in article.body
        assert "Hingucker beim Lichterfest" not in article.body
        assert all(p.get_text(strip=True) for p in soup.find_all("p"))

    def test_inbody_images_become_figures_with_captions(
        self, heineken_doc: Path
    ) -> None:
        article = DocxConverter().convert(heineken_doc)
        soup = BeautifulSoup(article.body, "html.parser")
        captions = {img.media_filename: img.caption for img in article.images}
        assert captions["media/image1.jpeg"] == (
            "Trophäe in der MRV-Achterhalle, zum vierten Mal in Amsterdam"
        )
        assert "Trophäe in der MRV-Achterhalle" not in article.body
        body_images = soup.find_all("img")
        assert len(body_images) == 5
        for img_tag in body_images:
            figure = img_tag.find_parent("figure")
            assert figure is not None
            figcaption = figure.find("figcaption")
            assert figcaption is not None
            src = img_tag["src"]
            assert isinstance(src, str)
            expected = next(
                text
                for filename, text in captions.items()
                if Path(filename).name == Path(src).name
            )
            assert figcaption.get_text() == expected
        assert soup.find("div", attrs={"data-custom-style": "Bildunterschrift"}) is None
        assert all(img.caption for img in article.images)

    def test_inbody_images_become_figures_and_no_image_marked_lead(
        self, abrudern_doc: Path
    ) -> None:
        article = DocxConverter().convert(abrudern_doc)
        soup = BeautifulSoup(article.body, "html.parser")
        captions = {img.media_filename: img.caption for img in article.images}
        assert (
            captions["media/image1.jpeg"]
            == "Die Sieger und Platzierten des Würfelvierers."
        )
        assert captions["media/image2.jpeg"] == "Alle Teilnehmer der Clubregatta"
        body_images = soup.find_all("img")
        assert len(body_images) == 2
        for img_tag in body_images:
            figure = img_tag.find_parent("figure")
            assert figure is not None
            assert figure.find("figcaption") is not None
        assert all(img.is_lead is False for img in article.images)

    def test_lead_plain_caption_line_captured_and_cut_from_body(
        self, pandoc_media_x, monkeypatch, ruderkurs_doc: Path
    ) -> None:
        monkeypatch.setattr(
            "pypandoc.convert_file",
            MagicMock(
                return_value=(
                    "<p><img src='media/x.jpg'></p>"
                    "<p>Ein Beispielbild ohne Bildunterschrift-Stil</p>"
                    "<h1>Titel</h1><p>Fliesstext</p>"
                )
            ),
        )
        article = DocxConverter().convert(ruderkurs_doc)
        assert (
            article.images[0].caption == "Ein Beispielbild ohne Bildunterschrift-Stil"
        )
        assert "Beispielbild" not in article.body
        assert BeautifulSoup(article.body, "html.parser").find("img") is None

    def test_inbody_image_without_caption_line_stays_unchanged(
        self, pandoc_media_x, monkeypatch, ruderkurs_doc: Path
    ) -> None:
        # No caption for any image: next block is a heading (x), an image
        # block (y), an empty paragraph (z), a shared image block (w1/w2),
        # or the image has no src (srcless).
        monkeypatch.setattr(
            "pypandoc.convert_file",
            MagicMock(
                return_value=(
                    "<h1>Titel</h1><p><img src='media/x.jpg'></p><h2>Next</h2>"
                    "<p><img src='media/y.jpg'></p>"
                    "<p><img src='media/z.jpg'></p><p></p>"
                    "<p><img src='media/w1.jpg'><img src='media/w2.jpg'></p>"
                    "<h3>Ende</h3>"
                    "<p><img></p><p>Unterschrift ohne Quelle</p>"
                )
            ),
        )
        article = DocxConverter().convert(ruderkurs_doc)
        soup = BeautifulSoup(article.body, "html.parser")
        assert article.images[0].caption == ""
        assert soup.find("figure") is None
        for name in ("x.jpg", "y.jpg", "z.jpg", "w1.jpg", "w2.jpg"):
            img = soup.find("img", src=f"media/{name}")
            assert img is not None
            parent = img.parent
            assert parent is not None
            assert parent.name == "p"
        assert any(img.get("src") is None for img in soup.find_all("img"))

    def test_inbody_plain_caption_line_becomes_figure_with_captured_caption(
        self, pandoc_media_x, monkeypatch, ruderkurs_doc: Path
    ) -> None:
        monkeypatch.setattr(
            "pypandoc.convert_file",
            MagicMock(
                return_value=(
                    "<h1>Titel</h1><p><img src='media/x.jpg'></p>"
                    "<p>Beispielunterschrift</p><p>Fliesstext</p>"
                )
            ),
        )
        article = DocxConverter().convert(ruderkurs_doc)
        soup = BeautifulSoup(article.body, "html.parser")
        figure = soup.find("figure")
        assert figure is not None
        img = figure.find("img")
        assert img is not None
        assert img["src"] == "media/x.jpg"
        figcaption = figure.find("figcaption")
        assert figcaption is not None
        assert figcaption.get_text() == "Beispielunterschrift"
        assert article.images[0].caption == "Beispielunterschrift"

    def test_inbody_plain_caption_line_flags_guess_in_note(
        self, pandoc_media_x, monkeypatch, ruderkurs_doc: Path
    ) -> None:
        # x.jpg matches extracted media; missing.jpg has no extracted media
        # file, so the note can only name x.jpg.
        monkeypatch.setattr(
            "pypandoc.convert_file",
            MagicMock(
                return_value=(
                    "<h1>Titel</h1><p><img src='media/x.jpg'></p>"
                    "<p>Geheimtext der Beispielunterschrift</p>"
                    "<p><img src='media/missing.jpg'></p>"
                    "<p>Waisenunterschrift</p>"
                )
            ),
        )
        article = DocxConverter().convert(ruderkurs_doc)
        assert article.note
        assert "media/x.jpg" in article.note
        assert "missing.jpg" not in article.note
        assert "\n" not in article.note
        assert "Geheimtext" not in article.note
        assert "Waisenunterschrift" not in article.note

    def test_styled_caption_line_not_flagged_in_note(
        self, converted_article: Article
    ) -> None:
        assert converted_article.note == ""
