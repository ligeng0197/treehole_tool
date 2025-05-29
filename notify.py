import json
import os
import aiohttp
import asyncio
import time
from utils import get_config

WECOM_ROBOT_URL = get_config("wecom_robot_url")
SENT_POSTS_FILE ="sent_posts.json"
MAX_SENT_POSTS = get_config("max_posts", 400)
CHECK_INTERVAL = get_config("sleep_time", 60)  # seconds

async def send_wecom_robot(content):
    headers = {"Content-Type": "application/json"}
    data = {
        "msgtype": "text",
        "text": {"content": content}
    }
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(WECOM_ROBOT_URL, headers=headers, json=data) as response:
                response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
                print("✅ WeCom robot message sent successfully.")
        except aiohttp.ClientError as e:
            print(f"❌ Failed to send WeCom robot message: {e}")

async def load_sent_posts():
    if os.path.exists(SENT_POSTS_FILE):
        with open(SENT_POSTS_FILE, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                print("❌ sent_posts.json decode error, initializing empty list.")
                return []
    else:
        return []

async def save_sent_posts(sent_posts):
    with open(SENT_POSTS_FILE, "w", encoding="utf-8") as f:
        json.dump(sent_posts, f, ensure_ascii=False, indent=2)

async def check_and_notify():
    sent_posts = await load_sent_posts()

    while True:
        try:
            with open("treehole_posts.json", "r", encoding="utf-8") as f:
                posts = json.load(f)
        except FileNotFoundError:
            print("❌ treehole_posts.json not found.")
            await asyncio.sleep(CHECK_INTERVAL)
            continue
        except json.JSONDecodeError:
            print("❌ treehole_posts.json decode error.")
            await asyncio.sleep(CHECK_INTERVAL)
            continue

        try:
            with open("evaluated_posts.json", "r", encoding="utf-8") as f:
                evaluated_posts = json.load(f)
        except FileNotFoundError:
            print("❌ evaluated_posts.json not found.")
            await asyncio.sleep(CHECK_INTERVAL)
            continue
        except json.JSONDecodeError:
            print("❌ evaluated_posts.json decode error.")
            await asyncio.sleep(CHECK_INTERVAL)
            continue

        tasks = []
        new_sent_posts = []
        for post in posts:
            post_id = post["id"]
            if (
                post_id in evaluated_posts
                and evaluated_posts[post_id] == True
                and post_id not in sent_posts
            ):
                post_date = post.get("date", "N/A")
                post_time = post.get("time", "N/A")
                content = f"🎯 检测到一个羽毛球相关帖子:\n{post_date} {post_time}\n帖子ID: {post_id}\n\n{post['content']}\n"
                tasks.append(send_wecom_robot(content))
                new_sent_posts.append(post_id)

        await asyncio.gather(*tasks)

        sent_posts.extend(new_sent_posts)

        # Keep only the most recent MAX_SENT_POSTS
        sent_posts = sent_posts[-MAX_SENT_POSTS:]
        await save_sent_posts(sent_posts)

        print(f"😴 Waiting for {CHECK_INTERVAL} seconds...")
        await asyncio.sleep(CHECK_INTERVAL)


async def run_notify():
    await check_and_notify()

if __name__ == "__main__":
    asyncio.run(run_notify())
