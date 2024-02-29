# Recomendador de lecturas

Para ejecutar el agente, es necesaria una cuenta en Dialogflow. Una vez creada, 
se puede importar el agente importando el archivo Recomendador-Libros.zip

Para ejecutar la aplicación son necesarias las siguientes aplicaciones:
- python3
- mongoDb
Será necesario instalar una serie de dependencias en python, para lo cuál puede pip como
instalador. A continuación, se enumeran las dependencias necesarias y cómo instalarlas:
- flask: pip install Flask
- pymongo: pip install pymongo
- openai: pip install openai
En el código se incluye una API-Key para el acceso a las funcionalidades del LLM.
También se incluye un export de los datos de MongoDB, para poder ser restaurados. La
aplicación python está configurada para conectarse a la conexión local por defecto, esto es,
localhost:27017.
Para importar los datos, se debe ejecutar el comando: mongorestore -d recommender
sconv/dump/recommender
Para ejecutar la aplicación, basta con ejecutar python3 -m flask --app recommender run
Una vez hecho esto, será necesario utilizar ngrok para hacer la aplicación accesible,
utilizando para ello ngrok http 5000 y cambiando en la sección de fullfilment en Dialogflow la
url obtenida al ejecutar el comando ngrok.