import azure.functions as func
import json
import logging
import requests
from bs4 import BeautifulSoup
import re
import pandas as pd

# Altro codice :)

app = func.FunctionApp()

def extract_noael_and_ld50(text_pages):
    noael_pattern = re.compile(r'(.*?NOAEL.*?\d+\.?\d*\s*[a-zA-Z/]+.*?(\.|$))', re.IGNORECASE)
    ld50_pattern = re.compile(r'(.*?LD50.*?\d+\.?\d*\s*[a-zA-Z/]+.*?(\.|$))', re.IGNORECASE)
    
    noael_matches = []
    ld50_matches = []
    
    for text, page_num in text_pages:
        lines = text.split("\n")
        for i, line in enumerate(lines):
            if re.search(noael_pattern, line):
                previous_line = lines[i - 1] if i > 0 else ""
                formatted_match = highlight_numbers(f"{previous_line}\n{line}")
                noael_matches.append((formatted_match, page_num))
            if re.search(ld50_pattern, line):
                previous_line = lines[i - 1] if i > 0 else ""
                formatted_match = highlight_numbers(f"{previous_line}\n{line}")
                ld50_matches.append((formatted_match, page_num))
    
    return noael_matches, ld50_matches

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

    ingrediente = req.params.get('ingrediente')
    if not ingrediente:
        try:
            req_body = req.get_json()
        except ValueError:
            pass
        else:
            ingrediente = req_body.get('ingrediente')

    if ingrediente:
        with open('invecchia.json', 'r') as file:
            echa = json.load(file)
        lista_ing = list(echa.keys())

        urlecha = echa.get(ingrediente)
        if urlecha:
            echalink = "https://echa.europa.eu/it/registration-dossier/-/registered-dossier/"+str(urlecha)+"/7/1"
            print(f"Link al dossier Echa: [Clicca qui per visualizzare il dossier]({echalink})")
            response = requests.get(echalink)
            soup = BeautifulSoup(response.content, 'html.parser')
            dl = echadnel(soup)
            nl = echanoael(soup)

            noael_matches = [(highlight_numbers(noael),) for noael in nl]
            dnel_matches = [(highlight_numbers(dnel),) for dnel in dl]
            return (noael_matches, dnel_matches)

        return func.HttpResponse(noael_matches, dnel_matches)
    else:
        return func.HttpResponse(
             "This HTTP triggered function executed successfully. Pass an ingredient in the query string from the list.",
             status_code=200
        )