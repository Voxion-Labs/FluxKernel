from __future__ import annotations

import sys
import tempfile
from pathlib import Path

# Add engine directory to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.workspace_search import search_workspace


def test_empty_query():
    res = search_workspace("")
    assert res["query"] == ""
    assert res["total_matches"] == 0
    assert len(res["results"]) == 0


def test_search_and_domain_filter():
    with tempfile.TemporaryDirectory() as tmp_dir:
        root = Path(tmp_dir)

        # Create multi-domain files
        (root / "main.go").write_text(
            'package main\n\nfunc RunFluxKernel() {\n    println("running")\n}\n',
            encoding="utf-8",
        )
        (root / "physics.tex").write_text(
            "\\documentclass{article}\n\\begin{document}\nQuantum Hamiltonian equation\n\\end{document}\n",
            encoding="utf-8",
        )
        (root / "ledger.csv").write_text(
            "id,account,balance\n1,treasury,50000\n2,operating,12000\n",
            encoding="utf-8",
        )
        (root / "system.py").write_text(
            "class SystemMonitor:\n    def check_health(self):\n        return True\n",
            encoding="utf-8",
        )

        # 1. Search for symbol
        res = search_workspace("RunFluxKernel", domain="all", target_dir=root)
        assert res["total_matches"] >= 1
        assert res["files_matched"] >= 1
        first = res["results"][0]
        assert first["path"] == "main.go"
        assert first["match_type"] == "symbol"
        assert first["domain"] == "tech"
        assert first["line_number"] == 3

        # 2. Search for filename
        res_file = search_workspace("ledger", domain="all", target_dir=root)
        assert any(r["match_type"] == "file" for r in res_file["results"])
        assert res_file["domains"]["finance"] >= 1

        # 3. Domain filter: search finance only
        res_fin = search_workspace("treasury", domain="finance", target_dir=root)
        assert res_fin["total_matches"] >= 1
        assert all(r["domain"] == "finance" for r in res_fin["results"])

        # Domain filter: search science only for tech term returns 0
        res_none = search_workspace("RunFluxKernel", domain="science", target_dir=root)
        assert res_none["total_matches"] == 0


def test_context_lines_extraction():
    with tempfile.TemporaryDirectory() as tmp_dir:
        root = Path(tmp_dir)
        content = "\n".join([f"line_{i}" for i in range(1, 11)])
        (root / "sample.txt").write_text(content, encoding="utf-8")

        res = search_workspace("line_5", domain="all", target_dir=root)
        assert res["total_matches"] == 1
        match = res["results"][0]
        assert match["line_number"] == 5
        assert match["snippet"] == "line_5"
        assert "line_3" in match["context_before"] or "line_4" in match["context_before"]
        assert "line_6" in match["context_after"] or "line_7" in match["context_after"]


def test_search_api_endpoints():
    try:
        from fastapi.testclient import TestClient
        from app.main import app

        with TestClient(app) as client:
            # GET search
            res = client.get("/api/v1/workspace/search?q=test&limit=5")
            assert res.status_code == 200
            data = res.json()
            assert "total_matches" in data
            assert "results" in data

            # POST search
            payload = {"query": "test", "domain": "all", "limit": 5}
            res_post = client.post("/api/v1/workspace/search", json=payload)
            assert res_post.status_code == 200
            data_post = res_post.json()
            assert data_post["query"] == "test"
    except ImportError:
        pass


if __name__ == "__main__":
    test_empty_query()
    test_search_and_domain_filter()
    test_context_lines_extraction()
    test_search_api_endpoints()
    print("All Universal Workspace Search unit tests passed successfully!")
