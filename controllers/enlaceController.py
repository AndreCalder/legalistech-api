import os
import json
from bson import ObjectId, json_util
from flask import g, jsonify
from mongoConnection import db
import requests

files = db["files"]
enlace_url = "https://api.fiducia.com.mx/enlace/v1/"

enlace_key = os.getenv("ENLACE_KEY")


class EnlaceController:

    # Funcion para hacer peticiones a la API de Enlace Jurídico
    def make_request(self, endpoint, method="GET", request_params=None, data=None):
        url = enlace_url + endpoint

        params = {
            "apikey": enlace_key,
        }

        if request_params:
            params = {**params, **request_params}

        if method == "GET":
            headers = {"Content-Type": "application/json"}
            response = requests.get(url, headers=headers, params=params, timeout=15)
        elif method == "POST":
            headers = {
                "Content-Type": "application/json",
                "X-Http-Method-Override": "GET",
            }
            response = requests.request(
                "POST", url, headers=headers, params=params, data=data, timeout=15
            )
        return response.json()

    # Obtiene la lista de carpetas del usuario
    def get_files(self):
        user_files = files.find({"user_id": ObjectId(g.userId)})

        return jsonify(json.loads(json_util.dumps(user_files)))

    # Obtiene los estados de la API de Enlace Jurídico
    # devuelve la lista de estados en formato JSON
    def get_states(self):
        states = self.make_request("estados")
        return jsonify(states)

    # Obtiene los juzgados de la API de Enlace Jurídico
    # Recibe el estado como parámetro
    # devuelve la lista de juzgados en formato JSON
    def get_courts(self, state):

        courts = self.make_request(
            "juzgados",
            method="POST",
            data=json.dumps({"estado": state, "entidad": "estatal"}),
        )

        return jsonify(courts)
