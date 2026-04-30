# Бот мониторинга вакансий — версия 2.0 (n8n)

## Описание

Пет-проект, демонстрирующий навык **автоматизации бизнес-процессов** с использованием low-code платформы n8n. Бот раз в 3 дня собирает вакансии из двух источников (Хабр Карьера и hh.ru), фильтрует шум, ранжирует по релевантности, сохраняет вакансий в Obsidian (через Google Drive + Junction) и отправляет дайджест в Telegram.


## Технологии

- **n8n** — low-code платформа автоматизации
- **Docker** — контейнеризация
- **Telegram Bot API** — уведомления
- **hh.ru API** — публичный API вакансий
- **Хабр Карьера RSS** — публичная RSS-лента

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


## Настройка Google Drive + Obsidian

Бот сохраняет `.md` заметки в Google Drive, а на вашем компьютере создаётся символическая ссылка (Junction), чтобы Obsidian видел эти файлы.

#### Шаг 1: Создайте папку в Google Drive

1. Зайдите на [drive.google.com](https://drive.google.com/)
    
2. Создайте папку: `Obsidian_Vacancies`
    
3. Откройте папку и скопируйте **ID папки** из адресной строки:
    
    text
    
    https://drive.google.com/drive/folders/ЭТОТ_ТЕКСТ_И_ЕСТЬ_ID
    

#### Шаг 2: Настройте узел Google Drive в n8n

1. В workflow найдите узел **Google Drive**
    
2. В поле **Credential** используйте ту же учётную запись, что для Google Sheets
    
3. **Operation**: `Create File From Text`
    
4. **Folder ID**: вставьте ID папки `Obsidian_Vacancies`
    
5. **File Name**: `{{$json.fileName}}`
    
6. **Content**: `{{$json.content}}`

#### Шаг 3: Настройте Junction на Windows (один раз)

Запустите PowerShell **от имени администратора**:

```powershell

New-Item -ItemType Junction -Path "D:\Obsidian_Vaults\Proekt_karera\Career-project-v1.0\02_POISK_RABOTY\01_Vacancies" -Target "G:\Мой диск\Obsidian_Vacancies"

```

**Важно:** Подставьте свои пути:

- `-Path` — путь к папке с вакансиями в вашем хранилище Obsidian
    
- `-Target` — путь к папке `Obsidian_Vacancies` на вашем Google Drive (он синхронизирован через приложение Google Drive для Windows)
    

#### Шаг 4: Проверьте

1. Запустите workflow
    
2. В Google Drive в папке `Obsidian_Vacancies` должны появиться `.md` файлы
    
3. В Obsidian в папке `01_Vacancies` они будут видны автоматически

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
│                               └──► [IF: Is New?] —————► (True) —► [Code Obsidian Formation] ➔ Формирование заметки ➔ [Google Drive API] ➔ [Junction] ➔ Obsidian
│
│
└── Delivery (Доставка)
   └── [Code Forming a message] ➔ Формирование сообщения ➔ [Telegram] ➔ Отправка в канал (Дайджест или "Отчет о тишине")
   
```


## Проверка работы

1. После импорта workflow нажмите **Execute Workflow**
    
2. Проверьте, что в Telegram пришло сообщение
    
3. Проверьте, что в Google Sheets появились ID вакансий
    
4. Проверьте, что в Google Drive появились `.md` файлы
    
5. Проверьте, что в Obsidian видны новые заметки
    

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
    

### Файлы не создаются в Obsidian

- Проверьте, что Junction создана корректно: в PowerShell выполните `dir D:\путь\к\папке` — ссылка должна вести на Google Drive
    
- Убедитесь, что Google Drive для Windows запущен и папка синхронизируется
    

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