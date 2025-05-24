"""Интерфейсы доменного слоя"""

from abc import ABC, abstractmethod
from typing import Optional

from .models import TravelRecommendation, TravelRequest


class ITravelRecommendationService(ABC):
    """Интерфейс сервиса рекомендаций путешествий"""

    @abstractmethod
    async def get_recommendation(self, request: TravelRequest) -> TravelRecommendation:
        """Получает рекомендацию путешествия на основе запроса пользователя"""
        pass

    @abstractmethod
    async def get_alternative_recommendation(
        self, request: TravelRequest, exclude_destinations: list[str]
    ) -> TravelRecommendation:
        """Получает альтернативную рекомендацию, исключая указанные направления"""
        pass


class IUserStateRepository(ABC):
    """Интерфейс репозитория состояний пользователей"""

    @abstractmethod
    async def save_travel_request(self, user_id: int, request: TravelRequest) -> None:
        """Сохраняет запрос пользователя"""
        pass

    @abstractmethod
    async def get_travel_request(self, user_id: int) -> Optional[TravelRequest]:
        """Получает текущий запрос пользователя"""
        pass

    @abstractmethod
    async def clear_travel_request(self, user_id: int) -> None:
        """Очищает запрос пользователя"""
        pass

    @abstractmethod
    async def save_user_progress(self, user_id: int, category: str, current_question: int) -> None:
        """Сохраняет прогресс пользователя в диалоге"""
        pass

    @abstractmethod
    async def get_user_progress(self, user_id: int) -> Optional[dict]:
        """Получает прогресс пользователя"""
        pass


class IAnalyticsService(ABC):
    """Интерфейс сервиса аналитики"""

    @abstractmethod
    async def track_category_usage(self, category: str) -> None:
        """Отслеживает использование категории"""
        pass

    @abstractmethod
    async def track_recommendation_request(
        self, category: str, destination: str, user_region: Optional[str] = None
    ) -> None:
        """Отслеживает запрос рекомендации"""
        pass

    @abstractmethod
    async def track_user_action(self, action: str, category: Optional[str] = None) -> None:
        """Отслеживает действие пользователя"""
        pass


class INotificationService(ABC):
    """Интерфейс сервиса уведомлений"""

    @abstractmethod
    async def send_error_notification(self, error: Exception, context: dict) -> None:
        """Отправляет уведомление об ошибке"""
        pass

    @abstractmethod
    async def send_usage_report(self, stats: dict) -> None:
        """Отправляет отчет об использовании"""
        pass
