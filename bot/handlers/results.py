"""Обработчики результатов поиска"""

import logging

from aiogram import Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot.keyboards.inline import get_result_actions_keyboard, get_new_search_keyboard

logger = logging.getLogger(__name__)

router = Router()


async def show_travel_recommendation(
    callback: CallbackQuery, state: FSMContext
) -> None:
    """Показывает рекомендацию путешествия пользователю"""
    logger.info("Показ рекомендации пользователю %d", callback.from_user.id)

    # Получаем данные из состояния
    data = await state.get_data()
    category = data.get("category", "family")  # Значение по умолчанию
    answers = data.get("answers", {})

    # Пока что показываем заглушку (в будущем здесь будет вызов use case)
    recommendation_text = _create_mock_recommendation(category, answers)

    # Отправляем рекомендацию с кнопками действий
    if callback.message and isinstance(callback.message, Message):
        await callback.message.edit_text(
            recommendation_text,
            reply_markup=get_result_actions_keyboard(),
            parse_mode="Markdown"
        )


@router.callback_query(lambda c: c.data == "action:retry")
async def callback_retry_search(callback: CallbackQuery, state: FSMContext) -> None:
    """Обработчик кнопки 'Другой вариант'"""
    logger.info("Пользователь %d запросил другой вариант", callback.from_user.id)

    # Получаем данные из состояния
    data = await state.get_data()
    category = data.get("category", "family")  # Значение по умолчанию
    answers = data.get("answers", {})

    # Показываем сообщение о поиске альтернативы
    if callback.message and isinstance(callback.message, Message):
        await callback.message.edit_text(
            "🔄 Ищу альтернативный вариант...\n\n"
            "Это может занять несколько секунд."
        )

    # Пока что показываем другую заглушку
    alternative_recommendation = _create_mock_alternative_recommendation(
        category, answers
    )

    # Отправляем альтернативную рекомендацию
    if callback.message and isinstance(callback.message, Message):
        await callback.message.edit_text(
            alternative_recommendation,
            reply_markup=get_result_actions_keyboard(),
            parse_mode="Markdown"
        )

    await callback.answer("Найден альтернативный вариант!")


@router.callback_query(lambda c: c.data == "action:share")
async def callback_share_result(callback: CallbackQuery, _: FSMContext) -> None:
    """Обработчик кнопки 'Поделиться'"""
    logger.info("Пользователь %d хочет поделиться результатом", callback.from_user.id)

    # Получаем текущий текст сообщения
    current_text = ""
    if (callback.message and
        isinstance(callback.message, Message) and
        callback.message.text):
        current_text = callback.message.text
    elif (callback.message and
          isinstance(callback.message, Message) and
          callback.message.caption):
        current_text = callback.message.caption

    # Добавляем информацию о боте в конец
    share_text = f"{current_text}\n\n🤖 Найдено с помощью @TraveleBot"

    # Отправляем новое сообщение для пересылки
    if callback.message and isinstance(callback.message, Message):
        await callback.message.answer(
            share_text,
            reply_markup=get_new_search_keyboard(),
            parse_mode="Markdown"
        )

    await callback.answer("Сообщение готово для пересылки!")


def _create_mock_recommendation(category: str, _: dict) -> str:
    """Создает заглушку рекомендации на основе категории и ответов"""

    # Базовые рекомендации для каждой категории
    mock_recommendations = {
        "family": {
            "destination": "Анталья, Турция",
            "description": "Идеальное место для семейного отдыха с детьми",
            "highlights": [
                "Аквапарки и детские развлечения",
                "Чистые пляжи с пологим входом",
                "Отели с детской анимацией"
            ],
            "practical_info": "Виза не нужна, прямые рейсы из Москвы 3.5 часа",
            "cost": "$800-1200 на семью",
            "duration": "7-10 дней"
        },
        "pets": {
            "destination": "Сочи, Россия",
            "description": (
                "Pet-friendly курорт с множеством отелей, принимающих животных"
            ),
            "highlights": [
                "Специальные пляжи для собак",
                "Ветеринарные клиники",
                "Парки для прогулок с питомцами"
            ],
            "practical_info": "Документы на животное, переноска для транспорта",
            "cost": "$400-600",
            "duration": "5-7 дней"
        },
        "photo": {
            "destination": "Каппадокия, Турция",
            "description": "Уникальные пейзажи для незабываемых фотографий",
            "highlights": [
                "Полеты на воздушных шарах",
                "Подземные города",
                "Сказочные дымоходы"
            ],
            "practical_info": "Лучшее время: апрель-май, сентябрь-октябрь",
            "cost": "$600-900",
            "duration": "4-5 дней"
        },
        "budget": {
            "destination": "Грузия (Тбилиси + Батуми)",
            "description": "Максимум впечатлений при минимальном бюджете",
            "highlights": [
                "Бесплатные экскурсии по старому городу",
                "Недорогая и вкусная еда",
                "Доступное жилье"
            ],
            "practical_info": "Виза не нужна, можно добраться автобусом",
            "cost": "$200-400",
            "duration": "5-7 дней"
        },
        "active": {
            "destination": "Красная Поляна, Сочи",
            "description": "Горные приключения и активный отдых",
            "highlights": [
                "Треккинг в горах",
                "Канатные дороги",
                "Экстремальные виды спорта"
            ],
            "practical_info": "Сезон: май-октябрь, нужна спортивная экипировка",
            "cost": "$500-800",
            "duration": "4-6 дней"
        }
    }

    rec = mock_recommendations.get(category, mock_recommendations["family"])

    text = f"🌍 **{rec['destination']}**\n\n"
    text += f"{rec['description']}\n\n"
    text += "✨ **Основные достопримечательности:**\n"
    for highlight in rec['highlights']:
        text += f"• {highlight}\n"
    text += f"\n📋 **Практическая информация:**\n{rec['practical_info']}\n\n"
    text += f"💰 **Примерная стоимость:** {rec['cost']}\n"
    text += f"⏱ **Рекомендуемая продолжительность:** {rec['duration']}"

    return text


def _create_mock_alternative_recommendation(category: str, _: dict) -> str:
    """Создает альтернативную заглушку рекомендации"""

    # Альтернативные рекомендации
    alternative_recommendations = {
        "family": "Кипр (Айя-Напа)",
        "pets": "Крым (Ялта)",
        "photo": "Исландия (Рейкьявик)",
        "budget": "Беларусь (Минск)",
        "active": "Алтай (Белокуриха)"
    }

    destination = alternative_recommendations.get(
        category, "Альтернативное направление"
    )

    text = f"🌍 **{destination}**\n\n"
    text += "Альтернативный вариант, который также может вам подойти!\n\n"
    text += "✨ **Почему стоит рассмотреть:**\n"
    text += "• Другая атмосфера и культура\n"
    text += "• Уникальные достопримечательности\n"
    text += "• Отличное соотношение цена-качество\n\n"
    text += "📋 **Практическая информация:** Подробности по запросу\n\n"
    text += "💰 **Примерная стоимость:** Уточняется\n"
    text += "⏱ **Рекомендуемая продолжительность:** 5-7 дней"

    return text
