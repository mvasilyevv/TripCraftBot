"""Форматирование промптов и ответов для LLM"""

import json
import logging
import re
from typing import Any

from bot.domain.models import TravelCategory, TravelRecommendation, TravelRequest
from bot.utils.openrouter import OpenRouterMessage

logger = logging.getLogger(__name__)


class PromptFormatter:
    """Класс для форматирования промптов для LLM"""

    def __init__(self) -> None:
        """Инициализирует форматтер промптов"""
        self._base_system_prompt = self._get_base_system_prompt()
        self._category_prompts = self._get_category_specific_prompts()

    def format_travel_request_prompt(self, request: TravelRequest) -> list[OpenRouterMessage]:
        """
        Форматирует запрос пользователя в промпт для LLM

        Args:
            request: Запрос пользователя на планирование путешествия

        Returns:
            Список сообщений для отправки в LLM
        """
        # Системный промпт
        system_prompt = self._base_system_prompt

        # Добавляем специфичный для категории промпт
        category_prompt = self._category_prompts.get(request.category, "")
        if category_prompt:
            system_prompt += f"\n\n{category_prompt}"

        # Формируем пользовательский запрос
        user_prompt = self._format_user_answers(request)

        return [
            OpenRouterMessage(role="system", content=system_prompt),
            OpenRouterMessage(role="user", content=user_prompt),
        ]

    def parse_llm_response(self, response_text: str) -> TravelRecommendation:
        """
        Парсит ответ от LLM в структуру TravelRecommendation

        Args:
            response_text: Текст ответа от LLM

        Returns:
            Структурированная рекомендация путешествия

        Raises:
            ValueError: Если не удалось распарсить ответ
        """
        try:
            # Пытаемся найти JSON в ответе
            json_match = re.search(r"\{.*\}", response_text, re.DOTALL)
            if json_match:
                json_text = json_match.group()
                data = json.loads(json_text)
                return self._create_recommendation_from_json(data)

            # Если JSON не найден, парсим как обычный текст
            return self._parse_text_response(response_text)

        except Exception as e:
            logger.error("Ошибка парсинга ответа LLM: %s. Ответ: %s", str(e), response_text[:500])
            # Возвращаем базовую рекомендацию с исходным текстом
            return TravelRecommendation(
                destination="Рекомендация от ИИ",
                description=response_text[:1000],
                highlights=["Подробности в описании"],
                practical_info="Обратитесь к специалисту для уточнения деталей",
            )

    def _get_base_system_prompt(self) -> str:
        """Возвращает базовый системный промпт"""
        return """Ты - опытный консультант по путешествиям с 15-летним стажем. Твоя задача - предоставлять персонализированные рекомендации путешествий на основе предпочтений пользователя.

ВАЖНЫЕ ПРИНЦИПЫ:
1. Всегда учитывай бюджет и предпочтения пользователя
2. Предлагай конкретные места с практической информацией
3. Включай актуальную информацию о визах, транспорте, жилье
4. Учитывай сезонность и погодные условия
5. Предоставляй реалистичные оценки стоимости

ФОРМАТ ОТВЕТА:
Отвечай в следующем JSON формате:
{
  "destination": "Название места назначения",
  "description": "Подробное описание места и почему оно подходит пользователю",
  "highlights": ["Список", "основных", "достопримечательностей"],
  "practical_info": "Практическая информация: виза, транспорт, лучшее время для поездки",
  "estimated_cost": "Примерная стоимость поездки",
  "duration": "Рекомендуемая продолжительность",
  "best_time": "Лучшее время для поездки"
}

Если JSON формат невозможен, структурируй ответ четко с заголовками."""

    def _get_category_specific_prompts(self) -> dict[TravelCategory, str]:
        """Возвращает специфичные промпты для каждой категории"""
        return {
            TravelCategory.FAMILY: """
СПЕЦИАЛИЗАЦИЯ: Семейные путешествия
- Приоритет безопасности и комфорта для детей
- Учитывай возраст детей при выборе активностей
- Рекомендуй семейные отели и рестораны
- Включай детские развлечения и образовательные места
- Учитывай удобство транспорта с детьми
""",
            TravelCategory.PETS: """
СПЕЦИАЛИЗАЦИЯ: Путешествия с питомцами
- Обязательно проверяй pet-friendly политику отелей
- Включай информацию о ветеринарных требованиях
- Рекомендуй места для прогулок с животными
- Учитывай транспортные ограничения для питомцев
- Предупреждай о необходимых документах и прививках
""",
            TravelCategory.PHOTO: """
СПЕЦИАЛИЗАЦИЯ: Фотографические путешествия
- Фокусируйся на визуально впечатляющих местах
- Учитывай лучшее время суток для фотографии
- Рекомендуй менее туристические, но красивые места
- Включай информацию о разрешениях на съемку
- Предлагай уникальные ракурсы и локации
""",
            TravelCategory.BUDGET: """
СПЕЦИАЛИЗАЦИЯ: Бюджетные путешествия
- Приоритет экономии без ущерба для впечатлений
- Рекомендуй бесплатные или недорогие активности
- Включай информацию о дешевом транспорте и жилье
- Предлагай местную еду вместо туристических ресторанов
- Учитывай сезонные скидки и предложения
""",
            TravelCategory.ACTIVE: """
СПЕЦИАЛИЗАЦИЯ: Активный отдых
- Фокусируйся на спортивных и приключенческих активностях
- Учитывай уровень физической подготовки
- Рекомендуй необходимое снаряжение
- Включай информацию о безопасности и страховке
- Предлагай разнообразные виды активного отдыха
""",
        }

    def _format_user_answers(self, request: TravelRequest) -> str:
        """Форматирует ответы пользователя в текст запроса"""
        category_names = {
            TravelCategory.FAMILY: "семейное путешествие",
            TravelCategory.PETS: "путешествие с питомцами",
            TravelCategory.PHOTO: "фотографическое путешествие",
            TravelCategory.BUDGET: "бюджетное путешествие",
            TravelCategory.ACTIVE: "активный отдых",
        }

        category_name = category_names.get(request.category, "путешествие")

        prompt = f"Помоги спланировать {category_name}. Вот мои предпочтения:\n\n"

        for _question_key, answer in request.answers.items():
            prompt += f"• {answer.answer_text}\n"

        prompt += "\nПожалуйста, предложи конкретное место для путешествия с подробной информацией."

        return prompt

    def _create_recommendation_from_json(self, data: dict[str, Any]) -> TravelRecommendation:
        """Создает рекомендацию из JSON данных"""
        return TravelRecommendation(
            destination=data.get("destination", "Неизвестное место"),
            description=data.get("description", "Описание недоступно"),
            highlights=data.get("highlights", []),
            practical_info=data.get("practical_info", "Информация уточняется"),
            estimated_cost=data.get("estimated_cost"),
            duration=data.get("duration"),
            best_time=data.get("best_time"),
        )

    def _parse_text_response(self, text: str) -> TravelRecommendation:
        """Парсит текстовый ответ без JSON структуры"""
        lines = text.split("\n")

        # Ищем название места назначения (обычно в начале или в заголовке)
        destination = "Рекомендация от ИИ"
        for line in lines[:5]:  # Проверяем первые 5 строк
            line = line.strip()
            if line and not line.startswith(("•", "-", "*", "1.", "2.")):
                # Убираем markdown форматирование
                clean_line = re.sub(r"[#*_`]", "", line).strip()
                if len(clean_line) > 3:
                    destination = clean_line
                    break

        # Извлекаем основное описание
        description_lines = []
        highlights = []
        practical_info = ""

        current_section = "description"

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Определяем секции
            if any(
                keyword in line.lower()
                for keyword in ["достопримечательности", "highlights", "что посмотреть"]
            ):
                current_section = "highlights"
                continue
            elif any(
                keyword in line.lower()
                for keyword in ["практическая", "practical", "как добраться", "виза"]
            ):
                current_section = "practical"
                continue

            # Добавляем контент в соответствующую секцию
            if current_section == "description" and not line.startswith(("•", "-", "*")):
                description_lines.append(line)
            elif current_section == "highlights" and line.startswith(("•", "-", "*")):
                highlight = re.sub(r"^[•\-*]\s*", "", line)
                if highlight:
                    highlights.append(highlight)
            elif current_section == "practical":
                practical_info += line + " "

        description = " ".join(description_lines) if description_lines else text[:500]

        return TravelRecommendation(
            destination=destination,
            description=description,
            highlights=highlights or ["Подробности в описании"],
            practical_info=practical_info.strip()
            or "Обратитесь к специалисту для уточнения деталей",
        )
