"""Thin client for the Joomla 5 REST content API."""

from docxwire.joomla.client import JoomlaApiError, JoomlaClient
from docxwire.joomla.mapping import build_article_payload

__all__ = ["JoomlaApiError", "JoomlaClient", "build_article_payload"]
