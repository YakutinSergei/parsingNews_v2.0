import json
from aiokafka import AIOKafkaProducer
from core.config import settings
import asyncio

producer: AIOKafkaProducer | None = None

async def init_producer():
    """
    Инициализация Kafka producer.
    """
    global producer
    producer = AIOKafkaProducer(
        bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
        value_serializer=lambda v: json.dumps(v, ensure_ascii=False).encode("utf-8")
    )
    await producer.start()

async def send_raw(news: dict):
    """
    Отправка новости в Kafka (topic = news_raw).
    news — словарь с ключами title, description, url, source, news_date и т.д.
    """
    if producer is None:
        raise RuntimeError("Producer не инициализирован")
    await producer.send_and_wait(settings.KAFKA_TOPIC_RAW, news)
    print(f"📤 Отправлено в Kafka [{settings.KAFKA_TOPIC_RAW}]: {news.get('title', '')[:60]}")

async def close_producer():
    if producer:
        await producer.stop()
