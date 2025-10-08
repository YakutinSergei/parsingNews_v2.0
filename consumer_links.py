import asyncio
import json
import re

from aiokafka import AIOKafkaConsumer
from core.config import settings
from parsers.universal_parser import extract_article
from producer import send_raw
from datetime import datetime, timezone

# регулярка для определения Telegram-ссылки
TG_LINK_RE = re.compile(r"https?://t\.me/[\w\d_]+/\d+")

# === Consumer ===
async def consume_links():
    """
    Слушает Kafka-топик tg_links, получает ссылки,
    определяет Telegram это или нет, и парсит.
    """
    consumer = AIOKafkaConsumer(
        settings.KAFKA_TOPIC_TG_LINKS,
        bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
        group_id="tg_parser_group",
        enable_auto_commit=True,
        auto_offset_reset="earliest",
        value_deserializer=lambda v: json.loads(v.decode("utf-8"))  # ✅ теперь словарь
    )

    await consumer.start()
    try:
        async for msg in consumer:
            data = msg.value  # тут уже dict
            print(f'{data=}')
            url = data["url"]
            text = data["text"]
            print(f"🔗 Получена ссылка: {url}")

            try:
                if TG_LINK_RE.match(url):
                    # === обработка Telegram-сообщения ===
                    # Здесь должен быть вызов твоего Telethon клиента (сейчас заглушка)
                    msg_dt = datetime.now(tz=timezone.utc)

                    news = {
                        "title": "",  # у телеги можно оставить пустой, весь текст идёт в description
                        "description": text,
                        "news_date": msg_dt.isoformat(),
                        "url": url,
                        "source": "Telegram",
                        "flag": "user_tg",  # 👈 отмечаем, что это от пользователя
                        "name": "tg_user_link"  # 👈 модуль-источник
                    }

                else:
                    # === обработка обычной статьи ===
                    article = extract_article(url)
                    if not article["description"]:
                        print(f"⚠️ Не удалось извлечь статью: {url}")
                        continue
                    news = {
                        "title": article["title"] or "",
                        "description": article["description"],
                        "news_date": datetime.now(tz=timezone.utc).isoformat(),
                        "url": article["url"],
                        "source": article["source"],
                        "flag": "user_web",  # 👈 новость прислал пользователь, но это сайт
                        "name": "user_link"  # 👈 модуль-источник
                    }
                # === Отправляем в Kafka
                await send_raw(news)
                print(f"📤 Отправлено в Kafka [news_raw]: {news['url']}")

            except Exception as e:
                print(f"❌ Ошибка при обработке {url}: {e}")

    finally:
        await consumer.stop()