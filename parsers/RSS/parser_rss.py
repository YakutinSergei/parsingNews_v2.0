import random

import aiohttp
import asyncio
import feedparser

from database.config import settings
from kafka_producer import send_to_kafka
from config import logger  # если логгер у тебя в config.py
from parsers.RSS import RSS_URLS


async def fetch_and_parse(session, url: str):
    """
    Загружает RSS, парсит и отправляет новости в Kafka.
    """
    try:
        async with session.get(url[0], timeout=10) as r:
            data = await r.text()
        # Парсим XML через feedparser
        feed = feedparser.parse(data)
        # Берём первые 3 новости (пример)
        for entry in feed.entries[:3]:
            '''
            ТУТ ПРОВЕРКА НА ПОВТОРЫ В БД
            '''

            '''
            Тут функция парсинга со страницы если нет такой новости в БД
            '''
            news = {
                "source": url,
                "type": "rss",
                "title": entry.title,
                "url": entry.link,
                "text": entry.get("summary", "")
            }
            await send_to_kafka(settings.KAFKA_TOPIC_RAW, news)

        logger.info(f"✅ RSS {url} обработан ({len(feed.entries)} новостей)")

    except Exception as e:
        logger.error(f"Ошибка RSS {url}: {e}")


async def rss_parser():
    """
    Основной цикл:
    - параллельно обрабатывает все RSS (через gather)
    - повторяется каждые 5 минут
    """
    async with aiohttp.ClientSession() as session:
        while True:
            tasks = [fetch_and_parse(session, url) for url in RSS_URLS]

            # запускаем все RSS одновременно
            await asyncio.gather(*tasks)

            logger.info("RSS-парсер завершил цикл, спим 5 минут...")
            await asyncio.sleep(300)
