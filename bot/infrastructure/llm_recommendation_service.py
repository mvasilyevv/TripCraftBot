"""Реализация сервиса рекомендаций с использованием LLM"""

import logging
from typing import List, Optional

from bot.domain.interfaces import ITravelRecommendationService
from bot.domain.models import ExternalServiceError, TravelRecommendation, TravelRequest
from bot.utils.formatter import PromptFormatter
from bot.utils.openrouter import OpenRouterClient, OpenRouterMessage

logger = logging.getLogger(__name__)


class LLMTravelRecommendationService(ITravelRecommendationService):
    """Сервис рекомендаций путешествий с использованием LLM"""

    def __init__(
        self,
        openrouter_client: OpenRouterClient,
        prompt_formatter: Optional[PromptFormatter] = None,
    ) -> None:
        """
        Инициализирует сервис рекомендаций

        Args:
            openrouter_client: Клиент для работы с OpenRouter API
            prompt_formatter: Форматтер промптов (создается автоматически
                если не передан)
        """
        self._client = openrouter_client
        self._formatter = prompt_formatter or PromptFormatter()
        self._excluded_destinations: List[str] = []

    async def get_recommendation(self, request: TravelRequest) -> TravelRecommendation:
        """
        Получает рекомендацию путешествия на основе запроса пользователя

        Args:
            request: Запрос пользователя на планирование путешествия

        Returns:
            Рекомендация путешествия

        Raises:
            ExternalServiceError: При ошибках LLM API
        """
        logger.info(
            "Получение рекомендации для пользователя %d, категория: %s",
            request.user_id,
            request.category.value,
        )

        try:
            # Форматируем промпт
            messages = self._formatter.format_travel_request_prompt(request)

            # Получаем ответ от LLM
            response_text = await self._client.generate_completion(
                messages=messages,
                max_tokens=2000,
                temperature=0.7,
            )

            # Парсим ответ
            recommendation = self._formatter.parse_llm_response(response_text)

            logger.info(
                "Успешно получена рекомендация для пользователя %d: %s",
                request.user_id,
                recommendation.destination,
            )

            return recommendation

        except Exception as e:
            logger.error(
                "Ошибка получения рекомендации для пользователя %d: %s",
                request.user_id,
                str(e),
            )

            if isinstance(e, ExternalServiceError):
                raise

            raise ExternalServiceError(f"Ошибка сервиса рекомендаций: {str(e)}") from e

    async def get_alternative_recommendation(
        self, request: TravelRequest, exclude_destinations: List[str]
    ) -> TravelRecommendation:
        """
        Получает альтернативную рекомендацию, исключая указанные направления

        Args:
            request: Запрос пользователя на планирование путешествия
            exclude_destinations: Список направлений для исключения

        Returns:
            Альтернативная рекомендация путешествия

        Raises:
            ExternalServiceError: При ошибках LLM API
        """
        logger.info(
            "Получение альтернативной рекомендации для пользователя %d, исключая: %s",
            request.user_id,
            exclude_destinations,
        )

        try:
            # Форматируем промпт с исключениями
            messages = self._formatter.format_travel_request_prompt(request)

            # Добавляем информацию об исключениях
            if exclude_destinations:
                exclusion_text = (
                    f"\n\nВАЖНО: НЕ предлагай следующие направления, "
                    f"так как они уже были рассмотрены: "
                    f"{', '.join(exclude_destinations)}. "
                    f"Предложи альтернативное место, которое также подойдет "
                    f"под указанные критерии."
                )

                # Добавляем к последнему сообщению пользователя
                if messages and messages[-1].role == "user":
                    messages[-1].content += exclusion_text
                else:
                    messages.append(OpenRouterMessage(role="user", content=exclusion_text))

            # Получаем ответ от LLM
            response_text = await self._client.generate_completion(
                messages=messages,
                max_tokens=2000,
                temperature=0.8,  # Немного больше креативности для альтернатив
            )

            # Парсим ответ
            recommendation = self._formatter.parse_llm_response(response_text)

            logger.info(
                "Успешно получена альтернативная рекомендация для пользователя %d: %s",
                request.user_id,
                recommendation.destination,
            )

            return recommendation

        except Exception as e:
            logger.error(
                "Ошибка получения альтернативной рекомендации для пользователя %d: %s",
                request.user_id,
                str(e),
            )

            if isinstance(e, ExternalServiceError):
                raise

            raise ExternalServiceError(
                f"Ошибка сервиса альтернативных рекомендаций: {str(e)}"
            ) from e

    async def check_service_health(self) -> bool:
        """
        Проверяет работоспособность сервиса рекомендаций

        Returns:
            True если сервис работает, False иначе
        """
        try:
            return await self._client.check_health()
        except Exception as e:
            logger.error("Ошибка проверки здоровья сервиса рекомендаций: %s", str(e))
            return False

    def get_fallback_recommendation(self, request: TravelRequest) -> TravelRecommendation:
        """
        Возвращает сообщение об ошибке вместо неперсонализированной рекомендации

        Args:
            request: Запрос пользователя

        Returns:
            Рекомендация с сообщением о недоступности сервиса
        """
        logger.warning(
            "Fallback вызван для пользователя %d, категория: %s. "
            "Не предоставляем неперсонализированные рекомендации",
            request.user_id,
            request.category.value,
        )

        # Определяем тип путешествия для сообщения
        category_names = {
            "family": "семейного путешествия",
            "pets": "путешествия с питомцами",
            "photo": "фотографического путешествия",
            "budget": "бюджетного путешествия",
            "active": "активного отдыха",
        }

        category_name = category_names.get(request.category.value, "путешествия")

        return TravelRecommendation(
            destination="Сервис временно недоступен",
            description=(
                f"К сожалению, наш сервис рекомендаций для {category_name} "
                f"временно недоступен. Мы не можем предоставить качественную "
                f"персонализированную рекомендацию в данный момент, так как "
                f"каждое путешествие должно быть уникальным и подобранным "
                f"специально под ваши предпочтения."
            ),
            highlights=[
                "Попробуйте повторить запрос через несколько минут",
                "Проверьте стабильность интернет-соединения",
                "Обратитесь в поддержку, если проблема повторяется",
                "Мы работаем над восстановлением сервиса",
            ],
            practical_info=(
                "Приносим извинения за временные неудобства. "
                "Наша команда разработчиков уже работает над устранением "
                "технических проблем. Качественные персонализированные "
                "рекомендации будут доступны в ближайшее время."
            ),
            estimated_cost="Недоступно",
            duration="Недоступно",
            best_time="Недоступно",
        )
