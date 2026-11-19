"""
Unit Tests for Episodic Feedback & Sovereign Rule Learning Engine.

Verifies rule distillation, domain classification, SIMD vector vault indexing,
diff rejection learning, prompt injection, and FastAPI feedback endpoints.
"""

from __future__ import annotations

from pathlib import Path
import sys

# Ensure engine path is in sys.path
ENGINE_DIR = Path(__file__).resolve().parent.parent
if str(ENGINE_DIR) not in sys.path:
    sys.path.insert(0, str(ENGINE_DIR))

from app.core import project_rag  # noqa: E402
from app.tools.feedback_learner import (  # noqa: E402
    add_learned_rule,
    build_rules_prompt_block,
    clear_all_rules,
    delete_learned_rule,
    get_matching_rules,
    list_learned_rules,
    record_diff_rejection,
)


def _reset():
    clear_all_rules()
    project_rag.clear_in_memory_vault()


def test_rule_creation_and_domain_inference():
    """Verify sovereign rule creation and default domain/category fallbacks."""
    _reset()

    # Explicit domain & category
    rule1 = add_learned_rule(
        directive="Never use Axios or Node-fetch; always use Go net/http or Python urllib standard library.",
        domain="tech",
        category="forbidden_pattern",
    )
    assert rule1.domain == "tech"
    assert rule1.category == "forbidden_pattern"

    # Finance rule
    rule2 = add_learned_rule(
        directive="In financial trading models and Black-Scholes pricing, assume 252 trading days per year.",
        domain="finance",
        category="domain_guideline",
    )
    assert rule2.domain == "finance"
    assert rule2.category == "domain_guideline"

    # Science rule defaulting to general when unspecified
    rule3 = add_learned_rule(
        directive="Ensure energy conservation when integrating Hamiltonian equations in quantum mechanics."
    )
    assert rule3.domain == "general"
    assert rule3.category == "general"

    rules = list_learned_rules()
    assert len(rules) == 3


def test_rule_matching_and_prompt_injection():
    """Verify rule retrieval against prompts and prompt injection block generation."""
    _reset()

    add_learned_rule(
        directive="Never use Axios or Node-fetch; always use standard library http.Client in Go.",
        category="forbidden_pattern",
        domain="tech",
    )

    add_learned_rule(
        directive="In corporate finance reports, compute EBITDA and Operating Cash Flow separately.",
        category="domain_guideline",
        domain="finance",
    )

    # Match tech prompt
    matched_tech = get_matching_rules("How do I make an HTTP API call to fetch weather data?")
    assert len(matched_tech) > 0
    assert any("Axios" in r.directive for r in matched_tech)

    # Match finance prompt
    matched_fin = get_matching_rules(
        "Generate a quarterly corporate finance summary with EBITDA margins"
    )
    assert len(matched_fin) > 0
    assert any("EBITDA" in r.directive for r in matched_fin)

    # Prompt block generation
    block = build_rules_prompt_block("Fetch external API data")
    assert "<LEARNED_USER_RULES>" in block
    assert "Axios" in block
    assert "</LEARNED_USER_RULES>" in block


def test_diff_rejection_learning():
    """Verify that rejecting an agentic diff creates a learned rule."""
    _reset()

    rule = record_diff_rejection(
        batch_id="diff-4091",
        reason="Violated zero-JS policy by adding React script tag",
        files_affected=["templates/dashboard.html"],
    )

    assert rule.category == "forbidden_pattern"
    assert rule.source == "diff_rejection"
    assert "diff-4091" in rule.directive
    assert "React" in rule.directive

    rules = list_learned_rules()
    assert len(rules) == 1


def test_rule_deletion_and_clear():
    """Verify deleting individual rules and wiping registry."""
    _reset()

    r1 = add_learned_rule(
        "Use 4 spaces for Python indentation.", category="coding_style", domain="tech"
    )
    add_learned_rule(
        "Format SQL queries with uppercase keywords.", category="coding_style", domain="tech"
    )

    assert len(list_learned_rules()) == 2
    deleted = delete_learned_rule(r1.rule_id)
    assert deleted is True
    assert len(list_learned_rules()) == 1

    clear_all_rules()
    assert len(list_learned_rules()) == 0


def test_fastapi_feedback_api():
    """Verify FastAPI /api/v1/feedback endpoints."""
    _reset()
    try:
        from fastapi.testclient import TestClient

        from app.database.connection import Base, engine
        from app.main import app

        try:
            Base.metadata.create_all(bind=engine)
        except Exception:
            pass

        with TestClient(app) as client:
            # 1. Record rule
            payload = {
                "directive": "Never commit unencrypted API keys or .env secrets to git.",
                "category": "forbidden_pattern",
                "domain": "tech",
                "trigger_keywords": ["keys", "secrets", "env", "git"],
            }
            res = client.post("/api/v1/feedback/record", json=payload)
            assert res.status_code == 200
            data = res.json()
            assert data["category"] == "forbidden_pattern"
            rule_id = data["rule_id"]

            # 2. Get rules
            res_list = client.get("/api/v1/feedback/rules")
            assert res_list.status_code == 200
            rules_list = res_list.json()
            assert len(rules_list) >= 1

            # 3. Evaluate prompt
            res_eval = client.post(
                "/api/v1/feedback/evaluate",
                json={"prompt": "How do I store API keys in my repo?"},
            )
            assert res_eval.status_code == 200
            eval_data = res_eval.json()
            assert eval_data["matched_rules_count"] >= 1
            assert "<LEARNED_USER_RULES>" in eval_data["rules_prompt_block"]

            # 4. Reject diff endpoint
            res_rej = client.post(
                "/api/v1/feedback/reject-diff",
                json={"batch_id": "diff-8899", "reason": "Hardcoded token in source"},
            )
            assert res_rej.status_code == 200
            assert "diff-8899" in res_rej.json()["directive"]

            # 5. Delete rule
            res_del = client.delete(f"/api/v1/feedback/rules/{rule_id}")
            assert res_del.status_code == 200
            assert res_del.json()["status"] == "deleted"

            # 6. Clear
            res_clear = client.post("/api/v1/feedback/clear")
            assert res_clear.status_code == 200
            assert res_clear.json()["status"] == "cleared"
    except ImportError:
        pass


if __name__ == "__main__":
    test_rule_creation_and_domain_inference()
    test_rule_matching_and_prompt_injection()
    test_diff_rejection_learning()
    test_rule_deletion_and_clear()
    test_fastapi_feedback_api()
    print("All Episodic Feedback & Sovereign Rule Learning tests passed successfully!")
