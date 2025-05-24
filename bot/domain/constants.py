"""Константы доменного слоя"""

from typing import Dict, List

from .models import TravelCategory

# Маппинг категорий на их отображаемые названия
CATEGORY_NAMES: Dict[TravelCategory, str] = {
    TravelCategory.FAMILY: "🏖 Семейное путешествие",
    TravelCategory.PETS: "🐾 Путешествие с питомцами",
    TravelCategory.PHOTO: "📸 Лучшие места для фото",
    TravelCategory.BUDGET: "💰 Бюджетное путешествие",
    TravelCategory.ACTIVE: "🏔 Активный отдых",
}

# Обязательные вопросы для каждой категории
REQUIRED_QUESTIONS: Dict[TravelCategory, List[str]] = {
    TravelCategory.FAMILY: ["family_size", "travel_time", "priority"],
    TravelCategory.PETS: ["pet_type", "transport", "duration"],
    TravelCategory.PHOTO: ["photo_type", "difficulty"],
    TravelCategory.BUDGET: ["budget", "days", "included"],
    TravelCategory.ACTIVE: ["activity_type", "skill_level"],
}

# Количество вопросов для каждой категории
QUESTIONS_COUNT: Dict[TravelCategory, int] = {
    TravelCategory.FAMILY: 3,
    TravelCategory.PETS: 3,
    TravelCategory.PHOTO: 2,
    TravelCategory.BUDGET: 3,
    TravelCategory.ACTIVE: 2,
}

# Максимальное время жизни запроса пользователя (в секундах)
REQUEST_TTL = 3600  # 1 час

# Максимальное количество альтернативных рекомендаций
MAX_ALTERNATIVE_RECOMMENDATIONS = 5

# Лимиты для валидации
MAX_DESTINATION_LENGTH = 100
MAX_DESCRIPTION_LENGTH = 2000
MAX_HIGHLIGHTS_COUNT = 10
MAX_PRACTICAL_INFO_LENGTH = 1000
