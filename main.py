import asyncio
import logging
import time
from abc import abstractmethod
from dataclasses import asdict, dataclass
from typing import Optional

import aiogram.utils.markdown as md
import attr
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.contrib.fsm_storage.redis import RedisStorage2
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.utils import executor

from config_reader import config
from laba_manager import LabaManager

logging.basicConfig(level=logging.INFO)


bot = Bot(token=config.bot_token.get_secret_value())
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)
lm = LabaManager()


def ns2ms(ns: int):
    return ns // 10 ** 6


class M1(StatesGroup):
    start_first_pendulum = State()
    stop_first_pendulum = State()
    start_second_pendulum = State()
    stop_second_pendulum = State()


start_kb = types.ReplyKeyboardMarkup(resize_keyboard=True, selective=True).add('СТАРТ')
stop_kb = types.ReplyKeyboardMarkup(resize_keyboard=True, selective=True).add('СТОП')


# class Session:
#     def __init__(self):
#         self.laba = None
    
#     async def handle_message(self, message: types.Message):
#         response = Response()
#         if self.laba is None:
#             laba = lm.find(message.text)
#             if laba is None:
#                 response.text = 'Лаба не найдена'
#             else:
#                 self.laba = laba
#                 response = await self.laba.get()
#         else:
#             await self.laba.put(message.text)
#             response = await self.laba.get()
#             if self.laba.done():
#                 self.laba = None
#         await message.answer(**asdict(response))
        

# async def m1(inchan: asyncio.Queue, outchan: asyncio.Queue):
#     data = {}
#     N1 = 3
#     await outchan.put(Response(f'Сделайте {N1} измерения'))


# @dp.message_handler()
# async def answer(message: types.Message, state: FSMContext):
#     response = Response()
#     async with state.proxy() as data:
#         lab = data.get('lab')
#         if lab is None:
#             lab_name = message.text
#             if lab_name not in laba_set:
#                 response.text = 'Net takoy laby'
#             else:
#                 data['lab'] = lab_name
#                 response.text = 'Created new laba'
#         else:
#             response.text = 'Processing laba...'
#     await message.answer(**asdict(response))


class Work(StatesGroup):
    choose = State()
    do = State()


@dp.message_handler(commands=['start'])
async def greet(message: types.Message, state: FSMContext):
    await message.answer('Выберите лабу')
    await state.set_state(Work.choose)

l = None
@dp.message_handler(state=Work.choose)
async def choose(message: types.Message, state: FSMContext):
    laba = lm.find(message.text)
    if laba is None:
        await message.answer('Нет такой лабы')
        return
    await state.set_state(Work.do)
    # await state.update_data(laba=laba)
    global l
    l = laba
    intro = await laba.get()
    await message.answer(**intro)


@dp.message_handler(state=Work.do)
async def do(message: types.Message, state: FSMContext):
    # data = await state.get_data()
    global l
    laba = l
    await laba.put(message.text)
    response = await laba.get()
    await message.answer(**response)
    if laba.done():
        await message.answer('Выберите новую лабу')
        await state.set_state(Work.choose)
            

@dp.message_handler(commands=['m1'])
async def m1(message: types.Message, state: FSMContext):
    await message.answer('Сделайте 3 измерения', reply_markup=start_kb)
    await M1.start_first_pendulum.set()


async def async_task(inchan: asyncio.Queue, outchan: asyncio.Queue):
    x = await inchan.get()
    await outchan.put(x)

# @dp.message_handler(commands=['async'])
# async def async_cmd(message: types.Message, state: FSMContext):
#     data = await state.get_data()
#     if 'session' not in data:
#         logging.info('HOOOOW')
#     data.setdefault('session', Session())
#     await data['session'].handle_message(message)
        
        # if 'laba' not in data:
        #     laba = data['laba']
        #     await laba.put(message.text)
        #     response = await laba.get()
        #     if response.text:
        #         await message.answer(**asdict(response))
        # else:
        # data['laba'] = MMM1()
        # laba = data['laba']
        # text = await laba.get()
        # await message.answer(text)
        # if laba.done():
        #     del data['laba']


    # inchan = asyncio.Queue()
    # outchan = asyncio.Queue()
    # loop = asyncio.get_event_loop()
    # loop.create_task(async_task(inchan, outchan))

    # await inchan.put(message.text)
    # result = await outchan.get()

    # await message.answer(f'You wrote: {result}')


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
    executor.start_polling(dp, skip_updates=False)

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
