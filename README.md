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