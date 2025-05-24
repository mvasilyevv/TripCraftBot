"""Точка входа для TripCraftBot"""

import asyncio
import logging
import os
import sys

import requests
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.redis import RedisStorage
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web
from redis.asyncio import Redis

from bot.handlers import categories, results, start
from config import DEBUG, FSM_TTL, LOG_LEVEL, TELEGRAM_BOT_TOKEN, get_redis_url


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
    return Bot(token=TELEGRAM_BOT_TOKEN)


async def create_dispatcher() -> Dispatcher:
    redis = Redis.from_url(get_redis_url(), encoding="utf-8", decode_responses=True)
    storage = RedisStorage(redis=redis, state_ttl=FSM_TTL)
    return Dispatcher(storage=storage)


async def register_handlers(dp: Dispatcher) -> None:
    """Регистрирует все обработчики событий"""
    dp.include_router(start.router)
    dp.include_router(categories.router)
    dp.include_router(results.router)


def get_webhook_url() -> str | None:
    """Получает webhook URL из файла или ngrok API"""
    # Сначала пытаемся прочитать из файла
    try:
        with open("/tmp/webhook_url", encoding="utf-8") as f:
            url = f.read().strip()
            if url:
                return url
    except FileNotFoundError:
        pass

    # Если файла нет, пытаемся получить из ngrok API
    try:
        response = requests.get("http://tripcraft-ngrok:4040/api/tunnels", timeout=5)
        if response.status_code == 200:
            data = response.json()
            tunnels = data.get("tunnels", [])
            for tunnel in tunnels:
                if tunnel.get("proto") == "https":
                    public_url = tunnel.get("public_url")
                    if public_url:
                        return f"{public_url}/webhook"
    except Exception as e:
        logging.getLogger(__name__).warning("Не удалось получить URL из ngrok API: %s", e)

    return None


async def setup_webhook(bot: Bot) -> str | None:
    """Настраивает webhook для бота"""
    logger = logging.getLogger(__name__)

    # Ждем ngrok контейнер
    logger.info("⏳ Ожидание ngrok контейнера...")
    webhook_url = None

    for attempt in range(30):  # 30 попыток по 2 секунды = 1 минута
        webhook_url = get_webhook_url()
        if webhook_url:
            break

        logger.info("⏳ Попытка %d/30: ожидание ngrok URL...", attempt + 1)
        await asyncio.sleep(2)

    if not webhook_url:
        logger.error("❌ Не удалось получить webhook URL")
        return None

    try:
        # Устанавливаем webhook
        await bot.set_webhook(webhook_url)
        logger.info("✅ Webhook установлен: %s", webhook_url)
        return webhook_url
    except Exception as e:
        logger.error("❌ Ошибка установки webhook: %s", e)
        return None


async def on_startup(bot: Bot) -> None:
    logger = logging.getLogger(__name__)
    logger.info("🤖 Бот запускается...")
    bot_info = await bot.get_me()
    logger.info("✅ Бот @%s успешно запущен", bot_info.username)

    if os.getenv("USE_WEBHOOK", "false").lower() == "true":
        webhook_url = await setup_webhook(bot)
        if not webhook_url:
            logger.error("❌ Не удалось настроить webhook")
            sys.exit(1)

    if DEBUG:
        logger.info("🔧 Режим разработки активен")


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

        # Проверяем режим работы
        use_webhook = os.getenv("USE_WEBHOOK", "false").lower() == "true"

        if use_webhook:
            logger.info("🌐 Запуск в режиме webhook...")

            # Создаем веб-приложение
            app = web.Application()

            # Настраиваем webhook handler
            webhook_requests_handler = SimpleRequestHandler(
                dispatcher=dp,
                bot=bot,
            )
            webhook_requests_handler.register(app, path="/webhook")

            # Добавляем health check endpoint
            async def health_check(_request: web.Request) -> web.Response:
                return web.json_response({"status": "ok", "bot": "TripCraftBot"})

            app.router.add_get("/health", health_check)

            # Настраиваем приложение
            setup_application(app, dp, bot=bot)

            # Запускаем веб-сервер
            host = os.getenv("WEBSERVER_HOST", "0.0.0.0")
            port = int(os.getenv("WEBSERVER_PORT", "8000"))

            logger.info("🚀 Запуск веб-сервера на %s:%d", host, port)

            runner = web.AppRunner(app)
            await runner.setup()
            site = web.TCPSite(runner, host, port)
            await site.start()

            logger.info("✅ Веб-сервер запущен")

            # Ждем завершения
            try:
                await asyncio.Future()  # Бесконечное ожидание
            finally:
                await runner.cleanup()
        else:
            logger.info("🔄 Запуск в режиме polling...")
            await dp.start_polling(bot, allowed_updates=["message", "callback_query"])

    except Exception as e:
        logger.error("❌ Критическая ошибка при запуске бота: %s", e)
        sys.exit(1)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.getLogger(__name__).info("Получен сигнал остановки")
    except Exception as e:
        logging.getLogger(__name__).error("Неожиданная ошибка: %s", e)
        sys.exit(1)
