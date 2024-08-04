import asyncio, nest_asyncio

from aiogram import Bot, Dispatcher, Router
from aiogram.types import Message, CallbackQuery
from aiogram.filters.command import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram import F

from databaseconnection import DataBaseWorker
import messages as mes

import datetime, math, os
from dotenv import load_dotenv
from os.path import join, dirname

dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)

BOT_TOKEN = os.getenv('BOT_TOKEN')

db = DataBaseWorker(
    host=os.getenv('db_host'),
    port=os.getenv('db_port'),
    user=os.getenv('db_user'),
    password=os.getenv('db_pass'),
    database=os.getenv('db_base')
)

states_router = Router()
dp = Dispatcher()
dp.include_router(states_router)

nest_asyncio.apply()


class RegForm(StatesGroup):
    name = State()
    email = State()


class NoteForm(StatesGroup):
    text = State()
    reminder_time = State()


async def init_connection():
    await db.connect()


@states_router.message(Command('start'))
async def start(message: Message, state: FSMContext):
    telegram_id = message.from_user.id
    if not await db.is_user_exists(telegram_id=telegram_id):
        await state.set_state(RegForm.name)
        await message.answer(text=mes.start_text)


@dp.message(Command('help'))
async def get_help(message: Message):
    await message.answer(text=mes.help_message)


@states_router.message(RegForm.name)
async def process_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await state.set_state(RegForm.email)
    await message.answer(text=mes.get_email)


@states_router.message(RegForm.email)
async def process_language(message: Message, state: FSMContext):
    data = await state.update_data(email=message.text)
    await state.clear()

    telegram_id = message.from_user.id
    if not await db.is_user_exists(telegram_id=telegram_id):
        await db.new_user(
            telegram_id=telegram_id,
            name=data['name'],
            email=data['email']
        )
        await message.answer(text=mes.registration_done)


@states_router.message(Command('addnote'))
async def new_note(message: Message, state: FSMContext):
    telegram_id = message.from_user.id
    if not await db.is_user_exists(telegram_id=telegram_id):
        await message.answer(text=mes.not_registered)
    else:
        await state.set_state(NoteForm.text)
        await message.answer(text=mes.enter_note_text)


@states_router.message(NoteForm.text)
async def process_note_text(message: Message, state: FSMContext):
    await state.update_data(text=message.text)
    await state.set_state(NoteForm.reminder_time)
    await message.answer(text=mes.enter_note_time)


@states_router.message(NoteForm.reminder_time)
async def process_language(message: Message, state: FSMContext):
    data = await state.update_data(reminder_time=message.text)
    await state.clear()

    try:
        date = datetime.datetime.strptime(data['reminder_time'], '%d.%m.%Y %H:%M')
    except ValueError:
        await message.answer(text=mes.wrong_date_format)
        return

    if date < datetime.datetime.now():
        await message.answer(text=mes.wrong_date)
    else:
        telegram_id = message.from_user.id
        user_id = await db.get_id_by_telegram_id(telegram_id=telegram_id)
        await db.new_note(
            user_id=user_id,
            text=data['text'],
            reminder_time=int(date.timestamp())
        )
        await message.answer(text=mes.note_created(int(date.timestamp())))


@dp.message(Command('mynotes'))
async def my_notes(message: Message):
    telegram_id = message.from_user.id
    if not await db.is_user_exists(telegram_id=telegram_id):
        await message.answer(text=mes.not_registered)
    else:
        user_id = await db.get_id_by_telegram_id(telegram_id=telegram_id)
        notes = await db.get_user_notes(user_id=user_id, limit=mes.NOTES_LIST_SIZE)
        if len(notes) == 0:
            await message.answer(text=mes.no_notes)
        else:
            notes_count = await db.user_notes_count(user_id=user_id)
            pages_count = math.ceil(notes_count/mes.NOTES_LIST_SIZE)
            await message.answer(text=mes.your_notes, reply_markup=await mes.notes_keyboard(notes=notes, offset=0,
                                                                                            pages_count=pages_count))


@dp.callback_query(F.data.startswith('notes_list_'))
async def my_notes_callback(callback: CallbackQuery):
    telegram_id = callback.from_user.id
    if not await db.is_user_exists(telegram_id=telegram_id):
        await callback.message.edit_text(text=mes.not_registered)
        await callback.message.edit_reply_markup(reply_markup=None)
    else:
        user_id = await db.get_id_by_telegram_id(telegram_id=telegram_id)
        data = callback.data
        offset = int(data.replace('notes_list_', ''))
        notes_count = await db.user_notes_count(user_id=user_id)
        pages_count = math.ceil(notes_count / mes.NOTES_LIST_SIZE)
        if offset < 0:
            offset = pages_count - 1
        elif offset >= pages_count:
            offset = 0
        notes = await db.get_user_notes(user_id=user_id, limit=mes.NOTES_LIST_SIZE, offset=mes.NOTES_LIST_SIZE * offset)
        await callback.message.edit_text(text=mes.your_notes)
        await callback.message.edit_reply_markup(reply_markup=await mes.notes_keyboard(notes=notes, offset=offset,
                                                                                       pages_count=pages_count))


@dp.callback_query(F.data.startswith('show_note_'))
async def show_note(callback: CallbackQuery):
    telegram_id = callback.from_user.id
    if not await db.is_user_exists(telegram_id=telegram_id):
        await callback.message.edit_text(text=mes.not_registered)
        await callback.message.edit_reply_markup(reply_markup=None)
    else:
        data = callback.data.replace('show_note_', '').split('_')
        try:
            note_id = int(data[0])
            offset = int(data[1])
        except (IndexError, ValueError):
            await callback.message.edit_text(text=mes.smth_went_wrong)
            await callback.message.edit_reply_markup(reply_markup=None)
            return
        note = await db.get_note(note_id=note_id)
        text, markup = await mes.show_note_message(note=note, offset=offset)
        await callback.message.edit_text(text=text)
        await callback.message.edit_reply_markup(reply_markup=markup)


async def main() -> None:
    bot = Bot(BOT_TOKEN)
    print('ready')
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(init_connection())
    asyncio.run(main())


