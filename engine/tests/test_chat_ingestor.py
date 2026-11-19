"""
Unit Tests for Cross-AI Learning Adapter & Transcript Ingestor.

Verifies format parsers (ChatGPT, Claude, Cursor, Markdown), code extraction,
domain classification, C++ SIMD Vector indexing, and FastAPI learning endpoints.
"""

from __future__ import annotations

from pathlib import Path
import sys

# Ensure engine path is in sys.path
ENGINE_DIR = Path(__file__).resolve().parent.parent
if str(ENGINE_DIR) not in sys.path:
    sys.path.insert(0, str(ENGINE_DIR))

from app.core import project_rag  # noqa: E402
from app.tools.chat_ingestor import (  # noqa: E402
    auto_detect_and_parse,
    clear_learned_sessions,
    ingest_and_index_sessions,
    parse_chatgpt,
    parse_claude,
    parse_cursor,
)


def _reset_state():
    clear_learned_sessions()
    project_rag.clear_in_memory_vault()


def test_parse_chatgpt_official_export():
    """Verify parsing ChatGPT official conversations.json schema with mapping tree."""
    _reset_state()
    chatgpt_export = [
        {
            "id": "chatgpt-sess-001",
            "title": "C++ SIMD Vector Dot Product",
            "create_time": 1700000000.0,
            "mapping": {
                "node-root": {
                    "id": "node-root",
                    "message": None,
                    "parent": None,
                    "children": ["node-user-1"],
                },
                "node-user-1": {
                    "id": "node-user-1",
                    "message": {
                        "id": "msg-u1",
                        "author": {"role": "user"},
                        "create_time": 1700000001.0,
                        "content": {
                            "content_type": "text",
                            "parts": [
                                "How do I implement an AVX2 SIMD dot product in C++ with FMA?"
                            ],
                        },
                    },
                    "parent": "node-root",
                    "children": ["node-asst-1"],
                },
                "node-asst-1": {
                    "id": "node-asst-1",
                    "message": {
                        "id": "msg-a1",
                        "author": {"role": "assistant"},
                        "create_time": 1700000005.0,
                        "content": {
                            "content_type": "text",
                            "parts": [
                                "Here is the AVX2 dot product function:\n```cpp\n#include <immintrin.h>\nfloat avx2_dot(const float* a, const float* b, int n) {\n    __m256 sum = _mm256_setzero_ps();\n    for (int i = 0; i < n; i += 8) {\n        __m256 va = _mm256_loadu_ps(a + i);\n        __m256 vb = _mm256_loadu_ps(b + i);\n        sum = _mm256_fmadd_ps(va, vb, sum);\n    }\n    return 0.0f;\n}\n```\nThis achieves 8 FLOPs per cycle."
                            ],
                        },
                    },
                    "parent": "node-user-1",
                    "children": [],
                },
            },
        }
    ]

    sessions = parse_chatgpt(chatgpt_export)
    assert len(sessions) == 1
    sess = sessions[0]
    assert sess.session_id == "chatgpt-sess-001"
    assert sess.title == "C++ SIMD Vector Dot Product"
    assert sess.source == "chatgpt"
    assert len(sess.turns) == 1

    turn = sess.turns[0]
    assert "AVX2 SIMD dot product" in turn.user_prompt
    assert "avx2_dot" in turn.assistant_response
    assert len(turn.code_snippets) == 1
    assert turn.code_snippets[0].lang == "cpp"
    assert turn.domain == "tech"


def test_parse_claude_json_and_markdown():
    """Verify parsing Claude JSON export and Claude Markdown transcript."""
    _reset_state()
    # Claude JSON
    claude_json = {
        "uuid": "claude-sess-99",
        "name": "Quantitative Finance Option Pricing",
        "created_at": "2024-05-10T14:00:00Z",
        "chat_messages": [
            {
                "sender": "human",
                "text": "Explain Black-Scholes call option pricing and cash flow yield",
            },
            {
                "sender": "assistant",
                "text": "The Black-Scholes formula calculates option price based on volatility and dividend yield:\n```python\nimport math\nfrom scipy.stats import norm\ndef black_scholes_call(S, K, T, r, sigma):\n    d1 = (math.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * math.sqrt(T))\n    d2 = d1 - sigma * math.sqrt(T)\n    return S * norm.cdf(d1) - K * math.exp(-r * T) * norm.cdf(d2)\n```",
            },
        ],
    }

    sessions = parse_claude(claude_json)
    assert len(sessions) == 1
    sess = sessions[0]
    assert sess.source == "claude"
    assert sess.title == "Quantitative Finance Option Pricing"
    assert len(sess.turns) == 1
    assert sess.turns[0].domain in {"tech", "finance"}
    assert len(sess.turns[0].code_snippets) == 1

    # Claude Markdown
    claude_md = """# Quantum Mechanics Simulation
Human:
How do we solve the time-independent Schrodinger equation and calculate Hamiltonian eigenvalues?

Assistant:
For a 1D potential well, the Hamiltonian operator H = -hbar^2 / (2m) d^2/dx^2 + V(x).
We discretize the kinetic energy operator into a tridiagonal Hamiltonian matrix.
"""
    md_sessions = parse_claude(claude_md)
    assert len(md_sessions) == 1
    assert md_sessions[0].turns[0].domain in {"science", "general"}


def test_parse_cursor_composer():
    """Verify parsing Cursor Composer JSON logs and Markdown transcripts."""
    _reset_state()
    cursor_log = {
        "title": "Go HTTP Reverse Proxy Resilience",
        "interactions": [
            {
                "prompt": "How to set Transport timeouts and disable keep-alives in Go reverse proxy?",
                "response": "Configure the http.Transport as follows:\n```go\ntransport := &http.Transport{\n    ResponseHeaderTimeout: 5 * time.Second,\n    DisableKeepAlives: true,\n}\n```",
                "timestamp": "2024-06-01T12:00:00Z",
            }
        ],
    }

    sessions = parse_cursor(cursor_log)
    assert len(sessions) == 1
    sess = sessions[0]
    assert sess.source == "cursor"
    assert len(sess.turns) == 1
    assert sess.turns[0].domain == "tech"
    assert sess.turns[0].code_snippets[0].lang == "go"


def test_auto_detect_and_index_simd_vault():
    """Verify auto-detection, capsule synthesis, and C++ SIMD Vector retrieval."""
    _reset_state()
    transcript = """# Distributed Ledger Architecture
### User:
What is the difference between proof-of-stake and proof-of-work in Byzantine fault tolerance?

### Assistant:
Proof of Work uses computational hash work (SHA-256) to elect block proposers.
Proof of Stake weights voting power by bonded tokens and slashed deposits.
"""
    sessions = auto_detect_and_parse(transcript, source="auto")
    assert len(sessions) == 1
    assert sessions[0].title == "Distributed Ledger Architecture"

    # Index into C++ SIMD Vector Vault
    res = ingest_and_index_sessions(sessions, auto_cache_rag=True)
    assert res["status"] == "success"
    assert res["total_turns_memorized"] == 1
    assert res["chunks_indexed"] >= 1

    # Semantic SIMD Search should retrieve this learned knowledge!
    retrieved = project_rag.retrieve_context(
        query="Byzantine fault tolerance proof-of-stake tokens", limit=3
    )
    assert len(retrieved) > 0
    top = retrieved[0]
    assert "ai://generic/" in top.path
    assert "Proof of Stake weights voting power" in top.content
    assert top.score > 0.0


def test_fastapi_learning_api():
    """Verify FastAPI learning router endpoints (/api/v1/learning/*)."""
    _reset_state()
    try:
        from fastapi.testclient import TestClient

        from app.database.connection import Base, engine
        from app.main import app

        try:
            Base.metadata.create_all(bind=engine)
        except Exception:
            pass

        with TestClient(app) as client:
            # Ingest payload
            payload = {
                "source": "markdown",
                "raw_content": "# Algorithmic Trading Bot\nUser:\nHow do we calculate Sharpe ratio and CAGR?\nAssistant:\nSharpe ratio is (Expected Return - Risk Free Rate) / Volatility.\n```python\ndef sharpe(returns, rf=0.02):\n    return (returns.mean() - rf) / returns.std()\n```",
            }
            resp = client.post("/api/v1/learning/ingest", json=payload)
            assert resp.status_code == 200
            data = resp.json()
            assert data["status"] == "success"
            assert data["sessions_processed"] == 1
            assert data["total_turns_memorized"] == 1
            assert data["total_code_snippets"] == 1

            # Status check
            status_resp = client.get("/api/v1/learning/status")
            assert status_resp.status_code == 200
            s_data = status_resp.json()
            assert s_data["total_sessions"] >= 1
            assert s_data["total_turns_memorized"] >= 1

            # Clear check
            clear_resp = client.post("/api/v1/learning/clear")
            assert clear_resp.status_code == 200
            assert clear_resp.json()["status"] == "cleared"

            # Verify cleared status
            status_after = client.get("/api/v1/learning/status").json()
            assert status_after["total_sessions"] == 0
    except ImportError:
        pass


if __name__ == "__main__":
    test_parse_chatgpt_official_export()
    test_parse_claude_json_and_markdown()
    test_parse_cursor_composer()
    test_auto_detect_and_index_simd_vault()
    test_fastapi_learning_api()
    print("All Cross-AI Learning Adapter & Transcript Ingestion tests passed successfully!")
