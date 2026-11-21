"""Цикл агента з базою знань без звернень до LLM: рішення задає сценарій."""

from agent.loop import normalize_citations, run_agent


def scripted(decisions):
    queue = iter(decisions)
    return lambda goal, observations, step, max_steps: next(queue)


def test_search_read_finish(tools):
    decide = scripted([
        {"action": "search_knowledge", "arguments": {"query": "конфлікти реплікації"}},
        {"action": "read_note", "arguments": {"path": "Реплікація/CRDT.md"}},
        {"action": "finish", "arguments": {"answer": "Злиття без конфліктів [[CRDT]]"}},
    ])
    state = run_agent("Як злити конкурентні записи?", tools, decide=decide)
    assert state.stop_reason == "finish" and state.llm_calls == 3
    assert state.observations[0].startswith("<fragment")
    assert state.observations[1].startswith("<note")
    assert state.final_answer.startswith("Злиття")


def test_rejected_action_becomes_observation(tools):
    decide = scripted([
        {"action": "delete_note", "arguments": {"path": "Шардинг/Хеш-партиціювання.md"}},
        {"action": "finish", "arguments": {"answer": "ok"}},
    ])
    state = run_agent("Тест", tools, decide=decide)
    assert state.observations[0].startswith("ERROR: unknown action")
    assert (tools.vault / "Шардинг" / "Хеш-партиціювання.md").exists()


def test_max_steps(tools):
    endless = lambda *args: {"action": "search_knowledge",
                             "arguments": {"query": "кворум"}}
    state = run_agent("Цикл", tools, decide=endless, max_steps=3)
    assert state.stop_reason == "max_steps" and state.step == 3


def test_citations_are_normalized():
    answer = "Факт [[Кворум], [[CRDT#Злиття]] і ще [[PACELC]]."
    assert normalize_citations(answer) == "Факт [[Кворум]], [[CRDT#Злиття]] і ще [[PACELC]]."
