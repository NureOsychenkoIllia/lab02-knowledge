"""Дія write_note: обмеження папкою Inbox, заборона без підтвердження, захист шляху."""

from kb.tools import KnowledgeTools


def make_tools(tools, answer):
    questions = []

    def confirm(question):
        questions.append(question)
        return answer

    writable = KnowledgeTools(tools.store, tools.vault, top_k=3, max_distance=0.9,
                              confirm=confirm, writable=True)
    return writable, questions


def test_write_note_disabled_by_default(tools):
    readonly = KnowledgeTools(tools.store, tools.vault)
    assert readonly.write_note("Тест", "Текст").startswith("ERROR: write_note is disabled")


def test_write_note_needs_confirmation(tools):
    writable, questions = make_tools(tools, answer=False)
    result = writable.write_note("Тест", "Текст")
    assert result.startswith("REJECTED")
    assert len(questions) == 1
    assert not (tools.vault / "Inbox" / "Тест.md").exists()


def test_write_note_creates_note_inside_inbox(tools):
    writable, _ = make_tools(tools, answer=True)
    result = writable.write_note("Нова нотатка", "Опис\n\n## Розділ\n\nТекст",
                                 tags="cap, кворум")
    assert result.startswith("CREATED")
    note = tools.vault / "Inbox" / "Нова нотатка.md"
    assert note.exists()
    text = note.read_text(encoding="utf-8")
    assert "tags: [cap, кворум]" in text and "## Розділ" in text


def test_write_note_rejects_escape_and_duplicates(tools):
    writable, _ = make_tools(tools, answer=True)
    assert writable.write_note("../../outside", "x").startswith("ERROR: invalid title")
    assert writable.write_note("_templates/Шаблон", "x").startswith("ERROR: invalid title")
    assert writable.write_note("Дубль", "x").startswith("CREATED")
    assert writable.write_note("Дубль", "x").startswith("ERROR: note already exists")
