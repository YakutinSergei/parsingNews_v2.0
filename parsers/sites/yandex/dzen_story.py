# dzen_story.py
import asyncio
import re
from typing import Dict, List, Optional
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout
from playwright_stealth import stealth_async  # pip install playwright-stealth

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

def textnorm(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "")).strip()

ANTI_TEXTS = (
    "Подтвердите, что запросы отправляли вы, а не робот",
    "We need to make sure you are not a robot",
    "Подтвердите, что это вы",
)

CONSENT_TEXTS = (
    "Мы используем файлы cookie", "Используем файлы cookie",
    "Accept cookies", "This site uses cookies", "Принять все", "Согласен", "Принять"
)

CONSENT_BUTTON_SELECTORS = [
    "button:has-text('Принять')",
    "button:has-text('Согласен')",
    "button:has-text('Принять все')",
    "button:has-text('Accept')",
    "[data-testid='button']:has-text('Accept')",
    "button:has-text('Это я')",
    "button:has-text('Продолжить')",
]

async def _maybe_bypass_consent_or_robot(page) -> bool:
    """
    Пытаемся закрыть cookie/anti-bot экраны.
    Возвращает True, если кликнули что-то полезное.
    """
    clicked = False
    # Попробуем найти характерные тексты на странице (cookie/robot)
    page_text = (await page.content())  # быстрый путь; для точности можно page.inner_text("body")
    if any(t in page_text for t in ANTI_TEXTS) or any(t in page_text for t in CONSENT_TEXTS):
        for sel in CONSENT_BUTTON_SELECTORS:
            try:
                btn = await page.query_selector(sel)
                if btn:
                    await btn.click()
                    clicked = True
                    # ждём возможный редирект/перерисовку
                    await page.wait_for_timeout(1200)
                    break
            except Exception:
                continue
    return clicked

async def _prepare_context(p, ua: str, storage_state_path: str = "yandex_storage.json"):
    """
    Создаёт контекст Playwright. Если есть сохранённая сессия — подключаем.
    """
    # Если storage_state существует — подключим его
    context_kwargs = dict(
        user_agent=ua,
        viewport={"width": 1366, "height": 900},
        locale="ru-RU",
        extra_http_headers={"Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7"},
        storage_state=storage_state_path if Path(storage_state_path).exists() else None,
    )
    context = await p.chromium.new_context(**context_kwargs)
    return context

from pathlib import Path

async def parse_dzen_link(url: str, retries: int = 2, storage_state: str = "yandex_storage.json") -> Dict:
    """
    Открывает страницу истории Дзена, обходит consent/anti-bot (насколько возможно),
    извлекает заголовок/описание/параграфы. Сессию сохраняет в storage_state.
    """
    ua = get_ua()

    async with async_playwright() as p:
        # ВНИМАНИЕ: используем persistent storage_state
        context = await _prepare_context(p, ua, storage_state_path=storage_state)
        page = await context.new_page()
        await stealth_async(page)  # скрыть webdriver следы

        page.set_default_timeout(35000)

        # Блокируем только тяжёлое
        async def _route(route):
            if route.request.resource_type in ("image", "media", "font"):
                await route.abort()
            else:
                await route.continue_()
        await page.route("**/*", _route)

        async def _attempt_once() -> Optional[str]:
            await page.goto(url, wait_until="domcontentloaded")
            await asyncio.sleep(1.2)

            # Попробуем закрыть cookie/robot экраны, если есть
            bypassed = await _maybe_bypass_consent_or_robot(page)
            if bypassed:
                # Подождём, возможно был редирект/перерисовка
                await asyncio.sleep(1.0)

            # Если всё ещё заглушка — ещё раз пробуем
            html = await page.content()
            if any(t in html for t in ANTI_TEXTS):
                # иногда на антибот-странице кнопка ниже
                # сделаем ещё один проход по кнопкам
                again = await _maybe_bypass_consent_or_robot(page)
                await asyncio.sleep(1.0)
                html = await page.content()

            # Ждём реальный контент
            try:
                await page.wait_for_selector("article, h1, main", timeout=5000)
            except PlaywrightTimeout:
                pass

            return await page.content()

        html = None
        for i in range(retries + 1):
            html = await _attempt_once()
            # если снова заглушка — попробуем ещё раз
            if html and not any(t in html for t in ANTI_TEXTS):
                break
            await asyncio.sleep(0.8 * (i + 1))

        # Сохраним актуальный storage_state, чтобы в след. раз не ловить баннер
        try:
            await context.storage_state(path=storage_state)
        except Exception:
            pass

        await context.close()

    # Если так и осталась заглушка — вернём спец. статус
    if not html or any(t in html for t in ANTI_TEXTS):
        return {"url": url, "title": None, "description": None, "paragraphs": [], "error": "anti-bot/consent"}

    soup = BeautifulSoup(html, "lxml")

    og = {m.get("property")[3:]: m.get("content", "") for m in soup.find_all("meta", property=True) if m.get("property", "").startswith("og:")}
    tw = {m.get("name")[8:]: m.get("content", "") for m in soup.find_all("meta", attrs={"name": True}) if m.get("name", "").startswith("twitter:")}

    h1 = soup.find("h1")
    title = textnorm(h1.get_text(" ")) if h1 else (og.get("title") or tw.get("title") or textnorm(soup.title.string if soup.title else ""))

    description = og.get("description") or tw.get("description")
    if not description:
        meta_desc = soup.find("meta", attrs={"name": "description"})
        if meta_desc and meta_desc.get("content"):
            description = textnorm(meta_desc["content"])

    paragraphs: List[str] = []
    seen_par = set()
    article = soup.find("article")
    containers = [article] if article else []
    if not containers:
        containers = soup.find_all("div", attrs={"class": re.compile(r"(content|article|story|text|body)", re.I)})

    if containers:
        for c in containers:
            for p in c.find_all("p"):
                t = textnorm(p.get_text(" "))
                if t and t not in seen_par:
                    seen_par.add(t)
                    paragraphs.append(t)
    else:
        for p in soup.find_all("p"):
            t = textnorm(p.get_text(" "))
            if t and t not in seen_par:
                seen_par.add(t)
                paragraphs.append(t)

    return {
        "url": url,
        "title": title or None,
        "description": description or None,
        "paragraphs": paragraphs,
    }
