"""Базовые классы инфраструктурного слоя"""

import logging
from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, Optional

logger = logging.getLogger(__name__)


class BaseExternalService(ABC):
    """Базовый класс для внешних сервисов"""

    def __init__(self, timeout: int = 30, retries: int = 2) -> None:
        self.timeout = timeout
        self.retries = retries
        self.logger = logging.getLogger(self.__class__.__name__)

    @abstractmethod
    async def _make_request(self, **kwargs: Any) -> Any:
        """Выполняет запрос к внешнему сервису"""
        pass

    async def make_request_with_retry(self, **kwargs: Any) -> Any:
        """Выполняет запрос с повторными попытками"""
        last_exception = None

        for attempt in range(self.retries + 1):
            try:
                self.logger.debug(
                    "Попытка %d/%d запроса к %s",
                    attempt + 1,
                    self.retries + 1,
                    self.__class__.__name__,
                )
                result = await self._make_request(**kwargs)
                if attempt > 0:
                    self.logger.info("Запрос успешен с попытки %d", attempt + 1)
                return result
            except Exception as e:
                last_exception = e
                if attempt < self.retries:
                    self.logger.warning(
                        "Попытка %d неудачна: %s. Повторяем...", attempt + 1, str(e)
                    )
                else:
                    self.logger.error("Все попытки исчерпаны. Последняя ошибка: %s", str(e))

        if last_exception:
            raise last_exception
        raise RuntimeError("Все попытки исчерпаны")


class BaseRepository(ABC):
    """Базовый класс для репозиториев"""

    def __init__(self) -> None:
        self.logger = logging.getLogger(self.__class__.__name__)

    @abstractmethod
    async def health_check(self) -> bool:
        """Проверяет доступность хранилища"""
        pass

    async def safe_operation(
        self, operation_name: str, operation_func: Any, *args: Any, **kwargs: Any
    ) -> Any:
        """Безопасно выполняет операцию с логированием"""
        try:
            self.logger.debug("Выполнение операции: %s", operation_name)
            result = await operation_func(*args, **kwargs)
            self.logger.debug("Операция %s выполнена успешно", operation_name)
            return result
        except Exception as e:
            self.logger.error("Ошибка при выполнении операции %s: %s", operation_name, str(e))
            raise


class BaseAnalyticsCollector(ABC):
    """Базовый класс для сборщиков аналитики"""

    def __init__(self) -> None:
        self.logger = logging.getLogger(self.__class__.__name__)

    @abstractmethod
    async def collect_metric(
        self, metric_name: str, value: Any, tags: Optional[Dict[str, str]] = None
    ) -> None:
        """Собирает метрику"""
        pass

    async def safe_collect(
        self, metric_name: str, value: Any, tags: Optional[Dict[str, str]] = None
    ) -> None:
        """Безопасно собирает метрику без прерывания основного потока"""
        try:
            await self.collect_metric(metric_name, value, tags)
        except Exception as e:
            self.logger.warning("Ошибка при сборе метрики %s: %s", metric_name, str(e))


class BaseNotificationSender(ABC):
    """Базовый класс для отправителей уведомлений"""

    def __init__(self) -> None:
        self.logger = logging.getLogger(self.__class__.__name__)

    @abstractmethod
    async def send_notification(
        self,
        message: str,
        level: str = "info",
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Отправляет уведомление"""
        pass

    async def safe_send(
        self,
        message: str,
        level: str = "info",
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Безопасно отправляет уведомление"""
        try:
            await self.send_notification(message, level, context)
        except Exception as e:
            self.logger.error("Ошибка при отправке уведомления: %s", str(e))
