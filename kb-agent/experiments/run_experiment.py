"""Експеримент: п'ять запитів типів A–E у трьох системах.

one-shot  — один виклик LLM без бази знань;
rag       — один пошук і один виклик LLM із фрагментами;
agent     — цикл агента з діями search_knowledge, read_note, finish.

Запуск: uv run python experiments/run_experiment.py
"""

import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from agent.loop import run_agent
from agent.reasoning import MODEL, get_client
from baseline import one_shot_answer, build_rag_prompt
from eval.citations import check_citations
from kb.tools import build_tools

QUERIES = [
    ("A", "Який розмір документа обмежує MongoDB?"),
    ("B", "Яку модель узгодженості обрати для кошика інтернет-магазину?"),
    ("C", "Як зміниться поведінка системи, якщо під час запису впаде одна репліка, "
          "і що станеться після її повернення?"),
    ("D", "Що таке PI Planning у SAFe?"),
    ("E", "Яку конфігурацію реплікації обрано для сервісу телеметрії?"),
]

PAUSE_SECONDS = 5


def main() -> None:
    tools = build_tools()
    rows = []
    for qtype, question in QUERIES:
        for mode in ("oneshot", "rag", "agent"):
            started = time.perf_counter()
            before = tools.store.embedder.calls
            if mode == "oneshot":
                answer, calls, observations = one_shot_answer(question), 1, []
            elif mode == "rag":
                prompt = build_rag_prompt(question, tools)
                answer = get_client().models.generate_content(
                    model=MODEL, contents=prompt).text
                calls, observations = 1, [prompt]
            else:
                state = run_agent(question, tools)
                answer, calls = state.final_answer, state.llm_calls
                observations = state.observations
            embeddings = tools.store.embedder.calls - before
            citations = check_citations(answer, observations)
            row = {"type": qtype, "question": question, "mode": mode,
                   "answer": answer, "llm_calls": calls,
                   "embedding_calls": embeddings,
                   "seconds": round(time.perf_counter() - started, 2),
                   "citations": citations}
            rows.append(row)
            print(f"[{qtype}/{mode}] llm={calls} emb={embeddings} "
                  f"t={row['seconds']}s grounded={citations['grounded']} "
                  f"({citations['valid']}/{citations['cited']})")
            time.sleep(PAUSE_SECONDS)

    Path("experiments/results").mkdir(parents=True, exist_ok=True)
    Path("experiments/results/experiment.json").write_text(
        json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
