#!/usr/bin/env bash
# Перевірка гігієни репозиторію перед здачею: чисте дерево, ключ і індекс не відстежуються.
set -euo pipefail
cd "$(dirname "$0")/../.."

if [ -z "$(git status --porcelain)" ]; then
    echo "git status: робоче дерево чисте"
else
    git status --short
fi
echo "--- відстежувані файли (перші 12):"
git ls-files | head -12
echo "--- ігнорується:"
git check-ignore kb-agent/.env kb-agent/chroma_data kb-agent/traces
