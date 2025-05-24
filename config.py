"""Конфигурация для TripCraftBot"""

import logging
import os
import sys

from dotenv import load_dotenv
from pydantic import ValidationError

from bot.infrastructure.config_validator import (
    AppConfig,
    BotConfiguration,
    ConfigurationError,
    LoggingConfig,
    OpenRouterConfig,
    RedisConfig,
    TelegramConfig,
)

load_dotenv()

logger = logging.getLogger(__name__)


def _get_env_or_exit(key: str, description: str) -> str:
    """Получает переменную окружения или завершает программу"""
    value = os.getenv(key)
    if not value:
        print(f"Ошибка: {key} не установлен в переменных окружения ({description})")
        sys.exit(1)
    return value


def _get_env_bool(key: str, default: bool = False) -> bool:
    """Получает булево значение из переменной окружения"""
    value = os.getenv(key, str(default)).lower()
    return value in ("true", "1", "yes", "on")


def _get_env_int(key: str, default: int) -> int:
    """Получает целое число из переменной окружения"""
    try:
        return int(os.getenv(key, str(default)))
    except ValueError:
        logger.warning(
            "Некорректное значение для %s, используется значение по умолчанию: %d",
            key,
            default,
        )
        return default


def create_configuration() -> BotConfiguration:
    """Создает и валидирует конфигурацию бота"""
    try:
        # Создаем конфигурацию из переменных окружения
        config = BotConfiguration(
            telegram=TelegramConfig(
                bot_token=_get_env_or_exit("TELEGRAM_BOT_TOKEN", "токен Telegram бота"),
                webhook_url=os.getenv("TELEGRAM_WEBHOOK_URL"),
                webhook_secret_token=os.getenv("TELEGRAM_WEBHOOK_SECRET_TOKEN"),
                webhook_max_connections=_get_env_int("TELEGRAM_WEBHOOK_MAX_CONNECTIONS", 40),
                webhook_allowed_updates=os.getenv("TELEGRAM_WEBHOOK_ALLOWED_UPDATES", "").split(",") if os.getenv("TELEGRAM_WEBHOOK_ALLOWED_UPDATES") else None,
                use_webhook=_get_env_bool("USE_WEBHOOK", False),
            ),
            openrouter=OpenRouterConfig(
                api_key=_get_env_or_exit("OPENROUTER_API_KEY", "ключ OpenRouter API"),
                base_url=os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"),
                primary_model=os.getenv(
                    "PRIMARY_MODEL", "perplexity/llama-3.1-sonar-large-128k-online"
                ),
                fallback_model=os.getenv("FALLBACK_MODEL", "anthropic/claude-3-haiku"),
                timeout=_get_env_int("API_TIMEOUT", 30),
                retries=_get_env_int("API_RETRIES", 2),
            ),
            redis=RedisConfig(
                host=os.getenv("REDIS_HOST", "localhost"),
                port=_get_env_int("REDIS_PORT", 6379),
                db=_get_env_int("REDIS_DB", 0),
                password=os.getenv("REDIS_PASSWORD"),
                ssl=_get_env_bool("REDIS_SSL", False),
                fsm_ttl=_get_env_int("FSM_TTL", 3600),
            ),
            logging=LoggingConfig(
                level=os.getenv("LOG_LEVEL", "INFO"),
                format=os.getenv(
                    "LOG_FORMAT", "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
                ),
            ),
            app=AppConfig(
                debug=_get_env_bool("DEBUG", False),
                environment=os.getenv("ENVIRONMENT", "production"),
            ),
        )

        # Дополнительная валидация
        config.validate_configuration()

        return config

    except ValidationError as e:
        error_messages = []
        for error in e.errors():
            field = " -> ".join(str(loc) for loc in error["loc"])
            message = error["msg"]
            error_messages.append(f"{field}: {message}")

        raise ConfigurationError(
            "Ошибки валидации конфигурации:\n" + "\n".join(error_messages)
        ) from e
    except Exception as e:
        raise ConfigurationError(f"Ошибка создания конфигурации: {str(e)}") from e


# Создаем глобальную конфигурацию
try:
    CONFIG = create_configuration()
except ConfigurationError as e:
    print(f"Критическая ошибка конфигурации: {e}")
    sys.exit(1)

# Экспортируем значения для обратной совместимости
TELEGRAM_BOT_TOKEN = CONFIG.telegram.bot_token
OPENROUTER_API_KEY = CONFIG.openrouter.api_key
OPENROUTER_BASE_URL = CONFIG.openrouter.base_url
PRIMARY_MODEL = CONFIG.openrouter.primary_model
FALLBACK_MODEL = CONFIG.openrouter.fallback_model
API_TIMEOUT = CONFIG.openrouter.timeout
API_RETRIES = CONFIG.openrouter.retries

REDIS_HOST = CONFIG.redis.host
REDIS_PORT = CONFIG.redis.port
REDIS_DB = CONFIG.redis.db
REDIS_PASSWORD = CONFIG.redis.password
REDIS_SSL = CONFIG.redis.ssl
FSM_TTL = CONFIG.redis.fsm_ttl

LOG_LEVEL = CONFIG.logging.level
DEBUG = CONFIG.app.debug


def get_redis_url() -> str:
    """Формирует URL для подключения к Redis"""
    return CONFIG.get_redis_url()


def get_config() -> BotConfiguration:
    """Возвращает текущую конфигурацию"""
    return CONFIG
