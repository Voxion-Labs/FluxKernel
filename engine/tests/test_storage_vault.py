"""
Unit Tests for Sovereign Zero-Footprint Embedded Storage Vault (Phase 5).

Verifies:
1. SQLite high-performance WAL initialization and 0% idle RAM connection reclamation.
2. Binary IEEE-754 float vector packing and lossless unpacking.
3. Document chunk indexing with raw float BLOBs and C++ AVX2 SIMD similarity search.
4. Episodic sovereign rule persistence.
5. Embedded zero-daemon asynchronous job queue and worker execution.
6. WAL checkpointing (TRUNCATE) and storage vacuuming.
"""

from __future__ import annotations

from pathlib import Path
import sys
import tempfile
import time

# Add engine directory to sys.path
ENGINE_DIR = Path(__file__).resolve().parent.parent
if str(ENGINE_DIR) not in sys.path:
    sys.path.insert(0, str(ENGINE_DIR))

from app.storage.vault import (  # noqa: E402
    EmbeddedTaskQueue,
    SovereignStorageVault,
)


def test_vault_initialization_and_zero_idle_connections():
    """Verify that SQLite WAL mode is active and active connections return to 0."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        db_path = Path(tmp_dir) / "test_vault.db"
        vault = SovereignStorageVault(db_path)

        stats = vault.get_stats()
        assert stats["status"] == "healthy"
        assert stats["active_connections"] == 0
        assert stats["documents_count"] == 0
        assert stats["chunks_count"] == 0
        assert stats["rules_count"] == 0

        # Verify PRAGMA journal_mode is WAL
        with vault.get_connection() as conn:
            mode = conn.execute("PRAGMA journal_mode;").fetchone()[0]
            assert mode.lower() == "wal"


def test_binary_vector_packing_and_unpacking():
    """Verify lossless raw binary IEEE-754 float vector serialization."""
    vec = [0.1234, -0.5678, 0.9999, 0.0, 1.4142]
    blob = SovereignStorageVault.pack_vector(vec)
    assert len(blob) == len(vec) * 4  # 4 bytes per float32

    unpacked = SovereignStorageVault.unpack_vector(blob)
    assert len(unpacked) == len(vec)
    for orig, res in zip(vec, unpacked):
        assert abs(orig - res) < 1e-6


def test_document_chunk_indexing_and_simd_retrieval():
    """Verify indexing chunks with float BLOBs and C++ SIMD dot product retrieval."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        db_path = Path(tmp_dir) / "test_rag_vault.db"
        vault = SovereignStorageVault(db_path)

        # Create sample vectors (3-dimensional for test)
        # Vector 1: highly aligned with [1.0, 0.0, 0.0]
        v1 = [1.0, 0.0, 0.0]
        v2 = [0.0, 1.0, 0.0]
        v3 = [0.0, 0.0, 1.0]

        chunks_data = [
            (0, "C++ SIMD AVX2 dot product implementation", v1),
            (1, "Go Gateway HTTP Reverse Proxy Router", v2),
            (2, "Quantitative Black-Scholes valuation formula", v3),
        ]

        inserted = vault.upsert_document_chunks(
            uri="src/kernel/core.cpp",
            domain="tech",
            chunks=chunks_data,
            kind="file",
        )
        assert inserted == 3

        stats = vault.get_stats()
        assert stats["documents_count"] == 1
        assert stats["chunks_count"] == 3
        assert stats["domains"]["tech"] == 1

        # Query aligned with v1
        query_v1 = [0.95, 0.05, 0.0]
        results = vault.query_similar_chunks(query_v1, domain_filter="tech", limit=2)
        assert len(results) > 0
        assert "SIMD AVX2" in results[0].content
        assert results[0].score > 0.9

        # Filter by different domain should return empty
        fin_results = vault.query_similar_chunks(query_v1, domain_filter="finance", limit=2)
        assert len(fin_results) == 0


def test_episodic_rules_persistence():
    """Verify storing, retrieving, and deleting episodic rules in vault."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        db_path = Path(tmp_dir) / "test_rules_vault.db"
        vault = SovereignStorageVault(db_path)

        vault.save_rule(
            rule_id="rule_tech_no_axios",
            directive="Always use Go net/http or Python urllib; avoid Axios.",
            domain="tech",
            category="forbidden_pattern",
            confidence=2.5,
            vector=[0.5, 0.5, 0.0],
        )

        vault.save_rule(
            rule_id="rule_fin_days",
            directive="Assume 252 trading days per year.",
            domain="finance",
            category="domain_guideline",
            confidence=1.0,
            vector=[0.0, 0.5, 0.5],
        )

        rules = vault.get_all_rules()
        assert len(rules) == 2
        assert rules[0]["rule_id"] == "rule_tech_no_axios"  # Highest confidence first
        assert rules[0]["confidence"] == 2.5
        assert len(rules[0]["vector"]) == 3

        # Delete rule
        deleted = vault.delete_rule("rule_fin_days")
        assert deleted is True
        assert len(vault.get_all_rules()) == 1


def test_embedded_task_queue_execution():
    """Verify zero-daemon asynchronous job enqueue and background worker processing."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        db_path = Path(tmp_dir) / "test_tasks_vault.db"
        vault = SovereignStorageVault(db_path)
        queue = EmbeddedTaskQueue(vault)

        # Register handler
        def multiply_handler(payload: dict) -> dict:
            a = payload.get("a", 0)
            b = payload.get("b", 0)
            return {"product": a * b, "success": True}

        queue.register_handler("compute_product", multiply_handler)
        queue.start_worker()

        try:
            # Enqueue task
            task_id = queue.enqueue("compute_product", {"a": 6, "b": 7})
            assert task_id.startswith("task_compute_product_")

            # Wait for background completion
            for _ in range(30):
                state = queue.get_task_state(task_id)
                if state["state"] in ("SUCCESS", "FAILURE"):
                    break
                time.sleep(0.05)

            final_state = queue.get_task_state(task_id)
            assert final_state["state"] == "SUCCESS"
            assert final_state["product"] == 42
        finally:
            queue.stop_worker()


def test_wal_checkpoint_and_vacuum():
    """Verify TRUNCATE WAL checkpoint and vacuuming."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        db_path = Path(tmp_dir) / "test_maint_vault.db"
        vault = SovereignStorageVault(db_path)

        # Insert dummy data to create WAL frames
        dummy_chunks = [(i, f"chunk content {i}", [float(i), 1.0]) for i in range(20)]
        vault.upsert_document_chunks("file://test.txt", "general", dummy_chunks)

        # Run WAL checkpoint
        cp_res = vault.wal_checkpoint(truncate=True)
        assert cp_res["mode"] == "TRUNCATE"
        assert cp_res["wal_size_bytes"] == 0

        # Run Vacuum
        vault.vacuum()
        assert vault.get_file_size() > 0


if __name__ == "__main__":
    test_vault_initialization_and_zero_idle_connections()
    test_binary_vector_packing_and_unpacking()
    test_document_chunk_indexing_and_simd_retrieval()
    test_episodic_rules_persistence()
    test_embedded_task_queue_execution()
    test_wal_checkpoint_and_vacuum()
    print("All Sovereign Storage Vault unit tests passed successfully!")
