# Ваш файл с парсером телеграм (telegram_parser.py)
import json
import logging
import re
import asyncio
from datetime import datetime

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



async def run_telegram_script_russia():
    api_id = env('api_id_russia')
    api_hash = env('api_hash_russia')

    # Настройка логгера
    logging.basicConfig(filename='telegram_parser.log', level=logging.ERROR)

    client = TelegramClient('myGrab_rus', api_id, api_hash, system_version="4.16.30-vxCUSTOM")
    print("GRAB - Started RUSSIAN")

    @client.on(events.NewMessage())
    async def my_group_handler(event):
        # Получаем идентификатор чата
        chat_id = event.chat_id

        # Получаем идентификатор сообщения
        message_id = event.id

        try:
            if chat_id != -4174113127:
                # === [1] Если это HTML-файл (.htm) ===
                file_name = getattr(event.file, 'name', None)
                if file_name and file_name.endswith(".htm"):
                    file_bytes = BytesIO()
                    await event.download_media(file=file_bytes)
                    file_bytes.seek(0)
                    html_content = file_bytes.read().decode('utf-8')

                    news_data = extract_news_from_html_content(html_content)

                    for n in news_data:
                        title = clean_leading_number(n['title'])
                        description = clean_text(n['text'])
                        await news_input(
                            check_type=False,
                            title=title,
                            description=description,
                            source='',
                            url=n['link'],
                            news_date=datetime.now()
                        )

                        # Здесь можно сохранить в БД или переслать в другой канал

                    return  # завершить обработку, если это файл

                # Получаем объект сущности по идентификатору чата
                entity = await client.get_entity(chat_id)

                if isinstance(entity, types.Chat):  # Группа
                    text = event.message.message
                    # date = event.message.date
                    name = f'Телеграм канал: {entity.title}'
                    link = ''


                    await news_input(
                        title=text[:30],
                        description=text,
                        source=entity.title,
                        url=link,
                        news_date=datetime.now()
                    )

                elif isinstance(entity, types.Channel):  # Канал

                    text = event.message.message
                    name = f'Телеграм канал: {entity.title}'
                    link = f'https://t.me/{entity.username}/{message_id}'
                    # date = event.message.date



                    await news_input(
                        title=text[:30],
                        description=text,
                        source=entity.title,
                        url=link,
                        news_date=datetime.now()
                    )

                else:

                    print("Неизвестный тип")

        except Exception as e:
            print(f"Ошибка: {e}")
            return None

    await client.start()
    await client.run_until_disconnected()