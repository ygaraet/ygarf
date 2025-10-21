from asyncio import run
import logging

from aiogram import Bot, Dispatcher

from data.config import TOKEN
from bot.handlers import user_handlers, callback_handlers

logging.basicConfig(level=logging.INFO)

bot = Bot(token=TOKEN)
dp = Dispatcher()

async def main():
    dp.include_router(user_handlers.router)
    dp.include_router(callback_handlers.router)
    
    me = await bot.get_me()
    logging.info(f"Bot started: @{me.username} (id={me.id})")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    run(main())