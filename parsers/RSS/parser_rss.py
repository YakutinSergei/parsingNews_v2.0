import aiohttp
import asyncio
import feedparser
import xml.etree.ElementTree as ET

import datetime

import requests
from bs4 import BeautifulSoup
from dateutil import parser as dateparser
from core.redis_client import redis_client
from parsers.RSS import RSS_URLS
from parsers.RSS.ria_rss import parse_ria
from parsers.RSS.tass_rss import parse_tass
from parsers.text_translator import translate_large_text
from producer import send_raw
from fake_useragent import UserAgent

ua = UserAgent()
headers = {"User-Agent": ua.random}  # случайный User-Agent

async def fetch(session, url: str, use_proxy: int = 0) -> str:
    """
    Загружает RSS по URL.
    Если use_proxy == 1 → подключаем прокси.
    """
    kwargs = {"timeout": 15}
    if use_proxy:
        # пример: HTTP(S) прокси
        kwargs["proxy"] = "http://bPLBfY:bN17yH@196.17.67.95:8000"

        # если SOCKS5:
        # kwargs["proxy"] = "socks5://login:password@127.0.0.1:1080"

    async with session.get(url, **kwargs) as r:
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
    rss_url, rss_id, rss_name, use_proxy = rss

    try:
        # 1. Скачиваем XML
        data = await fetch(session, rss_url, use_proxy=use_proxy)
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
            if rss_id in SELECTORS:
                content = get_news_content(url, rss_id)
            elif rss_id in SELECTORS_globalvoices:
                title = await translate_large_text(entry.get("title", ""))
                raw_content = safe_get_text(entry.get("content", entry.get("description", "")))
                content = await translate_large_text(raw_content)
            elif rss_id == 1: content = await parse_ria(url)  # РИА Новости
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
                "title": clean_for_telegram(entry.title),
                "description": clean_for_telegram(content),
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

import re

def clean_for_telegram(text: str) -> str:
    if not text:
        return ""

    # заменяем <br> и <br/> на перенос строки
    text = re.sub(r"<br\s*/?>", "\n", text, flags=re.IGNORECASE)

    # удаляем все остальные HTML-теги целиком
    text = re.sub(r"<[^>]+>", "", text)

    # убираем лишние пробелы и пустые строки
    text = re.sub(r"\n\s*\n+", "\n\n", text).strip()

    return text


# 🔹 Словарь селекторов
SELECTORS = {
    13: ("div", "news-detail"),
    14: ("div", "field field--name-body field--type-text-with-summary field--label-hidden lightgallery accent-links field__item"),
    15: ("div", "article__body"),
    16: ("div", "single-news__all-text"),
    17: ("div", "NYC0Ro8v fontSize_0"),
    18: ("div", "article_text_wrapper js-search-mark"),

}

SELECTORS_globalvoices = {
    19: ('western-europe'),
    20: ('middle-east-north-africa'),
    21: ('north-america'),
    22: ('latin-america'),
    23: ('eastern-central-europe'),
    24: ('central-asia-caucasus'),
    25: ('east-asia'),
    26: ('war-conflict'),
    27: ('technology'),
    28: ('science'),
    29: ('politics'),
    30: ('health'),
    31: ('development'),
    32: ('breaking-news'),
    33: ('disaster'),
}
def get_news_content(url: str, key: str) -> str:
    """
    Универсальный парсер новостей.
    Принимает url и ключ для выбора нужного селектора.
    """
    try:
        headers = {"User-Agent": ua.random}
        response = requests.get(url, headers=headers, timeout=10)
        response.encoding = "utf-8"

        soup = BeautifulSoup(response.text, "lxml")

        if key not in SELECTORS:
            return f"Ключ '{key}' не найден в SELECTORS"

        tag, class_name = SELECTORS[key]
        block = soup.find(tag, class_=class_name)

        if not block:
            return f"Контент по ключу '{key}' не найден"

        # Для вложенного div (как в "example")
        inner_div = block.find("div")
        return (inner_div.text if inner_div else block.text).strip()

    except Exception as e:
        return f"Ошибка при парсинге: {e}"


# Функция для анализа новостей
def analyze_news(news_text, word_list):
    for keyword in word_list:
        match = re.search(keyword, news_text, re.IGNORECASE)
        if match:
            return keyword  # Вернуть ключевое слово и совпавшую фразу

    return None


def safe_get_text(value) -> str:
    """
    Универсальное извлечение текста из RSS-полей.
    """
    if isinstance(value, list):
        # feedparser часто возвращает список словарей с "value"
        texts = []
        for v in value:
            if isinstance(v, dict) and "value" in v:
                texts.append(v["value"])
            else:
                texts.append(str(v))
        return " ".join(texts)
    if value is None:
        return ""
    return str(value)
