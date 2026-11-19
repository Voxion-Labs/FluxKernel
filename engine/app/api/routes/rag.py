from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.native_bridge import _IS_NATIVE_LOADED
from app.core.project_rag import (
    RetrievedChunk,
    retrieve_context,
    scan_and_index_workspace,
)
from app.database.connection import get_db
from app.database.models import ProjectDocumentChunk, ProjectPin

router = APIRouter(prefix="/rag", tags=["rag"])


class RAGSearchRequest(BaseModel):
    query: str = Field(..., min_length=1, description="Semantic search query")
    limit: int = Field(default=5, ge=1, le=50)
    domain: str | None = Field(
        default=None, description="Optional domain filter (tech, science, finance, general)"
    )


class RAGChunkOut(BaseModel):
    path: str
    content: str
    score: float
    domain: str
    chunk_index: int


class RAGSearchResponse(BaseModel):
    query: str
    results_count: int
    simd_accelerated: bool
    results: list[RAGChunkOut]


class RAGStatusResponse(BaseModel):
    total_pinned_files: int
    total_chunks: int
    simd_accelerated: bool
    domains: dict[str, int]


@router.get("/status", response_model=RAGStatusResponse)
def get_rag_status(db: Session = Depends(get_db)):
    """Return status and telemetry of the C++ SIMD Semantic Memory Vault."""
    try:
        total_pins = db.query(ProjectPin).count()
        chunks = db.query(ProjectDocumentChunk).all()

        domains: dict[str, int] = {}
        for chunk in chunks:
            from app.core.project_rag import infer_domain

            dom = infer_domain(chunk.path)
            domains[dom] = domains.get(dom, 0) + 1

        return RAGStatusResponse(
            total_pinned_files=total_pins,
            total_chunks=len(chunks),
            simd_accelerated=_IS_NATIVE_LOADED,
            domains=domains,
        )
    except Exception:
        # Fallback to in-memory vault stats if database tables are uninitialized
        from app.core.project_rag import get_vault_stats

        st = get_vault_stats()
        return RAGStatusResponse(
            total_pinned_files=st.get("workspace_chunks", 0),
            total_chunks=st.get("total_chunks", 0),
            simd_accelerated=_IS_NATIVE_LOADED,
            domains=st.get("domains", {}),
        )


@router.post("/index")
def index_workspace(db: Session = Depends(get_db)) -> dict[str, Any]:
    """Scan and index all eligible multi-domain workspace files into SIMD vector memory."""
    stats = scan_and_index_workspace(db)
    return stats


@router.post("/search", response_model=RAGSearchResponse)
def search_semantic_memory(
    payload: RAGSearchRequest,
    db: Session = Depends(get_db),
):
    """Query semantic vector memory using C++20 SIMD AVX2 accelerated dot product."""
    chunks: list[RetrievedChunk] = retrieve_context(
        db,
        query=payload.query,
        limit=payload.limit,
        domain_filter=payload.domain,
    )

    out_chunks = [
        RAGChunkOut(
            path=c.path,
            content=c.content,
            score=c.score,
            domain=c.domain,
            chunk_index=c.chunk_index,
        )
        for c in chunks
    ]

    return RAGSearchResponse(
        query=payload.query,
        results_count=len(out_chunks),
        simd_accelerated=_IS_NATIVE_LOADED,
        results=out_chunks,
    )
