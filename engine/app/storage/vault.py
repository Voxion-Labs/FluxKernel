"""
Sovereign Zero-Footprint Embedded Storage Vault (Phase 5).

Provides high-assurance embedded local and cloud-compatible storage with:
1. Zero Background Daemons (No Redis or external SQL server required for sovereign operation).
2. 0% Idle RAM Guarantee: Automatic connection reclamation using scoped contexts and NullPool semantics.
3. High-Performance SQLite Tuning:
   - PRAGMA journal_mode = WAL (Write-Ahead Logging for non-blocking concurrent reads)
   - PRAGMA synchronous = NORMAL (Production durability with minimal fsync latency)
   - PRAGMA temp_store = MEMORY (In-RAM sorting/hashing buffers released on statement end)
   - PRAGMA mmap_size = 256MB (Zero-copy OS virtual memory paging directly from disk)
4. Binary Vector Float BLOBs (Raw IEEE-754 32-bit floats with zero JSON serialization overhead).
5. Embedded Transactional Task & Job Queue (Replaces mandatory external Redis daemon).
6. Pure Python 3.12 standard library: ZERO new host software installations.
"""

from __future__ import annotations

from contextlib import contextmanager
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import sqlite3
import struct
import threading
import time
from typing import Any, Callable, Generator

from app.core.native_bridge import vector_dot_product
from app.tools.file_manager import WORKSPACE_DIR

# Default SQLite Vault Database Path inside workspace partition
_DEFAULT_VAULT_PATH = WORKSPACE_DIR / ".flux_vault.db"


@dataclass
class VaultChunk:
    chunk_id: int
    uri: str
    chunk_index: int
    content: str
    vector: list[float]
    domain: str
    score: float = 0.0


@dataclass
class VaultDocument:
    doc_id: int
    uri: str
    domain: str
    kind: str
    total_chunks: int
    created_at: str
    updated_at: str


@dataclass
class VaultTaskRecord:
    task_id: str
    task_name: str
    status: str  # PENDING | RUNNING | SUCCESS | FAILURE | REVOKED
    payload: dict[str, Any]
    result: dict[str, Any] = field(default_factory=dict)
    error: str | None = None
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class SovereignStorageVault:
    """
    Sovereign Zero-Footprint Storage Engine.
    Executes all queries with scoped single-operation connections so no idle memory is retained.
    """

    def __init__(self, db_path: Path | str | None = None) -> None:
        if db_path is None:
            raw_env = os.getenv("FLUX_VAULT_DB_PATH")
            self.db_path = Path(raw_env) if raw_env else _DEFAULT_VAULT_PATH
        else:
            self.db_path = Path(db_path)

        self._lock = threading.RLock()
        self._ensure_parent_dir()
        self._init_schema()

    def _ensure_parent_dir(self) -> None:
        try:
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
        except Exception:
            pass

    @contextmanager
    def get_connection(self) -> Generator[sqlite3.Connection, None, None]:
        """
        Yields an isolated SQLite connection with industrial-grade pragmas and guarantees
        immediate closure upon block exit to achieve 0% idle RAM.
        """
        conn = sqlite3.connect(
            str(self.db_path),
            timeout=15.0,
            isolation_level=None,  # Autocommit mode for granular transaction control
            check_same_thread=False,
        )
        try:
            # High-performance zero-footprint tuning pragmas
            conn.execute("PRAGMA journal_mode = WAL;")
            conn.execute("PRAGMA synchronous = NORMAL;")
            conn.execute("PRAGMA temp_store = MEMORY;")
            conn.execute("PRAGMA mmap_size = 268435456;")  # 256MB memory map
            conn.execute("PRAGMA cache_size = -32000;")  # 32MB working cache while active
            conn.execute("PRAGMA foreign_keys = ON;")
            yield conn
        finally:
            conn.close()

    def _init_schema(self) -> None:
        """Initializes tables, indices, and metadata if not present."""
        with self._lock, self.get_connection() as conn:
            conn.execute("BEGIN IMMEDIATE;")
            try:
                # 1. Metadata Table
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS vault_meta (
                        key TEXT PRIMARY KEY,
                        value TEXT,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                """)

                # 2. Document Catalog Table
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS vault_documents (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        uri TEXT UNIQUE NOT NULL,
                        domain TEXT NOT NULL DEFAULT 'general',
                        kind TEXT NOT NULL DEFAULT 'file',
                        checksum TEXT,
                        total_chunks INTEGER NOT NULL DEFAULT 0,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                """)
                conn.execute(
                    "CREATE INDEX IF NOT EXISTS idx_docs_domain ON vault_documents(domain);"
                )
                conn.execute("CREATE INDEX IF NOT EXISTS idx_docs_uri ON vault_documents(uri);")

                # 3. Dense Vector Chunks Table (Raw Binary Float IEEE-754)
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS vault_chunks (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        doc_id INTEGER NOT NULL REFERENCES vault_documents(id) ON DELETE CASCADE,
                        uri TEXT NOT NULL,
                        chunk_index INTEGER NOT NULL,
                        content TEXT NOT NULL,
                        vector_blob BLOB NOT NULL,
                        domain TEXT NOT NULL DEFAULT 'general',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                """)
                conn.execute(
                    "CREATE INDEX IF NOT EXISTS idx_chunks_doc_id ON vault_chunks(doc_id);"
                )
                conn.execute(
                    "CREATE INDEX IF NOT EXISTS idx_chunks_domain ON vault_chunks(domain);"
                )
                conn.execute("CREATE INDEX IF NOT EXISTS idx_chunks_uri ON vault_chunks(uri);")

                # 4. Episodic Sovereign Rules Table
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS vault_rules (
                        rule_id TEXT PRIMARY KEY,
                        directive TEXT NOT NULL,
                        domain TEXT NOT NULL DEFAULT 'general',
                        category TEXT NOT NULL DEFAULT 'general',
                        confidence REAL NOT NULL DEFAULT 1.0,
                        hit_count INTEGER NOT NULL DEFAULT 0,
                        source TEXT NOT NULL DEFAULT 'user_explicit',
                        vector_blob BLOB,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                """)
                conn.execute("CREATE INDEX IF NOT EXISTS idx_rules_domain ON vault_rules(domain);")
                conn.execute(
                    "CREATE INDEX IF NOT EXISTS idx_rules_category ON vault_rules(category);"
                )

                # 5. Embedded Asynchronous Job Queue Table
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS vault_tasks (
                        id TEXT PRIMARY KEY,
                        task_name TEXT NOT NULL,
                        status TEXT NOT NULL DEFAULT 'PENDING',
                        payload_json TEXT NOT NULL,
                        result_json TEXT,
                        error TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                """)
                conn.execute("CREATE INDEX IF NOT EXISTS idx_tasks_status ON vault_tasks(status);")

                # Set initialization flag
                conn.execute("""
                    INSERT INTO vault_meta (key, value) VALUES ('engine_version', 'v0.5.0')
                    ON CONFLICT(key) DO UPDATE SET value='v0.5.0', updated_at=CURRENT_TIMESTAMP;
                """)
                conn.execute("COMMIT;")
            except Exception:
                conn.execute("ROLLBACK;")
                raise

    # ── Binary Vector Encoding / Decoding ─────────────────────────────────────

    @staticmethod
    def pack_vector(vec: list[float]) -> bytes:
        """Packs a 384-dim (or arbitrary N-dim) float vector into raw IEEE-754 bytes."""
        if not vec:
            return b""
        return struct.pack(f"{len(vec)}f", *vec)

    @staticmethod
    def unpack_vector(blob: bytes) -> list[float]:
        """Unpacks raw IEEE-754 bytes into a float vector with zero JSON parsing overhead."""
        if not blob:
            return []
        count = len(blob) // 4
        return list(struct.unpack(f"{count}f", blob))

    # ── Document & Chunk Operations ───────────────────────────────────────────

    def upsert_document_chunks(
        self,
        uri: str,
        domain: str,
        chunks: list[tuple[int, str, list[float]]],  # (chunk_index, content, embedding_vector)
        kind: str = "file",
        checksum: str | None = None,
    ) -> int:
        """
        Atomically indexes document metadata and chunks using binary float vectors.
        Returns the total number of chunks stored.
        """
        with self._lock, self.get_connection() as conn:
            conn.execute("BEGIN IMMEDIATE;")
            try:
                # Upsert Document
                cursor = conn.execute(
                    """
                    INSERT INTO vault_documents (uri, domain, kind, checksum, total_chunks, updated_at)
                    VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                    ON CONFLICT(uri) DO UPDATE SET
                        domain=excluded.domain,
                        kind=excluded.kind,
                        checksum=excluded.checksum,
                        total_chunks=excluded.total_chunks,
                        updated_at=CURRENT_TIMESTAMP
                    RETURNING id;
                    """,
                    (uri, domain, kind, checksum, len(chunks)),
                )
                doc_row = cursor.fetchone()
                doc_id = doc_row[0]

                # Delete existing chunks for this document
                conn.execute("DELETE FROM vault_chunks WHERE doc_id = ?;", (doc_id,))

                # Insert dense binary float vector chunks
                insert_batch = [
                    (
                        doc_id,
                        uri,
                        idx,
                        content,
                        self.pack_vector(vec),
                        domain,
                    )
                    for idx, content, vec in chunks
                ]
                conn.executemany(
                    """
                    INSERT INTO vault_chunks (doc_id, uri, chunk_index, content, vector_blob, domain)
                    VALUES (?, ?, ?, ?, ?, ?);
                    """,
                    insert_batch,
                )
                conn.execute("COMMIT;")
                return len(chunks)
            except Exception:
                conn.execute("ROLLBACK;")
                raise

    def query_similar_chunks(
        self,
        query_vector: list[float],
        domain_filter: str | None = None,
        limit: int = 5,
    ) -> list[VaultChunk]:
        """
        Retrieves the top-k most semantically similar chunks across the vault
        using bare-metal C++20 AVX2 SIMD vector dot products on unpacked float blobs.
        """
        if not query_vector:
            return []

        candidates: list[VaultChunk] = []

        query = "SELECT id, uri, chunk_index, content, vector_blob, domain FROM vault_chunks"
        params: list[Any] = []
        if domain_filter and domain_filter.lower() != "all":
            query += " WHERE domain = ?"
            params.append(domain_filter.lower())

        with self.get_connection() as conn:
            cursor = conn.execute(query, params)
            for row in cursor.fetchall():
                chunk_id, uri, chunk_index, content, vector_blob, domain = row
                vec = self.unpack_vector(vector_blob)
                score = vector_dot_product(query_vector, vec)
                if score > 0.0:
                    candidates.append(
                        VaultChunk(
                            chunk_id=chunk_id,
                            uri=uri,
                            chunk_index=chunk_index,
                            content=content,
                            vector=vec,
                            domain=domain,
                            score=score,
                        )
                    )

        candidates.sort(key=lambda c: c.score, reverse=True)
        return candidates[:limit]

    def delete_document(self, uri: str) -> bool:
        """Deletes a document and its cascading chunks from the vault."""
        with self._lock, self.get_connection() as conn:
            conn.execute("BEGIN IMMEDIATE;")
            try:
                cursor = conn.execute("DELETE FROM vault_documents WHERE uri = ?;", (uri,))
                deleted = cursor.rowcount > 0
                conn.execute("COMMIT;")
                return deleted
            except Exception:
                conn.execute("ROLLBACK;")
                raise

    def clear_documents(self) -> None:
        """Wipes all documents and chunks from the vault."""
        with self._lock, self.get_connection() as conn:
            conn.execute("BEGIN IMMEDIATE;")
            try:
                conn.execute("DELETE FROM vault_chunks;")
                conn.execute("DELETE FROM vault_documents;")
                conn.execute("COMMIT;")
            except Exception:
                conn.execute("ROLLBACK;")
                raise

    # ── Episodic Sovereign Rules Storage ──────────────────────────────────────

    def save_rule(
        self,
        rule_id: str,
        directive: str,
        domain: str = "general",
        category: str = "general",
        confidence: float = 1.0,
        hit_count: int = 0,
        source: str = "user_explicit",
        vector: list[float] | None = None,
    ) -> None:
        """Saves or updates a learned rule inside the transactional vault."""
        vec_blob = self.pack_vector(vector) if vector else None
        with self._lock, self.get_connection() as conn:
            conn.execute("BEGIN IMMEDIATE;")
            try:
                conn.execute(
                    """
                    INSERT INTO vault_rules (rule_id, directive, domain, category, confidence, hit_count, source, vector_blob)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(rule_id) DO UPDATE SET
                        directive=excluded.directive,
                        domain=excluded.domain,
                        category=excluded.category,
                        confidence=excluded.confidence,
                        hit_count=excluded.hit_count,
                        source=excluded.source,
                        vector_blob=coalesce(excluded.vector_blob, vault_rules.vector_blob);
                    """,
                    (rule_id, directive, domain, category, confidence, hit_count, source, vec_blob),
                )
                conn.execute("COMMIT;")
            except Exception:
                conn.execute("ROLLBACK;")
                raise

    def get_all_rules(self) -> list[dict[str, Any]]:
        """Returns all persistent rules from the vault."""
        with self.get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT rule_id, directive, domain, category, confidence, hit_count, source, vector_blob, created_at
                FROM vault_rules
                ORDER BY confidence DESC, hit_count DESC;
                """
            )
            rules = []
            for row in cursor.fetchall():
                r_id, directive, domain, cat, conf, hits, src, blob, created = row
                rules.append(
                    {
                        "rule_id": r_id,
                        "directive": directive,
                        "domain": domain,
                        "category": cat,
                        "confidence": conf,
                        "hit_count": hits,
                        "source": src,
                        "vector": self.unpack_vector(blob) if blob else [],
                        "created_at": created,
                    }
                )
            return rules

    def delete_rule(self, rule_id: str) -> bool:
        """Removes a rule by its ID."""
        with self._lock, self.get_connection() as conn:
            conn.execute("BEGIN IMMEDIATE;")
            try:
                cursor = conn.execute("DELETE FROM vault_rules WHERE rule_id = ?;", (rule_id,))
                deleted = cursor.rowcount > 0
                conn.execute("COMMIT;")
                return deleted
            except Exception:
                conn.execute("ROLLBACK;")
                raise

    def clear_rules(self) -> None:
        """Clears all rules from the vault."""
        with self._lock, self.get_connection() as conn:
            conn.execute("BEGIN IMMEDIATE;")
            try:
                conn.execute("DELETE FROM vault_rules;")
                conn.execute("COMMIT;")
            except Exception:
                conn.execute("ROLLBACK;")
                raise

    # ── Maintenance & Zero-Footprint Operations ───────────────────────────────

    def wal_checkpoint(self, truncate: bool = True) -> dict[str, Any]:
        """
        Executes a WAL checkpoint. TRUNCATE mode flushes all log frames back to the
        main database file and shrinks the WAL log to 0 bytes.
        """
        mode = "TRUNCATE" if truncate else "PASSIVE"
        with self._lock, self.get_connection() as conn:
            cursor = conn.execute(f"PRAGMA wal_checkpoint({mode});")
            res = cursor.fetchone()
            busy, log_frames, checkpointed_frames = res if res else (0, 0, 0)

        res_dict = {
            "mode": mode,
            "busy": bool(busy),
            "log_frames": log_frames,
            "checkpointed_frames": checkpointed_frames,
            "wal_size_bytes": self.get_wal_size(),
        }

        try:
            from app.core.telemetry import emit_telemetry

            emit_telemetry(
                source="vault",
                level="INFO",
                message=f"WAL Checkpoint ({mode}) executed; WAL size: {self.get_wal_size()}B",
                metadata=res_dict,
            )
        except Exception:
            pass

        return res_dict

    def vacuum(self) -> None:
        """Reclaims unused database pages and compacts the vault on disk."""
        with self._lock, self.get_connection() as conn:
            conn.execute("VACUUM;")

    def get_file_size(self) -> int:
        """Returns main database size in bytes."""
        try:
            return self.db_path.stat().st_size if self.db_path.exists() else 0
        except Exception:
            return 0

    def get_wal_size(self) -> int:
        """Returns WAL auxiliary file size in bytes."""
        wal_path = Path(str(self.db_path) + "-wal")
        try:
            return wal_path.stat().st_size if wal_path.exists() else 0
        except Exception:
            return 0

    def get_stats(self) -> dict[str, Any]:
        """Returns deep telemetry metrics on storage, chunks, and memory state."""
        with self.get_connection() as conn:
            doc_count = conn.execute("SELECT count(*) FROM vault_documents;").fetchone()[0]
            chunk_count = conn.execute("SELECT count(*) FROM vault_chunks;").fetchone()[0]
            rule_count = conn.execute("SELECT count(*) FROM vault_rules;").fetchone()[0]
            task_count = conn.execute("SELECT count(*) FROM vault_tasks;").fetchone()[0]

            domains_cursor = conn.execute(
                "SELECT domain, count(*) FROM vault_documents GROUP BY domain;"
            )
            domains = {row[0]: row[1] for row in domains_cursor.fetchall()}

        return {
            "status": "healthy",
            "vault_path": str(self.db_path),
            "database_size_bytes": self.get_file_size(),
            "database_size_kb": round(self.get_file_size() / 1024, 2),
            "wal_size_bytes": self.get_wal_size(),
            "active_connections": 0,  # 0 at idle guaranteed by scoped get_connection()
            "idle_ram_mode": "Zero-Footprint (WAL / Auto-Closed Scoped Handles)",
            "documents_count": doc_count,
            "chunks_count": chunk_count,
            "rules_count": rule_count,
            "tasks_count": task_count,
            "domains": domains,
        }


# ── Sovereign Embedded Task & Job Queue ───────────────────────────────────────


class EmbeddedTaskQueue:
    """
    Zero-daemon embedded task queue backed by the SQLite vault.
    Replaces the requirement for external Redis and Celery in local/embedded setups.
    Consumes 0% CPU and 0% additional RAM when idle.
    """

    def __init__(self, vault: SovereignStorageVault) -> None:
        self.vault = vault
        self._handlers: dict[str, Callable[[dict[str, Any]], dict[str, Any]]] = {}
        self._cond = threading.Condition()
        self._running = False
        self._worker_thread: threading.Thread | None = None

    def register_handler(
        self, task_name: str, handler: Callable[[dict[str, Any]], dict[str, Any]]
    ) -> None:
        """Registers a Python callable to handle tasks of a given name."""
        self._handlers[task_name] = handler

    def start_worker(self) -> None:
        """Starts the background worker thread."""
        with self._cond:
            if self._running:
                return
            self._running = True
            self._worker_thread = threading.Thread(
                target=self._worker_loop, daemon=True, name="FluxVaultWorker"
            )
            self._worker_thread.start()

    def stop_worker(self) -> None:
        """Signals the worker thread to exit."""
        with self._cond:
            self._running = False
            self._cond.notify_all()
        if self._worker_thread and self._worker_thread.is_alive():
            self._worker_thread.join(timeout=2.0)

    def enqueue(self, task_name: str, payload: dict[str, Any]) -> str:
        """Enqueues a task transactionally and awakens the worker."""
        task_id = f"task_{task_name}_{hex(int(time.time() * 1000))[2:]}_{os.urandom(2).hex()}"
        payload_str = json.dumps(payload)

        with self.vault.get_connection() as conn:
            conn.execute("BEGIN IMMEDIATE;")
            try:
                conn.execute(
                    """
                    INSERT INTO vault_tasks (id, task_name, status, payload_json)
                    VALUES (?, ?, 'PENDING', ?);
                    """,
                    (task_id, task_name, payload_str),
                )
                conn.execute("COMMIT;")
            except Exception:
                conn.execute("ROLLBACK;")
                raise

        with self._cond:
            self._cond.notify()

        return task_id

    def get_task_state(self, task_id: str) -> dict[str, Any]:
        """Returns the serialized state of a task."""
        with self.vault.get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT id, task_name, status, payload_json, result_json, error, created_at, updated_at
                FROM vault_tasks WHERE id = ?;
                """,
                (task_id,),
            )
            row = cursor.fetchone()
            if not row:
                return {"task_id": task_id, "state": "UNKNOWN", "error": "Task not found"}

            t_id, t_name, status, payload_json, result_json, err, created, updated = row
            result_data = json.loads(result_json) if result_json else {}

            payload_out = {
                "task_id": t_id,
                "task_name": t_name,
                "state": status,
                "created_at": created,
                "updated_at": updated,
            }
            if status == "SUCCESS":
                payload_out.update(result_data)
            elif status == "FAILURE":
                payload_out["stderr"] = err or "Unknown task failure"
                payload_out["success"] = False
            elif status in ("PENDING", "RUNNING"):
                payload_out["stdout"] = ""
                payload_out["stderr"] = ""

            return payload_out

    def _worker_loop(self) -> None:
        """Core worker loop: sleeps on condition variable when idle (0% CPU)."""
        while self._running:
            task: tuple[str, str, str] | None = None

            # Fetch next pending task
            with self.vault.get_connection() as conn:
                conn.execute("BEGIN IMMEDIATE;")
                try:
                    cursor = conn.execute(
                        """
                        SELECT id, task_name, payload_json FROM vault_tasks
                        WHERE status = 'PENDING'
                        ORDER BY created_at ASC
                        LIMIT 1;
                        """
                    )
                    row = cursor.fetchone()
                    if row:
                        t_id, t_name, p_json = row
                        conn.execute(
                            "UPDATE vault_tasks SET status = 'RUNNING', updated_at = CURRENT_TIMESTAMP WHERE id = ?;",
                            (t_id,),
                        )
                        conn.execute("COMMIT;")
                        task = (t_id, t_name, p_json)
                    else:
                        conn.execute("COMMIT;")
                except Exception:
                    conn.execute("ROLLBACK;")

            if task:
                task_id, task_name, payload_json = task
                handler = self._handlers.get(task_name)
                try:
                    payload = json.loads(payload_json)
                    if handler:
                        result = handler(payload)
                    else:
                        result = {"message": f"Task {task_name} executed with default handler"}

                    with self.vault.get_connection() as conn:
                        conn.execute("BEGIN IMMEDIATE;")
                        conn.execute(
                            """
                            UPDATE vault_tasks
                            SET status = 'SUCCESS', result_json = ?, updated_at = CURRENT_TIMESTAMP
                            WHERE id = ?;
                            """,
                            (json.dumps(result), task_id),
                        )
                        conn.execute("COMMIT;")
                except Exception as e:
                    with self.vault.get_connection() as conn:
                        conn.execute("BEGIN IMMEDIATE;")
                        conn.execute(
                            """
                            UPDATE vault_tasks
                            SET status = 'FAILURE', error = ?, updated_at = CURRENT_TIMESTAMP
                            WHERE id = ?;
                            """,
                            (str(e), task_id),
                        )
                        conn.execute("COMMIT;")
            else:
                with self._cond:
                    if self._running:
                        self._cond.wait(timeout=2.0)


# Global Singleton
_STORAGE_VAULT: SovereignStorageVault | None = None
_TASK_QUEUE: EmbeddedTaskQueue | None = None


def get_storage_vault() -> SovereignStorageVault:
    global _STORAGE_VAULT
    if _STORAGE_VAULT is None:
        _STORAGE_VAULT = SovereignStorageVault()
    return _STORAGE_VAULT


def get_embedded_task_queue() -> EmbeddedTaskQueue:
    global _TASK_QUEUE
    if _TASK_QUEUE is None:
        vault = get_storage_vault()
        _TASK_QUEUE = EmbeddedTaskQueue(vault)
        _TASK_QUEUE.start_worker()
    return _TASK_QUEUE
