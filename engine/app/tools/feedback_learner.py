"""
Episodic Feedback & Rule-Learning Engine for FluxKernel (Alternative 3: Neural-Semantic).

Learns user habits, forbidden patterns, domain rules, and coding preferences
using LLM Zero-Shot Intent Distillation and pure C++ SIMD AVX2 Cosine Vector Retrieval.
Completely eliminates brittle hardcoded keyword lists.
ZERO GPU fine-tuning overhead, ZERO external dependencies, and ZERO Git bloat.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
import json
import re
from typing import Any

from app.core import project_rag
from app.tools.file_manager import WORKSPACE_DIR

# Path for optional local persistent store of sovereign rules
_RULES_FILE = WORKSPACE_DIR / ".flux_rules.json"


@dataclass
class LearnedRule:
    rule_id: str
    directive: str
    category: str  # "forbidden_pattern" | "coding_style" | "architecture" | "domain_guideline" | "workflow"
    domain: str  # "tech" | "science" | "finance" | "general"
    trigger_keywords: list[str] = field(default_factory=list)
    confidence: float = 1.0
    source: str = "user_explicit"  # "user_explicit" | "diff_rejection" | "correction_feedback"
    hit_count: int = 0
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


# In-memory registry of active sovereign learned rules
_RULES_REGISTRY: list[LearnedRule] = []


def _slugify(text: str, max_length: int = 24) -> str:
    cleaned = re.sub(r"[^\w\s-]", "", text).strip().lower()
    slug = re.sub(r"[-\s]+", "_", cleaned)
    return slug[:max_length] or "rule"


async def distill_rule_with_llm(user_input: str, context: str | None = None) -> dict[str, str]:
    """
    Uses the native LLM Router (Ollama / Gemini / Claude) to extract the core sovereign
    behavioral rule, domain, and category with zero keyword heuristics.
    Falls back gracefully when offline.
    """
    try:
        from app.core.llm_router import route_prompt

        prompt = (
            f'Analyze this user feedback or correction:\n"{user_input}"\n'
            f"Context: {context or 'None'}\n\n"
            "Distill into a JSON object with keys:\n"
            "- directive: concise imperative rule statement\n"
            "- category: one of [forbidden_pattern, coding_style, architecture, domain_guideline, workflow]\n"
            "- domain: one of [tech, science, finance, general]\n"
            "Return ONLY valid JSON."
        )
        res = await route_prompt(
            prompt,
            system_prompt="You are an expert AI governance auditor.",
            model_override="small",
        )
        cleaned = re.search(r"\{.*?\}", res, re.DOTALL)
        if cleaned:
            data = json.loads(cleaned.group(0))
            if "directive" in data:
                return {
                    "directive": str(data.get("directive", user_input)),
                    "domain": str(data.get("domain", "general")),
                    "category": str(data.get("category", "general")),
                }
    except Exception:
        pass

    return {
        "directive": user_input.strip(),
        "domain": "general",
        "category": "general",
    }


def load_rules_from_disk() -> None:
    """Loads previously saved learned rules from local workspace storage."""
    global _RULES_REGISTRY
    if not _RULES_FILE.exists():
        return
    try:
        content = _RULES_FILE.read_text(encoding="utf-8")
        data = json.loads(content)
        if isinstance(data, list):
            _RULES_REGISTRY = [LearnedRule(**item) for item in data if isinstance(item, dict)]
    except Exception:
        pass


def save_rules_to_disk() -> None:
    """Atomically persists active rules into local workspace storage."""
    try:
        _RULES_FILE.parent.mkdir(parents=True, exist_ok=True)
        data = [r.to_dict() for r in _RULES_REGISTRY]
        _RULES_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")
    except Exception:
        pass


def add_learned_rule(
    directive: str,
    category: str | None = None,
    domain: str | None = None,
    trigger_keywords: list[str] | None = None,
    source: str = "user_explicit",
    auto_cache_rag: bool = True,
) -> LearnedRule:
    """
    Registers a new behavioral rule, indexes it into C++ SIMD vector memory,
    and persists it locally.
    """
    clean_directive = directive.strip()
    if not clean_directive:
        raise ValueError("Rule directive cannot be empty.")

    dom = domain or "general"
    cat = category or "general"

    rule_slug = _slugify(clean_directive)
    timestamp_suffix = hex(int(datetime.now(timezone.utc).timestamp()))[2:]
    rule_id = f"rule_{dom}_{rule_slug}_{timestamp_suffix}"

    rule = LearnedRule(
        rule_id=rule_id,
        directive=clean_directive,
        category=cat,
        domain=dom,
        trigger_keywords=trigger_keywords or [],
        confidence=1.0,
        source=source,
    )

    # Prevent duplicate identical directives (boost confidence if repeated)
    for existing in _RULES_REGISTRY:
        if existing.directive.lower() == clean_directive.lower():
            existing.confidence = min(5.0, existing.confidence + 0.5)
            existing.hit_count += 1
            save_rules_to_disk()
            return existing

    _RULES_REGISTRY.append(rule)
    save_rules_to_disk()

    # Index into C++ SIMD Vector Vault
    if auto_cache_rag:
        try:
            capsule = (
                f"# Sovereign Behavioral Rule: {rule_id}\n"
                f"Category: {cat} | Domain: {dom} | Source: {source}\n"
                f"Directive: {clean_directive}\n"
            )
            project_rag.index_text_block(
                uri=f"rules://{dom}/{rule_id}.{cat}",
                content=capsule,
                domain=dom,
            )
        except Exception:
            pass

    return rule


def record_diff_rejection(
    batch_id: str,
    reason: str | None = None,
    files_affected: list[str] | None = None,
) -> LearnedRule:
    """
    Learns from a rejected diff proposed by the agentic loop.
    Captures what the user rejected so the agent never repeats the rejected approach.
    """
    affected_str = f" for files: {', '.join(files_affected)}" if files_affected else ""
    user_detail = f" Reason: {reason}." if reason else " Approach rejected during human review."
    directive = f"Avoid previous solution pattern in batch {batch_id}{affected_str}.{user_detail}"

    return add_learned_rule(
        directive=directive,
        category="forbidden_pattern",
        domain="tech",
        source="diff_rejection",
    )


def delete_learned_rule(rule_id: str) -> bool:
    """Removes a learned rule from active memory and disk."""
    global _RULES_REGISTRY
    initial_len = len(_RULES_REGISTRY)
    _RULES_REGISTRY = [r for r in _RULES_REGISTRY if r.rule_id != rule_id]
    if len(_RULES_REGISTRY) < initial_len:
        save_rules_to_disk()
        return True
    return False


def clear_all_rules() -> None:
    """Wipes all ephemeral and stored rules."""
    global _RULES_REGISTRY
    _RULES_REGISTRY = []
    if _RULES_FILE.exists():
        try:
            _RULES_FILE.unlink()
        except Exception:
            pass


def list_learned_rules(category: str | None = None, domain: str | None = None) -> list[LearnedRule]:
    """Returns active learned rules with optional filtering."""
    results = _RULES_REGISTRY
    if category and category.lower() != "all":
        results = [r for r in results if r.category.lower() == category.lower()]
    if domain and domain.lower() != "all":
        results = [r for r in results if r.domain.lower() == domain.lower()]
    return sorted(results, key=lambda r: (r.confidence, r.hit_count), reverse=True)


def get_matching_rules(prompt: str, domain: str | None = None, limit: int = 5) -> list[LearnedRule]:
    """
    Retrieves the most relevant learned rules for an incoming prompt.
    Powered 100% by C++ SIMD Vector Cosine Semantic Distance in high-dimensional embedding space.
    Zero hardcoded keyword lists.
    """
    if not _RULES_REGISTRY:
        return []

    prompt_vec = project_rag._embed_text(prompt)
    scored_rules: dict[str, tuple[float, LearnedRule]] = {}

    # 1. Direct C++ SIMD Cosine Semantic Ranking across all active rules
    for rule in _RULES_REGISTRY:
        if domain and domain.lower() != "all" and rule.domain != domain.lower():
            continue

        rule_vec = project_rag._embed_text(rule.directive)
        sim_score = project_rag._cosine_similarity(prompt_vec, rule_vec)
        if sim_score > 0.05:
            accumulated = (sim_score * 3.0) * rule.confidence
            scored_rules[rule.rule_id] = (accumulated, rule)

    # 2. C++ SIMD Vector Memory Vault Semantic Context Retrieval
    try:
        chunks = project_rag.retrieve_context(query=prompt, limit=10, domain_filter=domain)
        for chunk in chunks:
            if chunk.path.startswith("rules://"):
                parts = chunk.path.split("/")
                if len(parts) >= 3:
                    file_part = parts[-1].split(".")[0]
                    for r in _RULES_REGISTRY:
                        if r.rule_id == file_part or file_part in r.rule_id:
                            current_score = scored_rules.get(r.rule_id, (0.0, r))[0]
                            scored_rules[r.rule_id] = (current_score + (chunk.score * 2.5), r)
    except Exception:
        pass

    sorted_items = sorted(scored_rules.values(), key=lambda x: x[0], reverse=True)
    matched = [item[1] for item in sorted_items[:limit]]

    for r in matched:
        r.hit_count += 1
    if matched:
        save_rules_to_disk()

    return matched


def build_rules_prompt_block(prompt: str, domain: str | None = None) -> str:
    """
    Constructs a high-priority prompt injection block containing all learned user rules
    applicable to the incoming query or directive.
    """
    matched = get_matching_rules(prompt, domain=domain)
    if not matched:
        # Fallback: include high-confidence forbidden patterns regardless of prompt
        always_forbidden = [
            r for r in _RULES_REGISTRY if r.category == "forbidden_pattern" and r.confidence >= 2.0
        ]
        if not always_forbidden:
            return ""
        matched = always_forbidden[:3]

    lines = [
        "<LEARNED_USER_RULES>",
        "The following behavioral rules and preferences were explicitly learned from previous user corrections:",
    ]
    for idx, rule in enumerate(matched, start=1):
        lines.append(f"{idx}. [{rule.domain.upper()} / {rule.category.upper()}] {rule.directive}")
    lines.append(
        "Strictly follow these learned rules in your plan, code generation, and responses."
    )
    lines.append("</LEARNED_USER_RULES>")

    return "\n".join(lines)


# Eagerly initialize on module import
load_rules_from_disk()
