"""Крок 13: порівняння трьох моделей ембедингів на своєму контрольному наборі.

Для кожної моделі — окрема колекція, власна індексація сховища й оцінювання
hit@4, MRR і кількості хибних прийняттів на порозі KB_MAX_DISTANCE.

Запуск: uv run python experiments/compare_embeddings.py [--models ...]
"""

import argparse
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from eval.eval_retrieval import SET_PATH, evaluate
from kb.chunker import chunk_note
from kb.config import load_config
from kb.embedder import make_embedder
from kb.store import KnowledgeStore
from kb.vault import iter_notes

MODELS = [
    "all-MiniLM-L6-v2",
    "gemini-embedding-001",
    "gemini-embedding-2",
]


def index(vault: Path, store: KnowledgeStore, max_chars: int) -> int:
    """Повна індексація сховища для однієї моделі; колекція створюється з нуля."""
    if store.col.count():
        store.reset()
    written = 0
    for note in iter_notes(vault):
        chunks = chunk_note(note, max_chars)
        store.replace_note(chunks, note.content_hash, note.tags)
        written += len(chunks)
    return written


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--models", nargs="*", default=MODELS)
    parser.add_argument("-k", type=int, default=4)
    args = parser.parse_args()

    cfg = load_config()
    cases = json.loads(SET_PATH.read_text(encoding="utf-8"))
    rows = []
    for name in args.models:
        embedder = make_embedder(name, cfg.embed_dim)
        collection = f"cmp_{name.replace('.', '_').replace('-', '_')}"
        store = KnowledgeStore(embedder, collection, cfg.chroma_path)
        started = time.perf_counter()
        count = index(cfg.vault_path, store, cfg.chunk_chars)
        seconds = time.perf_counter() - started
        report = evaluate(store, cases, args.k, cfg.max_distance)
        row = {"model": embedder.name, "collection": collection, "chunks": count,
               "dim": embedder.dim, "index_seconds": round(seconds, 1),
               "embedding_calls": embedder.calls,
               "hit_at_k": report["hit_at_k"], "mrr": report["mrr"],
               "false_accepts": report["out_of_scope_accepted"],
               "rows": report["rows"]}
        rows.append(row)
        print(f"{embedder.name:28} chunks={count} hit@{args.k}={row['hit_at_k']} "
              f"MRR={row['mrr']} false={row['false_accepts']} "
              f"time={row['index_seconds']}s")

    out = Path("experiments/results/embeddings.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    merged = {}
    if out.exists():
        for row in json.loads(out.read_text(encoding="utf-8")):
            merged[row["model"]] = row
    for row in rows:
        merged[row["model"]] = row
    out.write_text(json.dumps(list(merged.values()), ensure_ascii=False, indent=2),
                   encoding="utf-8")


if __name__ == "__main__":
    main()
