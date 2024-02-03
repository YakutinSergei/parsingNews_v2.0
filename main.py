import asyncio

from data_base.model import create_table
from scraping.TG_new import run_telegram_script
#from data_base.model import db_connect
from scraping.news_website import  get_news_content_url

urls = [['http://kp.ru/rss/allsections.xml', 14, 'Комсомольская правда'],
        ['https://tass.ru/rss/v2.xml', 2, 'ТАСС'],
        ['https://ria.ru/export/rss2/archive/index.xml', 1, 'РИА новости'],
        ['https://www.mk.ru/rss/news/index.xml', 11, 'Московский Комсомолец'],
        ['https://www.interfax.ru/rss.asp', 16, 'Интерфакс'],
        ['https://rssexport.rbc.ru/rbcnews/news/30/full.rss', 7,  'RBC'],
        ['https://lenta.ru/rss/google-newsstand/main/', 9, 'Лента'],
        ['https://aif.ru/rss/googlearticles', 15, 'Аргументы и факты'],
        ['http://www.vz.ru/export/yandex.xml', 8, 'Взгляд'],
        ['http://www.rg.ru/xml/index.xml', 5,'Российская газета'],
        ['http://www.gazeta.ru/export/rss/social.xml', 6, 'Газета.Ru'],
        ['http://russian.rt.com/rss/', 10, 'RT на русском']
        ]

async def main():
    #await db_connect()
    tasks = []
    # Запуск телеграм-парсера
    tasks.append(asyncio.create_task(run_telegram_script()))

    tasks.append(asyncio.create_task(create_table()))
    # for url in urls:
    #     task = asyncio.create_task(get_news_content_url(url))
    #     tasks.append(task)
    await asyncio.gather(*tasks)

asyncio.run(main())