#!/usr/bin/env bash
# Крок 17: дія write_note. Чотири випадки: заборонена без --allow-write,
# відхилена людиною, підтверджена (нотатка з'являється лише в Inbox/)
# і відхилені шляхи, що виходять за межі сховища.
set -euo pipefail
cd "$(dirname "$0")/.."

vault=$(grep '^OBSIDIAN_VAULT=' .env | cut -d= -f2- | tr -d '"')
trap 'rm -rf "$vault/Inbox"' EXIT

echo "# без --allow-write дія заборонена"
uv run python experiments/write_note_demo.py
echo
echo "# людина відповіла «n»"
printf 'n\n' | uv run python experiments/write_note_demo.py --allow-write
echo
echo "# людина відповіла «y»"
printf 'y\n' | uv run python experiments/write_note_demo.py --allow-write
echo
echo "# відхилені назви й повторне створення"
printf 'y\n' | PYTHONPATH=. uv run python - <<'PY'
from kb.config import load_config
from kb.embedder import GeminiEmbedder
from kb.store import KnowledgeStore, create_client
from kb.tools import KnowledgeTools
cfg = load_config()
tools = KnowledgeTools(KnowledgeStore(GeminiEmbedder(cfg.embed_model, cfg.embed_dim),
                        cfg.collection, client=create_client(cfg)), cfg.vault_path,
                        writable=True)
for title in ("../../etc/passwd", "_templates/Шаблон", "Перевірка дії write_note"):
    print(f"{title!r} -> {tools.write_note(title, 'x')}")
PY
echo
echo "# що лежить у папці Inbox"
ls -1 "$vault/Inbox"
