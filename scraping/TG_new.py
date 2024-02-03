# Ваш файл с парсером телеграм (telegram_parser.py)

import asyncio
import logging
import os

from telethon import TelegramClient, events
from telethon.tl import types

# from database.orm import add_news
# from parser.chanel_tg import chanel

from environs import Env
from telethon.tl.types import PeerChat, PeerChannel

env = Env()
env.read_env()

async def run_telegram_script():
    api_id = env('api_id')
    api_hash = env('api_hash')



    # Настройка логгера
    logging.basicConfig(filename='telegram_parser.log', level=logging.ERROR)

    client = TelegramClient('myGrab', api_id, api_hash, system_version="4.16.30-vxCUSTOM")
    print("GRAB - Started")

    @client.on(events.NewMessage())
    async def my_group_handler(event):
        print(event)
        print(event.message.id)
        print(event.message.peer_id.chat_id)


        # Извлекаем информацию о сообщении

        # Дата и время отправки сообщения
        date = event.date

        # Текст сообщения
        message_text = event.text

        # Идентификатор отправителя (если это пользователь)
        sender_id = event.from_id.user_id if isinstance(event.from_id, types.PeerUser) else None

        # Имя пользователя отправителя (если это пользователь)
        sender_username = event.from_id.username if isinstance(event.from_id, types.PeerUser) else None

        # Идентификатор чата/канала отправителя (если это канал или группа)
        sender_channel_id = event.from_id.channel_id if isinstance(event.from_id, types.PeerChannel) else None

        print(f'id:{sender_channel_id}')

        # Ссылка на сообщение
        message_link = f"https://t.me/c/{sender_channel_id}/{event.id}" if sender_channel_id else None

        # Получение информации о группе или канале отправителя
        sender_entity = None
        if sender_channel_id:
            sender_entity = await client.get_entity(sender_channel_id)

            # Вывод даты и времени
            print(f"Дата: {date}")

            # Вывод текста сообщения
            print(f"Текст сообщения: {message_text}")


        # Проверка наличия медиа в сообщении
        media = None
        if event.media:
            if isinstance(event.media, types.MessageMediaPhoto):
                media = "Фотография"
                # Сохранение фотографии
                photo_path = os.path.join('media', 'img', f'photo_{date}.jpg')
                await event.download_media(file=photo_path)
            elif isinstance(event.media, types.MessageMediaDocument):
                media = "Документ"
                # Сохранение документа (может быть видео или другой файл)
                document_path = os.path.join('media', 'img', f'document_{date}.')
                await event.download_media(file=document_path)
            elif isinstance(event.media, types.MessageMediaVideo):
                media = "Видео"
                # Сохранение видео
                video_path = os.path.join('media', 'img', f'video_{date}.mp4')
                await event.download_media(file=video_path)

        # Вывод информации



        # Вывод типа медиа (если есть)
        print(f"Тип медиа: {media}")

        # Вывод информации об отправителе
        if sender_id:
            print(f"Отправитель (пользователь): {sender_id}")
        elif sender_entity:
            print(f"Отправитель (группа/канал): {sender_entity.title}")

        # Вывод username отправителя (если есть)
        if sender_username:
            print(f"Username отправителя: {sender_username}")

        # Вывод ссылки на сообщение (если есть)
        if message_link:
            print(f"Ссылка на сообщение: {message_link}")


    await client.start()
    await client.run_until_disconnected()
