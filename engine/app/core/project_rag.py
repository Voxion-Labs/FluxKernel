from __future__ import annotations

import json
import math
import re
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

try:
    from sqlalchemy.orm import Session
    from app.database.models import ProjectDocumentChunk, ProjectPin

    _HAS_SQLALCHEMY = True
except (ImportError, Exception):
    Session = Any  # type: ignore
    ProjectDocumentChunk = None  # type: ignore
    ProjectPin = None  # type: ignore
    _HAS_SQLALCHEMY = False

from app.core.native_bridge import _IS_NATIVE_LOADED, vector_dot_product
from app.tools.file_manager import (
    WORKSPACE_DIR,
    _resolve_and_check_path,
)

_TOKEN_PATTERN = re.compile(r"[A-Za-z_][A-Za-z0-9_./:-]{1,63}")
_VECTOR_SIZE = 384
_CHUNK_SIZE = 1200
_CHUNK_OVERLAP = 180


# In-memory zero-dependency store for bare-metal host execution
@dataclass
class MemoryChunk:
    path: str
    chunk_index: int
    content: str
    embedding: list[float]
    domain: str = "general"


_IN_MEMORY_VAULT: list[MemoryChunk] = []

# Multi-domain text extensions (Zero Node.js/TS, strictly tri-stack & multi-disciplinary)
_TEXT_EXTENSIONS = {
    # Tech & Systems Engineering
    ".go",
    ".cpp",
    ".cc",
    ".cxx",
    ".h",
    ".hpp",
    ".c",
    ".py",
    ".rs",
    ".sql",
    ".sh",
    ".bat",
    ".ps1",
    # Science, Math & Simulation
    ".tex",
    ".latex",
    ".m",
    ".r",
    # Finance, Commerce & Tabular Data
    ".csv",
    ".tsv",
    ".json",
    # Documents, Specs & Enterprise Operations
    ".md",
    ".txt",
    ".yaml",
    ".yml",
    ".toml",
    ".ini",
    ".env",
    ".css",
    ".html",
}


def infer_domain(path_str: str) -> str:
    """Classify file path or memory URI into its sovereign domain archetype."""
    path_lower = path_str.lower()
    if "/tech/" in path_lower or "domain:tech" in path_lower or path_lower.endswith(".tech"):
        return "tech"
    if (
        "/science/" in path_lower
        or "domain:science" in path_lower
        or path_lower.endswith(".science")
    ):
        return "science"
    if (
        "/finance/" in path_lower
        or "domain:finance" in path_lower
        or path_lower.endswith(".finance")
    ):
        return "finance"
    ext = Path(path_str).suffix.lower()
    if ext in {
        ".go",
        ".cpp",
        ".cc",
        ".cxx",
        ".h",
        ".hpp",
        ".c",
        ".py",
        ".rs",
        ".sql",
        ".sh",
        ".bat",
        ".ps1",
    }:
        return "tech"
    if ext in {".tex", ".latex", ".m", ".r"}:
        return "science"
    if ext in {".csv", ".tsv", ".json"}:
        return "finance"
    return "general"


@dataclass
class RetrievedChunk:
    path: str
    content: str
    score: float
    domain: str = "general"
    chunk_index: int = 0


def _is_text_file(path: Path) -> bool:
    return path.is_file() and path.suffix.lower() in _TEXT_EXTENSIONS


def _iter_pin_targets(path: Path) -> Iterable[Path]:
    if path.is_file():
        if _is_text_file(path):
            yield path
        return

    for item in path.rglob("*"):
        if item.is_file() and _is_text_file(item):
            yield item


def _chunk_text(text: str, size: int = _CHUNK_SIZE, overlap: int = _CHUNK_OVERLAP) -> list[str]:
    normalized = text.strip()
    if not normalized:
        return []

    chunks: list[str] = []
    start = 0
    while start < len(normalized):
        end = min(len(normalized), start + size)
        chunks.append(normalized[start:end])
        if end >= len(normalized):
            break
        start = max(0, end - overlap)
    return chunks


def _embed_text(text: str) -> list[float]:
    vector = [0.0] * _VECTOR_SIZE
    for token in _TOKEN_PATTERN.findall(text.lower()):
        index = hash(token) % _VECTOR_SIZE
        vector[index] += 1.0

    norm = math.sqrt(sum(value * value for value in vector))
    if norm == 0:
        return vector
    return [value / norm for value in vector]


def _cosine_similarity(left: list[float], right: list[float]) -> float:
    """Compute cosine similarity via bare-metal C++20 SIMD AVX2 vector dot product."""
    return vector_dot_product(left, right)


def _relative_workspace_path(path: Path) -> str:
    return path.relative_to(WORKSPACE_DIR).as_posix()


def scan_and_index_workspace(
    db: Session | None = None, target_dir: Path | None = None
) -> dict[str, Any]:
    """
    Scans the entire workspace directory, indexes all multi-domain files (Tech, Science, Finance, Docs)
    into ProjectPin and ProjectDocumentChunk with SIMD-ready embeddings.
    Falls back gracefully to in-memory vault when database is absent.
    """
    global _IN_MEMORY_VAULT
    root = target_dir or WORKSPACE_DIR
    if not root.exists():
        root.mkdir(parents=True, exist_ok=True)

    eligible_files = [p for p in root.rglob("*") if _is_text_file(p)]
    # Ignore internal partitions (.git, .flux_snapshots, .flux_temp)
    eligible_files = [
        p
        for p in eligible_files
        if not any(part.startswith(".") and part != "." for part in p.relative_to(root).parts)
    ]

    total_chunks = 0
    domains_count: dict[str, int] = {"tech": 0, "science": 0, "finance": 0, "general": 0}
    new_in_memory: list[MemoryChunk] = []

    use_db = _HAS_SQLALCHEMY and db is not None

    for file_path in eligible_files:
        try:
            rel_path = file_path.relative_to(root).as_posix()
        except ValueError:
            rel_path = file_path.name
        domain = infer_domain(rel_path)
        domains_count[domain] = domains_count.get(domain, 0) + 1

        pin = None
        if use_db:
            pin = db.query(ProjectPin).filter(ProjectPin.path == rel_path).first()
            if pin is None:
                pin = ProjectPin(path=rel_path, kind="file", label=f"Domain: {domain}")
                db.add(pin)
                db.flush()
            else:
                db.query(ProjectDocumentChunk).filter(
                    ProjectDocumentChunk.pin_id == pin.id
                ).delete()
                db.flush()

        try:
            content = file_path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            content = file_path.read_text(encoding="utf-8", errors="ignore")

        chunks = _chunk_text(content)
        for index, chunk in enumerate(chunks):
            embedding = _embed_text(chunk)
            if use_db and pin is not None:
                db.add(
                    ProjectDocumentChunk(
                        pin_id=pin.id,
                        path=rel_path,
                        chunk_index=index,
                        content=chunk,
                        embedding_json=json.dumps(embedding),
                    )
                )
            new_in_memory.append(
                MemoryChunk(
                    path=rel_path,
                    chunk_index=index,
                    content=chunk,
                    embedding=embedding,
                    domain=domain,
                )
            )
            total_chunks += 1

    if use_db:
        db.commit()

    _IN_MEMORY_VAULT = new_in_memory

    return {
        "status": "indexed",
        "files_indexed": len(eligible_files),
        "chunks_indexed": total_chunks,
        "domains": domains_count,
        "simd_accelerated": _IS_NATIVE_LOADED,
    }


def pin_workspace_paths(
    db: Session, paths: list[str], *, label: str | None = None
) -> list[ProjectPin]:
    pinned: list[ProjectPin] = []

    for raw_path in paths:
        target = _resolve_and_check_path(raw_path)
        relative_root = _relative_workspace_path(target)
        kind = "folder" if target.is_dir() else "file"

        pin = db.query(ProjectPin).filter(ProjectPin.path == relative_root).first()
        if pin is None:
            pin = ProjectPin(path=relative_root, kind=kind, label=label)
            db.add(pin)
            db.flush()
        else:
            pin.kind = kind
            if label:
                pin.label = label
            db.query(ProjectDocumentChunk).filter(ProjectDocumentChunk.pin_id == pin.id).delete()
            db.flush()

        for file_path in _iter_pin_targets(target):
            try:
                content = file_path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                content = file_path.read_text(encoding="utf-8", errors="ignore")

            for index, chunk in enumerate(_chunk_text(content)):
                embedding = _embed_text(chunk)
                db.add(
                    ProjectDocumentChunk(
                        pin_id=pin.id,
                        path=_relative_workspace_path(file_path),
                        chunk_index=index,
                        content=chunk,
                        embedding_json=json.dumps(embedding),
                    )
                )

        pinned.append(pin)

    db.commit()
    for pin in pinned:
        db.refresh(pin)
    return pinned


def list_pins(db: Session) -> list[ProjectPin]:
    return db.query(ProjectPin).order_by(ProjectPin.created_at.desc(), ProjectPin.id.desc()).all()


def delete_pin(db: Session, pin_id: int) -> bool:
    pin = db.query(ProjectPin).filter(ProjectPin.id == pin_id).first()
    if pin is None:
        return False
    db.delete(pin)
    db.commit()
    return True


def retrieve_context(
    db: Session | None = None,
    query: str = "",
    limit: int = 5,
    domain_filter: str | None = None,
) -> list[RetrievedChunk]:
    if not query.strip():
        return []

    query_embedding = _embed_text(query)
    results: list[RetrievedChunk] = []

    use_db = _HAS_SQLALCHEMY and db is not None

    if use_db:
        chunks = db.query(ProjectDocumentChunk).all()
        for chunk in chunks:
            domain = infer_domain(chunk.path)
            if domain_filter and domain_filter.lower() != "all" and domain != domain_filter.lower():
                continue

            try:
                embedding = json.loads(chunk.embedding_json)
            except json.JSONDecodeError:
                continue

            score = _cosine_similarity(query_embedding, embedding)
            if score <= 0:
                continue
            results.append(
                RetrievedChunk(
                    path=chunk.path,
                    content=chunk.content,
                    score=score,
                    domain=domain,
                    chunk_index=chunk.chunk_index,
                )
            )
    else:
        for m_chunk in _IN_MEMORY_VAULT:
            if (
                domain_filter
                and domain_filter.lower() != "all"
                and m_chunk.domain != domain_filter.lower()
            ):
                continue
            score = _cosine_similarity(query_embedding, m_chunk.embedding)
            if score <= 0:
                continue
            results.append(
                RetrievedChunk(
                    path=m_chunk.path,
                    content=m_chunk.content,
                    score=score,
                    domain=m_chunk.domain,
                    chunk_index=m_chunk.chunk_index,
                )
            )

    results.sort(key=lambda item: item.score, reverse=True)
    return results[:limit]


def index_text_block(
    uri: str,
    content: str,
    domain: str = "general",
    db: Session | None = None,
) -> int:
    """
    Indexes an arbitrary text block (e.g. from live web research or imported AI chat)
    directly into the SIMD-accelerated memory vault (and database if present).
    Returns the number of chunks indexed.
    """
    global _IN_MEMORY_VAULT
    chunks = _chunk_text(content)
    if not chunks:
        return 0

    use_db = _HAS_SQLALCHEMY and db is not None
    pin = None
    if use_db:
        pin = db.query(ProjectPin).filter(ProjectPin.path == uri).first()
        if pin is None:
            pin = ProjectPin(path=uri, kind="memory", label=f"Domain: {domain}")
            db.add(pin)
            db.flush()
        else:
            db.query(ProjectDocumentChunk).filter(ProjectDocumentChunk.pin_id == pin.id).delete()
            db.flush()

    count = 0
    for index, chunk in enumerate(chunks):
        embedding = _embed_text(chunk)
        if use_db and pin is not None:
            db.add(
                ProjectDocumentChunk(
                    pin_id=pin.id,
                    path=uri,
                    chunk_index=index,
                    content=chunk,
                    embedding_json=json.dumps(embedding),
                )
            )
        _IN_MEMORY_VAULT.append(
            MemoryChunk(
                path=uri,
                chunk_index=index,
                content=chunk,
                embedding=embedding,
                domain=domain,
            )
        )
        count += 1

    if use_db:
        db.commit()

    return count


def clear_in_memory_vault() -> None:
    """Clears all ephemeral in-memory vault chunks."""
    global _IN_MEMORY_VAULT
    _IN_MEMORY_VAULT = []


def get_vault_stats() -> dict[str, Any]:
    """Returns real-time diagnostics of the in-memory SIMD vault."""
    domains: dict[str, int] = {"tech": 0, "science": 0, "finance": 0, "general": 0}
    ai_memories = 0
    web_memories = 0
    workspace_chunks = 0

    for ch in _IN_MEMORY_VAULT:
        domains[ch.domain] = domains.get(ch.domain, 0) + 1
        if ch.path.startswith("ai://"):
            ai_memories += 1
        elif ch.path.startswith("web://"):
            web_memories += 1
        else:
            workspace_chunks += 1

    return {
        "total_chunks": len(_IN_MEMORY_VAULT),
        "ai_memory_chunks": ai_memories,
        "web_memory_chunks": web_memories,
        "workspace_chunks": workspace_chunks,
        "domains": domains,
        "simd_accelerated": _IS_NATIVE_LOADED,
    }


def build_context_block(chunks: list[RetrievedChunk]) -> str:
    if not chunks:
        return ""

    sections = []
    for chunk in chunks:
        sections.append(f"[{chunk.path} | score={chunk.score:.3f}]\n{chunk.content[:1000]}")
    return "\n\n".join(sections)
