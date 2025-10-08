import asyncio
import re
import torch
from bs4 import BeautifulSoup
from transformers import MarianMTModel, MarianTokenizer
import nltk

# Скачать токенизатор предложений (один раз)
nltk.download("punkt")

# Загружаем модель перевода
model_name = "Helsinki-NLP/opus-mt-en-ru"
tokenizer = MarianTokenizer.from_pretrained(model_name)
model = MarianMTModel.from_pretrained(model_name)

# Автоматически определяем устройство (GPU или CPU)
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model = model.to(device)

BATCH_SIZE = 16  # кол-во предложений в одном батче


def clean_text(text: str) -> str:
    """
    Очистка текста от HTML-разметки и лишних символов.
    """
    text = BeautifulSoup(text, "lxml").get_text()
    text = re.sub(r"&[a-zA-Z]+;", " ", text)  # заменяем HTML-сущности
    text = re.sub(r"[^\w\s.,!?;:()\-\n]", " ", text, flags=re.UNICODE)  # убираем спецсимволы
    text = re.sub(r"\s+", " ", text).strip()  # нормализуем пробелы
    return text


async def translate_batch(sentences: list[str]) -> list[str]:
    """
    Перевод пачки предложений асинхронно.
    """
    def _translate():
        inputs = tokenizer(sentences, return_tensors="pt", padding=True, truncation=True).to(device)
        translated = model.generate(
            **inputs,
            num_beams=2,        # ускоряем за счет уменьшения beam search
            max_length=512,
            early_stopping=True
        )
        return tokenizer.batch_decode(translated, skip_special_tokens=True)

    return await asyncio.to_thread(_translate)


async def translate_large_text(text: str) -> str:
    """
    Асинхронный перевод длинного текста:
    1) чистим текст
    2) режем на предложения
    3) переводим пачками
    """
    clean = clean_text(text)
    sentences = nltk.sent_tokenize(clean, language="english")

    translated_sentences = []
    for i in range(0, len(sentences), BATCH_SIZE):
        batch = sentences[i:i + BATCH_SIZE]
        batch_translations = await translate_batch(batch)
        translated_sentences.extend(batch_translations)

    return " ".join(translated_sentences)


# 🔹 Пример использования
async def main():
    raw_text = """
    <p>Hello <b>world</b>! This is a <i>test</i> of the async translation function. 😀
    Another sentence with <a href="#">link</a> &amp; some weird chars $$$ !!!</p>
    """
    translated = await translate_large_text(raw_text)
    print(translated)


if __name__ == "__main__":
    asyncio.run(main())
