from aiogram.fsm.state import State, StatesGroup


class FamilyTravelStates(StatesGroup):
    asking_family_size = State()
    asking_travel_time = State()
    asking_priority = State()
    processing = State()


class PetTravelStates(StatesGroup):
    asking_pet_type = State()
    asking_transport = State()
    asking_duration = State()
    processing = State()


class PhotoTravelStates(StatesGroup):
    asking_photo_type = State()
    asking_difficulty = State()
    processing = State()


class BudgetTravelStates(StatesGroup):
    asking_budget = State()
    asking_days = State()
    asking_included = State()
    processing = State()


class ActiveTravelStates(StatesGroup):
    asking_activity_type = State()
    asking_skill_level = State()
    processing = State()


# Константы для категорий путешествий
TRAVEL_CATEGORIES = {
    "family": "🏖 Семейное путешествие",
    "pets": "🐾 Путешествие с питомцами",
    "photo": "📸 Лучшие места для фото",
    "budget": "💰 Бюджетное путешествие",
    "active": "🏔 Активный отдых",
}

# Маппинг категорий на состояния
CATEGORY_STATES = {
    "family": FamilyTravelStates,
    "pets": PetTravelStates,
    "photo": PhotoTravelStates,
    "budget": BudgetTravelStates,
    "active": ActiveTravelStates,
}

# Количество вопросов для каждой категории
CATEGORY_QUESTIONS_COUNT = {
    "family": 3,
    "pets": 3,
    "photo": 2,
    "budget": 3,
    "active": 2,
}
