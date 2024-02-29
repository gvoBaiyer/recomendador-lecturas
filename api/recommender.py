from flask import Flask, request, jsonify
from pymongo import MongoClient
from openai import OpenAI
import json
import mongo
import llm

recommender = Flask(__name__)

sessions_books = {}
sessions_filters = {}
sessions_recommendation = {}

translations = {
  "genre": "Genero",
  "author": "Autor",
  "theme": "Tema",
  "minPages": "Número mínimo de páginas",
  "maxPages": "Número máximo de páginas",
  "lang": "Idioma",
  "langLevel": "Nivel de idioma",
  "similarBook": "Libro similar",
  "age": "Edad"
}

client = OpenAI(
    api_key="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",
)

database = MongoClient ('mongodb://localhost:27017')["recommender"]

recommendation_intents = ["RecomendarLibro", "RecomendarLibro-AddFilters-no"]

def get_text_response(messages):
  return {
      "fulfillmentMessages": [
        {
          "text": {
            "text": messages
          }
        }
      ]
    } 

def get_synopsis(book, session_id):
  if sessions_books.get(session_id) is not None and sessions_books.get(session_id).get("lang") is not None:
    lang = sessions_books.get(session_id).get("lang")
  else:
    lang = "es"
  synopsis = mongo.get_synopsis(database, book, lang) 
  if synopsis is None:
    response = llm.get_synopsis(client, book, lang)
    synopsis = json.loads(response)["synopsis"]
    print(response)
    mongo.add_synopsis(database, book, synopsis, lang)
  if synopsis == "":
    return get_text_response([f"Lo siento, no conozco el libro {book}. ¿Quizás todavía no se ha escrito?"])
  messages = [f"Aquí tienes la sinopsis del libro {book}. " + synopsis]
  return get_text_response(messages)

def get_information(book, session_id):
  if sessions_books.get(session_id) is not None and sessions_books.get(session_id).get("lang") is not None:
    lang = sessions_books.get(session_id).get("lang")
  else:
    lang = "es"
  information = mongo.get_information(database, book, lang) 
  if information is None:
    response = llm.get_information(client, book, lang)
    print(response)
    information = json.loads(response)["information"]
    mongo.add_information(database, book, information, lang) 
  if information == "":
    return get_text_response([f"Lo siento, no conozco el libro {book}. ¿Quizás todavía no se ha escrito?"])
  return get_text_response([f"Aquí tienes información sobre el libro {book}. " + information])
 

def get_recommendation(filters):
  print(filters) 
  llm_response = llm.get_recommendation(client, filters)
  llm_response = json.loads(llm_response)
  return llm_response["book"], llm_response["author"]  


def handle_recommendation(filters, session_id):
  sessions_filters[session_id] = filters
  book, author = get_recommendation(filters)
  if book == None:
    return get_text_response(["Lo siento, no conozco ningún libro que cumpla con las características especificadas."])  
  sessions_books[session_id]["book"] = book
  sessions_recommendation[session_id] = True
  return get_text_response([f"En ese caso, te recomiendo el libro {book}, de {author}. ¿Quieres alguna otra recomendación? También puedo darte la sinopsis o información sobre el libro."])    
  

def handle_next_recommendation(message, previous_filters, session_id):
  response = llm.get_filters(client, message)
  result = json.loads(response)
  if is_empty_filters(result["filters"]):
    return handle_recommendation_filters(previous_filters, session_id)
  return handle_recommendation(result["filters"], session_id)
  


def handle_recommendation_filters(filters, session_id):
  sessions_recommendation[session_id] = False
  if is_empty_filters(filters):
    return {
      "followupEventInput": {
        "name": "recomendacionCheck",
        "languageCode": "es-ES",
        "parameters": {}
      }
    }
  else:
    return {
      "followupEventInput": {
        "name": "filtersCheck",
        "languageCode": "es-ES",
        "parameters": {}
      }
    }


def get_filters(filters):
  active_filters = ""
  for filter in filters:
    if filters[filter] != "" and filters[filter] != 'es':
       active_filters = active_filters + f"{translations[filter]}: {filters[filter]}\n"
  return active_filters


def is_empty_filters(filters):
  return all(value == '' or value == 'es' for value in filters.values())


def get_event_response(request, session_id):
  message = request['queryResult']['queryText']
  result = json.loads(llm.get_intent(client, message))
  intent = result["intent"]
  print(result)
  if result["book"] == "" and sessions_books.get(session_id) is not None and sessions_books.get(session_id).get("book") is not None:
    book = sessions_books.get(session_id).get("book")
  else:
    book = result["book"]
  if intent == "recomendacion":
    lang = result["filters"].get("lang", "es")
    if lang == '':
      lang = "es"
    if is_empty_filters(result["filters"]):
      return handle_recommendation_filters(sessions_filters.get(session_id, {}), session_id)
    sessions_books[session_id]["lang"] = lang
    print(intent)
    return {
      "followupEventInput": {
        "name": intent,
        "languageCode": "es-ES",
        "parameters": {
          "book": book, 
          "genre": result["filters"].get("genre", ""),
          "author": result["filters"].get("author", ""),
          "theme": result["filters"].get("theme", ""),
          "minPages": result["filters"].get("minPages", ""),
          "maxPages": result["filters"].get("maxPages", ""),
          "similarBook": result["filters"].get("similarBook", ""),
          "age": result["filters"].get("age", ""),
          "lang": lang,
          "langLevel": result["filters"].get("langLevel", "")
        }
      }
    }
  return {
    "followupEventInput": {
      "name": result["intent"],
      "languageCode": "es-ES",
      "parameters": {
        "book": book
      }
    }
  }

def handle_filters(request, session_id):
  message = request['queryResult']['queryText']
  response = llm.get_filters(client, message)
  result = json.loads(response)
  if is_empty_filters(result["filters"]):
    return get_text_response(["¿En qué estás interesado?"])
  lang = result["filters"].get("lang", "es")
  if lang == '':
    lang = "es"
  sessions_books[session_id]["lang"] = lang 
  return {
    "followupEventInput": {
      "name": "recomendacion",
      "languageCode": "es-ES",
      "parameters": {
        "genre": result["filters"].get("genre", ""),
        "author": result["filters"].get("author", ""),
        "theme": result["filters"].get("theme", ""),
        "minPages": result["filters"].get("minPages", ""),
        "maxPages": result["filters"].get("maxPages", ""),
        "similarBook": result["filters"].get("similarBook", ""),
        "age": result["filters"].get("age", ""),
        "lang": lang,
        "langLevel": result["filters"].get("langLevel", "")
      }
    }
  }

def handle_new_filters(request, session_id):
  message = request['queryResult']['queryText']
  response = llm.get_filters(client, message)
  result = json.loads(response)
  if is_empty_filters(result["filters"]):
    return {
      "followupEventInput": {
        "name": "recomendacionCheck",
        "languageCode": "es-ES",
        "parameters": {}
      }
    }
  lang = result["filters"].get("lang", "es")
  if lang == '':
    lang = "es"
  sessions_books[session_id]["lang"] = lang 
  return {
    "followupEventInput": {
      "name": "recomendacion",
      "languageCode": "es-ES",
      "parameters": {
        "genre": result["filters"].get("genre", ""),
        "author": result["filters"].get("author", ""),
        "theme": result["filters"].get("theme", ""),
        "minPages": result["filters"].get("minPages", ""),
        "maxPages": result["filters"].get("maxPages", ""),
        "similarBook": result["filters"].get("similarBook", ""),
        "age": result["filters"].get("age", ""),
        "lang": lang,
        "langLevel": result["filters"].get("langLevel", "")
      }
    }
  }

def get_response(intent, request):
  print(intent)
  session_id = request["session"].split("/sessions/")[1]
  if sessions_books.get(session_id) is None:
    sessions_books[session_id] = {}
  if intent == "ObtenerInformacion":
    book = request['queryResult']['parameters']['book']
    sessions_books[session_id]["book"] = book
    return get_information(book, session_id)
  if intent == "ObtenerSinopsis":
    book = request['queryResult']['parameters']['book']
    sessions_books[session_id]["book"] = book
    return get_synopsis(book, session_id)
  if intent == "RecomendarLibro-AddFilters-yes":
    previos_action = sessions_recommendation.get(session_id, False) 
    if previos_action:
      return handle_recommendation_filters(request['queryResult']['parameters'], session_id)
    return handle_filters(request, session_id)
  if intent == "RecomendarLibro-yes":
    return handle_next_recommendation(request['queryResult']['queryText'], request['queryResult']['parameters'], session_id)
  if intent == "RecomendarLibro-KeepFilters-no":  
    return handle_new_filters(request, session_id)
  if intent == "RecomendarLibro-KeepFilters":
    return get_text_response(["¿Te gustaría que la nueva recomendación se base en los criterios que mencionaste anteriormente?\n" + get_filters(sessions_filters[session_id])])
  if intent == "RecomendarLibro-KeepFilters-yes":  
    previos_action = sessions_recommendation.get(session_id, False) 
    if previos_action:
      return handle_recommendation_filters(sessions_filters[session_id], session_id)
    return handle_recommendation(sessions_filters[session_id], session_id)
  if intent in recommendation_intents:
    print(request)
    print(request['queryResult']['parameters'])
    filters = request['queryResult']['parameters']
    return handle_recommendation(filters, session_id)
  else:
    return get_event_response(request, session_id)


@recommender.post("/recommendation")
def handle_request():
    intent = request.json['queryResult']['intent']['displayName']
    response = get_response(intent, request.json)
    return jsonify(response)