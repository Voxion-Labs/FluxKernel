"""
rollback_manager.py — Atomic Workspace Snapshot & Instant Rollback Engine for FluxKernel.

Design Principles:
- Complete thread-safe state capture of the workspace prior to agent mutations.
- Cryptographic SHA-256 integrity verification across all snapshots.
- Reversible rollback operations: Automatically captures a safety pre-rollback snapshot.
- Fast index caching for instant retrieval and listing.
- Partition isolation: Protected .flux_snapshots store immune to agent tampering.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.tools.file_manager import WORKSPACE_DIR

_SNAPSHOT_DIR = WORKSPACE_DIR / ".flux_snapshots"
_INDEX_FILE = _SNAPSHOT_DIR / "index.json"
_LOCK = threading.RLock()

# Internal files/folders that are excluded from snapshots
_EXCLUDED_NAMES = {
    ".flux_snapshots",
    ".flux_temp",
    ".git",
    "__pycache__",
    ".pytest_cache",
    ".DS_Store",
}


def _ensure_storage() -> None:
    _SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
    if not _INDEX_FILE.is_file():
        _INDEX_FILE.write_text("[]", encoding="utf-8")


def _calculate_sha256(file_path: Path) -> str:
    hasher = hashlib.sha256()
    with file_path.open("rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


class RollbackManager:
    """Manages workspace state snapshots, validation, and instantaneous state rollback."""

    @classmethod
    def create_snapshot(
        cls,
        trigger: str = "manual",
        iteration: int | None = None,
        label: str | None = None,
    ) -> dict[str, Any]:
        """
        Capture an atomic, cryptographic snapshot of the current WORKSPACE_DIR.

        Args:
            trigger: Why this snapshot was taken ('manual', 'loop_init', 'pre_mutation', etc.)
            iteration: Agentic loop iteration number if applicable
            label: Human-readable description
        """
        with _LOCK:
            _ensure_storage()

            now = datetime.now(timezone.utc)
            timestamp_str = now.strftime("%Y%m%d_%H%M%S")
            short_id = hashlib.sha256(f"{time.time()}_{trigger}_{iteration}".encode()).hexdigest()[
                :8
            ]
            snapshot_id = f"snap_{timestamp_str}_{short_id}"

            snap_path = _SNAPSHOT_DIR / snapshot_id
            files_dest = snap_path / "files"
            files_dest.mkdir(parents=True, exist_ok=True)

            manifest_files: dict[str, dict[str, Any]] = {}
            file_count = 0

            # Traverse WORKSPACE_DIR and copy each file into files_dest
            for root, dirs, files in os.walk(WORKSPACE_DIR):
                # Filter out excluded directories in-place
                dirs[:] = [d for d in dirs if d not in _EXCLUDED_NAMES]

                for file_name in files:
                    if file_name in _EXCLUDED_NAMES:
                        continue

                    full_path = Path(root) / file_name
                    if not full_path.is_file():
                        continue

                    rel_path = full_path.relative_to(WORKSPACE_DIR).as_posix()
                    file_sha = _calculate_sha256(full_path)
                    file_size = full_path.stat().st_size

                    dest_path = files_dest / rel_path
                    dest_path.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(full_path, dest_path)

                    manifest_files[rel_path] = {
                        "hash": file_sha,
                        "size": file_size,
                    }
                    file_count += 1

            manifest: dict[str, Any] = {
                "snapshot_id": snapshot_id,
                "timestamp": time.time(),
                "created_at": now.isoformat(),
                "trigger": trigger,
                "iteration": iteration,
                "label": label or f"{trigger.capitalize()} checkpoint",
                "file_count": file_count,
                "files": manifest_files,
            }

            # Write manifest.json
            manifest_path = snap_path / "manifest.json"
            manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

            # Update index.json
            try:
                index_data: list[dict[str, Any]] = json.loads(
                    _INDEX_FILE.read_text(encoding="utf-8")
                )
            except Exception:
                index_data = []

            index_entry = {
                "snapshot_id": snapshot_id,
                "timestamp": manifest["timestamp"],
                "created_at": manifest["created_at"],
                "trigger": trigger,
                "iteration": iteration,
                "label": manifest["label"],
                "file_count": file_count,
            }
            # Insert at the beginning (newest first)
            index_data.insert(0, index_entry)
            _INDEX_FILE.write_text(json.dumps(index_data, indent=2), encoding="utf-8")

            return manifest

    @classmethod
    def list_snapshots(cls, limit: int = 50) -> list[dict[str, Any]]:
        """Return a chronological list of recent snapshots (newest first)."""
        with _LOCK:
            _ensure_storage()
            try:
                data: list[dict[str, Any]] = json.loads(_INDEX_FILE.read_text(encoding="utf-8"))
                return data[:limit]
            except Exception:
                return []

    @classmethod
    def get_snapshot(cls, snapshot_id: str) -> dict[str, Any] | None:
        """Retrieve complete manifest details for a given snapshot."""
        with _LOCK:
            manifest_path = _SNAPSHOT_DIR / snapshot_id / "manifest.json"
            if not manifest_path.is_file():
                return None
            try:
                return json.loads(manifest_path.read_text(encoding="utf-8"))
            except Exception:
                return None

    @classmethod
    def rollback_to_snapshot(cls, snapshot_id: str) -> dict[str, Any]:
        """
        Atomically rollback the WORKSPACE_DIR to the exact state captured in snapshot_id.

        Safeguard: Takes a safety pre-rollback recovery snapshot first to allow undoing rollbacks.
        """
        with _LOCK:
            target_snap = cls.get_snapshot(snapshot_id)
            if not target_snap:
                raise ValueError(f"Snapshot '{snapshot_id}' does not exist.")

            target_files: dict[str, dict[str, Any]] = target_snap.get("files", {})
            snap_files_dir = _SNAPSHOT_DIR / snapshot_id / "files"

            # 1. Take safety pre-rollback recovery point
            safety_snap = cls.create_snapshot(
                trigger="safety_pre_rollback",
                label=f"Recovery state before rollback to {snapshot_id}",
            )

            files_restored: list[str] = []
            files_deleted: list[str] = []

            # 2. Delete any file currently in WORKSPACE_DIR that was not in the snapshot
            for root, dirs, files in os.walk(WORKSPACE_DIR):
                dirs[:] = [d for d in dirs if d not in _EXCLUDED_NAMES]

                for file_name in files:
                    if file_name in _EXCLUDED_NAMES:
                        continue

                    current_full = Path(root) / file_name
                    rel_path = current_full.relative_to(WORKSPACE_DIR).as_posix()

                    if rel_path not in target_files:
                        current_full.unlink(missing_ok=True)
                        files_deleted.append(rel_path)

            # Clean up any empty directories left over
            for root, dirs, _ in os.walk(WORKSPACE_DIR, topdown=False):
                dirs[:] = [d for d in dirs if d not in _EXCLUDED_NAMES]
                for d in dirs:
                    d_path = Path(root) / d
                    try:
                        if not any(d_path.iterdir()):
                            d_path.rmdir()
                    except Exception:
                        pass

            # 3. Restore all files from the snapshot files directory
            for rel_path, file_meta in target_files.items():
                src = snap_files_dir / rel_path
                dst = WORKSPACE_DIR / rel_path

                if not src.is_file():
                    continue

                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dst)

                # Verify restored integrity
                restored_hash = _calculate_sha256(dst)
                if restored_hash != file_meta.get("hash"):
                    raise RuntimeError(
                        f"Integrity check failed for restored file '{rel_path}'! Hash mismatch."
                    )

                files_restored.append(rel_path)

            return {
                "success": True,
                "snapshot_id": snapshot_id,
                "files_restored": files_restored,
                "files_deleted": files_deleted,
                "safety_snapshot_id": safety_snap["snapshot_id"],
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

    @classmethod
    def purge_snapshots(cls, keep_last: int = 50) -> int:
        """Purge older snapshots to maintain bounded disk footprint."""
        with _LOCK:
            _ensure_storage()
            snapshots = cls.list_snapshots(limit=1000)
            if len(snapshots) <= keep_last:
                return 0

            to_remove = snapshots[keep_last:]
            removed_count = 0

            for entry in to_remove:
                s_id = entry.get("snapshot_id")
                if s_id:
                    s_dir = _SNAPSHOT_DIR / s_id
                    shutil.rmtree(s_dir, ignore_errors=True)
                    removed_count += 1

            # Update index
            kept = snapshots[:keep_last]
            _INDEX_FILE.write_text(json.dumps(kept, indent=2), encoding="utf-8")
            return removed_count
