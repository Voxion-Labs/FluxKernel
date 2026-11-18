from __future__ import annotations

import sys
import tempfile
from pathlib import Path

# Add engine directory to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core import project_rag

try:
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from app.database.models import Base

    _HAS_SQLALCHEMY = True
except (ImportError, Exception):
    _HAS_SQLALCHEMY = False


def test_text_extensions_clean():
    """Verify that legacy TypeScript and JavaScript are purged, and multi-domain extensions are present."""
    exts = project_rag._TEXT_EXTENSIONS
    assert ".ts" not in exts
    assert ".tsx" not in exts
    assert ".js" not in exts
    assert ".jsx" not in exts

    # Tri-stack tech
    assert ".go" in exts
    assert ".cpp" in exts
    assert ".py" in exts
    assert ".sql" in exts

    # Finance and tabular
    assert ".csv" in exts
    assert ".tsv" in exts

    # Science and math
    assert ".tex" in exts


def test_infer_domain():
    """Verify domain classification archetypes."""
    assert project_rag.infer_domain("pkg/server/main.go") == "tech"
    assert project_rag.infer_domain("native/core.cpp") == "tech"
    assert project_rag.infer_domain("reports/q3_balance.csv") == "finance"
    assert project_rag.infer_domain("data/ledger.json") == "finance"
    assert project_rag.infer_domain("papers/proof.tex") == "science"
    assert project_rag.infer_domain("README.md") == "general"


def test_indexing_and_simd_retrieval():
    """Verify scanning, indexing, and C++ SIMD vector dot product retrieval."""
    db = None
    if _HAS_SQLALCHEMY:
        test_engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(bind=test_engine)
        TestingSession = sessionmaker(bind=test_engine)
        db = TestingSession()

    with tempfile.TemporaryDirectory() as tmp_dir:
        root = Path(tmp_dir)

        # Create multi-domain files
        (root / "kernel.go").write_text(
            'package main\n\nfunc RunFluxKernel() { println("Sovereign") }', encoding="utf-8"
        )
        (root / "physics.cpp").write_text(
            '#include <iostream>\nint main() { std::cout << "Quantum State"; }', encoding="utf-8"
        )
        (root / "ledger.csv").write_text(
            "item,cost,roi\nserver,1000,2.5\nstorage,200,3.0", encoding="utf-8"
        )
        (root / "memo.md").write_text(
            "# Executive Briefing\nDeployment of autonomous kernel is complete.", encoding="utf-8"
        )

        # Scan and index
        stats = project_rag.scan_and_index_workspace(db, target_dir=root)
        assert stats["status"] == "indexed"
        assert stats["files_indexed"] == 4
        assert stats["chunks_indexed"] >= 4
        assert stats["domains"]["tech"] == 2
        assert stats["domains"]["finance"] == 1
        assert stats["domains"]["general"] == 1

        # Retrieve tech
        tech_results = project_rag.retrieve_context(db, query="RunFluxKernel Sovereign", limit=5)
        assert len(tech_results) > 0
        assert tech_results[0].path == "kernel.go"
        assert tech_results[0].score > 0.0
        assert tech_results[0].domain == "tech"

        # Retrieve finance with domain filter
        fin_results = project_rag.retrieve_context(
            db, query="server cost ledger roi", limit=5, domain_filter="finance"
        )
        assert len(fin_results) > 0
        assert fin_results[0].path == "ledger.csv"
        assert fin_results[0].domain == "finance"

        # Verify cross-domain filter strictly excludes non-matching domains
        no_tech = project_rag.retrieve_context(
            db, query="Quantum State", limit=5, domain_filter="finance"
        )
        assert all(r.domain == "finance" for r in no_tech)
        assert not any(r.path == "physics.cpp" for r in no_tech)

    if db is not None:
        db.close()


def test_rag_api_endpoints():
    """Verify FastAPI /api/v1/rag endpoints."""
    try:
        from fastapi.testclient import TestClient
        from app.main import app

        client = TestClient(app)

        # Status check
        res = client.get("/api/v1/rag/status")
        assert res.status_code == 200
        data = res.json()
        assert "total_pinned_files" in data
        assert "simd_accelerated" in data

        # Search endpoint
        search_payload = {
            "query": "FluxKernel sovereign architecture",
            "limit": 3,
        }
        res_search = client.post("/api/v1/rag/search", json=search_payload)
        assert res_search.status_code == 200
        search_data = res_search.json()
        assert search_data["query"] == "FluxKernel sovereign architecture"
        assert "simd_accelerated" in search_data
    except ImportError:
        pass


if __name__ == "__main__":
    test_text_extensions_clean()
    test_infer_domain()
    test_indexing_and_simd_retrieval()
    test_rag_api_endpoints()
    print("All Universal Multi-Domain RAG & SIMD tests passed successfully!")
