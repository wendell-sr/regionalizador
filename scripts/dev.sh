#!/usr/bin/env bash
# Wrapper Unix para o script Python de dev.
# Uso: ./scripts/dev.sh [--install] [--backend] [--frontend] [--port N]

set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec python3 "$SCRIPT_DIR/dev.py" "$@"
