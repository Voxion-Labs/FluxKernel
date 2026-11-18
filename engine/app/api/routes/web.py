"""
web.py — Controlled external web access routes for FluxKernel.

All requests are validated by web_fetcher.py (https-only, 100MB cap, etc.).

Endpoints:
  POST /api/v1/web/fetch     — Fetch or scrape a URL
  POST /api/v1/web/download  — Download a binary file into workspace/
  POST /api/v1/web/api       — Ping an external JSON API
"""

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.tools.web_fetcher import (
    download_file,
    fetch_api,
    fetch_url,
    research_topic,
    scrape_page,
    search_web,
)

router = APIRouter(prefix="/web", tags=["web"])


# ── Request Models ─────────────────────────────────────────────────────────────


class SearchRequest(BaseModel):
    query: str
    max_results: int = 5


class ResearchRequest(BaseModel):
    query: str
    max_sources: int = 3
    auto_cache_rag: bool = True


class FetchRequest(BaseModel):
    url: str
    css_selector: str | None = None
    save_as: str | None = None
    raw: bool = False  # If True, return raw HTML; if False, return clean text via scrape


class DownloadRequest(BaseModel):
    url: str
    filename: str


class ApiRequest(BaseModel):
    url: str
    headers: dict[str, str] | None = None
    payload: dict[str, Any] | None = None
    save_as: str | None = None


# ── Routes ────────────────────────────────────────────────────────────────────


@router.post("/fetch")
async def web_fetch(request: FetchRequest) -> dict:
    """
    Fetch or scrape an external https URL.
    Returns raw text or cleaned page content depending on the `raw` flag.
    """
    try:
        if request.raw:
            return fetch_url(url=request.url, save_as=request.save_as)
        else:
            return scrape_page(
                url=request.url,
                css_selector=request.css_selector,
                save_as=request.save_as,
            )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Web fetch failed: {e!s}")


@router.post("/download")
async def web_download(request: DownloadRequest) -> dict:
    """
    Stream-download a binary file from an https URL into workspace/.
    Returns workspace path and file size.
    """
    try:
        return download_file(url=request.url, filename=request.filename)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Download failed: {e!s}")


@router.post("/api")
async def web_api(request: ApiRequest) -> dict:
    """
    Ping an external JSON API endpoint (GET or POST).
    """
    try:
        return fetch_api(
            url=request.url,
            headers=request.headers,
            payload=request.payload,
            save_as=request.save_as,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"API request failed: {e!s}")


@router.post("/search")
async def web_search(request: SearchRequest) -> dict:
    """
    Perform zero-key autonomous live web search for factual and technical grounding.
    """
    try:
        results = search_web(query=request.query, max_results=request.max_results)
        return {
            "query": request.query,
            "count": len(results),
            "results": results,
        }
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Web search failed: {e!s}")


@router.post("/research")
async def web_research(request: ResearchRequest) -> dict:
    """
    Autonomously research a topic across live web intelligence and cache directly
    into FluxKernel's C++ SIMD Vector Memory Vault with zero Git LFS overhead.
    """
    try:
        return research_topic(
            query=request.query,
            max_sources=request.max_sources,
            auto_cache_rag=request.auto_cache_rag,
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Research synthesis failed: {e!s}")
