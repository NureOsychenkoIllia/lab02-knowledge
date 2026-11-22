"""Друкує таблицю відстаней, збережену experiments/compare_embeddings.py."""

import json
from pathlib import Path

ROWS = json.loads((Path(__file__).with_name("results") / "embeddings.json").read_text(
    encoding="utf-8"))
print(f"{'модель':26} {'hit@4':>6} {'MRR':>6} {'макс. top-1':>12} "
      f"{'top-1 прав.':>12} {'мін. поза':>10} {'поріг':>6}")
for row in ROWS:
    print(f"{row['model']:26} {row['hit_at_k']:>6} {row['mrr']:>6} "
          f"{row['max_top1_distance']:>12} {row['top1_correct']:>12} "
          f"{row['min_out_of_scope_distance']:>10} {row['suggested_threshold']:>6}")
