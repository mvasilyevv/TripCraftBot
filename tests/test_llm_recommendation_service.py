"""Тесты для LLM сервиса рекомендаций"""

from unittest.mock import AsyncMock, MagicMock

import pytest

from bot.domain.models import (
    ExternalServiceError,
    TravelCategory,
    TravelRecommendation,
    TravelRequest,
)
from bot.infrastructure.llm_recommendation_service import LLMTravelRecommendationService
from bot.utils.formatter import PromptFormatter
from bot.utils.openrouter import OpenRouterClient, OpenRouterMessage


@pytest.fixture
def mock_openrouter_client() -> MagicMock:
    """Мок клиента OpenRouter"""
    client = MagicMock(spec=OpenRouterClient)
    client.generate_completion = AsyncMock()
    client.check_health = AsyncMock()
    return client


@pytest.fixture
def mock_formatter() -> MagicMock:
    """Мок форматтера промптов"""
    formatter = MagicMock(spec=PromptFormatter)
    formatter.format_travel_request_prompt = MagicMock()
    formatter.parse_llm_response = MagicMock()
    return formatter


@pytest.fixture
def llm_service(
    mock_openrouter_client: MagicMock, mock_formatter: MagicMock
) -> LLMTravelRecommendationService:
    """Фикстура для создания LLM сервиса"""
    return LLMTravelRecommendationService(
        openrouter_client=mock_openrouter_client,
        prompt_formatter=mock_formatter,
    )


@pytest.fixture
def sample_travel_request() -> TravelRequest:
    """Фикстура для создания примера запроса"""
    request = TravelRequest(user_id=123, category=TravelCategory.FAMILY, answers={})
    request.add_answer("family_size", "2_adults_1_child", "2 взрослых + 1 ребенок")
    return request


@pytest.fixture
def sample_recommendation() -> TravelRecommendation:
    """Фикстура для создания примера рекомендации"""
    return TravelRecommendation(
        destination="Анталья, Турция",
        description="Отличное место для семейного отдыха",
        highlights=["Пляжи", "Аквапарки", "Отели"],
        practical_info="Виза не нужна",
        estimated_cost="$1000",
        duration="7 дней",
        best_time="Май-октябрь",
    )


@pytest.mark.asyncio
async def test_get_recommendation_success(
    llm_service: LLMTravelRecommendationService,
    mock_openrouter_client: MagicMock,
    mock_formatter: MagicMock,
    sample_travel_request: TravelRequest,
    sample_recommendation: TravelRecommendation,
) -> None:
    """Тест успешного получения рекомендации"""
    # Настраиваем моки
    mock_messages = [
        OpenRouterMessage(role="system", content="System prompt"),
        OpenRouterMessage(role="user", content="User request"),
    ]
    mock_formatter.format_travel_request_prompt.return_value = mock_messages
    mock_openrouter_client.generate_completion.return_value = "LLM response"
    mock_formatter.parse_llm_response.return_value = sample_recommendation

    # Выполняем тест
    result = await llm_service.get_recommendation(sample_travel_request)

    # Проверяем результат
    assert result == sample_recommendation
    mock_formatter.format_travel_request_prompt.assert_called_once_with(sample_travel_request)
    mock_openrouter_client.generate_completion.assert_called_once_with(
        messages=mock_messages,
        max_tokens=2000,
        temperature=0.7,
    )
    mock_formatter.parse_llm_response.assert_called_once_with("LLM response")


@pytest.mark.asyncio
async def test_get_recommendation_external_service_error(
    llm_service: LLMTravelRecommendationService,
    mock_openrouter_client: MagicMock,
    mock_formatter: MagicMock,
    sample_travel_request: TravelRequest,
) -> None:
    """Тест обработки ошибки внешнего сервиса"""
    # Настраиваем моки
    mock_messages = [OpenRouterMessage(role="user", content="Test")]
    mock_formatter.format_travel_request_prompt.return_value = mock_messages
    mock_openrouter_client.generate_completion.side_effect = ExternalServiceError("API Error")

    # Выполняем тест и проверяем исключение
    with pytest.raises(ExternalServiceError, match="API Error"):
        await llm_service.get_recommendation(sample_travel_request)


@pytest.mark.asyncio
async def test_get_recommendation_unexpected_error(
    llm_service: LLMTravelRecommendationService,
    mock_openrouter_client: MagicMock,
    mock_formatter: MagicMock,
    sample_travel_request: TravelRequest,
) -> None:
    """Тест обработки неожиданной ошибки"""
    # Настраиваем моки
    mock_messages = [OpenRouterMessage(role="user", content="Test")]
    mock_formatter.format_travel_request_prompt.return_value = mock_messages
    mock_openrouter_client.generate_completion.side_effect = ValueError("Unexpected error")

    # Выполняем тест и проверяем исключение
    with pytest.raises(ExternalServiceError, match="Ошибка сервиса рекомендаций"):
        await llm_service.get_recommendation(sample_travel_request)


@pytest.mark.asyncio
async def test_get_alternative_recommendation_success(
    llm_service: LLMTravelRecommendationService,
    mock_openrouter_client: MagicMock,
    mock_formatter: MagicMock,
    sample_travel_request: TravelRequest,
    sample_recommendation: TravelRecommendation,
) -> None:
    """Тест успешного получения альтернативной рекомендации"""
    exclude_destinations = ["Сочи", "Крым"]

    # Настраиваем моки
    mock_messages = [OpenRouterMessage(role="user", content="User request")]
    mock_formatter.format_travel_request_prompt.return_value = mock_messages
    mock_openrouter_client.generate_completion.return_value = "Alternative response"
    mock_formatter.parse_llm_response.return_value = sample_recommendation

    # Выполняем тест
    result = await llm_service.get_alternative_recommendation(
        sample_travel_request, exclude_destinations
    )

    # Проверяем результат
    assert result == sample_recommendation

    # Проверяем, что в сообщения добавлена информация об исключениях
    call_args = mock_openrouter_client.generate_completion.call_args
    assert call_args[1]["temperature"] == 0.8  # Больше креативности для альтернатив

    # Проверяем, что последнее сообщение содержит информацию об исключениях
    messages_used = call_args[1]["messages"]
    last_message_content = messages_used[-1].content
    assert "Сочи" in last_message_content
    assert "Крым" in last_message_content


@pytest.mark.asyncio
async def test_get_alternative_recommendation_no_exclusions(
    llm_service: LLMTravelRecommendationService,
    mock_openrouter_client: MagicMock,
    mock_formatter: MagicMock,
    sample_travel_request: TravelRequest,
    sample_recommendation: TravelRecommendation,
) -> None:
    """Тест получения альтернативной рекомендации без исключений"""
    # Настраиваем моки
    mock_messages = [OpenRouterMessage(role="user", content="User request")]
    mock_formatter.format_travel_request_prompt.return_value = mock_messages
    mock_openrouter_client.generate_completion.return_value = "Alternative response"
    mock_formatter.parse_llm_response.return_value = sample_recommendation

    # Выполняем тест без исключений
    result = await llm_service.get_alternative_recommendation(sample_travel_request, [])

    # Проверяем результат
    assert result == sample_recommendation

    # Проверяем, что исключения не добавлялись
    call_args = mock_openrouter_client.generate_completion.call_args
    messages_used = call_args[1]["messages"]
    assert len(messages_used) == len(mock_messages)


@pytest.mark.asyncio
async def test_check_service_health_success(
    llm_service: LLMTravelRecommendationService, mock_openrouter_client: MagicMock
) -> None:
    """Тест успешной проверки здоровья сервиса"""
    mock_openrouter_client.check_health.return_value = True

    result = await llm_service.check_service_health()

    assert result is True
    mock_openrouter_client.check_health.assert_called_once()


@pytest.mark.asyncio
async def test_check_service_health_failure(
    llm_service: LLMTravelRecommendationService, mock_openrouter_client: MagicMock
) -> None:
    """Тест неудачной проверки здоровья сервиса"""
    mock_openrouter_client.check_health.side_effect = Exception("Health check failed")

    result = await llm_service.check_service_health()

    assert result is False


def test_get_fallback_recommendation_family(
    llm_service: LLMTravelRecommendationService, sample_travel_request: TravelRequest
) -> None:
    """Тест получения fallback сообщения для семейной категории"""
    result = llm_service.get_fallback_recommendation(sample_travel_request)

    assert "Сервис временно недоступен" in result.destination
    assert "семейного путешествия" in result.description
    assert "персонализированную" in result.description
    assert len(result.highlights) > 0
    assert "извинения" in result.practical_info.lower()
    assert result.estimated_cost == "Недоступно"
    assert result.duration == "Недоступно"


def test_get_fallback_recommendation_pets(llm_service: LLMTravelRecommendationService) -> None:
    """Тест получения fallback сообщения для путешествий с питомцами"""
    request = TravelRequest(user_id=456, category=TravelCategory.PETS, answers={})

    result = llm_service.get_fallback_recommendation(request)

    assert "Сервис временно недоступен" in result.destination
    assert "путешествия с питомцами" in result.description
    assert "персонализированную" in result.description


def test_get_fallback_recommendation_photo(llm_service: LLMTravelRecommendationService) -> None:
    """Тест получения fallback сообщения для фото-путешествий"""
    request = TravelRequest(user_id=789, category=TravelCategory.PHOTO, answers={})

    result = llm_service.get_fallback_recommendation(request)

    assert "Сервис временно недоступен" in result.destination
    assert "фотографического путешествия" in result.description
    assert "персонализированную" in result.description


def test_get_fallback_recommendation_budget(llm_service: LLMTravelRecommendationService) -> None:
    """Тест получения fallback сообщения для бюджетных путешествий"""
    request = TravelRequest(user_id=101, category=TravelCategory.BUDGET, answers={})

    result = llm_service.get_fallback_recommendation(request)

    assert "Сервис временно недоступен" in result.destination
    assert "бюджетного путешествия" in result.description
    assert "персонализированную" in result.description


def test_get_fallback_recommendation_active(llm_service: LLMTravelRecommendationService) -> None:
    """Тест получения fallback сообщения для активного отдыха"""
    request = TravelRequest(user_id=202, category=TravelCategory.ACTIVE, answers={})

    result = llm_service.get_fallback_recommendation(request)

    assert "Сервис временно недоступен" in result.destination
    assert "активного отдыха" in result.description
    assert "персонализированную" in result.description


def test_get_fallback_recommendation_unknown_category(
    llm_service: LLMTravelRecommendationService,
) -> None:
    """Тест получения fallback сообщения для неизвестной категории"""
    # Создаем запрос с неизвестной категорией
    request = TravelRequest(user_id=303, category=TravelCategory.FAMILY, answers={})

    # Подменяем значение категории на неизвестное
    request.category = MagicMock()
    request.category.value = "unknown"

    result = llm_service.get_fallback_recommendation(request)

    # Должно вернуться общее сообщение о недоступности
    assert "Сервис временно недоступен" in result.destination
    assert "путешествия" in result.description  # fallback для неизвестной категории
