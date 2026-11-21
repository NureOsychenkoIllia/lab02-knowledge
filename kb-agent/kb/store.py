"""Векторний індекс на Chroma. Ембединги обчислюємо самі й передаємо явно."""

from dataclasses import dataclass
from pathlib import Path

import chromadb

from .chunker import Chunk
from .embedder import Embedder


class EmbedderMismatch(RuntimeError):
    """Колекцію побудовано іншою моделлю ембедингів: потрібна переіндексація."""


@dataclass
class Hit:
    path: str
    title: str
    heading: str
    text: str
    distance: float


def create_client(cfg) -> chromadb.ClientAPI:
    """PersistentClient для одного процесу, HttpClient коли задано CHROMA_HOST."""
    if cfg.chroma_host:
        return chromadb.HttpClient(host=cfg.chroma_host, port=cfg.chroma_port)
    return chromadb.PersistentClient(path=str(cfg.chroma_path))


class KnowledgeStore:
    def __init__(self, embedder: Embedder, collection: str = "obsidian_kb",
                 path: Path | None = None, client=None):
        self.embedder = embedder
        self.client = client or chromadb.PersistentClient(path=str(path))
        self.name = collection
        self.col = self.client.get_or_create_collection(
            name=collection,
            embedding_function=None,
            configuration={"hnsw": {"space": "cosine"}},
            metadata={"embedder": embedder.name},
        )
        built_with = (self.col.metadata or {}).get("embedder")
        if built_with != embedder.name:
            raise EmbedderMismatch(
                f"collection '{collection}' was built with {built_with}, "
                f"current embedder is {embedder.name}; rebuild the index")

    def count(self) -> int:
        return self.col.count()

    def indexed_hashes(self) -> dict[str, str]:
        """{шлях нотатки: хеш вмісту} для інкрементної індексації."""
        data = self.col.get(include=["metadatas"])
        return {m["path"]: m["note_hash"] for m in data["metadatas"]}

    def replace_note(self, chunks: list[Chunk], note_hash: str,
                     tags: list[str]) -> None:
        if not chunks:
            return
        self.delete_note(chunks[0].path)
        metadatas = []
        for c in chunks:
            meta = {"path": c.path, "title": c.title, "heading": c.heading,
                    "ordinal": c.ordinal, "note_hash": note_hash}
            if tags:
                meta["tags"] = tags
            metadatas.append(meta)
        self.col.upsert(
            ids=[c.id for c in chunks],
            embeddings=self.embedder.embed_documents([c.embed_text for c in chunks]),
            documents=[c.text for c in chunks],
            metadatas=metadatas,
        )

    def delete_note(self, path: str) -> None:
        self.col.delete(where={"path": path})

    def search(self, query: str, k: int = 4, tag: str | None = None) -> list[Hit]:
        if self.count() == 0:
            return []
        result = self.col.query(
            query_embeddings=[self.embedder.embed_query(query)],
            n_results=min(k, self.count()),
            where={"tags": {"$contains": tag}} if tag else None,
            include=["documents", "metadatas", "distances"],
        )
        return [
            Hit(path=m["path"], title=m["title"], heading=m["heading"],
                text=doc, distance=float(d))
            for doc, m, d in zip(result["documents"][0], result["metadatas"][0],
                                 result["distances"][0])
        ]

    def reset(self) -> None:
        """Видаляє колекцію й одразу створює її знову з тими самими параметрами."""
        self.client.delete_collection(self.name)
        self.col = self.client.create_collection(
            name=self.name,
            embedding_function=None,
            configuration={"hnsw": {"space": "cosine"}},
            metadata={"embedder": self.embedder.name},
        )
