"""
test_code_executor.py — Test suite for multi-language execution (Python, Go, C++).
Verifies that TypeScript and JavaScript runners have been completely purged
and that native Go and C++ runners execute cleanly.
"""

import sys
from pathlib import Path

# Add engine directory to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.tools.code_executor import (
    COMPILER_AVAILABILITY,
    check_compiler_availability,
    detect_language,
    execute_code_sync,
)


def test_detect_language():
    """Verify supported extensions map to python, cpp, and go, while TS/JS are rejected as unknown."""
    assert detect_language("script.py") == "python"
    assert detect_language("main.go") == "go"
    assert detect_language("fast_core.cpp") == "cpp"
    assert detect_language("legacy.cc") == "cpp"
    assert detect_language("math.c") == "cpp"

    # Purged languages
    assert detect_language("index.ts") == "unknown"
    assert detect_language("Component.tsx") == "unknown"
    assert detect_language("script.js") == "unknown"
    assert detect_language("module.mjs") == "unknown"
    assert detect_language("file.unknown") == "unknown"


def test_compiler_availability_schema():
    """Verify compiler pre-flight only tracks C++ and Go, not node/npm/ts-node."""
    avail = check_compiler_availability()
    assert "g++" in avail
    assert "go" in avail
    assert "node" not in avail
    assert "ts-node" not in avail
    assert "npx" not in avail


def test_typescript_javascript_rejected():
    """Explicitly verify that attempting to execute TypeScript or JavaScript is rejected."""
    ts_res = execute_code_sync("console.log('test');", language="typescript")
    assert not ts_res["success"]
    assert "Unsupported language: 'typescript'" in ts_res["stderr"]

    js_res = execute_code_sync("console.log('test');", language="javascript")
    assert not js_res["success"]
    assert "Unsupported language: 'javascript'" in js_res["stderr"]


def test_python_execution_success():
    """Verify standard Python code executes successfully."""
    code = 'print("FluxKernel Python Executor OK")'
    result = execute_code_sync(code, language="python")
    assert result["success"] is True
    assert "FluxKernel Python Executor OK" in result["stdout"]
    assert result["exit_code"] == 0
    assert result["language"] == "python"


def test_python_execution_error():
    """Verify Python syntax or runtime error returns success=False."""
    code = 'raise RuntimeError("Deliberate error for testing")'
    result = execute_code_sync(code, language="python")
    assert result["success"] is False
    assert "Deliberate error for testing" in result["stderr"]
    assert result["exit_code"] != 0


def test_go_execution():
    """Verify Go execution if go compiler is installed."""
    if not COMPILER_AVAILABILITY["go"]:
        print("Skipping Go execution test (go compiler not available)")
        return

    code = """package main

import "fmt"

func main() {
    fmt.Println("FluxKernel Native Go OK")
}
"""
    result = execute_code_sync(code, language="go")
    assert result["success"] is True, f"Go execution failed: {result}"
    assert "FluxKernel Native Go OK" in result["stdout"]
    assert result["exit_code"] == 0
    assert result["language"] == "go"


def test_go_snippet_auto_wrap():
    """Verify that bare Go print statements are cleanly auto-wrapped in main package."""
    if not COMPILER_AVAILABILITY["go"]:
        print("Skipping Go snippet test (go compiler not available)")
        return

    code = 'fmt.Println("Auto-wrapped Go snippet")'
    result = execute_code_sync(code, language="go")
    assert result["success"] is True, f"Go snippet failed: {result}"
    assert "Auto-wrapped Go snippet" in result["stdout"]
    assert result["exit_code"] == 0


def test_cpp_execution():
    """Verify C++ execution if g++ is installed."""
    if not COMPILER_AVAILABILITY["g++"]:
        print("Skipping C++ execution test (g++ compiler not available)")
        return

    code = """#include <iostream>

int main() {
    std::cout << "FluxKernel Native C++ OK" << std::endl;
    return 0;
}
"""
    result = execute_code_sync(code, language="cpp")
    assert result["success"] is True, f"C++ execution failed: {result}"
    assert "FluxKernel Native C++ OK" in result["stdout"]
    assert result["exit_code"] == 0
    assert result["language"] == "cpp"


if __name__ == "__main__":
    test_detect_language()
    test_compiler_availability_schema()
    test_typescript_javascript_rejected()
    test_python_execution_success()
    test_python_execution_error()
    test_go_execution()
    test_go_snippet_auto_wrap()
    test_cpp_execution()
    print("All code executor tests passed!")
