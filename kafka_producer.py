import json
from aiokafka import AIOKafkaProducer

from config import KAFKA_BOOTSTRAP_SERVERS

producer: AIOKafkaProducer | None = None

async def init_producer():
    """
    Инициализация Kafka producer (подключение к брокеру).
    """
    global producer
    producer = AIOKafkaProducer(
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        value_serializer=lambda v: json.dumps(v).encode("utf-8")
    )
    await producer.start()

async def send_to_kafka(topic: str, news: dict):
    """
    Отправка словаря-новости в Kafka.
    """
    try:
        await producer.send_and_wait(topic, news)
        print(f"📤 Отправлено в Kafka [{topic}]: {news['title'][:50]}")
    except Exception as e:
        print(f"Kafka send error: {e}")

async def close_producer():
    """
    Завершение работы producer.
    """
    if producer:
        await producer.stop()
