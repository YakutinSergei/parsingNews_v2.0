def is_important(news: dict) -> bool:
    return "пожар" in news["title"].lower()
