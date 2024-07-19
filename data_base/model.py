import sqlite3
import datetime

from environs import Env
from sqlalchemy import Column, Integer, String, DateTime, create_engine, func, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, Mapped, mapped_column

env = Env()
env.read_env()


# Определение базового класса для объявления моделей
Base = declarative_base()

# Определение модели таблицы
class NewsTable(Base):
    __tablename__ = 'news_2sn'

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str]
    description: Mapped[str]
    news_date: Mapped[datetime.datetime]
    created_at: Mapped[datetime.datetime]
    updated_at: Mapped[datetime.datetime]
    source: Mapped[str]
    url: Mapped[str]
    #img_news: Mapped[str | None]
    #flag_news: Mapped[bool | None]
    #key_words: Mapped[str | None]
    # city_news: Mapped[str | None]
    # object_news: Mapped[str | None]
    # events: Mapped[bool | None]
    # source_id: Mapped[int] = mapped_column(ForeignKey("monitor_source_site_news.id"))




class SourceSiteNews(Base):
    __tablename__ = 'monitor_source_site_news'

    id = Column(Integer, primary_key=True)
    title = Column(String)
    url = Column(String)
    img_site_news = Column(String)





async def create_table(database_name=env('db_name'),
                 user=env('user'),
                 password=env('password'),
                 host=env('host'), port=5432):
    db_url = f"postgresql://{user}:{password}@{host}:{port}/{database_name}"
    engine = create_engine(db_url)
    Base.metadata.create_all(engine)


def create_session(database_name=env('db_name'),
                 user=env('user'),
                 password=env('password'),
                 host=env('host'), port=5432):
    db_url = f"postgresql://{user}:{password}@{host}:{port}/{database_name}"
    engine = create_engine(db_url)
    Session = sessionmaker(bind=engine)
    return Session()


#Добавление новых новостей
def add_news(title, publish_date, content, url, source_new, compliance=False):
    session = create_session()
    new_entry = NewsTable(title=title,
                          publish_date=publish_date,
                          source_id=source_new,
                          content=content,
                          url=url,
                          flag_news=compliance)

    session.add(new_entry)
    session.commit()
    id = new_entry.id
    session.close()
    return id


# Функция проверки есть ли такая новость
def news_exists(url):
    session = create_session()

    # Проверка наличия новости с заданным заголовком
    existing_news = (session.
                     query(NewsTable).
                     filter(func.lower(NewsTable.url) == func.lower(url)).first())
    session.close()

    return existing_news is not None


'''Функция вывода ид источника информации'''
def find_or_create_source(name):
    session = create_session()

    # Поиск записи с заданным именем
    existing_source = session.query(SourceSiteNews).filter(SourceSiteNews.title.ilike(name)).first()

    if existing_source:
        # Если запись уже существует, вернуть ее id
        session.close()
        return existing_source.id
    else:
        # Если запись не существует, создать новую запись и вернуть ее id
        new_source = SourceSiteNews(title=name)
        session.add(new_source)
        session.commit()
        source_id = new_source.id
        session.close()
        return source_id


# def add_sqlite(title, publish_date, content, url, source_new, compliance=False):
#     with sqlite3.connect('db.sqlite3') as conn:
#         # Создаем объект курсора
#         cursor = conn.cursor()
#
#         # Используем оператор ? для предотвращения SQL-инъекций
#         cursor.execute('''
#                 INSERT INTO monitor_rhb_news(title, publish_date, source_id, content, url, flag_news)
#                 VALUES (?, ?, ?, ?, ?, ?)
#             ''', (title, publish_date, source_new, content, url, compliance))
#
#         cursor.execute('SELECT last_insert_rowid()')
#         id = cursor.fetchone()[0]
#
#         return id
#
#
# def news_exists(url):
#     # Создаем контекстный менеджер с помощью оператора with
#     with sqlite3.connect('db.sqlite3') as conn:
#         # Создаем объект курсора
#         cursor = conn.cursor()
#
#         # Выполняем запрос для проверки наличия новости с заданным URL
#         cursor.execute('SELECT COUNT(*) FROM monitor_rhb_news WHERE LOWER(url) = LOWER(?)', (url,))
#         count = cursor.fetchone()[0]
#
#     # Соединение будет автоматически закрыто при выходе из блока with
#
#     return count > 0




# import asyncpg
#
# from environs import Env
#
#
# env = Env()
# env.read_env()
#
# '''Первое подключение к базе данных'''
# async def db_connect():
#     try:
#         conn = await asyncpg.connect(user=env('user'),  password=env('password'), database=env('db_name'), host=env('host'))
#
#         await conn.execute('''CREATE TABLE IF NOT EXISTS monitor_source_site_news(id SERIAL PRIMARY KEY,
#                                                                    title_site TEXT,
#                                                                    url_site TEXT,
#                                                                    img_site_news TEXT
#                                                                    );''')
#
#         await conn.execute('''CREATE TABLE IF NOT EXISTS monitor_rhb_news(id SERIAL PRIMARY KEY,
#                                                                     title TEXT,
#                                                                     content TEXT,
#                                                                     url TEXT,
#                                                                     img_news TEXT,
#                                                                     flag_news INTEGER,
#                                                                     key_words TEXT,
#                                                                     city_news TEXT,
#                                                                     object_news TEXT,
#                                                                     publish_date TIMESTAMP,
#                                                                     source_id INTEGER REFERENCES news_img(id)
#                                                                     );''')
#
#
#     except Exception as _ex:
#         print('[INFO] Error ', _ex)
#
#     finally:
#           if conn:
#             await conn.close()
#             print('[INFO] PostgresSQL closed')
