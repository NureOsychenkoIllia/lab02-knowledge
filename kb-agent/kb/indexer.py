"""Інкрементна індексація сховища: python -m kb.indexer [--rebuild]"""

import argparse
import time
from dataclasses import dataclass
from pathlib import Path

from .chunker import chunk_note
from .store import KnowledgeStore
from .vault import iter_notes


@dataclass
class IndexReport:
    added: int = 0
    updated: int = 0
    unchanged: int = 0
    deleted: int = 0
    chunks: int = 0

    def __str__(self) -> str:
        return (f"added {self.added}, updated {self.updated}, "
                f"unchanged {self.unchanged}, deleted {self.deleted}, "
                f"chunks written {self.chunks}")


def index_vault(vault: Path, store: KnowledgeStore, max_chars: int = 900) -> IndexReport:
    report = IndexReport()
    indexed = store.indexed_hashes()
    seen: set[str] = set()
    for note in iter_notes(vault):
        seen.add(note.path)
        if indexed.get(note.path) == note.content_hash:
            report.unchanged += 1
            continue
        chunks = chunk_note(note, max_chars)
        store.replace_note(chunks, note.content_hash, note.tags)
        report.chunks += len(chunks)
        if note.path in indexed:
            report.updated += 1
        else:
            report.added += 1
    for path in set(indexed) - seen:
        store.delete_note(path)
        report.deleted += 1
    return report


def main() -> None:
    from .config import load_config
    from .embedder import GeminiEmbedder

    parser = argparse.ArgumentParser(description="Індексація сховища Obsidian у Chroma")
    parser.add_argument("--rebuild", action="store_true",
                        help="видалити колекцію і проіндексувати заново")
    args = parser.parse_args()

    cfg = load_config()
    embedder = GeminiEmbedder(cfg.embed_model, cfg.embed_dim)

    if args.rebuild:
        import chromadb
        client = chromadb.PersistentClient(path=str(cfg.chroma_path))
        if cfg.collection in [c.name for c in client.list_collections()]:
            client.delete_collection(cfg.collection)
    store = KnowledgeStore(embedder, cfg.collection, cfg.chroma_path)

    started = time.perf_counter()
    report = index_vault(cfg.vault_path, store, cfg.chunk_chars)
    print(f"vault: {cfg.vault_path}")
    print(f"index: {report}")
    print(f"collection '{cfg.collection}': {store.count()} chunks, "
          f"embedding calls: {embedder.calls}, "
          f"time: {time.perf_counter() - started:.1f} s")


if __name__ == "__main__":
    main()
