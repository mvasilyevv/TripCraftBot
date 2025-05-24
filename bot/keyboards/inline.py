"""Модуль для создания inline клавиатур Telegram бота"""

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from bot.states.travel import TRAVEL_CATEGORIES


def _add_back_button(
    buttons: list[list[InlineKeyboardButton]],
    back_callback: str = "action:back"
) -> None:
    """Добавляет кнопку 'Назад' к списку кнопок"""
    buttons.append([InlineKeyboardButton(text="⬅️ Назад", callback_data=back_callback)])


def get_main_menu_keyboard() -> InlineKeyboardMarkup:
    """Создает клавиатуру главного меню с категориями путешествий"""
    buttons = []
    for category_key, category_name in TRAVEL_CATEGORIES.items():
        button = InlineKeyboardButton(text=category_name, callback_data=f"category:{category_key}")
        buttons.append([button])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_destination_keyboard(show_back_to_menu: bool = True) -> InlineKeyboardMarkup:
    """Клавиатура для выбора направления путешествия"""
    buttons = [
        [InlineKeyboardButton(text="🌍 Подобрать автоматически", callback_data="destination:auto")],
        [InlineKeyboardButton(text="📍 Указать город/страну", callback_data="destination:manual")],
    ]

    # Добавляем кнопку "Назад" (к главному меню для первого вопроса)
    if show_back_to_menu:
        buttons.append([InlineKeyboardButton(text="🏠 Главное меню", callback_data="action:menu")])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_family_size_keyboard(show_back: bool = True) -> InlineKeyboardMarkup:
    """Клавиатура для выбора размера семьи"""
    buttons = [
        [InlineKeyboardButton(text="2 взрослых", callback_data="family_size:2+0")],
        [InlineKeyboardButton(text="2 взрослых + 1 ребенок", callback_data="family_size:2+1")],
        [InlineKeyboardButton(text="2 взрослых + 2 детей", callback_data="family_size:2+2")],
        [InlineKeyboardButton(text="Другое", callback_data="family_size:other")],
    ]

    if show_back:
        _add_back_button(buttons)

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_travel_time_keyboard(show_back: bool = True) -> InlineKeyboardMarkup:
    """Клавиатура для выбора времени путешествия"""
    buttons = [
        [InlineKeyboardButton(text="Ближайший месяц", callback_data="time:month")],
        [InlineKeyboardButton(text="Через 2-3 месяца", callback_data="time:quarter")],
        [InlineKeyboardButton(text="Через полгода", callback_data="time:half_year")],
    ]

    if show_back:
        _add_back_button(buttons)

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_family_priority_keyboard(show_back: bool = True) -> InlineKeyboardMarkup:
    """Клавиатура для выбора приоритетов семейного путешествия"""
    buttons = [
        [InlineKeyboardButton(text="Море/пляж", callback_data="priority:beach")],
        [InlineKeyboardButton(text="Развлечения", callback_data="priority:entertainment")],
        [InlineKeyboardButton(text="Культура", callback_data="priority:culture")],
    ]

    if show_back:
        _add_back_button(buttons)

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_pet_type_keyboard(show_back: bool = True) -> InlineKeyboardMarkup:
    """Клавиатура для выбора типа питомца"""
    buttons = [
        [InlineKeyboardButton(text="Собака малая", callback_data="pet:small_dog")],
        [InlineKeyboardButton(text="Собака крупная", callback_data="pet:large_dog")],
        [InlineKeyboardButton(text="Кошка", callback_data="pet:cat")],
    ]

    if show_back:
        _add_back_button(buttons)

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_transport_keyboard(show_back: bool = True) -> InlineKeyboardMarkup:
    """Клавиатура для выбора транспорта"""
    buttons = [
        [InlineKeyboardButton(text="Авто", callback_data="transport:car")],
        [InlineKeyboardButton(text="Поезд", callback_data="transport:train")],
        [InlineKeyboardButton(text="Самолет", callback_data="transport:plane")],
    ]

    if show_back:
        _add_back_button(buttons)

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_duration_keyboard(show_back: bool = True) -> InlineKeyboardMarkup:
    """Клавиатура для выбора продолжительности поездки"""
    buttons = [
        [InlineKeyboardButton(text="Выходные", callback_data="duration:weekend")],
        [InlineKeyboardButton(text="Неделя", callback_data="duration:week")],
        [InlineKeyboardButton(text="2+ недели", callback_data="duration:long")],
    ]

    if show_back:
        _add_back_button(buttons)

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_photo_type_keyboard(show_back: bool = True) -> InlineKeyboardMarkup:
    """Клавиатура для выбора типа фотографий"""
    buttons = [
        [InlineKeyboardButton(text="Природа", callback_data="photo:nature")],
        [InlineKeyboardButton(text="Архитектура", callback_data="photo:architecture")],
        [InlineKeyboardButton(text="Стрит-фото", callback_data="photo:street")],
    ]

    if show_back:
        _add_back_button(buttons)

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_difficulty_keyboard(show_back: bool = True) -> InlineKeyboardMarkup:
    """Клавиатура для выбора сложности маршрута"""
    buttons = [
        [InlineKeyboardButton(text="Только легкие места", callback_data="difficulty:easy")],
        [InlineKeyboardButton(text="Готов к треккингу", callback_data="difficulty:hard")],
    ]

    if show_back:
        _add_back_button(buttons)

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_budget_keyboard(show_back: bool = True) -> InlineKeyboardMarkup:
    """Клавиатура для выбора бюджета"""
    buttons = [
        [InlineKeyboardButton(text="До 30 000₽", callback_data="budget:30000")],
        [InlineKeyboardButton(text="30-50 тыс₽", callback_data="budget:50000")],
        [InlineKeyboardButton(text="50-80 тыс₽", callback_data="budget:80000")],
    ]

    if show_back:
        _add_back_button(buttons)

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_budget_days_keyboard(show_back: bool = True) -> InlineKeyboardMarkup:
    """Клавиатура для выбора количества дней поездки"""
    buttons = [
        [InlineKeyboardButton(text="3-4 дня", callback_data="days:short")],
        [InlineKeyboardButton(text="Неделя", callback_data="days:week")],
        [InlineKeyboardButton(text="10+ дней", callback_data="days:long")],
    ]

    if show_back:
        _add_back_button(buttons)

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_included_keyboard(show_back: bool = True) -> InlineKeyboardMarkup:
    """Клавиатура для выбора включенных услуг"""
    buttons = [
        [InlineKeyboardButton(text="Только проживание", callback_data="included:accommodation")],
        [InlineKeyboardButton(text="Все включено", callback_data="included:all")],
    ]

    if show_back:
        _add_back_button(buttons)

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_activity_type_keyboard(show_back: bool = True) -> InlineKeyboardMarkup:
    """Клавиатура для выбора типа активности"""
    buttons = [
        [InlineKeyboardButton(text="Горы/треккинг", callback_data="activity:mountains")],
        [InlineKeyboardButton(text="Вело", callback_data="activity:cycling")],
        [InlineKeyboardButton(text="Водный спорт", callback_data="activity:water")],
    ]

    if show_back:
        _add_back_button(buttons)

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_skill_level_keyboard(show_back: bool = True) -> InlineKeyboardMarkup:
    """Клавиатура для выбора уровня навыков"""
    buttons = [
        [InlineKeyboardButton(text="Новичок", callback_data="skill:beginner")],
        [InlineKeyboardButton(text="Любитель", callback_data="skill:amateur")],
        [InlineKeyboardButton(text="Профи", callback_data="skill:pro")],
    ]

    if show_back:
        _add_back_button(buttons)

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_result_actions_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура с действиями для результатов поиска"""
    buttons = [
        [
            InlineKeyboardButton(text="🔄 Другой вариант", callback_data="action:retry"),
            InlineKeyboardButton(text="📤 Поделиться", callback_data="action:share"),
        ],
        [InlineKeyboardButton(text="🏠 Главное меню", callback_data="action:menu")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_new_search_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура для начала нового поиска"""
    buttons = [
        [InlineKeyboardButton(text="🔍 Новый поиск", callback_data="action:new_search")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)
