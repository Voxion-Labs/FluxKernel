from __future__ import annotations

import os
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from app.core.project_rag import infer_domain
from app.tools.file_manager import WORKSPACE_DIR

# Partitions and build outputs excluded from search
_EXCLUDED_DIRS = {
    ".git",
    ".flux_snapshots",
    ".flux_temp",
    "__pycache__",
    ".pytest_cache",
    "build",
    "bin",
    ".vscode",
    ".idea",
    "node_modules",
}

# Max file size to scan (1 MB to ensure microsecond responsiveness)
_MAX_FILE_SIZE_BYTES = 1024 * 1024

# Symbol pattern definitions for multi-language detection
_SYMBOL_PATTERNS = [
    re.compile(r"^\s*(?:func|def|class|struct|type|interface)\s+([A-Za-z0-9_]+)", re.MULTILINE),
    re.compile(r"^\s*(?:CREATE\s+TABLE|CREATE\s+INDEX)\s+([A-Za-z0-9_]+)", re.IGNORECASE),
]


@dataclass
class SearchResultItem:
    path: str
    line_number: int
    snippet: str
    context_before: list[str] = field(default_factory=list)
    context_after: list[str] = field(default_factory=list)
    domain: str = "general"
    match_type: str = "exact"  # "file", "symbol", "exact", "token"
    score: float = 0.8


def is_searchable_file(path: Path) -> bool:
    """Checks if a file is safe and eligible for fast workspace indexing."""
    if not path.is_file():
        return False
    try:
        if path.stat().st_size > _MAX_FILE_SIZE_BYTES:
            return False
    except OSError:
        return False

    suffix = path.suffix.lower()
    text_extensions = {
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
        ".md",
        ".txt",
        ".json",
        ".csv",
        ".tsv",
        ".yaml",
        ".yml",
        ".toml",
        ".ini",
        ".cfg",
        ".tex",
        ".latex",
        ".html",
        ".css",
    }
    return suffix in text_extensions


def search_workspace(
    query: str,
    domain: str = "all",
    limit: int = 25,
    target_dir: Path | None = None,
) -> dict[str, Any]:
    """
    Executes a high-speed multi-domain search across workspace files.
    Identifies exact occurrences, symbol declarations, and filenames with
    surrounding context lines and domain taxonomy tagging.
    """
    clean_query = query.strip()
    if not clean_query:
        return {
            "query": "",
            "domain": domain,
            "total_matches": 0,
            "files_matched": 0,
            "domains": {"tech": 0, "science": 0, "finance": 0, "general": 0},
            "results": [],
        }

    root = target_dir or WORKSPACE_DIR
    if not root.exists():
        return {
            "query": clean_query,
            "domain": domain,
            "total_matches": 0,
            "files_matched": 0,
            "domains": {"tech": 0, "science": 0, "finance": 0, "general": 0},
            "results": [],
        }

    query_lower = clean_query.lower()
    query_tokens = [t for t in re.split(r"\W+", query_lower) if t]
    filter_domain = domain.lower() if domain else "all"

    results: list[SearchResultItem] = []
    files_with_matches: set[str] = set()
    domain_counts = {"tech": 0, "science": 0, "finance": 0, "general": 0}

    # Walk workspace directory tree safely
    for dirpath, dirnames, filenames in os.walk(root):
        # Exclude internal partitions in-place to prune subtrees
        dirnames[:] = [d for d in dirnames if d not in _EXCLUDED_DIRS and not d.startswith(".")]

        rel_dir = os.path.relpath(dirpath, root)
        if rel_dir != "." and any(part in _EXCLUDED_DIRS for part in Path(rel_dir).parts):
            continue

        for filename in filenames:
            file_path = Path(dirpath) / filename
            if not is_searchable_file(file_path):
                continue

            try:
                rel_posix = file_path.relative_to(root).as_posix()
            except ValueError:
                rel_posix = file_path.name

            file_domain = infer_domain(rel_posix)
            if filter_domain != "all" and file_domain != filter_domain:
                continue

            # 1. Filename match
            if query_lower in filename.lower():
                score = 1.0 if query_lower == filename.lower() else 0.92
                item = SearchResultItem(
                    path=rel_posix,
                    line_number=1,
                    snippet=f"File: {filename}",
                    domain=file_domain,
                    match_type="file",
                    score=score,
                )
                results.append(item)
                files_with_matches.add(rel_posix)
                domain_counts[file_domain] = domain_counts.get(file_domain, 0) + 1

            # 2. Content lines scan
            try:
                content = file_path.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue

            lines = content.splitlines()
            for idx, line in enumerate(lines):
                line_lower = line.lower()
                line_num = idx + 1

                # Check for symbol declarations
                is_symbol = False
                for sym_re in _SYMBOL_PATTERNS:
                    m = sym_re.search(line)
                    if m and query_lower in m.group(1).lower():
                        is_symbol = True
                        break

                match_found = False
                match_score = 0.0
                match_type = "exact"

                if is_symbol:
                    match_found = True
                    match_score = 0.95
                    match_type = "symbol"
                elif query_lower in line_lower:
                    match_found = True
                    match_score = 0.85
                    match_type = "exact"
                elif query_tokens and all(token in line_lower for token in query_tokens):
                    match_found = True
                    match_score = 0.70
                    match_type = "token"

                if match_found:
                    # Collect 2 lines of surrounding context
                    start_ctx = max(0, idx - 2)
                    end_ctx = min(len(lines), idx + 3)
                    before = lines[start_ctx:idx]
                    after = lines[idx + 1 : end_ctx]

                    item = SearchResultItem(
                        path=rel_posix,
                        line_number=line_num,
                        snippet=line.strip()[:240],
                        context_before=[b.strip()[:200] for b in before],
                        context_after=[a.strip()[:200] for a in after],
                        domain=file_domain,
                        match_type=match_type,
                        score=match_score,
                    )
                    results.append(item)
                    files_with_matches.add(rel_posix)
                    domain_counts[file_domain] = domain_counts.get(file_domain, 0) + 1

    # Sort results by relevance score descending, then by file path
    results.sort(key=lambda r: (-r.score, r.path, r.line_number))

    capped_results = results[:limit]

    return {
        "query": clean_query,
        "domain": filter_domain,
        "total_matches": len(results),
        "files_matched": len(files_with_matches),
        "domains": domain_counts,
        "results": [asdict(r) for r in capped_results],
    }
