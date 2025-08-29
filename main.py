import asyncio
from kafka_producer import init_producer, close_producer

from kafka_consumer import consume_and_save
from config import logger
from parsers.RSS.parser_rss import rss_parser


async def main():
    await init_producer()
    logger.info("Сервис новостей запущен")

    try:
        await asyncio.gather(
            rss_parser(),
            # site_parser(),
            # tg_parser(),
            # consume_and_save()
        )
    finally:
        await close_producer()
        logger.info("Сервис остановлен")

if __name__ == "__main__":
    asyncio.run(main())
