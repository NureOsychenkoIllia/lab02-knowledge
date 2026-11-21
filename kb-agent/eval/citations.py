"""Перевірка обґрунтованості: чи кожне посилання [[...]] у відповіді
веде на джерело, яке агент справді отримав у спостереженнях.

Запуск: uv run python -m eval.citations traces/trace_....json
"""

import json
import re
import sys

CITATION = re.compile(r"\[\[([^\]]+)\]\]")
SOURCE = re.compile(r'source="\[\[([^\]]+)\]\]"')
# write_note підтверджує створення рядком CREATED: [[Назва]] path="Inbox/…"
CREATED = re.compile(r'CREATED: \[\[([^\]]+)\]\] path="([^"]+)"')


def _note_name(citation: str) -> str:
    """Inbox/Нотатка.md -> Нотатка: модель цитує створену нотатку шляхом."""
    stem = citation.split("#")[0].rsplit("/", 1)[-1]
    return stem[:-3] if stem.endswith(".md") else stem


def check_citations(answer: str, observations: list[str]) -> dict:
    cited = CITATION.findall(answer or "")
    sources = {s for obs in observations for s in SOURCE.findall(obs or "")}
    created = {f"{title}" for obs in observations
               for title, _ in CREATED.findall(obs or "")}
    sources |= created
    titles = {s.split("#")[0] for s in sources}
    valid = [c for c in cited
             if c in sources or c.split("#")[0] in titles
             or _note_name(c) in created]
    return {"cited": len(cited), "valid": len(valid),
            "invalid": sorted(set(cited) - set(valid)),
            "grounded": bool(cited) and len(valid) == len(cited)}


def main() -> None:
    data = json.loads(open(sys.argv[1], encoding="utf-8").read())
    observations = [r["observation"] for r in data["trace"] if r["observation"]]
    print(json.dumps(check_citations(data["final_answer"], observations),
                     ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
