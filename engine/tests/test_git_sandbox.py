from __future__ import annotations

import sys
import tempfile
from pathlib import Path

# Add engine directory to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.git_sandbox import GitSandboxManager


def test_sandbox_lifecycle_mirror():
    with tempfile.TemporaryDirectory() as tmp_dir:
        root = Path(tmp_dir)

        # Create original workspace files
        (root / "main.py").write_text("print('original')", encoding="utf-8")
        (root / "data.csv").write_text("id,val\n1,100\n", encoding="utf-8")

        task_id = "test-alpha-99"

        # 1. Create sandbox
        meta = GitSandboxManager.create_sandbox(task_id=task_id, target_dir=root)
        assert meta.task_id == f"task-{task_id}"
        assert meta.branch_name == f"flux/task-{task_id}"
        assert meta.status == "active"
        sandbox_path = Path(meta.sandbox_path)
        assert sandbox_path.exists()

        # 2. Write file inside sandbox
        GitSandboxManager.write_file(
            task_id=task_id,
            rel_path="main.py",
            content="print('mutated in sandbox')",
        )
        GitSandboxManager.write_file(
            task_id=task_id,
            rel_path="new_module.py",
            content="# New module",
        )

        # Verify original workspace remains 100% untouched
        assert (root / "main.py").read_text() == "print('original')"
        assert not (root / "new_module.py").exists()

        # 3. Check diff
        diff_res = GitSandboxManager.get_diff(task_id=task_id, base_dir=root)
        assert diff_res["task_id"] == f"task-{task_id}"
        assert len(diff_res["files"]) >= 2
        assert diff_res["total_additions"] > 0

        # 4. Merge sandbox
        merge_res = GitSandboxManager.merge_sandbox(task_id=task_id, dest_dir=root)
        assert merge_res["status"] == "merged"
        assert (root / "main.py").read_text() == "print('mutated in sandbox')"
        assert (root / "new_module.py").exists()


def test_sandbox_abort():
    with tempfile.TemporaryDirectory() as tmp_dir:
        root = Path(tmp_dir)
        (root / "critical.py").write_text("PRISTINE_VALUE = 42", encoding="utf-8")

        task_id = "test-beta-abort"
        meta = GitSandboxManager.create_sandbox(task_id=task_id, target_dir=root)

        # Mutate inside sandbox
        GitSandboxManager.write_file(
            task_id=task_id,
            rel_path="critical.py",
            content="PRISTINE_VALUE = 0  # Broken mutation",
        )

        # Abort sandbox
        abort_res = GitSandboxManager.abort_sandbox(task_id=task_id, dest_dir=root)
        assert abort_res["status"] == "aborted"

        # Verify original file is 100% untouched
        assert (root / "critical.py").read_text() == "PRISTINE_VALUE = 42"


def test_branches_api_endpoints():
    try:
        from fastapi.testclient import TestClient
        from app.main import app

        with TestClient(app) as client:
            # 1. List branches
            res = client.get("/api/v1/branches")
            assert res.status_code == 200

            # 2. Create branch
            create_payload = {"task_id": "api-test-42"}
            res_create = client.post("/api/v1/branches/create", json=create_payload)
            assert res_create.status_code == 200
            data = res_create.json()
            assert data["status"] == "created"
            assert "flux/task-api-test-42" in data["branch_name"]

            # 3. Get diff
            res_diff = client.get("/api/v1/branches/task-api-test-42/diff")
            assert res_diff.status_code == 200

            # 4. Abort
            res_abort = client.post("/api/v1/branches/task-api-test-42/abort")
            assert res_abort.status_code == 200
            assert res_abort.json()["status"] == "aborted"
    except ImportError:
        pass


if __name__ == "__main__":
    test_sandbox_lifecycle_mirror()
    test_sandbox_abort()
    test_branches_api_endpoints()
    print("All Isolated Git Branching Sandbox unit tests passed successfully!")
