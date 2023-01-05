import gc
from datetime import date, datetime

from aiogram import Bot, Dispatcher
from aiogram import types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils import executor

import sqlite

import config
import messages

import exceptions
import expenses
from categories import Categories
from middlewares import AccessMiddleware


async def on_startup(_):
    await sqlite.db_start()


storage = MemoryStorage()
bot = Bot(config.API_TOKEN)
dp = Dispatcher(bot,
                storage=storage)


async def on_startup(_):
    await sqlite.db_start()
    print('Бот запущен.')
    print('База данных подключена.')


@dp.message_handler(commands=['start'])
async def start(message):
    await bot.send_message(message.chat.id,
                           text=messages.start_message.format(
                               message.from_user))
    await menu(message)
    await sqlite.create_profile(message.from_user.id)


@dp.message_handler(text='В меню')
async def menu(message):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    signup = types.KeyboardButton('Записаться на сеанс')
    services = types.KeyboardButton('Услуги')
    other = types.KeyboardButton('Примеры работ')
    helper = types.KeyboardButton('Консультация с мастером')
    database = types.KeyboardButton('Анкета')
    master = types.KeyboardButton('Я - мастер')
    keyboard.add(signup, services, other, helper, database, master)
    await message.answer(
        text="Что Вы хотите сделать?",
        reply_markup=keyboard)
    await message.delete()


chat_id = '364936872'


@dp.message_handler(text='Записаться на сеанс')
async def serve(message):
    keyboard = InlineKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)

    googleform = InlineKeyboardButton(text="🔮 Гугл форма", url='https://forms.gle/wZ8xSs9J2jcxC35c7')
    keyboard.add(googleform)
    await message.answer(text="Заполните гугл форму ниже:", reply_markup=keyboard)

    keyboard1 = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    back = types.KeyboardButton(text="В меню")
    keyboard1.add(back)


@dp.message_handler(text='Услуги')
async def services_handler(message):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    back = types.KeyboardButton(text="В меню")
    find = types.KeyboardButton(text='Подробное описание услуг')
    signup = types.KeyboardButton('Записаться на сеанс')
    helper = types.KeyboardButton('Консультация с мастером')
    database = types.KeyboardButton('Анкета')
    master = types.KeyboardButton('Я - мастер')
    keyboard.add(find, back, signup, helper, database, master)
    await message.answer(
        text=messages.uslugi_message, reply_markup=keyboard)
    await message.delete()


@dp.message_handler(text='Примеры работ')
async def exampleofwork_handler(message):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    back = types.KeyboardButton(text="В меню")
    signup = types.KeyboardButton('Записаться на сеанс')
    helper = types.KeyboardButton('Консультация с мастером')
    database = types.KeyboardButton('Анкета')
    master = types.KeyboardButton('Я - мастер')
    keyboard.add(back, signup, helper, database, master)
    await bot.send_photo(message.chat.id,
                         photo=messages.photo1)
    await bot.send_photo(message.chat.id,
                         photo=messages.photo2)
    await bot.send_photo(message.chat.id,
                         photo=messages.photo3)
    await menu(message)


@dp.message_handler(text='Подробное описание услуг')
async def description_handler(message):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    back = types.KeyboardButton(text="В меню", callback_data="")
    keyboard.add(back)
    await message.answer(text=messages.osobennosti_message,
                         reply_markup=keyboard)
    await message.delete()


@dp.message_handler(text='Консультация с мастером')
async def contacts_handler(message):
    keyboard = InlineKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)

    mastertelega = InlineKeyboardButton(text=messages.link_tg_message, url='https://t.me/maynosss')
    mastervk = InlineKeyboardButton(text=messages.link_vk_message, url='https://vk.com/maynosss')
    keyboard.add(mastertelega, mastervk)
    await message.answer(text="Контакты мастера ниже:", reply_markup=keyboard)
    await message.delete()
    keyboard1 = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    back = types.KeyboardButton('В меню')
    keyboard1.add(back)
    await message.answer(text=messages.back_message, reply_markup=keyboard1)


class ProfileStatesGroup(StatesGroup):
    name = State()
    birthday = State()
    number = State()


def get_kb() -> ReplyKeyboardMarkup:
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(KeyboardButton('/create'))

    return kb


def get_cancel_kb() -> ReplyKeyboardMarkup:
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(KeyboardButton('/cancel'))

    return kb


@dp.message_handler(commands=['cancel'], state='*')
async def cmd_cancel(message: types.Message, state: FSMContext):
    if state is None:
        return

    await state.finish()
    await message.reply('Вы прервали создание анкеты!',
                        reply_markup=get_kb())


@dp.message_handler(text='Анкета')
async def cmd_start(message: types.Message) -> None:
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    back = types.KeyboardButton(text="В меню", callback_data="")
    keyboard.add(back)
    await message.answer('Для заполнения анкеты нажмите /create',
                         reply_markup=get_kb())

    await sqlite.create_profile(message.from_user.id)


@dp.message_handler(commands=['create'])
async def cmd_create(message: types.Message) -> None:
    await message.reply("Приступим! Пришлите полное ФИО!",
                        reply_markup=get_kb())
    await sqlite.create_profile(user_id=message.from_user.id)
    await ProfileStatesGroup.next()


@dp.message_handler(state=ProfileStatesGroup.name)
async def load_name(message: types.Message, state: FSMContext) -> None:
    async with state.proxy() as data:
        data['name'] = message.text

    await message.reply('Введите дату рождения!')
    await ProfileStatesGroup.next()


@dp.message_handler(state=ProfileStatesGroup.birthday)
async def load_birthday(message: types.Message, state: FSMContext) -> None:
    async with state.proxy() as data:
        data['birthday'] = message.text

        await message.reply('Введите номер телефона!')
        await ProfileStatesGroup.next()


@dp.message_handler(state=ProfileStatesGroup.number)
async def check_number(message: types.Message, state: FSMContext) -> None:
    async with state.proxy() as data:
        data['number'] = message.text

    await message.reply('Ваша акнета успешно создана! Чтобы вернуться нажмите /start')
    #    await sqlite.edit_profile(state, user_id=message.from_user.id)
    await state.finish()


@dp.message_handler(text='Я - мастер')
async def send_welcome(message: types.Message):
    await message.answer(
        "Привет! Я помогу тебе вести учет расходов\n\n"
        "Для добавления расхода напиши '250 краска'\n"
        "Сегодняшняя статистика: /today\n"
        "Расходы за текущий месяц: /month\n"
        "Последние внесённые расходы: /expenses\n"
        "Категории трат: /categories")


@dp.message_handler(lambda message: message.text.startswith('/del'))
async def del_expense(message: types.Message):
    row_id = int(message.text[4:])
    expenses.delete_expense(row_id)
    answer_message = "Удалила"
    await message.answer(answer_message)


@dp.message_handler(commands=['categories'])
async def categories_list(message: types.Message):
    categories = Categories().get_all_categories()
    answer_message = "Категории трат:\n\n* " +\
            ("\n* ".join([c.name+' ('+", ".join(c.aliases)+')' for c in categories]))
    await message.answer(answer_message)


@dp.message_handler(commands=['today'])
async def today_statistics(message: types.Message):
    answer_message: str = expenses.get_today_statistics()
    await message.answer(answer_message)


@dp.message_handler(commands=['month'])
async def month_statistics(message: types.Message):
    answer_message = expenses.get_month_statistics()
    await message.answer(answer_message)


@dp.message_handler(commands=['expenses'])
async def list_expenses(message: types.Message):
    last_expenses = expenses.last()
    if not last_expenses:
        await message.answer("Расходы ещё не заведены")
        return

    last_expenses_rows = [
        f"{expense.amount} руб. на {expense.category_name} — нажми "
        f"/del{expense.id} для удаления"
        for expense in last_expenses]
    answer_message = "Последние сохранённые траты:\n\n* " + "\n\n* "\
            .join(last_expenses_rows)
    await message.answer(answer_message)


@dp.message_handler()
async def add_expense(message: types.Message):
    try:
        expense = expenses.add_expense(message.text)
    except exceptions.NotCorrectMessage as e:
        await message.answer(str(e))
        return
    answer_message = (
        f"Добавлены траты {expense.amount} руб на {expense.category_name}.\n\n"
        f"{expenses.get_today_statistics()}")
    await message.answer(answer_message)


@dp.message_handler(content_types=['text'])
async def notresponsedmessage(message):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    back = types.KeyboardButton('В меню')
    keyboard.add(back)
    await bot.send_sticker(message.chat.id,
                           sticker='CAACAgIAAxkBAAEG4ixjn53FnPpL2LVBDcEuteQRFS-MfwACfRUAAlDlUEjpsJGXpy389SwE')
    await message.answer(text=messages.not_responsed_message, reply_markup=keyboard)


if __name__ == '__main__':
    if config.API_TOKEN == "":
        print("Нет токена. Вставьте токен.")
    else:
        executor.start_polling(dp, skip_updates=True,
                               on_startup=on_startup)
