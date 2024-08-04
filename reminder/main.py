import asyncio
import aioschedule as schedule
from databaseconnection import DataBaseWorker
from telethon import TelegramClient
from dotenv import load_dotenv
import os
from os.path import join, dirname

dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)

BOT_TOKEN = os.getenv('BOT_TOKEN')
API_ID = int(os.getenv('API_ID'))
API_HASH = os.getenv('API_HASH')
bot = TelegramClient('bot', API_ID, API_HASH)

db = DataBaseWorker(
    host=os.getenv('db_host'),
    port=os.getenv('db_port'),
    user=os.getenv('db_user'),
    password=os.getenv('db_pass'),
    database=os.getenv('db_base')
)


async def send_notes():
    notes = await db.get_notes_to_send()
    for text, telegram_id in notes:
        await bot.send_message(entity=await bot.get_entity(telegram_id), message=f'Через 10 минут:\n\n{text}')


async def setup():
    schedule.every(1).minutes.do(send_notes)
    print('ready')
    while True:
        await schedule.run_pending()
        await asyncio.sleep(1)


async def main():
    await db.connect()
    await bot.start(bot_token=BOT_TOKEN)
    await setup()

asyncio.run(main())
