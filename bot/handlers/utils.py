"""Утилиты для обработчиков"""

from bot.states.travel import CATEGORY_QUESTIONS_COUNT


def get_progress_text(category: str, current_question: int) -> str:
    """Формирует текст индикатора прогресса"""
    total_questions = CATEGORY_QUESTIONS_COUNT[category]
    return f"Вопрос {current_question} из {total_questions}"


def get_current_question_number(category: str, question_key: str) -> int:
    """Получает номер текущего вопроса"""
    # Маппинг вопросов для каждой категории
    category_questions = {
        "family": ["family_size", "travel_time", "priority"],
        "pets": ["pet_type", "transport", "duration"],
        "photo": ["photo_type", "difficulty"],
        "budget": ["budget", "days", "included"],
        "active": ["activity_type", "skill_level"],
    }

    questions = category_questions.get(category, [])
    if question_key not in questions:
        return 1
    return questions.index(question_key) + 1
