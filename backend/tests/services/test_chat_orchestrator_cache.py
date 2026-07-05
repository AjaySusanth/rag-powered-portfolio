from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.api.schemas.chat import StreamCitationsEvent, StreamTokenEvent
from src.cache.base import BaseCache
from src.services.chat_orchestrator import ChatOrchestrator


class MockCache(BaseCache):
    def __init__(self, should_fail=False):
        self.data = {}
        self.should_fail = should_fail

    async def get_chat_response(self, query):
        if self.should_fail:
            return None # degrade gracefully
        return self.data.get(query)

    async def set_chat_response(self, query, answer, citations):
        if self.should_fail:
            return
        self.data[query] = {
            "answer": answer,
            "citations": [c.model_dump() for c in citations]
        }

    async def get_embedding(self, text: str):
        if self.should_fail:
            return None
        return self.data.get(f"embed:{text}")

    async def set_embedding(self, text: str, embedding: list):
        if self.should_fail:
            return
        self.data[f"embed:{text}"] = embedding


@pytest.fixture
def mock_pipeline():
    with patch("src.services.chat_orchestrator.detect_project") as mock_detect, \
         patch("src.services.chat_orchestrator.retrieve") as mock_retrieve, \
         patch("src.services.chat_orchestrator.PromptBuilder.build") as mock_build, \
         patch("src.services.chat_orchestrator.create_generator_from_settings") as mock_create_generator:

        mock_detect.return_value = None
        mock_retrieve.return_value = []

        mock_build_result = MagicMock()
        mock_build_result.prompt = "test prompt"
        mock_build_result.chunks_used = []
        mock_build.return_value = mock_build_result

        mock_generator = AsyncMock()
        async def mock_stream(*args, **kwargs):
            yield "Hello"
            yield " World"
        mock_generator.stream = mock_stream
        mock_create_generator.return_value = mock_generator

        yield {
            "detect": mock_detect,
            "retrieve": mock_retrieve,
            "build": mock_build,
            "generator": mock_create_generator
        }


@pytest.mark.anyio
async def test_chat_orchestrator_cache_hit():
    orchestrator = ChatOrchestrator()
    mock_cache = MockCache()
    mock_cache.data["test query"] = {
        "answer": "Cached answer",
        "citations": [{"file": "test.md", "layer": "layer-1", "project": "global"}]
    }
    orchestrator.cache = mock_cache

    events = [e async for e in orchestrator.stream_chat("test query")]

    # 1 token event (with full cached answer), 1 citation event
    assert len(events) == 2
    assert isinstance(events[0], StreamTokenEvent)
    assert events[0].token == "Cached answer"
    assert isinstance(events[1], StreamCitationsEvent)
    assert len(events[1].citations) == 1


@pytest.mark.anyio
async def test_chat_orchestrator_cache_miss_stores_result(mock_pipeline):
    orchestrator = ChatOrchestrator()
    mock_cache = MockCache()
    orchestrator.cache = mock_cache

    events = [e async for e in orchestrator.stream_chat("new query")]

    # "Hello", " World", citations
    assert len(events) == 3
    assert events[0].token == "Hello"
    assert events[1].token == " World"
    assert isinstance(events[2], StreamCitationsEvent)

    # Verify pipeline was executed
    mock_pipeline["retrieve"].assert_called_once()

    # Verify cache was populated
    cached = mock_cache.data.get("new query")
    assert cached is not None
    assert cached["answer"] == "Hello World"


@pytest.mark.anyio
async def test_chat_orchestrator_redis_failure_degrades_gracefully(mock_pipeline):
    # This verifies that Redis unavailability does not affect API functionality
    orchestrator = ChatOrchestrator()
    mock_cache = MockCache(should_fail=True)
    orchestrator.cache = mock_cache

    events = [e async for e in orchestrator.stream_chat("another query")]

    # Verify pipeline runs successfully despite cache failure
    assert len(events) == 3
    mock_pipeline["retrieve"].assert_called_once()
