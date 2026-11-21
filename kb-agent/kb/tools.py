"""Дії агента над базою знань. Повертають рядки-спостереження."""

from pathlib import Path

from .store import KnowledgeStore
from .vault import parse_note, resolve_note_path, strip_wikilinks

NOT_FOUND = "NOT_FOUND"


class KnowledgeTools:
    def __init__(self, store: KnowledgeStore, vault: Path, top_k: int = 4,
                 max_distance: float = 0.40, max_note_chars: int = 4000):
        self.store, self.vault = store, vault
        self.top_k, self.max_distance = top_k, max_distance
        self.max_note_chars = max_note_chars

    def search_knowledge(self, query: str, tag: str | None = None) -> str:
        """Семантичний пошук фрагментів нотаток, найближчих до запиту."""
        hits = self.store.search(query, self.top_k, tag)
        relevant = [h for h in hits if h.distance <= self.max_distance]
        if not relevant:
            best = f"{hits[0].distance:.3f}" if hits else "n/a"
            return (f"{NOT_FOUND}: no notes closer than {self.max_distance} "
                    f"for query '{query}' (best distance: {best}).")
        # Межі <fragment> відділяють дані з нотаток від інструкцій агента
        return "\n".join(
            f'<fragment source="[[{h.title}#{h.heading.split(" > ")[-1]}]]" '
            f'path="{h.path}" distance="{h.distance:.3f}">\n'
            f"{strip_wikilinks(h.text)}\n</fragment>"
            for h in relevant)

    def read_note(self, path: str) -> str:
        """Повний текст нотатки зі сховища (для деталей поза фрагментом)."""
        try:
            file = resolve_note_path(self.vault, path)
        except ValueError as exc:
            return f"ERROR: {exc}"
        except FileNotFoundError:
            return f"{NOT_FOUND}: note '{path}' does not exist."
        note = parse_note(self.vault, file)
        text = strip_wikilinks(note.body).strip()
        if len(text) > self.max_note_chars:
            text = text[:self.max_note_chars] + "\n[...truncated]"
        links = ", ".join(note.links) or "none"
        return (f'<note source="[[{note.title}]]" path="{note.path}" '
                f'tags="{", ".join(note.tags)}" links="{links}">\n{text}\n</note>')


def build_tools() -> KnowledgeTools:
    """Збирає робочі інструменти з параметрів .env."""
    from .config import load_config
    from .embedder import GeminiEmbedder

    from .store import create_client

    cfg = load_config()
    store = KnowledgeStore(GeminiEmbedder(cfg.embed_model, cfg.embed_dim),
                           cfg.collection, client=create_client(cfg))
    return KnowledgeTools(store, cfg.vault_path, cfg.top_k, cfg.max_distance)
