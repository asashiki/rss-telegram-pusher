import asyncio
import html
import json
import logging
import os
import re
import time

import feedparser
from telegram import Bot
from telegram.error import TelegramError

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
RSS_URL = os.getenv("RSS_URL")
POSTS_FILE = "sent_posts.json"
MAX_PUSH_PER_RUN = 5  # 单次最多推送5条

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

def load_sent_posts():
    try:
        if os.path.exists(POSTS_FILE):
            with open(POSTS_FILE, "r", encoding="utf-8") as f:
                content = f.read().strip()
                return json.loads(content) if content else []
        logging.info("首次运行，创建空ID列表")
        return []
    except Exception as e:
        logging.error(f"读取已发送ID失败：{str(e)}")
        return []

def save_sent_posts(post_ids):
    try:
        with open(POSTS_FILE, "w", encoding="utf-8") as f:
            json.dump(post_ids, f, ensure_ascii=False, indent=2)
        logging.info(f"已保存ID列表（共{len(post_ids)}条）")
    except Exception as e:
        logging.error(f"保存已发送ID失败：{str(e)}")

def fetch_updates():
    try:
        logging.info(f"获取RSS源：{RSS_URL}")
        feed = feedparser.parse(RSS_URL)
        if feed.bozo:
            logging.error(f"RSS解析错误：{feed.bozo_exception}")
            return None
        logging.info(f"成功获取{len(feed.entries)}条RSS条目")
        return feed
    except Exception as e:
        logging.error(f"获取RSS失败：{str(e)}")
        return None

def escape_markdown(text):
    special_chars = r"\_*[]()~`>#+-=|{}.!"
    for char in special_chars:
        text = text.replace(char, f"\\{char}")
    return text


def extract_post_id(entry):
    id_fields = ["id", "guid", "link"]
    for field in id_fields:
        value = getattr(entry, field, None)
        if value:
            candidate = value.strip()
            break
    else:
        return None

    match = re.search(r"(\d+)(?!.*\d)", candidate)
    if match:
        return match.group(1)
    return candidate


def extract_description(entry):
    raw_description = getattr(entry, "description", None) or getattr(entry, "summary", None) or ""
    fallback = getattr(entry, "title", None) or getattr(entry, "link", None) or ""
    if raw_description:
        cleaned = raw_description.strip()
        if cleaned.startswith("<![CDATA[") and cleaned.endswith("]]>"):
            cleaned = cleaned[9:-3]
        cleaned = html.unescape(cleaned)
        cleaned = re.sub(r"<[^>]+>", "", cleaned)
        cleaned = cleaned.replace("\r", "").strip()
        if cleaned:
            return cleaned
    return fallback.strip()


def get_entry_timestamp(entry):
    time_struct = getattr(entry, "published_parsed", None) or getattr(entry, "updated_parsed", None)
    if time_struct:
        return time.mktime(time_struct)
    return 0


async def send_message(bot, text, delay=3):
    try:
        await asyncio.sleep(delay)  # 发送间隔
        escaped_text = escape_markdown(text)
        message = f"主人{escaped_text}"
        logging.info(f"发送消息：{message[:100]}")
        await bot.send_message(
            chat_id=CHAT_ID,
            text=message,
            parse_mode="MarkdownV2"
        )
        logging.info("消息发送成功")
        return True
    except TelegramError as e:
        logging.error(f"Telegram发送失败：{str(e)}")
        return False

async def check_for_updates(sent_post_ids):
    updates = fetch_updates()
    if not updates:
        return

    new_posts = []
    for entry in updates.entries:
        try:
            post_id = extract_post_id(entry)
            if not post_id:
                logging.warning("无效条目，无法获取ID，跳过")
                continue
            post_id = str(post_id)
            if post_id in sent_post_ids:
                continue

            description = extract_description(entry)
            timestamp = get_entry_timestamp(entry)
            logging.info(f"解析到新条目 ID：{post_id}，内容长度：{len(description)}")
            new_posts.append({
                "id": post_id,
                "text": description,
                "timestamp": timestamp
            })
        except Exception as e:
            logging.error(f"解析条目失败：{str(e)}")
            continue

    if new_posts:
        # 按发布时间排序（旧→新），取前5条
        new_posts.sort(key=lambda x: (x["timestamp"], x["id"]))
        new_posts = new_posts[:MAX_PUSH_PER_RUN]  # 限制单次最多5条
        logging.info(f"发现{len(new_posts)}条新信息（单次最多推{MAX_PUSH_PER_RUN}条），准备依次推送（间隔3秒）")

        async with Bot(token=TELEGRAM_TOKEN) as bot:
            for i, post in enumerate(new_posts):
                # 第一条立即发送，后续每条间隔3秒
                success = await send_message(bot, post["text"], delay=3 if i > 0 else 0)
                if success:
                    sent_post_ids.append(post["id"])  # 仅记录成功发送的ID

        save_sent_posts(sent_post_ids)
    else:
        logging.info("无新帖子需要推送")

async def main():
    logging.info("===== 脚本开始运行 =====")
    sent_post_ids = load_sent_posts()
    try:
        await check_for_updates(sent_post_ids)
    except Exception as e:
        logging.error(f"主逻辑执行失败：{str(e)}")
    logging.info("===== 脚本运行结束 =====")

if __name__ == "__main__":
    asyncio.run(main())
