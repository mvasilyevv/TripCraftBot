"""Точка входа для TraveleBot"""

import asyncio
import logging
import sys
from typing import cast

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.redis import RedisStorage
from redis.asyncio import Redis

from config import TELEGRAM_BOT_TOKEN, LOG_LEVEL, DEBUG, FSM_TTL, get_redis_url


def setup_logging() -> None:
    logging.basicConfig(
        level=getattr(logging, LOG_LEVEL),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )
    logging.getLogger("aiogram").setLevel(logging.WARNING)
    logging.getLogger("aiohttp").setLevel(logging.WARNING)
    logging.getLogger("redis").setLevel(logging.WARNING)


async def create_bot() -> Bot:
    """Создает экземпляр бота."""
    return Bot(token=cast(str, TELEGRAM_BOT_TOKEN))


async def create_dispatcher() -> Dispatcher:
    redis = Redis.from_url(
        get_redis_url(), encoding="utf-8", decode_responses=True
    )
    storage = RedisStorage(redis=redis, state_ttl=FSM_TTL)
    return Dispatcher(storage=storage)


async def register_handlers(dp: Dispatcher) -> None:
    pass


async def on_startup(bot: Bot) -> None:
    logger = logging.getLogger(__name__)
    logger.info("Бот запускается...")
    bot_info = await bot.get_me()
    logger.info("Бот @%s успешно запущен", bot_info.username)
    if DEBUG:
        logger.info("Режим разработки активен")


async def on_shutdown(bot: Bot) -> None:
    logger = logging.getLogger(__name__)
    logger.info("Бот останавливается...")
    await bot.session.close()
    logger.info("Бот успешно остановлен")


async def main() -> None:
    setup_logging()
    logger = logging.getLogger(__name__)

    try:
        bot = await create_bot()
        dp = await create_dispatcher()
        await register_handlers(dp)
        dp.startup.register(on_startup)
        dp.shutdown.register(on_shutdown)
        logger.info("Запуск polling...")
        await dp.start_polling(
            bot, allowed_updates=["message", "callback_query"]
        )
    except Exception as e:
        logger.error("Критическая ошибка при запуске бота: %s", e)
        sys.exit(1)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.getLogger(__name__).info("Получен сигнал остановки")
    except Exception as e:
        logging.getLogger(__name__).error("Неожиданная ошибка: %s", e)
        sys.exit(1)
