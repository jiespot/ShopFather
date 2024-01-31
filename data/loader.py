import json
import logging

from aiogram import Bot, Dispatcher
from aiogram.bot.api import TelegramAPIServer
from aiogram.contrib.fsm_storage.memory import MemoryStorage

from utils.api_session import AsyncSession
from utils.db_tools import sqlite_init

with open('config_master.json', 'r') as f:
    config = json.load(f)

with open('locale.json', 'r', encoding='utf-8') as f:
    locale = json.load(f)

bot_token = config["bot"]["token"]
local_server = config["bot"]["tg_server"]
admin_ids = config["bot"]["admin_ids"]
super_admin_id = admin_ids
logs_chat = config["bot"]["logs_chat"]
sub_chat_ids = config["bot"]["sub_chat_ids"]

logging.basicConfig(level=logging.INFO, format=f"%(asctime)s [%(levelname)-5.5s] [MASTER] %(message)s",
                    handlers=[logging.StreamHandler()])
logging.getLogger('apscheduler.executors.default').setLevel(logging.WARNING)
logging.getLogger('apscheduler.scheduler').propagate = False

price_sql = sqlite_init('prices.db')
sqlite = sqlite_init('sqlite.db')
cursor = sqlite.cursor()

aSession = AsyncSession()

bot = Bot(token=bot_token, server=TelegramAPIServer.from_base(local_server), parse_mode='html')
dp = Dispatcher(bot, storage=MemoryStorage())
