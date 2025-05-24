"""Доменные модели для TripCraftBot"""

from dataclasses import dataclass
from enum import Enum
from typing import Dict, Optional


class TravelCategory(Enum):
    """Категории путешествий"""

    FAMILY = "family"
    PETS = "pets"
    PHOTO = "photo"
    BUDGET = "budget"
    ACTIVE = "active"


@dataclass
class UserAnswer:
    """Ответ пользователя на вопрос"""

    question_key: str
    answer_value: str
    answer_text: str


@dataclass
class TravelRequest:
    """Запрос на планирование путешествия"""

    user_id: int
    category: TravelCategory
    answers: Dict[str, UserAnswer]
    created_at: Optional[str] = None

    def add_answer(self, question_key: str, answer_value: str, answer_text: str) -> None:
        """Добавляет ответ пользователя"""
        self.answers[question_key] = UserAnswer(question_key, answer_value, answer_text)

    def get_answer(self, question_key: str) -> Optional[UserAnswer]:
        """Получает ответ пользователя по ключу"""
        return self.answers.get(question_key)

    def is_complete(self, required_questions: list[str]) -> bool:
        """Проверяет, все ли обязательные вопросы отвечены"""
        return all(question in self.answers for question in required_questions)


@dataclass
class TravelRecommendation:
    """Рекомендация путешествия"""

    destination: str
    description: str
    highlights: list[str]
    practical_info: str
    estimated_cost: Optional[str] = None
    duration: Optional[str] = None
    best_time: Optional[str] = None

    def format_for_telegram(self) -> str:
        """Форматирует рекомендацию для отправки в Telegram"""
        text = f"🌍 **{self.destination}**\n\n"
        text += f"{self.description}\n\n"

        if self.highlights:
            text += "✨ **Основные достопримечательности:**\n"
            for highlight in self.highlights:
                text += f"• {highlight}\n"
            text += "\n"

        if self.practical_info:
            text += f"📋 **Практическая информация:**\n{self.practical_info}\n\n"

        if self.estimated_cost:
            text += f"💰 **Примерная стоимость:** {self.estimated_cost}\n"

        if self.duration:
            text += f"⏱ **Рекомендуемая продолжительность:** {self.duration}\n"

        if self.best_time:
            text += f"📅 **Лучшее время для поездки:** {self.best_time}\n"

        return text


class TravelPlannerError(Exception):
    """Базовое исключение для планировщика путешествий"""

    pass


class InvalidTravelRequestError(TravelPlannerError):
    """Ошибка некорректного запроса на планирование"""

    pass


class ExternalServiceError(TravelPlannerError):
    """Ошибка внешнего сервиса"""

    pass


class ConfigurationError(TravelPlannerError):
    """Ошибка конфигурации"""

    pass
