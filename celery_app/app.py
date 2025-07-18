from celery import Celery
from kombu import Queue

celery = Celery(
    "news_aggregator",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/1"
)

celery.conf.task_queues = [
    Queue("rss"),
    Queue("sites"),
    Queue("telegram"),
]

celery.conf.task_default_queue = "default"


# 👇 Это нужно, чтобы Celery знал о задачах
celery.autodiscover_tasks(['celery_app'])