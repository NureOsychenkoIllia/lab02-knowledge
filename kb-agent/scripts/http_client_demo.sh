#!/usr/bin/env bash
# Крок 14: Chroma у режимі клієнт-сервер. Сервер піднімається у фоні, оцінювання
# виконується через HttpClient (CHROMA_HOST), після чого сервер зупиняється.
set -euo pipefail
cd "$(dirname "$0")/.."

uv run chroma run --path ./chroma_data --port 8000 > /tmp/chroma_lab02.log 2>&1 &
server=$!
trap 'kill $server 2>/dev/null || true' EXIT

for _ in $(seq 1 40); do
    curl -sf http://localhost:8000/api/v2/heartbeat >/dev/null && break
    sleep 0.5
done

echo "# Chroma server: $(curl -s http://localhost:8000/api/v2/heartbeat)"
echo
echo "# PersistentClient (без CHROMA_HOST)"
uv run python -m kb.inspect --limit 1 | head -3
echo
echo "# HttpClient (CHROMA_HOST=localhost)"
CHROMA_HOST=localhost uv run python -m kb.inspect --limit 1 | head -3
echo
echo "# оцінювання пошуку через сервер"
CHROMA_HOST=localhost uv run python -m eval.eval_retrieval -k 4 | tail -3
