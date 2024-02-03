import spacy

# Загрузка модели spaCy
nlp = spacy.load("ru_core_news_lg")  # Замените "xx_ent_wiki_sm" на более крупную модель по вашему выбору


def extract_entities(text):
    doc = nlp(text)
    entities = {'cities': [], 'incidents': []}

    for ent in doc.ents:
        if ent.label_ == 'LOC':  # Извлечение города
            entities['cities'].append(ent.text)
        elif ent.label_ == 'NORP':  # Извлечение объекта происшествия
            entities['incidents'].append(ent.text)

    return entities

# Пример использования
news_text = '''В Липецке отменят несколько рейсов трамваев 2 февраля. В расписание трамвая № 2 внесут изменения на некоторое время.

В областном центре в пятницу запланированы работы по опиловке деревьев на пересечении улиц 8 марта и Терешковой. В связи с этим работа трамваев, следующих по маршруту № 2 «Центральный рынок – Кольцо 9 микрорайона» изменят.

По информации администрации города Липецка, рейсы со временем отправления от остановки «Центральный рынок» 9:47 и 9:56 отменяются.'''
result = extract_entities(news_text)
print("Города:", result['cities'])
print("Происшествия:", result['incidents'])