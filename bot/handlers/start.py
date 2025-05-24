"""Обработчики стартовых команд"""

import logging
from aiogram import Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot.keyboards.inline import get_main_menu_keyboard

logger = logging.getLogger(__name__)

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext) -> None:
    """Обработчик команды /start"""
    user_id = message.from_user.id if message.from_user else 0
    logger.info("Пользователь %d запустил бота", user_id)

    # Очищаем состояние пользователя
    await state.clear()

    # Отправляем главное меню без приветствия
    await message.answer(
        "Выберите тип путешествия:",
        reply_markup=get_main_menu_keyboard()
    )


@router.message(Command("menu"))
async def cmd_menu(message: Message, state: FSMContext) -> None:
    """Обработчик команды /menu"""
    user_id = message.from_user.id if message.from_user else 0
    logger.info("Пользователь %d запросил главное меню", user_id)

    # Очищаем состояние пользователя
    await state.clear()

    # Отправляем главное меню
    await message.answer(
        "Выберите тип путешествия:",
        reply_markup=get_main_menu_keyboard()
    )


@router.callback_query(lambda c: c.data == "action:new_search")
async def callback_new_search(callback: CallbackQuery, state: FSMContext) -> None:
    """Обработчик кнопки 'Новый поиск'"""
    logger.info("Пользователь %d начал новый поиск", callback.from_user.id)

    # Очищаем состояние пользователя
    await state.clear()

    # Отправляем главное меню
    if callback.message and isinstance(callback.message, Message):
        await callback.message.edit_text(
            "Выберите тип путешествия:",
            reply_markup=get_main_menu_keyboard()
        )

    await callback.answer()


@router.callback_query(lambda c: c.data == "action:menu")
async def callback_main_menu(callback: CallbackQuery, state: FSMContext) -> None:
    """Обработчик кнопки 'Главное меню'"""
    logger.info("Пользователь %d вернулся в главное меню", callback.from_user.id)

    # Очищаем состояние пользователя
    await state.clear()

    # Отправляем главное меню
    if callback.message and isinstance(callback.message, Message):
        await callback.message.edit_text(
            "Выберите тип путешествия:",
            reply_markup=get_main_menu_keyboard()
        )

    await callback.answer()
