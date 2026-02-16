"""
Unit tests for agent/tools/web.py.

Stage: 05 - TEST
Sprint: Sprint 02
"""

import json
import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from nanobot.agent.tools.web import (
    _strip_tags,
    _normalize,
    _validate_url,
    WebSearchTool,
    WebFetchTool,
    USER_AGENT,
    MAX_REDIRECTS,
)


class TestStripTags:
    def test_plain_text(self):
        assert _strip_tags("hello world") == "hello world"

    def test_removes_tags(self):
        assert _strip_tags("<p>hello</p>") == "hello"

    def test_removes_script(self):
        assert _strip_tags("<script>alert('xss')</script>hello") == "hello"

    def test_removes_style(self):
        assert _strip_tags("<style>.foo{color:red}</style>hello") == "hello"

    def test_decodes_entities(self):
        assert _strip_tags("&amp; &lt; &gt;") == "& < >"

    def test_nested_tags(self):
        assert _strip_tags("<div><p><b>hello</b></p></div>") == "hello"

    def test_empty(self):
        assert _strip_tags("") == ""


class TestNormalize:
    def test_collapse_spaces(self):
        assert _normalize("hello    world") == "hello world"

    def test_collapse_tabs(self):
        assert _normalize("hello\t\tworld") == "hello world"

    def test_collapse_newlines(self):
        assert _normalize("a\n\n\n\nb") == "a\n\nb"

    def test_strip(self):
        assert _normalize("  hello  ") == "hello"


class TestValidateUrl:
    def test_valid_https(self):
        ok, msg = _validate_url("https://example.com")
        assert ok is True
        assert msg == ""

    def test_valid_http(self):
        ok, msg = _validate_url("http://example.com")
        assert ok is True

    def test_invalid_scheme(self):
        ok, msg = _validate_url("ftp://example.com")
        assert ok is False
        assert "http" in msg.lower()

    def test_no_scheme(self):
        ok, msg = _validate_url("example.com")
        assert ok is False

    def test_missing_domain(self):
        ok, msg = _validate_url("https://")
        assert ok is False
        assert "domain" in msg.lower()

    def test_empty(self):
        ok, msg = _validate_url("")
        assert ok is False


class TestWebSearchTool:
    def test_init_default(self):
        tool = WebSearchTool()
        assert tool.name == "web_search"
        assert tool.max_results == 5

    def test_init_custom(self):
        tool = WebSearchTool(api_key="test-key", max_results=3)
        assert tool.api_key == "test-key"
        assert tool.max_results == 3

    def test_properties(self):
        tool = WebSearchTool()
        assert tool.parameters["type"] == "object"
        assert "query" in tool.parameters["properties"]

    @pytest.mark.asyncio
    async def test_no_api_key(self):
        tool = WebSearchTool(api_key="")
        result = await tool.execute("test query")
        assert "not configured" in result.lower()

    @pytest.mark.asyncio
    async def test_search_success(self):
        tool = WebSearchTool(api_key="test-key")
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "web": {
                "results": [
                    {"title": "Result 1", "url": "https://example.com", "description": "Desc 1"},
                    {"title": "Result 2", "url": "https://example.org"},
                ]
            }
        }
        mock_response.raise_for_status = MagicMock()

        with patch("nanobot.agent.tools.web.httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__ = AsyncMock(return_value=MagicMock(
                get=AsyncMock(return_value=mock_response)
            ))
            mock_client.return_value.__aexit__ = AsyncMock()
            result = await tool.execute("test")

        assert "Result 1" in result
        assert "example.com" in result

    @pytest.mark.asyncio
    async def test_search_no_results(self):
        tool = WebSearchTool(api_key="test-key")
        mock_response = MagicMock()
        mock_response.json.return_value = {"web": {"results": []}}
        mock_response.raise_for_status = MagicMock()

        with patch("nanobot.agent.tools.web.httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__ = AsyncMock(return_value=MagicMock(
                get=AsyncMock(return_value=mock_response)
            ))
            mock_client.return_value.__aexit__ = AsyncMock()
            result = await tool.execute("test")

        assert "no results" in result.lower()

    @pytest.mark.asyncio
    async def test_search_error(self):
        tool = WebSearchTool(api_key="test-key")

        with patch("nanobot.agent.tools.web.httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__ = AsyncMock(return_value=MagicMock(
                get=AsyncMock(side_effect=Exception("Connection failed"))
            ))
            mock_client.return_value.__aexit__ = AsyncMock()
            result = await tool.execute("test")

        assert "error" in result.lower()


class TestWebFetchTool:
    def test_init(self):
        tool = WebFetchTool()
        assert tool.name == "web_fetch"
        assert tool.max_chars == 50000

    def test_custom_max_chars(self):
        tool = WebFetchTool(max_chars=1000)
        assert tool.max_chars == 1000

    @pytest.mark.asyncio
    async def test_invalid_url_scheme(self):
        tool = WebFetchTool()
        with patch.dict("sys.modules", {"readability": MagicMock()}):
            result = await tool.execute("ftp://example.com")
        data = json.loads(result)
        assert "error" in data

    @pytest.mark.asyncio
    async def test_invalid_url_no_domain(self):
        tool = WebFetchTool()
        with patch.dict("sys.modules", {"readability": MagicMock()}):
            result = await tool.execute("https://")
        data = json.loads(result)
        assert "error" in data

    @pytest.mark.asyncio
    async def test_fetch_error(self):
        tool = WebFetchTool()

        with patch.dict("sys.modules", {"readability": MagicMock()}), \
             patch("nanobot.agent.tools.web.httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__ = AsyncMock(return_value=MagicMock(
                get=AsyncMock(side_effect=Exception("Timeout"))
            ))
            mock_client.return_value.__aexit__ = AsyncMock()
            result = await tool.execute("https://example.com")

        data = json.loads(result)
        assert "error" in data


class TestConstants:
    def test_user_agent(self):
        assert "Mozilla" in USER_AGENT

    def test_max_redirects(self):
        assert MAX_REDIRECTS == 5
