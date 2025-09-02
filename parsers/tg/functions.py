import re

def clean_text(text: str) -> str:
    if not isinstance(text, str):
        return ""

    # Удаление мягких переносов и управляющих символов
    text = text.replace('\u00AD', '')  # мягкий перенос
    text = re.sub(r'[\r\n\t]', ' ', text)  # замена на пробел

    # Удаление слэшей
    text = text.replace('/', ' ').replace('\\', ' ')

    # Удаление всего после "Адрес [ Источник :" (если есть)
    text = re.split(r'Адрес\s*\[\s*Источник\s*:', text)[0]

    # Удаление повторяющихся пробелов
    text = re.sub(r'\s+', ' ', text)

    # Обрезка пробелов по краям
    return re.sub(r'^\s*\d{1,3}\.\s*', '', text)


def clean_leading_number(text: str) -> str:
    """
    Удаляет ведущий номер с точкой в начале строки (например, '1. текст')
    """
    if not isinstance(text, str):
        return ""

    # Удаляет 'число. ' или 'число.' в начале строки
    return re.sub(r'^\s*\d{1,3}\.\s*', '', text)