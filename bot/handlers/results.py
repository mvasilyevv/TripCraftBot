"""Обработчики результатов поиска"""

import logging

from aiogram import Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot.domain.models import ExternalServiceError, InvalidTravelRequestError
from bot.infrastructure.service_factory import get_service_factory
from bot.keyboards.inline import get_new_search_keyboard, get_result_actions_keyboard

logger = logging.getLogger(__name__)

router = Router()


async def show_travel_recommendation(callback: CallbackQuery, _: FSMContext) -> None:
    """Показывает рекомендацию путешествия пользователю"""
    logger.info("Показ рекомендации пользователю %d", callback.from_user.id)

    if not callback.from_user:
        logger.error("Отсутствует информация о пользователе в callback")
        return

    user_id = callback.from_user.id

    try:
        # Получаем use case для рекомендаций
        service_factory = get_service_factory()
        recommendation_use_case = service_factory.get_travel_recommendation_use_case()

        # Получаем рекомендацию
        recommendation = await recommendation_use_case.execute(user_id)

        # Форматируем рекомендацию для Telegram
        recommendation_text = recommendation.format_for_telegram()

        # Отправляем рекомендацию с кнопками действий
        if callback.message and isinstance(callback.message, Message):
            await callback.message.edit_text(
                recommendation_text,
                reply_markup=get_result_actions_keyboard(),
                parse_mode="Markdown",
            )

    except InvalidTravelRequestError:
        logger.error("Запрос пользователя %d не найден", user_id)
        error_text = "❌ Не удалось найти ваш запрос.\n\nПожалуйста, начните новый поиск."
        if callback.message and isinstance(callback.message, Message):
            await callback.message.edit_text(error_text, reply_markup=get_new_search_keyboard())

    except ExternalServiceError as e:
        logger.error("Ошибка внешнего сервиса для пользователя %d: %s", user_id, str(e))

        # Пытаемся получить fallback рекомендацию
        try:
            service_factory = get_service_factory()
            recommendation_service = service_factory.get_recommendation_service()
            state_repository = service_factory.get_state_repository()

            # Получаем запрос пользователя для fallback
            request = await state_repository.get_travel_request(user_id)
            if request:
                fallback_recommendation = recommendation_service.get_fallback_recommendation(
                    request
                )
                recommendation_text = fallback_recommendation.format_for_telegram()
                recommendation_text += "\n\n⚠️ *Рекомендация сгенерирована в автономном режиме*"

                if callback.message and isinstance(callback.message, Message):
                    await callback.message.edit_text(
                        recommendation_text,
                        reply_markup=get_result_actions_keyboard(),
                        parse_mode="Markdown",
                    )
                return
        except Exception as fallback_error:
            logger.error("Ошибка fallback рекомендации: %s", str(fallback_error))

        # Если fallback тоже не сработал
        error_text = (
            "❌ Временные проблемы с сервисом рекомендаций.\n\n"
            "Попробуйте повторить запрос через несколько минут."
        )
        if callback.message and isinstance(callback.message, Message):
            await callback.message.edit_text(error_text, reply_markup=get_new_search_keyboard())

    except Exception as e:
        logger.error(
            "Неожиданная ошибка при получении рекомендации для пользователя %d: %s", user_id, str(e)
        )
        error_text = (
            "❌ Произошла неожиданная ошибка.\n\nПожалуйста, попробуйте начать новый поиск."
        )
        if callback.message and isinstance(callback.message, Message):
            await callback.message.edit_text(error_text, reply_markup=get_new_search_keyboard())


@router.callback_query(lambda c: c.data == "action:retry")
async def callback_retry_search(callback: CallbackQuery, state: FSMContext) -> None:
    """Обработчик кнопки 'Другой вариант'"""
    logger.info("Пользователь %d запросил другой вариант", callback.from_user.id)

    if not callback.from_user:
        logger.error("Отсутствует информация о пользователе в callback")
        return

    user_id = callback.from_user.id

    # Показываем сообщение о поиске альтернативы
    if callback.message and isinstance(callback.message, Message):
        await callback.message.edit_text(
            "🔄 Ищу альтернативный вариант...\n\nЭто может занять несколько секунд."
        )

    try:
        # Получаем use case для альтернативных рекомендаций
        service_factory = get_service_factory()
        alternative_use_case = service_factory.get_alternative_recommendation_use_case()

        # Получаем данные из состояния для исключений
        data = await state.get_data()
        exclude_destinations = data.get("previous_destinations", [])

        # Получаем альтернативную рекомендацию
        recommendation = await alternative_use_case.execute(user_id, exclude_destinations)

        # Сохраняем новое направление в исключения
        if "previous_destinations" not in data:
            data["previous_destinations"] = []
        data["previous_destinations"].append(recommendation.destination)
        await state.update_data(previous_destinations=data["previous_destinations"])

        # Форматируем рекомендацию для Telegram
        recommendation_text = recommendation.format_for_telegram()

        # Отправляем альтернативную рекомендацию
        if callback.message and isinstance(callback.message, Message):
            await callback.message.edit_text(
                recommendation_text,
                reply_markup=get_result_actions_keyboard(),
                parse_mode="Markdown",
            )

        await callback.answer("Найден альтернативный вариант!")

    except InvalidTravelRequestError:
        logger.error("Запрос пользователя %d не найден для альтернативы", user_id)
        error_text = "❌ Не удалось найти ваш запрос.\n\nПожалуйста, начните новый поиск."
        if callback.message and isinstance(callback.message, Message):
            await callback.message.edit_text(error_text, reply_markup=get_new_search_keyboard())

    except ExternalServiceError as e:
        logger.error(
            "Ошибка сервиса при поиске альтернативы для пользователя %d: %s", user_id, str(e)
        )

        # Пытаемся получить fallback рекомендацию
        try:
            service_factory = get_service_factory()
            recommendation_service = service_factory.get_recommendation_service()
            state_repository = service_factory.get_state_repository()

            request = await state_repository.get_travel_request(user_id)
            if request:
                fallback_recommendation = recommendation_service.get_fallback_recommendation(
                    request
                )
                recommendation_text = fallback_recommendation.format_for_telegram()
                recommendation_text += "\n\n⚠️ *Альтернатива сгенерирована в автономном режиме*"

                if callback.message and isinstance(callback.message, Message):
                    await callback.message.edit_text(
                        recommendation_text,
                        reply_markup=get_result_actions_keyboard(),
                        parse_mode="Markdown",
                    )
                await callback.answer("Найден альтернативный вариант!")
                return
        except Exception as fallback_error:
            logger.error("Ошибка fallback альтернативы: %s", str(fallback_error))

        error_text = (
            "❌ Временные проблемы с поиском альтернатив.\n\n"
            "Попробуйте повторить запрос через несколько минут."
        )
        if callback.message and isinstance(callback.message, Message):
            await callback.message.edit_text(error_text, reply_markup=get_new_search_keyboard())

    except Exception as e:
        logger.error(
            "Неожиданная ошибка при поиске альтернативы для пользователя %d: %s", user_id, str(e)
        )
        error_text = (
            "❌ Произошла неожиданная ошибка.\n\nПожалуйста, попробуйте начать новый поиск."
        )
        if callback.message and isinstance(callback.message, Message):
            await callback.message.edit_text(error_text, reply_markup=get_new_search_keyboard())


@router.callback_query(lambda c: c.data == "action:share")
async def callback_share_result(callback: CallbackQuery, _: FSMContext) -> None:
    """Обработчик кнопки 'Поделиться'"""
    logger.info("Пользователь %d хочет поделиться результатом", callback.from_user.id)

    # Получаем текущий текст сообщения
    current_text = ""
    if callback.message and isinstance(callback.message, Message) and callback.message.text:
        current_text = callback.message.text
    elif callback.message and isinstance(callback.message, Message) and callback.message.caption:
        current_text = callback.message.caption

    # Добавляем информацию о боте в конец
    share_text = f"{current_text}\n\n🤖 Найдено с помощью @TripCraftBot"

    # Отправляем новое сообщение для пересылки
    if callback.message and isinstance(callback.message, Message):
        await callback.message.answer(
            share_text, reply_markup=get_new_search_keyboard(), parse_mode="Markdown"
        )

    await callback.answer("Сообщение готово для пересылки!")
