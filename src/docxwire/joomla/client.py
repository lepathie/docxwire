"""Transport and article CRUD for the Joomla 5 content API.

Thin, synchronous client over ``requests``. This module owns the
transport contract only: endpoint composition from the Joomla
settings, the ``X-Joomla-Token`` / ``Accept`` headers, and the
``{"errors": [...]}`` failure envelope. All payload shaping lives in
:mod:`docxwire.joomla.mapping`.
"""

from __future__ import annotations

import requests

from docxwire.settings import JoomlaSettings

__all__ = ["JoomlaApiError", "JoomlaClient"]

ARTICLES_PATH = "/content/articles"
ACCEPT = "application/vnd.api+json"


class JoomlaApiError(Exception):
    """A non-2xx response from the Joomla content API.

    Carries the HTTP *status* and the server-provided *errors* entries
    from the ``{"errors": [...]}`` envelope. When the body does not
    match the envelope, *errors* is empty and the raw body is kept in
    *raw*.
    """

    def __init__(self, status: int, errors: list[dict], raw: str | None = None) -> None:
        self.status = status
        self.errors = errors
        self.raw = raw
        detail = (
            "; ".join(entry.get("title", "") for entry in errors)
            or raw
            or "unknown error"
        )
        super().__init__(f"Joomla API error {status}: {detail}")


class JoomlaClient:
    """Thin client for the Joomla 5 content API article endpoints."""

    def __init__(
        self, settings: JoomlaSettings, session: requests.Session | None = None
    ) -> None:
        self._settings = settings
        self._session = session if session is not None else requests.Session()
        self._session.headers["X-Joomla-Token"] = settings.token
        self._session.headers["Accept"] = ACCEPT
        self._endpoint = settings.base_url + settings.base_path + ARTICLES_PATH

    def list_articles(self, **params: str | int) -> list[dict]:
        """List articles, forwarding *params* as query parameters unchanged."""
        body = self._request("GET", self._endpoint, params=params or None)
        return body["data"]

    def get_article(self, article_id: int | str) -> dict:
        """Fetch one article by ID."""
        body = self._request("GET", f"{self._endpoint}/{article_id}")
        return body["data"]

    def create_article(self, payload: dict) -> dict:
        """Create an article from a flat *payload*; returns the created item."""
        body = self._request("POST", self._endpoint, json=payload)
        return body["data"]

    def update_article(self, article_id: int | str, payload: dict) -> dict:
        """Update an article by ID with a partial *payload*."""
        body = self._request("PATCH", f"{self._endpoint}/{article_id}", json=payload)
        return body["data"]

    def delete_article(self, article_id: int | str) -> None:
        """Hard-delete an article by ID (the API answers 204 with no body).

        The content API only hard-deletes articles that are already in the
        trash; for a live article the DELETE is a 204 no-op. To fully remove
        a live article, first move it to the trash (``update_article(id,
        {"state": -2})``), then call this.
        """
        self._request("DELETE", f"{self._endpoint}/{article_id}")

    def _request(self, method: str, url: str, **kwargs) -> dict:
        response = self._session.request(method, url, **kwargs)
        if response.status_code >= 400:
            raise _error_from_response(response)
        if not response.text:
            return {}
        return response.json()


def _error_from_response(response: requests.Response) -> JoomlaApiError:
    """Build a :class:`JoomlaApiError` from a failed response."""
    try:
        body = response.json()
    except ValueError:
        return JoomlaApiError(response.status_code, [], raw=response.text)
    if isinstance(body, dict) and isinstance(body.get("errors"), list):
        return JoomlaApiError(response.status_code, body["errors"], raw=response.text)
    return JoomlaApiError(response.status_code, [], raw=response.text)
