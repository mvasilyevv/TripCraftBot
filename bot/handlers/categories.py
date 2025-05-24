"""Обработчики категорий путешествий"""

import logging
from typing import Any, Dict

from aiogram import Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot.domain.models import TravelCategory
from bot.handlers.results import show_travel_recommendation
from bot.infrastructure.service_factory import get_service_factory
from bot.keyboards.inline import (
    get_activity_type_keyboard,
    get_budget_days_keyboard,
    get_budget_keyboard,
    get_difficulty_keyboard,
    get_duration_keyboard,
    get_family_priority_keyboard,
    get_family_size_keyboard,
    get_included_keyboard,
    get_pet_type_keyboard,
    get_photo_type_keyboard,
    get_skill_level_keyboard,
    get_transport_keyboard,
    get_travel_time_keyboard,
)
from bot.states.travel import (
    CATEGORY_QUESTIONS_COUNT,
    ActiveTravelStates,
    BudgetTravelStates,
    FamilyTravelStates,
    PetTravelStates,
    PhotoTravelStates,
)

logger = logging.getLogger(__name__)

router = Router()

# Маппинг вопросов для каждой категории
CATEGORY_QUESTIONS: Dict[str, Dict[str, Dict[str, Any]]] = {
    "family": {
        "family_size": {
            "text": "Сколько человек будет путешествовать?",
            "keyboard": get_family_size_keyboard,
            "next_state": FamilyTravelStates.asking_travel_time,
        },
        "travel_time": {
            "text": "Когда планируете поехать?",
            "keyboard": get_travel_time_keyboard,
            "next_state": FamilyTravelStates.asking_priority,
        },
        "priority": {
            "text": "Что для вас важнее всего?",
            "keyboard": get_family_priority_keyboard,
            "next_state": FamilyTravelStates.processing,
        },
    },
    "pets": {
        "pet_type": {
            "text": "Какой у вас питомец?",
            "keyboard": get_pet_type_keyboard,
            "next_state": PetTravelStates.asking_transport,
        },
        "transport": {
            "text": "Каким транспортом планируете добираться?",
            "keyboard": get_transport_keyboard,
            "next_state": PetTravelStates.asking_duration,
        },
        "duration": {
            "text": "На сколько планируете поехать?",
            "keyboard": get_duration_keyboard,
            "next_state": PetTravelStates.processing,
        },
    },
    "photo": {
        "photo_type": {
            "text": "Какие фото вас интересуют?",
            "keyboard": get_photo_type_keyboard,
            "next_state": PhotoTravelStates.asking_difficulty,
        },
        "difficulty": {
            "text": "Готовы ли к сложным маршрутам?",
            "keyboard": get_difficulty_keyboard,
            "next_state": PhotoTravelStates.processing,
        },
    },
    "budget": {
        "budget": {
            "text": "Какой у вас бюджет на человека?",
            "keyboard": get_budget_keyboard,
            "next_state": BudgetTravelStates.asking_days,
        },
        "days": {
            "text": "На сколько дней планируете поездку?",
            "keyboard": get_budget_days_keyboard,
            "next_state": BudgetTravelStates.asking_included,
        },
        "included": {
            "text": "Что должно быть включено в бюджет?",
            "keyboard": get_included_keyboard,
            "next_state": BudgetTravelStates.processing,
        },
    },
    "active": {
        "activity_type": {
            "text": "Какой вид активности вас интересует?",
            "keyboard": get_activity_type_keyboard,
            "next_state": ActiveTravelStates.asking_skill_level,
        },
        "skill_level": {
            "text": "Какой у вас уровень подготовки?",
            "keyboard": get_skill_level_keyboard,
            "next_state": ActiveTravelStates.processing,
        },
    },
}

# Маппинг состояний на категории и вопросы
STATE_TO_CATEGORY_QUESTION = {
    # Family
    FamilyTravelStates.asking_family_size: ("family", "family_size"),
    FamilyTravelStates.asking_travel_time: ("family", "travel_time"),
    FamilyTravelStates.asking_priority: ("family", "priority"),
    # Pets
    PetTravelStates.asking_pet_type: ("pets", "pet_type"),
    PetTravelStates.asking_transport: ("pets", "transport"),
    PetTravelStates.asking_duration: ("pets", "duration"),
    # Photo
    PhotoTravelStates.asking_photo_type: ("photo", "photo_type"),
    PhotoTravelStates.asking_difficulty: ("photo", "difficulty"),
    # Budget
    BudgetTravelStates.asking_budget: ("budget", "budget"),
    BudgetTravelStates.asking_days: ("budget", "days"),
    BudgetTravelStates.asking_included: ("budget", "included"),
    # Active
    ActiveTravelStates.asking_activity_type: ("active", "activity_type"),
    ActiveTravelStates.asking_skill_level: ("active", "skill_level"),
}


def get_progress_text(category: str, current_question: int) -> str:
    """Формирует текст индикатора прогресса"""
    total_questions = CATEGORY_QUESTIONS_COUNT[category]
    return f"Вопрос {current_question} из {total_questions}"


def get_current_question_number(category: str, question_key: str) -> int:
    """Получает номер текущего вопроса"""
    questions = list(CATEGORY_QUESTIONS[category].keys())
    return questions.index(question_key) + 1


@router.callback_query(lambda c: c.data and c.data.startswith("category:"))
async def callback_category_selected(callback: CallbackQuery, state: FSMContext) -> None:
    """Обработчик выбора категории путешествия"""
    if not callback.data or not callback.from_user:
        logger.error("Callback data или информация о пользователе отсутствует")
        return

    category = callback.data.split(":")[1]
    user_id = callback.from_user.id
    logger.info("Пользователь %d выбрал категорию %s", user_id, category)

    try:
        # Создаем новый запрос через use case
        service_factory = get_service_factory()
        start_planning_use_case = service_factory.get_start_planning_use_case()

        # Преобразуем строку категории в enum
        travel_category = TravelCategory(category)

        # Начинаем планирование
        await start_planning_use_case.execute(user_id, travel_category)

        # Сохраняем категорию в состоянии FSM для совместимости
        await state.update_data(category=category, answers={})

        # Получаем первый вопрос для категории
        first_question_key = list(CATEGORY_QUESTIONS[category].keys())[0]
        question_data = CATEGORY_QUESTIONS[category][first_question_key]

        # Устанавливаем состояние для первого вопроса
        if category == "family":
            await state.set_state(FamilyTravelStates.asking_family_size)
        elif category == "pets":
            await state.set_state(PetTravelStates.asking_pet_type)
        elif category == "photo":
            await state.set_state(PhotoTravelStates.asking_photo_type)
        elif category == "budget":
            await state.set_state(BudgetTravelStates.asking_budget)
        elif category == "active":
            await state.set_state(ActiveTravelStates.asking_activity_type)

        # Формируем текст с индикатором прогресса
        progress_text = get_progress_text(category, 1)
        full_text = f"{progress_text}\n\n{question_data['text']}"

        # Отправляем первый вопрос
        if callback.message and isinstance(callback.message, Message):
            await callback.message.edit_text(full_text, reply_markup=question_data["keyboard"]())

        await callback.answer()

    except Exception as e:
        logger.error("Ошибка при выборе категории для пользователя %d: %s", user_id, str(e))
        await callback.answer("Произошла ошибка. Попробуйте еще раз.")


# Обработчики ответов для семейных путешествий
@router.callback_query(lambda c: c.data and c.data.startswith("family_size:"))
async def callback_family_size(callback: CallbackQuery, state: FSMContext) -> None:
    """Обработчик выбора размера семьи"""
    await _process_answer(callback, state, "family_size", "family")


@router.callback_query(lambda c: c.data and c.data.startswith("time:"))
async def callback_travel_time(callback: CallbackQuery, state: FSMContext) -> None:
    """Обработчик выбора времени путешествия"""
    await _process_answer(callback, state, "travel_time", "family")


@router.callback_query(lambda c: c.data and c.data.startswith("priority:"))
async def callback_family_priority(callback: CallbackQuery, state: FSMContext) -> None:
    """Обработчик выбора приоритета для семейного путешествия"""
    await _process_answer(callback, state, "priority", "family")


# Обработчики ответов для путешествий с питомцами
@router.callback_query(lambda c: c.data and c.data.startswith("pet:"))
async def callback_pet_type(callback: CallbackQuery, state: FSMContext) -> None:
    """Обработчик выбора типа питомца"""
    await _process_answer(callback, state, "pet_type", "pets")


@router.callback_query(lambda c: c.data and c.data.startswith("transport:"))
async def callback_transport(callback: CallbackQuery, state: FSMContext) -> None:
    """Обработчик выбора транспорта"""
    await _process_answer(callback, state, "transport", "pets")


@router.callback_query(lambda c: c.data and c.data.startswith("duration:"))
async def callback_duration(callback: CallbackQuery, state: FSMContext) -> None:
    """Обработчик выбора продолжительности"""
    await _process_answer(callback, state, "duration", "pets")


# Обработчики ответов для фото-путешествий
@router.callback_query(lambda c: c.data and c.data.startswith("photo:"))
async def callback_photo_type(callback: CallbackQuery, state: FSMContext) -> None:
    """Обработчик выбора типа фото"""
    await _process_answer(callback, state, "photo_type", "photo")


@router.callback_query(lambda c: c.data and c.data.startswith("difficulty:"))
async def callback_difficulty(callback: CallbackQuery, state: FSMContext) -> None:
    """Обработчик выбора сложности"""
    await _process_answer(callback, state, "difficulty", "photo")


# Обработчики ответов для бюджетных путешествий
@router.callback_query(lambda c: c.data and c.data.startswith("budget:"))
async def callback_budget(callback: CallbackQuery, state: FSMContext) -> None:
    """Обработчик выбора бюджета"""
    await _process_answer(callback, state, "budget", "budget")


@router.callback_query(lambda c: c.data and c.data.startswith("days:"))
async def callback_budget_days(callback: CallbackQuery, state: FSMContext) -> None:
    """Обработчик выбора количества дней"""
    await _process_answer(callback, state, "days", "budget")


@router.callback_query(lambda c: c.data and c.data.startswith("included:"))
async def callback_included(callback: CallbackQuery, state: FSMContext) -> None:
    """Обработчик выбора включенных услуг"""
    await _process_answer(callback, state, "included", "budget")


# Обработчики ответов для активного отдыха
@router.callback_query(lambda c: c.data and c.data.startswith("activity:"))
async def callback_activity_type(callback: CallbackQuery, state: FSMContext) -> None:
    """Обработчик выбора типа активности"""
    await _process_answer(callback, state, "activity_type", "active")


@router.callback_query(lambda c: c.data and c.data.startswith("skill:"))
async def callback_skill_level(callback: CallbackQuery, state: FSMContext) -> None:
    """Обработчик выбора уровня навыков"""
    await _process_answer(callback, state, "skill_level", "active")


async def _process_answer(
    callback: CallbackQuery, state: FSMContext, question_key: str, category: str
) -> None:
    """Универсальная функция обработки ответа пользователя"""
    if not callback.data or not callback.from_user:
        logger.error("Callback data или информация о пользователе отсутствует")
        return

    user_id = callback.from_user.id
    answer_value = callback.data.split(":")[1]
    answer_text = _get_button_text(callback, answer_value)

    logger.info("Пользователь %d ответил на вопрос %s: %s", user_id, question_key, answer_value)

    try:
        # Сохраняем ответ через use case
        service_factory = get_service_factory()
        process_answer_use_case = service_factory.get_process_answer_use_case()

        await process_answer_use_case.execute(
            user_id=user_id,
            question_key=question_key,
            answer_value=answer_value,
            answer_text=answer_text,
        )

        # Также сохраняем в состоянии FSM для совместимости
        await _save_answer(state, question_key, answer_value, answer_text)

        # Обрабатываем следующий шаг
        await _handle_next_step(callback, state, question_key, category)
        await callback.answer()

    except Exception as e:
        logger.error("Ошибка при обработке ответа пользователя %d: %s", user_id, str(e))
        await callback.answer("Произошла ошибка. Попробуйте еще раз.")


def _get_button_text(callback: CallbackQuery, default_value: str) -> str:
    """Получает текст кнопки из callback"""
    if (
        callback.message
        and isinstance(callback.message, Message)
        and callback.message.reply_markup
        and callback.message.reply_markup.inline_keyboard
    ):
        for row in callback.message.reply_markup.inline_keyboard:
            for button in row:
                if button.callback_data == callback.data:
                    return button.text
    return default_value


async def _save_answer(
    state: FSMContext, question_key: str, answer_value: str, answer_text: str
) -> None:
    """Сохраняет ответ пользователя в состоянии"""
    data = await state.get_data()
    answers = data.get("answers", {})
    answers[question_key] = {"value": answer_value, "text": answer_text}
    await state.update_data(answers=answers)


async def _handle_next_step(
    callback: CallbackQuery, state: FSMContext, question_key: str, category: str
) -> None:
    """Обрабатывает переход к следующему вопросу или результатам"""
    questions = list(CATEGORY_QUESTIONS[category].keys())
    current_index = questions.index(question_key)

    if current_index + 1 < len(questions):
        await _show_next_question(callback, state, category, questions, current_index)
    else:
        await _handle_processing_state(callback, state, category)


async def _show_next_question(
    callback: CallbackQuery, state: FSMContext, category: str, questions: list, current_index: int
) -> None:
    """Показывает следующий вопрос"""
    next_question_key = questions[current_index + 1]
    question_data = CATEGORY_QUESTIONS[category][next_question_key]

    await state.set_state(question_data["next_state"])

    current_question_num = get_current_question_number(category, next_question_key)
    progress_text = get_progress_text(category, current_question_num)
    full_text = f"{progress_text}\n\n{question_data['text']}"

    if callback.message and isinstance(callback.message, Message):
        await callback.message.edit_text(full_text, reply_markup=question_data["keyboard"]())


async def _handle_processing_state(
    callback: CallbackQuery, state: FSMContext, category: str
) -> None:
    """Обрабатывает состояние processing - переход к результатам"""
    logger.info("Пользователь %d завершил опрос категории %s", callback.from_user.id, category)

    # Устанавливаем состояние обработки
    if category == "family":
        await state.set_state(FamilyTravelStates.processing)
    elif category == "pets":
        await state.set_state(PetTravelStates.processing)
    elif category == "photo":
        await state.set_state(PhotoTravelStates.processing)
    elif category == "budget":
        await state.set_state(BudgetTravelStates.processing)
    elif category == "active":
        await state.set_state(ActiveTravelStates.processing)

    # Показываем сообщение о поиске
    if callback.message and isinstance(callback.message, Message):
        await callback.message.edit_text(
            "🔍 Ищу идеальное место для вашего путешествия...\n\n"
            "Это может занять несколько секунд."
        )

    # Здесь будет вызов use case для получения рекомендации
    # Пока что просто переходим к результатам (будет реализовано в handlers/results.py)
    await show_travel_recommendation(callback, state)
