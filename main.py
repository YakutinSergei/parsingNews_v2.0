import asyncio

from data_base.model import create_table
from scraping.TG_new import run_telegram_script
#from data_base.model import db_connect
from scraping.news_website import get_news_content_url

urls = [['https://ria.ru/export/rss2/archive/index.xml', 1, 'РИА новости'],
        ['https://tass.ru/rss/v2.xml', 2, 'ТАСС'],
        ['http://www.rg.ru/xml/index.xml', 3,'Российская газета'],
        ['http://www.gazeta.ru/export/rss/social.xml', 4, 'Газета.Ru'],
        ['https://rssexport.rbc.ru/rbcnews/news/30/full.rss', 5,  'RBC'],
        ['http://www.vz.ru/export/yandex.xml', 6, 'Взгляд'],
        ['https://lenta.ru/rss/google-newsstand/main/', 7, 'Лента'],
        ['http://russian.rt.com/rss/', 8, 'RT на русском'],
        ['https://www.mk.ru/rss/news/index.xml', 9, 'Московский Комсомолец'],
        ['http://kp.ru/rss/allsections.xml', 10, 'Комсомольская правда'],
        ['https://aif.ru/rss/googlearticles', 11, 'Аргументы и факты'],
        ['https://www.interfax.ru/rss.asp', 12, 'Интерфакс'],
        ]

async def main():
    #await db_connect()
    tasks = []
    # Запуск телеграм-парсера
    tasks.append(asyncio.create_task(run_telegram_script()))

    tasks.append(asyncio.create_task(create_table()))
    for url in urls:
        task = asyncio.create_task(get_news_content_url(url))
        tasks.append(task)
    await asyncio.gather(*tasks)

asyncio.run(main())