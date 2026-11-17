"""
native_bridge.py — Python C ABI bridge to the FluxKernel C++20 native engine.

Provides zero-overhead bare-metal execution for:
  - High-speed vector dot product (accelerating embeddings/cosine similarity)
  - Memory-level difference calculation (accelerating DiffBatch generation)
  - Canonical sandbox path traversal validation & write protection
  - Destructive command & shell injection interception
  - Hardware arithmetic compute kernels

Transparent fallback: If the native shared library (libflux_core.so / flux_core.dll)
is not yet compiled on the local system, fully equivalent pure Python implementations
are used automatically without throwing errors.
"""

from __future__ import annotations

import ctypes
import sys
from pathlib import Path
from typing import Sequence

# ── Library Discovery ─────────────────────────────────────────────────────────

_SEARCH_PATHS = [
    # Production Docker / Linux standard location
    Path("/usr/local/lib/libflux_core.so"),
    # Local build directories relative to repo root
    Path(__file__).resolve().parent.parent.parent.parent / "native" / "build" / "libflux_core.so",
    Path(__file__).resolve().parent.parent.parent.parent
    / "native"
    / "build"
    / "Release"
    / "flux_core.dll",
    Path(__file__).resolve().parent.parent.parent.parent / "native" / "build" / "flux_core.dll",
    Path(__file__).resolve().parent.parent.parent.parent
    / "native"
    / "build"
    / "libflux_core.dylib",
    Path("libflux_core.so"),
    Path("flux_core.dll"),
]

_lib = None
_IS_NATIVE_LOADED = False

for candidate in _SEARCH_PATHS:
    if candidate.is_file():
        try:
            _lib = ctypes.CDLL(str(candidate))
            _IS_NATIVE_LOADED = True
            break
        except Exception:
            _lib = None

# ── C ABI Bindings ────────────────────────────────────────────────────────────

if _lib is not None:
    try:
        # const char* flux_version(void)
        _lib.flux_version.restype = ctypes.c_char_p
        _lib.flux_version.argtypes = []

        # int32_t flux_compute(int32_t a, int32_t b)
        _lib.flux_compute.restype = ctypes.c_int32
        _lib.flux_compute.argtypes = [ctypes.c_int32, ctypes.c_int32]

        # int32_t flux_sandbox_available(void)
        _lib.flux_sandbox_available.restype = ctypes.c_int32
        _lib.flux_sandbox_available.argtypes = []

        # int64_t flux_diff_distance(const char* a, size_t len_a, const char* b, size_t len_b)
        _lib.flux_diff_distance.restype = ctypes.c_int64
        _lib.flux_diff_distance.argtypes = [
            ctypes.c_char_p,
            ctypes.c_size_t,
            ctypes.c_char_p,
            ctypes.c_size_t,
        ]

        # float flux_fast_vector_dot(const float* a, const float* b, size_t len)
        _lib.flux_fast_vector_dot.restype = ctypes.c_float
        _lib.flux_fast_vector_dot.argtypes = [
            ctypes.POINTER(ctypes.c_float),
            ctypes.POINTER(ctypes.c_float),
            ctypes.c_size_t,
        ]

        # int32_t flux_sandbox_verify_path(const char* base_dir, const char* target_path)
        _lib.flux_sandbox_verify_path.restype = ctypes.c_int32
        _lib.flux_sandbox_verify_path.argtypes = [ctypes.c_char_p, ctypes.c_char_p]

        # int32_t flux_sandbox_verify_write(const char* base_dir, const char* target_path)
        _lib.flux_sandbox_verify_write.restype = ctypes.c_int32
        _lib.flux_sandbox_verify_write.argtypes = [ctypes.c_char_p, ctypes.c_char_p]

        # int32_t flux_security_verify_command(const char* cmd_str)
        _lib.flux_security_verify_command.restype = ctypes.c_int32
        _lib.flux_security_verify_command.argtypes = [ctypes.c_char_p]
    except AttributeError:
        _IS_NATIVE_LOADED = False
        _lib = None


# ── Public API Functions ──────────────────────────────────────────────────────


def is_native_loaded() -> bool:
    """Return True if C++ shared library is actively linked, False if using Python fallback."""
    return _IS_NATIVE_LOADED


def get_native_version() -> str:
    """Return the native engine version string."""
    if _IS_NATIVE_LOADED and _lib is not None:
        raw = _lib.flux_version()
        return raw.decode("utf-8") if raw else "Unknown"
    return "FluxKernel-Native-PythonFallback-v0.4.0"


def compute(a: int, b: int) -> int:
    """Execute high-speed arithmetic kernel."""
    if _IS_NATIVE_LOADED and _lib is not None:
        return int(_lib.flux_compute(ctypes.c_int32(a), ctypes.c_int32(b)))
    return a * b


def is_sandbox_available() -> bool:
    """Check if native OS process sandboxing primitives are available."""
    if _IS_NATIVE_LOADED and _lib is not None:
        return bool(_lib.flux_sandbox_available())
    return sys.platform in ("linux", "win32")


def calculate_diff_distance(a: str, b: str) -> int:
    """Compute difference score between two strings using native memory diffing or fallback."""
    if _IS_NATIVE_LOADED and _lib is not None:
        bytes_a = a.encode("utf-8")
        bytes_b = b.encode("utf-8")
        return int(
            _lib.flux_diff_distance(
                bytes_a,
                len(bytes_a),
                bytes_b,
                len(bytes_b),
            )
        )

    # Pure Python fallback
    if a == b:
        return 0
    min_len = min(len(a), len(b))
    diff = sum(1 for i in range(min_len) if a[i] != b[i])
    diff += abs(len(a) - len(b))
    return diff


def vector_dot_product(vec_a: Sequence[float], vec_b: Sequence[float]) -> float:
    """Compute high-speed dot product of two float vectors (for embedding cosine similarity)."""
    if len(vec_a) != len(vec_b):
        raise ValueError(f"Vector dimensions mismatch: {len(vec_a)} vs {len(vec_b)}")

    length = len(vec_a)
    if length == 0:
        return 0.0

    if _IS_NATIVE_LOADED and _lib is not None:
        arr_type = ctypes.c_float * length
        c_a = arr_type(*vec_a)
        c_b = arr_type(*vec_b)
        return float(_lib.flux_fast_vector_dot(c_a, c_b, ctypes.c_size_t(length)))

    # Pure Python fallback
    return float(sum(x * y for x, y in zip(vec_a, vec_b, strict=False)))


def verify_path_safe(base_dir: str | Path, target_path: str | Path) -> bool:
    """Verify that target_path resides safely within base_dir without path traversal escapes."""
    base_str = str(base_dir)
    target_str = str(target_path)

    if _IS_NATIVE_LOADED and _lib is not None:
        result = _lib.flux_sandbox_verify_path(
            base_str.encode("utf-8"),
            target_str.encode("utf-8"),
        )
        return result == 1

    # Pure Python fallback
    try:
        base_resolved = Path(base_str).resolve()
        target_resolved = (
            (base_resolved / target_str).resolve()
            if not Path(target_str).is_absolute()
            else Path(target_str).resolve()
        )
        target_resolved.relative_to(base_resolved)
        return True
    except (ValueError, Exception):
        return False


def verify_write_safe(base_dir: str | Path, target_path: str | Path) -> bool:
    """
    Verify that target_path is safe to write:
    1. Resides strictly inside base_dir.
    2. Does NOT touch internal protected directories (.git, .flux_snapshots) or sensitive keys (.env).
    """
    if not verify_path_safe(base_dir, target_path):
        return False

    base_str = str(base_dir)
    target_str = str(target_path)

    if _IS_NATIVE_LOADED and _lib is not None:
        result = _lib.flux_sandbox_verify_write(
            base_str.encode("utf-8"),
            target_str.encode("utf-8"),
        )
        return result == 1

    # Pure Python fallback
    try:
        base_resolved = Path(base_str).resolve()
        target_resolved = (
            (base_resolved / target_str).resolve()
            if not Path(target_str).is_absolute()
            else Path(target_str).resolve()
        )
        rel = target_resolved.relative_to(base_resolved).as_posix().lower()

        # Disallow writing to protected internal partitions
        protected_prefixes = (
            ".git",
            ".flux_snapshots",
            ".env",
        )
        for p in protected_prefixes:
            if rel == p or rel.startswith(f"{p}/"):
                return False

        return True
    except (ValueError, Exception):
        return False


def verify_command_safe(cmd_str: str) -> bool:
    """
    Scan an arbitrary shell or subprocess command string to detect destructive operations
    (root directory deletion, disk formatting, fork-bombs, poweroff, etc.).
    Returns True if command is permitted, False if dangerous.
    """
    if not cmd_str:
        return True

    if _IS_NATIVE_LOADED and _lib is not None:
        result = _lib.flux_security_verify_command(cmd_str.encode("utf-8"))
        return result == 1

    # Pure Python fallback
    lower_cmd = cmd_str.lower()
    dangerous_patterns = (
        "rm -rf /",
        "rm -rf /*",
        "rm -fr /",
        "rmdir /s /q c:\\",
        "rd /s /q c:\\",
        "del /f /s /q c:\\",
        "del /s /q c:\\",
        ":(){ :|:& };:",
        "%0|%0",
        "mkfs",
        "format c:",
        "format d:",
        "diskpart",
        "fdisk",
        "dd if=/dev/zero",
        "dd if=/dev/urandom",
        "chmod -r 777 /",
        "icacls c:\\ /grant",
        "shutdown -s",
        "shutdown /s",
        "init 0",
        "systemctl poweroff",
    )
    for pattern in dangerous_patterns:
        if pattern in lower_cmd:
            return False

    return True
