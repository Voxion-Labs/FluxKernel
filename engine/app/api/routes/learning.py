"""
FastAPI Routes for Cross-AI Learning Adapter & Transcript Ingestion.

Exposes endpoints to ingest conversation exports, reasoning trees, and code blocks
from external AI assistants (ChatGPT, Claude, Cursor, Markdown transcripts)
into Flux's C++ SIMD Vector Memory Vault with zero Git LFS overhead.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.tools.chat_ingestor import (
    auto_detect_and_parse,
    clear_learned_sessions,
    get_learning_status,
    ingest_and_index_sessions,
)

router = APIRouter(prefix="/learning", tags=["learning"])


class IngestChatRequest(BaseModel):
    raw_content: str = Field(
        ..., min_length=1, description="Raw JSON or Markdown transcript export"
    )
    source: str = Field(
        default="auto", description="Source platform: auto, chatgpt, claude, cursor, markdown"
    )
    session_title: str | None = Field(default=None, description="Optional title override")
    auto_cache_rag: bool = Field(
        default=True, description="Whether to auto-index into C++ SIMD Vector Vault"
    )


class IngestSessionSummary(BaseModel):
    session_id: str
    title: str
    source: str
    turns_count: int
    code_snippets_count: int
    domains: dict[str, int]
    chunks_indexed: int
    created_at: str


class IngestChatResponse(BaseModel):
    status: str
    sessions_processed: int
    total_turns_memorized: int
    total_code_snippets: int
    chunks_indexed: int
    source_breakdown: dict[str, int]
    domain_breakdown: dict[str, int]
    sessions: list[IngestSessionSummary]


class LearningStatusResponse(BaseModel):
    total_sessions: int
    total_turns_memorized: int
    total_code_snippets: int
    total_chunks_indexed: int
    sources: dict[str, int]
    domains: dict[str, int]
    recent_sessions: list[dict[str, Any]]


@router.post("/ingest", response_model=IngestChatResponse)
def ingest_chat_transcripts(req: IngestChatRequest):
    """
    Ingests and parses conversation transcripts from ChatGPT, Claude, Cursor, or Markdown,
    synthesizes high-signal knowledge capsules, and indexes them into the C++ SIMD memory vault.
    """
    try:
        sessions = auto_detect_and_parse(
            raw_content=req.raw_content,
            source=req.source,
            session_title=req.session_title,
        )
        if not sessions:
            raise HTTPException(
                status_code=400,
                detail="No conversation turns could be extracted from the provided transcript payload.",
            )

        result = ingest_and_index_sessions(sessions, auto_cache_rag=req.auto_cache_rag)
        return result
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=500, detail=f"Cross-AI learning ingestion failed: {exc}"
        ) from exc


@router.get("/status", response_model=LearningStatusResponse)
def get_ai_learning_status():
    """Returns real-time diagnostics of learned AI conversation capsules."""
    return get_learning_status()


@router.post("/clear")
def clear_ai_learning():
    """Clears all ephemeral ingested AI sessions from the registry."""
    clear_learned_sessions()
    return {"status": "cleared", "message": "Cross-AI learning registry cleared successfully."}
