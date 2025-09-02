import aiohttp
import asyncio
import feedparser
import xml.etree.ElementTree as ET

import datetime
import time

from dateutil import parser as dateparser
from core.redis_client import redis_client
from parsers.RSS import RSS_URLS
from parsers.RSS.ria_rss import parse_ria
from parsers.RSS.tass_rss import parse_tass
from producer import send_raw


async def fetch(session, url: str) -> str:
    """
    Загружает RSS по URL.
    """
    async with session.get(url, timeout=15) as r:
        return await r.text()


async def rss_parser():
    print('RSS parser')
    async with aiohttp.ClientSession() as session:
        while True:
            # создаём список задач — каждый RSS обрабатывается отдельно
            tasks = [process_rss(session, rss) for rss in RSS_URLS]
            await asyncio.gather(*tasks)

            # ждём 5 минут и запускаем новый цикл
            await asyncio.sleep(120)

async def process_rss(session, rss):
    rss_url = rss[0]
    rss_id = rss[1]
    rss_name = rss[2]

    try:
        # 1. Скачиваем XML
        data = await fetch(session, rss_url)
        feed = feedparser.parse(data)
        root = ET.fromstring(data)

        # 2. Перебираем новости последовательно
        for entry in feed.entries:
            url = entry.link
            redis_key = f"seen_urls:{rss_id}"

            # Проверяем уникальность
            added = await redis_client.sadd(redis_key, url)
            if added == 0:
                print(f"⚠️ [{rss_name}] встречена старая новость → прекращаем обработку")
                break

            # 3. Контент для конкретных источников
            if rss_id == 1: content = await parse_ria(url)  # РИА Новости
            elif rss_id == 2: content = await parse_tass(url)  # ТАСС
            elif rss_id == 5: # RBC
                ns = {"rbc": "https://www.rbc.ru"}

                guid = entry.get("guid")
                item = None
                for it in root.findall(".//item"):
                    if it.findtext("guid") == guid or it.findtext("link") == url:
                        item = it
                        break

                if item is not None:
                    full = item.find("rbc:full-text", ns)
                    if full is not None and full.text:
                        content = full.text
                    else:
                        content = entry.get("description", "")
            elif rss_id == 6:  # Взгляд
                ns = {"yandex": "http://news.yandex.ru"}

                # ищем item с таким guid или link
                guid = entry.get("guid")
                item = None
                for it in root.findall(".//item"):
                    if it.findtext("guid") == guid or it.findtext("link") == url:
                        item = it
                        break
                if item is not None:
                    full = item.find("yandex:full-text", ns)
                    if full is not None and full.text:
                        content = full.text
                    else:
                        content = entry.get("description", "")

                else:
                    content = entry.get("description", "")
            elif rss_id == 7: #Взгляд
                root = ET.fromstring(data)
                ns = {"content": "http://purl.org/rss/1.0/modules/content/"}

                guid = entry.get("guid")
                item = None
                for it in root.findall(".//item"):
                    if it.findtext("guid") == guid or it.findtext("link") == url:
                        item = it
                        break

                if item is not None:
                    full = item.find("content:encoded", ns)
                    if full is not None and full.text:
                        content = full.text
                    else:
                        content = entry.get("description", "")
                else:
                    content = entry.get("description", "")
            else:
                content = entry.get("description", "")

            # 4. Формируем объект новости
            news = {
                "title": entry.title,
                "description": content,
                "news_date": normalize_date_str(entry),
                "url": url,
                "source": rss_name,
                "flag": "raw",
                "name": "rss_parser"
            }

            # 5. Отправляем в Kafka
            await send_raw(news)
            print(f"📤 [{rss_name}] новая новость отправлена: {entry.title[:60]}")

    except Exception as e:
        print(f"[RSS error] {rss_name} ({rss_url}): {e}")



def normalize_date_str(entry) -> str:
    """
    Приводит дату из RSS к строке в формате ISO-8601 (YYYY-MM-DDTHH:MM:SS).
    """
    # 1. Если есть published_parsed (struct_time)
    if entry.get("published_parsed"):
        dt = datetime.datetime(*entry.published_parsed[:6])
        return dt.isoformat()

    # 2. Если есть published (строка)
    if entry.get("published"):
        try:
            dt = dateparser.parse(entry.published)
            return dt.replace(tzinfo=None).isoformat()
        except Exception:
            pass

    # 3. fallback → текущее время
    return datetime.datetime.utcnow().isoformat()