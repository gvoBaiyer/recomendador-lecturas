import re
from pymongo import MongoClient

def add_synopsis(database, book, synopsis, language="es"):
    collection = database["synopsis"]
    document = {
        "book": book,
        "synopsis": synopsis,
        "language": language
    }
    collection.insert_one(document)

def get_synopsis(database, book, language="es"):
    collection = database["synopsis"]
    document = collection.find_one({"book": re.compile(book, re.IGNORECASE), "language": language})
    if document is None:
        return None
    return document["synopsis"]

def add_information(database, book, information, language="es"):
    collection = database["information"]
    document = {
        "book": book,
        "information": str(information),
        "language": language
    }
    collection.insert_one(document)

def get_information(database, book, language="es"):
    collection = database["information"]
    document = collection.find_one({"book": re.compile(book, re.IGNORECASE), "language": language})
    if document is None:
        return None
    return document["information"]
