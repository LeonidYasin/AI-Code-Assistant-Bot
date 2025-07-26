# 🤖 AI Code Assistant CLI

**Универсальный консольный ассистент для анализа, рефакторинга и генерации кода.**  
Работает **локально**, использует **дешёвые или бесплатные LLM** (DeepSeek, Kimi, GigaChat) и **не требует внешних подписок**.

---

## 📌 За 10 секунд

| Что вы получаете | Как это работает |
|---|---|
| `aicli analyze src/` | Показывает запахи кода и предлагает фиксы |
| `aicli generate --spec "CRUD блог"` | Создаёт Express + Prisma + React проект с тестами |
| `aicli fix logs/error.log src/app.ts` | Исправляет ошибку по логам |
| **Цена** | Бесплатно или ≈ 0.3 ₽ за 1000 токенов |

---

## 🚀 Установка за 30 секунд

1. Клонируй
   ```bash
   git clone https://github.com/LeonidYasin/AI-Code-Assistant-Bot.git
   cd AI-Code-Assistant-Bot


python -m venv venv
venv\Scripts\activate   # или source venv/bin/activate
pip install -r requirements.txt

# Бесплатный DeepSeek (по умолчанию)
PROVIDER=hf_deepseek
HF_TOKEN=hf_xxx

# Быстрый Kimi
PROVIDER=kimi
KIMI_API_KEY=sk-xxx

| Команда                                      | Что делает                 |
| -------------------------------------------- | -------------------------- |
| `aicli analyze --model deepseek src/`        | Анализ кода                |
| `aicli generate --spec "REST API для задач"` | Генерирует проект          |
| `aicli fix --log logs/error.log src/app.ts`  | Исправляет ошибки          |
| `aicli switch-model kimi`                    | Переключится на другую LLM |


📺 Telegram-бот (опционально)
Telegram-интерфейс поддерживается, но не является приоритетом.
Если нужен — задай TELEGRAM_BOT_TOKEN; все новые фичи сначала появляются в CLI.
🧩 Добавить свою модель
Создай adapters/my_llm.py → реализуй ask(messages) -> str.
Добавь запись в config/models.yaml.
Отправь PR — мердж за 24 ч.
📄 Лицензия
MIT © 2025 Leonid Yasin

leonidyasin@gmail.com

















# 🤖 AI Code Assistant Bot

**Telegram-бот для анализа и управления проектами с поддержкой GigaChat**

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/)
[![Telegram](https://img.shields.io/badge/Telegram-Bot-blue.svg)](https://core.telegram.org/bots)
[![GigaChat](https://img.shields.io/badge/GigaChat-API-green.svg)](https://developers.sber.ru/docs/ru/gigachat/api/overview)

## 📋 Содержание

- [Возможности](#-возможности)
- [Быстрый старт](#-быстрый-старт)
  - [Требования](#-требования)
  - [Установка](#-установка)
  - [Настройка](#-настройка)
  - [Запуск](#-запуск)
- [Использование](#-использование)
  - [CLI команды](#-cli-команды)
  - [Telegram команды](#-telegram-команды)
- [Структура проекта](#-структура-проекта)
- [Разработка](#-разработка)
- [Вклад в проект](#-вклад-в-проект)
- [Лицензия](#-лицензия)

## 🚀 Возможности

- **Анализ проектов** - полная статистика и структура
- **Управление проектами** - создание, переключение, просмотр
- **Анализ кода** - оценка зрелости и рекомендации
- **CLI и Telegram интерфейсы** - удобная работа в любом формате
- **Поддержка Python проектов** - анализ зависимостей и структуры
- **Интеграция с GigaChat** - расширенные возможности анализа кода

## 🚀 Быстрый старт

### 📋 Требования

- Python 3.9+
- Учетная запись Telegram для работы с ботом
- API ключ GigaChat (опционально, для расширенного анализа кода)

### ⚙️ Установка

1. Клонируйте репозиторий:
   ```bash
   git clone https://github.com/yourusername/ai-code-assistant.git
   cd ai-code-assistant
   ```

2. Создайте и активируйте виртуальное окружение:
   ```bash
   # Для Windows
   python -m venv venv
   .\venv\Scripts\activate
   
   # Для Linux/MacOS
   python3 -m venv venv
   source venv/bin/activate
   ```

3. Установите зависимости:
   ```bash
   pip install -r requirements.txt
   ```

### ⚙️ Настройка

1. Скопируйте файл с примерами переменных окружения:
   ```bash
   copy .env.example .env
   ```

2. Откройте файл `.env` и настройте параметры:
   ```
   # Токен вашего Telegram бота
   TELEGRAM_BOT_TOKEN=your_telegram_bot_token
   
   # API ключ GigaChat (опционально)
   GIGACHAT_API_KEY=your_gigachat_api_key
   
   # Настройки логирования
   LOG_LEVEL=INFO
   LOG_FILE=bot.log
   ```

### 🚀 Запуск

#### Запуск бота в режиме Telegram:
```bash
python main.py
```

#### Запуск в режиме CLI:
```bash
# Показать список проектов
python main.py project list

# Создать новый проект
python main.py project create my_project

# Переключиться на проект
python main.py project switch my_project

# Показать информацию о проекте
python main.py project info
```

## 💻 Использование

### 📋 CLI команды

#### Управление проектами:
```
project list           - Показать список проектов
project create <name>  - Создать новый проект
project switch <name>  - Переключиться на проект
project info           - Показать информацию о текущем проекте
```

#### Анализ кода:
```
analyze <код>         - Проанализировать фрагмент кода
analyze_project       - Проанализировать текущий проект
```

### 🤖 Telegram команды

#### Основные команды:
```
/start - Начать работу с ботом
/help  - Показать справку
```

#### Управление проектами:
```
/project list   - Показать список проектов
/project create - Создать новый проект
/project switch - Переключиться на проект
/project info   - Информация о текущем проекте
```

#### Анализ кода:
```
/analyze - Проанализировать код
/analyze_project - Проанализировать текущий проект
```

## 🏗️ Структура проекта

```
ai-code-assistant/
├── .github/                    # GitHub workflows и шаблоны
│   └── workflows/
│       └── tests.yml
│
├── core/                      # Основная логика приложения
│   ├── ai/                     # AI/ML компоненты
│   ├── bot/                    # Логика бота
│   ├── cli/                    # CLI команды
│   ├── project/                # Управление проектами
│   └── utils/                  # Вспомогательные функции
│
├── config/                    # Файлы конфигурации
│   ├── default.yaml
│   └── development.yaml
│
├── docs/                      # Документация
│   └── archive/                # Архивные версии документации
│       └── v1.0.0/             # Версия 1.0.0
│
├── handlers/                  # Обработчики команд
│   ├── commands.py
│   ├── nlp_processor.py
│   └── project_handlers.py
│
├── projects/                  # Директории проектов
│   └── example_project/
│
├── scripts/                   # Вспомогательные скрипты
│   ├── setup_env.sh
│   └── deploy.sh
│
├── tests/                     # Тесты
│   ├── unit/
│   ├── integration/
│   └── conftest.py
│
├── .env.example              # Пример переменных окружения
├── .gitignore
├── main.py                    # Точка входа
├── pyproject.toml             # Зависимости и метаданные
└── README.md                  # Эта документация
```

## 🛠️ Разработка

### Установка для разработки

1. Клонируйте репозиторий:
   ```bash
   git clone https://github.com/yourusername/ai-code-assistant.git
   cd ai-code-assistant
   ```

2. Установите зависимости для разработки:
   ```bash
   pip install -r requirements-dev.txt
   ```

3. Установите pre-commit хуки:
   ```bash
   pre-commit install
   ```

### Запуск тестов

```bash
# Запуск всех тестов
pytest

# Запуск unit-тестов
pytest tests/unit

# Запуск интеграционных тестов
pytest tests/integration
```

### Форматирование кода

```bash
# Автоматическое форматирование кода
black .

# Сортировка импортов
isort .

# Проверка стиля кода
flake8
```

## 🤝 Вклад в проект

Приветствуются любые вклады! Пожалуйста, следуйте этим шагам:

1. Создайте форк репозитория
2. Создайте ветку для вашей функции (`git checkout -b feature/AmazingFeature`)
3. Сделайте коммит ваших изменений (`git commit -m 'Add some AmazingFeature'`)
4. Отправьте изменения в ваш форк (`git push origin feature/AmazingFeature`)
5. Откройте Pull Request

## 📄 Лицензия

Этот проект распространяется под лицензией MIT. См. файл `LICENSE` для дополнительной информации.

---

<div align="center">
  <sub>Создано с ❤️ для разработчиков</sub>
</div>
