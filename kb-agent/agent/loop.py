"""Цикл агента ЛР 1, у якому середовищем стала база знань."""

import time
from collections.abc import Callable
from typing import Any

from kb.tools import KnowledgeTools

from .errors import DecisionError
from .reasoning import get_decision
from .state import AgentState
from .validator import validate_decision

MAX_STEPS = 8
MAX_OBSERVATION_CHARS = 6000

DecideFn = Callable[[str, list[str], int, int], dict]


def execute_action(decision: dict, state: AgentState,
                   tools: KnowledgeTools) -> str | None:
    """Dispatcher: перевірене рішення -> виклик методу бази знань."""
    action, args = decision["action"], decision["arguments"]
    if action == "search_knowledge":
        return tools.search_knowledge(args["query"], args.get("tag"))
    if action == "read_note":
        return tools.read_note(args["path"])
    if action == "finish":
        state.final_answer = args["answer"]
        state.finished = True
        state.stop_reason = "finish"
        return None
    raise DecisionError(f"no handler for action {action!r}")


def print_step(record: dict) -> None:
    print(f"\nSTEP {record['step']}")
    print(f"  ACTION:      {record['action']} {record['arguments'] or ''}")
    if record.get("decision_summary"):
        print(f"  DECISION:    {record['decision_summary']}")
    if record["observation"] is not None:
        first = record["observation"].splitlines()[0][:110]
        print(f"  OBSERVATION: {first} ... ({len(record['observation'])} chars)")


def run_agent(goal: str, tools: KnowledgeTools, decide: DecideFn = get_decision,
              max_steps: int = MAX_STEPS) -> AgentState:
    state = AgentState(goal=goal)

    while not state.finished:
        if state.step >= max_steps:
            state.finished = True
            state.stop_reason = "max_steps"
            state.final_answer = (f"Агент зупинився: вичерпано ліміт кроків "
                                  f"({max_steps}) без фінальної відповіді.")
            break

        state.step += 1
        record: dict[str, Any] = {"step": state.step}
        decision: dict | None = None
        started = time.perf_counter()
        try:
            state.llm_calls += 1
            decision = decide(state.goal, state.observations, state.step, max_steps)
            validate_decision(decision)
            observation = execute_action(decision, state, tools)
            record.update(action=decision["action"],
                          arguments=decision["arguments"],
                          decision_summary=decision.get("decision_summary", ""))
        except DecisionError as exc:
            observation = f"ERROR: {exc}"
            record.update(action="rejected", arguments=None,
                          decision_summary="", rejected=decision)

        if observation is not None and len(observation) > MAX_OBSERVATION_CHARS:
            observation = observation[:MAX_OBSERVATION_CHARS] + "\n[...truncated]"
        record["observation"] = observation
        record["seconds"] = round(time.perf_counter() - started, 2)
        state.trace.append(record)
        if observation is not None:
            state.observations.append(observation)
        print_step(record)

    return state
