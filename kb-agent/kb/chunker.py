"""Розбиття нотатки на фрагменти за заголовками Markdown."""

import re
from dataclasses import dataclass

from .vault import Note, strip_wikilinks

HEADING = re.compile(r"^(#{1,6})\s+(.+?)\s*#*\s*$")


@dataclass
class Chunk:
    id: str
    path: str
    title: str
    heading: str
    ordinal: int
    text: str
    embed_text: str


def split_sections(body: str) -> list[tuple[str, str]]:
    """Повертає пари (шлях заголовків, текст). Код у ``` не розбирається."""
    sections: list[tuple[str, str]] = []
    stack: list[tuple[int, str]] = []
    lines: list[str] = []
    in_code = False

    def flush():
        text = "\n".join(lines).strip()
        if text:
            sections.append((" > ".join(t for _, t in stack), text))
        lines.clear()

    for line in body.splitlines():
        if line.lstrip().startswith("```"):
            in_code = not in_code
        match = None if in_code else HEADING.match(line)
        if match:
            flush()
            level = len(match.group(1))
            while stack and stack[-1][0] >= level:
                stack.pop()
            stack.append((level, match.group(2).strip()))
        else:
            lines.append(line)
    flush()
    return sections


def _pack(paragraphs: list[str], max_chars: int) -> list[str]:
    """Жадібно об'єднує абзаци в шматки до max_chars; задовгий абзац ріже."""
    parts, current = [], ""
    for para in paragraphs:
        while len(para) > max_chars:
            cut = para.rfind(" ", 0, max_chars)
            if cut <= 0:
                cut = max_chars
            if current:
                parts.append(current)
                current = ""
            parts.append(para[:cut].strip())
            para = para[cut:].strip()
        if current and len(current) + len(para) + 2 > max_chars:
            parts.append(current)
            current = para
        else:
            current = f"{current}\n\n{para}" if current else para
    if current:
        parts.append(current)
    return parts


def chunk_note(note: Note, max_chars: int = 900) -> list[Chunk]:
    chunks: list[Chunk] = []
    for heading, text in split_sections(note.body):
        paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
        for part in _pack(paragraphs, max_chars):
            n = len(chunks)
            context = f"Нотатка: {note.title}\nРозділ: {heading or note.title}\n"
            if note.tags:
                context += f"Теги: {', '.join(note.tags)}\n"
            chunks.append(Chunk(
                id=f"{note.path}::{n}", path=note.path, title=note.title,
                heading=heading or note.title, ordinal=n, text=part,
                embed_text=context + "\n" + strip_wikilinks(part),
            ))
    return chunks
