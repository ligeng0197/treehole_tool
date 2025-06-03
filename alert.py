import asyncio
import aiohttp
import time
import os
import json  # Import json module
from utils import get_config
from datetime import datetime
import hashlib

WECOM_ROBOT_URL = get_config("alert_robot_url")
CHECK_INTERVAL = get_config("process_sleep_time", 60)  # seconds
ERROR_KEYWORDS = ["Error", "Exception", "Failed"]  # Keywords to look for in the log
SENT_ALERTS_FILE = "sent_alerts.json"

async def send_wecom_robot(content):
    if not WECOM_ROBOT_URL:
        print("⚠️  WeCom robot URL is not configured. Skipping alert.")
        return

    headers = {"Content-Type": "application/json"}
    data = {
        "msgtype": "text",
        "text": {"content": content}
    }
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(WECOM_ROBOT_URL, headers=headers, json=data) as response:
                response.raise_for_status()
                print("✅ WeCom robot message sent successfully.")
        except aiohttp.ClientError as e:
            print(f"❌ Failed to send WeCom robot message: {e}")

async def load_sent_alerts():
    if os.path.exists(SENT_ALERTS_FILE):
        with open(SENT_ALERTS_FILE, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                print("❌ sent_alerts.json decode error, initializing empty list.")
                return []
    else:
        return []

async def save_sent_alerts(sent_alerts):
    with open(SENT_ALERTS_FILE, "w", encoding="utf-8") as f:
        json.dump(sent_alerts, f, ensure_ascii=False, indent=2)

async def check_log_and_alert():
    sent_alerts = await load_sent_alerts()

    while True:
        try:
            with open("run.log", "r", encoding="utf-8") as f:
                log_content = f.read()
        except FileNotFoundError:
            print("❌ run.log not found.")
            await asyncio.sleep(CHECK_INTERVAL)
            continue

        # Find new error messages
        error_messages = []
        for keyword in ERROR_KEYWORDS:
            if keyword in log_content:
                lines = log_content.splitlines()
                for line in lines:
                    if keyword in line:
                        try:
                            timestamp_str = line.split(']')[0].strip().lstrip('[')
                            timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S").strftime("%Y-%m-%d %H:%M:%S")
                        except (ValueError, IndexError):
                            assert False,"Wrong place"
                        line_encoded = line.encode('utf-8')
                        alert_id = f"{timestamp}-{hashlib.sha256(line_encoded).hexdigest()}"  # Create a unique ID
                        if alert_id not in sent_alerts:
                            error_messages.append((timestamp, line))
                            sent_alerts.append(alert_id)

        # Send alerts for new error messages
        tasks = []
        for timestamp, line in error_messages:
            content = f"🚨 异常警告 ({timestamp}):\n{line}"
            tasks.append(send_wecom_robot(content))

        await asyncio.gather(*tasks)

        await save_sent_alerts(sent_alerts)

        print(f"😴 Alert Waiting for {CHECK_INTERVAL} seconds...")
        await asyncio.sleep(CHECK_INTERVAL)

async def run_alert():
    await check_log_and_alert()

if __name__ == "__main__":
    import json
    asyncio.run(run_alert())
