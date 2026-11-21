#!/usr/bin/env bash
# Перегляд колекції у TUI: у Chroma 1.5 шлях до даних передають абсолютним.
set -euo pipefail
cd "$(dirname "$0")/.."
exec uv run chroma browse "${KB_COLLECTION:-obsidian_kb}" --path "$PWD/chroma_data" --theme dark
