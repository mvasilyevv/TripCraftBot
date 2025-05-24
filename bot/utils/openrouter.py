"""Клиент для OpenRouter API"""

import asyncio
import json
import logging
from typing import Any

import httpx
from pydantic import BaseModel, Field

from bot.domain.models import ExternalServiceError

logger = logging.getLogger(__name__)


class OpenRouterMessage(BaseModel):
    """Сообщение для OpenRouter API"""

    role: str = Field(..., description="Роль отправителя")
    content: str = Field(..., description="Содержимое сообщения")


class OpenRouterRequest(BaseModel):
    """Запрос к OpenRouter API"""

    model: str = Field(..., description="Модель для использования")
    messages: list[OpenRouterMessage] = Field(..., description="Список сообщений")
    max_tokens: int | None = Field(default=2000, description="Максимальное количество токенов")
    temperature: float | None = Field(default=0.7, description="Температура генерации")
    top_p: float | None = Field(default=0.9, description="Top-p параметр")


class OpenRouterResponse(BaseModel):
    """Ответ от OpenRouter API"""

    id: str = Field(..., description="ID ответа")
    model: str = Field(..., description="Использованная модель")
    choices: list[dict[str, Any]] = Field(..., description="Варианты ответов")
    usage: dict[str, Any] | None = Field(default=None, description="Информация об использовании")


class OpenRouterClient:
    """Клиент для работы с OpenRouter API"""

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://openrouter.ai/api/v1",
        primary_model: str = "perplexity/llama-3.1-sonar-large-128k-online",
        fallback_model: str = "anthropic/claude-3-haiku",
        timeout: int = 30,
        retries: int = 2,
    ) -> None:
        """
        Инициализирует клиент OpenRouter API

        Args:
            api_key: Ключ API для OpenRouter
            base_url: Базовый URL API
            primary_model: Основная модель для использования
            fallback_model: Резервная модель при ошибках
            timeout: Таймаут запроса в секундах
            retries: Количество повторных попыток
        """
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._primary_model = primary_model
        self._fallback_model = fallback_model
        self._timeout = timeout
        self._retries = retries

        self._headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/mvasilyevv/TripCraftBot",
            "X-Title": "TripCraftBot",
        }

    async def generate_completion(
        self,
        messages: list[OpenRouterMessage],
        model: str | None = None,
        max_tokens: int = 2000,
        temperature: float = 0.7,
    ) -> str:
        """
        Генерирует ответ от LLM модели

        Args:
            messages: Список сообщений для отправки
            model: Модель для использования (если не указана, используется primary_model)
            max_tokens: Максимальное количество токенов в ответе
            temperature: Температура генерации (0.0-1.0)

        Returns:
            Сгенерированный текст ответа

        Raises:
            ExternalServiceError: При ошибках API или сети
        """
        target_model = model or self._primary_model

        request_data = OpenRouterRequest(
            model=target_model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
        )

        # Пытаемся с основной моделью
        try:
            return await self._make_request(request_data)
        except ExternalServiceError as e:
            logger.warning(
                "Ошибка с основной моделью %s: %s. Пробуем резервную модель %s",
                target_model,
                str(e),
                self._fallback_model,
            )

            # Если основная модель не сработала, пробуем резервную
            if target_model != self._fallback_model:
                request_data.model = self._fallback_model
                try:
                    return await self._make_request(request_data)
                except ExternalServiceError as fallback_error:
                    logger.error(
                        "Ошибка и с резервной моделью %s: %s",
                        self._fallback_model,
                        str(fallback_error),
                    )
                    raise ExternalServiceError(
                        f"Обе модели недоступны. Основная: {str(e)}, "
                        f"Резервная: {str(fallback_error)}"
                    ) from fallback_error
            else:
                raise

    async def _make_request(self, request_data: OpenRouterRequest) -> str:
        """
        Выполняет HTTP запрос к OpenRouter API с retry логикой

        Args:
            request_data: Данные запроса

        Returns:
            Сгенерированный текст ответа

        Raises:
            ExternalServiceError: При ошибках API или сети
        """
        url = f"{self._base_url}/chat/completions"

        for attempt in range(self._retries + 1):
            try:
                async with httpx.AsyncClient(timeout=self._timeout) as client:
                    logger.debug(
                        "Отправка запроса к OpenRouter (попытка %d/%d): модель=%s",
                        attempt + 1,
                        self._retries + 1,
                        request_data.model,
                    )

                    response = await client.post(
                        url,
                        headers=self._headers,
                        json=request_data.model_dump(),
                    )

                    if response.status_code == 200:
                        response_data = response.json()
                        openrouter_response = OpenRouterResponse(**response_data)

                        if not openrouter_response.choices:
                            raise ExternalServiceError("Пустой ответ от OpenRouter API")

                        content: str = (
                            openrouter_response.choices[0].get("message", {}).get("content", "")
                        )
                        if not content:
                            raise ExternalServiceError(
                                "Пустое содержимое в ответе от OpenRouter API"
                            )

                        logger.info(
                            "Успешный ответ от OpenRouter: модель=%s, токены=%s",
                            openrouter_response.model,
                            openrouter_response.usage.get("total_tokens")
                            if openrouter_response.usage
                            else "неизвестно",
                        )

                        return content.strip()

                    elif response.status_code == 429:
                        # Rate limit - ждем перед повторной попыткой
                        wait_time = 2**attempt
                        logger.warning(
                            "Rate limit от OpenRouter API. Ожидание %d секунд перед повторной попыткой",
                            wait_time,
                        )
                        await asyncio.sleep(wait_time)
                        continue

                    elif response.status_code >= 500:
                        # Серверная ошибка - повторяем
                        logger.warning(
                            "Серверная ошибка OpenRouter API: %d. Повторная попытка %d/%d",
                            response.status_code,
                            attempt + 1,
                            self._retries + 1,
                        )
                        if attempt < self._retries:
                            await asyncio.sleep(1)
                            continue

                    # Клиентская ошибка или исчерпаны попытки
                    error_text = response.text
                    try:
                        error_data = response.json()
                        error_message = error_data.get("error", {}).get("message", error_text)
                    except (json.JSONDecodeError, AttributeError):
                        error_message = error_text

                    raise ExternalServiceError(
                        f"Ошибка OpenRouter API: {response.status_code} - {error_message}"
                    )

            except httpx.TimeoutException:
                logger.warning(
                    "Таймаут запроса к OpenRouter API (попытка %d/%d)",
                    attempt + 1,
                    self._retries + 1,
                )
                if attempt < self._retries:
                    await asyncio.sleep(1)
                    continue
                raise ExternalServiceError("Таймаут запроса к OpenRouter API") from None

            except httpx.RequestError as e:
                logger.warning(
                    "Ошибка сети при запросе к OpenRouter API: %s (попытка %d/%d)",
                    str(e),
                    attempt + 1,
                    self._retries + 1,
                )
                if attempt < self._retries:
                    await asyncio.sleep(1)
                    continue
                raise ExternalServiceError(f"Ошибка сети: {str(e)}") from e

        raise ExternalServiceError("Исчерпаны все попытки запроса к OpenRouter API")

    async def check_health(self) -> bool:
        """
        Проверяет доступность OpenRouter API

        Returns:
            True если API доступен, False иначе
        """
        try:
            test_messages = [
                OpenRouterMessage(role="user", content="Привет! Это тестовое сообщение.")
            ]
            await self.generate_completion(test_messages, max_tokens=10)
            return True
        except Exception as e:
            logger.error("Проверка здоровья OpenRouter API не удалась: %s", str(e))
            return False
