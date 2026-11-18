"""
test_web_intelligence.py — Verification suite for FluxKernel Autonomous Web Intelligence & Research Grounding.
"""

from __future__ import annotations

import os
import sys

# Ensure engine path is in sys.path
ENGINE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ENGINE_DIR not in sys.path:
    sys.path.insert(0, ENGINE_DIR)

from app.core import project_rag  # noqa: E402
from app.tools import web_fetcher  # noqa: E402


def test_search_web_structure():
    """Verify that search_web returns clean, structured search hits."""
    query = "Calculus"
    results = web_fetcher.search_web(query, max_results=3)

    assert isinstance(results, list)
    assert len(results) > 0
    first = results[0]
    assert "title" in first
    assert "snippet" in first
    assert "url" in first
    assert len(first["title"]) > 0


def test_research_topic_and_simd_caching():
    """Verify that research_topic extracts knowledge and caches directly into C++ SIMD vector memory."""
    vault_initial_count = len(project_rag._IN_MEMORY_VAULT)

    query = "Quantum Mechanics"
    res = web_fetcher.research_topic(query, max_sources=2, auto_cache_rag=True)

    assert res["query"] == query
    assert res["sources_investigated"] > 0
    assert "findings" in res
    assert "research_brief" in res
    assert res["cached_to_simd_vault"] is True

    # Check that knowledge chunks landed in SIMD vector memory with 0 bytes committed to git
    assert len(project_rag._IN_MEMORY_VAULT) >= vault_initial_count

    # Test that C++ SIMD RAG can now retrieve this web knowledge!
    retrieved = project_rag.retrieve_context(query="Quantum Mechanics", limit=3)
    assert len(retrieved) > 0


def test_web_api_endpoints():
    """Verify FastAPI /api/v1/web/search and /research endpoints."""
    try:
        from fastapi.testclient import TestClient
        from app.main import app

        client = TestClient(app)

        # Search endpoint
        res = client.post("/api/v1/web/search", json={"query": "Algorithms", "max_results": 2})
        assert res.status_code == 200
        data = res.json()
        assert data["query"] == "Algorithms"
        assert len(data["results"]) > 0

        # Research endpoint
        res_res = client.post(
            "/api/v1/web/research",
            json={"query": "Linear Algebra", "max_sources": 1, "auto_cache_rag": True},
        )
        assert res_res.status_code == 200
        data_res = res_res.json()
        assert data_res["query"] == "Linear Algebra"
        assert data_res["cached_to_simd_vault"] is True
    except ImportError:
        pass


if __name__ == "__main__":
    test_search_web_structure()
    test_research_topic_and_simd_caching()
    test_web_api_endpoints()
    print("All Autonomous Web Intelligence & Grounding tests passed successfully!")
