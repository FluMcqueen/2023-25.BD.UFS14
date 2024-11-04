import azure.functions as func
import json
import logging
import requests
from bs4 import BeautifulSoup
import fitz 
import re
import pandas as pd

# Altro codice :)

app = func.FunctionApp()

def get_pdf_link(ingredient_id):
    url = f"https://cir-reports.cir-safety.org/cir-ingredient-status-report/?id={ingredient_id}"
    response = requests.get(url).text
    soup = BeautifulSoup(response, "lxml")
    tab = soup.find("table")
    attach = tab.find("a")
    pidieffe = attach["href"]
    linktr = str(pidieffe).replace("../", "")
    pdf_link = "https://cir-reports.cir-safety.org/" + linktr
    return pdf_link

def extract_text_from_pdf_url(url):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            pdf_data = response.content
            text_pages = []
            document = fitz.open(stream=pdf_data, filetype="pdf")
            for page_num in range(len(document)):
                try:
                    page = document.load_page(page_num)
                    page_text = page.get_text()
                    if page_text:
                        text_pages.append((page_text, page_num + 1))
                    else:
                        print(f"Nessun testo trovato nella pagina {page_num + 1}")
                except Exception as e:
                    print(f"Errore durante l'estrazione del testo dalla pagina {page_num + 1}: {str(e)}")
            return text_pages
        else:
            print(f"Errore durante l'apertura del PDF. Codice di stato: {response.status_code}")
    except Exception as e:
        print(f"Errore generale durante l'operazione di estrazione del testo dal PDF: {str(e)}")


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
        with open('cirjs.json', 'r') as file:
            cir = json.load(file)
        lista_ing = list(cir.keys())
        ingredient_id = cir.get(ingrediente)

        if ingredient_id:
            pdf_link = get_pdf_link(ingredient_id)

            try:
                text_pages = extract_text_from_pdf_url(pdf_link)
                        
                noael_matches, ld50_matches = extract_noael_and_ld50(text_pages)
                        
                if noael_matches:
                    noael_df = pd.DataFrame(noael_matches, columns=["NOAEL value", "Page"])
                    print("NOAEL")
                        
                if ld50_matches:
                    ld50_df = pd.DataFrame(ld50_matches, columns=["LD50 value", "Page"])
                    print("LD50")
                        
                if not noael_matches and not ld50_matches:
                    print("Nessun valore NOAEL o LD50 trovato.")                            
                        
            except Exception as e:
                return (f"ERRORE: {e}")

        return func.HttpResponse(f"Hello, {ingrediente}. This HTTP triggered function executed successfully.")
    else:
        return func.HttpResponse(
             "This HTTP triggered function executed successfully. Pass a ingrediente in the query string or in the request body for a personalized response.",
             status_code=200
        )