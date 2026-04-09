# Бот для мониторинга вакансий → Obsidian

Минимальный каркас под пет‑проект:
- создаёт заметки-вакансии (`.md`) в папке Obsidian по единому YAML-формату;
- позже сюда добавим источники (HH/Habr/SuperJob), дедупликацию и Telegram-дайджест.

## Быстрый старт (Windows)

1) Установи Python 3.11+.
2) Открой PowerShell в папке:
`ПРОЕКТ КАРЬЕРА v1.0/03 - ПЕТ-ПРОЕКТЫ(проекты внутри проекта)/Бот для мониторинга вакансий/bot/`

3) Запусти (пока без внешних API — создаст тестовые заметки):

```powershell
python .\run_demo.py
```

Если из-за кириллицы в путях возникают ошибки, запускай так:

```powershell
python -X utf8 .\run_demo.py
```

## HH → Obsidian (первый реальный источник)

Скрипт `run_hh_to_obsidian.py`:
- тянет вакансии с HH через публичный API,
- создаёт новые заметки в Obsidian,
- хранит дедупликацию в `state.json` (чтобы не создавать повторно).

Запуск:

```powershell
python -X utf8 .\run_hh_to_obsidian.py
```

## Telegram-бот (витрина проекта)

Бот умеет:
- по команде `/run` запустить HH → Obsidian (создать новые заметки),
- прислать в Telegram топ‑5 с ссылками и причинами выбора.

### 1) Установка зависимостей

```powershell
pip install -r .\requirements.txt
```

### 2) Создай `.env` и положи туда токен BotFather

1) Скопируй пример:

```powershell
copy .\.env.example .\.env
```

2) Открой файл `.env` и вставь токен в строку `TELEGRAM_BOT_TOKEN=...`

Важно: `.env` **не коммитится** (он в `.gitignore`).

### 3) Создай бота у BotFather и получи токен

Если `.env` по какой-то причине не используешь, можно запустить через переменную окружения:

```powershell
$env:TELEGRAM_BOT_TOKEN="123456:ABCDEF..."
python -X utf8 .\telegram_bot.py
```

Дальше открой чат с ботом и напиши `/start`, затем `/run`.

### Что можно показать работодателю
- Этот файл (`README.md`) — как быстро развернуть локально.
- Файл `telegram_bot.py` — Telegram-интерфейс (витрина).
- Файл `run_hh_to_obsidian.py` — ядро пайплайна (сбор → фильтры → скоринг → Obsidian).
- Obsidian-дашборд `Дашборд - Вакансии по статусу` — результат как база знаний.

## Настройки

Файл `config.json`:
- `vault_root`: корень твоего Obsidian vault (как видит Obsidian).
- `vacancies_folder`: папка, куда складывать заметки вакансий.
- `hh`: параметры поиска HH (`search_text`, `area`, ...).

### Как создать `config.json` (если ты клонировал репозиторий)

Скопируй пример и подстрой под себя:

```powershell
copy .\config.example.json .\config.json
```

Дальше в `config.json` отредактируй минимум:
- `vault_root` — путь к твоему vault (обычно `D:/Obsidian_Vaults/Proekt_karera`)
- `vacancies_folder` — куда сохранять заметки вакансий внутри vault

## Следующие шаги

- коннектор HH (API) → создание заметок
- коннектор Habr Career (RSS/HTML) → создание заметок
- дедупликация по `source+external_id` (SQLite)
- Telegram-дайджест топ‑5 в день


