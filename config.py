"""Конфигурация для TraveleBot"""

import os
import sys
from dotenv import load_dotenv

load_dotenv()

def get_telegram_token() -> str:
    """Получает токен Telegram бота из переменных окружения"""
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        print("Ошибка: TELEGRAM_BOT_TOKEN не установлен в переменных окружения")
        sys.exit(1)
    return token


def get_openrouter_key() -> str:
    """Получает ключ OpenRouter API из переменных окружения"""
    key = os.getenv("OPENROUTER_API_KEY")
    if not key:
        print("Ошибка: OPENROUTER_API_KEY не установлен в переменных окружения")
        sys.exit(1)
    return key


# Обязательные переменные окружения
TELEGRAM_BOT_TOKEN = get_telegram_token()
OPENROUTER_API_KEY = get_openrouter_key()

OPENROUTER_BASE_URL = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
PRIMARY_MODEL = os.getenv(
    "PRIMARY_MODEL", "perplexity/llama-3.1-sonar-large-128k-online"
)
FALLBACK_MODEL = os.getenv("FALLBACK_MODEL", "anthropic/claude-3-haiku")
API_TIMEOUT = int(os.getenv("API_TIMEOUT", "30"))
API_RETRIES = int(os.getenv("API_RETRIES", "2"))

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_DB = int(os.getenv("REDIS_DB", "0"))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD")
REDIS_SSL = os.getenv("REDIS_SSL", "false").lower() == "true"
FSM_TTL = int(os.getenv("FSM_TTL", "3600"))

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
DEBUG = os.getenv("DEBUG", "false").lower() == "true"


def get_redis_url() -> str:
    """Формирует URL для подключения к Redis"""
    scheme = "rediss" if REDIS_SSL else "redis"
    auth = f":{REDIS_PASSWORD}@" if REDIS_PASSWORD else ""
    return f"{scheme}://{auth}{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}"
