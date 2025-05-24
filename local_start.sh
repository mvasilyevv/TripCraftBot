#!/bin/bash

# Скрипт для локального запуска TripCraftBot
# Использует кеширование Docker для быстрой пересборки

set -e  # Остановка при ошибке

echo "🚀 Запуск TripCraftBot локально..."

# Проверяем, что Docker запущен
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker не запущен. Запустите Docker Desktop и попробуйте снова."
    exit 1
fi

# Проверяем наличие .env файла
if [ ! -f .env ]; then
    echo "❌ Файл .env не найден. Создайте его на основе .env.example"
    exit 1
fi

# Останавливаем существующие контейнеры
echo "🛑 Останавливаем существующие контейнеры..."
docker compose down --remove-orphans 2>/dev/null || true

# Удаляем старый образ бота для принудительной пересборки
echo "🗑️  Удаляем старый образ бота..."
docker rmi tripcraftbot-tripcraft-bot 2>/dev/null || true

# Собираем и запускаем с кешированием
echo "🔨 Пересобираем и запускаем контейнеры..."
docker compose up --build --force-recreate

echo "✅ TripCraftBot запущен!"
echo "📊 Ngrok UI доступен на: http://localhost:4040"
echo "📋 Логи бота: docker logs tripcraft-bot -f"
echo "🛑 Остановка: Ctrl+C или docker compose down"
