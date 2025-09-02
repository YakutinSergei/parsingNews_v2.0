from datetime import datetime
import aiohttp
from bs4 import BeautifulSoup
from fake_useragent import UserAgent


async def parse_ria(url: str):
    """
    Асинхронный парсер новостей РИА Новости.

    Аргументы:
        url (str): ссылка на новость РИА.

    Возвращает:
        str: текст статьи (склеенный из абзацев),
        или None, если парсинг не удался.
    """
    try:
        # 1. Генерируем случайный User-Agent
        ua = UserAgent()
        headers = {"User-Agent": ua.random}

        # 2. Делаем асинхронный HTTP-запрос через aiohttp
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, timeout=10) as resp:
                if resp.status != 200:
                    raise ValueError(f"Ошибка HTTP {resp.status}")
                html = await resp.text()

        # 3. Парсим HTML с помощью BeautifulSoup
        soup = BeautifulSoup(html, "lxml")

        # 4. Достаём блок с основным содержимым статьи
        article_divs = soup.find("div", class_="layout-article__main-over")
        if not article_divs:
            raise ValueError("Не найден блок с текстом статьи")

        paragraphs = article_divs.find_all("div", class_="article__text")
        if not paragraphs:
            raise ValueError("Не найдены абзацы статьи")

        # 5. Склеиваем абзацы в единый текст
        content = " ".join(p.get_text(strip=True) for p in paragraphs)

        return content

    except Exception as e:
        # Ошибки логируем, возвращаем None
        print(f"[RIA parser error] {url}: {e}")
        return None
