import json
from sys import argv

from aiogram.bot.api import TelegramAPIServer

bot_id = argv[1]

with open('shops/config_global.json', 'r') as f:
    config_global = json.load(f)
local_server = TelegramAPIServer.from_base(config_global["bot"]["tg_server"])
chain_address = config_global["crypto"]["chain_address"]
gas_price = config_global["crypto"]["gas_price"]
minimal_amount = config_global["crypto"]["minimal_amount"]
super_admin_id = config_global["crypto"]["super_admin_id"]
admin_ids_global = config_global["bot"]["admin_ids"]

with open(f"shops/{super_admin_id}.json", 'r', encoding='utf-8') as f:
    config_user = json.load(f)
withdraw_address_admin = config_user["withdraw_address"]


with open(f"shops/{bot_id}.json", 'r', encoding='utf-8') as f:
    config_user = json.load(f)
bot_token = config_user["token"]
currency_code = config_user["currency_code"]
withdraw_address = config_user["withdraw_address"]
ref_percent = config_user["ref_percent"]
hide_ad = config_user["hide_ad"]
lang_list = config_user['langs']
invite_link = config_user['invite_link']
invite_link_id = config_user['invite_link_id']
yookassa_token = config_user['yookassa_token']
qiwi_number = config_user['qiwi_number']
qiwi_by_number = config_user['qiwi_by_number']
qiwi_nickname = config_user['qiwi_nickname']
qiwi_token = config_user['qiwi_token']
qiwi_private_key = config_user['qiwi_private_key']
cryptobot_token = config_user['cryptobot_token']
terms_status = config_user['terms_status']

admin_ids = config_user["admin_ids"] + admin_ids_global

with open('locale.json', 'r', encoding='utf-8') as f:
    locale = json.load(f)

locale['en']['start_message'] = config_user['start_message_en']
locale['ru']['start_message'] = config_user['start_message_ru']
locale['en']['help_message'] = config_user['help_message_en']
locale['ru']['help_message'] = config_user['help_message_ru']
locale['en']['contact_message'] = config_user['contact_message_en']
locale['ru']['contact_message'] = config_user['contact_message_ru']

if hide_ad is False:
    locale['en']['help_message'] += '\n\n<b>Bot created from @Web3Father_BOT.\n Join our <a href="https://t.me/web3father_shop">Group Chat.</a></b>'
    locale['ru']['help_message'] += '\n\n<b>Бот создан из @Web3Father_BOT.\n Присоединяйтесь к нашему <a href="https://t.me/web3father_shop">групповому чату.</a></b>'

locale['en']['button_help'] = config_user['help_button_en']
locale['ru']['button_help'] = config_user['help_button_ru']
locale['en']['button_contact'] = config_user['contact_button_en']
locale['ru']['button_contact'] = config_user['contact_button_ru']
locale['en']['invite'] = config_user['invite_en']
locale['ru']['invite'] = config_user['invite_ru']

locale['en']['terms'] = config_user['terms_en']
locale['ru']['terms'] = config_user['terms_ru']

if len(lang_list) == 1 and lang_list[0] == 'en':
    locale['buttons']['help'] = [config_user['help_button_en']]
    locale['buttons']['contact'] = [config_user['contact_button_en']]
elif len(lang_list) == 1 and lang_list[0] == 'ru':
    locale['buttons']['help'] = [config_user['help_button_ru']]
    locale['buttons']['contact'] = [config_user['contact_button_ru']]
else:
    locale['buttons']['help'] = [config_user['help_button_en'], config_user['help_button_ru']]
    locale['buttons']['contact'] = [config_user['contact_button_en'], config_user['contact_button_ru']]
