# Ваш файл с парсером телеграм (telegram_parser.py)

import asyncio
import logging
import os

from telethon import TelegramClient, events
from telethon.tl import types
from telethon.tl.types import InputPeerChat, PeerUser


# from database.orm import add_news
# from parser.chanel_tg import chanel

from environs import Env
from telethon.tl.types import PeerChat, PeerChannel

from data_base.model import add_news, find_or_create_source
from scraping.news_website import file_path, analyze_news

env = Env()
env.read_env()



# Открываем файл для чтения
with open(file_path, 'r', encoding='utf-8') as file:
    # Считываем строки из файла и создаем список
    lines = [line.strip() for line in file if line.strip()]

async def run_telegram_script():
    api_id = env('api_id')
    api_hash = env('api_hash')



    # Настройка логгера
    logging.basicConfig(filename='telegram_parser.log', level=logging.ERROR)

    client = TelegramClient('myGrab', api_id, api_hash, system_version="4.16.30-vxCUSTOM")
    print("GRAB - Started")

    @client.on(events.NewMessage())
    async def my_group_handler(event):
        compliance = False
        source_new = 17
        # Получаем идентификатор чата
        chat_id = event.chat_id

        # Получаем идентификатор сообщения
        message_id = event.id

        try:
            # Получаем объект сущности по идентификатору чата
            entity = await client.get_entity(chat_id)
            if isinstance(entity, types.Chat): #Группа
                text = event.message.message
                date = event.message.date
                name = entity.title
                link = ''
                await save_media_from_event(event)

                matching_words = analyze_news(text, lines)

                if matching_words:
                    print(f"Совпадающие слова: {matching_words}")
                    compliance = True

                source_new= await find_or_create_source(name)


                news = add_news(title=text,
                                publish_date=date,
                                content=text,
                                url=link,
                                compliance=compliance,
                                source_new=source_new)

                await save_media_from_event(event=event, save_dir=f'../media/img_news/{news}')

            elif isinstance(entity, types.Channel): # Канал
                text = event.message.message
                name = entity.title
                link = f'Ссылка на сообщение: https://t.me/{entity.username}/{message_id}'
                date = event.message.date

                matching_words = analyze_news(text, lines)

                if matching_words:
                    print(f"Совпадающие слова: {matching_words}")
                    compliance = True

                source_new= await find_or_create_source(name)

                news = add_news(title=text[:40],
                                publish_date=date,
                                content=text,
                                url=link,
                                compliance=compliance,
                                source_new=source_new)

                await save_media_from_event(event=event, save_dir=f'../media/img_news/{news}')
            else:

                print("Неизвестный тип")
        except Exception as e:
            print(f"Ошибка: {e}")
            return None

    await client.start()
    await client.run_until_disconnected()



'''Функция сохранения файлов'''


async def save_media_from_event(event, save_dir='../media/img_news/'):
    # Проверка наличия медиа в сообщении
    if event.media:
        # Создаем директорию, если она не существует
        os.makedirs(save_dir, exist_ok=True)

        # Получаем дату сообщения для создания уникального имени файла
        date_str = event.date.strftime("%Y%m%d_%H%M%S")

        # Проверяем тип медиа и сохраняем его
        if isinstance(event.media, types.MessageMediaPhoto):
            photo_path = os.path.join(save_dir, f"photo_{date_str}.jpg")
            await event.download_media(file=photo_path)
        elif isinstance(event.media, types.MessageMediaDocument):
            document_path = os.path.join(save_dir, f"document_{date_str}")
            await event.download_media(file=document_path)

    elif event.video:
        # Создаем директорию, если она не существует
        os.makedirs(save_dir, exist_ok=True)

        # Получаем уникальное имя файла на основе даты сообщения
        date_str = event.date.strftime("%Y%m%d_%H%M%S")

        # Скачиваем видео и сохраняем его
        video = await event.download_media()
        video_path = os.path.join(save_dir, f"video_{date_str}.mp4")
        os.rename(video, video_path)