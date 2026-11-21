"""Друкує таблицю відстаней, збережену experiments/compare_embeddings.py."""

import json
from pathlib import Path

ROWS = json.loads((Path(__file__).with_name("results") / "embeddings.json").read_text(
    encoding="utf-8"))
print(f"{'модель':26} {'hit@4':>6} {'MRR':>6} {'макс. прав.':>12} "
      f"{'мін. поза':>10} {'поріг':>6}")
for row in ROWS:
    print(f"{row['model']:26} {row['hit_at_k']:>6} {row['mrr']:>6} "
          f"{row['max_correct_distance']:>12} {row['min_out_of_scope_distance']:>10} "
          f"{row['suggested_threshold']:>6}")
