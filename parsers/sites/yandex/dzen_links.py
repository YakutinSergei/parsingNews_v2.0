# dzen_links.py
import json
import asyncio
from pathlib import Path
from typing import Dict, List, Tuple
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout
from playwright_stealth import stealth_async

SEEN_FILE = Path("seen_links.json")

# --- fake UA ---
try:
    from fake_useragent import UserAgent
    _ua = UserAgent()
    def get_ua() -> str:
        return _ua.chrome
except Exception:
    import random
    DESKTOP_UA = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_0) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
    ]
    def get_ua() -> str:
        return random.choice(DESKTOP_UA)

def load_seen() -> set:
    if SEEN_FILE.exists():
        try:
            return set(json.loads(SEEN_FILE.read_text(encoding="utf-8")))
        except Exception:
            return set()
    return set()

def save_seen(seen: set) -> None:
    SEEN_FILE.write_text(json.dumps(sorted(seen), ensure_ascii=False, indent=2), encoding="utf-8")

def make_absolute(url: str, base: str = "https://dzen.ru") -> str:
    url = (url or "").strip()
    if not url:
        return url
    if url.startswith("//"):
        return "https:" + url
    if url.startswith("/"):
        return urljoin(base, url)
    return url

def is_dzen_story(url: str) -> bool:
    try:
        p = urlparse(url)
        return p.netloc.endswith("dzen.ru") and p.path.startswith("/news/story/")
    except Exception:
        return False

async def fetch_dzen_html(filename: str = "dzen_page.html", scrolls: int = 10, storage_state: str = "yandex_storage.json") -> str:
    ua = get_ua()
    async with async_playwright() as p:
        context_kwargs = dict(
            user_agent=ua,
            viewport={"width": 1366, "height": 900},
            locale="ru-RU",
            extra_http_headers={"Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7"},
            storage_state=storage_state if Path(storage_state).exists() else None,
        )
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(**context_kwargs)
        page = await context.new_page()
        await stealth_async(page)

        await page.goto("https://dzen.ru/news", timeout=60000)

        # Попробуем закрыть cookie/consent, если всплыло
        try:
            for sel in ("button:has-text('Принять')", "button:has-text('Согласен')", "button:has-text('Accept')"):
                btn = await page.query_selector(sel)
                if btn:
                    await btn.click()
                    await asyncio.sleep(0.8)
                    break
        except Exception:
            pass

        # ждём карточки
        try:
            await page.wait_for_selector("a.news-site--card-top-avatar__rootElement-1U, a[data-testid='card-link']", timeout=15000)
        except PlaywrightTimeout:
            pass

        for _ in range(scrolls):
            await page.evaluate("window.scrollBy(0, document.body.scrollHeight)")
            await asyncio.sleep(0.8)

        content = await page.content()
        Path(filename).write_text(content, encoding="utf-8")

        # сохраним storage_state после принятия cookies
        try:
            await context.storage_state(path=storage_state)
        except Exception:
            pass

        await context.close()
        await browser.close()

    return filename

def parse_dzen_html(filename: str = "dzen_page.html") -> Dict[str, List[Dict[str, str]]]:
    html = Path(filename).read_text(encoding="utf-8")
    soup = BeautifulSoup(html, "html.parser")

    result: Dict[str, List[Dict[str, str]]] = {}
    current_category = "Главное"

    for element in soup.find_all(["h2", "a"]):
        if element.name == "h2" and "news-site--text__h2-19" in element.get("class", []):
            current_category = element.get_text(strip=True) or current_category
            result.setdefault(current_category, [])
        elif element.name == "a" and (element.get("data-testid") == "card-link" or "news-site--card-top-avatar__rootElement-1U" in element.get("class", [])):
            link = make_absolute(element.get("href"))
            title = element.get_text(" ", strip=True)
            if title and link and is_dzen_story(link):
                result.setdefault(current_category, []).append({"title": title, "url": link})
    return result

async def get_new_links(scrolls: int = 12) -> Tuple[Dict[str, List[Dict[str, str]]], List[str]]:
    """
    Возвращает:
      - словарь {категория: [{title, url}, ...]} только по НОВЫМ ссылкам,
      - плоский список новых URL (для удобства).
    Также обновляет seen_links.json.
    """
    filename = await fetch_dzen_html("dzen_page.html", scrolls=scrolls)
    categories = parse_dzen_html(filename)

    seen = load_seen()
    new_categories: Dict[str, List[Dict[str, str]]] = {}
    flat_new: List[str] = []

    for cat, items in categories.items():
        for item in items:
            url = item["url"]
            if url in seen:
                continue
            new_categories.setdefault(cat, []).append(item)
            flat_new.append(url)
            seen.add(url)

    save_seen(seen)
    return new_categories, flat_new