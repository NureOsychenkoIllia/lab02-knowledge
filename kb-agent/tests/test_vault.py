import pytest

from kb.vault import iter_notes, parse_note, resolve_note_path, strip_wikilinks


def test_note_properties_and_links(vault):
    note = parse_note(vault, vault / "Реплікація" / "CRDT.md")
    assert note.title == "CRDT"
    assert "crdt" in note.tags and "реплікація" in note.tags
    assert "Conflict-free replicated data types" in note.aliases
    assert "Kleppmann" in note.properties["source"]
    assert note.links == sorted(
        ["Конфлікти під час реплікації", "Кінцева узгодженість", "Мультилідерна реплікація"])


def test_iter_notes_skips_service_dirs(vault):
    (vault / "_templates").mkdir()
    (vault / "_templates" / "Шаблон.md").write_text("# Шаблон\n", encoding="utf-8")
    paths = [note.path for note in iter_notes(vault)]
    assert len(paths) == 6
    assert not any(path.startswith("_") for path in paths)


def test_resolve_note_path_by_name_and_extension(vault):
    assert resolve_note_path(vault, "Хеш-партиціювання") == \
        (vault / "Шардинг" / "Хеш-партиціювання.md").resolve()
    assert resolve_note_path(vault, "Шардинг/Хеш-партиціювання.md").name == \
        "Хеш-партиціювання.md"
    assert resolve_note_path(vault, "[[CRDT#Властивості]]").name == "CRDT.md"


def test_resolve_note_path_rejects_outside_vault(vault):
    with pytest.raises(ValueError, match="outside the vault"):
        resolve_note_path(vault, "../../etc/passwd")
    with pytest.raises(ValueError, match="outside the vault"):
        resolve_note_path(vault, "/etc/passwd")
    with pytest.raises(FileNotFoundError):
        resolve_note_path(vault, "Немає такої нотатки")


def test_strip_wikilinks_keeps_caption():
    text = "див. [[Хеш-партиціювання|хешування]] і [[CRDT#Злиття]]"
    assert strip_wikilinks(text) == "див. хешування і CRDT"


def test_inbox_is_not_indexed_until_reviewed(vault):
    inbox = vault / "Inbox"
    inbox.mkdir()
    (inbox / "Нотатка агента.md").write_text(
        "---\ntags: [тест]\nsource: \"агент\"\n---\n# Нотатка агента\n\nТекст.\n",
        encoding="utf-8")
    assert all(not note.path.startswith("Inbox/") for note in iter_notes(vault))
    assert any(note.path.startswith("Inbox/") for note in iter_notes(vault, include_inbox=True))
