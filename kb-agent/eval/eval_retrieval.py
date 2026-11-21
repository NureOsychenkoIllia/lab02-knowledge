"""Оцінювання пошуку: hit@k, MRR і калібрування порогу відстані.

Запуск: uv run python -m eval.eval_retrieval [-k 4]
"""

import argparse
import json
from pathlib import Path

from kb.store import KnowledgeStore

SET_PATH = Path(__file__).with_name("retrieval_set.json")


def evaluate(store: KnowledgeStore, cases: list[dict], k: int,
             max_distance: float) -> dict:
    rows, hits_at_k, reciprocal = [], 0, 0.0
    in_scope = [c for c in cases if c["expected"]]
    false_accepts = 0
    for case in cases:
        hits = store.search(case["query"], k)
        paths = [h.path for h in hits]
        best = hits[0].distance if hits else None
        if case["expected"]:
            ranks = [paths.index(p) + 1 for p in case["expected"] if p in paths]
            rank = min(ranks) if ranks else None
            hits_at_k += rank is not None
            reciprocal += 1 / rank if rank else 0.0
        else:
            rank = None
            false_accepts += best is not None and best <= max_distance
        rows.append({"query": case["query"], "expected": case["expected"],
                     "top": paths[:3], "rank": rank,
                     "best_distance": round(best, 3) if best is not None else None})
    n = len(in_scope) or 1
    return {"k": k, "hit_at_k": round(hits_at_k / n, 3), "mrr": round(reciprocal / n, 3),
            "out_of_scope_accepted": false_accepts, "max_distance": max_distance,
            "rows": rows}


def main() -> None:
    from kb.config import load_config
    from kb.embedder import make_embedder
    from kb.store import create_client

    parser = argparse.ArgumentParser()
    parser.add_argument("-k", type=int, default=4)
    args = parser.parse_args()
    cfg = load_config()
    store = KnowledgeStore(make_embedder(cfg.embed_model, cfg.embed_dim),
                           cfg.collection, client=create_client(cfg))
    report = evaluate(store, json.loads(SET_PATH.read_text(encoding="utf-8")),
                      args.k, cfg.max_distance)
    for r in report["rows"]:
        print(f"{str(r['rank']):>4} {r['best_distance']} {r['query']}")
    print(f"\nhit@{report['k']} = {report['hit_at_k']}, MRR = {report['mrr']}, "
          f"out-of-scope accepted at {report['max_distance']}: "
          f"{report['out_of_scope_accepted']}")
    Path("eval/results.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
