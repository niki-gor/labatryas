import logging
import time

import aiogram.utils.markdown as md
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.utils import executor
from dotenv import dotenv_values

logging.basicConfig(level=logging.INFO)

config = dotenv_values()

bot = Bot(token=config["API_TOKEN"])
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)


def ns2ms(ns: int):
    return ns // 10 ** 6


class M1(StatesGroup):
    start_first_pendulum = State()
    stop_first_pendulum = State()
    start_second_pendulum = State()
    stop_second_pendulum = State()


start_kb = types.ReplyKeyboardMarkup(resize_keyboard=True, selective=True).add('СТАРТ')
stop_kb = types.ReplyKeyboardMarkup(resize_keyboard=True, selective=True).add('СТОП')


@dp.message_handler(commands=['m1'])
async def m1(message: types.Message):
    await message.answer('Сделайте 3 измерения', reply_markup=start_kb)
    await M1.start_first_pendulum.set()


def msg_text(text):
    def eq(msg):
        return msg.text == text
    return eq


@dp.message_handler(msg_text('СТАРТ'), state=M1.start_first_pendulum)
async def start_first_pendulum(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['start'] = time.time_ns()
    await message.answer('Секундомер запущен!', reply_markup=stop_kb)
    await M1.stop_first_pendulum.set()


@dp.message_handler(msg_text('СТОП'), state=M1.stop_first_pendulum)
async def stop_first_pendulum(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data.setdefault('first', [])
        delta_ms = ns2ms(time.time_ns() - data['start'])
        data['first'].append(delta_ms)
        await message.answer(f'{len(data["first"])}-ое измерение: {data["first"][-1]}', reply_markup=start_kb)
        if len(data['first']) == 3:
            await message.answer('Сделайте одно измерение', reply_markup=start_kb)
            await M1.start_second_pendulum.set()
        else:
            await M1.start_first_pendulum.set()


@dp.message_handler(msg_text('СТАРТ'), state=M1.start_second_pendulum)
async def start_second_pendulum(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['start'] = time.time_ns()
    await message.answer('Секундомер запущен!', reply_markup=stop_kb)
    await M1.stop_second_pendulum.set()


@dp.message_handler(msg_text('СТОП'), state=M1.stop_second_pendulum)
async def stop_second_pendulum(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data.setdefault('second', [])
        delta_ms = ns2ms(time.time_ns() - data['start'])
        data['second'].append(delta_ms)
        await message.answer(f'{len(data["second"])}-ое измерение: {data["second"][-1]}', reply_markup=start_kb)
        if len(data['second']) == 1:
            await bot.send_message(
                message.chat.id,
                md.text(
                    md.text('Маятник 1:', *data['first']),
                    md.text('Маятник 2:', *data['second']),
                    sep='\n',
                ),
            )
            data.clear()
            await state.finish()
        else:
            await M1.start_second_pendulum.set()


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)

# @dp.message_handler(state=M1.pendulum2)
# async def process_name(message: types.Message, state: FSMContext):
#     async with state.proxy() as data:
#         data['2'] = message.text
#         markup = types.ReplyKeyboardRemove()
#
#         await bot.send_message(
#             message.chat.id,
#             md.text(
#                 md.text(md.bold(data['1'])),
#                 md.text(md.code(data['2'])),
#                 sep='\n',
#             ),
#             reply_markup=markup,
#             parse_mode=ParseMode.MARKDOWN,
#         )
#
#     state.finish()


#
#
#
#
# # создаём форму и указываем поля
# class Form(StatesGroup):
#     name = State()
#     age = State()
#     gender = State()
#
#
# # Начинаем наш диалог
# @dp.message_handler(commands=['start'])
# async def cmd_start(message: types.Message):
#     await Form.name.set()
#     await message.reply("Привет! Как тебя зовут?")
#
#
# # Добавляем возможность отмены, если пользователь передумал заполнять
# @dp.message_handler(state='*', commands='cancel')
# @dp.message_handler(Text(equals='отмена', ignore_case=True), state='*')
# async def cancel_handler(message: types.Message, state: FSMContext):
#     current_state = await state.get_state()
#     if current_state is None:
#         return
#
#     await state.finish()
#     await message.reply('ОК')
#
#
# # Сюда приходит ответ с именем
# @dp.message_handler(state=Form.name)
# async def process_name(message: types.Message, state: FSMContext):
#     async with state.proxy() as data:
#         data['name'] = message.text
#
#     await Form.next()
#     await message.reply("Сколько тебе лет?")
#
#
# # Проверяем возраст
# @dp.message_handler(lambda message: not message.text.isdigit(), state=Form.age)
# async def process_age_invalid(message: types.Message):
#     return await message.reply("Напиши возраст или напиши /cancel")
#
# # Принимаем возраст и узнаём пол
# @dp.message_handler(lambda message: message.text.isdigit(), state=Form.age)
# async def process_age(message: types.Message, state: FSMContext):
#     await Form.next()
#     await state.update_data(age=int(message.text))
#
#     markup = types.ReplyKeyboardMarkup(resize_keyboard=True, selective=True)
#     markup.add("М", "Ж")
#     markup.add("Другое")
#
#     await message.reply("Укажи пол (кнопкой)", reply_markup=markup)
#
#
# # Проверяем пол
# @dp.message_handler(lambda message: message.text not in ["М", "Ж", "Другое"], state=Form.gender)
# async def process_gender_invalid(message: types.Message):
#     return await message.reply("Не знаю такой пол. Укажи пол кнопкой на клавиатуре")
#
#
# # Сохраняем пол, выводим анкету
# @dp.message_handler(state=Form.gender)
# async def process_gender(message: types.Message, state: FSMContext):
#     async with state.proxy() as data:
#         data['gender'] = message.text
#         markup = types.ReplyKeyboardRemove()
#
#         await bot.send_message(
#             message.chat.id,
#             md.text(
#                 md.text('Hi! Nice to meet you,', md.bold(data['name'])),
#                 md.text('Age:', md.code(data['age'])),
#                 md.text('Gender:', data['gender']),
#                 sep='\n',
#             ),
#             reply_markup=markup,
#             parse_mode=ParseMode.MARKDOWN,
#         )
#
#     await state.finish()
# import aiogram.utils.markdown as md
# from aiogram import Bot, Dispatcher, types
# from aiogram.contrib.fsm_storage.memory import MemoryStorage
# from aiogram.dispatcher import FSMContext
# from aiogram.dispatcher.filters import Text
# from aiogram.dispatcher.filters.state import State, StatesGroup
# from aiogram.types import ParseMode
# from aiogram.utils import executor
# from dotenv import dotenv_values
#
#
# bot = Bot(token=dotenv_values()['API_TOKEN'])
# storage = MemoryStorage()
# dp = Dispatcher(bot, storage=storage)
#
#
#
