"""
test_sandbox_security.py — Hardened Sandbox & Process Containment Test Suite.
Verifies that path traversal attacks, protected partition tampering (.git, .flux_snapshots),
and dangerous destructive command injections are strictly blocked.
"""

import sys
from pathlib import Path

# Add engine directory to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.native_bridge import (
    verify_command_safe,
    verify_path_safe,
    verify_write_safe,
)
from app.tools.code_executor import execute_code_sync
from app.tools.file_manager import (
    WORKSPACE_DIR,
    SecurityException,
    get_file_tree,
    read_file,
    write_file,
)


class _AssertRaises:
    """Lightweight assertion context manager that does not depend on external test runners."""

    def __init__(self, expected_exc: type[BaseException]):
        self.expected_exc = expected_exc

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            raise AssertionError(f"Expected exception {self.expected_exc.__name__} was not raised.")
        return issubclass(exc_type, self.expected_exc)


def test_path_traversal_boundaries():
    """Verify that path traversal outside WORKSPACE_DIR is rejected."""
    base = WORKSPACE_DIR
    safe_child = base / "project" / "main.py"
    escape_attempt = base / ".." / "outside_secret.txt"
    root_escape = (
        Path("C:/Windows/System32/cmd.exe") if sys.platform == "win32" else Path("/etc/passwd")
    )

    assert verify_path_safe(base, safe_child) is True
    assert verify_path_safe(base, escape_attempt) is False
    assert verify_path_safe(base, root_escape) is False


def test_protected_partition_write_blocking():
    """Verify write isolation against internal engine partitions (.git, .flux_snapshots, .env)."""
    base = WORKSPACE_DIR
    safe_file = base / "src" / "app.py"
    git_file = base / ".git" / "HEAD"
    snapshot_file = base / ".flux_snapshots" / "snap_1" / "payload.py"
    env_file = base / ".env"

    assert verify_write_safe(base, safe_file) is True
    assert verify_write_safe(base, git_file) is False
    assert verify_write_safe(base, snapshot_file) is False
    assert verify_write_safe(base, env_file) is False


def test_dangerous_command_interception():
    """Verify dangerous shell command patterns are blocked before subprocess execution."""
    safe_cmds = [
        "python main.py",
        "go run cmd/server/main.go",
        "g++ -O3 -std=c++20 main.cpp",
        "echo 'Hello World'",
    ]
    for cmd in safe_cmds:
        assert verify_command_safe(cmd) is True, f"Expected safe command to be permitted: {cmd}"

    destructive_cmds = [
        "rm -rf /",
        "rm -rf /*",
        "rmdir /s /q C:\\",
        "del /f /s /q C:\\Windows",
        ":(){ :|:& };:",
        "%0|%0",
        "mkfs.ext4 /dev/sda1",
        "format C:",
        "dd if=/dev/zero of=/dev/sda",
        "chmod -R 777 /",
    ]
    for cmd in destructive_cmds:
        assert verify_command_safe(cmd) is False, (
            f"Expected destructive command to be blocked: {cmd}"
        )


def test_file_manager_security_exceptions():
    """Verify file_manager raises SecurityException when an agent attempts unauthorized writes."""
    # Attempt writing outside bounds
    with _AssertRaises(SecurityException):
        write_file("../../rogue.txt", "rogue content")

    # Attempt reading outside bounds
    with _AssertRaises(SecurityException):
        read_file("../../outside.txt")

    # Attempt tampering with protected snapshot partition
    with _AssertRaises(SecurityException):
        write_file(".flux_snapshots/snap_test/fake.txt", "tampered content")

    # Attempt tampering with .git
    with _AssertRaises(SecurityException):
        write_file(".git/config", "tampered config")


def test_file_tree_hides_protected_partitions():
    """Verify that get_file_tree hides internal partitions from agent visibility."""
    tree = get_file_tree("")
    tree_names = [node["name"] for node in tree]
    assert ".flux_temp" not in tree_names
    assert ".flux_snapshots" not in tree_names
    assert ".git" not in tree_names


def test_code_executor_sandbox_blocking():
    """Verify execute_code_sync immediately halts destructive command execution."""
    destructive_script = 'import os; os.system("rm -rf /")'
    result = execute_code_sync(destructive_script, language="python")
    assert result["success"] is False
    assert "Execution blocked by FluxKernel Sandbox" in result["stderr"]
    assert result["exit_code"] == 126


if __name__ == "__main__":
    test_path_traversal_boundaries()
    test_protected_partition_write_blocking()
    test_dangerous_command_interception()
    test_file_manager_security_exceptions()
    test_file_tree_hides_protected_partitions()
    test_code_executor_sandbox_blocking()
    print("All Hardened Sandbox security tests passed successfully!")
