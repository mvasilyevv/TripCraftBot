"""Базовые классы для обработчиков Telegram событий"""

import logging
from abc import ABC, abstractmethod
from typing import Any, Optional, Union

from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot.domain.models import TravelPlannerError

logger = logging.getLogger(__name__)


class BaseHandler(ABC):
    """Базовый класс для обработчиков событий"""

    def __init__(self) -> None:
        self.logger = logging.getLogger(self.__class__.__name__)

    async def safe_execute(
        self, handler_func: Any, event: Union[Message, CallbackQuery], *args: Any, **kwargs: Any
    ) -> Any:
        """Безопасно выполняет обработчик с обработкой ошибок"""
        try:
            return await handler_func(event, *args, **kwargs)
        except TravelPlannerError as e:
            self.logger.warning("Бизнес-ошибка в обработчике: %s", str(e))
            await self._handle_business_error(event, e)
        except Exception as e:
            self.logger.error("Неожиданная ошибка в обработчике: %s", str(e), exc_info=True)
            await self._handle_unexpected_error(event, e)

    async def _handle_business_error(
        self, event: Union[Message, CallbackQuery], error: TravelPlannerError
    ) -> None:
        """Обрабатывает бизнес-ошибки"""
        error_message = "Произошла ошибка при обработке запроса. Попробуйте еще раз."

        if isinstance(event, Message):
            await event.answer(error_message)
        elif isinstance(event, CallbackQuery):
            await event.answer(error_message, show_alert=True)

    async def _handle_unexpected_error(
        self, event: Union[Message, CallbackQuery], error: Exception
    ) -> None:
        """Обрабатывает неожиданные ошибки"""
        error_message = "Произошла техническая ошибка. Мы уже работаем над ее устранением."

        if isinstance(event, Message):
            await event.answer(error_message)
        elif isinstance(event, CallbackQuery):
            await event.answer(error_message, show_alert=True)


class BaseMessageHandler(BaseHandler):
    """Базовый класс для обработчиков сообщений"""

    @abstractmethod
    async def handle(self, message: Message, state: FSMContext) -> None:
        """Обрабатывает входящее сообщение"""
        pass

    async def __call__(self, message: Message, state: FSMContext) -> None:
        """Точка входа для обработчика сообщений"""
        self.logger.info(
            "Обработка сообщения от пользователя %d: %s",
            message.from_user.id if message.from_user else 0,
            message.text[:50] if message.text else "без текста",
        )
        await self.safe_execute(self.handle, message, state)


class BaseCallbackHandler(BaseHandler):
    """Базовый класс для обработчиков callback запросов"""

    @abstractmethod
    async def handle(self, callback: CallbackQuery, state: FSMContext) -> None:
        """Обрабатывает callback запрос"""
        pass

    async def __call__(self, callback: CallbackQuery, state: FSMContext) -> None:
        """Точка входа для обработчика callback запросов"""
        self.logger.info(
            "Обработка callback от пользователя %d: %s",
            callback.from_user.id if callback.from_user else 0,
            callback.data,
        )
        await self.safe_execute(self.handle, callback, state)


class BaseStatefulHandler(BaseHandler):
    """Базовый класс для обработчиков с состоянием"""

    async def get_user_data(self, state: FSMContext, key: str, default: Any = None) -> Any:
        """Получает данные пользователя из состояния"""
        data = await state.get_data()
        return data.get(key, default)

    async def set_user_data(self, state: FSMContext, key: str, value: Any) -> None:
        """Сохраняет данные пользователя в состояние"""
        await state.update_data({key: value})

    async def clear_user_data(self, state: FSMContext, keys: Optional[list[str]] = None) -> None:
        """Очищает данные пользователя"""
        if keys:
            data = await state.get_data()
            for key in keys:
                data.pop(key, None)
            await state.set_data(data)
        else:
            await state.clear()

    async def get_progress_info(self, current_step: int, total_steps: int) -> str:
        """Формирует информацию о прогрессе"""
        return f"Вопрос {current_step} из {total_steps}"


class HandlerRegistry:
    """Реестр обработчиков для регистрации в диспетчере"""

    def __init__(self) -> None:
        self._message_handlers: list[tuple] = []
        self._callback_handlers: list[tuple] = []

    def register_message_handler(
        self, handler: BaseMessageHandler, *filters: Any, **kwargs: Any
    ) -> None:
        """Регистрирует обработчик сообщений"""
        self._message_handlers.append((handler, filters, kwargs))

    def register_callback_handler(
        self, handler: BaseCallbackHandler, *filters: Any, **kwargs: Any
    ) -> None:
        """Регистрирует обработчик callback запросов"""
        self._callback_handlers.append((handler, filters, kwargs))

    def get_message_handlers(self) -> list[tuple]:
        """Возвращает зарегистрированные обработчики сообщений"""
        return self._message_handlers.copy()

    def get_callback_handlers(self) -> list[tuple]:
        """Возвращает зарегистрированные обработчики callback запросов"""
        return self._callback_handlers.copy()
