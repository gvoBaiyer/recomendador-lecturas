from openai import OpenAI

context_intent = {'role':'system', 'content':"""
Tu deber es clasificar la intención del usuario a partir de su mensaje. Hay 3 intenciones posibles, obtener información \
obtener una sinopsisi o obtener una recomendación sobre un libro. \
Debes devolver una respuesta en formato json, con la siguiente estructura: \
{ \
  "intent": INTENT \
  "book: BOOK \
  "filters: FILTERS \
} \
donde INTENT tomará uno de estos valores: \
 - informacion si el usuario desea obtener información \
 - sinopsis si el usuario quiere una sinopsis o resumen \
 - recomendacion si el usuario quiere una recomendación \
 - fallback si la intención no es clara o no se corresponde con alguna de las anteriores \
BOOK será el título del libro en caso de que se incluya en el mensaje. En caso contrario su valor \
sera una cadena vacia \
FILTERS solo se tendrá en cuenta si se trata de una recomendación y seguirá esta estructura \
{
  "genre": genero literario en el que el usuario está interesado, vacío si no se ha especificado \
  "author": autor en el que el usuario está interesado, vacío si no se ha especificado \
  "theme": tema sobre el que el usuario está interesado, vacío si no se ha especificado \
  "minPages": número de páginas mínimo, vacío si no se ha especificado \
  "maxPages": número de páginas máximo, vacío si no se ha especificado \
  "lang": idioma que se desea, en formato ISO 639, es si no se ha especificado \
  "langLevel": nivel del idioma que se desea, vacío si no se ha especificado \
  "similarBook": libro similar en el que el usuario estáinteresado, vacío si no se ha especificado \
  "age": edad público del libro, vacío si no se ha especificado \
}
"""}

context_information = {'role':'system', 'content':"""
Quiero que des información sobre el libro solicitado. \
Deberas dar los siguientes datos: \
autor, fecha de publicación, número de paginas y género literaro, siguiendo este fromato: \
Autor: valor Número de páginas: valor Fecha de publicación: valor Género: valor \
Nunca respondas con una pregunta. Debes utilizar solo el título del libro \
Response en formato JSON, con clave information y valor la información generada \
Si no pudes obtener la información el valor será un string vacío\
La respuesta deberá conteneres solo el JSON generado, sin indicar el formato
"""}

context_information_language = {'role':'system', 'content':"""
Quiero que des información sobre el libro solicitado. \
Deberas responser indicando el nivel del idioma y las caracteristicas \
destacables para un estudiante español que quiera aprender sobre el idioma \
Nunca respondas con una pregunta. Debes utilizar solo el título del libro \
Response en formato JSON, con clave information y valor la información generada \
Si no pudes obtener la información el valor será un string vacío \
La respuesta deberá conteneres solo el JSON generado, sin indicar el formato
"""}

context_synopsis = {'role':'system', 'content':"""
Quiero que hagas una sinopsis sobre el libro solicitado. \
La sinopsis deberá ser de un máximo de 100 palabras. \
Response en formato JSON, con clave synopsis y valor la synopsis generada \
Si no pudes obtener la synopsis el valor será un string vacío \
La respuesta deberá conteneres solo el JSON generado, sin indicar el formato
"""}

context_synopsis_language = {'role':'system', 'content':"""
Quiero que hagas una sinopsis sobre el libro solicitado. \
La sinopsis deberá estar en el idioma solicitado por el usuario, no en español\
La sinopsis deberá ser de un máximo de 100 palabras \
Response en formato JSON, con clave synopsis y valor la synopsis generada \
Si no pudes obtener la synopsis el valor será un string vacío \
La respuesta deberá conteneres solo el JSON generado, sin indicar el formato
"""}

context_recommendation = {'role':'system', 'content':"""
Quiero que hagas una recomendación sobre un libro que cumpla con los filtros introducidos.\
Si los filtros están vacíos recomienda un libro al azar \
La respuesta deberá ser en formato json siguiendo la siguiente estructura: \
{ \
  "book": Nombre del libreo recomendado \
  "author": Autor del libro \
}
"""}

context_recommendation_language = {'role':'system', 'content':"""
Quiero que hagas una recomendación sobre un libro que cumpla con los filtros introducidos.\
El idioma original del libro deberá ser el solicitado por el usuario
La respuesta deberá ser en formato json siguiendo la siguiente estructura: \
{ \
  "book": Nombre del libreo recomendado \
  "author": Autor del libro \
}
"""}


context_filters = {'role':'system', 'content':"""
Tu deber es obtener los filtros que el usuario desea aplicar a una recomendación de lectura
Debes devolver una respuesta en formato json, con la siguiente estructura: \
En caso de no poder obetner ningún filtro, devuelve todos los campos vacíos \
{ \
  "filters: FILTERS \
} \
FILTERS seguirá esta estructura \
{
  "genre": genero literario en el que el usuario está interesado, vacío si no se ha especificado \
  "author": autor en el que el usuario está interesado, vacío si no se ha especificado \
  "theme": tema sobre el que el usuario está interesado, vacío si no se ha especificado \
  "minPages": número de páginas mínimo, vacío si no se ha especificado \
  "maxPages": número de páginas máximo, vacío si no se ha especificado \
  "lang": idioma que se desea, en formato ISO 639, es si no se ha especificado \
  "langLevel": nivel del idioma que se desea, vacío si no se ha especificado \
  "similarBook": libro similar en el que el usuario estáinteresado, vacío si no se ha especificado \
  "age": edad público del libro, vacío si no se ha especificado \
}
"""}


def get_information(client, book, lang="es"):
    if lang == "es":
        return collect_messages(client, book, context_information, 0.8)
    else:
        message = f"Libro: {book}, idioma: {lang}"
        return collect_messages(client, message, context_information_language, 0.8)


def get_synopsis(client, book, lang="es"):
    if lang == "es":
        return collect_messages(client, book, context_synopsis, 0.8)
    else:
        message = f"Libro: {book}, idioma: {lang}"
        return collect_messages(client, message, context_synopsis_language, 0.8)


def get_recommendation(client, filters):
  if filters.get("lang", "es") == "es":
    return collect_messages(client, filters, context_recommendation, 1)
  else:
    return collect_messages(client, filters, context_recommendation_language, 1)


def get_intent(client, message):
    return collect_messages(client, message, context_intent)

def get_filters(client, message):
    return collect_messages(client, message, context_filters)


def get_completion_from_messages(client, messages, model="gpt-3.5-turbo-1106", temperature=0):
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature, # this is the degree of randomness of the model's output
    )
    return response.choices[0].message.content


def collect_messages(client, message, context, temperature=0):
    messages = [context]
    messages.append({'role':'user', 'content':f"{message}"})
    response = get_completion_from_messages(client, messages, temperature=temperature) 
    return response
