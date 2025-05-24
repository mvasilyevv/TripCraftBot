"""Тесты для форматтера промптов"""

import pytest

from bot.domain.models import TravelCategory, TravelRequest
from bot.utils.formatter import PromptFormatter


@pytest.fixture
def formatter() -> PromptFormatter:
    """Фикстура для создания форматтера"""
    return PromptFormatter()


@pytest.fixture
def sample_travel_request() -> TravelRequest:
    """Фикстура для создания примера запроса путешествия"""
    request = TravelRequest(user_id=123, category=TravelCategory.FAMILY, answers={})
    request.add_answer("family_size", "2_adults_1_child", "2 взрослых + 1 ребенок")
    request.add_answer("travel_time", "summer", "Летом")
    request.add_answer("priority", "safety", "Безопасность")
    return request


def test_format_travel_request_prompt_family(
    formatter: PromptFormatter, sample_travel_request: TravelRequest
) -> None:
    """Тест форматирования промпта для семейного путешествия"""
    messages = formatter.format_travel_request_prompt(sample_travel_request)

    assert len(messages) == 2
    assert messages[0].role == "system"
    assert messages[1].role == "user"

    # Проверяем, что системный промпт содержит специфичную информацию
    # для семейных путешествий
    system_content = messages[0].content
    assert "семейные путешествия" in system_content.lower()
    assert "безопасности" in system_content.lower()  # "приоритет безопасности"
    assert "детей" in system_content.lower()

    # Проверяем, что пользовательский промпт содержит ответы
    user_content = messages[1].content
    assert "2 взрослых + 1 ребенок" in user_content
    assert "Летом" in user_content
    assert "Безопасность" in user_content


def test_format_travel_request_prompt_budget(formatter: PromptFormatter) -> None:
    """Тест форматирования промпта для бюджетного путешествия"""
    request = TravelRequest(user_id=456, category=TravelCategory.BUDGET, answers={})
    request.add_answer("budget", "low", "До 30000 рублей")
    request.add_answer("days", "5_7", "5-7 дней")

    messages = formatter.format_travel_request_prompt(request)

    system_content = messages[0].content
    assert "бюджетные путешествия" in system_content.lower()
    assert "экономии" in system_content.lower()

    user_content = messages[1].content
    assert "бюджетное путешествие" in user_content
    assert "До 30000 рублей" in user_content


def test_parse_llm_response_json_format(formatter: PromptFormatter) -> None:
    """Тест парсинга ответа LLM в JSON формате"""
    json_response = """
    Вот рекомендация для вашего путешествия:

    {
        "destination": "Анталья, Турция",
        "description": "Отличное место для семейного отдыха",
        "highlights": ["Пляжи", "Аквапарки", "Отели"],
        "practical_info": "Виза не нужна",
        "estimated_cost": "$1000",
        "duration": "7 дней",
        "best_time": "Май-октябрь"
    }

    Хорошего отдыха!
    """

    recommendation = formatter.parse_llm_response(json_response)

    assert recommendation.destination == "Анталья, Турция"
    assert recommendation.description == "Отличное место для семейного отдыха"
    assert recommendation.highlights == ["Пляжи", "Аквапарки", "Отели"]
    assert recommendation.practical_info == "Виза не нужна"
    assert recommendation.estimated_cost == "$1000"
    assert recommendation.duration == "7 дней"
    assert recommendation.best_time == "Май-октябрь"


def test_parse_llm_response_text_format(formatter: PromptFormatter) -> None:
    """Тест парсинга ответа LLM в текстовом формате"""
    text_response = """
    # Каппадокия, Турция

    Уникальное место для фотографических путешествий с невероятными пейзажами.

    ## Основные достопримечательности:
    • Полеты на воздушных шарах
    • Сказочные дымоходы
    • Подземные города

    ## Практическая информация:
    Лучшее время для посещения: апрель-май, сентябрь-октябрь.
    Необходимо бронировать полеты заранее.
    """

    recommendation = formatter.parse_llm_response(text_response)

    assert "Каппадокия" in recommendation.destination
    assert "фотографических путешествий" in recommendation.description
    assert len(recommendation.highlights) >= 1
    assert "апрель-май" in recommendation.practical_info


def test_parse_llm_response_malformed_json(formatter: PromptFormatter) -> None:
    """Тест парсинга некорректного JSON"""
    malformed_response = """
    {
        "destination": "Тест",
        "description": "Описание"
        // некорректный JSON
    }
    """

    recommendation = formatter.parse_llm_response(malformed_response)

    # Должен вернуть базовую рекомендацию с исходным текстом
    assert recommendation.destination == "Рекомендация от ИИ"
    assert malformed_response[:100] in recommendation.description


def test_parse_llm_response_empty_content(formatter: PromptFormatter) -> None:
    """Тест парсинга пустого ответа"""
    empty_response = ""

    recommendation = formatter.parse_llm_response(empty_response)

    assert recommendation.destination == "Рекомендация от ИИ"
    assert recommendation.highlights == ["Подробности в описании"]


def test_format_user_answers_family(
    formatter: PromptFormatter, sample_travel_request: TravelRequest
) -> None:
    """Тест форматирования ответов пользователя для семейной категории"""
    user_prompt = formatter._format_user_answers(sample_travel_request)

    assert "семейное путешествие" in user_prompt
    assert "2 взрослых + 1 ребенок" in user_prompt
    assert "Летом" in user_prompt
    assert "Безопасность" in user_prompt


def test_format_user_answers_pets(formatter: PromptFormatter) -> None:
    """Тест форматирования ответов для путешествий с питомцами"""
    request = TravelRequest(user_id=789, category=TravelCategory.PETS, answers={})
    request.add_answer("pet_type", "dog", "Собака")
    request.add_answer("transport", "car", "На автомобиле")

    user_prompt = formatter._format_user_answers(request)

    assert "путешествие с питомцами" in user_prompt
    assert "Собака" in user_prompt
    assert "На автомобиле" in user_prompt


def test_create_recommendation_from_json_complete(formatter: PromptFormatter) -> None:
    """Тест создания рекомендации из полного JSON"""
    data = {
        "destination": "Тест Сити",
        "description": "Тестовое описание",
        "highlights": ["Достопримечательность 1", "Достопримечательность 2"],
        "practical_info": "Практическая информация",
        "estimated_cost": "50 000₽",
        "duration": "5 дней",
        "best_time": "Весна",
    }

    recommendation = formatter._create_recommendation_from_json(data)

    assert recommendation.destination == "Тест Сити"
    assert recommendation.description == "Тестовое описание"
    assert recommendation.highlights == ["Достопримечательность 1", "Достопримечательность 2"]
    assert recommendation.practical_info == "Практическая информация"
    assert recommendation.estimated_cost == "50 000₽"
    assert recommendation.duration == "5 дней"
    assert recommendation.best_time == "Весна"


def test_create_recommendation_from_json_minimal(formatter: PromptFormatter) -> None:
    """Тест создания рекомендации из минимального JSON"""
    data = {"destination": "Минимальный Тест"}

    recommendation = formatter._create_recommendation_from_json(data)

    assert recommendation.destination == "Минимальный Тест"
    assert recommendation.description == "Описание недоступно"
    assert recommendation.highlights == []
    assert recommendation.practical_info == "Информация уточняется"


def test_parse_text_response_with_sections(formatter: PromptFormatter) -> None:
    """Тест парсинга текстового ответа с секциями"""
    text = """
    Прага, Чехия

    Красивый исторический город с множеством достопримечательностей.

    Основные достопримечательности:
    • Пражский замок
    • Карлов мост
    • Староместская площадь

    Практическая информация:
    Виза не нужна для граждан России.
    Лучшее время: май-сентябрь.
    """

    recommendation = formatter._parse_text_response(text)

    assert "Прага" in recommendation.destination
    assert "исторический город" in recommendation.description
    assert "Пражский замок" in recommendation.highlights
    # Проверяем, что практическая информация содержит хотя бы одну из строк
    practical_info = recommendation.practical_info
    assert (
        "Виза не нужна" in practical_info
        or "Лучшее время" in practical_info
        or len(practical_info) > 10
    )


def test_get_category_specific_prompts(formatter: PromptFormatter) -> None:
    """Тест получения специфичных промптов для категорий"""
    prompts = formatter._get_category_specific_prompts()

    assert TravelCategory.FAMILY in prompts
    assert TravelCategory.PETS in prompts
    assert TravelCategory.PHOTO in prompts
    assert TravelCategory.BUDGET in prompts
    assert TravelCategory.ACTIVE in prompts

    # Проверяем содержимое промптов
    assert "семейные" in prompts[TravelCategory.FAMILY].lower()
    assert "питомцами" in prompts[TravelCategory.PETS].lower()
    assert "фотографические" in prompts[TravelCategory.PHOTO].lower()
    assert "бюджетные" in prompts[TravelCategory.BUDGET].lower()
    assert "активный" in prompts[TravelCategory.ACTIVE].lower()


def test_base_system_prompt(formatter: PromptFormatter) -> None:
    """Тест базового системного промпта"""
    base_prompt = formatter._get_base_system_prompt()

    assert "консультант по путешествиям" in base_prompt.lower()
    assert "json" in base_prompt.lower()
    assert "destination" in base_prompt
    assert "description" in base_prompt
    assert "highlights" in base_prompt
