from newsplease import NewsPlease

url = "https://ria.ru/20250830/vsu-2038473058.html"

# Загружаем статью
article = NewsPlease.from_url(url)

# Теперь у нас есть объект со структурированными полями
print("Заголовок:", article.title)
print("Дата публикации:", article.date_publish)
print("Авторы:", article.authors)
print("Язык:", article.language)
print("URL:", article.url)
print("Текст:\n", article.maintext, "...")
