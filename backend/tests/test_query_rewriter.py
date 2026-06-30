"""
WHY THIS WAS CHOSEN:
This module contains unit tests for the Query Rewriter subsystem. It tests
both the MockQueryRewriter's custom mapping and fallback behavior, and verifies
the factory method (create_rewriter_from_settings) correctly respects settings.
By testing these interfaces, we ensure that adding query rewriting to the 
retrieval pipeline doesn't break query flows and behaves predictably under mock config.
"""

import pytest
from src.config import settings
from src.models.rewrite_result import RewriteResult
from src.retrieval.rewriters.base import BaseQueryRewriter
from src.retrieval.rewriters.mock import MockQueryRewriter
from src.retrieval.rewriters.factory import create_rewriter_from_settings
from src.retrieval.rewriters.gemini import GeminiQueryRewriter

@pytest.mark.anyio
async def test_mock_rewriter_custom_mapping():
    # Setup custom query mapping
    rewrites = {
        "explain auth": RewriteResult(
            rewritten_query="Explain the authentication implementation, JWT flow, middleware, login, authorization, and token validation.",
            rewritten=True,
            explanation="Expanded ambiguous retrieval terms for auth."
        ),
        "AKS deployment": RewriteResult(
            rewritten_query="Azure Kubernetes Service deployment architecture, Terraform configuration, Kubernetes manifests, Helm charts, networking and deployment pipeline.",
            rewritten=True,
            explanation="Expanded AKS terms."
        )
    }
    
    rewriter = MockQueryRewriter(rewrites=rewrites)
    
    # Check custom mappings
    res1 = await rewriter.rewrite("explain auth")
    assert res1.rewritten is True
    assert "JWT" in res1.rewritten_query
    
    res2 = await rewriter.rewrite("AKS deployment")
    assert res2.rewritten is True
    assert "Terraform" in res2.rewritten_query

@pytest.mark.anyio
async def test_mock_rewriter_fallback():
    rewriter = MockQueryRewriter(rewrites={})
    
    # Query not in mapping should pass through unchanged
    original = "How does SecretProviderClass retrieve secrets?"
    res = await rewriter.rewrite(original)
    assert res.rewritten is False
    assert res.rewritten_query == original
    assert "passed through" in res.explanation

def test_rewriter_factory(monkeypatch):
    # Test factory returns MockQueryRewriter
    monkeypatch.setattr(settings, "REWRITER_PROVIDER", "mock")
    rewriter = create_rewriter_from_settings()
    assert isinstance(rewriter, MockQueryRewriter)
    
    # Test factory returns GeminiQueryRewriter
    monkeypatch.setattr(settings, "REWRITER_PROVIDER", "gemini")
    rewriter_gemini = create_rewriter_from_settings()
    assert isinstance(rewriter_gemini, GeminiQueryRewriter)
    assert rewriter_gemini.model_name == settings.MODEL_REWRITER

@pytest.mark.anyio
async def test_gemini_rewriter_empty_query():
    rewriter = GeminiQueryRewriter()
    res_empty = await rewriter.rewrite("")
    assert res_empty.rewritten is False
    assert res_empty.rewritten_query == ""
    
    res_space = await rewriter.rewrite("   ")
    assert res_space.rewritten is False
    assert res_space.rewritten_query == ""
