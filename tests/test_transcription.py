"""
Unit tests for providers/transcription.py.

Stage: 05 - TEST
Sprint: Sprint 02
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from pathlib import Path

from nanobot.providers.transcription import GroqTranscriptionProvider


class TestGroqTranscriptionInit:
    def test_explicit_key(self):
        p = GroqTranscriptionProvider(api_key="test-key")
        assert p.api_key == "test-key"
        assert "groq.com" in p.api_url

    def test_env_key(self):
        with patch.dict("os.environ", {"GROQ_API_KEY": "env-key"}):
            p = GroqTranscriptionProvider()
            assert p.api_key == "env-key"

    def test_no_key(self):
        with patch.dict("os.environ", {}, clear=True):
            p = GroqTranscriptionProvider()
            assert p.api_key is None


class TestGroqTranscribe:
    @pytest.mark.asyncio
    async def test_no_api_key(self):
        p = GroqTranscriptionProvider(api_key=None)
        result = await p.transcribe("/fake/audio.ogg")
        assert result == ""

    @pytest.mark.asyncio
    async def test_file_not_found(self, tmp_path):
        p = GroqTranscriptionProvider(api_key="test-key")
        result = await p.transcribe(tmp_path / "nonexistent.ogg")
        assert result == ""

    @pytest.mark.asyncio
    async def test_transcribe_success(self, tmp_path):
        audio_file = tmp_path / "audio.ogg"
        audio_file.write_bytes(b"fake audio data")

        p = GroqTranscriptionProvider(api_key="test-key")

        mock_response = MagicMock()
        mock_response.json.return_value = {"text": "Hello world"}
        mock_response.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch("nanobot.providers.transcription.httpx.AsyncClient", return_value=mock_client):
            result = await p.transcribe(audio_file)
        assert result == "Hello world"

    @pytest.mark.asyncio
    async def test_transcribe_error(self, tmp_path):
        audio_file = tmp_path / "audio.ogg"
        audio_file.write_bytes(b"fake audio data")

        p = GroqTranscriptionProvider(api_key="test-key")

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(side_effect=Exception("API error"))
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch("nanobot.providers.transcription.httpx.AsyncClient", return_value=mock_client):
            result = await p.transcribe(audio_file)
        assert result == ""

    @pytest.mark.asyncio
    async def test_transcribe_empty_text(self, tmp_path):
        audio_file = tmp_path / "audio.ogg"
        audio_file.write_bytes(b"fake audio data")

        p = GroqTranscriptionProvider(api_key="test-key")

        mock_response = MagicMock()
        mock_response.json.return_value = {}
        mock_response.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch("nanobot.providers.transcription.httpx.AsyncClient", return_value=mock_client):
            result = await p.transcribe(audio_file)
        assert result == ""
