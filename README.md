# lab02-knowledge

Лабораторна робота № 2 з дисципліни «Штучний інтелект у ПІ»: підключення бази знань
до AI-агента з ЛР 1. Сховище нотаток Obsidian індексується у векторну базу Chroma,
а агент відповідає на питання лише за знайденими фрагментами й цитує джерела
у форматі `[[Нотатка#Розділ]]`.

Предметна область — **NoSQL і розподілені дані** (варіант 9): моделі даних,
теорема CAP і рівні узгодженості, реплікація й конфлікти, шардинг, а також власні
проєктні рішення ADR-004 і ADR-005 проєкту «SmartLease».

## Структура

```
kb-agent/         проєкт: kb/ (vault, chunker, embedder, store, indexer, tools),
                  agent/ (validator, reasoning, loop), eval/ (набір, метрики,
                  перевірка посилань), tests/ (24 тести), experiments/, traces/
report/           звіт Typst (ЛБ2_ШІуПІ_Осиченко.typ), рисунки й PDF
scripts/          term_shot.py — рендер термінальних скріншотів для звіту
KB-CARD.md        паспорт бази знань версії 1.0.0
```

Сховище `kb-vault` подається окремим архівом: воно лежить поза репозиторієм,
у каталозі `../kb-vault`.

## Швидкий старт

```sh
cd kb-agent
cp .env.example .env          # OBSIDIAN_VAULT=<шлях до kb-vault>, GEMINI_API_KEY=<ключ>
uv sync
uv run python -m kb.indexer   # індексація; --rebuild перебудовує з нуля
uv run python -m kb.search "віртуальні вузли хешування" --tag шардинг
uv run python -m eval.eval_retrieval -k 4
uv run python main.py "Яку модель узгодженості обрати для кошика інтернет-магазину?"
uv run python main.py "Що таке PI Planning у SAFe?" --mode oneshot
uv run pytest -q
```

Модуль `kb.inspect` показує вміст колекції (штатна команда `chroma browse`
у Chroma 1.5.9 колекцію не читає — див. розділ «Висновки» звіту).

## Демонстрація та експеримент

```sh
bash scripts/index_demo.sh                     # чотири запуски індексатора
uv run python experiments/run_experiment.py    # 5 запитів × 3 системи
uv run python -m eval.citations traces/<файл>.json
```

## Звіт

```sh
cd report
typst compile --root ../.. ЛБ2_ШІуПІ_Осиченко.typ
```

Ключ API зберігається лише у `kb-agent/.env` (права 600, файл у `.gitignore`);
у репозиторії є тільки `.env.example` з порожнім значенням.
