"""Реализация репозитория состояний пользователей с Redis"""

import json
import logging
from typing import Any

from redis.asyncio import Redis
from redis.exceptions import ConnectionError, RedisError, TimeoutError

from bot.domain.interfaces import IUserStateRepository
from bot.domain.models import ExternalServiceError, TravelCategory, TravelRequest
from bot.infrastructure.base import BaseRepository

logger = logging.getLogger(__name__)


class RedisUserStateRepository(BaseRepository, IUserStateRepository):
    """Репозиторий состояний пользователей на основе Redis"""

    def __init__(self, redis_client: Redis, ttl: int = 3600) -> None:
        super().__init__()
        self._redis = redis_client
        self._ttl = ttl

    async def health_check(self) -> bool:
        """Проверяет доступность Redis"""
        try:
            await self._redis.ping()
            return True
        except Exception as e:
            self.logger.error("Redis недоступен: %s", str(e))
            return False

    def _get_travel_request_key(self, user_id: int) -> str:
        """Формирует ключ для запроса путешествия"""
        return f"travel_request:{user_id}"

    def _get_user_progress_key(self, user_id: int) -> str:
        """Формирует ключ для прогресса пользователя"""
        return f"user_progress:{user_id}"

    async def save_travel_request(self, user_id: int, request: TravelRequest) -> None:
        """Сохраняет запрос пользователя"""
        try:
            key = self._get_travel_request_key(user_id)

            # Сериализуем запрос в JSON
            data = {
                "user_id": request.user_id,
                "category": request.category.value,
                "answers": {
                    q_key: {
                        "question_key": answer.question_key,
                        "answer_value": answer.answer_value,
                        "answer_text": answer.answer_text,
                    }
                    for q_key, answer in request.answers.items()
                },
                "created_at": request.created_at,
            }

            json_data = json.dumps(data, ensure_ascii=False)

            await self.safe_operation(
                f"save_travel_request:{user_id}",
                self._redis.setex,
                key,
                self._ttl,
                json_data,
            )

            self.logger.debug("Запрос пользователя %d сохранен", user_id)

        except (ConnectionError, TimeoutError) as e:
            self.logger.error("Ошибка подключения к Redis при сохранении запроса: %s", str(e))
            raise ExternalServiceError(f"Ошибка сохранения данных: {str(e)}") from e
        except RedisError as e:
            self.logger.error("Ошибка Redis при сохранении запроса: %s", str(e))
            raise ExternalServiceError(f"Ошибка базы данных: {str(e)}") from e
        except Exception as e:
            self.logger.error("Неожиданная ошибка при сохранении запроса: %s", str(e))
            raise ExternalServiceError(f"Внутренняя ошибка: {str(e)}") from e

    async def get_travel_request(self, user_id: int) -> TravelRequest | None:
        """Получает текущий запрос пользователя"""
        try:
            key = self._get_travel_request_key(user_id)

            json_data = await self.safe_operation(
                f"get_travel_request:{user_id}",
                self._redis.get,
                key,
            )

            if not json_data:
                self.logger.debug("Запрос пользователя %d не найден", user_id)
                return None

            # Десериализуем из JSON
            data = json.loads(json_data)

            # Восстанавливаем объект TravelRequest
            from bot.domain.models import UserAnswer

            answers = {}
            for q_key, answer_data in data["answers"].items():
                answers[q_key] = UserAnswer(
                    question_key=answer_data["question_key"],
                    answer_value=answer_data["answer_value"],
                    answer_text=answer_data["answer_text"],
                )

            request = TravelRequest(
                user_id=data["user_id"],
                category=TravelCategory(data["category"]),
                answers=answers,
                created_at=data.get("created_at"),
            )

            self.logger.debug("Запрос пользователя %d получен", user_id)
            return request

        except (ConnectionError, TimeoutError) as e:
            self.logger.error("Ошибка подключения к Redis при получении запроса: %s", str(e))
            raise ExternalServiceError(f"Ошибка получения данных: {str(e)}") from e
        except RedisError as e:
            self.logger.error("Ошибка Redis при получении запроса: %s", str(e))
            raise ExternalServiceError(f"Ошибка базы данных: {str(e)}") from e
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            self.logger.error("Ошибка десериализации запроса пользователя %d: %s", user_id, str(e))
            # Удаляем поврежденные данные
            await self._safe_delete(key)
            return None
        except Exception as e:
            self.logger.error("Неожиданная ошибка при получении запроса: %s", str(e))
            raise ExternalServiceError(f"Внутренняя ошибка: {str(e)}") from e

    async def clear_travel_request(self, user_id: int) -> None:
        """Очищает запрос пользователя"""
        try:
            key = self._get_travel_request_key(user_id)

            await self.safe_operation(
                f"clear_travel_request:{user_id}",
                self._redis.delete,
                key,
            )

            self.logger.debug("Запрос пользователя %d очищен", user_id)

        except (ConnectionError, TimeoutError) as e:
            self.logger.error("Ошибка подключения к Redis при очистке запроса: %s", str(e))
            raise ExternalServiceError(f"Ошибка очистки данных: {str(e)}") from e
        except RedisError as e:
            self.logger.error("Ошибка Redis при очистке запроса: %s", str(e))
            raise ExternalServiceError(f"Ошибка базы данных: {str(e)}") from e
        except Exception as e:
            self.logger.error("Неожиданная ошибка при очистке запроса: %s", str(e))
            raise ExternalServiceError(f"Внутренняя ошибка: {str(e)}") from e

    async def save_user_progress(self, user_id: int, category: str, current_question: int) -> None:
        """Сохраняет прогресс пользователя в диалоге"""
        try:
            key = self._get_user_progress_key(user_id)

            data = {
                "category": category,
                "current_question": current_question,
            }

            json_data = json.dumps(data, ensure_ascii=False)

            await self.safe_operation(
                f"save_user_progress:{user_id}",
                self._redis.setex,
                key,
                self._ttl,
                json_data,
            )

            self.logger.debug("Прогресс пользователя %d сохранен", user_id)

        except (ConnectionError, TimeoutError) as e:
            self.logger.error("Ошибка подключения к Redis при сохранении прогресса: %s", str(e))
            raise ExternalServiceError(f"Ошибка сохранения прогресса: {str(e)}") from e
        except RedisError as e:
            self.logger.error("Ошибка Redis при сохранении прогресса: %s", str(e))
            raise ExternalServiceError(f"Ошибка базы данных: {str(e)}") from e
        except Exception as e:
            self.logger.error("Неожиданная ошибка при сохранении прогресса: %s", str(e))
            raise ExternalServiceError(f"Внутренняя ошибка: {str(e)}") from e

    async def get_user_progress(self, user_id: int) -> dict[str, Any] | None:
        """Получает прогресс пользователя"""
        try:
            key = self._get_user_progress_key(user_id)

            json_data = await self.safe_operation(
                f"get_user_progress:{user_id}",
                self._redis.get,
                key,
            )

            if not json_data:
                self.logger.debug("Прогресс пользователя %d не найден", user_id)
                return None

            data: dict[str, Any] = json.loads(json_data)
            self.logger.debug("Прогресс пользователя %d получен", user_id)
            return data

        except (ConnectionError, TimeoutError) as e:
            self.logger.error("Ошибка подключения к Redis при получении прогресса: %s", str(e))
            raise ExternalServiceError(f"Ошибка получения прогресса: {str(e)}") from e
        except RedisError as e:
            self.logger.error("Ошибка Redis при получении прогресса: %s", str(e))
            raise ExternalServiceError(f"Ошибка базы данных: {str(e)}") from e
        except (json.JSONDecodeError, KeyError) as e:
            self.logger.error(
                "Ошибка десериализации прогресса пользователя %d: %s", user_id, str(e)
            )
            # Удаляем поврежденные данные
            await self._safe_delete(key)
            return None
        except Exception as e:
            self.logger.error("Неожиданная ошибка при получении прогресса: %s", str(e))
            raise ExternalServiceError(f"Внутренняя ошибка: {str(e)}") from e

    async def _safe_delete(self, key: str) -> None:
        """Безопасно удаляет ключ из Redis"""
        try:
            await self._redis.delete(key)
            self.logger.debug("Ключ %s удален", key)
        except Exception as e:
            self.logger.warning("Не удалось удалить поврежденный ключ %s: %s", key, str(e))
