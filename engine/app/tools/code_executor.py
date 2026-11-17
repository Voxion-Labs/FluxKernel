"""
code_executor.py — Multi-language code execution engine for FluxKernel.

Supports:
  - Python  (.py)  — via sys.executable (same interpreter as the server)
  - C++     (.cpp) — via g++ (with C++20 standard support and fallback)
  - Go      (.go)  — via go run (Go 1.22+)

Short tasks run synchronously (execute_code_sync).
Long tasks are dispatched to a Celery worker (dispatch_async_execution)
and tracked by task_id via the /api/v1/tasks/* endpoints.
"""

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Literal

from app.core.native_bridge import verify_command_safe
from app.core.task_queue import celery_app
from app.tools.file_manager import WORKSPACE_DIR

# ── Types ─────────────────────────────────────────────────────────────────────
Language = Literal["python", "cpp", "go", "unknown"]

ExecutionResult = dict  # {success, stdout, stderr, exit_code, language}

# ── Language Detection ────────────────────────────────────────────────────────
_EXTENSION_MAP: dict[str, Language] = {
    ".py": "python",
    ".cpp": "cpp",
    ".cc": "cpp",
    ".cxx": "cpp",
    ".c": "cpp",  # treat as C but compile with g++ (works for C)
    ".go": "go",
}


def detect_language(filename_or_ext: str) -> Language:
    """
    Infer execution language from a filename or bare extension string.
    Returns 'unknown' if the extension is not recognised.
    """
    ext = Path(filename_or_ext).suffix.lower()
    return _EXTENSION_MAP.get(ext, "unknown")


# ── Compiler Pre-flight ───────────────────────────────────────────────────────
def _check_available(cmd: str) -> bool:
    """Return True if `cmd` is found on PATH."""
    return shutil.which(cmd) is not None


COMPILER_AVAILABILITY: dict[str, bool] = {
    "g++": _check_available("g++"),
    "go": _check_available("go"),
}


def check_compiler_availability() -> dict[str, bool]:
    """Return the cached compiler availability map."""
    return COMPILER_AVAILABILITY


# ── Temp-file Helpers ─────────────────────────────────────────────────────────
_TEMP_DIR = WORKSPACE_DIR / ".flux_temp"
_TEMP_DIR.mkdir(parents=True, exist_ok=True)


def _make_temp_file(content: str, suffix: str) -> Path:
    f = tempfile.NamedTemporaryFile(
        dir=str(_TEMP_DIR),
        suffix=suffix,
        delete=False,
        mode="w+",
        encoding="utf-8",
    )
    f.write(content)
    f.close()
    return Path(f.name)


def _cleanup(*paths: Path) -> None:
    for p in paths:
        p.unlink(missing_ok=True)


def _format_timeout_stdout(stdout: str | bytes | None) -> str:
    if stdout is None:
        return ""
    if isinstance(stdout, bytes):
        return stdout.decode("utf-8", errors="replace")
    return str(stdout)


# ── Language Runners ──────────────────────────────────────────────────────────


def _run_python(code: str, timeout: int) -> ExecutionResult:
    src = _make_temp_file(code, ".py")
    try:
        result = subprocess.run(
            [sys.executable, str(src)],
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=str(WORKSPACE_DIR),
        )
        return {
            "success": result.returncode == 0,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "exit_code": result.returncode,
            "language": "python",
        }
    except subprocess.TimeoutExpired as e:
        return {
            "success": False,
            "stdout": _format_timeout_stdout(e.stdout),
            "stderr": f"Execution halted: time limit exceeded ({timeout}s).",
            "exit_code": 124,
            "language": "python",
        }
    finally:
        _cleanup(src)


def _run_cpp(code: str, timeout: int) -> ExecutionResult:
    if not COMPILER_AVAILABILITY["g++"]:
        return {
            "success": False,
            "stdout": "",
            "stderr": "g++ is not available on this system. Install build-essential (Linux) or MinGW (Windows).",
            "exit_code": 127,
            "language": "cpp",
        }

    src = _make_temp_file(code, ".cpp")
    binary_ext = ".exe" if sys.platform == "win32" else ""
    binary = src.with_suffix(binary_ext or ".out")

    try:
        # Step 1: Compile with C++20, falling back to C++17 or C++14 if unsupported by older compiler
        compile_result = subprocess.run(
            ["g++", "-std=c++20", "-Wall", "-o", str(binary), str(src)],
            capture_output=True,
            text=True,
            timeout=60,
            cwd=str(WORKSPACE_DIR),
        )
        if (
            compile_result.returncode != 0
            and "unrecognized command line option" in compile_result.stderr
        ):
            for fallback_std in ["-std=c++17", "-std=c++14"]:
                compile_result = subprocess.run(
                    ["g++", fallback_std, "-Wall", "-o", str(binary), str(src)],
                    capture_output=True,
                    text=True,
                    timeout=60,
                    cwd=str(WORKSPACE_DIR),
                )
                if "unrecognized command line option" not in compile_result.stderr:
                    break

        if compile_result.returncode != 0:
            return {
                "success": False,
                "stdout": "",
                "stderr": f"[Compilation Error]\n{compile_result.stderr}",
                "exit_code": compile_result.returncode,
                "language": "cpp",
            }

        # Step 2: Execute compiled binary
        run_result = subprocess.run(
            [str(binary)],
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=str(WORKSPACE_DIR),
        )
        return {
            "success": run_result.returncode == 0,
            "stdout": run_result.stdout,
            "stderr": run_result.stderr,
            "exit_code": run_result.returncode,
            "language": "cpp",
        }
    except subprocess.TimeoutExpired as e:
        return {
            "success": False,
            "stdout": _format_timeout_stdout(e.stdout),
            "stderr": f"Execution halted: time limit exceeded ({timeout}s).",
            "exit_code": 124,
            "language": "cpp",
        }
    finally:
        _cleanup(src, binary)


def _run_go(code: str, timeout: int) -> ExecutionResult:
    if not COMPILER_AVAILABILITY["go"]:
        return {
            "success": False,
            "stdout": "",
            "stderr": "go compiler is not available on PATH. Ensure Go 1.22+ is installed.",
            "exit_code": 127,
            "language": "go",
        }

    clean_code = code.strip()
    if not clean_code.startswith("package ") and "package main" not in clean_code:
        if "func main" not in clean_code and "import " not in clean_code:
            clean_code = (
                f'package main\n\nimport (\n\t"fmt"\n)\n\nfunc main() {{\n\t{clean_code}\n}}\n'
            )

    src = _make_temp_file(clean_code, ".go")
    try:
        result = subprocess.run(
            ["go", "run", str(src)],
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=str(WORKSPACE_DIR),
        )
        return {
            "success": result.returncode == 0,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "exit_code": result.returncode,
            "language": "go",
        }
    except subprocess.TimeoutExpired as e:
        return {
            "success": False,
            "stdout": _format_timeout_stdout(e.stdout),
            "stderr": f"Execution halted: time limit exceeded ({timeout}s).",
            "exit_code": 124,
            "language": "go",
        }
    finally:
        _cleanup(src)


# ── Public Synchronous Executor ───────────────────────────────────────────────


def execute_code_sync(
    code: str,
    language: Language | str = "python",
    timeout: int = 30,
) -> ExecutionResult:
    """
    Execute code synchronously in the requested language.
    Suitable for tasks expected to complete within `timeout` seconds.
    Supported languages: python, cpp, go.
    """
    # Hardened Sandbox Barrier: intercept destructive system commands
    if not verify_command_safe(code):
        return {
            "success": False,
            "stdout": "",
            "stderr": "Execution blocked by FluxKernel Sandbox: Destructive or unauthorized system operation detected.",
            "exit_code": 126,
            "language": language,
        }

    match language:
        case "python":
            return _run_python(code, timeout)
        case "cpp":
            return _run_cpp(code, timeout)
        case "go":
            return _run_go(code, timeout)
        case _:
            return {
                "success": False,
                "stdout": "",
                "stderr": f"Unsupported language: '{language}'. Supported: python, cpp, go.",
                "exit_code": 1,
                "language": language,
            }


# Backwards-compatible alias used by existing routes
def execute_python_code(code, timeout=10):
    return _run_python(code, timeout)


# ── Celery Async Task (Feature 1) ────────────────────────────────────────────


@celery_app.task(bind=True, name="fluxkernel.execute_code_async")
def execute_code_async_task(
    self,
    code: str,
    language: str = "python",
    timeout: int = 300,
) -> ExecutionResult:
    """
    Celery task wrapper around execute_code_sync.
    Results are stored in Redis and retrievable via the task ID.
    """
    return execute_code_sync(code, language, timeout)


def dispatch_async_execution(
    code: str,
    language: str = "python",
    timeout: int = 300,
) -> str:
    """
    Enqueue code for background execution.

    Returns:
        task_id — use GET /api/v1/tasks/{task_id}/stream to follow progress.
    """
    task = execute_code_async_task.apply_async(
        args=[code],
        kwargs={"language": language, "timeout": timeout},
    )
    return task.id
