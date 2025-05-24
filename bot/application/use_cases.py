"""Use cases для TripCraftBot"""

import logging
from typing import Optional

from bot.domain.interfaces import (
    IAnalyticsService,
    ITravelRecommendationService,
    IUserStateRepository,
)
from bot.domain.models import (
    InvalidTravelRequestError,
    TravelCategory,
    TravelRecommendation,
    TravelRequest,
)

logger = logging.getLogger(__name__)


class StartTravelPlanningUseCase:
    """Use case для начала планирования путешествия"""

    def __init__(
        self,
        state_repository: IUserStateRepository,
        analytics_service: IAnalyticsService,
    ) -> None:
        self._state_repository = state_repository
        self._analytics_service = analytics_service

    async def execute(self, user_id: int, category: TravelCategory) -> TravelRequest:
        """Начинает новое планирование путешествия"""
        logger.info("Пользователь %d начал планирование категории %s", user_id, category.value)

        # Очищаем предыдущий запрос
        await self._state_repository.clear_travel_request(user_id)

        # Создаем новый запрос
        request = TravelRequest(user_id=user_id, category=category, answers={})

        # Сохраняем запрос
        await self._state_repository.save_travel_request(user_id, request)

        # Отслеживаем использование категории
        await self._analytics_service.track_category_usage(category.value)

        return request


class ProcessUserAnswerUseCase:
    """Use case для обработки ответа пользователя"""

    def __init__(self, state_repository: IUserStateRepository) -> None:
        self._state_repository = state_repository

    async def execute(
        self,
        user_id: int,
        question_key: str,
        answer_value: str,
        answer_text: str,
    ) -> TravelRequest:
        """Обрабатывает ответ пользователя на вопрос"""
        logger.info("Пользователь %d ответил на вопрос %s: %s", user_id, question_key, answer_value)

        # Получаем текущий запрос
        request = await self._state_repository.get_travel_request(user_id)
        if not request:
            raise InvalidTravelRequestError("Запрос пользователя не найден")

        # Добавляем ответ
        request.add_answer(question_key, answer_value, answer_text)

        # Сохраняем обновленный запрос
        await self._state_repository.save_travel_request(user_id, request)

        return request


class GetTravelRecommendationUseCase:
    """Use case для получения рекомендации путешествия"""

    def __init__(
        self,
        recommendation_service: ITravelRecommendationService,
        state_repository: IUserStateRepository,
        analytics_service: IAnalyticsService,
    ) -> None:
        self._recommendation_service = recommendation_service
        self._state_repository = state_repository
        self._analytics_service = analytics_service

    async def execute(self, user_id: int) -> TravelRecommendation:
        """Получает рекомендацию путешествия для пользователя"""
        logger.info("Получение рекомендации для пользователя %d", user_id)

        # Получаем запрос пользователя
        request = await self._state_repository.get_travel_request(user_id)
        if not request:
            raise InvalidTravelRequestError("Запрос пользователя не найден")

        # Получаем рекомендацию
        recommendation = await self._recommendation_service.get_recommendation(request)

        # Отслеживаем запрос рекомендации
        await self._analytics_service.track_recommendation_request(
            request.category.value, recommendation.destination
        )

        logger.info("Рекомендация для пользователя %d: %s", user_id, recommendation.destination)

        return recommendation


class GetAlternativeRecommendationUseCase:
    """Use case для получения альтернативной рекомендации"""

    def __init__(
        self,
        recommendation_service: ITravelRecommendationService,
        state_repository: IUserStateRepository,
        analytics_service: IAnalyticsService,
    ) -> None:
        self._recommendation_service = recommendation_service
        self._state_repository = state_repository
        self._analytics_service = analytics_service

    async def execute(
        self, user_id: int, exclude_destinations: Optional[list[str]] = None
    ) -> TravelRecommendation:
        """Получает альтернативную рекомендацию для пользователя"""
        logger.info("Получение альтернативной рекомендации для пользователя %d", user_id)

        # Получаем запрос пользователя
        request = await self._state_repository.get_travel_request(user_id)
        if not request:
            raise InvalidTravelRequestError("Запрос пользователя не найден")

        # Получаем альтернативную рекомендацию
        recommendation = await self._recommendation_service.get_alternative_recommendation(
            request, exclude_destinations or []
        )

        # Отслеживаем запрос альтернативной рекомендации
        await self._analytics_service.track_user_action(
            "alternative_request", request.category.value
        )

        logger.info(
            "Альтернативная рекомендация для пользователя %d: %s",
            user_id,
            recommendation.destination,
        )

        return recommendation


class ClearUserStateUseCase:
    """Use case для очистки состояния пользователя"""

    def __init__(self, state_repository: IUserStateRepository) -> None:
        self._state_repository = state_repository

    async def execute(self, user_id: int) -> None:
        """Очищает состояние пользователя"""
        logger.info("Очистка состояния пользователя %d", user_id)
        await self._state_repository.clear_travel_request(user_id)
