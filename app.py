# app.py
import asyncio
from fetcher import run_fetcher
from evaluator import run_evaluator

async def main():
    task1 = asyncio.create_task(run_fetcher())
    task2 = asyncio.create_task(run_evaluator())
    await asyncio.gather(task1, task2)

if __name__ == "__main__":
    asyncio.run(main())
