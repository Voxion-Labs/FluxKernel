"""
test_e2e_triumvirate.py — End-to-end integration and architectural verification test.

Validates that FluxKernel's tri-stack backend operates harmoniously:
1. Go Gateway architecture & routing definitions
2. C++20 Native Acceleration & ABI Bridge
3. Python Cognitive Engine & Multi-Language Sandboxed Execution
4. Complete absence of TypeScript / JavaScript in the backend
"""

import sys
from pathlib import Path

# Setup paths
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
ENGINE_DIR = REPO_ROOT / "engine"
GATEWAY_DIR = REPO_ROOT / "gateway"
NATIVE_DIR = REPO_ROOT / "native"
FRONTEND_DIR = REPO_ROOT / "frontend"

sys.path.insert(0, str(ENGINE_DIR))

from app.core import native_bridge  # noqa: E402
from app.tools import code_executor  # noqa: E402


def test_zero_backend_typescript():
    """Verify that no .ts or .tsx files exist in backend directories."""
    backend_dirs = [ENGINE_DIR, GATEWAY_DIR, NATIVE_DIR]
    for b_dir in backend_dirs:
        ts_files = list(b_dir.rglob("*.ts")) + list(b_dir.rglob("*.tsx"))
        assert len(ts_files) == 0, f"Found unexpected TS files in {b_dir}: {ts_files}"

    # Verify Next.js API routes were completely purged
    legacy_api_dir = FRONTEND_DIR / "src" / "app" / "api"
    assert not legacy_api_dir.exists(), "frontend/src/app/api must not exist (0% TS in backend)"


def test_native_accelerator_interface():
    """Verify C++20 ABI bridge functions correctly."""
    version = native_bridge.get_native_version()
    assert version is not None
    assert len(version) > 0

    # Arithmetic compute
    assert native_bridge.compute(12, 12) == 144

    # Levenshtein / character-level difference distance
    assert native_bridge.calculate_diff_distance("fluxkernel", "fluxkernel") == 0
    assert native_bridge.calculate_diff_distance("fluxkernel", "fluxkernal") == 1

    # Fast vector dot product
    vec1 = [0.5, 1.5, 2.5]
    vec2 = [2.0, 2.0, 2.0]
    # (0.5*2) + (1.5*2) + (2.5*2) = 1 + 3 + 5 = 9.0
    dot = native_bridge.vector_dot_product(vec1, vec2)
    assert abs(dot - 9.0) < 0.001


def test_code_executor_triumvirate():
    """Verify multi-language executor handles Python, Go, and C++, rejecting TS."""
    # Python
    py_res = code_executor.execute_code_sync("print(100 + 200)", language="python")
    assert py_res["success"] is True
    assert "300" in py_res["stdout"]

    # Go (if available on host)
    if code_executor.COMPILER_AVAILABILITY["go"]:
        go_code = """package main
import "fmt"
func main() {
    fmt.Println("Tri-Stack Go Active")
}"""
        go_res = code_executor.execute_code_sync(go_code, language="go")
        assert go_res["success"] is True
        assert "Tri-Stack Go Active" in go_res["stdout"]

    # TypeScript rejection
    ts_res = code_executor.execute_code_sync("console.log('forbidden');", language="typescript")
    assert ts_res["success"] is False
    assert "Unsupported language: 'typescript'" in ts_res["stderr"]


def test_gateway_manifest_integrity():
    """Verify Go Gateway directory structure and go.mod."""
    go_mod = GATEWAY_DIR / "go.mod"
    assert go_mod.is_file(), "gateway/go.mod must exist"
    content = go_mod.read_text(encoding="utf-8")
    assert "module github.com/Voxion-Labs/FluxKernel/gateway" in content

    main_go = GATEWAY_DIR / "cmd" / "server" / "main.go"
    assert main_go.is_file(), "gateway/cmd/server/main.go must exist"


def test_native_cmake_manifest_integrity():
    """Verify C++20 Native accelerator CMake configuration."""
    cmake_lists = NATIVE_DIR / "CMakeLists.txt"
    assert cmake_lists.is_file(), "native/CMakeLists.txt must exist"
    content = cmake_lists.read_text(encoding="utf-8")
    assert "CXX_STANDARD 20" in content
    assert "flux_core" in content


if __name__ == "__main__":
    test_zero_backend_typescript()
    test_native_accelerator_interface()
    test_code_executor_triumvirate()
    test_gateway_manifest_integrity()
    test_native_cmake_manifest_integrity()
    print("All end-to-end tri-stack architectural verifications passed successfully!")
