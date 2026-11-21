"""Дії агента над базою знань. Повертають рядки-спостереження."""

import re
from collections.abc import Callable
from pathlib import Path

from .store import KnowledgeStore
from .vault import parse_note, resolve_note_path, strip_wikilinks

NOT_FOUND = "NOT_FOUND"
INBOX = "Inbox"
TITLE = re.compile(r"^[^\n]{1,80}$")

# Підтвердження людиною; у тестах його замінює сценарій
ConfirmFn = Callable[[str], bool]


def ask_confirmation(question: str) -> bool:
    """Підтвердження в терміналі; без TTY вважаємо, що людина не підтвердила."""
    print(question)
    try:
        return input("Підтвердити? [y/N] ").strip().lower() in {"y", "yes", "так"}
    except EOFError:
        return False


class KnowledgeTools:
    def __init__(self, store: KnowledgeStore, vault: Path, top_k: int = 4,
                 max_distance: float = 0.40, max_note_chars: int = 4000,
                 confirm: ConfirmFn = ask_confirmation, writable: bool = False):
        self.store, self.vault = store, vault
        self.top_k, self.max_distance = top_k, max_distance
        self.max_note_chars = max_note_chars
        self.confirm, self.writable = confirm, writable

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

    def write_note(self, title: str, body: str, tags: str = "") -> str:
        """Створює нотатку лише в папці Inbox і лише після підтвердження людьми."""
        if not self.writable:
            return "ERROR: write_note is disabled; start the agent with --allow-write"
        name = title.strip()
        if not TITLE.match(name) or "/" in name or name.startswith("_"):
            return f"ERROR: invalid title {title!r}: one line without slashes"
        target = (self.vault.resolve() / INBOX / f"{name}.md").resolve()
        if self.vault.resolve() not in target.parents:
            return f"ERROR: path outside the vault: {target}"
        if target.exists():
            return f"ERROR: note already exists: {name!r}"
        tag_list = [t.strip() for t in tags.split(",") if t.strip()]
        question = (f"Створити нотатку «{INBOX}/{name}.md» "
                    f"({len(body)} символів, теги: {', '.join(tag_list) or 'немає'})?")
        if not self.confirm(question):
            return "REJECTED: the human did not confirm the note creation."
        target.parent.mkdir(parents=True, exist_ok=True)
        meta = ["---", f"tags: [{', '.join(tag_list)}]", "aliases: []",
                'source: "створено агентом"', "updated: 2026-11-21", "---", ""]
        target.write_text("\n".join(meta) + body.strip() + "\n", encoding="utf-8")
        return (f"CREATED: [[{name}]] path=\"{INBOX}/{name}.md\" chars={len(body)}; "
                f"run the indexer to make it searchable")


def build_tools() -> KnowledgeTools:
    """Збирає робочі інструменти з параметрів .env."""
    from .config import load_config
    from .embedder import GeminiEmbedder

    from .store import create_client

    cfg = load_config()
    store = KnowledgeStore(GeminiEmbedder(cfg.embed_model, cfg.embed_dim),
                           cfg.collection, client=create_client(cfg))
    return KnowledgeTools(store, cfg.vault_path, cfg.top_k, cfg.max_distance)
