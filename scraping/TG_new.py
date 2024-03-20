# Ваш файл с парсером телеграм (telegram_parser.py)

import asyncio
import logging
import os

from telethon import TelegramClient, events
from telethon.tl import types
from telethon.tl.types import InputPeerChat


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
        #print(event.message.peer_id.chat_id)

        # Получаем идентификатор чата
        chat_id = event.chat_id

        # Получаем идентификатор сообщения
        message_id = event.id

        try:
            # Получаем объект сущности по идентификатору чата
            entity = InputPeerChat(chat_id)

            # Получаем подробную информацию о чате
            chat = await client.get_entity(chat_id)
            print(f'Информация: {chat.username}')

            # Получаем название чата
            title = chat.title

            print(f'Название группы: {title}')
        except Exception as e:
            print(f"Ошибка при получении названия группы: {e}")
            return None

        # Формируем ссылку на сообщение
        message_link = f"https://t.me/c/{chat_id}/{message_id}"

        # Выводим ссылку на сообщение
        print(f"Ссылка на сообщение: {message_link}")





    await client.start()
    await client.run_until_disconnected()
