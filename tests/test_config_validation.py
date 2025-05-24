"""Тесты для валидации конфигурации"""

import pytest
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


class TestTelegramConfig:
    """Тесты для конфигурации Telegram"""

    def test_valid_telegram_config(self) -> None:
        """Тест валидной конфигурации Telegram"""
        config = TelegramConfig(
            bot_token="123456789:ABCdefGHIjklMNOpqrsTUVwxyz-1234567890",
            webhook_url="https://example.com/webhook",
        )

        assert config.bot_token == "123456789:ABCdefGHIjklMNOpqrsTUVwxyz-1234567890"
        assert config.webhook_url == "https://example.com/webhook"

    def test_invalid_bot_token_format(self) -> None:
        """Тест невалидного формата токена"""
        with pytest.raises(ValidationError) as exc_info:
            TelegramConfig(
                bot_token="1234567890123456789012345678901234567890invalid_token_without_colon"
            )

        errors = exc_info.value.errors()
        assert any("Токен должен содержать ровно один символ ':'" in str(error) for error in errors)

    def test_invalid_bot_token_short(self) -> None:
        """Тест слишком короткого токена"""
        with pytest.raises(ValidationError) as exc_info:
            TelegramConfig(bot_token="1234567890123456789012345678901234567890:short")

        errors = exc_info.value.errors()
        assert any("Вторая часть токена слишком короткая" in str(error) for error in errors)

    def test_invalid_webhook_url(self) -> None:
        """Тест невалидного URL webhook"""
        with pytest.raises(ValidationError) as exc_info:
            TelegramConfig(
                bot_token="123456789:ABCdefGHIjklMNOpqrsTUVwxyz-1234567890",
                webhook_url="invalid_url",
            )

        errors = exc_info.value.errors()
        assert any("URL webhook должен начинаться с http://" in str(error) for error in errors)


class TestOpenRouterConfig:
    """Тесты для конфигурации OpenRouter"""

    def test_valid_openrouter_config(self) -> None:
        """Тест валидной конфигурации OpenRouter"""
        config = OpenRouterConfig(
            api_key="sk-1234567890abcdef",
            base_url="https://openrouter.ai/api/v1",
            timeout=30,
            retries=2,
        )

        assert config.api_key == "sk-1234567890abcdef"
        assert config.base_url == "https://openrouter.ai/api/v1"
        assert config.timeout == 30
        assert config.retries == 2

    def test_invalid_api_key(self) -> None:
        """Тест невалидного ключа API"""
        with pytest.raises(ValidationError) as exc_info:
            OpenRouterConfig(api_key="invalid_key")

        errors = exc_info.value.errors()
        assert any("Ключ API должен начинаться с 'sk-' или 'or-'" in str(error) for error in errors)

    def test_invalid_base_url(self) -> None:
        """Тест невалидного базового URL"""
        with pytest.raises(ValidationError) as exc_info:
            OpenRouterConfig(
                api_key="sk-1234567890abcdef",
                base_url="invalid_url",
            )

        errors = exc_info.value.errors()
        assert any("Базовый URL должен начинаться с http://" in str(error) for error in errors)

    def test_invalid_timeout_range(self) -> None:
        """Тест невалидного диапазона таймаута"""
        with pytest.raises(ValidationError):
            OpenRouterConfig(
                api_key="sk-1234567890abcdef",
                timeout=1,  # Меньше минимума
            )

        with pytest.raises(ValidationError):
            OpenRouterConfig(
                api_key="sk-1234567890abcdef",
                timeout=500,  # Больше максимума
            )


class TestRedisConfig:
    """Тесты для конфигурации Redis"""

    def test_valid_redis_config(self) -> None:
        """Тест валидной конфигурации Redis"""
        config = RedisConfig(
            host="localhost",
            port=6379,
            db=0,
            password="secret",
            ssl=True,
            fsm_ttl=3600,
        )

        assert config.host == "localhost"
        assert config.port == 6379
        assert config.db == 0
        assert config.password == "secret"
        assert config.ssl is True
        assert config.fsm_ttl == 3600

    def test_invalid_port_range(self) -> None:
        """Тест невалидного диапазона порта"""
        with pytest.raises(ValidationError):
            RedisConfig(port=0)  # Меньше минимума

        with pytest.raises(ValidationError):
            RedisConfig(port=70000)  # Больше максимума

    def test_empty_host(self) -> None:
        """Тест пустого хоста"""
        with pytest.raises(ValidationError) as exc_info:
            RedisConfig(host="   ")

        errors = exc_info.value.errors()
        assert any("Хост не может быть пустым" in str(error) for error in errors)


class TestLoggingConfig:
    """Тесты для конфигурации логирования"""

    def test_valid_logging_config(self) -> None:
        """Тест валидной конфигурации логирования"""
        config = LoggingConfig(level="DEBUG")

        assert config.level == "DEBUG"

    def test_invalid_log_level(self) -> None:
        """Тест невалидного уровня логирования"""
        with pytest.raises(ValidationError) as exc_info:
            LoggingConfig(level="INVALID")

        errors = exc_info.value.errors()
        assert any("Уровень логирования должен быть одним из:" in str(error) for error in errors)

    def test_case_insensitive_log_level(self) -> None:
        """Тест нечувствительности к регистру уровня логирования"""
        config = LoggingConfig(level="info")
        assert config.level == "INFO"


class TestAppConfig:
    """Тесты для конфигурации приложения"""

    def test_valid_app_config(self) -> None:
        """Тест валидной конфигурации приложения"""
        config = AppConfig(debug=True, environment="development")

        assert config.debug is True
        assert config.environment == "development"

    def test_invalid_environment(self) -> None:
        """Тест невалидного окружения"""
        with pytest.raises(ValidationError) as exc_info:
            AppConfig(environment="invalid")

        errors = exc_info.value.errors()
        assert any("Окружение должно быть одним из:" in str(error) for error in errors)


class TestBotConfiguration:
    """Тесты для полной конфигурации бота"""

    def test_valid_bot_configuration(self) -> None:
        """Тест валидной конфигурации бота"""
        config = BotConfiguration(
            telegram=TelegramConfig(
                bot_token="123456789:ABCdefGHIjklMNOpqrsTUVwxyz-1234567890"
            ),
            openrouter=OpenRouterConfig(api_key="sk-1234567890abcdef"),
            redis=RedisConfig(),
            logging=LoggingConfig(),
            app=AppConfig(),
        )

        assert config.telegram.bot_token == "123456789:ABCdefGHIjklMNOpqrsTUVwxyz-1234567890"
        assert config.openrouter.api_key == "sk-1234567890abcdef"

    def test_get_redis_url(self) -> None:
        """Тест формирования URL Redis"""
        config = BotConfiguration(
            telegram=TelegramConfig(
                bot_token="123456789:ABCdefGHIjklMNOpqrsTUVwxyz-1234567890"
            ),
            openrouter=OpenRouterConfig(api_key="sk-1234567890abcdef"),
            redis=RedisConfig(host="localhost", port=6379, db=0, password="secret"),
            logging=LoggingConfig(),
            app=AppConfig(),
        )

        url = config.get_redis_url()
        assert url == "redis://:secret@localhost:6379/0"

    def test_get_redis_url_with_ssl(self) -> None:
        """Тест формирования URL Redis с SSL"""
        config = BotConfiguration(
            telegram=TelegramConfig(
                bot_token="123456789:ABCdefGHIjklMNOpqrsTUVwxyz-1234567890"
            ),
            openrouter=OpenRouterConfig(api_key="sk-1234567890abcdef"),
            redis=RedisConfig(ssl=True),
            logging=LoggingConfig(),
            app=AppConfig(),
        )

        url = config.get_redis_url()
        assert url == "rediss://localhost:6379/0"

    def test_validate_configuration_warnings(self) -> None:
        """Тест предупреждений при валидации конфигурации"""
        config = BotConfiguration(
            telegram=TelegramConfig(
                bot_token="123456789:ABCdefGHIjklMNOpqrsTUVwxyz-1234567890"
            ),
            openrouter=OpenRouterConfig(
                api_key="sk-1234567890abcdef",
                timeout=150,  # Большой таймаут
            ),
            redis=RedisConfig(fsm_ttl=300),  # Маленький TTL
            logging=LoggingConfig(),
            app=AppConfig(debug=True, environment="production"),  # Debug в production
        )

        # Не должно вызывать исключение, только предупреждения
        config.validate_configuration()

    def test_validate_configuration_missing_token(self) -> None:
        """Тест валидации с отсутствующим токеном"""
        # Создаем конфигурацию с пустым токеном, обходя pydantic валидацию
        config = BotConfiguration(
            telegram=TelegramConfig(bot_token="x"),  # Минимальный токен
            openrouter=OpenRouterConfig(api_key="sk-1234567890abcdef"),
            redis=RedisConfig(),
            logging=LoggingConfig(),
            app=AppConfig(),
        )

        # Вручную устанавливаем пустой токен
        config.telegram.bot_token = ""

        with pytest.raises(ConfigurationError) as exc_info:
            config.validate_configuration()

        assert "Токен Telegram бота не установлен" in str(exc_info.value)
