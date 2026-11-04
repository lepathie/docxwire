from __future__ import annotations

import json
from typing import Any
from unittest.mock import MagicMock

import pytest

from docxwire.joomla.client import JoomlaApiError, JoomlaClient
from docxwire.settings import JoomlaSettings


def make_settings() -> JoomlaSettings:
    return JoomlaSettings(
        base_url="https://example.org",
        base_path="/api/index.php/v1",
        token="test-token",
        default_catid=7,
    )


def make_session(status: int = 200, payload: object = None) -> Any:
    session = MagicMock()
    session.headers = {}
    resp = MagicMock()
    resp.status_code = status
    if payload is None:
        resp.text = ""
        resp.json.side_effect = ValueError("no json")
    else:
        resp.text = json.dumps(payload)
        resp.json.return_value = payload
    session.request.return_value = resp
    return session


@pytest.fixture
def session_factory() -> Any:
    """Factory for mock sessions with a canned response."""
    return make_session


def make_client(session: Any) -> JoomlaClient:
    return JoomlaClient(make_settings(), session=session)


class TestClientConfiguration:
    def test_endpoint_composed_from_settings(self, session_factory: Any) -> None:
        session = session_factory(200, {"data": []})
        make_client(session).list_articles()
        method, url = session.request.call_args.args
        assert method == "GET"
        assert url == "https://example.org/api/index.php/v1/content/articles"

    def test_token_sent_on_every_request(self, session_factory: Any) -> None:
        session = session_factory()
        make_client(session)
        assert session.headers["X-Joomla-Token"] == "test-token"

    def test_accept_header_sent_on_every_request(self, session_factory: Any) -> None:
        session = session_factory()
        make_client(session)
        assert session.headers["Accept"] == "application/vnd.api+json"


class TestArticleCrud:
    def test_list_returns_data_items(self, session_factory: Any) -> None:
        session = session_factory(
            200, {"data": [{"id": "1"}, {"id": "2"}], "links": {}}
        )
        assert make_client(session).list_articles() == [{"id": "1"}, {"id": "2"}]

    def test_get_returns_article(self, session_factory: Any) -> None:
        session = session_factory(200, {"data": {"id": "5", "attributes": {}}})
        assert make_client(session).get_article(5) == {"id": "5", "attributes": {}}

    def test_get_addressed_by_id(self, session_factory: Any) -> None:
        session = session_factory(200, {"data": {"id": "5"}})
        make_client(session).get_article(5)
        method, url = session.request.call_args.args
        assert method == "GET"
        assert url.endswith("/content/articles/5")

    def test_create_returns_created_article(self, session_factory: Any) -> None:
        session = session_factory(200, {"data": {"id": "9", "attributes": {}}})
        result = make_client(session).create_article({"title": "t"})
        assert result == {"id": "9", "attributes": {}}
        args, kwargs = session.request.call_args
        method, url = args
        assert method == "POST"
        assert url.endswith("/content/articles")
        assert kwargs["json"] == {"title": "t"}

    def test_update_returns_updated_article(self, session_factory: Any) -> None:
        session = session_factory(
            200, {"data": {"id": "9", "attributes": {"title": "u"}}}
        )
        result = make_client(session).update_article(9, {"title": "u"})
        assert result == {"id": "9", "attributes": {"title": "u"}}
        args, kwargs = session.request.call_args
        method, url = args
        assert method == "PATCH"
        assert url.endswith("/content/articles/9")
        assert kwargs["json"] == {"title": "u"}

    def test_delete_returns_none_on_204(self, session_factory: Any) -> None:
        session = session_factory(204)
        assert make_client(session).delete_article(9) is None
        method, url = session.request.call_args.args
        assert method == "DELETE"
        assert url.endswith("/content/articles/9")


class TestFilterPassThrough:
    def test_category_filter_forwarded(self, session_factory: Any) -> None:
        session = session_factory(200, {"data": []})
        make_client(session).list_articles(**{"filter[category]": 7})
        _, kwargs = session.request.call_args
        assert kwargs["params"] == {"filter[category]": 7}

    def test_ordering_forwarded(self, session_factory: Any) -> None:
        session = session_factory(200, {"data": []})
        make_client(session).list_articles(
            **{"list[ordering]": "title", "list[direction]": "desc"}
        )
        _, kwargs = session.request.call_args
        assert kwargs["params"] == {
            "list[ordering]": "title",
            "list[direction]": "desc",
        }


class TestErrorSurfacing:
    @pytest.mark.parametrize(
        ("status", "errors"),
        [
            (401, [{"title": "Forbidden"}]),
            (404, [{"title": "Resource not found", "code": 404}]),
            (500, [{"title": "boom"}]),
        ],
    )
    def test_non_2xx_raises_typed_error_without_retry(
        self, session_factory: Any, status: int, errors: list[dict]
    ) -> None:
        session = session_factory(status, {"errors": errors})
        with pytest.raises(JoomlaApiError) as excinfo:
            make_client(session).list_articles()
        assert excinfo.value.status == status
        assert excinfo.value.errors == errors
        assert session.request.call_count == 1

    def test_json_body_without_envelope_carries_raw_text(
        self, session_factory: Any
    ) -> None:
        session = session_factory(500, {"unexpected": "shape"})
        with pytest.raises(JoomlaApiError) as excinfo:
            make_client(session).list_articles()
        assert excinfo.value.status == 500
        assert excinfo.value.errors == []
        assert excinfo.value.raw == '{"unexpected": "shape"}'

    def test_non_json_body_carries_raw_text(self, session_factory: Any) -> None:
        session = MagicMock()
        session.headers = {}
        resp = MagicMock()
        resp.status_code = 502
        resp.text = "<html>bad gateway</html>"
        resp.json.side_effect = ValueError("no json")
        session.request.return_value = resp
        with pytest.raises(JoomlaApiError) as excinfo:
            make_client(session).list_articles()
        assert excinfo.value.status == 502
        assert excinfo.value.errors == []
        assert excinfo.value.raw == "<html>bad gateway</html>"
