"""Доменные модели для TripCraftBot"""

import logging
import re
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


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
    answers: dict[str, UserAnswer]
    created_at: str | None = None

    def add_answer(self, question_key: str, answer_value: str, answer_text: str) -> None:
        """Добавляет ответ пользователя"""
        # Проверяем, был ли уже ответ на этот вопрос
        if question_key in self.answers:
            old_value = self.answers[question_key].answer_value
            logger.info("Пользователь %d перезаписывает ответ на вопрос %s: '%s' → '%s'",
                       self.user_id, question_key, old_value, answer_value)
        else:
            logger.info("Пользователь %d добавляет новый ответ на вопрос %s: '%s'",
                       self.user_id, question_key, answer_value)

        self.answers[question_key] = UserAnswer(question_key, answer_value, answer_text)

    def get_answer(self, question_key: str) -> UserAnswer | None:
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
    estimated_cost: str | None = None
    duration: str | None = None
    best_time: str | None = None

    def format_for_telegram(self) -> str:
        """Форматирует рекомендацию для отправки в Telegram"""
        # Очищаем название от технических меток
        clean_destination = self._clean_destination(self.destination)

        text = f"🌍 **{clean_destination}**\n\n"

        # Очищаем и форматируем описание
        clean_description = self._clean_description(self.description)
        if clean_description:
            text += f"{clean_description}\n\n"

        if self.highlights:
            text += "✨ **Основные достопримечательности:**\n"
            for highlight in self.highlights:
                clean_highlight = self._clean_text(highlight)
                if clean_highlight:
                    text += f"• {clean_highlight}\n"
            text += "\n"

        # Форматируем практическую информацию более компактно
        if self.practical_info:
            clean_practical = self._clean_practical_info(self.practical_info)
            if clean_practical:
                text += f"📋 **Практическая информация:**\n{clean_practical}\n\n"

        # Добавляем дополнительную информацию, если она есть
        additional_info = []
        if self.estimated_cost:
            additional_info.append(f"💰 **Стоимость:** {self.estimated_cost}")
        if self.duration:
            additional_info.append(f"⏱ **Продолжительность:** {self.duration}")
        if self.best_time:
            additional_info.append(f"📅 **Лучшее время:** {self.best_time}")

        if additional_info:
            text += "\n".join(additional_info)

        return text

    def _clean_destination(self, destination: str) -> str:
        """Очищает название места назначения"""
        # Убираем технические метки
        pattern = r'####?\s*(Destination|Description|destination|description)\s*'
        clean = re.sub(pattern, '', destination)
        # Убираем повторяющиеся заголовки
        clean = re.sub(r'^(.+?):\s*\1', r'\1', clean)
        # Убираем markdown форматирование
        clean = re.sub(r'[#*_`]', '', clean)
        # Убираем лишние пробелы
        clean = re.sub(r'\s+', ' ', clean).strip()

        return clean or "Рекомендация путешествия"

    def _clean_description(self, description: str) -> str:
        """Очищает описание от технической информации"""

        # Разбиваем на строки
        lines = description.split('\n')
        clean_lines = []

        skip_patterns = [
            r'####?\s*(Destination|Description|Estimated Cost|Duration|Best Time)',
            r'^\s*-\s*(Цена тура|Транспорт|Жилье|Лучшее время)',
            r'^\s*\*\s*',
            r'^\s*•\s*Маршрут тура:',
        ]

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Пропускаем технические строки
            if any(re.match(pattern, line, re.IGNORECASE) for pattern in skip_patterns):
                continue

            # Убираем повторяющиеся заголовки
            if '### ' in line and line.count(':') > 1:
                continue

            # Очищаем markdown
            clean_line = re.sub(r'[#*_`]', '', line)
            clean_line = re.sub(r'\s+', ' ', clean_line).strip()

            if clean_line and len(clean_line) > 10:
                clean_lines.append(clean_line)

        # Объединяем первые несколько строк как основное описание
        main_description = ' '.join(clean_lines[:5]) if clean_lines else description[:500]

        # Ограничиваем длину (увеличиваем лимит)
        if len(main_description) > 800:
            main_description = main_description[:800] + "..."

        return main_description

    def _clean_practical_info(self, practical_info: str) -> str:
        """Очищает практическую информацию"""

        # Убираем технические метки
        clean = re.sub(r'####?\s*', '', practical_info)
        clean = re.sub(r'[#*_`]', '', clean)

        # Разбиваем на предложения и берем самые важные
        sentences = [s.strip() for s in clean.split('.') if s.strip()]
        important_sentences = []

        for sentence in sentences[:6]:  # Берем первые 6 предложений
            if len(sentence) > 20 and not sentence.startswith(('Маршрут тура', 'Это позволяет')):
                important_sentences.append(sentence)

        result = '. '.join(important_sentences)
        if result and not result.endswith('.'):
            result += '.'

        return result[:600] if result else ""

    def _clean_text(self, text: str) -> str:
        """Общая очистка текста"""

        # Убираем markdown и лишние символы
        clean = re.sub(r'[#*_`]', '', text)
        clean = re.sub(r'\s+', ' ', clean).strip()

        return clean


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
