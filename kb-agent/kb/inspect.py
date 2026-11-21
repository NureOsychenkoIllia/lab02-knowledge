"""Перегляд колекції без TUI: python -m kb.inspect [--limit N]"""

import argparse
from collections import Counter

from .tools import build_tools


def main() -> None:
    parser = argparse.ArgumentParser(description="Вміст колекції Chroma")
    parser.add_argument("--limit", type=int, default=3)
    args = parser.parse_args()

    tools = build_tools()
    store = tools.store
    data = store.col.get(include=["documents", "metadatas"])
    counts = Counter(meta["path"] for meta in data["metadatas"])
    print(f"collection '{store.name}': {store.count()} chunks, "
          f"{len(counts)} notes, embedder {store.embedder.name}")
    print(f"metadata: {store.col.metadata}")
    print(f"\nnotes and chunks:")
    for path, count in sorted(counts.items()):
        print(f"  {count}  {path}")
    print(f"\nfirst {args.limit} chunks:")
    for chunk_id, doc, meta in list(zip(data["ids"], data["documents"],
                                        data["metadatas"]))[:args.limit]:
        preview = doc.replace("\n", " ")[:60]
        print(f"  {chunk_id}\n    heading={meta['heading']!r} tags={meta.get('tags')}\n"
              f"    {preview}...")


if __name__ == "__main__":
    main()
