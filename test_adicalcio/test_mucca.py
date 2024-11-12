import pandas as pd
import json
import requests
import time
import csv
import paho.mqtt.client as mqtt

import pytest
from jsonschema import validate


client_id = "clientId-z3wVScq2zf"
client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
client._client_id = client_id.encode("utf-8")

topic = 'testtopic/1'

contatore = 0

schema = {
    "type" : "object",
    "properties" : {
        "ts" : {"type" : "number"},
        "Linear" : {"type" : "number"},
        "Polynomial" : {"type" : "number"},
    },
}

def test_diz(dictionary, schema):
    validate(instance=dictionary, schema=schema)

def linear(value):
    a_coef = 2.6647E-02
    b_coef = 7.2683E+01
    res = a_coef * value - b_coef
    return round(res, 5)

def polynomial(value):
    a_coef = 7.0405E-12
    b_coef = 1.0504E-07
    c_coef = 2.7117E-02
    d_coef = 7.3308E+01
    res = a_coef * value**3 - b_coef * value**2 + c_coef * value - d_coef
    return round(res, 5)


def invia_messaggio(mess, topic = topic, client = client):
    global contatore
    msg_info = client.publish(topic, mess, qos=1)
    time.sleep(0.1)
    contatore += 1
    print(f"Inviato questo messaggio: {mess}")

def val_to_json(ts, line, pol, at):
    diz = dict()
    diz["ts"] = ts
    diz["Linear"] = line
    diz["Polynomial"] = pol
    test_diz(diz, schema)
    # print(diz)
    messaggio = str(diz)
    invia_messaggio(messaggio)
    json_str = json.dumps(diz)
    print("-"*42)
    call_api(json_str, at)

def call_api(js, device_token):
    url = f"https://zion.nextind.eu/api/v1/{device_token}/telemetry"
    requests.post(url, json=js)

def on_connect(client, userdata, flags, reason_code, properties):
    if reason_code != 0:
        print("Failed to connect")
    else:
        client.subscribe("testtopic/1")
    
def on_publish(client, userdata, mid, reason_code, properties=None):
    print(f"Messaggio {mid} pubblicato")

broker = "broker.hivemq.com"
port = 1883

client.on_publish = on_publish
client.on_connect = on_connect

client.connect(broker, port=port)

client.loop_start()

df = pd.read_csv("Estensimetro.csv", sep=";")

print(df.head())
df["Value"] = df["Value"].str.replace(",", ".")
print("-"*42)

for _, row in df.iterrows():
    timestamp = row["Timestamp"]
    v = row["Value"]
    at = row["Access token"]
    v=float(v)
    lin = linear(v)
    pol = polynomial(v)
    val_to_json(timestamp, lin, pol, at)

print(f"Il dataset ha {df.shape[0]} righe e ho inviato {contatore} messaggi")