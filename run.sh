#!/usr/bin/env bash
# ==============================================================================
# Voxion Labs - FluxKernel Autonomous Operating System Launcher
# Cross-Platform Linux & macOS Zero-Setup Script
# ==============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [ -f "${SCRIPT_DIR}/scripts/launch.sh" ]; then
    exec "${SCRIPT_DIR}/scripts/launch.sh" "$@"
fi

echo "=============================================================================="
echo " Voxion Labs - FluxKernel Autonomous Operating System"
echo " Tri-Stack Sovereign Architecture (Go + C++20 + Python)"
echo "=============================================================================="
echo ""

# 1. Check Python
PYTHON_CMD=""
if command -v python3 >/dev/null 2>&1; then
    PYTHON_CMD="python3"
elif command -v python >/dev/null 2>&1; then
    PYTHON_CMD="python"
else
    echo "[ERROR] Python 3.10+ is required but not found in PATH." >&2
    exit 1
fi

# 2. Check Go
if ! command -v go >/dev/null 2>&1; then
    echo "[ERROR] Go 1.22+ is required but not found in PATH." >&2
    exit 1
fi

# 3. Optional C++ compilation
if command -v g++ >/dev/null 2>&1 || command -v clang++ >/dev/null 2>&1; then
    CXX_COMPILER="g++"
    if command -v clang++ >/dev/null 2>&1; then
        CXX_COMPILER="clang++"
    fi

    OS_NAME="$(uname -s)"
    LIB_EXT="so"
    if [ "$OS_NAME" = "Darwin" ]; then
        LIB_EXT="dylib"
    fi

    mkdir -p native/build
    if [ ! -f "native/build/libflux_core.${LIB_EXT}" ]; then
        echo "[INFO] Compiling C++ native accelerator with ${CXX_COMPILER}..."
        $CXX_COMPILER -O3 -fPIC -shared -std=c++20 native/src/flux_core.cpp -I native/include -o "native/build/libflux_core.${LIB_EXT}" 2>/dev/null || true
        if [ -f "native/build/libflux_core.${LIB_EXT}" ]; then
            echo "[OK] Native accelerator compiled (native/build/libflux_core.${LIB_EXT})."
        else
            echo "[INFO] C++ compilation skipped; using Python transparent fallback."
        fi
    fi
fi

# Graceful cleanup on SIGINT/SIGTERM
cleanup() {
    echo ""
    echo "[SHUTDOWN] Terminating FluxKernel processes..."
    kill 0 2>/dev/null || true
    wait 2>/dev/null || true
    echo "[SHUTDOWN] All services stopped."
    exit 0
}
trap cleanup EXIT INT TERM

echo "[1/3] Starting FluxKernel Python Brain on port 8000..."
(
    cd engine
    $PYTHON_CMD -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --log-level warning
) &

sleep 2

echo "[2/3] Starting FluxKernel Go Gateway & Web Console on port 8080..."
(
    cd gateway
    go run ./cmd/server
) &

sleep 2

echo "[3/3] Opening Sovereign Web Console..."
URL="http://localhost:8080/dashboard"
if command -v xdg-open >/dev/null 2>&1; then
    xdg-open "$URL" >/dev/null 2>&1 &
elif command -v open >/dev/null 2>&1; then
    open "$URL" >/dev/null 2>&1 &
else
    echo "Please open $URL in your browser."
fi

echo ""
echo "=============================================================================="
echo " FluxKernel is LIVE and operational!"
echo " Web Console: http://localhost:8080/dashboard"
echo " API Gateway: http://localhost:8080"
echo " Brain Engine: http://localhost:8000"
echo ""
echo " Press Ctrl+C to terminate all services."
echo "=============================================================================="
echo ""

wait
