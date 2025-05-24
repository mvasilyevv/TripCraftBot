"""Middleware для обработки ошибок сети и Telegram API"""

import asyncio
import logging
from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.exceptions import TelegramNetworkError, TelegramRetryAfter
from aiogram.types import TelegramObject


class NetworkErrorMiddleware(BaseMiddleware):
    """Middleware для обработки сетевых ошибок и повторных попыток"""

    def __init__(self, max_retries: int = 3, retry_delay: float = 1.0):
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.logger = logging.getLogger(__name__)

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        """Обрабатывает события с повторными попытками при сетевых ошибках"""
        
        for attempt in range(self.max_retries + 1):
            try:
                return await handler(event, data)
                
            except TelegramRetryAfter as e:
                if attempt < self.max_retries:
                    self.logger.warning(
                        "Получен TelegramRetryAfter, ожидание %d секунд (попытка %d/%d)",
                        e.retry_after, attempt + 1, self.max_retries + 1
                    )
                    await asyncio.sleep(e.retry_after)
                    continue
                else:
                    self.logger.error("Превышено максимальное количество попыток для TelegramRetryAfter")
                    raise
                    
            except TelegramNetworkError as e:
                if attempt < self.max_retries:
                    delay = self.retry_delay * (2 ** attempt)  # Экспоненциальная задержка
                    self.logger.warning(
                        "Сетевая ошибка Telegram: %s. Повтор через %.1f сек (попытка %d/%d)",
                        e, delay, attempt + 1, self.max_retries + 1
                    )
                    await asyncio.sleep(delay)
                    continue
                else:
                    self.logger.error("Превышено максимальное количество попыток для сетевой ошибки: %s", e)
                    # Не поднимаем исключение, чтобы не ломать бота
                    return None
                    
            except Exception as e:
                self.logger.error("Неожиданная ошибка в обработчике: %s", e, exc_info=True)
                # Для других ошибок не делаем повторных попыток
                raise

        return None
