from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Query
from pydantic import BaseModel, Field

from app.core.workspace_search import search_workspace

router = APIRouter(prefix="/workspace", tags=["search"])


class SearchRequest(BaseModel):
    query: str = Field(..., description="Search term, symbol name, or phrase")
    domain: str = Field("all", description="Domain filter: all, tech, science, finance, general")
    limit: int = Field(25, ge=1, le=100, description="Maximum results to return")


@router.get("/search")
async def get_workspace_search(
    q: str = Query("", description="Query string to search across workspace"),
    domain: str = Query("all", description="Domain filter: all, tech, science, finance, general"),
    limit: int = Query(25, ge=1, le=100),
) -> dict[str, Any]:
    """Fast workspace search across files, symbols, and contents with domain tagging."""
    return search_workspace(query=q, domain=domain, limit=limit)


@router.post("/search")
async def post_workspace_search(payload: SearchRequest) -> dict[str, Any]:
    """JSON-based search endpoint for IDE/UI integrations."""
    return search_workspace(
        query=payload.query,
        domain=payload.domain,
        limit=payload.limit,
    )
