from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from datetime import datetime
from geopy.distance import geodesic
from pymongo import MongoClient
import sys
import random
import pytest
from jsonschema import validate

uri = "mongodb+srv://Flu:Assurbanipal685@clusterbuddha.l0ctpfp.mongodb.net/"

# Connessione a mongo
client = MongoClient(uri, server_api=ServerApi('1'))

# Ping
try:
    client.admin.command('ping')
    print("Pinged your deployment. You successfully connected to MongoDB!")
except Exception as e:
    print(e)
    
db = client["ConcertiDB"]
collection = db["Concerti"]

schema = {
  "type": "object",
  "properties": {
    "_id": {"bsonType": "objectId"},
    "nome_evento": {"type": "string"},
    "location": {"type": "object",
      "properties": {
        "address": {
            "type": "object",
          "properties": {
            "nome": {"type": "string"},
            "indirizzo": {"type": "string"},
            "num_civico": {"type": "integer"},
            "città": {"type": "string"},
            "stato": {"type": "string"}
          },
        },
        "geo": {
          "type": "object",
          "properties": {
            "type": {
              "type": "string",
              "enum": ["Point"]
            },
            "coordinates": {
              "type": "array",
              "items": {
                "type": "number"
              },
              "minItems": 2,
              "maxItems": 2
            }
          },
        }
      },
    },
    "cantanti": {
      "type": "array",
      "items": {"type": "string"}
    },
    "data": {
      "type": "string",
      "format": "date-time"
    },
    "max_posti": {"type": "integer"},
    "disp": {"type": "integer"},
    "prezzo": {"type": "number"}
  },
}

def val_wrapper(instance, schema):
    try:
        validate(instance, schema)
        return True
    except:
        return False

def test_concerto(ins):
    assert val_wrapper(ins, schema=schema)

#Ricerca artisti
def concerti_artista(col):
    artista = input("Artista ?: ")
    if type(col) != list:
        concerti = col.find({"cantanti": artista})
        test_main2(concerti)
    else:
        nuovi = []
        for doc in col:
            if artista in doc["cantanti"]:
                nuovi.append(doc)
        if len(nuovi)==0:
            print("-"*42)
            print("Nessun evento trovato con il nuovo filtro, puoi comunque comprare biglietti presentati in precedenza")
            c = input("Vuoi proseguire con l'acquisto? (y/n) ")
            if c == "y":
                test_main2(nuovi)
            else:
                fine()
        test_main2(nuovi)

def concerti_data(col):
    inizio = input("Data inizio (YYYY-MM-DD)?: ")
    fine = input("Data fine (YYYY-MM-DD)?: ")
    inizio_mongo = datetime.strptime(inizio, "%Y-%m-%d")
    fine_mongo = datetime.strptime(fine, "%Y-%m-%d")
    if type(col) != list:
        concerti = col.find({
            "data": {
                "$gte": inizio_mongo,
                "$lte": fine_mongo
            }
        })
        test_main2(concerti)
    else:
        nuovi = [doc for doc in col if inizio_mongo <= doc['data'] <= fine_mongo]
        if len(nuovi)==0:
            print("-"*42)
            print("Nessun evento trovato con il nuovo filtro, puoi comunque comprare biglietti presentati in precedenza")
            c = input("Vuoi proseguire con l'acquisto? (y/n) ")
            if c == "y":
                test_main2(nuovi)
            else:
                fine()
        test_main2(nuovi)

def concerti_luogo(col):
    latitude = float(input("Latitudine?: "))
    longitude = float(input("Longitudine?: "))
    distanza = float(input("Distanza massima in km?: "))
    if type(col) != list:
        concerti = col.find({
            "location.geo": {
                "$geoWithin": {
                    "$centerSphere": [[longitude, latitude], distanza / 6378100]
                }
            }
        })
        test_main2(concerti)
    else:
        nuovi = []
        for doc in col:
            concert_coordinates = (doc['location']['geo']['coordinates'][1], doc['location']['geo']['coordinates'][0])
            geodist = geodesic([latitude, longitude], concert_coordinates).kilometers
            if geodist <= distanza:
                nuovi.append(doc)
        if len(nuovi)==0:
            print("-"*42)
            print("Nessun evento trovato con il nuovo filtro, puoi comunque comprare biglietti presentati in precedenza")
            c = input("Vuoi proseguire con l'acquisto? (y/n) ")
            if c == "y":
                test_main2(nuovi)
            else:
                fine()
        test_main2(nuovi)

def fine():
    print("-"*42)
    print("La ringraziamo di aver utilizzato il nostro servizio :) ")
    sys.exit()

def purchase_tickets(concert_id, num_tickets):
    concert = collection.find_one({"_id": concert_id})
    if concert and concert["disp"] >= num_tickets:
        collection.update_one(
            {"_id": concert_id},
            {"$inc": {"disp": -num_tickets}}
        )
        tickets = [f"{concert['nome_evento']}, {concert['data']}, n.{random.randint(10000, 99999)}"
            for _ in range(num_tickets)]
        return tickets, concert["prezzo"] * num_tickets
    else:
        return None, None

def test_main():
    print("Trova i tuoi concerti preferiti tra i disponibili:")
    print("1: Per Artista")
    print("2: Per Date")
    print("3: Per Vicinanza")
    choice = input("> ")

    if choice == '1':        
        concerti_artista(collection)
    elif choice == '2':
        concerti_data(collection)
    elif choice == '3':
        concerti_luogo(collection)
    else:
        print("Scelta non valida")
        return

def test_main2(concerts):
    if concerts:
        print("-"*42)
        lista_conc = list(concerts)
        print(lista_conc)

        print("-"*42)
        print("Concerti trovati:", len(lista_conc))
        for i, concert in enumerate(lista_conc, 1):
            status = 'sold-out' if concert["disp"] == 0 else f"disp:{concert['disp']}"
            print(f"{i}: {concert['nome_evento']}, {concert['data']}, {status}, {concert['prezzo']}€")

        print("-"*42)
        r = input("Vuoi applicare ulteriori filtri di ricerca? (y/n) ")
        if r == "y":
            print("-"*42)
            alsc = int(input("1. Filtra per artista \n2. Filtra per data\n3. Filtra per posizione\n> "))
            if alsc == 1:
                concerti_artista(lista_conc)
            elif alsc == 2:
                concerti_data(lista_conc)
            elif alsc == 3:
                concerti_luogo(lista_conc)
        
        if len(lista_conc)>0:
            concert_choice = int(input("Per quale concerto vuoi acquistare? ")) - 1
            num_tickets = int(input("Quanti biglietti? "))

            concert_id = lista_conc[concert_choice]["_id"]
            tickets, total_price = purchase_tickets(concert_id, num_tickets)
            if tickets:
                print("-"*42)
                print(f"I tuoi biglietti per un totale di {total_price:.2f}€:")
                for ticket in tickets:
                    print(ticket)
                fine()
            else:
                print("Non ci sono abbastanza biglietti disponibili")
                fine()
        else:
            print("Nessun concerto trovato")
            fine()

if __name__ == "__main__":
    test_main()
