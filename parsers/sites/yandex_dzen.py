import asyncio
from pathlib import Path
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup


async def fetch_dzen_html(filename: str = "dzen_page.html", scrolls: int = 10) -> str:
    """
    Загружает страницу Дзен.Новости через Playwright и сохраняет её HTML в файл.
    :param filename: куда сохранить HTML
    :param scrolls: сколько раз проскроллить страницу вниз
    :return: путь к сохранённому файлу
    """
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        await page.goto("https://dzen.ru/news", timeout=60000)

        # ждём появления хотя бы одной карточки
        await page.wait_for_selector("a.news-site--card-top-avatar__rootElement-1U", timeout=15000)

        # автоскролл для подгрузки новостей
        for _ in range(scrolls):
            await page.evaluate("window.scrollBy(0, document.body.scrollHeight)")
            await asyncio.sleep(1)

        # получаем финальный HTML
        content = await page.content()
        Path(filename).write_text(content, encoding="utf-8")

        await browser.close()

    return filename


def parse_dzen_html(filename: str = "dzen_page.html") -> dict:
    """
    Парсит сохранённый HTML через BeautifulSoup.
    Разбивает новости по категориям (Главное, Политика, Экономика и т.п.)
    """
    html = Path(filename).read_text(encoding="utf-8")
    soup = BeautifulSoup(html, "html.parser")

    result = {}
    current_category = "Главное"  # до первого <h2> идут главные новости

    # Перебираем все h2 и карточки новостей
    for element in soup.find_all(["h2", "a"]):
        # нашли категорию
        if element.name == "h2" and "news-site--text__h2-19" in element.get("class", []):
            current_category = element.get_text(strip=True)
            result.setdefault(current_category, [])

        # нашли карточку
        elif element.name == "a" and element.get("data-testid") == "card-link":
            link = element.get("href")
            title_tag = element.find("p", class_="news-site--card-top-avatar__text-SL")
            title = title_tag.get_text(strip=True) if title_tag else None
            if title and link:
                result.setdefault(current_category, []).append(
                    {"title": title, "url": link}
                )

    return result


async def main():
    # 1. Загружаем страницу и сохраняем HTML
    filename = await fetch_dzen_html("dzen_page.html", scrolls=15)

    # 2. Парсим сохранённый файл
    categories = parse_dzen_html(filename)

    # 3. Выводим результат
    for category, news in categories.items():
        print(f"\n=== {category} ({len(news)} новостей) ===")
        for n in news:  # для примера первые 5 новостей
            print(f"- {n['title']} -> {n['url']}")


if __name__ == "__main__":
    asyncio.run(main())
