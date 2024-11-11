import azure.functions as func
import json
import logging
import requests
from bs4 import BeautifulSoup
import re
import pandas as pd

# Altro codice :)

app = func.FunctionApp()

def echanoael(zuppa):
    noael_matches = []
    div = zuppa.find('div', id='SectionContent')
    dl = div.find_all('dl')

    for sez in dl:
        coldx = sez.find_all('dd')
        for ddtag in coldx:
            if ddtag.text == "NOAEL":
                h3 = ddtag.find_previous('h3')
                nxt = ddtag.find_next('dd')
                risp = f"Il NOAEL con queste condizioni:  {h3.text} è  {nxt.text}"
                noael_matches.append(risp)
    
    return noael_matches

def echadnel(zuppa):
    dnel_matches = []
    div = zuppa.find('div', id='SectionContent')
    dl = div.find_all('dl')

    for sez in dl:
        coldx = sez.find_all('dd')
        for ddtag in coldx:
            if ddtag.text == "DNEL (Derived No Effect Level)":
                h3 = ddtag.find_previous('h3')
                nxt = ddtag.find_next('dd')
                risp = f"Il DNEL con queste condizioni:  {h3.text} è  {nxt.text}"
                dnel_matches.append(risp)
    
    return dnel_matches

def highlight_numbers(text):
    text = re.sub(r'(\d+,\d+\.?\d*)', r'<b style="color:red;">\1</b>', text)
    
    highlight_words = ["rat", "NOAEL", "LD50", "rats", "rabbits", "ld50", "g/kg", "mg/kg/day", "mg/kg"]
    if highlight_words:
        pattern = r'\b(' + '|'.join(re.escape(word) for word in highlight_words) + r')\b'
        text = re.sub(pattern, r'<span style="color:yellow">\1</span>', text)
    
    return text


@app.route(route="MyHttpTrigger", auth_level=func.AuthLevel.ANONYMOUS)
def MyHttpTrigger(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')

    with open('invecchia.json', 'r') as file:
            echa = json.load(file)
    lista_ing = list(echa.keys())
    lista_ing = sorted(lista_ing)

    ingrediente = req.params.get('ingrediente')
    if not ingrediente:
        try:
            req_body = req.get_json()
        except ValueError:
            pass
        else:
            ingrediente = req_body.get('ingrediente')
        return func.HttpResponse(f"Scrivi nella barra di ricerca ?ingrediente=uno della lista\nPer esempio http://127.0.0.1:7071/api/MyHttpTrigger?ingrediente=Aluminium Oxide\n\n{lista_ing}")

    if ingrediente:

        urlecha = echa.get(ingrediente)
        if urlecha:
            echalink = "https://echa.europa.eu/it/registration-dossier/-/registered-dossier/"+str(urlecha)+"/7/1"
            #print(f"Link al dossier Echa: [Clicca qui per visualizzare il dossier]({echalink})")
            response = requests.get(echalink)
            soup = BeautifulSoup(response.content, 'html.parser')
            dl = echadnel(soup)
            nl = echanoael(soup)

            response_body = {
                "NOAEL": nl,
                "DNEL": dl
                        }
            return func.HttpResponse(json.dumps(response_body), mimetype="application/json", status_code=200)

        return func.HttpResponse("Ingrediente non torvato")
    else:
        return func.HttpResponse(
             "This HTTP triggered function executed successfully. Pass an ingredient in the query string from the list.",
             status_code=200
        )