from kb.tools import KnowledgeTools


def test_search_returns_fragments_with_sources(tools):
    result = tools.search_knowledge("кворум репліки запис читання")
    assert result.startswith("<fragment")
    assert 'source="[[' in result
    assert "distance=" in result


def test_threshold_gives_not_found(tools):
    strict = KnowledgeTools(tools.store, tools.vault, max_distance=0.01)
    assert strict.search_knowledge("рецепт борщу").startswith("NOT_FOUND")


def test_read_note_and_errors(tools):
    assert 'path="Реплікація/CRDT.md"' in tools.read_note("CRDT")
    assert tools.read_note("Неіснуюча").startswith("NOT_FOUND")
    assert tools.read_note("../../.ssh/id_rsa").startswith("ERROR")


def test_read_note_truncates_long_text(tools):
    short = KnowledgeTools(tools.store, tools.vault, max_note_chars=80)
    result = short.read_note("CRDT")
    assert "[...truncated]" in result
