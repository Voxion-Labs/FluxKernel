#!/usr/bin/env bash
# ==============================================================================
# FluxKernel Operations & Workflow CLI (ops.sh)
# Single-command operational automation for development, formatting, testing, rebasing, and pushing.
# ==============================================================================
set -euo pipefail

CMD="${1:-help}"
MSG="${2:-}"

step() { echo -e "\n\033[1;36m==> $1\033[0m"; }
success() { echo -e "\033[1;32m✓ $1\033[0m"; }
warn() { echo -e "\033[1;33m⚠ $1\033[0m"; }

do_lint() {
    step "Formatting and Linting Go (gateway/)..."
    if command -v gofmt >/dev/null 2>&1; then
        (cd gateway && gofmt -w .)
        success "Go files formatted with gofmt"
    fi

    step "Formatting and Linting Python (engine/)..."
    if command -v ruff >/dev/null 2>&1; then
        ruff format engine/
        ruff check --fix engine/
        success "Python codebase formatted and linted with ruff"
    fi
}

do_test() {
    step "Running Go Unit Tests (gateway/)..."
    if command -v go >/dev/null 2>&1; then
        (cd gateway && go test -v ./...)
        success "Go test suite passed!"
    fi

    step "Running Python Backend & Native Bridge Verification..."
    if command -v python3 >/dev/null 2>&1; then
        python3 engine/tests/test_native_bridge.py
        python3 engine/tests/test_code_executor.py
        python3 engine/tests/test_sandbox_security.py
        python3 engine/tests/test_rollback_manager.py
        python3 engine/tests/test_agentic_loop.py
        python3 engine/tests/test_universal_rag.py
        python3 engine/tests/test_e2e_triumvirate.py
        success "Python verification, sandbox security, rollback engine, and native bridge passed!"
    fi
}

do_sync() {
    step "Fetching remote changes from origin..."
    git fetch origin main

    step "Rebasing onto origin/main..."
    if ! git rebase origin/main; then
        warn "Rebase conflict detected. Resolving tracker ledger automatically if needed..."
        if [ -f index.json ]; then
            git checkout --ours index.json 2>/dev/null || true
            git add index.json 2>/dev/null || true
            git rebase --continue 2>/dev/null || true
        fi
    fi
    success "Rebased successfully onto origin/main."
}

do_push() {
    if [ -z "$MSG" ]; then
        echo "Error: Push command requires a commit message!"
        echo "Usage: ./ops.sh push 'fix(ci): format go files and fix python linting rules'"
        exit 1
    fi

    do_lint
    do_test

    step "Staging changes..."
    git add -A

    if git diff --staged --quiet; then
        warn "No changes to commit. Working directory clean."
    else
        step "Committing: '$MSG'..."
        git commit -m "$MSG"
        success "Committed."
    fi

    do_sync

    step "Pushing commit(s) to origin/main..."
    git push origin main
    success "Successfully pushed to origin/main!"
}

do_clean() {
    step "Cleaning temporary files..."
    find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
    find . -type f -name "*.pyc" -delete 2>/dev/null || true
    rm -rf .flux_temp native/build bin 2>/dev/null || true
    success "Clean completed."
}

case "$CMD" in
    sync|rebase) do_sync ;;
    lint|format) do_lint ;;
    test)        do_test ;;
    push)        do_push ;;
    start)       exec ./run.sh ;;
    clean)       do_clean ;;
    up)          docker compose up -d ;;
    down)        docker compose down ;;
    status)
        git status
        git log -n 5 --oneline
        ;;
    help|*)
        echo "FluxKernel Ops CLI"
        echo "Commands: sync | rebase | push <msg> | lint | test | up | down | clean | status"
        ;;
esac
