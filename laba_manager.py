import asyncio
import logging
from abc import abstractmethod
from typing import Optional

logging.basicConfig(level=logging.INFO)

class Laba:
    def __init__(self):
        self._in = asyncio.Queue()
        self._out = asyncio.Queue()
        self._task = asyncio.create_task(self.task_func())
    
    async def put(self, text: str):
        await self._in.put(text)
    
    async def get(self) -> dict:
        return await self._out.get()

    async def _answer(self, text=None):
        response = {
            'text': text
        }
        await self._out.put(response)
    
    def done(self) -> bool:
        return self._task.done()
    
    @abstractmethod
    async def task_func(self):
        pass


class MMM1(Laba):
    async def task_func(self):
        await self._answer('Сделайте 3 измерения')
        self.pendulum1 = []
        for i in range(3):
            measurement = await self._in.get()
            self.pendulum1.append(measurement)
            if i == 2:
                break
            await self._answer('Измерение сделано')
        await self._answer(' '.join(self.pendulum1))


class LabaManager:
    def find(self, laba_name: str) -> Optional[Laba]:
        return MMM1()