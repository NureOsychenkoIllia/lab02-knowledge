from kb.chunker import chunk_note, split_sections
from kb.vault import Note


def test_split_sections_builds_heading_path():
    body = "# Нотатка\n\nВступ.\n\n## Перший\n\nТекст.\n\n### Вкладений\n\nДеталі.\n"
    assert split_sections(body) == [
        ("Нотатка", "Вступ."),
        ("Нотатка > Перший", "Текст."),
        ("Нотатка > Перший > Вкладений", "Деталі."),
    ]


def test_split_sections_ignores_headings_in_code_block():
    body = "## Розділ\n\n```python\n# не заголовок\nprint(1)\n```\n"
    sections = split_sections(body)
    assert len(sections) == 1
    assert "# не заголовок" in sections[0][1]


def test_chunk_ids_are_stable_and_context_is_added():
    note = Note(path="Тека/Нотатка.md", title="Нотатка", body="# Нотатка\n\nОпис.\n",
                tags=["тег"])
    first = chunk_note(note, 900)
    second = chunk_note(note, 900)
    assert [c.id for c in first] == [c.id for c in second] == ["Тека/Нотатка.md::0"]
    assert first[0].embed_text.startswith("Нотатка: Нотатка\nРозділ: Нотатка\nТеги: тег")


def test_long_section_is_packed_into_several_chunks():
    paragraph = "Речення про партиції та репліки. " * 20
    note = Note(path="Тека/Довга.md", title="Довга",
                body="# Довга\n\n" + "\n\n".join([paragraph] * 4))
    chunks = chunk_note(note, 600)
    assert len(chunks) > 1
    assert all(len(chunk.text) <= 600 for chunk in chunks)
