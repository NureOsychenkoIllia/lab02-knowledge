#!/usr/bin/env bash
# Чотири запуски індексатора: первинний, без змін, після редагування, після видалення.
set -euo pipefail
cd "$(dirname "$0")/.."

vault=$(grep '^OBSIDIAN_VAULT=' .env | cut -d= -f2- | tr -d '"')
note_edit="$vault/Шардинг/Ребалансування партицій.md"
note_del="$vault/Шардинг/Хеш-партиціювання.md"
tmp=$(mktemp -d)
cp "$note_edit" "$tmp/edit.md"
cp "$note_del" "$tmp/del.md"

restore() {
    cp -f "$tmp/edit.md" "$note_edit"
    cp -f "$tmp/del.md" "$note_del"
    rm -rf "$tmp"
    uv run python -m kb.indexer >/dev/null
}
trap restore EXIT

echo "# 1. первинна індексація"
uv run python -m kb.indexer --rebuild
echo
echo "# 2. повторний запуск без змін"
uv run python -m kb.indexer
echo
# Безкоштовний рівень Gemini дозволяє 100 текстів ембедингів за хвилину,
# тому перед наступним записом чекаємо, поки вікно ліміту скинеться.
sleep 65
echo "# 3. після редагування нотатки «Шардинг/Ребалансування партицій.md»"
printf '\n## Перевірка інкрементної індексації\n\nНотатку доповнено після первинної індексації.\n' >> "$note_edit"
uv run python -m kb.indexer
echo
echo "# 4. після видалення нотатки «Шардинг/Хеш-партиціювання.md»"
rm "$note_del"
uv run python -m kb.indexer
