# async_fetcher.py
import asyncio
import json
from datetime import datetime
import os
from playwright.async_api import async_playwright
from utils import get_config

max_posts = get_config("max_posts", 400)

async def extract_posts(page):
    posts = []
    items = await page.query_selector_all(".flow-item-row")

    for item in items:
        try:
            post_id = await (await item.query_selector(".box-id")).inner_text()
            timestamp = await (await item.query_selector(".box-header")).inner_text()
            content_element = await item.query_selector(".box-content span")
            content = await content_element.inner_text() if content_element else ""

            # 时间提取和格式处理
            try:
                date_str = timestamp.split()[-2]  # "05-28"
                time_str = timestamp.split()[-1]  # "12:05"
                date_object = datetime.strptime(date_str, "%m-%d")
                time_object = datetime.strptime(time_str, "%H:%M")
                date = date_object.strftime("%m-%d")
                time = time_object.strftime("%H:%M")
            except ValueError:
                date = "N/A"
                time = "N/A"

            posts.append({
                "id": post_id.strip(),
                "timestamp": timestamp.strip(),
                "content": content.strip(),
                "date": date,
                "time": time
            })
        except Exception as e:
            print(f"❌ Error extracting post: {e}")
            continue

    return posts

def save_posts(posts, filename="treehole_posts.json"):
    if os.path.exists(filename):
        with open(filename, "r", encoding="utf-8") as f:
            try:
                existing_posts = json.load(f)
            except json.JSONDecodeError:
                existing_posts = []
    else:
        existing_posts = []

    new_posts = []
    existing_ids = {post["id"] for post in existing_posts}
    for post in posts:
        if post["id"] not in existing_ids:
            new_posts.append(post)

    all_posts = existing_posts + new_posts
    if len(all_posts) > max_posts:
        all_posts = all_posts[-max_posts:]

    with open(filename, "w", encoding="utf-8") as f:
        json.dump(all_posts, f, ensure_ascii=False, indent=2)

    return len(new_posts)

async def run_fetcher():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        
        # Check if auth.json exists
        if os.path.exists("auth.json"):
            context = await browser.new_context(storage_state="auth.json")
            print("🟢 已找到 auth.json，尝试使用登录状态...")
        else:
            context = await browser.new_context()
            print("⚠️  未找到 auth.json，将打开浏览器进行登录...")

        page = await context.new_page()

        await page.goto("https://treehole.pku.edu.cn/web/")

        # Check if already logged in
        if await page.locator('text=退出').count() == 0:
            print("🟢 正在打开树洞页面，请登录后按回车继续...")
            input("🔑 登录完成后按回车以继续抓取帖子...")
            # Save storage state to auth.json
            await context.storage_state(path="auth.json")
            print("💾 登录状态已保存到 auth.json")
        else:
            print("🟢 已登录，开始抓取帖子...")

        empty_posts_count = 0  # Counter for consecutive empty posts
        error_logged = False  # Flag to track if the error has been logged

        while True:
            print(f"🔁 正在刷新页面并抓取数据 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            await page.reload(wait_until="networkidle")
            posts = await extract_posts(page)
            saved_count = save_posts(posts)
            print(f"✅ 成功抓取并保存 {saved_count} 条帖子")

            if not posts:
                empty_posts_count += 1
                print(f"⚠️  连续 {empty_posts_count} 次抓取到空帖子列表")
                if empty_posts_count >= 3 and not error_logged:
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    error_message = f"[{timestamp}] [Error] 🚨 连续3次抓取到空帖子列表，请检查树洞是否正常！"
                    print(error_message)
                    with open("run.log", "a", encoding="utf-8") as log_file:
                        log_file.write(error_message + "\n")
                    error_logged = True  # Set the flag to True after logging
            else:
                empty_posts_count = 0  # Reset the counter if posts are found
                error_logged = False # Reset the error flag if posts are found

            await asyncio.sleep(get_config("fetch_sleep_time", 60))

if __name__ == "__main__":
    asyncio.run(run_fetcher())
