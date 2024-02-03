import asyncio
import os
import re
import requests
import feedparser
import random


from datetime import datetime
from urllib.parse import urljoin

from newspaper import Article, Config
from bs4 import BeautifulSoup
from fake_useragent import UserAgent

from data_base.model import add_news, news_exists
from scraping.user_agents import user_agent_list

file_path = 'stop_word.txt'

# Открываем файл для чтения
with open(file_path, 'r', encoding='utf-8') as file:
    # Считываем строки из файла и создаем список
    lines = [line.strip() for line in file if line.strip()]


async def get_news_content_url(url_rss): # Получаем ссылки на новости из RSS
    feed = feedparser.parse(url_rss[0])
    if feed.bozo:
        print("Error parsing the feed:", feed.bozo_exception)
        return

    for entry in feed.entries:
        url_news = entry.link
        pub_date = entry.published
        date_parts = pub_date.split(' ')
        pub_date = ' '.join(date_parts[0:5])
        date_format = '%a, %d %b %Y %H:%M:%S'
        try:
            pub_date = datetime.strptime(pub_date, date_format)
        except:
            print(pub_date)
            pub_date = None

        new = await get_news_content(url=url_news, pub_date=pub_date, source_new=url_rss[1])
        if new:
            break
        await asyncio.sleep(1)


async def get_news_content(url, pub_date, source_new):
    try:
        config = Config()
        ua = UserAgent()
        user_agent = ua.random
        config.browser_user_agent = user_agent
        article = Article(url, config=config)
        article.download()
        article.parse()
        title = article.title  # Заголовок статьи
        compliance = False # Переменная для проверки есть ли совпадения

        print("url:", url)  # Заголовок
        print("Title:", title)  # Заголовок
        print("Publish Date:", pub_date)  # Дата опубликования
        print("_"*30)  # Дата опубликования

        #Парсер для ТАСС
        if source_new == 2:
            if not news_exists(url):
                response = requests.get(url=url, headers=random_user_agent_headers())
                response.encoding = 'utf-8'
                soup = BeautifulSoup(response.text, 'lxml')
                img_tag = soup.find('div', class_='Image_wrapper__LRh5J')
                if img_tag:
                    img_tag = img_tag.find('img')
                else:
                    img_tag = None

                compliance = False

                content = ''
                texts = soup.find_all('span', class_='tass_pkg_text-oEhbR')

                for text in texts:
                    content += text.text



                matching_words = analyze_news(content, lines)

                if matching_words:
                    print(f"Совпадающие слова: {matching_words}")
                    compliance = True

                # Добавляем в базу данных
                news = add_news(title=title,
                                publish_date=pub_date,
                                content=content,
                                url=url,
                                compliance=compliance,
                                source_new=source_new)

                # Ищем картинку к новости
                if img_tag:
                    # Получение URL изображения
                    img_url = urljoin(url, img_tag['src'])
                    print(img_tag)

                    # Загрузка изображения
                    img_response = requests.get(img_url)

                    image_folder = f'../media/img_news/{news}'  # путь к папке
                    os.makedirs(image_folder, exist_ok=True)

                    image_file_path = os.path.join(image_folder, 'saved_image.jpg')

                    # Сохранение изображения в файл
                    with open(image_file_path, 'wb') as img_file:
                        img_file.write(img_response.content)


                return 0
            else:
                return 1

        #Парсер для РИА новости
        elif source_new == 1:
            if not news_exists(url):
                response = requests.get(url=url, headers=random_user_agent_headers())
                response.encoding = 'utf-8'
                soup = BeautifulSoup(response.text, 'lxml')

                article = soup.find('div', class_='layout-article__main-over').find_all('div', class_='article__text')

                papers = [text.text for text in article]
                paper = ''

                img_tag = soup.find('div', class_='photoview__open')
                if img_tag:
                    img_tag = img_tag.find('img')
                else:
                    img_tag = None

                # Время и дата публикации статьи
                time_date_news = soup.find('div', class_='article__info-date').find('a').text
                date_object = datetime.strptime(time_date_news, "%H:%M %d.%m.%Y")

                time_date_news = date_object.strftime("%Y-%m-%d %H:%M:%S")

                for text in papers:
                    paper += text

                compliance = False  # Есть ли совпадения
                matching_words = analyze_news(paper, lines)

                if matching_words:
                    print(f"Совпадающие слова: {matching_words}")
                    compliance = True

                news = add_news(title=title,
                                publish_date=time_date_news,
                                content=paper,
                                url=url,
                                compliance=compliance,
                                source_new=source_new)

                # Ищем картинку к новости
                if img_tag:
                    # Получение URL изображения
                    img_url = urljoin(url, img_tag['src'])

                    # Загрузка изображения
                    img_response = requests.get(img_url)

                    image_folder = f'../media/img_news/{news}'  # путь к папке
                    os.makedirs(image_folder, exist_ok=True)

                    image_file_path = os.path.join(image_folder, 'saved_image.jpg')

                    # Сохранение изображения в файл
                    with open(image_file_path, 'wb') as img_file:
                        img_file.write(img_response.content)

                    return 0
            else:
                return 1



        #Парсер для остальных источников
        else:
            if not news_exists(url): # Проверяем есть ли такая новость
                content = article.text
                matching_words = analyze_news(content, lines)

                if matching_words:
                    print(f"Совпадающие слова: {matching_words}")
                    compliance = True


                # Добавляем в базу данных
                news = add_news(title=title,
                                publish_date=pub_date,
                                content=content,
                                url=url,
                                compliance=compliance,
                                source_new=source_new)

                images = article.images

                if images:
                    # Взять первое изображение из статьи (можно добавить логику для обработки нескольких изображений)
                    image_url = next(iter(images))

                    # Загрузка изображения и сохранение в файл
                    image_response = requests.get(image_url)

                    image_folder = f'../media/img_news/{news["id"]}'  # путь к папке
                    os.makedirs(image_folder, exist_ok=True)

                    image_file_path = os.path.join(image_folder, 'saved_image.jpg')

                    # Сохранение изображения в файл
                    with open(image_file_path, 'wb') as img_file:
                        img_file.write(image_response.content)
                return 0
            else:
                return 1

    except Exception as _ex:
        print('[INFO] Error ', _ex)


# Функция для анализа новостей
def analyze_news(news_text, word_list):
    for keyword in word_list:
        match = re.search(keyword, news_text, re.IGNORECASE)
        if match:
            return keyword  # Вернуть ключевое слово и совпавшую фразу

    return None



def random_user_agent_headers():
    '''Возвращет рандомный user-agent и друге параметры для имитации запроса из браузера'''
    rnd_index = random.randint(0, len(user_agent_list) - 1)

    header = {
        'User-Agent': user_agent_list[rnd_index],
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate, br',
        'DNT': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
    }

    return header