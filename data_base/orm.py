from datetime import datetime

import asyncpg

from environs import Env

env = Env()
env.read_env()


'''Проверяем есть ли такая новость'''


async def news_exists(url: str):
    try:

        conn = await asyncpg.connect(user=env('user'),
                                     password=env('password'),
                                     database=env('db_name'),
                                     host=env('host'))

        url = await conn.fetchrow(f'''SELECT id 
                                            FROM monitor_rhb_news 
                                            WHERE url = '{url}';''')
        return url


    except Exception as _ex:
        print('[INFO] Error ', _ex)

    finally:
        if conn:
            await conn.close()
            print('[INFO] PostgresSQL closed')


'''Добавляем новую новость'''


async def news_add(date_news,
                   title: str,
                   content: str,
                   source_id: int,
                   url: str,
                   flag_news: int,
                   img_news: str = None,
                   key_words: str = None,
                   city_news: str = None,
                   object: str = None,
                   ):
    try:
        conn = await asyncpg.connect(user=env('user'), password=env('password'), database=env('db_name'),
                                     host=env('host'))

        result = await conn.fetchrow(f'''INSERT INTO monitor_rhb_news(
                                                    title, 
                                                    content, 
                                                    source_id, 
                                                    url, 
                                                    img_news, 
                                                    flag_news, 
                                                    key_words, 
                                                    city_news, 
                                                    object_news,
                                                    publish_date)
                                          VALUES($1, 
                                                $2,
                                                $3,
                                                $4,
                                                $5,
                                                $6,
                                                $7,
                                                $8,
                                                $9,
                                                $10)
                                          RETURNING id
                                        ''',
                                       title,
                                       content,
                                       source_id,
                                       url,
                                       img_news,
                                       flag_news,
                                       key_words,
                                       city_news,
                                       object,
                                     date_news
                                       )
        return result
    except Exception as _ex:
        print('[INFO] Error ', _ex)

    finally:
        if conn:
            await conn.close()
            print('[INFO] PostgresSQL closed')
