import argparse
import json
import time
from pathlib import Path

from agent.loop import run_agent
from baseline import one_shot_answer, rag_answer
from kb.tools import build_tools


def save_trace(state, embed_calls: int) -> Path:
    Path("traces").mkdir(exist_ok=True)
    path = Path("traces") / f"trace_{time.strftime('%Y%m%d_%H%M%S')}.json"
    payload = {"goal": state.goal, "stop_reason": state.stop_reason,
               "steps": state.step, "llm_calls": state.llm_calls,
               "embedding_calls": embed_calls,
               "final_answer": state.final_answer, "trace": state.trace}
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def main() -> None:
    parser = argparse.ArgumentParser(description="Агент з базою знань Obsidian + Chroma")
    parser.add_argument("goal", help="питання до бази знань у лапках")
    parser.add_argument("--mode", choices=["agent", "rag", "oneshot"], default="agent")
    parser.add_argument("--allow-write", action="store_true",
                        help="дозволити дію write_note (лише папка Inbox, з підтвердженням)")
    args = parser.parse_args()

    started = time.perf_counter()
    if args.mode == "oneshot":
        print(one_shot_answer(args.goal))
        print(f"\n[one-shot] LLM calls: 1, time: {time.perf_counter() - started:.2f} s")
        return

    tools = build_tools()
    tools.writable = args.allow_write
    if args.mode == "rag":
        print(rag_answer(args.goal, tools))
        print(f"\n[rag] LLM calls: 1, embedding calls: {tools.store.embedder.calls}, "
              f"time: {time.perf_counter() - started:.2f} s")
        return

    state = run_agent(args.goal, tools)
    embed_calls = tools.store.embedder.calls
    print("\nFINAL ANSWER:\n" + (state.final_answer or ""))
    print(f"\n[agent] steps: {state.step}, LLM calls: {state.llm_calls}, "
          f"embedding calls: {embed_calls}, stop: {state.stop_reason}, "
          f"time: {time.perf_counter() - started:.2f} s")
    print(f"trace saved: {save_trace(state, embed_calls)}")


if __name__ == "__main__":
    main()
