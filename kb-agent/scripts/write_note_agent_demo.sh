#!/usr/bin/env bash
# Крок 17: агент сам викликає write_note на прохання людини; підтвердження — «y».
set -euo pipefail
cd "$(dirname "$0")/.."

vault=$(grep '^OBSIDIAN_VAULT=' .env | cut -d= -f2- | tr -d '"')
trap 'rm -rf "$vault/Inbox"' EXIT

printf 'y\n' | uv run python main.py \
  "Збережи нотатку «Кошик і read-your-writes» про те, що для кошика обрано read-your-writes" \
  --allow-write
