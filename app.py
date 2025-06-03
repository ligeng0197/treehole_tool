# app.py
import asyncio
from fetcher import run_fetcher
from evaluator import run_evaluator
from notify import run_notify
from alert import run_alert

async def main():
    task1 = asyncio.create_task(run_fetcher())
    task2 = asyncio.create_task(run_evaluator())
    task3 = asyncio.create_task(run_notify())
    task4 = asyncio.create_task(run_alert())
    await asyncio.gather(task1, task2, task3, task4)
    

if __name__ == "__main__":
    asyncio.run(main())
