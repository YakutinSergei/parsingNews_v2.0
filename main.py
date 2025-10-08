import asyncio

from consumer_links import consume_links
from parsers.RSS.parser_rss import rss_parser
from parsers.tg.telegram_news import run_telegram_script_russia
from producer import init_producer, close_producer


async def main():
    await init_producer()
    try:
        await asyncio.gather(
            rss_parser(),
            #run_telegram_script_russia(),
            consume_links(),  # 👈 слушаем Kafka с tg_links
        )
    finally:
        await close_producer()


if __name__ == "__main__":
    asyncio.run(main())
