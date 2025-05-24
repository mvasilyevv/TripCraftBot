"""Тесты для OpenRouter клиента"""

from typing import Any, Dict
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from bot.domain.models import ExternalServiceError
from bot.utils.openrouter import OpenRouterClient, OpenRouterMessage


@pytest.fixture
def openrouter_client() -> OpenRouterClient:
    """Фикстура для создания клиента OpenRouter"""
    return OpenRouterClient(
        api_key="test-api-key",
        base_url="https://test.openrouter.ai/api/v1",
        primary_model="test/primary-model",
        fallback_model="test/fallback-model",
        timeout=10,
        retries=1,
    )


@pytest.fixture
def mock_response() -> Dict[str, Any]:
    """Фикстура для мокового ответа от API"""
    return {
        "id": "test-response-id",
        "model": "test/primary-model",
        "choices": [{"message": {"content": "Тестовый ответ от модели"}}],
        "usage": {"total_tokens": 100},
    }


@pytest.mark.asyncio
async def test_generate_completion_success(
    openrouter_client: OpenRouterClient, mock_response: Dict[str, Any]
) -> None:
    """Тест успешной генерации ответа"""
    messages = [OpenRouterMessage(role="user", content="Тестовое сообщение")]

    with patch("httpx.AsyncClient") as mock_client:
        mock_response_obj = MagicMock()
        mock_response_obj.status_code = 200
        mock_response_obj.json.return_value = mock_response

        mock_client.return_value.__aenter__.return_value.post = AsyncMock(
            return_value=mock_response_obj
        )

        result = await openrouter_client.generate_completion(messages)

        assert result == "Тестовый ответ от модели"
        mock_client.return_value.__aenter__.return_value.post.assert_called_once()


@pytest.mark.asyncio
async def test_generate_completion_fallback_model(
    openrouter_client: OpenRouterClient, mock_response: Dict[str, Any]
) -> None:
    """Тест переключения на fallback модель при ошибке основной"""
    messages = [OpenRouterMessage(role="user", content="Тестовое сообщение")]

    # Мокаем ответ для fallback модели
    fallback_response = mock_response.copy()
    fallback_response["model"] = "test/fallback-model"

    with patch("httpx.AsyncClient") as mock_client:
        # Первый вызов (основная модель) - ошибка 500
        error_response = MagicMock()
        error_response.status_code = 500
        error_response.text = "Internal Server Error"

        # Второй вызов (fallback модель) - успех
        success_response = MagicMock()
        success_response.status_code = 200
        success_response.json.return_value = fallback_response

        mock_client.return_value.__aenter__.return_value.post = AsyncMock(
            side_effect=[error_response, success_response]
        )

        result = await openrouter_client.generate_completion(messages)

        assert result == "Тестовый ответ от модели"
        assert mock_client.return_value.__aenter__.return_value.post.call_count == 2


@pytest.mark.asyncio
async def test_generate_completion_rate_limit_retry(
    openrouter_client: OpenRouterClient, mock_response: Dict[str, Any]
) -> None:
    """Тест повторной попытки при rate limit"""
    messages = [OpenRouterMessage(role="user", content="Тестовое сообщение")]

    with patch("httpx.AsyncClient") as mock_client, patch(
        "asyncio.sleep", new_callable=AsyncMock
    ) as mock_sleep:
        # Первый вызов - rate limit
        rate_limit_response = MagicMock()
        rate_limit_response.status_code = 429

        # Второй вызов - успех
        success_response = MagicMock()
        success_response.status_code = 200
        success_response.json.return_value = mock_response

        mock_client.return_value.__aenter__.return_value.post = AsyncMock(
            side_effect=[rate_limit_response, success_response]
        )

        result = await openrouter_client.generate_completion(messages)

        assert result == "Тестовый ответ от модели"
        mock_sleep.assert_called_once_with(1)  # Ожидание перед повторной попыткой


@pytest.mark.asyncio
async def test_generate_completion_timeout_error(openrouter_client: OpenRouterClient) -> None:
    """Тест обработки таймаута"""
    messages = [OpenRouterMessage(role="user", content="Тестовое сообщение")]

    with patch("httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value.post = AsyncMock(
            side_effect=httpx.TimeoutException("Request timeout")
        )

        with pytest.raises(ExternalServiceError, match="Таймаут запроса"):
            await openrouter_client.generate_completion(messages)


@pytest.mark.asyncio
async def test_generate_completion_network_error(openrouter_client: OpenRouterClient) -> None:
    """Тест обработки сетевой ошибки"""
    messages = [OpenRouterMessage(role="user", content="Тестовое сообщение")]

    with patch("httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value.post = AsyncMock(
            side_effect=httpx.RequestError("Network error")
        )

        with pytest.raises(ExternalServiceError, match="Ошибка сети"):
            await openrouter_client.generate_completion(messages)


@pytest.mark.asyncio
async def test_generate_completion_empty_response(openrouter_client: OpenRouterClient) -> None:
    """Тест обработки пустого ответа"""
    messages = [OpenRouterMessage(role="user", content="Тестовое сообщение")]

    empty_response = {"id": "test-response-id", "model": "test/primary-model", "choices": []}

    with patch("httpx.AsyncClient") as mock_client:
        mock_response_obj = MagicMock()
        mock_response_obj.status_code = 200
        mock_response_obj.json.return_value = empty_response

        mock_client.return_value.__aenter__.return_value.post = AsyncMock(
            return_value=mock_response_obj
        )

        with pytest.raises(ExternalServiceError, match="Пустой ответ"):
            await openrouter_client.generate_completion(messages)


@pytest.mark.asyncio
async def test_generate_completion_client_error(openrouter_client: OpenRouterClient) -> None:
    """Тест обработки клиентской ошибки (4xx)"""
    messages = [OpenRouterMessage(role="user", content="Тестовое сообщение")]

    with patch("httpx.AsyncClient") as mock_client:
        error_response = MagicMock()
        error_response.status_code = 400
        error_response.text = "Bad Request"
        error_response.json.return_value = {"error": {"message": "Invalid request format"}}

        mock_client.return_value.__aenter__.return_value.post = AsyncMock(
            return_value=error_response
        )

        with pytest.raises(ExternalServiceError, match="Invalid request format"):
            await openrouter_client.generate_completion(messages)


@pytest.mark.asyncio
async def test_check_health_success(openrouter_client: OpenRouterClient) -> None:
    """Тест успешной проверки здоровья API"""
    mock_response = {
        "id": "health-check",
        "model": "test/primary-model",
        "choices": [{"message": {"content": "OK"}}],
    }

    with patch("httpx.AsyncClient") as mock_client:
        mock_response_obj = MagicMock()
        mock_response_obj.status_code = 200
        mock_response_obj.json.return_value = mock_response

        mock_client.return_value.__aenter__.return_value.post = AsyncMock(
            return_value=mock_response_obj
        )

        result = await openrouter_client.check_health()
        assert result is True


@pytest.mark.asyncio
async def test_check_health_failure(openrouter_client: OpenRouterClient) -> None:
    """Тест неудачной проверки здоровья API"""
    with patch("httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value.post = AsyncMock(
            side_effect=httpx.RequestError("Connection failed")
        )

        result = await openrouter_client.check_health()
        assert result is False


def test_openrouter_message_creation() -> None:
    """Тест создания сообщения OpenRouter"""
    message = OpenRouterMessage(role="user", content="Тест")
    assert message.role == "user"
    assert message.content == "Тест"


def test_openrouter_client_initialization() -> None:
    """Тест инициализации клиента OpenRouter"""
    client = OpenRouterClient(
        api_key="test-key",
        base_url="https://test.api.com",
        primary_model="primary",
        fallback_model="fallback",
        timeout=30,
        retries=3,
    )

    assert client._api_key == "test-key"
    assert client._base_url == "https://test.api.com"
    assert client._primary_model == "primary"
    assert client._fallback_model == "fallback"
    assert client._timeout == 30
    assert client._retries == 3
