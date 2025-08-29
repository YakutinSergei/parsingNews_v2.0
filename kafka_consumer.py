import json
from aiokafka import AIOKafkaConsumer, AIOKafkaProducer
from database.database import async_session, init_db
from database.models import NewsTable
from config import KAFKA_BOOTSTRAP_SERVERS, KAFKA_TOPIC_RAW, KAFKA_TOPIC_SAVED

async def consume_and_save():
    """
    Consumer для Kafka:
    1. Читает из топика news_raw
    2. Сохраняет в БД
    3. Отправляет подтверждённую новость в топик news_saved
    """
    consumer = AIOKafkaConsumer(
        KAFKA_TOPIC_RAW,
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        value_deserializer=lambda v: json.loads(v.decode("utf-8"))
    )
    producer = AIOKafkaProducer(
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        value_serializer=lambda v: json.dumps(v).encode("utf-8")
    )

    await consumer.start()
    await producer.start()
    await init_db()

    try:
        async for msg in consumer:
            news = msg.value

            # сохраняем в БД
            async with async_session() as session:
                db_news = NewsTable(
                    source=news["source"],
                    type=news["type"],
                    title=news["title"],
                    url=news["url"],
                    text=news["text"],
                )
                session.add(db_news)
                await session.commit()
                print(f"💾 Сохранено: {db_news.title[:50]}")

            # отправляем в news_saved
            await producer.send_and_wait(KAFKA_TOPIC_SAVED, {
                "id": db_news.id,
                "title": db_news.title,
                "url": db_news.url,
                "text": db_news.text,
                "source": db_news.source,
                "type": db_news.type
            })
            print(f"📤 Отправлено в Kafka [news_saved]: {db_news.title[:50]}")
    finally:
        await consumer.stop()
        await producer.stop()
