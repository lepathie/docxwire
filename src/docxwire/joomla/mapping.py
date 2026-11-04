"""Pure mapping from a converted Article to a Joomla API payload.

The single place Joomla field knowledge lives: how a docxwire
``Article`` becomes the flat JSON object the content API's create
endpoint accepts (verified against the live site — see the
joomla-client change's design, "Verified contract").
"""

from __future__ import annotations

from docxwire.converter.base import Article

__all__ = ["build_article_payload"]

ALL_LANGUAGES = "*"


def build_article_payload(article: Article, default_catid: int) -> dict:
    """Map *article* to a flat create payload for the content API.

    The whole body goes into ``introtext`` with an empty ``fulltext``
    (no read-more split; ``articletext`` is never emitted), and an
    unset article category (sentinel ``0``) falls back to
    *default_catid*.
    """
    payload: dict[str, object] = {
        "title": article.title,
        "alias": article.slug,
        "catid": article.catid or default_catid,
        "introtext": article.body,
        "fulltext": "",
        "created_by_alias": article.created_by_alias,
        "metadesc": article.metadesc,
        "metakey": article.metakey,
        "language": ALL_LANGUAGES,
    }
    if article.created_date:
        payload["created"] = article.created_date
    return payload
