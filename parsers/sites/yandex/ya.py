import asyncio
from datetime import datetime, timedelta
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
import re

MONTHS_RU = {
    "января": 1, "февраля": 2, "марта": 3, "апреля": 4,
    "мая": 5, "июня": 6, "июля": 7, "августа": 8,
    "сентября": 9, "октября": 10, "ноября": 11, "декабря": 12,
}

def parse_date_russian(raw: str) -> datetime:
    """Парсит дату в разных форматах из Дзен"""
    raw = raw.strip().lower()
    now = datetime.now()

    # --- "11 сентября в 11:12"
    match = re.match(r"(\d{1,2})\s+([а-я]+)\s+в\s+(\d{1,2}):(\d{2})", raw)
    if match:
        day, month_str, hour, minute = match.groups()
        month = MONTHS_RU.get(month_str)
        if month:
            return datetime(now.year, int(day), month, int(hour), int(minute))

    # --- "сегодня в 14:00"
    match = re.match(r"сегодня\s+в\s+(\d{1,2}):(\d{2})", raw)
    if match:
        hour, minute = map(int, match.groups())
        return datetime(now.year, now.month, now.day, hour, minute)

    # --- "вчера в 22:15"
    match = re.match(r"вчера\s+в\s+(\d{1,2}):(\d{2})", raw)
    if match:
        hour, minute = map(int, match.groups())
        yesterday = now - timedelta(days=1)
        return datetime(yesterday.year, yesterday.month, yesterday.day, hour, minute)

    # --- "54 минуты назад"
    match = re.match(r"(\d+)\s+минут", raw)
    if match:
        minutes = int(match.group(1))
        return now - timedelta(minutes=minutes)

    # --- "час назад" или "1 час назад"
    if raw.startswith("час назад"):
        return now - timedelta(hours=1)

    match = re.match(r"(\d+)\s+час", raw)  # 1 час, 2 часа, 5 часов назад
    if match:
        hours = int(match.group(1))
        return now - timedelta(hours=hours)

    # --- Если формат неизвестен
    return now


async def get_dzen_article(url: str) -> dict:
    result = {"title": None, "text": None, "source": None, "date": None}

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(url, timeout=60000)

        # скроллим вниз для подгрузки
        await page.evaluate("window.scrollBy(0, document.body.scrollHeight)")
        await asyncio.sleep(2)

        html = await page.content()
        await browser.close()

    soup = BeautifulSoup(html, "html.parser")

    # Заголовок
    h1 = soup.find("h1")
    if h1:
        result["title"] = h1.get_text(strip=True)

    # Текст
    digest_div = soup.find("div", {"data-testid": "story-digest"})
    if digest_div:
        spans = digest_div.find_all("span")
        text_blocks = [span.get_text(strip=True) for span in spans if span.get_text(strip=True)]
        result["text"] = "\n".join(text_blocks)

    # Источник
    source_span = soup.find("span", class_="news-story-block__source-text")
    if source_span:
        result["source"] = source_span.get_text(strip=True)

    # Дата
    time_div = soup.find("div", class_="news-story-block__time")
    if time_div:
        result["date"] = parse_date_russian(time_div.get_text(strip=True))
    else:
        result["date"] = datetime.now()

    return result


# ==== Тест ====
if __name__ == "__main__":
    url = "https://dzen.ru/news/story/95845998-dd60-52ad-8dc0-dcba869fc315?lang=ru&rubric=svo&fan=1&t=1757600225&tt=true&persistent_id=3221399944&cl4url=40ff4991fc92bdcd61d1b705c4958afb&story=839f64af-eabf-5156-98b9-daa638152401"
    article = asyncio.run(get_dzen_article(url))
    print("Заголовок:", article["title"])
    print("Источник:", article["source"])
    print("Дата:", article["date"])
    print("Текст:", article["text"])
