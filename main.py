from aiogram import Dispatcher, Bot
import asyncio

import os
import logging

from dotenv import load_dotenv
from app.routers import router, crypto_parse
from app.database.models import async_main
import app.database.requests as rq

load_dotenv()

TOKEN = os.environ['TOKEN']

bot = Bot(token=TOKEN)
dp = Dispatcher()

async def auto_expire_checker():
    while True:
        try:
            expired_count = await rq.expire_subscription()
            if expired_count > 0:
                logging.info(f"Сброшено просроченных Premium-подписок: {expired_count}")
        except Exception as e:
            logging.error(f"Ошибка при проверке просроченных подписок: {e}")
        
        await asyncio.sleep(3600)
async def main():
    await async_main()
    
    dp.include_router(router)

    asyncio.create_task(crypto_parse(bot))
    asyncio.create_task(auto_expire_checker())

    await dp.start_polling(bot)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Bot stopped!")
