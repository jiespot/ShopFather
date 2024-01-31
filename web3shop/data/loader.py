import logging
import sqlite3

from aiogram import Bot, Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from data.config import bot_token, bot_id, local_server, chain_address, super_admin_id
from misc.api_session import AsyncSession
from web3 import Web3, HTTPProvider
from web3.middleware import geth_poa_middleware

logging.basicConfig(level=logging.INFO, format=f"%(asctime)s [%(levelname)-5.5s] [{bot_id}] %(message)s",
                    handlers=[logging.StreamHandler()])
logging.getLogger('apscheduler.executors.default').setLevel(logging.WARNING)
logging.getLogger('apscheduler.scheduler').propagate = False

w3 = Web3(HTTPProvider(chain_address), middlewares=[geth_poa_middleware])
bot = Bot(token=bot_token, server=local_server, parse_mode='html')
dp = Dispatcher(bot, storage=MemoryStorage())

scheduler = AsyncIOScheduler(timezone="Europe/Moscow")

aSession = AsyncSession()

sqlite = sqlite3.connect(f'shops/{bot_id}.db')
cursor = sqlite.cursor()

price_sql = sqlite3.connect(f'../prices.db')
