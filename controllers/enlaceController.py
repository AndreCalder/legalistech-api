from flask import jsonify, g
from controllers.util.enlace_base import EnlaceBase
from mongoConnection import db
from bson import ObjectId
import json
from bson import json_util

binders = db["binders"]


class EnlaceController(EnlaceBase):

    # === Expedient Methods ===

    # Search an expedient by number, court, etc.
    def search_expedient(self, payload):
        return jsonify(
            self.make_request("expedientes", method="POST", data=json.dumps(payload))
        )

    # Retrieve full history of a given expedient
    def get_expedient_history(self, payload):
        return jsonify(
            self.make_request(
                "expedientes/historial", method="POST", data=json.dumps(payload)
            )
        )

    # Suggest related expedients based on filters (AI assistant)
    def get_expedients_by_binder(self, binder_id):
        binder = binders.find_one({
            "user_id": ObjectId(g.userId),
            "carpeta_id": int(binder_id)  # ensure numeric match
        })
        if not binder:
            return jsonify({"error": "Binder not found"}), 404

        payload = {
            "estado": binder["estado"],
            "entidad": "estatal",
            "carpeta_id": binder["carpeta_id"]
        }

        # POST + override GET, per Fiducia collection
        response = self.make_request(
            "carpetas/expedientes",
            method="POST",
            override="GET",
            data=json.dumps(payload)
        )

        if isinstance(response, dict) and response.get("error"):
            return jsonify({"error": "Enlace error", "details": response}), 502

        return jsonify(response)

    # Get list of states from Enlace
    def get_states(self):
        return jsonify(self.make_request("estados"))

    # Get list of courts for a given state
    def get_courts(self, state):
        payload = {"estado": state, "entidad": "estatal"}
        return jsonify(
            self.make_request("juzgados", method="POST", data=json.dumps(payload))
        )

    # === Binder Methods (via Enlace API) ===

    # Create a binder using Enlace API and store locally
    def create_binder(self, payload):
        response = self.make_request(
            "carpetas", method="POST", data=json.dumps(payload)
        )

        estado = payload.get("estado")
        carpetas = response.get("carpetas").get("estatal")

        # Find the carpeta in carpetas where carpeta == payload.get("carpeta")
        target_carpeta = next(
            (c for c in carpetas if c["carpeta"] == payload.get("carpeta")), None
        )

        if target_carpeta:
            binders.insert_one(
                {
                    "user_id": ObjectId(g.userId),
                    "carpeta_id": target_carpeta["carpeta_id"],
                    "carpeta": target_carpeta["carpeta"],
                    "estado": estado,
                    "creada": target_carpeta["creada"],
                }
            )

        return jsonify(
            {
                "message": "Binder created via API and stored locally",
                "api_response": response,
            }
        )

    def get_binders(self):
        # 1) Pull the user’s binders from Mongo
        cursor = binders.find({"user_id": ObjectId(g.userId)}, {"_id": 0, "carpeta_id": 1, "estado": 1})
        mongo_binders = list(cursor)

        if not mongo_binders:
            return jsonify([])  # no binders saved for this user

        # 2) Group carpeta_ids by estado (Enlace requires estado to list)
        by_estado = {}
        for b in mongo_binders:
            estado = b.get("estado")
            carpeta_id = b.get("carpeta_id")
            if estado is None or carpeta_id is None:
                # skip malformed rows
                continue
            by_estado.setdefault(estado, set()).add(int(carpeta_id))

        # 3) For each estado, call Enlace "Listar Carpetas" and filter by our carpeta_ids
        matched = []

        for estado, carpeta_ids in by_estado.items():
            # Enlace wants POST with X-Http-Method-Override: GET
            payload = {"estado": estado, "entidad": "estatal"}

            # NOTE: we need a way to force POST + override GET. See make_request note below.
            resp = self.make_request(
                "carpetas",
                method="GET",            # if your make_request actually sends GET, this may work
                override="GET",
                data=json.dumps(payload) # some servers ignore body on GET; safer to do POST+override
            )

            # Defend against API errors / shapes
            if not isinstance(resp, dict):
                continue

            # Enlace response shape (per your Postman): {"carpetas": {"estatal": [ {...}, ... ]}}
            estatales = (resp.get("carpetas") or {}).get("estatal") or []
            if not isinstance(estatales, list):
                continue

            # 4) Keep only binders whose carpeta_id is in our user’s set
            for c in estatales:
                try:
                    cid = int(c.get("carpeta_id"))
                except (TypeError, ValueError):
                    continue
                if cid in carpeta_ids:
                    matched.append(c)

        return jsonify(matched)


    # Rename binder using Enlace API and update local copy
    def rename_binder(self, binder_id, payload):
        response = self.make_request(
            "carpetas/renombrar", method="POST", data=json.dumps(payload)
        )

        binders.update_one(
            {"carpeta_id": binder_id, "user_id": ObjectId(g.userId)},
            {"$set": {"carpeta": payload.get("carpeta")}},
        )

        return jsonify(
            {
                "message": "Binder renamed via API and updated locally",
                "api_response": response,
            }
        )

    # Delete binder via Enlace API and remove local reference
    def delete_binder(self, binder_id, payload):
        response = self.make_request(
            "carpetas/eliminar", method="POST", data=json.dumps(payload)
        )

        binders.delete_one({"carpeta_id": binder_id, "user_id": ObjectId(g.userId)})

        return jsonify(
            {
                "message": "Binder deleted via API and removed locally",
                "api_response": response,
            }
        )
