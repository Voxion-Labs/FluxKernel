from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.core.flux_driver import (
    FluxDriver,
    get_active_engine,
    list_available_engines,
    set_active_engine,
)

router = APIRouter(prefix="/driver", tags=["driver"])


class SelectEngineRequest(BaseModel):
    engine: str = Field(
        ..., description="Engine ID: flux-native, gemini, anthropic, deepseek, ollama"
    )


class GenerateRequest(BaseModel):
    prompt: str = Field(..., description="Input prompt or directive")
    system_prompt: str = Field("", description="System instructions")
    persona: str = Field("coder", description="Persona: coder, architect, auditor, refactorer")
    domain: str = Field("general", description="Domain: tech, science, finance, general")
    engine_override: str | None = Field(
        None, description="Optional override engine for this request"
    )


@router.get("/status")
def get_driver_status() -> dict[str, Any]:
    """Returns active driver configuration and available engine matrix."""
    return {
        "active_engine": get_active_engine(),
        "available_engines": list_available_engines(),
    }


@router.post("/select")
def select_engine(req: SelectEngineRequest) -> dict[str, Any]:
    """Switches the active inference engine across the sovereign system."""
    try:
        new_engine = set_active_engine(req.engine)
        return {
            "status": "updated",
            "active_engine": new_engine,
            "message": f"Active AI driver switched to {new_engine}",
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/generate")
async def generate_completion(req: GenerateRequest) -> dict[str, Any]:
    """Executes multi-domain inference through the selected driver."""
    res = await FluxDriver.generate(
        prompt=req.prompt,
        system_prompt=req.system_prompt,
        persona=req.persona,
        domain=req.domain,
        engine_override=req.engine_override,
    )
    return {
        "content": res.content,
        "engine": res.engine,
        "domain": res.domain,
        "tokens_estimated": res.tokens_estimated,
        "latency_ms": res.latency_ms,
        "is_fallback": res.is_fallback,
    }
