"""Параметри бази знань. Значення читаються з .env, у коді лише типові."""

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class KBConfig:
    vault_path: Path
    chroma_path: Path
    collection: str = "obsidian_kb"
    embed_model: str = "gemini-embedding-001"
    embed_dim: int = 768
    chunk_chars: int = 900
    top_k: int = 4
    max_distance: float = 0.40
    chroma_host: str | None = None
    chroma_port: int = 8000


def load_config() -> KBConfig:
    vault = os.getenv("OBSIDIAN_VAULT")
    if not vault:
        raise RuntimeError("Задайте OBSIDIAN_VAULT у файлі .env")
    vault_path = Path(vault).expanduser().resolve()
    if not vault_path.is_dir():
        raise RuntimeError(f"Сховище не знайдено: {vault_path}")
    return KBConfig(
        vault_path=vault_path,
        chroma_path=Path(os.getenv("CHROMA_PATH", "./chroma_data")).expanduser().resolve(),
        collection=os.getenv("KB_COLLECTION", "obsidian_kb"),
        embed_model=os.getenv("EMBED_MODEL", "gemini-embedding-001"),
        embed_dim=int(os.getenv("EMBED_DIM", "768")),
        chunk_chars=int(os.getenv("CHUNK_CHARS", "900")),
        top_k=int(os.getenv("KB_TOP_K", "4")),
        max_distance=float(os.getenv("KB_MAX_DISTANCE", "0.40")),
        chroma_host=os.getenv("CHROMA_HOST") or None,
        chroma_port=int(os.getenv("CHROMA_PORT", "8000")),
    )
