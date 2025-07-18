import sys
import subprocess

from celery_app.app import celery
from mock.parser import collect_news
from mock.classifier import is_important
from mock.summarizer import summarize
from mock.telegram_sender import send_to_telegram

@celery.task(queue="news")
def process_news_pipeline():
    print(">> Задача Celery запущена!", file=sys.stderr)
    news_items = collect_news()
    print(f">> Найдено {len(news_items)} новостей", file=sys.stderr)

    for news in news_items:
        print(f">> Обработка: {news['title']}", file=sys.stderr)
        if is_important(news):
            summary = summarize(news["text"])
            send_to_telegram(news["title"], summary, news["url"])
        else:
            print(f"[SKIP] Неважная новость: {news['title']}", file=sys.stderr)



@celery.task(queue="telegram")
def parse_telegram():
    print("▶️ Celery запускает Telegram-парсер как отдельный процесс")
    subprocess.Popen(["python", "parsers/telegram_news.py"])