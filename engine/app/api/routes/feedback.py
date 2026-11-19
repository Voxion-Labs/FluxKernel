"""
FastAPI Routes for Episodic Feedback & Sovereign Rule Learning.

Enables recording user corrections, diff rejections, and custom behavioral directives
that are stored and dynamically injected into Agentic Loops and Personas.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.tools.feedback_learner import (
    add_learned_rule,
    build_rules_prompt_block,
    clear_all_rules,
    delete_learned_rule,
    get_matching_rules,
    list_learned_rules,
    record_diff_rejection,
)

router = APIRouter(prefix="/feedback", tags=["feedback"])


class RecordFeedbackRequest(BaseModel):
    directive: str = Field(..., min_length=2, description="Rule directive or user preference")
    category: str | None = Field(
        default=None,
        description="forbidden_pattern, coding_style, architecture, domain_guideline, workflow",
    )
    domain: str | None = Field(default=None, description="tech, science, finance, general")
    trigger_keywords: list[str] | None = Field(
        default=None, description="Optional keyword triggers"
    )
    source: str = Field(
        default="user_explicit", description="user_explicit, correction_feedback, diff_rejection"
    )


class DiffRejectionRequest(BaseModel):
    batch_id: str = Field(..., description="ID of rejected diff batch")
    reason: str | None = Field(
        default=None, description="User explanation of why diff was rejected"
    )
    files_affected: list[str] | None = Field(default=None, description="Files affected in batch")


class EvaluatePromptRequest(BaseModel):
    prompt: str = Field(..., min_length=1, description="Prompt to evaluate against learned rules")
    domain: str | None = Field(default=None, description="Optional domain filter")


class LearnedRuleOut(BaseModel):
    rule_id: str
    directive: str
    category: str
    domain: str
    trigger_keywords: list[str]
    confidence: float
    source: str
    hit_count: int
    created_at: str


class EvaluatePromptResponse(BaseModel):
    prompt: str
    domain: str | None
    matched_rules_count: int
    matched_rules: list[LearnedRuleOut]
    rules_prompt_block: str


@router.post("/record", response_model=LearnedRuleOut)
def record_feedback(req: RecordFeedbackRequest):
    """Records a new learned rule or behavioral preference from user feedback."""
    try:
        rule = add_learned_rule(
            directive=req.directive,
            category=req.category,
            domain=req.domain,
            trigger_keywords=req.trigger_keywords,
            source=req.source,
        )
        return rule.to_dict()
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/reject-diff", response_model=LearnedRuleOut)
def record_rejected_diff(req: DiffRejectionRequest):
    """Learns from an agentic diff rejection to avoid repeating rejected patterns."""
    rule = record_diff_rejection(
        batch_id=req.batch_id,
        reason=req.reason,
        files_affected=req.files_affected,
    )
    return rule.to_dict()


@router.get("/rules", response_model=list[LearnedRuleOut])
def get_all_rules(category: str | None = None, domain: str | None = None):
    """Lists all active sovereign learned rules."""
    rules = list_learned_rules(category=category, domain=domain)
    return [r.to_dict() for r in rules]


@router.delete("/rules/{rule_id}")
def delete_rule(rule_id: str):
    """Deletes a learned rule by ID."""
    deleted = delete_learned_rule(rule_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Rule '{rule_id}' not found.")
    return {"status": "deleted", "rule_id": rule_id}


@router.post("/evaluate", response_model=EvaluatePromptResponse)
def evaluate_prompt_against_rules(req: EvaluatePromptRequest):
    """Evaluates an incoming prompt against learned rules and returns the prompt injection block."""
    matched = get_matching_rules(req.prompt, domain=req.domain)
    block = build_rules_prompt_block(req.prompt, domain=req.domain)

    return EvaluatePromptResponse(
        prompt=req.prompt,
        domain=req.domain,
        matched_rules_count=len(matched),
        matched_rules=[m.to_dict() for m in matched],
        rules_prompt_block=block,
    )


@router.post("/clear")
def clear_rules() -> dict[str, Any]:
    """Clears all active learned rules from memory and disk."""
    clear_all_rules()
    return {"status": "cleared", "message": "All learned rules cleared successfully."}
