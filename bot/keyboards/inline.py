from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from bot.states.travel import TRAVEL_CATEGORIES


def get_main_menu_keyboard() -> InlineKeyboardMarkup:
    buttons = []
    for category_key, category_name in TRAVEL_CATEGORIES.items():
        button = InlineKeyboardButton(text=category_name, callback_data=f"category:{category_key}")
        buttons.append([button])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_family_size_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text="2 взрослых", callback_data="family_size:2+0")],
        [InlineKeyboardButton(text="2 взрослых + 1 ребенок", callback_data="family_size:2+1")],
        [InlineKeyboardButton(text="2 взрослых + 2 детей", callback_data="family_size:2+2")],
        [InlineKeyboardButton(text="Другое", callback_data="family_size:other")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_travel_time_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text="Ближайший месяц", callback_data="time:month")],
        [InlineKeyboardButton(text="Через 2-3 месяца", callback_data="time:quarter")],
        [InlineKeyboardButton(text="Через полгода", callback_data="time:half_year")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_family_priority_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text="Море/пляж", callback_data="priority:beach")],
        [InlineKeyboardButton(text="Развлечения", callback_data="priority:entertainment")],
        [InlineKeyboardButton(text="Культура", callback_data="priority:culture")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_pet_type_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text="Собака малая", callback_data="pet:small_dog")],
        [InlineKeyboardButton(text="Собака крупная", callback_data="pet:large_dog")],
        [InlineKeyboardButton(text="Кошка", callback_data="pet:cat")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_transport_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text="Авто", callback_data="transport:car")],
        [InlineKeyboardButton(text="Поезд", callback_data="transport:train")],
        [InlineKeyboardButton(text="Самолет", callback_data="transport:plane")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_duration_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text="Выходные", callback_data="duration:weekend")],
        [InlineKeyboardButton(text="Неделя", callback_data="duration:week")],
        [InlineKeyboardButton(text="2+ недели", callback_data="duration:long")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_photo_type_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text="Природа", callback_data="photo:nature")],
        [InlineKeyboardButton(text="Архитектура", callback_data="photo:architecture")],
        [InlineKeyboardButton(text="Стрит-фото", callback_data="photo:street")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_difficulty_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text="Только легкие места", callback_data="difficulty:easy")],
        [InlineKeyboardButton(text="Готов к треккингу", callback_data="difficulty:hard")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_budget_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text="До $300", callback_data="budget:300")],
        [InlineKeyboardButton(text="$300-500", callback_data="budget:500")],
        [InlineKeyboardButton(text="$500-800", callback_data="budget:800")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_budget_days_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text="3-4 дня", callback_data="days:short")],
        [InlineKeyboardButton(text="Неделя", callback_data="days:week")],
        [InlineKeyboardButton(text="10+ дней", callback_data="days:long")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_included_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text="Только проживание", callback_data="included:accommodation")],
        [InlineKeyboardButton(text="Все включено", callback_data="included:all")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_activity_type_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text="Горы/треккинг", callback_data="activity:mountains")],
        [InlineKeyboardButton(text="Вело", callback_data="activity:cycling")],
        [InlineKeyboardButton(text="Водный спорт", callback_data="activity:water")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_skill_level_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text="Новичок", callback_data="skill:beginner")],
        [InlineKeyboardButton(text="Любитель", callback_data="skill:amateur")],
        [InlineKeyboardButton(text="Профи", callback_data="skill:pro")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_result_actions_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        [
            InlineKeyboardButton(text="🔄 Другой вариант", callback_data="action:retry"),
            InlineKeyboardButton(text="📤 Поделиться", callback_data="action:share"),
        ],
        [InlineKeyboardButton(text="🏠 Главное меню", callback_data="action:menu")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_new_search_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text="🔍 Новый поиск", callback_data="action:new_search")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)
