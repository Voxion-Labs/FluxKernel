"""Unit tests for the Python C ABI Native Bridge."""

import sys
from pathlib import Path

# Add engine directory to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core import native_bridge


def test_native_version():
    version = native_bridge.get_native_version()
    assert version is not None
    assert len(version) > 0
    print(f"Version: {version} (Native loaded: {native_bridge.is_native_loaded()})")


def test_compute():
    result = native_bridge.compute(6, 7)
    assert result == 42


def test_sandbox_query():
    available = native_bridge.is_sandbox_available()
    assert isinstance(available, bool)


def test_diff_distance():
    assert native_bridge.calculate_diff_distance("alpha", "alpha") == 0
    assert native_bridge.calculate_diff_distance("alpha", "alphb") == 1
    assert native_bridge.calculate_diff_distance("alpha", "alph") == 1


def test_vector_dot():
    vec_a = [1.0, 2.0, 3.0]
    vec_b = [4.0, 5.0, 6.0]
    # 1*4 + 2*5 + 3*6 = 4 + 10 + 18 = 32.0
    dot = native_bridge.vector_dot_product(vec_a, vec_b)
    assert abs(dot - 32.0) < 0.001


def test_path_safety():
    base = Path(__file__).resolve().parent
    safe_child = base / "child.txt"
    unsafe_escape = base / ".." / ".." / "escape.txt"

    assert native_bridge.verify_path_safe(base, safe_child) is True
    assert native_bridge.verify_path_safe(base, unsafe_escape) is False


if __name__ == "__main__":
    test_native_version()
    test_compute()
    test_sandbox_query()
    test_diff_distance()
    test_vector_dot()
    test_path_safety()
    print("All native bridge tests passed!")
