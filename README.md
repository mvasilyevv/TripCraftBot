# TripCraftBot

Telegram бот для планирования путешествий

## Установка

1. Клонируйте репозиторий:
```bash
git clone https://github.com/mvasilyevv/TripCraftBot.git
cd TripCraftBot
```

2. Создайте виртуальное окружение:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# или
venv\Scripts\activate  # Windows
```

3. Установите зависимости:
```bash
pip install -r requirements.txt
```

4. Скопируйте файл конфигурации:
```bash
cp .env.example .env
```

5. Заполните переменные окружения в файле `.env`:
```
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
OPENROUTER_API_KEY=your_openrouter_api_key
```

## Запуск

### Локальная разработка

1. Запустите Redis:
```bash
redis-server
```

2. Запустите бота:
```bash
python main.py
```

### Настройка pre-commit hooks

```bash
pre-commit install
```

## Структура проекта

```
TripCraftBot/
├── bot/
│   ├── handlers/          # Обработчики событий
│   ├── keyboards/         # Inline клавиатуры
│   ├── states/           # FSM состояния
│   └── utils/            # Утилиты
├── config.py             # Конфигурация
├── main.py              # Точка входа
├── requirements.txt     # Все зависимости
└── docs/               # Документация
```

## Разработка

### Качество кода

Проект использует следующие инструменты:
- `black` - форматирование кода
- `isort` - сортировка импортов
- `flake8` - линтинг
- `mypy` - проверка типов
- `pytest` - тестирование

### Запуск тестов

```bash
pytest
```

### Проверка качества кода

```bash
black .
isort .
flake8 .
mypy .
```

## Архитектура

Бот построен на принципах "Чистой архитектуры":

1. **Handlers** - обработчики событий Telegram
2. **States** - состояния FSM для диалогов
3. **Keyboards** - inline клавиатуры
4. **Utils** - утилиты для работы с внешними API

## Технологии

- **aiogram 3.x** - фреймворк для Telegram ботов
- **Redis** - хранение состояний FSM
- **OpenRouter API** - доступ к LLM моделям
- **python-dotenv** - управление переменными окружения

## Лицензия