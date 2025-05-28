# async_fetcher.py
import asyncio
import json
from datetime import datetime
import os
from playwright.async_api import async_playwright

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
    if len(all_posts) > 400:
        all_posts = all_posts[-400:]

    with open(filename, "w", encoding="utf-8") as f:
        json.dump(all_posts, f, ensure_ascii=False, indent=2)

    return len(new_posts)

async def run_fetcher():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()

        print("🟢 正在打开树洞页面，请登录后按回车继续...")
        await page.goto("https://treehole.pku.edu.cn/web/")
        input("🔑 登录完成后按回车以继续抓取帖子...")

        while True:
            print(f"🔁 正在刷新页面并抓取数据 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            await page.reload(wait_until="networkidle")
            posts = await extract_posts(page)
            saved_count = save_posts(posts)
            print(f"✅ 成功抓取并保存 {saved_count} 条帖子")
            await asyncio.sleep(60)

if __name__ == "__main__":
    asyncio.run(run_fetcher())
