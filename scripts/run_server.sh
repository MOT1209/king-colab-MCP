#!/usr/bin/env bash
# Convenience launcher: creates a venv on first run, installs the package,
# then starts the MCP server over stdio (or $MCP_TRANSPORT if set).
set -euo pipefail
cd "$(dirname "$0")/.."

if [ ! -d .venv ]; then
    python3 -m venv .venv
fi
# shellcheck disable=SC1091
source .venv/bin/activate
pip install -q --upgrade pip
pip install -q -e .

exec google-colab-mcp "$@"
