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
    def match_expedients(self, payload):
        return jsonify(
            self.make_request("asistente", method="POST", data=json.dumps(payload))
        )

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
        user_binders = binders.find({"user_id": ObjectId(g.userId)})
        return jsonify(json.loads(json_util.dumps(user_binders)))

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
