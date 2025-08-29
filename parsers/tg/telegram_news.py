# Ваш файл с парсером телеграм (telegram_parser.py)
import asyncio

import logging

from telethon import TelegramClient, events
from telethon.tl import types

from environs import Env

env = Env()
env.read_env()


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
                # Получаем объект сущности по идентификатору чата
                entity = await client.get_entity(chat_id)
                if isinstance(entity, types.Chat):  # Группа
                    text = event.message.message
                    # date = event.message.date
                    name = f'Телеграм канал: {entity.title}'
                    link = ''

                    print(text[:30])
                    print(link)
                    print('-' * 30)

                elif isinstance(entity, types.Channel):  # Канал
                    text = event.message.message
                    name = f'Телеграм канал: {entity.title}'
                    link = f'https://t.me/{entity.username}/{message_id}'
                    # date = event.message.date

                    print(text[:30])
                    print(link)
                    print('-' * 30)

                else:

                    print("Неизвестный тип")

        except Exception as e:
            print(f"Ошибка: {e}")
            return None

    await client.start()
    await client.run_until_disconnected()


if __name__ == "__main__":
    asyncio.run(run_telegram_script_russia())