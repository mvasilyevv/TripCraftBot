"""Обработчики категорий путешествий"""

import logging
from typing import Any

from aiogram import Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot.domain.models import TravelCategory
from bot.handlers.utils import get_current_question_number, get_progress_text
from bot.infrastructure.service_factory import get_service_factory
from bot.keyboards.inline import (
    get_activity_type_keyboard,
    get_budget_days_keyboard,
    get_budget_keyboard,
    get_destination_keyboard,
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
    ActiveTravelStates,
    BudgetTravelStates,
    FamilyTravelStates,
    PetTravelStates,
    PhotoTravelStates,
)

logger = logging.getLogger(__name__)

router = Router()


# Маппинг состояний для навигации назад (строковые представления)
BACK_NAVIGATION_MAP = {
    # Family
    "FamilyTravelStates:asking_family_size": FamilyTravelStates.asking_destination,
    "FamilyTravelStates:asking_travel_time": FamilyTravelStates.asking_family_size,
    "FamilyTravelStates:asking_priority": FamilyTravelStates.asking_travel_time,

    # Pets
    "PetTravelStates:asking_pet_type": PetTravelStates.asking_destination,
    "PetTravelStates:asking_transport": PetTravelStates.asking_pet_type,
    "PetTravelStates:asking_duration": PetTravelStates.asking_transport,

    # Photo
    "PhotoTravelStates:asking_photo_type": PhotoTravelStates.asking_destination,
    "PhotoTravelStates:asking_difficulty": PhotoTravelStates.asking_photo_type,

    # Budget
    "BudgetTravelStates:asking_budget": BudgetTravelStates.asking_destination,
    "BudgetTravelStates:asking_days": BudgetTravelStates.asking_budget,
    "BudgetTravelStates:asking_included": BudgetTravelStates.asking_days,

    # Active
    "ActiveTravelStates:asking_activity_type": ActiveTravelStates.asking_destination,
    "ActiveTravelStates:asking_skill_level": ActiveTravelStates.asking_activity_type,
}


# Маппинг состояний к категориям и вопросам для навигации назад
STATE_TO_CATEGORY_QUESTION = {
    # Family
    FamilyTravelStates.asking_destination: ("family", "destination"),
    FamilyTravelStates.asking_family_size: ("family", "family_size"),
    FamilyTravelStates.asking_travel_time: ("family", "travel_time"),
    FamilyTravelStates.asking_priority: ("family", "priority"),

    # Pets
    PetTravelStates.asking_destination: ("pets", "destination"),
    PetTravelStates.asking_pet_type: ("pets", "pet_type"),
    PetTravelStates.asking_transport: ("pets", "transport"),
    PetTravelStates.asking_duration: ("pets", "duration"),

    # Photo
    PhotoTravelStates.asking_destination: ("photo", "destination"),
    PhotoTravelStates.asking_photo_type: ("photo", "photo_type"),
    PhotoTravelStates.asking_difficulty: ("photo", "difficulty"),

    # Budget
    BudgetTravelStates.asking_destination: ("budget", "destination"),
    BudgetTravelStates.asking_budget: ("budget", "budget"),
    BudgetTravelStates.asking_days: ("budget", "days"),
    BudgetTravelStates.asking_included: ("budget", "included"),

    # Active
    ActiveTravelStates.asking_destination: ("active", "destination"),
    ActiveTravelStates.asking_activity_type: ("active", "activity_type"),
    ActiveTravelStates.asking_skill_level: ("active", "skill_level"),
}


async def handle_back_navigation(callback: CallbackQuery, state: FSMContext) -> None:
    """Обрабатывает навигацию назад по вопросам"""
    current_state = await state.get_state()

    if not current_state:
        # Если состояния нет, возвращаемся в главное меню
        from bot.keyboards.inline import get_main_menu_keyboard
        if callback.message and isinstance(callback.message, Message):
            await callback.message.edit_text(
                "Выберите тип путешествия:",
                reply_markup=get_main_menu_keyboard()
            )
        return

    # Получаем предыдущее состояние
    previous_state = BACK_NAVIGATION_MAP.get(current_state)

    if not previous_state:
        # Если предыдущего состояния нет, возвращаемся в главное меню
        from bot.keyboards.inline import get_main_menu_keyboard
        await state.clear()
        if callback.message and isinstance(callback.message, Message):
            await callback.message.edit_text(
                "Выберите тип путешествия:",
                reply_markup=get_main_menu_keyboard()
            )
        return

    # Устанавливаем предыдущее состояние
    await state.set_state(previous_state)

    # Получаем информацию о предыдущем вопросе
    category, question_key = STATE_TO_CATEGORY_QUESTION.get(previous_state, (None, None))

    if not category or not question_key:
        # Если не можем определить категорию, возвращаемся в главное меню
        from bot.keyboards.inline import get_main_menu_keyboard
        await state.clear()
        if callback.message and isinstance(callback.message, Message):
            await callback.message.edit_text(
                "Выберите тип путешествия:",
                reply_markup=get_main_menu_keyboard()
            )
        return

    # Получаем данные вопроса
    question_data = CATEGORY_QUESTIONS[category][question_key]
    question_text = question_data["text"]
    keyboard_func = question_data["keyboard"]

    # Получаем номер текущего вопроса для прогресса
    current_question = get_current_question_number(category, question_key)
    progress_text = get_progress_text(category, current_question)

    # Формируем полный текст с прогрессом
    full_text = f"{progress_text}\n\n{question_text}"

    # Определяем, какую кнопку "Назад" показывать
    if question_key == "destination":
        # Для первого вопроса показываем кнопку "Главное меню"
        keyboard = keyboard_func(show_back_to_menu=True)
    else:
        # Для остальных вопросов показываем кнопку "Назад"
        keyboard = keyboard_func(show_back=True)

    # Отправляем предыдущий вопрос
    if callback.message and isinstance(callback.message, Message):
        await callback.message.edit_text(full_text, reply_markup=keyboard)


# Маппинг вопросов для каждой категории
CATEGORY_QUESTIONS: dict[str, dict[str, dict[str, Any]]] = {
    "family": {
        "destination": {
            "text": "Куда хотите поехать?",
            "keyboard": get_destination_keyboard,
            "next_state": FamilyTravelStates.asking_family_size,
        },
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
        "destination": {
            "text": "Куда хотите поехать с питомцем?",
            "keyboard": get_destination_keyboard,
            "next_state": PetTravelStates.asking_pet_type,
        },
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
        "destination": {
            "text": "В каком городе/стране ищете места для фото?",
            "keyboard": get_destination_keyboard,
            "next_state": PhotoTravelStates.asking_photo_type,
        },
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
        "destination": {
            "text": "Куда хотите поехать?",
            "keyboard": get_destination_keyboard,
            "next_state": BudgetTravelStates.asking_budget,
        },
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
        "destination": {
            "text": "В каком городе/стране ищете активный отдых?",
            "keyboard": get_destination_keyboard,
            "next_state": ActiveTravelStates.asking_activity_type,
        },
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
    FamilyTravelStates.asking_destination: ("family", "destination"),
    FamilyTravelStates.asking_family_size: ("family", "family_size"),
    FamilyTravelStates.asking_travel_time: ("family", "travel_time"),
    FamilyTravelStates.asking_priority: ("family", "priority"),
    # Pets
    PetTravelStates.asking_destination: ("pets", "destination"),
    PetTravelStates.asking_pet_type: ("pets", "pet_type"),
    PetTravelStates.asking_transport: ("pets", "transport"),
    PetTravelStates.asking_duration: ("pets", "duration"),
    # Photo
    PhotoTravelStates.asking_destination: ("photo", "destination"),
    PhotoTravelStates.asking_photo_type: ("photo", "photo_type"),
    PhotoTravelStates.asking_difficulty: ("photo", "difficulty"),
    # Budget
    BudgetTravelStates.asking_destination: ("budget", "destination"),
    BudgetTravelStates.asking_budget: ("budget", "budget"),
    BudgetTravelStates.asking_days: ("budget", "days"),
    BudgetTravelStates.asking_included: ("budget", "included"),
    # Active
    ActiveTravelStates.asking_destination: ("active", "destination"),
    ActiveTravelStates.asking_activity_type: ("active", "activity_type"),
    ActiveTravelStates.asking_skill_level: ("active", "skill_level"),
}


@router.callback_query(lambda c: c.data and c.data.startswith("destination:auto"))
async def callback_destination_auto(callback: CallbackQuery, state: FSMContext) -> None:
    """Обработчик выбора автоматического подбора направления"""
    if not callback.message or not isinstance(callback.message, Message):
        await callback.answer("Ошибка: сообщение недоступно")
        return

    user_id = callback.from_user.id if callback.from_user else 0
    logger.info("Пользователь %d выбрал автоматический подбор направления", user_id)

    # Сохраняем выбор автоматического подбора
    data = await state.get_data()
    category = data.get("category")
    if not category:
        await callback.answer("Ошибка: категория не найдена")
        return

    try:
        # Сохраняем ответ через use case
        service_factory = get_service_factory()
        process_answer_use_case = service_factory.get_process_answer_use_case()

        await process_answer_use_case.execute(
            user_id=user_id,
            question_key="destination",
            answer_value="auto",
            answer_text="Направление: подобрать автоматически",
        )

        # Также сохраняем в состоянии FSM для совместимости
        answers = data.get("answers", {})
        answers["destination"] = {
            "question_key": "destination",
            "answer_value": "auto",
            "answer_text": "Направление: подобрать автоматически",
        }
        await state.update_data(answers=answers)

    except Exception as e:
        logger.error("Ошибка при сохранении автоматического направления для пользователя %d: %s", user_id, str(e))
        await callback.answer("Произошла ошибка. Попробуйте еще раз.")
        return

    # Переходим к следующему вопросу
    questions = list(CATEGORY_QUESTIONS[category].keys())
    next_question_key = questions[1]  # Второй вопрос после направления
    question_data = CATEGORY_QUESTIONS[category][next_question_key]

    # Устанавливаем правильное состояние для следующего вопроса
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

    current_question_num = get_current_question_number(category, next_question_key)
    progress_text = get_progress_text(category, current_question_num)
    full_text = f"{progress_text}\n\n{question_data['text']}"

    keyboard = question_data["keyboard"](show_back=True)
    await callback.message.edit_text(full_text, reply_markup=keyboard)
    await callback.answer()


@router.callback_query(lambda c: c.data and c.data.startswith("destination:manual"))
async def callback_destination_manual(callback: CallbackQuery, state: FSMContext) -> None:
    """Обработчик выбора ручного ввода направления"""
    if not callback.message or not isinstance(callback.message, Message):
        await callback.answer("Ошибка: сообщение недоступно")
        return

    user_id = callback.from_user.id if callback.from_user else 0
    logger.info("Пользователь %d выбрал ручной ввод направления", user_id)

    # Просим пользователя ввести направление
    await callback.message.edit_text(
        "📍 Введите город или страну, куда хотите поехать:\n\n"
        "Например: Париж, Франция или Бали, Индонезия"
    )
    await callback.answer()


@router.message()
async def handle_destination_input(message: Message, state: FSMContext) -> None:
    """Обработчик ввода направления пользователем"""
    if not message.text:
        return

    user_id = message.from_user.id if message.from_user else 0
    current_state = await state.get_state()

    # Проверяем, что пользователь находится в состоянии ввода направления
    if not current_state or "asking_destination" not in current_state:
        return

    destination = message.text.strip()
    logger.info("Пользователь %d ввел направление: %s", user_id, destination)

    # Сохраняем направление как ответ
    data = await state.get_data()
    category = data.get("category")
    if not category:
        await message.answer("Ошибка: категория не найдена. Начните заново с /start")
        return

    try:
        # Сохраняем ответ через use case
        service_factory = get_service_factory()
        process_answer_use_case = service_factory.get_process_answer_use_case()

        await process_answer_use_case.execute(
            user_id=user_id,
            question_key="destination",
            answer_value=destination,  # Сохраняем само направление как значение
            answer_text=f"Направление: {destination}",
        )

        # Также сохраняем в состоянии FSM для совместимости
        answers = data.get("answers", {})
        answers["destination"] = {
            "question_key": "destination",
            "answer_value": destination,  # Сохраняем само направление
            "answer_text": f"Направление: {destination}",
        }
        await state.update_data(answers=answers)

    except Exception as e:
        logger.error("Ошибка при сохранении направления для пользователя %d: %s", user_id, str(e))
        await message.answer("Произошла ошибка при сохранении направления. Попробуйте еще раз.")
        return

    # Переходим к следующему вопросу
    questions = list(CATEGORY_QUESTIONS[category].keys())
    next_question_key = questions[1]  # Второй вопрос после направления
    question_data = CATEGORY_QUESTIONS[category][next_question_key]

    # Устанавливаем правильное состояние для следующего вопроса
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

    current_question_num = get_current_question_number(category, next_question_key)
    progress_text = get_progress_text(category, current_question_num)
    full_text = f"{progress_text}\n\n{question_data['text']}"

    keyboard = question_data["keyboard"](show_back=True)
    await message.answer(full_text, reply_markup=keyboard)


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

        # Устанавливаем состояние для первого вопроса (направление)
        if category == "family":
            await state.set_state(FamilyTravelStates.asking_destination)
        elif category == "pets":
            await state.set_state(PetTravelStates.asking_destination)
        elif category == "photo":
            await state.set_state(PhotoTravelStates.asking_destination)
        elif category == "budget":
            await state.set_state(BudgetTravelStates.asking_destination)
        elif category == "active":
            await state.set_state(ActiveTravelStates.asking_destination)

        # Формируем текст с индикатором прогресса
        progress_text = get_progress_text(category, 1)
        full_text = f"{progress_text}\n\n{question_data['text']}"

        # Отправляем первый вопрос (для первого вопроса показываем кнопку "Главное меню")
        if callback.message and isinstance(callback.message, Message):
            keyboard = question_data["keyboard"](show_back_to_menu=True)
            await callback.message.edit_text(full_text, reply_markup=keyboard)

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

    # Проверяем, был ли уже ответ на этот вопрос
    if question_key in answers:
        old_value = answers[question_key].get("value", "")
        logger.info("Перезаписываем ответ на вопрос %s: '%s' → '%s'",
                   question_key, old_value, answer_value)
    else:
        logger.info("Сохраняем новый ответ на вопрос %s: '%s'", question_key, answer_value)

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
    callback: CallbackQuery,
    state: FSMContext,
    category: str,
    questions: list[str],
    current_index: int,
) -> None:
    """Показывает следующий вопрос"""
    next_question_key = questions[current_index + 1]
    question_data = CATEGORY_QUESTIONS[category][next_question_key]

    await state.set_state(question_data["next_state"])

    current_question_num = get_current_question_number(category, next_question_key)
    progress_text = get_progress_text(category, current_question_num)
    full_text = f"{progress_text}\n\n{question_data['text']}"

    # Определяем, нужно ли показывать кнопку "Назад"
    show_back = True  # Для всех вопросов кроме первого показываем кнопку "Назад"

    if callback.message and isinstance(callback.message, Message):
        keyboard = question_data["keyboard"](show_back=show_back)
        await callback.message.edit_text(full_text, reply_markup=keyboard)


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
            "🔍 Ищу идеальное место для вашего путешествия...\n\nЭто может занять несколько секунд."
        )

    # Здесь будет вызов use case для получения рекомендации
    # Пока что просто переходим к результатам (будет реализовано в handlers/results.py)
    # Используем отложенный импорт для избежания циклических зависимостей
    from bot.handlers.results import show_travel_recommendation

    await show_travel_recommendation(callback, state)
