# Используем официальный Python образ
FROM python:3.11-slim

# Устанавливаем системные зависимости
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Создаем рабочую директорию
WORKDIR /app

# Копируем файлы зависимостей ПЕРВЫМИ для лучшего кеширования
COPY requirements.txt ./

# Устанавливаем Python зависимости с кешированием pip
RUN pip install --upgrade pip && \
    pip install --cache-dir=/tmp/pip-cache -r requirements.txt

# Копируем код приложения (это будет пересобираться при изменениях кода)
COPY . .

# Создаем директорию для логов
RUN mkdir -p /app/logs

# Открываем порт
EXPOSE 8000

# Устанавливаем переменные окружения по умолчанию
ENV USE_WEBHOOK=true
ENV PYTHONUNBUFFERED=1

# Запускаем бота напрямую
CMD ["python", "main.py"]
