import logging
import time
from typing import Dict

from aiogram import Bot, Dispatcher, executor, types
from dotenv import dotenv_values

logging.basicConfig(level=logging.INFO)

config = dotenv_values()
API_TOKEN = config["API_TOKEN"]

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

stopwatch: Dict[int, int] = {}


@dp.message_handler(commands=['go'])
async def start_stopwatch(message: types.Message):
    stopwatch[message.from_id] = time.time_ns()


def ns2ms(ns: int):
    return ns // 10 ** 6


@dp.message_handler(commands=['stop'])
async def start_stopwatch(message: types.Message):
    try:
        started_at = stopwatch.pop(message.from_id)
    except KeyError:
        await message.answer('You did not start stopwatch')
        return
    delta_ns = time.time_ns() - started_at
    delta_ms = ns2ms(delta_ns)
    await message.answer(delta_ms)


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
