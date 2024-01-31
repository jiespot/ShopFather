from aiogram import executor
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from handlers import dp
from utils.utils import update_prices, check_tokens, update_config, start_slave_bot
from data.loader import sqlite, cursor
import logging


async def start_bots(dp):
    bot_req = cursor.execute('SELECT id FROM bots WHERE stopped = 0').fetchall()
    for x in bot_req:
        update_config(x[0])
        await start_slave_bot(x[0])

if __name__ == "__main__":
    # Подключение sqlite
    scheduler = AsyncIOScheduler(timezone="Europe/Moscow")
    scheduler.add_job(update_prices, "interval", seconds=31, max_instances=2)
    scheduler.add_job(check_tokens, "interval", seconds=27, max_instances=2)
    try:
        scheduler.start()
        while True:
            time.sleep(2)
    except:
        print("SCHEDULER FAILED...\n")
    executor.start_polling(dp, on_startup=start_bots, skip_updates=True)
    sqlite.close()
    logging.info("Соединение с SQLite закрыто")
