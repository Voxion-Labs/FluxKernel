from __future__ import annotations

import difflib
import json
import shutil
import subprocess
import threading
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.tools.file_manager import WORKSPACE_DIR

_SANDBOXES_ROOT = WORKSPACE_DIR / ".flux_sandboxes"
_REGISTRY_FILE = _SANDBOXES_ROOT / "registry.json"
_LOCK = threading.RLock()

# Internal files/folders excluded from sandbox mirroring
_EXCLUDED_NAMES = {
    ".flux_snapshots",
    ".flux_sandboxes",
    ".flux_temp",
    ".git",
    "__pycache__",
    ".pytest_cache",
    ".DS_Store",
}


@dataclass
class SandboxMetadata:
    task_id: str
    branch_name: str
    base_branch: str
    sandbox_path: str
    mode: str  # "worktree" | "mirror"
    status: str  # "active" | "merged" | "aborted"
    created_at: str
    files_modified: list[str] = field(default_factory=list)


def _ensure_storage() -> None:
    _SANDBOXES_ROOT.mkdir(parents=True, exist_ok=True)
    if not _REGISTRY_FILE.is_file():
        _REGISTRY_FILE.write_text("[]", encoding="utf-8")


def _read_registry() -> list[dict[str, Any]]:
    _ensure_storage()
    try:
        data = json.loads(_REGISTRY_FILE.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else []
    except Exception:
        return []


def _save_registry(entries: list[dict[str, Any]]) -> None:
    _ensure_storage()
    try:
        _REGISTRY_FILE.write_text(json.dumps(entries, indent=2), encoding="utf-8")
    except Exception:
        pass


def _is_git_available() -> bool:
    return shutil.which("git") is not None


def _get_git_repo_root(path: Path) -> Path | None:
    if not _is_git_available():
        return None
    try:
        res = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            cwd=path,
            capture_output=True,
            text=True,
            check=False,
        )
        if res.returncode == 0 and res.stdout.strip():
            return Path(res.stdout.strip()).resolve()
    except Exception:
        pass
    return None


def _get_current_git_branch(repo_root: Path) -> str:
    try:
        res = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=False,
        )
        if res.returncode == 0 and res.stdout.strip():
            return res.stdout.strip()
    except Exception:
        pass
    return "main"


class GitSandboxManager:
    """
    Manages isolated task branches and sandboxed workspace environments.
    Guarantees that mutations made by an autonomous directive are kept
    in an isolated branch sandbox until explicitly approved at the diff gate.
    """

    @classmethod
    def create_sandbox(
        cls,
        task_id: str,
        base_branch: str | None = None,
        target_dir: Path | None = None,
    ) -> SandboxMetadata:
        """Initializes an isolated task branch and working sandbox."""
        with _LOCK:
            _ensure_storage()
            clean_id = task_id.strip().replace(" ", "_")
            if not clean_id.startswith("task-"):
                clean_id = f"task-{clean_id}"

            branch_name = f"flux/{clean_id}"
            root = target_dir or WORKSPACE_DIR
            sandboxes_base = (root / ".flux_sandboxes") if target_dir else _SANDBOXES_ROOT
            sandbox_dir = sandboxes_base / clean_id
            sandbox_dir.mkdir(parents=True, exist_ok=True)

            repo_root = _get_git_repo_root(root)
            actual_base = base_branch or (
                _get_current_git_branch(repo_root) if repo_root else "main"
            )

            mode = "mirror"

            # Attempt Git Worktree initialization if repository is available
            if repo_root and _is_git_available():
                try:
                    wt_target = sandbox_dir / "worktree"
                    if wt_target.exists():
                        shutil.rmtree(wt_target, ignore_errors=True)

                    res = subprocess.run(
                        ["git", "worktree", "add", "-b", branch_name, str(wt_target), actual_base],
                        cwd=repo_root,
                        capture_output=True,
                        text=True,
                        check=False,
                    )
                    if res.returncode == 0:
                        mode = "worktree"
                        sandbox_dir = wt_target
                except Exception:
                    mode = "mirror"

            # Fallback: Mirror existing workspace files into the sandbox directory
            if mode == "mirror":
                for item in root.iterdir():
                    if item.name in _EXCLUDED_NAMES:
                        continue
                    dest = sandbox_dir / item.name
                    if item.is_dir():
                        shutil.copytree(
                            item,
                            dest,
                            dirs_exist_ok=True,
                            ignore=shutil.ignore_patterns(*_EXCLUDED_NAMES),
                        )
                    elif item.is_file():
                        shutil.copy2(item, dest)

            meta = SandboxMetadata(
                task_id=clean_id,
                branch_name=branch_name,
                base_branch=actual_base,
                sandbox_path=str(sandbox_dir.resolve()),
                mode=mode,
                status="active",
                created_at=datetime.now(timezone.utc).isoformat(),
                files_modified=[],
            )

            # Update registry
            registry = _read_registry()
            # Remove prior entry if matching task_id exists
            registry = [e for e in registry if e.get("task_id") != clean_id]
            registry.append(asdict(meta))
            _save_registry(registry)

            # Emit telemetry event
            try:
                from app.core.telemetry import emit_telemetry

                emit_telemetry(
                    source="git_sandbox",
                    level="INFO",
                    message=f"Created isolated branch {branch_name} ({mode}) for {clean_id}",
                    metadata={"task_id": clean_id, "branch": branch_name, "mode": mode},
                )
            except Exception:
                pass

            return meta

    @classmethod
    def write_file(cls, task_id: str, rel_path: str, content: str) -> Path:
        """Writes a proposed file directly into the isolated task sandbox."""
        with _LOCK:
            meta = cls.get_sandbox(task_id)
            if not meta or meta.status != "active":
                raise ValueError(f"No active sandbox found for task {task_id}")

            sandbox_root = Path(meta.sandbox_path)
            clean_rel = Path(rel_path).as_posix().lstrip("/\\")

            target = (sandbox_root / clean_rel).resolve()
            if not target.is_relative_to(sandbox_root):
                raise PermissionError("Path traversal outside sandbox boundary is blocked.")

            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")

            if clean_rel not in meta.files_modified:
                meta.files_modified.append(clean_rel)
                registry = _read_registry()
                for e in registry:
                    if e.get("task_id") == meta.task_id:
                        e["files_modified"] = meta.files_modified
                _save_registry(registry)

            return target

    @classmethod
    def get_diff(cls, task_id: str, base_dir: Path | None = None) -> dict[str, Any]:
        """Calculates unified diff between original workspace and the isolated task branch."""
        with _LOCK:
            meta = cls.get_sandbox(task_id)
            if not meta:
                return {"task_id": task_id, "files": [], "total_additions": 0, "total_deletions": 0}

            base_root = base_dir or WORKSPACE_DIR
            sandbox_root = Path(meta.sandbox_path)

            diff_files = []
            total_adds = 0
            total_dels = 0

            # Scan all files modified in the sandbox
            all_paths = set(meta.files_modified)
            if sandbox_root.exists():
                for p in sandbox_root.rglob("*"):
                    if p.is_file():
                        try:
                            rel = p.relative_to(sandbox_root)
                            if not any(part in _EXCLUDED_NAMES for part in rel.parts):
                                all_paths.add(rel.as_posix())
                        except ValueError:
                            pass
                        except ValueError:
                            pass

            for rel_str in sorted(all_paths):
                orig_file = base_root / rel_str
                sand_file = sandbox_root / rel_str

                old_text = (
                    orig_file.read_text(encoding="utf-8", errors="ignore")
                    if orig_file.is_file()
                    else ""
                )
                new_text = (
                    sand_file.read_text(encoding="utf-8", errors="ignore")
                    if sand_file.is_file()
                    else ""
                )

                if old_text == new_text:
                    continue

                old_lines = old_text.splitlines(keepends=True)
                new_lines = new_text.splitlines(keepends=True)

                patch_lines = list(
                    difflib.unified_diff(
                        old_lines,
                        new_lines,
                        fromfile=f"a/{rel_str}",
                        tofile=f"b/{rel_str}",
                    )
                )

                adds = sum(
                    1 for line in patch_lines if line.startswith("+") and not line.startswith("+++")
                )
                dels = sum(
                    1 for line in patch_lines if line.startswith("-") and not line.startswith("---")
                )

                total_adds += adds
                total_dels += dels

                diff_files.append(
                    {
                        "path": rel_str,
                        "old_content": old_text,
                        "new_content": new_text,
                        "additions": adds,
                        "deletions": dels,
                        "patch": "".join(patch_lines),
                    }
                )

            return {
                "task_id": meta.task_id,
                "branch_name": meta.branch_name,
                "base_branch": meta.base_branch,
                "status": meta.status,
                "mode": meta.mode,
                "files": diff_files,
                "total_additions": total_adds,
                "total_deletions": total_dels,
            }

    @classmethod
    def merge_sandbox(cls, task_id: str, dest_dir: Path | None = None) -> dict[str, Any]:
        """
        Applies changes from the isolated task branch into the base workspace.
        This completes the review and approval gate transaction.
        """
        with _LOCK:
            meta = cls.get_sandbox(task_id)
            if not meta:
                raise ValueError(f"No sandbox found for task {task_id}")

            target_root = dest_dir or WORKSPACE_DIR
            sandbox_root = Path(meta.sandbox_path)

            applied_files = []
            if sandbox_root.exists():
                for p in sandbox_root.rglob("*"):
                    if p.is_file():
                        rel = p.relative_to(sandbox_root)
                        if not any(part in _EXCLUDED_NAMES for part in rel.parts):
                            dest_file = target_root / rel
                            dest_file.parent.mkdir(parents=True, exist_ok=True)
                            shutil.copy2(p, dest_file)
                            applied_files.append(rel.as_posix())

            # Cleanup worktree or directory
            repo_root = _get_git_repo_root(target_root)
            if meta.mode == "worktree" and repo_root and _is_git_available():
                try:
                    subprocess.run(
                        ["git", "worktree", "remove", "--force", str(sandbox_root)],
                        cwd=repo_root,
                        capture_output=True,
                        check=False,
                    )
                    # Delete the merged task branch
                    subprocess.run(
                        ["git", "branch", "-D", meta.branch_name],
                        cwd=repo_root,
                        capture_output=True,
                        check=False,
                    )
                except Exception:
                    pass
            else:
                shutil.rmtree(sandbox_root, ignore_errors=True)

            meta.status = "merged"
            registry = _read_registry()
            for e in registry:
                if e.get("task_id") == meta.task_id:
                    e["status"] = "merged"
            _save_registry(registry)

            # Telemetry
            try:
                from app.core.telemetry import emit_telemetry

                emit_telemetry(
                    source="git_sandbox",
                    level="SUCCESS",
                    message=f"Merged task branch {meta.branch_name} ({len(applied_files)} files)",
                    metadata={
                        "task_id": meta.task_id,
                        "branch": meta.branch_name,
                        "files_count": len(applied_files),
                    },
                )
            except Exception:
                pass

            return {
                "status": "merged",
                "task_id": meta.task_id,
                "branch_name": meta.branch_name,
                "files_applied": applied_files,
            }

    @classmethod
    def abort_sandbox(cls, task_id: str, dest_dir: Path | None = None) -> dict[str, Any]:
        """
        Rejects and purges the isolated task branch without touching the base workspace.
        Leaves original files 100% intact.
        """
        with _LOCK:
            meta = cls.get_sandbox(task_id)
            if not meta:
                return {"status": "aborted", "task_id": task_id}

            target_root = dest_dir or WORKSPACE_DIR
            sandbox_root = Path(meta.sandbox_path)

            repo_root = _get_git_repo_root(target_root)
            if meta.mode == "worktree" and repo_root and _is_git_available():
                try:
                    subprocess.run(
                        ["git", "worktree", "remove", "--force", str(sandbox_root)],
                        cwd=repo_root,
                        capture_output=True,
                        check=False,
                    )
                    subprocess.run(
                        ["git", "branch", "-D", meta.branch_name],
                        cwd=repo_root,
                        capture_output=True,
                        check=False,
                    )
                except Exception:
                    pass
            else:
                shutil.rmtree(sandbox_root, ignore_errors=True)

            meta.status = "aborted"
            registry = _read_registry()
            for e in registry:
                if e.get("task_id") == meta.task_id:
                    e["status"] = "aborted"
            _save_registry(registry)

            # Telemetry
            try:
                from app.core.telemetry import emit_telemetry

                emit_telemetry(
                    source="git_sandbox",
                    level="WARN",
                    message=f"Aborted and purged task branch {meta.branch_name}",
                    metadata={"task_id": meta.task_id, "branch": meta.branch_name},
                )
            except Exception:
                pass

            return {
                "status": "aborted",
                "task_id": meta.task_id,
                "branch_name": meta.branch_name,
            }

    @classmethod
    def get_sandbox(cls, task_id: str) -> SandboxMetadata | None:
        """Retrieves metadata for a specific task sandbox."""
        clean_id = task_id.strip().replace(" ", "_")
        if not clean_id.startswith("task-"):
            clean_id = f"task-{clean_id}"

        registry = _read_registry()
        for e in registry:
            if e.get("task_id") == clean_id:
                return SandboxMetadata(**e)
        return None

    @classmethod
    def list_sandboxes(cls) -> list[dict[str, Any]]:
        """Returns all recorded sandbox transactions."""
        return _read_registry()
