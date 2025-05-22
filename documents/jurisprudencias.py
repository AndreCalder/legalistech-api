import json
import requests
from jurisprudencias_data import jurisprudencias_complete
import re

"""

base_url = "https://sjf2.scjn.gob.mx/services/sjftesismicroservice/api/public/tesis"

pages = 8

body = {
    "classifiers": [
        {
            "name": "idEpoca",
            "value": ["200", "100", "5"],
            "allSelected": False,
            "visible": False,
            "isMatrix": False,
        },
        {
            "name": "numInstancia",
            "value": ["6", "1", "2", "7"],
            "allSelected": False,
            "visible": False,
            "isMatrix": False,
        },
        {
            "name": "idTipoTesis",
            "value": ["1"],
            "allSelected": False,
            "visible": False,
            "isMatrix": False,
        },
        {
            "name": "tipoDocumento",
            "value": ["1"],
            "allSelected": False,
            "visible": False,
            "isMatrix": False,
        },
        {
            "name": "tipoTesis",
            "value": ["Jurisprudencia"],
            "allSelected": False,
            "visible": True,
            "isMatrix": False,
        },
    ],
    "searchTerms": [],
    "bFacet": True,
    "ius": [],
    "idApp": "SJFAPP2020",
    "lbSearch": [
        "11a. Época - Pleno",
        "11a. Época - 1a. Sala",
        "11a. Época - 2a. Sala",
        "11a. Época - TCC",
        "10a. Época - Pleno",
        "10a. Época - 1a. Sala",
        "10a. Época - 2a. Sala",
        "10a. Época - TCC",
    ],
 
    "filterExpression": "",
}

jurisprudencias = []

for page_num in range(0, pages):
    if page_num > 0:
        searchParams = {"page": page_num, "size": 2000}
    else:
        searchParams = {"size": 2000}
    response = requests.post(
        base_url,
        headers={"Content-Type": "application/json"},
        json=body,
        params=searchParams,
    )
    jurisprudencias.extend(response.json().get("documents"))
    
output_filename = "jurisprudencias.json"

with open(output_filename, "w") as f:
    json.dump(jurisprudencias, f, indent=4)

"""


def remove_html_tags(text: str) -> str:
    clean_text = re.sub(r"<.*?>", "", text or "")
    return clean_text


def remove_accented_vowels(text: str) -> str:
    replacements = {
        "á": "a",
        "é": "e",
        "í": "i",
        "ó": "o",
        "ú": "u",
        "Á": "A",
        "É": "E",
        "Í": "I",
        "Ó": "O",
        "Ú": "U",
    }
    for accented, plain in replacements.items():
        text = text.replace(accented, plain)
    return text


modified_jurisprudencias = []
# len(jurisprudencias_complete)
for i in range(0, len(jurisprudencias_complete)):

    jurisprudencia = jurisprudencias_complete[i]
    ius = jurisprudencia.get("ius")
    get_url = f"https://sjf2.scjn.gob.mx/services/sjftesismicroservice/api/public/tesis/{ius}?isSemanal=true&hostName=https://sjf2.scjn.gob.mx"  # noqa

    response = requests.get(get_url, timeout=10)
    data = response.json()
    jurisprudencia["rubro"] = remove_accented_vowels(jurisprudencia.get("rubro"))
    jurisprudencia["textoPublicacion"] = remove_accented_vowels(
        jurisprudencia.get("textoPublicacion")
    )
    jurisprudencia["fuente"] = remove_accented_vowels(jurisprudencia.get("fuente"))
    jurisprudencia["epocaAbr"] = remove_accented_vowels(jurisprudencia.get("epocaAbr"))
    jurisprudencia["localizacion"] = remove_accented_vowels(
        jurisprudencia.get("localizacion")
    )

    if remove_html_tags(data.get("texto")) == "":
        jurisprudencia["texto"] = jurisprudencia.get("rubro")
    else:
        jurisprudencia["texto"] = remove_accented_vowels(
            remove_html_tags(data.get("texto"))
            + " === PRECEDENTES === "
            + remove_html_tags(data.get("precedentes"))
        )
    modified_jurisprudencias.append(jurisprudencia)

output_filename = "jurisprudencias_complete.json"

with open(output_filename, "w") as f:
    json.dump(modified_jurisprudencias, f, indent=4)
