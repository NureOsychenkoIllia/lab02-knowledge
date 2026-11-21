"""Налагодження пошуку без агента: python -m kb.search "запит" [--tag тег]"""

import argparse

from .tools import build_tools


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("query")
    parser.add_argument("--tag")
    parser.add_argument("-k", type=int, default=6)
    args = parser.parse_args()

    tools = build_tools()
    for rank, hit in enumerate(tools.store.search(args.query, args.k, args.tag), 1):
        mark = "+" if hit.distance <= tools.max_distance else "-"
        preview = hit.text.replace("\n", " ")[:70]
        print(f"{rank}. {mark} {hit.distance:.3f} {hit.path} > {hit.heading}\n   {preview}")
    print(f"\n'+' — нижче порогу KB_MAX_DISTANCE={tools.max_distance}")


if __name__ == "__main__":
    main()
