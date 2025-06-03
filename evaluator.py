# evaluator_async.py
import json
import os
import asyncio
from openai import AsyncOpenAI
from utils import get_config

openai_api_key = get_config("openai_api_key")
use_openai = get_config("use_openai")

if use_openai:
    client = AsyncOpenAI(
        api_key=openai_api_key,
        base_url="https://aihubmix.com/v1"
    )

evaluated_posts_file = "evaluated_posts.json"
max_posts = get_config("max_posts", 500)  # Use a default value if not found
sleep_time = get_config("process_sleep_time", 60)

async def evaluate(content):
    if use_openai:
        try:
            response = await client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "你是一个助手，用于判断给定的帖子内容是否是需要出羽毛球场或转让羽毛球场。如果是，返回json {\"relevant\": true}，否则返回 {\"relevant\": false}。只返回json，不要返回其他内容。"},
                    {"role": "user", "content": content}
                ]
            )
            result = json.loads(response.choices[0].message.content)
            return result
        except Exception as e:
            print(f"OpenAI API调用失败: {e}")
            return {"relevant": False}
    else:
        keywords = ["羽球", "羽毛球", "中羽"]
        if any(keyword in content for keyword in keywords):
            return {"relevant": True}
        else:
            return {"relevant": False}

async def run_evaluator():
    evaluated_posts = {}

    # Load already evaluated posts
    if os.path.exists(evaluated_posts_file):
        with open(evaluated_posts_file, "r", encoding="utf-8") as f:
            try:
                evaluated_posts = json.load(f)
            except json.JSONDecodeError:
                print("❌ evaluated_posts.json 解码失败，初始化为空。")
                evaluated_posts = {}

    while True:
        try:
            with open("treehole_posts.json", "r", encoding="utf-8") as f:
                posts = json.load(f)
        except FileNotFoundError:
            print("treehole_posts.json 不存在，5秒后重试...")
            await asyncio.sleep(5)
            continue

        updated = False
        processed_count = 0

        for post in posts:
            post_id = post["id"]
            if post_id not in evaluated_posts:
                result = await evaluate(post["content"])
                evaluated_posts[post_id] = result["relevant"]

                if result["relevant"]:
                    print("🎯 命中帖子:", post_id, post["content"])
                updated = True
                processed_count += 1

        print(f"✅ 本轮处理了 {processed_count} 个帖子")

        if updated:
            # Limit the number of evaluated posts to the most recent 400
            evaluated_posts = dict(list(evaluated_posts.items())[-max_posts-100:])
            with open(evaluated_posts_file, "w", encoding="utf-8") as f:
                json.dump(evaluated_posts, f, ensure_ascii=False, indent=2)

        await asyncio.sleep(sleep_time)

if __name__ == "__main__":
    asyncio.run(run_evaluator())
