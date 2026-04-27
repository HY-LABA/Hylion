#!/bin/bash
# Compare what changed after an update (default: HEAD@{1} -> HEAD).
# Read-only diagnostics for superproject and lerobot submodule pointer/content.

set -euo pipefail

BASE_REF="${1:-HEAD@{1}}"
TARGET_REF="${2:-HEAD}"

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/../../.." && pwd)"
ROOT_GIT_DIR="$(git -C "$PROJECT_DIR" rev-parse --show-toplevel)"

# Derive the default submodule path from this project location (e.g. smolVLA/docs/reference/lerobot).
PROJECT_REL="${PROJECT_DIR#"$ROOT_GIT_DIR"/}"
if [[ "$PROJECT_DIR" == "$ROOT_GIT_DIR" ]]; then
    PROJECT_REL=""
fi
DEFAULT_SUBMODULE_PATH="${PROJECT_REL:+$PROJECT_REL/}docs/reference/lerobot"

resolve_submodule_path() {
    if git -C "$ROOT_GIT_DIR" ls-tree HEAD "$DEFAULT_SUBMODULE_PATH" 2>/dev/null | awk '{print $1}' | grep -q '^160000$'; then
        echo "$DEFAULT_SUBMODULE_PATH"
        return
    fi

    if git -C "$ROOT_GIT_DIR" ls-tree HEAD "smolVLA/lerobot" 2>/dev/null | awk '{print $1}' | grep -q '^160000$'; then
        echo "smolVLA/lerobot"
        return
    fi

    if git -C "$ROOT_GIT_DIR" ls-tree HEAD "lerobot" 2>/dev/null | awk '{print $1}' | grep -q '^160000$'; then
        echo "lerobot"
        return
    fi

    # Fallback: first gitlink that ends with lerobot.
    git -C "$ROOT_GIT_DIR" ls-tree -r HEAD | awk '$1=="160000" && $4 ~ /(^|\/)lerobot$/ {print $4; exit}'
}

SUBMODULE_PATH="$(resolve_submodule_path || true)"

require_ref() {
    local ref="$1"
    if ! git -C "$ROOT_GIT_DIR" rev-parse --verify -q "$ref" >/dev/null; then
        echo "[error] ref not found in superproject: $ref"
        echo "        Try: ./check_update_diff.sh HEAD~1 HEAD"
        exit 1
    fi
}

show_section() {
    local title="$1"
    echo
    echo "===== ${title} ====="
}

require_ref "$BASE_REF"
require_ref "$TARGET_REF"

BASE_COMMIT="$(git -C "$ROOT_GIT_DIR" rev-parse "$BASE_REF")"
TARGET_COMMIT="$(git -C "$ROOT_GIT_DIR" rev-parse "$TARGET_REF")"

cd "$ROOT_GIT_DIR"

echo "[info] compare range: ${BASE_REF} -> ${TARGET_REF}"
echo "[info] repo: $ROOT_GIT_DIR"
echo "[info] project: $PROJECT_DIR"
if [[ -n "$SUBMODULE_PATH" ]]; then
    echo "[info] submodule path: $SUBMODULE_PATH"
else
    echo "[warn] could not auto-detect lerobot submodule path"
fi

show_section "Superproject Commits"
if git log --oneline "${BASE_REF}..${TARGET_REF}" | sed -n '1,30p' | grep -q .; then
    git log --oneline "${BASE_REF}..${TARGET_REF}" | sed -n '1,30p'
else
    echo "(no commit differences in superproject)"
fi

show_section "Superproject Changed Files"
if git diff --name-status "$BASE_REF" "$TARGET_REF" | sed -n '1,80p' | grep -q .; then
    git diff --name-status "$BASE_REF" "$TARGET_REF" | sed -n '1,80p'
else
    echo "(no file differences in superproject)"
fi

show_section "Submodule Pointer Change (lerobot)"
if [[ -z "$SUBMODULE_PATH" ]]; then
    echo "(lerobot submodule path not found in current superproject)"
elif git diff --submodule=log "$BASE_COMMIT" "$TARGET_COMMIT" -- "$SUBMODULE_PATH" | grep -q .; then
    git diff --submodule=log "$BASE_COMMIT" "$TARGET_COMMIT" -- "$SUBMODULE_PATH"
else
    echo "(lerobot pointer unchanged in superproject)"
fi

if [[ -z "$SUBMODULE_PATH" ]]; then
    show_section "Submodule Commit Analysis"
    echo "(skipped: lerobot submodule path unresolved)"
    exit 0
fi

BASE_SUB="$(git rev-parse "${BASE_COMMIT}:${SUBMODULE_PATH}" 2>/dev/null || true)"
TARGET_SUB="$(git rev-parse "${TARGET_COMMIT}:${SUBMODULE_PATH}" 2>/dev/null || true)"

if [[ ! "$BASE_SUB" =~ ^[0-9a-f]{40}$ || ! "$TARGET_SUB" =~ ^[0-9a-f]{40}$ ]]; then
    show_section "Submodule Commit Analysis"
    echo "(unable to resolve lerobot gitlink SHAs for one of the refs)"
    exit 0
fi

if [[ -z "$BASE_SUB" || -z "$TARGET_SUB" ]]; then
    show_section "Submodule Commit Analysis"
    echo "(unable to resolve lerobot gitlink in one of the refs)"
    exit 0
fi

if [[ "$BASE_SUB" == "$TARGET_SUB" ]]; then
    show_section "Submodule Commit Analysis"
    echo "(lerobot commit unchanged: ${TARGET_SUB})"
    exit 0
fi

if [[ ! -d "$ROOT_GIT_DIR/$SUBMODULE_PATH/.git" && ! -f "$ROOT_GIT_DIR/$SUBMODULE_PATH/.git" ]]; then
    show_section "Submodule Commit Analysis"
    echo "(lerobot repository not initialized locally)"
    echo "Run: git submodule update --init $SUBMODULE_PATH"
    exit 0
fi

show_section "lerobot Commits (${BASE_SUB:0:8}..${TARGET_SUB:0:8})"
if git -C "$ROOT_GIT_DIR/$SUBMODULE_PATH" log --oneline --decorate "${BASE_SUB}..${TARGET_SUB}" | sed -n '1,50p' | grep -q .; then
    git -C "$ROOT_GIT_DIR/$SUBMODULE_PATH" log --oneline --decorate "${BASE_SUB}..${TARGET_SUB}" | sed -n '1,50p'
else
    echo "(no visible commit log in local lerobot clone for this range)"
fi

show_section "lerobot Changed Files"
if git -C "$ROOT_GIT_DIR/$SUBMODULE_PATH" diff --name-status "$BASE_SUB" "$TARGET_SUB" | sed -n '1,120p' | grep -q .; then
    git -C "$ROOT_GIT_DIR/$SUBMODULE_PATH" diff --name-status "$BASE_SUB" "$TARGET_SUB" | sed -n '1,120p'
else
    echo "(no changed files in lerobot range)"
fi

show_section "lerobot pyproject.toml Diff"
if git -C "$ROOT_GIT_DIR/$SUBMODULE_PATH" diff "$BASE_SUB" "$TARGET_SUB" -- pyproject.toml | grep -q .; then
    git -C "$ROOT_GIT_DIR/$SUBMODULE_PATH" diff "$BASE_SUB" "$TARGET_SUB" -- pyproject.toml
else
    echo "(pyproject.toml unchanged in this lerobot range)"
fi
