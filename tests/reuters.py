import asyncio
import random
import re
from datetime import datetime, timedelta

from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
from fake_useragent import UserAgent

# создаём объект fake-useragent — он подставит случайные User-Agent строки настоящих браузеров
ua = UserAgent()

def get_desktop_ua():
    """Возвращает случайный desktop User-Agent (без мобильных и планшетов)."""
    while True:
        agent = ua.random
        if not re.search(r"(Mobile|Android|iPhone|iPad|iPod)", agent, re.IGNORECASE):
            return agent


async def parse_dzen_article(browser, url):
    """
    Открывает новость Dzen и извлекает:
    - заголовок
    - текст статьи
    - автора
    - изображения
    Для каждой статьи создаётся отдельный контекст и свой User-Agent.
    """

    # 🧭 Генерация случайного desktop User-Agent
    random_ua = get_desktop_ua()

    # 🧩 Создаём новый контекст браузера (новая сессия)
    context = await browser.new_context(
        user_agent=random_ua,
        viewport={
            "width": random.randint(1280, 1920),
            "height": random.randint(720, 1080)
        },
        locale=random.choice(["ru-RU", "en-US", "uk-UA"]),
    )

    page = await context.new_page()

    result = {
        "url": url,
        "user_agent": random_ua,
        "title": None,
        "text": None,
        "author": None,
        "images": [],
    }

    try:
        print(f"🌐 Открываем статью: {url}")

        # 🔹 Загружаем страницу (без ожидания полной тишины сети)
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=60000)
        except Exception:
            print("⚠ Медленная загрузка, пробуем с 'load'")
            try:
                await page.goto(url, wait_until="load", timeout=60000)
            except Exception:
                print("❌ Не удалось загрузить страницу Dzen")
                return None

        # Небольшая пауза — ждём прогрузку контента
        await asyncio.sleep(random.uniform(2, 4))

        # -------------------------
        # 🟩 Заголовок
        # -------------------------
        title_el = await page.query_selector("h1, [data-testid='news-headline'], .article__title")
        if title_el:
            result["title"] = (await title_el.inner_text()).strip()

        # -------------------------
        # 🟩 Контент статьи
        # -------------------------
        article_body = await page.query_selector("[data-testid='article-body']")
        if article_body:
            blocks = await article_body.query_selector_all("[data-testid='article-render__block']")
            content_parts = []
            for block in blocks:
                block_type = await block.get_attribute("data-block-type")
                if block_type == "image":
                    continue
                text = await block.inner_text()
                if text:
                    clean = " ".join(text.split())
                    content_parts.append(clean)
            if content_parts:
                result["text"] = "\n\n".join(content_parts).strip()

        # -------------------------
        # 🟩 Автор
        # -------------------------
        author_el = await page.query_selector("[class*='author'], [data-testid='author-name']")
        if author_el:
            author_text = (await author_el.inner_text()).strip()
            if author_text.lower().startswith("автор:"):
                author_text = author_text.split(":", 1)[1].strip()
            result["author"] = author_text


        # 🧾 Лог
        print(f"✅ Собрано: {result['title'] or '(без заголовка)'} | UA: {result['user_agent'][:35]}")

    except Exception as e:
        print(f"⚠ Ошибка при парсинге статьи {url}: {e}")
        result["error"] = str(e)

    finally:
        await page.close()
        await context.close()

    return result


async def parse_dzen_news(hours_back=5):
    """
    Асинхронный парсер новостей с Dzen.ru (раздел 'Хронологическая лента')
    hours_back — за какой период времени брать новости (по умолчанию 5 часов)
    """

    # URL ленты новостей Dzen
    url = "https://dzen.ru/news/rubric/chronologic"

    # текущая дата и время минус N часов назад (для фильтрации свежих новостей)
    cutoff_time = datetime.now() - timedelta(hours=hours_back)

    # сюда будем складывать найденные новости
    results = []

    # выбираем случайный User-Agent (чтобы не детектировался бот)
    random_ua = get_desktop_ua()
    print(f"🧭 Используем случайный User-Agent:\n{random_ua}\n")

    # создаём асинхронный контекст Playwright
    async with async_playwright() as p:
        # запускаем браузер Chromium
        # headless=True — без графического интерфейса (работает в фоне)
        browser = await p.chromium.launch(headless=False)

        # создаём новый контекст браузера (новая сессия)
        # передаём в него настройки для маскировки под реального пользователя
        context = await browser.new_context(
            user_agent=random_ua,                   # подставляем случайный UA
            viewport={                              # имитация разрешения экрана пользователя
                "width": random.randint(1280, 1920),  # случайная ширина окна
                "height": random.randint(1000, 1280)   # случайная высота окна
            },
            locale=random.choice(["ru-RU", "en-US", "uk-UA"]),  # случайная локаль пользователя
        )

        # создаём новую вкладку (страницу)
        page = await context.new_page()

        # задаём дополнительные HTTP-заголовки, чтобы имитировать реальный браузер
        await page.set_extra_http_headers({
            "Accept-Language": "ru-RU,ru;q=0.9,en;q=0.8",  # языковые предпочтения
            "Referer": "https://dzen.ru/",                 # с какой страницы пришёл пользователь
            "DNT": "1",                                    # «Do Not Track» — не отслеживать
        })

        try:
            print("🌐 Загружаем страницу Dzen...")
            # Переходим по URL, ждём пока страница полностью загрузится
            # wait_until="networkidle" — ждём пока сеть станет «пустой» (все запросы выполнены)
            # timeout=90000 — максимальное время ожидания 90 секунд
            # Загружаем страницу без ожидания полной тишины сети
            try:
                await page.goto(url, wait_until="domcontentloaded", timeout=60000)
            except Exception:
                print("⚠ Первичная загрузка заняла слишком долго, пробуем снова с 'load'")
                try:
                    await page.goto(url, wait_until="load", timeout=60000)
                except Exception:
                    print("❌ Не удалось загрузить страницу Dzen даже со вторым методом")
                    return []

            # Делаем небольшую паузу, чтобы эмулировать чтение человеком
            await asyncio.sleep(random.uniform(2, 4))

            # Ждём, пока на странице появятся новости (элементы <article>)
            await page.wait_for_selector("article", timeout=20000)
            print("✅ Страница загружена, начинаем сбор новостей...\n")

        except Exception as e:
            # Если страница не загрузилась или сайт ответил ошибкой
            print(f"⚠ Ошибка загрузки страницы: {e}")
            await browser.close()
            return []  # возвращаем пустой список, чтобы не ломать программу

        # Прокручиваем страницу, чтобы подгрузились дополнительные новости (lazy-loading)
        last_height = 0  # сохраняем высоту страницы перед прокруткой

        for _ in range(random.randint(2,5)):  # случайное количество итераций (8–14)
            await page.mouse.wheel(0, -4000) # прокрутка вверх
            await asyncio.sleep(random.uniform(1, 2))

        # Получаем все карточки новостей по data-testid
        articles = await page.query_selector_all("article[data-testid='card-horizontal-meta']")
        count = await page.eval_on_selector_all("article", "els => els.length")
        print(f"🔍 Найдено элементов <article>: {count}")
        for a in articles:
            try:
                # Заголовок
                title_el = await a.query_selector("[data-testid='card-horizontal-meta-title']")
                title = await title_el.inner_text() if title_el else None

                sourse_el = await a.query_selector("[data-testid='news-site--card-horizontal-news-meta__author-1D']")
                source = await sourse_el.inner_text() if sourse_el else None

                # Описание
                desc_el = await a.query_selector("[data-testid='card-description']")
                description = await desc_el.inner_text() if desc_el else None

                # Ссылка
                link_el = await a.query_selector("a[data-testid='card-horizontal-meta-link']")
                href = await link_el.get_attribute("href") if link_el else None

                # Время публикации
                time_el = await a.query_selector("[class*='timestamp']")
                time_text = await time_el.inner_text() if time_el else None

                # Парсинг времени
                published = None
                if time_text:
                    t = time_text.lower().replace("\xa0", " ").strip()
                    if "мин" in t:
                        mins = int(t.split()[0])
                        published = datetime.now() - timedelta(minutes=mins)
                    elif "час" in t:
                        hrs = int(t.split()[0])
                        published = datetime.now() - timedelta(hours=hrs)
                    elif "вчера" in t:
                        published = datetime.now() - timedelta(days=1)

                if published and published >= cutoff_time:
                    description = await parse_dzen_article(browser, href)
                    results.append({
                        "title": title or "",
                        "description": description or "",
                        "link": href or "",
                        "source": source or "",
                        "published": published.strftime("%Y-%m-%d %H:%M"),
                    })
                else:
                    # Для отладки: покажем карточки, которые не прошли фильтр
                    print(f"🕐 Пропущена: {title} — {time_text}")

            except Exception as e:
                print("⚠ Ошибка при парсинге карточки:", e)

        # Закрываем браузер (важно освобождать ресурсы)
        await browser.close()

    # Сортируем новости по времени — от новых к старым
    results.sort(key=lambda x: x["published"], reverse=True)

    # Возвращаем список словарей с новостями
    return results


# Главная функция, запускающая парсер
async def main():
    # Запускаем парсер и получаем список новостей за последние 5 часов
    news = await parse_dzen_news(hours_back=5)
    print(f"📰 Найдено {len(news)} новостей за последние 5 часов:\n")

    # Выводим результат в консоль
    for n in news:
        print(f"[{n['published']}] {n['title']}")
        print(f"[{n['source']}]")
        print(f"→ {n['link']}\n")


# Точка входа программы
if __name__ == "__main__":
    # asyncio.run запускает асинхронную функцию main()
    asyncio.run(main())



