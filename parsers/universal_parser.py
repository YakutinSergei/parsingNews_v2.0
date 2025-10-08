from datetime import datetime, timezone
import re
import requests
from newspaper import Article
from readability import Document
import trafilatura


def looks_like_gibberish(text: str) -> bool:
    """
    Проверка текста на каракули/мусор/капчу.
    """
    text = text.strip()

    # слишком мало текста
    if len(text) < 50:
        return True

    # содержит HTML-теги
    if re.search(r"<(html|div|script|body|head)", text.lower()):
        return True

    # повторяющиеся символы
    if len(set(text)) < 5:
        return True

    # битая кодировка (много "Ð", "Ñ")
    if re.search(r"[ÐÑ�]{5,}", text):
        return True

    # фразы капчи
    bad_phrases = [
        "вы не робот",
        "smartcaptcha",
        "нам очень жаль",
        "отключено исполнение javascript",
        "подтвердите, что вы человек"
    ]
    if any(phrase in text.lower() for phrase in bad_phrases):
        return True

    return False


def extract_article(url: str, flag: str = "user_web", name: str = "article_parser") -> dict | None:
    """
    Универсальное извлечение статьи по ссылке.
    Newspaper3k → Trafilatura → Readability.
    Фильтрует капчу/каракулы.
    """
    title, text, source, pub_date = None, None, None, None

    # --- Newspaper3k ---
    try:
        article = Article(url, language="ru")
        article.download()
        article.parse()
        if article.title and article.text:
            title = article.title.strip()
            text = article.text.strip()
            source = "newspaper3k"
            if article.publish_date:
                pub_date = article.publish_date
    except Exception as e:
        print("[Newspaper3k] Ошибка:", e)

    # --- Trafilatura ---
    if not text:
        try:
            html = requests.get(url, timeout=10).text
            extracted = trafilatura.extract(html, with_metadata=True)
            if extracted:
                if isinstance(extracted, dict):
                    title = extracted.get("title")
                    text = extracted.get("text")
                    pub_date = extracted.get("date")
                else:
                    text = extracted.strip()
                source = "trafilatura"
        except Exception as e:
            print("[Trafilatura] Ошибка:", e)

    # --- Readability ---
    if not text:
        try:
            html = requests.get(url, timeout=10).text
            doc = Document(html)
            title = doc.short_title().strip()
            text = doc.summary()
            source = "readability"
        except Exception as e:
            print("[Readability] Ошибка:", e)

    # === Проверка валидности ===
    if not text or looks_like_gibberish(text):
        print(f"⚠️ Каракули/капча вместо статьи, url={url}")
        return None

    # news_date
    if isinstance(pub_date, str):
        try:
            pub_date = datetime.fromisoformat(pub_date)
        except Exception:
            pub_date = None

    if pub_date is None:
        pub_date = datetime.now(tz=timezone.utc)

    return {
        "title": title or "",
        "description": text.strip(),
        "news_date": pub_date.isoformat(),
        "url": url,
        "source": source or "unknown",
        "flag": flag,
        "name": name
    }
