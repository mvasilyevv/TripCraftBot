"""Тесты для доменных моделей"""

import pytest

from bot.domain.constants import REQUIRED_QUESTIONS
from bot.domain.models import TravelCategory, TravelRecommendation, TravelRequest


class TestTravelRequest:
    """Тесты для модели TravelRequest"""

    def test_create_travel_request(self) -> None:
        """Тест создания запроса на путешествие"""
        request = TravelRequest(
            user_id=123, category=TravelCategory.FAMILY, answers={}
        )

        assert request.user_id == 123
        assert request.category == TravelCategory.FAMILY
        assert request.answers == {}

    def test_add_answer(self) -> None:
        """Тест добавления ответа"""
        request = TravelRequest(
            user_id=123, category=TravelCategory.FAMILY, answers={}
        )

        request.add_answer("family_size", "2+1", "2 взрослых + 1 ребенок")

        assert "family_size" in request.answers
        answer = request.get_answer("family_size")
        assert answer is not None
        assert answer.question_key == "family_size"
        assert answer.answer_value == "2+1"
        assert answer.answer_text == "2 взрослых + 1 ребенок"

    def test_get_nonexistent_answer(self) -> None:
        """Тест получения несуществующего ответа"""
        request = TravelRequest(
            user_id=123, category=TravelCategory.FAMILY, answers={}
        )

        answer = request.get_answer("nonexistent")
        assert answer is None

    def test_is_complete_empty(self) -> None:
        """Тест проверки завершенности пустого запроса"""
        request = TravelRequest(
            user_id=123, category=TravelCategory.FAMILY, answers={}
        )

        required_questions = REQUIRED_QUESTIONS[TravelCategory.FAMILY]
        assert not request.is_complete(required_questions)

    def test_is_complete_partial(self) -> None:
        """Тест проверки завершенности частично заполненного запроса"""
        request = TravelRequest(
            user_id=123, category=TravelCategory.FAMILY, answers={}
        )

        request.add_answer("family_size", "2+1", "2 взрослых + 1 ребенок")

        required_questions = REQUIRED_QUESTIONS[TravelCategory.FAMILY]
        assert not request.is_complete(required_questions)

    def test_is_complete_full(self) -> None:
        """Тест проверки завершенности полностью заполненного запроса"""
        request = TravelRequest(
            user_id=123, category=TravelCategory.FAMILY, answers={}
        )

        # Добавляем все обязательные ответы
        request.add_answer("family_size", "2+1", "2 взрослых + 1 ребенок")
        request.add_answer("travel_time", "month", "Ближайший месяц")
        request.add_answer("priority", "beach", "Море/пляж")

        required_questions = REQUIRED_QUESTIONS[TravelCategory.FAMILY]
        assert request.is_complete(required_questions)


class TestTravelRecommendation:
    """Тесты для модели TravelRecommendation"""

    def test_create_recommendation(self) -> None:
        """Тест создания рекомендации"""
        recommendation = TravelRecommendation(
            destination="Анталья, Турция",
            description="Отличное место для семейного отдыха",
            highlights=["Пляжи", "Аквапарки", "Исторические места"],
            practical_info="Виза не нужна, прямые рейсы",
            estimated_cost="$800-1200",
            duration="7-10 дней",
            best_time="Май-октябрь",
        )

        assert recommendation.destination == "Анталья, Турция"
        assert len(recommendation.highlights) == 3
        assert recommendation.estimated_cost == "$800-1200"

    def test_format_for_telegram(self) -> None:
        """Тест форматирования для Telegram"""
        recommendation = TravelRecommendation(
            destination="Анталья, Турция",
            description="Отличное место для семейного отдыха",
            highlights=["Пляжи", "Аквапарки"],
            practical_info="Виза не нужна",
            estimated_cost="$800-1200",
        )

        formatted = recommendation.format_for_telegram()

        assert "🌍 **Анталья, Турция**" in formatted
        assert "Отличное место для семейного отдыха" in formatted
        assert "✨ **Основные достопримечательности:**" in formatted
        assert "• Пляжи" in formatted
        assert "• Аквапарки" in formatted
        assert "📋 **Практическая информация:**" in formatted
        assert "💰 **Примерная стоимость:** $800-1200" in formatted

    def test_format_minimal_recommendation(self) -> None:
        """Тест форматирования минимальной рекомендации"""
        recommendation = TravelRecommendation(
            destination="Тест", description="Описание", highlights=[], practical_info=""
        )

        formatted = recommendation.format_for_telegram()

        assert "🌍 **Тест**" in formatted
        assert "Описание" in formatted
        # Проверяем, что опциональные поля не добавляются
        assert "💰" not in formatted
        assert "⏱" not in formatted
        assert "📅" not in formatted
