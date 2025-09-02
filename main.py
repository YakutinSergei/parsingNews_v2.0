import asyncio

from parsers.RSS.parser_rss import rss_parser
from parsers.tg.telegram_news import run_telegram_script_russia
from producer import init_producer, close_producer
# from parsers.site_parser import site_parser
# from parsers.tg_parser import tg_parser

async def main():
    await init_producer()  # запускаем Kafka producer

    try:
        await asyncio.gather(
            rss_parser(),
            # site_parser(),
            run_telegram_script_russia()
        )
    finally:
        await close_producer()

if __name__ == "__main__":
    asyncio.run(main())
