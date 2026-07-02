import httpx
import time
import json
import asyncio
from unittest.mock import patch, AsyncMock, MagicMock
from httpx import AsyncClient, ASGITransport
from src.main import app
from src.api.routes.chat import chat_limiter
from src.config import settings
from src.retrieval.hybrid_retriever import RetrievalResult
from src.models.chunk import Chunk

# Setup local mock chunk for the mock retriever to return
mock_chunk = Chunk(
    chunk_id="chunk-1",
    parent_document_id="doc-1",
    content_hash="hash-1",
    content="TalentForge uses React, Python, and Neon PostgreSQL.",
    project="talentforge",
    layer="design",
    source_type="markdown",
    source_file="architecture.md",
    chunk_index=0,
    token_count=10,
    char_count=50
)
mock_retrieval_res = RetrievalResult(chunk=mock_chunk, score=0.99)


async def run_tests():
    print("=" * 80)
    print("RUNNING FEATURE #17 VALIDATION TESTS USING ASGI TRANSPORT")
    print("=" * 80)
    
    # 0. Save original settings
    orig_requests = settings.RATE_LIMIT_REQUESTS
    orig_window = settings.RATE_LIMIT_WINDOW_SECONDS

    # Set limits to 10 requests per 5 seconds for fast test execution
    settings.RATE_LIMIT_REQUESTS = 10
    settings.RATE_LIMIT_WINDOW_SECONDS = 5
    chat_limiter.windows.clear()
    
    # Patch all downstream components to avoid external LLM/Gemini dependencies
    with patch("src.services.chat_orchestrator.detect_project", return_value="talentforge") as mock_detect_project, \
         patch("src.services.chat_orchestrator.retrieve", new_callable=AsyncMock, return_value=[mock_retrieval_res]) as mock_retrieve, \
         patch("src.services.chat_orchestrator.create_generator_from_settings") as mock_create_generator:
         
        mock_gen = MagicMock()
        async def mock_stream_iter(prompt, system_instruction):
            yield "TalentForge is built using React, Python, and Neon PostgreSQL."
        mock_gen.stream.side_effect = mock_stream_iter
        mock_create_generator.return_value = mock_gen

        # Test 1: Send 3 normal requests
        print("\n--- Test 1: Normal Usage (3 requests) ---")
        transport = ASGITransport(app=app, client=("1.1.1.1", 12345))
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            for i in range(1, 4):
                resp = await client.post("/chat", json={"message": "What is TalentForge?"})
                print(f"Request {i}: HTTP {resp.status_code}")
                if resp.status_code == 200:
                    lines = [l.strip() for l in resp.text.split("\n") if l.strip()]
                    if lines:
                        print(f"  Last line: {lines[-1]}")
                        print(f"  Second to last: {lines[-2] if len(lines) > 1 else ''}")
                        
        # Test 2: Trigger Rate Limit (Send 8 more requests to reach 11)
        print("\n--- Test 2: Trigger Rate Limit (11 requests total) ---")
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            # We already sent 3. Let's send 7 more (successful) and then the 11th (blocked)
            for i in range(4, 11):
                resp = await client.post("/chat", json={"message": "What is TalentForge?"})
                print(f"Request {i}: HTTP {resp.status_code}")
                
            # The 11th request:
            resp_blocked = await client.post("/chat", json={"message": "What is TalentForge?"})
            print(f"Request 11: HTTP {resp_blocked.status_code}")
            print(f"  Headers: {dict(resp_blocked.headers)}")
            print(f"  Body: {resp_blocked.text}")
            
        # Test 3: Window Reset
        print("\n--- Test 3: Window Reset ---")
        retry_after = int(resp_blocked.headers.get("Retry-After", 5))
        print(f"Waiting for {retry_after} seconds until window resets...")
        await asyncio.sleep(retry_after + 1)
        
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp_reset = await client.post("/chat", json={"message": "What is TalentForge?"})
            print(f"Request after reset: HTTP {resp_reset.status_code}")
            
        # Test 4: Independent Clients
        print("\n--- Test 4: Independent Clients (Client A 429, Client B 200) ---")
        chat_limiter.windows.clear()
        settings.RATE_LIMIT_REQUESTS = 1  # limit to 1 request
        
        transport_a = ASGITransport(app=app, client=("10.0.0.1", 12345))
        transport_b = ASGITransport(app=app, client=("20.0.0.2", 12345))
        
        async with AsyncClient(transport=transport_a, base_url="http://test") as client_a, \
                   AsyncClient(transport=transport_b, base_url="http://test") as client_b:
            
            # Client A request 1 (Success)
            resp_a1 = await client_a.post("/chat", json={"message": "What is TalentForge?"})
            print(f"Client A (10.0.0.1) Request 1: HTTP {resp_a1.status_code}")
            
            # Client A request 2 (Blocked 429)
            resp_a2 = await client_a.post("/chat", json={"message": "What is TalentForge?"})
            print(f"Client A (10.0.0.1) Request 2: HTTP {resp_a2.status_code}")
            
            # Client B request 1 (Success 200)
            resp_b1 = await client_b.post("/chat", json={"message": "What is TalentForge?"})
            print(f"Client B (20.0.0.2) Request 1: HTTP {resp_b1.status_code}")

        # Execution Order Check: validation vs dependency
        print("\n--- Execution Order Check: Invalid Payload (body: {}) on Rate-Limited Client ---")
        # Client A is already rate limited (sent 2 requests, limit is 1)
        async with AsyncClient(transport=transport_a, base_url="http://test") as client_a:
            # Send empty/invalid payload
            resp_invalid = await client_a.post("/chat", json={})
            print(f"Client A sends invalid payload: HTTP {resp_invalid.status_code}")
            print(f"  Response Body: {resp_invalid.text}")

    # Restore original settings
    settings.RATE_LIMIT_REQUESTS = orig_requests
    settings.RATE_LIMIT_WINDOW_SECONDS = orig_window


if __name__ == "__main__":
    asyncio.run(run_tests())
