from datetime import datetime
import aiohttp
from bs4 import BeautifulSoup
from fake_useragent import UserAgent


async def parse_tass(url: str) -> str:
    """
    Асинхронный парсер новости с сайта ТАСС.
    Возвращает текст статьи или пустую строку при ошибке.
    """
    try:
        # 1. Генерируем случайный User-Agent
        ua = UserAgent()
        headers = {"User-Agent": ua.random}

        # 2. Отправляем запрос через aiohttp
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, timeout=10) as resp:
                if resp.status != 200:
                    raise ValueError(f"Ошибка HTTP {resp.status}")

                html = await resp.text()

        # 3. Парсим HTML
        soup = BeautifulSoup(html, "lxml")

        # 4. Достаём текст статьи
        texts = soup.find_all("span", class_="tass_pkg_text-oEhbR")
        if not texts:
            texts = soup.find_all('p', class_="Paragraph_paragraph__F_jNb")
            if not texts:
                raise ValueError("⚠️ Не найден текст статьи (возможно, изменился CSS-класс)")


        content = " ".join(t.get_text(strip=True) for t in texts)

        return content

    except Exception as e:
        print(f"[TASS parser error] {url}: {e}")
        return ""
