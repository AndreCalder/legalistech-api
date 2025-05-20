from bson import ObjectId
import pymongo
import certifi
from os import environ

client = pymongo.MongoClient(
    "mongodb+srv://andrecalder98:LFgw87KNYZ2OjZOK@qgo.xywmfco.mongodb.net/?retryWrites=true&w=majority&appName=qGo",
    tlsCAFile=certifi.where(),
)
db = client["milegalista"]
sentencias = db["sentencias"]

categorias = {
    "Divorcios": ["Divorcio", "Divorcio Incausado"],
    "Sucesiones Testamentarias": [
        "Juicio Sucesorio Testamentario",
        "Sucesión Testamentaria",
        "Juicio Sucesorio Testamentario Acumulado",
        "Sucesorio Testamentario",
    ],
    "Sucesiones Intestamentarias": [
        "Juicio Sucesorio Intestamentario",
        "Juicio Sucesorio Intestamentario Acumulado",
        "Juicio Especial Intestamentario",
    ],
    "Diligencias Voluntarias de Identidad y Estado Civil": [
        "Diligencias de Jurisdicción Voluntaria, Identidad de Persona"
    ],
    "Diligencias Voluntarias de Validación y Reconocimiento Judicial": [
        "Diligencias de Jurisdicción Voluntaria, Homologación de Sentencia"
    ],
    "Diligencias Voluntarias de Discapacidad": [
        "Diligencias de Jurisdicción Voluntaria, Declaración de Grado de Discapacidad",
        "Diligencias de Jurisdicción Voluntaria, Estado de Incapacidad",
        "Diligencias de Jurisdicción Voluntaria, Discapacidad",
        "Diligencias de Jurisdicción Voluntaria, Discapacidad (Interdicción)",
        "Diligencias de Jurisdicción Voluntaria, Declaración de Estado de Interdicción",
    ],
    "Controversias Familiares": [
        "Controversia del Orden Familiar",
        "Controversia del Orden Familiar, Alimentos por Comparecencia",
        "Controversia del Orden Familiar, Guarda, Custodia y Alimentos",
    ],
    "Diligencias Notariales": [
        "Diligencias de Declaración Formal de Testamento Ológrafo",
        "Ratificación de las Firmas de Cesión de Derechos Hereditarios",
        "Incidente de Cancelación de Pensión Alimenticia",
        "Incidente de Adjudicación Suplementaria",
    ],
    "Procesos Ejecutivos y Medidas de Protección": [
        "Vía de Apremio",
        "Medidas de Protección",
    ],
    "Juicios Ordinarios Civiles": [
        "Juicio Ordinario Civil de Petición de Herencia",
        "Juicio Ordinario Civil, Reconocimiento de Paternidad",
    ],
}


# Función para categorizar los casos
def categorizar_caso(tipo_caso):
    for categoria, palabras_clave in categorias.items():
        if any(palabra in tipo_caso for palabra in palabras_clave):
            return categoria
    print(" ============ " + tipo_caso + " ============ ")
    return "Otros"


for sentencia in sentencias.find():
    tipo_caso = sentencia["case_info"]["case_type"]
    categoria = categorizar_caso(tipo_caso)
    sentencias.update_one({"_id": ObjectId(sentencia["_id"])},{"$set": {"case_info.case_type": categoria}})
