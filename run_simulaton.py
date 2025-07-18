from celery_app.tasks import process_news_pipeline, parse_telegram

if __name__ == "__main__":
    print("🚀 Отправка задач в Celery...")

    # Отправляем задачу в очередь "news"
    process_news_pipeline.delay()

    # Отправляем задачу в очередь "telegram"
    parse_telegram.delay()

    print("✅ Все задачи отправлены!")
