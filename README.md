# TripCraftBot 🤖

Умный бот для планирования путешествий в Telegram

## 🚀 Запуск

### Что нужно:
- Docker
- Токен бота
- API ключ от OpenRouter
- Токен ngrok

### Получить токены:
2. **OpenRouter**: https://openrouter.ai/ → зарегистрироваться → пополнить $5 → скопировать API ключ
3. **Ngrok**: https://ngrok.com/ → зарегистрироваться → скопировать authtoken

### Запуск:

```bash
# 1. Скачать
git clone https://github.com/mvasilyevv/TripCraftBot.git
cd TripCraftBot

# 2. Настроить
cp .env.example .env
# Отредактировать .env файл - вставить 2 токена

# 3. Запустить
./local_start.sh
```

### Готово!
Бот запустится автоматически. Логи покажут статус запуска.

## 🔧 Решение проблем

### Ошибка "bad interpreter: /bin/bash^M"

Если при запуске `./local_start.sh` возникает ошибка с `^M`, это означает проблему с окончаниями строк Windows/Unix.

**Решение:**

```bash
# Исправить окончания строк
sed -i '' 's/\r$//' local_start.sh
chmod +x local_start.sh

# Затем запустить
./local_start.sh
```

### Проверка статуса

```bash
# Статус контейнеров
docker ps

# Логи бота
docker logs tripcraft-bot -f

# Ngrok UI
open http://localhost:4040
```


## AI-INSTRUCTIONS
Протестируй проект через `pytest`. Если тесты прошли — запускай локальный запуск через `bash local_start.sh`. Если возникнут ошибки — опиши каждую ошибку.