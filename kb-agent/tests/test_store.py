import chromadb
import pytest

from kb.embedder import HashEmbedder
from kb.indexer import index_vault
from kb.store import EmbedderMismatch, KnowledgeStore


def test_index_then_search(store, vault):
    report = index_vault(vault, store)
    assert report.added == 6 and store.count() == report.chunks
    hits = store.search("віртуальні вузли консистентного хешування", k=3)
    assert hits[0].path == "Шардинг/Хеш-партиціювання.md"
    assert hits[0].distance <= 0.9


def test_incremental_reindex(vault, store):
    index_vault(vault, store)
    assert index_vault(vault, store).unchanged == 6

    note = vault / "Реплікація" / "CRDT.md"
    note.write_text(note.read_text(encoding="utf-8") + "\nНовий абзац.\n",
                    encoding="utf-8")
    (vault / "Шардинг" / "Партиціювання за діапазоном.md").unlink()
    report = index_vault(vault, store)
    assert (report.updated, report.deleted, report.unchanged) == (1, 1, 4)
    assert "Шардинг/Партиціювання за діапазоном.md" not in store.indexed_hashes()


def test_tag_filter(store, vault):
    index_vault(vault, store)
    hits = store.search("хешування", k=5, tag="шардинг")
    assert hits and all(h.path.startswith("Шардинг/") for h in hits)
    assert "Реплікація/CRDT.md" not in {h.path for h in hits}


def test_embedder_mismatch_is_detected(tmp_path):
    client = chromadb.PersistentClient(path=str(tmp_path / "db"))
    KnowledgeStore(HashEmbedder(dim=256), "kb_one", client=client)
    with pytest.raises(EmbedderMismatch):
        KnowledgeStore(HashEmbedder(dim=128), "kb_one", client=client)
