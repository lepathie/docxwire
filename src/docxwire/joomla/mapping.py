"""Pure mapping from a converted Article to a Joomla API payload.

The single place Joomla field knowledge lives: how a docxwire
``Article`` becomes the flat JSON object the content API's create
endpoint accepts (verified against the live site — see the
joomla-client change's design, "Verified contract").
"""

from __future__ import annotations

from bs4 import BeautifulSoup

from docxwire.converter.base import Article
from docxwire.settings import JoomlaSettings

__all__ = ["build_article_payload"]

ALL_LANGUAGES = "*"


def build_article_payload(article: Article, settings: JoomlaSettings) -> dict:
    """Map *article* to a flat create payload for the content API.

    The whole body goes into ``introtext`` with an empty ``fulltext``
    (no read-more split; ``articletext`` is never emitted), an unset
    article category (sentinel ``0``) falls back to the settings'
    ``default_catid``, body ``<img>`` references are rewritten to the
    images' uploaded paths (raising when one is missing), and the first
    lead image is carried in the ``images`` object. The payload's
    ``language`` is the article's language when the article carries one,
    else the settings' ``default_language``, else the all-languages
    sentinel ``*``.
    """
    payload: dict[str, object] = {
        "title": article.title,
        "alias": article.slug,
        "catid": article.catid or settings.default_catid,
        "introtext": _rewrite_body_images(article),
        "fulltext": "",
        "created_by_alias": article.created_by_alias,
        "metadesc": article.metadesc,
        "metakey": article.metakey,
        "language": article.language or settings.default_language or ALL_LANGUAGES,
    }
    if article.created_date:
        payload["created"] = article.created_date
    lead = next((image for image in article.images if image.is_lead), None)
    if lead is not None:
        payload["images"] = {
            "image_intro": lead.upload_path,
            "image_intro_alt": "",
            "image_intro_caption": lead.caption,
            "image_fulltext": lead.upload_path,
            "image_fulltext_alt": "",
            "image_fulltext_caption": lead.caption,
        }
    return payload


def _rewrite_body_images(article: Article) -> str:
    """Rewrite every body ``<img src>`` to the image's uploaded path.

    The lookup is exact: pandoc's ``src`` equals
    :attr:`Image.media_filename`. A body image without a populated
    ``upload_path`` raises, so a payload never ships with a dead
    reference.
    """
    mapping = {
        image.media_filename: image.upload_path
        for image in article.images
        if image.upload_path
    }
    soup = BeautifulSoup(article.body, "html.parser")
    imgs = soup.find_all("img")
    if not imgs:
        return article.body
    for img in imgs:
        src = img.get("src")
        if not isinstance(src, str) or src not in mapping:
            raise ValueError(f"Body image {src!r} has no upload path")
        img["src"] = mapping[src]
    return soup.decode()
