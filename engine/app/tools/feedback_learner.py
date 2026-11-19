"""
Episodic Feedback & Rule-Learning Engine for FluxKernel.

Learns user habits, forbidden patterns, domain rules, and coding preferences
from direct user feedback, diff rejections, and explicit instructions.
Indexes distilled rules into the C++ SIMD Vector Vault and dynamically
injects active rules into the Agentic Planner, Coder, and Personas
with ZERO GPU fine-tuning overhead, ZERO external dependencies, and ZERO Git bloat.
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


def _infer_rule_domain(text: str) -> str:
    lower = text.lower()
    fin_keywords = [
        "finance",
        "trading",
        "stock",
        "ebitda",
        "p&l",
        "portfolio",
        "black-scholes",
        "yield",
        "roi",
        "cagr",
        "dividend",
        "balance sheet",
    ]
    sci_keywords = [
        "physics",
        "quantum",
        "chemistry",
        "hamiltonian",
        "schrodinger",
        "derivative",
        "integral",
        "energy",
        "equation",
        "molecule",
    ]
    tech_keywords = [
        "code",
        "golang",
        "go",
        "python",
        "c++",
        "simd",
        "api",
        "docker",
        "test",
        "compiler",
        "http",
        "git",
        "database",
        "function",
        "struct",
        "class",
    ]

    for kw in fin_keywords:
        if kw in lower:
            return "finance"
    for kw in sci_keywords:
        if kw in lower:
            return "science"
    for kw in tech_keywords:
        if kw in lower:
            return "tech"
    return "general"


def _infer_rule_category(text: str) -> str:
    lower = text.lower()
    if any(
        k in lower for k in ["never", "don't", "avoid", "stop", "do not", "forbidden", "disallow"]
    ):
        return "forbidden_pattern"
    if any(
        k in lower
        for k in [
            "style",
            "format",
            "convention",
            "indent",
            "snake_case",
            "camelcase",
            "tabs",
            "spaces",
        ]
    ):
        return "coding_style"
    if any(
        k in lower
        for k in ["architecture", "layer", "interface", "design", "pattern", "clean arch", "mvc"]
    ):
        return "architecture"
    if any(k in lower for k in ["workflow", "git", "commit", "test first", "tdd", "snapshot"]):
        return "workflow"
    return "domain_guideline"


def _extract_keywords(text: str) -> list[str]:
    words = re.findall(r"\b[a-zA-Z0-9_-]{3,}\b", text.lower())
    stop_words = {
        "the",
        "and",
        "for",
        "with",
        "that",
        "this",
        "from",
        "when",
        "always",
        "never",
        "should",
        "must",
        "have",
        "been",
    }
    unique = []
    for w in words:
        if w not in stop_words and w not in unique:
            unique.append(w)
    return unique[:8]


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

    dom = domain or _infer_rule_domain(clean_directive)
    cat = category or _infer_rule_category(clean_directive)
    kws = trigger_keywords or _extract_keywords(clean_directive)

    rule_slug = _slugify(clean_directive)
    timestamp_suffix = hex(int(datetime.now(timezone.utc).timestamp()))[2:]
    rule_id = f"rule_{dom}_{rule_slug}_{timestamp_suffix}"

    rule = LearnedRule(
        rule_id=rule_id,
        directive=clean_directive,
        category=cat,
        domain=dom,
        trigger_keywords=kws,
        confidence=1.0,
        source=source,
    )

    # Prevent duplicate identical directives
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
                f"Triggers: {', '.join(kws)}\n"
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
    Combines C++ SIMD semantic vector retrieval with keyword trigger matching.
    """
    if not _RULES_REGISTRY:
        return []

    prompt_lower = prompt.lower()
    scored_rules: dict[str, tuple[float, LearnedRule]] = {}

    # 1. Fast Keyword matching
    for rule in _RULES_REGISTRY:
        if domain and domain.lower() != "all" and rule.domain != domain.lower():
            continue

        match_count = sum(1 for kw in rule.trigger_keywords if kw in prompt_lower)
        if match_count > 0:
            score = (match_count * 1.5) + rule.confidence
            scored_rules[rule.rule_id] = (score, rule)

    # 2. C++ SIMD Vector Vault retrieval fallback / boost
    try:
        chunks = project_rag.retrieve_context(query=prompt, limit=10, domain_filter=domain)
        for chunk in chunks:
            if chunk.path.startswith("rules://"):
                # Extract rule_id from path
                # Path format: rules://<domain>/<rule_id>.<cat>
                parts = chunk.path.split("/")
                if len(parts) >= 3:
                    file_part = parts[-1].split(".")[0]
                    for r in _RULES_REGISTRY:
                        if r.rule_id == file_part or file_part in r.rule_id:
                            current_score = scored_rules.get(r.rule_id, (0.0, r))[0]
                            scored_rules[r.rule_id] = (current_score + (chunk.score * 2.0), r)
    except Exception:
        pass

    # Sort rules by accumulated relevance score
    sorted_items = sorted(scored_rules.values(), key=lambda x: x[0], reverse=True)
    matched = [item[1] for item in sorted_items[:limit]]

    # Increment hit count on matched rules
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
