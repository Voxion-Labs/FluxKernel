#!/usr/bin/env bash
# ==============================================================================
# FluxKernel 1-Click Production Launcher (Linux & macOS)
# Approach A: Embedded Local Daemon + Native OS WebView
# ==============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

GATEWAY_PORT="${PORT:-8080}"
ENGINE_PORT="${ENGINE_PORT:-8000}"
NO_BROWSER="${NO_BROWSER:-0}"

# Terminal Colors
CYAN='\033[1;36m'
GREEN='\033[1;32m'
YELLOW='\033[1;33m'
RED='\033[1;31m'
NC='\033[0m'

echo -e "\n${CYAN}==============================================================================${NC}"
echo -e " FluxKernel Sovereign Autonomous Operating System"
echo -e " Tri-Stack Sovereign Architecture (Go + C++20 + Python)"
echo -e " Approach A: Embedded Local Daemon + Native OS WebView"
echo -e "${CYAN}==============================================================================${NC}"

# 1. Check Python
PYTHON_BIN=""
if command -v python3 >/dev/null 2>&1; then
    PYTHON_BIN="python3"
elif command -v python >/dev/null 2>&1; then
    PYTHON_BIN="python"
else
    echo -e "${RED}[ERROR] Python 3.10+ is required but not found in PATH.${NC}" >&2
    exit 1
fi
PY_VER=$($PYTHON_BIN -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}')")
echo -e "  ${GREEN}[OK]${NC} Python runtime detected: v${PY_VER}"

# 2. Check Go
if ! command -v go >/dev/null 2>&1; then
    echo -e "${RED}[ERROR] Go 1.22+ is required but not found in PATH.${NC}" >&2
    exit 1
fi
GO_VER=$(go version)
echo -e "  ${GREEN}[OK]${NC} Go runtime detected: ${GO_VER}"

# 3. Optional C++ Native Acceleration
OS_NAME="$(uname -s)"
LIB_EXT="so"
if [ "${OS_NAME}" = "Darwin" ]; then
    LIB_EXT="dylib"
fi

if command -v g++ >/dev/null 2>&1 || command -v clang++ >/dev/null 2>&1; then
    CXX_COMPILER="g++"
    if command -v clang++ >/dev/null 2>&1; then
        CXX_COMPILER="clang++"
    fi
    mkdir -p native/build
    SO_PATH="native/build/libflux_core.${LIB_EXT}"
    if [ ! -f "${SO_PATH}" ]; then
        echo -e "  ${YELLOW}[INFO]${NC} Compiling C++20 SIMD vector accelerator with ${CXX_COMPILER}..."
        $CXX_COMPILER -O3 -fPIC -shared -std=c++20 native/src/flux_core.cpp -I native/include -o "${SO_PATH}" 2>/dev/null || true
        if [ -f "${SO_PATH}" ]; then
            echo -e "  ${GREEN}[OK]${NC} Native C++ accelerator compiled: ${SO_PATH}"
        else
            echo -e "  ${YELLOW}[INFO]${NC} Native compilation skipped; Python transparent fallback active."
        fi
    else
        echo -e "  ${GREEN}[OK]${NC} Native C++ accelerator ready: ${SO_PATH}"
    fi
fi

# 4. Compile Go Gateway to Static Binary if needed
mkdir -p bin
GATEWAY_BIN="bin/fluxkernel-gateway"
if [ ! -f "${GATEWAY_BIN}" ]; then
    echo -e "  ${YELLOW}[INFO]${NC} Compiling sovereign Go Gateway binary (embedded templates & static assets)..."
    (
        cd gateway
        go build -ldflags="-s -w" -o "../${GATEWAY_BIN}" ./cmd/server
    )
    if [ -f "${GATEWAY_BIN}" ]; then
        chmod +x "${GATEWAY_BIN}"
        echo -e "  ${GREEN}[OK]${NC} Go Gateway compiled successfully: ${GATEWAY_BIN}"
    fi
else
    echo -e "  ${GREEN}[OK]${NC} Static Go Gateway binary ready: ${GATEWAY_BIN}"
fi

# 5. Launch Background Daemons with Clean Shutdown Trap
PYTHON_PID=""
GATEWAY_PID=""

cleanup() {
    echo -e "\n${YELLOW}Gracefully stopping FluxKernel daemons...${NC}"
    if [ -n "${GATEWAY_PID}" ] && kill -0 "${GATEWAY_PID}" 2>/dev/null; then
        kill "${GATEWAY_PID}" 2>/dev/null || true
    fi
    if [ -n "${PYTHON_PID}" ] && kill -0 "${PYTHON_PID}" 2>/dev/null; then
        kill "${PYTHON_PID}" 2>/dev/null || true
    fi
    wait 2>/dev/null || true
    echo -e "${GREEN}All FluxKernel daemons stopped cleanly. Zero background footprint.${NC}"
    exit 0
}
trap cleanup EXIT INT TERM

echo -e "  ${YELLOW}[INFO]${NC} [1/3] Starting Python Cognitive Engine on port ${ENGINE_PORT}..."
(
    cd engine
    exec $PYTHON_BIN -m uvicorn app.main:app --host 127.0.0.1 --port "${ENGINE_PORT}" --log-level warning
) >/dev/null 2>&1 &
PYTHON_PID=$!

echo -e "  ${YELLOW}[INFO]${NC} [2/3] Starting Go Gateway & Mission Control UI on port ${GATEWAY_PORT}..."
export PORT="${GATEWAY_PORT}"
export ENGINE_URL="http://127.0.0.1:${ENGINE_PORT}"
"${GATEWAY_BIN}" >/dev/null 2>&1 &
GATEWAY_PID=$!

# 6. Health Probe Loop
echo -e "  ${YELLOW}[INFO]${NC} [3/3] Performing tri-stack health probe..."
MAX_RETRIES=15
READY=0
for i in $(seq 1 $MAX_RETRIES); do
    sleep 0.5
    if curl -s -f "http://127.0.0.1:${GATEWAY_PORT}/healthz" >/dev/null 2>&1; then
        READY=1
        break
    fi
done

if [ "$READY" -eq 1 ]; then
    echo -e "  ${GREEN}[OK]${NC} Tri-Stack Orchestration Verified: All services OPERATIONAL!"
else
    echo -e "  ${YELLOW}[INFO]${NC} Gateway initializing; proceeding to launch webview."
fi

# 7. LAN IP Detection for Mobile / Cross-Device
LAN_IP="127.0.0.1"
if [ "${OS_NAME}" = "Darwin" ]; then
    LAN_IP=$(ipconfig getifaddr en0 2>/dev/null || echo "127.0.0.1")
else
    LAN_IP=$(hostname -I 2>/dev/null | awk '{print $1}' || echo "127.0.0.1")
fi

LOCAL_URL="http://127.0.0.1:${GATEWAY_PORT}/dashboard"
LAN_URL="http://${LAN_IP}:${GATEWAY_PORT}/dashboard"

echo -e "\n${CYAN}==============================================================================${NC}"
echo -e " FluxKernel Live Endpoints"
echo -e "  🖥  Local Desktop Console: ${GREEN}${LOCAL_URL}${NC}"
echo -e "  📱  Mobile / LAN Console:   ${CYAN}${LAN_URL}${NC}"
echo -e "  ⚡  API Gateway Proxy:      http://127.0.0.1:${GATEWAY_PORT}"
echo -e "  🧠  Cognitive Engine:       http://127.0.0.1:${ENGINE_PORT}"
echo -e "${CYAN}==============================================================================${NC}"

# 8. Launch Native OS WebView / Browser (Approach A)
if [ "${NO_BROWSER}" -eq 0 ]; then
    if [ "${OS_NAME}" = "Darwin" ]; then
        if [ -d "/Applications/Google Chrome.app" ]; then
            echo -e "  ${YELLOW}[INFO]${NC} Launching Chrome App Mode (native window)..."
            open -na "Google Chrome" --args "--app=${LOCAL_URL}" "--window-size=1366,860" || open "${LOCAL_URL}"
        else
            open "${LOCAL_URL}"
        fi
    else
        if command -v google-chrome >/dev/null 2>&1; then
            google-chrome "--app=${LOCAL_URL}" "--window-size=1366,860" >/dev/null 2>&1 &
        elif command -v chromium >/dev/null 2>&1; then
            chromium "--app=${LOCAL_URL}" "--window-size=1366,860" >/dev/null 2>&1 &
        elif command -v xdg-open >/dev/null 2>&1; then
            xdg-open "${LOCAL_URL}" >/dev/null 2>&1 &
        fi
    fi
fi

echo -e "\nPress [Ctrl+C] to gracefully terminate FluxKernel services."
wait "${GATEWAY_PID}" "${PYTHON_PID}"
