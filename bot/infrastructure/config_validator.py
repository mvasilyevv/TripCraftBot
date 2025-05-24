"""Валидация конфигурации с использованием Pydantic"""

import logging
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class ConfigurationError(Exception):
    """Ошибка конфигурации"""
    pass

logger = logging.getLogger(__name__)


class TelegramConfig(BaseModel):
    """Конфигурация Telegram бота"""

    bot_token: str = Field(..., min_length=1, description="Токен Telegram бота")
    webhook_url: Optional[str] = Field(default=None, description="URL для webhook")

    @field_validator("bot_token")
    @classmethod
    def validate_bot_token(cls, v: str) -> str:
        """Валидирует токен Telegram бота"""
        if not v.count(":") == 1:
            raise ValueError("Токен должен содержать ровно один символ ':'")

        parts = v.split(":")
        if not parts[0].isdigit():
            raise ValueError("Первая часть токена должна быть числом")

        if len(parts[1]) < 35:
            raise ValueError("Вторая часть токена слишком короткая")

        return v

    @field_validator("webhook_url")
    @classmethod
    def validate_webhook_url(cls, v: Optional[str]) -> Optional[str]:
        """Валидирует URL webhook"""
        if v is None:
            return v

        if not v.startswith(("http://", "https://")):
            raise ValueError("URL webhook должен начинаться с http:// или https://")

        return v


class OpenRouterConfig(BaseModel):
    """Конфигурация OpenRouter API"""

    api_key: str = Field(..., min_length=10, description="Ключ OpenRouter API")
    base_url: str = Field(
        default="https://openrouter.ai/api/v1", description="Базовый URL API"
    )
    primary_model: str = Field(
        default="perplexity/llama-3.1-sonar-large-128k-online",
        description="Основная модель",
    )
    fallback_model: str = Field(
        default="anthropic/claude-3-haiku", description="Резервная модель"
    )
    timeout: int = Field(
        default=30, ge=5, le=300, description="Таймаут запроса в секундах"
    )
    retries: int = Field(
        default=2, ge=0, le=10, description="Количество повторных попыток"
    )

    @field_validator("api_key")
    @classmethod
    def validate_api_key(cls, v: str) -> str:
        """Валидирует ключ API"""
        if not v.startswith(("sk-", "or-")):
            raise ValueError("Ключ API должен начинаться с 'sk-' или 'or-'")
        return v

    @field_validator("base_url")
    @classmethod
    def validate_base_url(cls, v: str) -> str:
        """Валидирует базовый URL"""
        if not v.startswith(("http://", "https://")):
            raise ValueError("Базовый URL должен начинаться с http:// или https://")
        return v


class RedisConfig(BaseModel):
    """Конфигурация Redis"""

    host: str = Field(default="localhost", description="Хост Redis")
    port: int = Field(default=6379, ge=1, le=65535, description="Порт Redis")
    db: int = Field(default=0, ge=0, le=15, description="Номер базы данных")
    password: Optional[str] = Field(default=None, description="Пароль Redis")
    ssl: bool = Field(default=False, description="Использовать SSL")
    fsm_ttl: int = Field(
        default=3600, ge=300, le=86400, description="TTL для состояний FSM в секундах"
    )

    @field_validator("host")
    @classmethod
    def validate_host(cls, v: str) -> str:
        """Валидирует хост"""
        if not v.strip():
            raise ValueError("Хост не может быть пустым")
        return v.strip()


class LoggingConfig(BaseModel):
    """Конфигурация логирования"""

    level: str = Field(default="INFO", description="Уровень логирования")
    format: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        description="Формат логов",
    )

    @field_validator("level")
    @classmethod
    def validate_level(cls, v: str) -> str:
        """Валидирует уровень логирования"""
        valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        v_upper = v.upper()
        if v_upper not in valid_levels:
            raise ValueError(
                f"Уровень логирования должен быть одним из: {valid_levels}"
            )
        return v_upper


class AppConfig(BaseModel):
    """Общая конфигурация приложения"""

    debug: bool = Field(default=False, description="Режим отладки")
    environment: str = Field(default="production", description="Окружение")

    @field_validator("environment")
    @classmethod
    def validate_environment(cls, v: str) -> str:
        """Валидирует окружение"""
        valid_environments = {"development", "testing", "production"}
        v_lower = v.lower()
        if v_lower not in valid_environments:
            raise ValueError(f"Окружение должно быть одним из: {valid_environments}")
        return v_lower


class BotConfiguration(BaseModel):
    """Полная конфигурация бота"""

    telegram: TelegramConfig
    openrouter: OpenRouterConfig
    redis: RedisConfig
    logging: LoggingConfig
    app: AppConfig

    def get_redis_url(self) -> str:
        """Формирует URL для подключения к Redis"""
        scheme = "rediss" if self.redis.ssl else "redis"
        auth = f":{self.redis.password}@" if self.redis.password else ""
        return f"{scheme}://{auth}{self.redis.host}:{self.redis.port}/{self.redis.db}"

    def validate_configuration(self) -> None:
        """Дополнительная валидация конфигурации"""
        try:
            # Проверяем, что все обязательные поля заполнены
            if not self.telegram.bot_token:
                raise ConfigurationError("Токен Telegram бота не установлен")

            if not self.openrouter.api_key:
                raise ConfigurationError("Ключ OpenRouter API не установлен")

            # Проверяем совместимость настроек
            if self.app.debug and self.app.environment == "production":
                logger.warning(
                    "Режим отладки включен в production окружении. "
                    "Это может привести к утечке конфиденциальной информации."
                )

            # Проверяем разумность настроек
            if self.openrouter.timeout > 120:
                logger.warning(
                    "Таймаут OpenRouter API больше 2 минут. "
                    "Это может привести к долгому ожиданию пользователей."
                )

            if self.redis.fsm_ttl < 600:
                logger.warning(
                    "TTL для состояний FSM меньше 10 минут. "
                    "Пользователи могут потерять прогресс слишком быстро."
                )

            logger.info("Конфигурация успешно валидирована")

        except Exception as e:
            raise ConfigurationError(f"Ошибка валидации конфигурации: {str(e)}") from e
