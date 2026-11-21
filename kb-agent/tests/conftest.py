"""Спільні фікстури: тестове сховище і Chroma у тимчасовому каталозі."""

import shutil
from pathlib import Path

import chromadb
import pytest

from kb.embedder import HashEmbedder
from kb.indexer import index_vault
from kb.store import KnowledgeStore
from kb.tools import KnowledgeTools

FIXTURE_VAULT = Path(__file__).parent / "vault"


@pytest.fixture
def vault(tmp_path) -> Path:
    target = tmp_path / "vault"
    shutil.copytree(FIXTURE_VAULT, target)
    return target


@pytest.fixture
def store(tmp_path) -> KnowledgeStore:
    client = chromadb.PersistentClient(path=str(tmp_path / "chroma"))
    return KnowledgeStore(HashEmbedder(), "test_kb", client=client)


@pytest.fixture
def tools(vault, store) -> KnowledgeTools:
    index_vault(vault, store)
    return KnowledgeTools(store, vault, top_k=3, max_distance=0.9)
