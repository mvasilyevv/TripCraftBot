"""Фабрика для создания сервисов"""

import logging
from typing import Optional

from redis.asyncio import Redis

from bot.application.use_cases import (
    GetAlternativeRecommendationUseCase,
    GetTravelRecommendationUseCase,
    ProcessUserAnswerUseCase,
    StartTravelPlanningUseCase,
)
from bot.domain.interfaces import IAnalyticsService, IUserStateRepository
from bot.infrastructure.llm_recommendation_service import LLMTravelRecommendationService
from bot.infrastructure.redis_repository import RedisUserStateRepository
from bot.utils.formatter import PromptFormatter
from bot.utils.openrouter import OpenRouterClient
from config import get_config

logger = logging.getLogger(__name__)


class MockAnalyticsService(IAnalyticsService):
    """Заглушка для сервиса аналитики"""

    async def track_category_usage(self, category: str) -> None:
        """Отслеживает использование категории"""
        logger.info("Аналитика: использование категории %s", category)

    async def track_recommendation_request(
        self, category: str, destination: str, user_region: Optional[str] = None
    ) -> None:
        """Отслеживает запрос рекомендации"""
        logger.info(
            "Аналитика: запрос рекомендации категория=%s, направление=%s, регион=%s",
            category,
            destination,
            user_region,
        )

    async def track_user_action(self, action: str, category: Optional[str] = None) -> None:
        """Отслеживает действие пользователя"""
        logger.info("Аналитика: действие пользователя %s, категория=%s", action, category)


class ServiceFactory:
    """Фабрика для создания экземпляров сервисов"""

    def __init__(self) -> None:
        """Инициализирует фабрику сервисов"""
        self._config = get_config()
        self._openrouter_client: Optional[OpenRouterClient] = None
        self._recommendation_service: Optional[LLMTravelRecommendationService] = None
        self._state_repository: Optional[IUserStateRepository] = None
        self._analytics_service: Optional[IAnalyticsService] = None
        self._prompt_formatter: Optional[PromptFormatter] = None

    def get_openrouter_client(self) -> OpenRouterClient:
        """Возвращает клиент OpenRouter API"""
        if self._openrouter_client is None:
            self._openrouter_client = OpenRouterClient(
                api_key=self._config.openrouter.api_key,
                base_url=self._config.openrouter.base_url,
                primary_model=self._config.openrouter.primary_model,
                fallback_model=self._config.openrouter.fallback_model,
                timeout=self._config.openrouter.timeout,
                retries=self._config.openrouter.retries,
            )
        return self._openrouter_client

    def get_prompt_formatter(self) -> PromptFormatter:
        """Возвращает форматтер промптов"""
        if self._prompt_formatter is None:
            self._prompt_formatter = PromptFormatter()
        return self._prompt_formatter

    def get_recommendation_service(self) -> LLMTravelRecommendationService:
        """Возвращает сервис рекомендаций"""
        if self._recommendation_service is None:
            openrouter_client = self.get_openrouter_client()
            prompt_formatter = self.get_prompt_formatter()
            self._recommendation_service = LLMTravelRecommendationService(
                openrouter_client=openrouter_client,
                prompt_formatter=prompt_formatter,
            )
        return self._recommendation_service

    def get_state_repository(self) -> IUserStateRepository:
        """Возвращает репозиторий состояний пользователей"""
        if self._state_repository is None:
            redis_client = Redis.from_url(
                self._config.get_redis_url(),
                encoding="utf-8",
                decode_responses=True,
            )
            self._state_repository = RedisUserStateRepository(
                redis_client=redis_client,
                ttl=self._config.redis.fsm_ttl,
            )
        return self._state_repository

    def get_analytics_service(self) -> IAnalyticsService:
        """Возвращает сервис аналитики"""
        if self._analytics_service is None:
            # Пока используем заглушку
            self._analytics_service = MockAnalyticsService()
        return self._analytics_service

    def get_travel_recommendation_use_case(self) -> GetTravelRecommendationUseCase:
        """Возвращает use case для получения рекомендаций"""
        return GetTravelRecommendationUseCase(
            recommendation_service=self.get_recommendation_service(),
            state_repository=self.get_state_repository(),
            analytics_service=self.get_analytics_service(),
        )

    def get_alternative_recommendation_use_case(self) -> GetAlternativeRecommendationUseCase:
        """Возвращает use case для получения альтернативных рекомендаций"""
        return GetAlternativeRecommendationUseCase(
            recommendation_service=self.get_recommendation_service(),
            state_repository=self.get_state_repository(),
            analytics_service=self.get_analytics_service(),
        )

    def get_start_planning_use_case(self) -> StartTravelPlanningUseCase:
        """Возвращает use case для начала планирования путешествия"""
        return StartTravelPlanningUseCase(
            state_repository=self.get_state_repository(),
            analytics_service=self.get_analytics_service(),
        )

    def get_process_answer_use_case(self) -> ProcessUserAnswerUseCase:
        """Возвращает use case для обработки ответов пользователя"""
        return ProcessUserAnswerUseCase(
            state_repository=self.get_state_repository(),
        )


# Глобальный экземпляр фабрики
_service_factory: Optional[ServiceFactory] = None


def get_service_factory() -> ServiceFactory:
    """Возвращает глобальный экземпляр фабрики сервисов"""
    global _service_factory
    if _service_factory is None:
        _service_factory = ServiceFactory()
    return _service_factory
