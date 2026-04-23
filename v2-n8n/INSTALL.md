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



## Структура workflow

Schedule Trigger (ежедневно в 9:00)
    │
    ├──► Хабр: HTTP Request → Code (парсинг) → Filter (опыт) → Filter (формат)
    │
    └──► hh.ru: HTTP Request → Code (парсинг) → Filter (опыт) → Filter (формат)
    │
    └──► Merge (объединение)
          │
          └──► Code (ранжирование) → Limit (топ-5) → Code (формирование) → Telegram



## Проверка работы

1. После импорта workflow нажмите **Execute Workflow** (зеленый треугольник)
    
2. Проверьте, что в Telegram пришло сообщение
    

## Устранение неполадок

**Ошибка "Can't parse entities" в Telegram**

- В Parse Mode выберите **Markdown (Legacy)** вместо MarkdownV2
    

### Вакансии не приходят

- Проверьте фильтры — возможно, слишком жесткие
    
- Временно отключите фильтры, чтобы увидеть все вакансии


## Настройка сохранения в Obsidian

#### 1. Настройте Google Drive в n8n

1. Создайте папку в Google Drive: `Obsidian_Vacancies`
2. В n8n добавьте узел **Google Drive**:
   - **Operation**: `Create File From Text`
   - **Folder ID**: ID вашей папки
   - **File Name**: `{{$json.fileName}}`
   - **Content**: `{{$json.content}}`

#### 2. Настройте Junction на Windows

В PowerShell (от администратора):

```powershell
New-Item -ItemType Junction -Path "D:\Obsidian_Vaults\Proekt_karera\Career-project-v1.0\02_POISK_RABOTY\01_Vacancies" -Target "G:\Мой диск\Obsidian_Vacancies"
```

#### 3. Проверьте

- Запустите workflow
    
- Файлы появятся в Google Drive
    
- В Obsidian они будут видны автоматически


## Дорожная карта

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