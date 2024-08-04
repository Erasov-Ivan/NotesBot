from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import datetime
from models import Note

NOTES_LIST_SIZE = 10
SHOWED_NOTE_PART_LEN = 15

start_text = 'Здравствуйте!\nЯ бот для создания заметок.\nДля начала Вам необходимо зарегестрироваться\nКак я могу к вам обращаться?'
get_email = 'Введите Ваш email'
registration_done = '''Спасибо за регистрацию!

Как мной пользоваться?
/addnote - создание новой заметки
/mynotes - просмотр всех заметок

А также я буду напоминать Вам о заметке за 10 минут до указанного времени
'''
help_message = '''Как мной пользоваться?
/addnote - создание новой заметки
/mynotes - просмотр всех заметок

А также я буду напоминать Вам о заметке за 10 минут до указанного времени'''
not_registered = 'Для выполнения данной команды Вам необходимо зарегестрироваться\nВведите /start'
enter_note_text = 'Введите текст заметки одним сообщением'
enter_note_time = 'Введите дату и время в формате DD.MM.YYYY HH:MM\n\n Например: ' + datetime.datetime.now().strftime('%d.%m.%Y %H:%M') + ' (текущее время)'
wrong_date = 'Дата и время должны быть не меньше текущего'
wrong_date_format = 'Дата и время не соответствуют формату'
no_notes = 'У Вас ещё нет заметок'
your_notes = 'Ваши заметки'

smth_went_wrong = 'Что-то пошло не так'


def note_created(reminder_time: int) -> str:
    return f'Новая заметка создана, напомню Вам о ней {datetime.datetime.utcfromtimestamp(reminder_time - 10 * 60)}'


async def notes_keyboard(notes: list[Note], offset: int, pages_count: int) -> InlineKeyboardMarkup:
    keyboard = []
    for note in notes:
        showed_text = f'{note.text[:SHOWED_NOTE_PART_LEN]}...' if len(note.text) >= SHOWED_NOTE_PART_LEN else note.text
        keyboard.append(
            [
                InlineKeyboardButton(text=showed_text, callback_data=f'show_note_{note.id}_{offset}')
            ]
        )

    if pages_count > 1:
        keyboard.append(
            [
                InlineKeyboardButton(text='<-', callback_data=f'notes_list_{offset-1}'),
                InlineKeyboardButton(text=f'{offset + 1}/{pages_count}', callback_data='None'),
                InlineKeyboardButton(text='->', callback_data=f'notes_list_{offset+1}'),
            ]
        )
    else:
        keyboard.append(
            [
                InlineKeyboardButton(text=f'1/1', callback_data='None'),
            ]
        )

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


async def show_note_message(note: Note, offset: int) -> (str, InlineKeyboardMarkup):
    text = f'Заметка\n\n{note.text}\n\nДата и время: {datetime.datetime.utcfromtimestamp(note.reminder_time)}'
    keyboard = [[InlineKeyboardButton(text='Назад', callback_data=f'notes_list_{offset}')]]
    return text, InlineKeyboardMarkup(inline_keyboard=keyboard)

