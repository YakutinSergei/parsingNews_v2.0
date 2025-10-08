# Ваш файл с парсером телеграм (telegram_parser.py)
import json
import logging
import re
import asyncio
from datetime import datetime, timezone

from telethon import TelegramClient, events
from telethon.tl import types

from environs import Env
from io import BytesIO


from bs4 import BeautifulSoup

from parsers.tg.functions import clean_leading_number, clean_text
from producer import send_raw

env = Env()
env.read_env()

# 🔧 Функция парсинга HTML в памяти
def extract_news_from_html_content(html: str):
    soup = BeautifulSoup(html, "html.parser")
    pattern = re.compile(r"\d+\.\s+.+")
    news = []

    for font_tag in soup.find_all("font", {"color": "red", "size": "5"}):
        title_tag = font_tag.find("b")
        if title_tag and pattern.match(title_tag.get_text()):
            title = title_tag.get_text(strip=True)
            block = font_tag.find_parent("blockquote")
            if block:
                text = block.get_text(separator="\n", strip=True)
                link_tag = block.find("a", string="Адрес")
                link = link_tag['href'] if link_tag and 'href' in link_tag.attrs else None
                news.append({"title": title, "text": text, "link": link})
    return news


async def news_input(title: str,
               description: str,
               source: str,
               url: str,
               news_date,
               check_type: bool = True):  # может быть str или datetime
    '''Отправляет в кафка'''
    if isinstance(news_date, datetime):
        news_date = news_date.isoformat()
    if not source or not description:
        return None
    else:
        # 4. Формируем объект новости
        news = {
            "title": title,
            "description": description,
            "news_date": news_date,
            "url": url,
            "source": f'tg_{source}',
            "flag": "raw",
            "name": "tg_pars"
        }

        # 5. Отправляем в Kafka
        await send_raw(news)
        print(f"📤 [{source}] новая новость отправлена: {description[:100]}")



# === Парсер HTML-файлов .htm (специальный случай) ===
def extract_news_from_html_content(html: str):
    """Парсит .htm файл: ищет заголовки и блоки с текстом и ссылками"""
    soup = BeautifulSoup(html, "html.parser")  # создаём объект BeautifulSoup для HTML
    pattern = re.compile(r"\d+\.\s+.+")  # регулярка для заголовков вида "1. Текст"

    out = []  # список для результатов
    for font_tag in soup.find_all("font", {"color": "red", "size": "5"}):  # ищем <font color=red size=5>
        title_tag = font_tag.find("b")  # внутри должен быть <b> — заголовок
        if not title_tag:
            continue
        title = title_tag.get_text(strip=True)  # текст заголовка
        if not pattern.match(title):  # проверяем по регулярке, что это "нумерованный" заголовок
            continue

        block = font_tag.find_parent("blockquote")  # блок текста рядом с заголовком
        if not block:
            continue

        text = block.get_text(separator="\n", strip=True)  # вытаскиваем текст блока
        link_tag = block.find("a", string=re.compile(r"Адрес", re.I))  # ищем ссылку "Адрес ..."
        link = link_tag["href"] if link_tag and link_tag.has_attr("href") else ""  # берём href

        out.append({"title": title, "text": text, "link": link})  # добавляем в список
    return out


# === Основная функция для запуска клиента Telethon ===
async def run_telegram_script_russia():
    # получаем данные API из переменных окружения
    api_id = env('api_id_russia')
    api_hash = env('api_hash_russia')

    # настройка логгера (будем писать в консоль для удобства отладки)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    log = logging.getLogger("tg_rus")

    # создаём клиент Telethon (сессия сохранится в файл "myGrab_rus.session")
    client = TelegramClient('myGrab_rus', api_id, api_hash, system_version="4.16.30-vxCUSTOM")
    log.info("GRAB - Started RUSSIAN")

    EXCLUDE_CHAT_ID = -4174113127  # исключаем один конкретный чат

    # === Обработчик новых сообщений ===
    @client.on(events.NewMessage())
    async def handler(event: events.NewMessage.Event):
        try:
            msg = event.message  # само сообщение
            if not msg:  # если пустое событие
                return

            chat_id = event.chat_id  # id чата
            if chat_id == EXCLUDE_CHAT_ID:  # исключаем ненужный чат
                return

            # --- кейс 1: пришёл файл .htm ---
            file = event.file  # получаем файл, если есть
            file_name = getattr(file, "name", None)  # имя файла
            if file_name and file_name.lower().endswith(".htm"):  # проверка, что это HTML-файл
                buf = BytesIO()  # создаём буфер в памяти
                await event.download_media(file=buf)  # скачиваем файл в буфер
                buf.seek(0)  # ставим указатель в начало
                html_content = buf.read().decode("utf-8", errors="ignore")  # читаем текст из файла

                # парсим HTML и загружаем все найденные новости
                for n in extract_news_from_html_content(html_content):
                    title = clean_leading_number(n["title"])  # очищаем заголовок (убираем "1. ", "2. " и т.д.)
                    description = clean_text(n["text"])  # чистим текст
                    if not (title or description or n["link"]):  # если совсем пусто — пропускаем
                        continue
                    await news_input(  # сохраняем новость в БД (или отправляем дальше)
                        check_type=False,
                        title=title,
                        description=description,
                        source="Telegram (HTM)",
                        url=n["link"],
                        news_date=datetime.now(timezone.utc),  # время фиксации (UTC)
                    )
                return  # выходим из обработчика — файл уже обработали

            # --- кейс 2: обычное текстовое сообщение ---
            text = (msg.message or "").strip()  # достаём текст сообщения
            if not text:  # если текст пустой — игнорируем
                return

            # получаем дату сообщения (из Telegram, в UTC)
            msg_dt = (msg.date or datetime.now().replace(tzinfo=timezone.utc)).astimezone(timezone.utc)

            # entity может быть сразу в event.chat (экономим на get_entity)
            entity = event.chat if event.chat else await client.get_entity(chat_id)

            # источник: название чата/канала
            if isinstance(entity, (types.Chat, types.Channel)) and getattr(entity, "title", None):
                source = entity.title.strip()
            else:
                source = "Telegram"

            # ссылка на сообщение (только если канал публичный и у него есть username)
            url = ""
            if isinstance(entity, types.Channel) and getattr(entity, "username", None):
                if source == 'Mash':
                    url = f"https://t.me/mash/{event.id}"
                else:
                    url = f"https://t.me/{entity.username}/{event.id}"

            # сохраняем новость (заголовок пустой, весь текст идёт в description)
            await news_input(
                title='',
                description=clean_text(text),
                source=source,
                url=url,
                news_date=msg_dt,  # дата от Telegram
            )

        except Exception as e:
            # логируем ошибку (с полным трейсбеком)
            logging.exception(f"Ошибка в обработчике: {e}")

    # запускаем клиент и ждём сообщений
    await client.start()
    await client.run_until_disconnected()