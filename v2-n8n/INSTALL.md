# Бот мониторинга вакансий — версия 2.0 (n8n)

## Описание

Пет-проект, демонстрирующий навык **автоматизации бизнес-процессов** с использованием low-code платформы n8n. Бот раз в 3 дня собирает вакансии из двух источников (Хабр Карьера и hh.ru), фильтрует шум, ранжирует по релевантности, сохраняет вакансий в Obsidian (через Google Drive + Junction) и отправляет дайджест в Telegram.


## Технологии

- **n8n** — low-code платформа автоматизации
- **Docker** — контейнеризация
- **Telegram Bot API** — уведомления
- **hh.ru API** — публичный API вакансий
- **Хабр Карьера RSS** — публичная RSS-лента
- **Dropbox API** — система хранение данных(облако)

## Требования

- Docker Desktop (Windows/Mac) или Docker Engine (Linux)
- Telegram Bot Token (получить у @BotFather)
- Ваш Chat ID
- Google аккаунт (для Google Sheets и Google Drive)


## Быстрый старт

#### 1. Установить Docker

[Скачать Docker Desktop](https://www.docker.com/products/docker-desktop/)

#### 2. Клонировать репозиторий

```bash
git clone https://github.com/your-username/career-bot.git
cd career-bot/v2-n8n
```

#### 3. Запустить n8n через Docker
```bash
docker-compose up -d
```

n8n будет доступен по адресу: [http://localhost:5678](http://localhost:5678/)

#### 4. Настроить Telegram бота

1. В Telegram найти @BotFather
    
2. Отправить `/newbot` и получить токен
    
3. Узнать свой Chat ID:
    
    - Отправить боту любое сообщение
        
    - Открыть в браузере:  
        `https://api.telegram.org/bot<ВАШ_ТОКЕН>/getUpdates`
        
    - Найти число в поле `chat` → `id`

#### 5. Импортировать workflow

1. Открыть [http://localhost:5678](http://localhost:5678/)
    
2. Нажать на три точки (⋮) → **Import from File**
    
3. Выбрать файл `workflow/career-bot-workflow.json`
    
4. В узле **Telegram** добавить:
    
    - **Credential**: создать новый с вашим токеном
        
    - **Chat ID**: вставить ваш Chat ID
        
5. Нажать **Save** и переключить тумблер на **Active**


## Настройка Google Sheets (дедупликация)

Бот использует Google Sheets как базу памяти для хранения ID всех обработанных вакансий. Это предотвращает дублирование при каждом запуске.

#### Шаг 1: Создайте таблицу

1. Зайдите на [sheets.google.com](https://sheets.google.com/)
    
2. Создайте новую таблицу
    
3. Назовите её `career_bot_db`
    
4. В первой строке (заголовки) укажите хотя бы **одну колонку**:
   - **A1**: `vacancy_id`

**Опционально** (для удобства отладки):
- **B1**: `source`
- **C1**: `title`
- **D1**: `createdAt`

5. Заполните хотя бы одну строку-пример (можно позже, бот сам добавит)


#### Шаг 2: Получите ID таблицы

ID таблицы — это часть URL между `/d/` и `/edit`:

text

https://docs.google.com/spreadsheets/d/ЭТОТ_ТЕКСТ_И_ЕСТЬ_ID/edit

Скопируйте этот ID.

#### Шаг 3: Настройте узел Google Sheets в n8n

1. В workflow найдите узел **Google Sheets** (он называется `Google Sheets - Get all vacancies` или похоже)
    
2. Нажмите **Create New** в поле **Credential**
    
3. Выберите **OAuth2**
    
4. Нажмите **Sign in with Google** и разрешите доступ
    
5. В поле **Document ID** вставьте ID вашей таблицы
    
6. В поле **Sheet Name** укажите `Лист1` (или название вашего листа)
    

#### Шаг 4: Проверьте доступ

1. Нажмите **Execute Node** на узле Google Sheets
    
2. В Output должны появиться данные из таблицы (или пустой массив, если таблица пуста)
    

---

## Настройка Dropbox + Obsidian (синхронизация)

Бот сохраняет `.md` заметки в Dropbox, а Obsidian синхронизируется через плагин **Remotely Save**.

### Шаг 1: Создайте приложение в Dropbox

1. Зайдите на [dropbox.com/developers/apps](https://www.dropbox.com/developers/apps)
2. Нажмите **Create app**
3. Выберите:
   - **Scoped access**
   - **Full Dropbox** (доступ ко всему хранилищу)
4. Название: `n8n-obsidian-sync-bot`
5. Нажмите **Create app**

### Шаг 2: Настройте разрешения

1. В панели приложения перейдите на вкладку **Permissions**
2. Поставьте галочки:
   - `files.content.write` (запись файлов)
   - `files.content.read` (чтение файлов)
3. Нажмите **Submit**

### Шаг 3: Настройте OAuth в n8n

1. В n8n добавьте узел **Dropbox**
2. Нажмите **Create New** в поле **Credential**
3. Выберите **OAuth2 API**
4. Скопируйте **OAuth Redirect URL** из n8n
5. Вернитесь в консоль Dropbox, вставьте этот URL в поле **Redirect URIs**
6. Скопируйте **App key** (Client ID) и **App secret** (Client Secret) из Dropbox
7. Вставьте их в n8n
8. Нажмите **Connect** и разрешите доступ

### Шаг 4: Настройте путь в узле Dropbox

В узле **Dropbox** укажите:

| Поле | Значение |
|------|----------|
| **Operation** | `Upload` |
| **File Path** | `/Приложения/remotely-save/Obsidian_Vaults/Proekt_karera/Career-project-v1.0/02_POISK_RABOTY/01_Vacancies/{{$json.fileName}}` |
| **Binary Property** | `data` |

**Важно:** Путь должен совпадать с тем, который создаст плагин Remotely Save после первой синхронизации.

### Шаг 5: Настройте Obsidian

1. Установите плагин **Remotely Save**
2. В настройках выберите **Dropbox** как удалённый сервис
3. Авторизуйтесь через Dropbox
4. Нажмите **Sync** — папка структура создастся автоматически
5. Скопируйте полный путь из настроек плагина в узел n8n

### Преимущества Dropbox

- ✅ Не требует Junction (символических ссылок)
- ✅ Работает на любых устройствах (Windows, Mac, Linux)
- ✅ Синхронизация с Obsidian через плагин
- ✅ Доступно на смартфоне


## Как работает дедупликация

```
Запуск бота
    │
    ▼
Загрузка ID из Google Sheets (все обработанные вакансии)
    │
    ▼
Получение новых вакансий из источника (Хабр)
    │
    ▼
Проверка: ID вакансии уже есть в таблице?
    │
    ├──► ДА → пропустить (не сохранять, не отправлять)
    │
    └──► НЕТ → сохранить в Obsidian + добавить ID в Google Sheets + отправить в Telegram
    │
    ▼
Если все вакансии — дубли → отправить "отчёт о тишине"

```

**Преимущества:**

- Таблица не привязана к локальному компьютеру
    
- Можно архивировать заметки в Obsidian, не теряя историю
    
- Легко посмотреть статистику вручную

## Структура workflow

```
career-bot-v2 (n8n + Docker)
│
├── [Schedule Trigger] ———► Запуск каждые 3 дня в 09:00
│
├── Sources (Парсинг)
│  └──► [Хабр Карьера] ➔ HTTP Request ➔ Code (парсинг) ➔ Filter (опыт) ➔ Filter (формат)
│  └──► [hh.ru] ➔ HTTP Request ➔ Code (парсинг) ➔ Filter (опыт) ➔ Filter (формат)
│
├── Processing (Обработка)
│  └── [Merge] ——————————► (Объединение потоков)
│      └──► [Code: Deduplication] ➔ Проверка уникальности по ID (Static Data)
│           └──► [GS: Examination] ➔ Запрос в базу (Google Sheets)
│                └──► [Code: Ranging] ➔ Ранжирование по релевантности 
│                     └──► [Limit] ➔ Отбор ТОП-5 свежих вакансий
│                          └──► [Code: Deduplication_Final] ➔ Сравнение (Smart Match)
│                               └──► [IF: Is New?] —————► (True) —► [Code Obsidian Formation] ➔ Формирование заметки ➔ [Dropbox API] ➔ [Remotely Save] ➔ Obsidian
│
│
└── Delivery (Доставка)
   └── [Code Forming a message] ➔ Формирование сообщения ➔ [Telegram] ➔ Отправка в канал (Дайджест или "Отчет о тишине")
   
```


## Проверка работы

1. После импорта workflow нажмите **Execute Workflow**
2. Проверьте, что в Telegram пришло сообщение
3. Проверьте, что в Google Sheets появились ID вакансий
4. Проверьте, что в Dropbox появились `.md` файлы по указанному пути
5. В Obsidian нажмите **Sync** (в плагине Remotely Save) — заметки должны появиться
---

## Устранение неполадок

### Ошибка "Can't parse entities" в Telegram

- В узле **Telegram** в поле **Parse Mode** выберите **Markdown (Legacy)** вместо MarkdownV2
    

### Вакансии не приходят

- Проверьте фильтры — возможно, слишком жесткие
    
- Временно отключите фильтры, чтобы увидеть все вакансии
    

### Ошибка "Cannot read properties of undefined" в Google Sheets

- Проверьте, что в узле Google Sheets правильно указан **Sheet Name**
    
- По умолчанию в русском Google Sheets лист называется `Лист1`
    

### Файлы не создаются в Obsidian (Dropbox + Remotely Save)

1. **Проверьте путь в узле Dropbox:**
   - Откройте Remotely Save в Obsidian
   - Нажмите **Sync** один раз
   - Скопируйте полный путь к папке из настроек плагина
   - Убедитесь, что путь в узле Dropbox совпадает

2. **Проверьте авторизацию:**
   - В n8n откройте креденшел Dropbox
   - Нажмите **Reconnect** и заново разрешите доступ

3. **Проверьте синхронизацию:**
   - В Obsidian нажмите **Sync** (стрелочка в левом нижнем углу)
   - Должно появиться уведомление об успешной синхронизации

4. **Если файлы есть в Dropbox, но не в Obsidian:**
   - Проверьте, что в настройках Remotely Save выбран **Dropbox**
   - Убедитесь, что путь к папке указан верно (без лишних слешей)
   - Нажмите **Download from remote**

### Дубли всё равно появляются

- Проверьте, что в Google Sheets таблица заполняется (выполните узел отдельно)
    
- Убедитесь, что ID вакансий уникальны (Хабр выдаёт `guid`, hh.ru — `id`)



## Дорожная карта

* Интеграция с Obsidian (сохранение заметок)
- Добавить источник Telegram-каналов с вакансиями
- Настроить автоматическое откликание на подходящие вакансии
- Интеграция с Obsidian (сохранение заметок) 
- Добавить аналитику: графики динамики количества вакансий
- Интеграция с CRM (например, Bitrix24)
- Деплой на VPS



## Ссылки

- [n8n документация](https://docs.n8n.io/)
    
- [hh.ru API](https://dev.hh.ru/)
    
- [Хабр Карьера RSS](https://career.habr.com/vacancies/rss)
    
- [Google Sheets AP](https://developers.google.com/sheets/api)