"""Publish one document end to end: convert, upload images, create the article.

This is the orchestration shared by every front-end of the tool; the CLI
calls :func:`publish_article` after loading settings from the working
directory.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

from docxwire.converter.base import Article, Image, slug_date
from docxwire.converter.docx import DocxConverter
from docxwire.joomla.client import JoomlaClient
from docxwire.joomla.mapping import build_article_payload
from docxwire.settings import Settings

__all__ = ["publish_article"]


def publish_article(docx_path: Path | str, settings: Settings) -> dict:
    """Convert *docx_path*, upload every image of the resulting article,
    and create the article on the site.

    Each image is uploaded to ``articles/<YYYY>/<MM>/<slug>/<filename>``
    under the site's ``images/`` tree, where ``<filename>`` is the media
    file's basename and the folder date is the article's slug date, falling
    back to its created date, then to the current date — and every image is
    uploaded before the article create is sent, so the created article's
    body references resolve. Returns the created article's data.

    Raises the converter's ``RuntimeError`` on conversion failure and
    ``JoomlaApiError`` on an upload or create failure.
    """
    article = DocxConverter().convert(Path(docx_path))
    client = JoomlaClient(settings.joomla)
    for image in article.images:
        rel_path = _image_rel_path(article, image)
        image.upload_path = f"/images/{rel_path}"
        client.upload_image(image.data, rel_path)
    return client.create_article(build_article_payload(article, settings.joomla))


def _image_rel_path(article: Article, image: Image) -> str:
    # The file slot is the media file's basename: pandoc's media/ extraction
    # prefix (and any other directory components) stay out of the site path.
    return (
        f"articles/{_folder_date(article)}/{article.slug}/"
        f"{Path(image.media_filename).name}"
    )


def _folder_date(article: Article) -> str:
    """``<YYYY>/<MM>``: the article's slug date, else its created date,
    else the current date."""
    if folder := slug_date(article.slug):
        return folder
    if article.created_date:
        return f"{article.created_date[:4]}/{article.created_date[5:7]}"
    today = date.today()
    return f"{today.year:04d}/{today.month:02d}"
