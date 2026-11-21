import types

import chromadb
import pytest

from kb.config import KBConfig
from kb.embedder import HashEmbedder
from kb.indexer import index_vault
from kb.store import EmbedderMismatch, KnowledgeStore, create_client


def test_index_then_search(store, vault):
    report = index_vault(vault, store)
    assert report.added == 6 and store.count() == report.chunks
    hits = store.search("віртуальні вузли консистентного хешування", k=3)
    assert hits[0].path == "Шардинг/Хеш-партиціювання.md"
    assert hits[0].distance <= 0.9


def test_client_follows_chroma_host(tmp_path, monkeypatch):
    calls = []

    def fake_persistent(path):
        calls.append(("persistent", path))
        return "persistent-client"

    def fake_http(host, port):
        calls.append(("http", host, port))
        return "http-client"

    monkeypatch.setattr(chromadb, "PersistentClient", fake_persistent)
    monkeypatch.setattr(chromadb, "HttpClient", fake_http)

    local = KBConfig(vault_path=tmp_path, chroma_path=tmp_path / "db")
    remote = KBConfig(vault_path=tmp_path, chroma_path=tmp_path / "db",
                      chroma_host="localhost", chroma_port=8000)
    assert create_client(local) == "persistent-client"
    assert create_client(remote) == "http-client"
    assert calls == [("persistent", str(tmp_path / "db")),
                     ("http", "localhost", 8000)]


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
