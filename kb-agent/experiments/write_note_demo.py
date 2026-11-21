"""Крок 17: дія write_note. Показує три випадки: заборонена за замовчуванням,
відхилена людиною і підтверджена — нотатка створюється лише в Inbox/.

Підтвердження читається зі стандартного входу, тому скрипт обгорнуто в
scripts/write_note_demo.sh: там кожен запуск отримує свою відповідь «y» чи «n».
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from kb.config import load_config
from kb.embedder import make_embedder
from kb.store import KnowledgeStore, create_client
from kb.tools import KnowledgeTools


def main() -> None:
    parser = argparse.ArgumentParser(description="Демонстрація дії write_note")
    parser.add_argument("--title", default="Перевірка дії write_note")
    parser.add_argument("--body", default="Опис тестової нотатки.\n\n## Розділ\n\nТекст розділу.\n")
    parser.add_argument("--allow-write", action="store_true")
    args = parser.parse_args()

    cfg = load_config()
    store = KnowledgeStore(make_embedder(cfg.embed_model, cfg.embed_dim),
                           cfg.collection, client=create_client(cfg))
    tools = KnowledgeTools(store, cfg.vault_path, writable=args.allow_write)
    print(tools.write_note(args.title, args.body, "тест"))


if __name__ == "__main__":
    main()
