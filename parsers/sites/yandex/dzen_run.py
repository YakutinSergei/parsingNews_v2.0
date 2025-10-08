import asyncio
import os
import json
from typing import List, Dict, Any, Optional

from dzen_links import get_new_links  # из предыдущего файла
from dzen_story import parse_dzen_link  # из предыдущего файла
from parsers.sites.yandex.ya import get_dzen_article

SEEN_FILE = "seen_links.json"


def load_seen_links() -> set:
    """Загрузить уже обработанные ссылки"""
    if os.path.exists(SEEN_FILE):
        with open(SEEN_FILE, "r", encoding="utf-8") as f:
            return set(json.load(f))
    return set()


def save_seen_links(links: set):
    """Сохранить список обработанных ссылок"""
    with open(SEEN_FILE, "w", encoding="utf-8") as f:
        json.dump(list(links), f, ensure_ascii=False, indent=2)


async def collect_dzen_news(
    scrolls: int = 12,
    max_concurrency: int = 4,
    limit_total: Optional[int] = None,
    save_to: Optional[str] = "dzen_news.json",
) -> List[Dict[str, Any]]:
    """
    ЕДИНАЯ ФУНКЦИЯ ЗАПУСКА.
    1) Собирает НОВЫЕ ссылки с главной Дзен.Новости.
    2) По этим ссылкам парсит заголовок/описание/текст.

    :param scrolls: сколько «проскроллить» главную
    :param max_concurrency: параллельность при парсинге новостей
    :param limit_total: максимальное количество ссылок для обработки (None — без лимита)
    :param save_to: путь для сохранения результата в JSON (None — не сохранять)
    :return: список словарей с данными новостей
    """
    # шаг 1: собрать ссылки
    categories, flat_new = await get_new_links(scrolls=scrolls)
    print(flat_new)
    print(flat_new[:10])

    # шаг 2: фильтруем новые
    seen_links = load_seen_links()
    new_links = [link for link in flat_new if link not in seen_links]

    if not new_links:
        print("🔹 Новых ссылок нет")
        return []

    if limit_total:
        new_links = new_links[:limit_total]

    print(f"🔹 Найдено {len(new_links)} новых ссылок")

    # шаг 3: параллельный парсинг
    semaphore = asyncio.Semaphore(max_concurrency)

    async def sem_task(url):
        async with semaphore:
            return await get_dzen_article(url)

    tasks = [asyncio.create_task(sem_task(url)) for url in new_links]
    news_data = await asyncio.gather(*tasks)

    # шаг 4: обновляем список seen
    seen_links.update(new_links)
    save_seen_links(seen_links)

    # шаг 5: сохраняем результат (опционально)
    if save_to:
        with open(save_to, "w", encoding="utf-8") as f:
            json.dump(news_data, f, ensure_ascii=False, indent=2)

    return news_data


# ==== Тест ====
if __name__ == "__main__":
    async def main():
        news = await collect_dzen_news(limit_total=5)
        for n in news:
            print("—", n.get("title"), n.get("date"))

    asyncio.run(main())