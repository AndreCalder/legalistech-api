from flask import Blueprint, request, g
from controllers.enlaceController import EnlaceController
from controllers.token import TokenController

tokenController = TokenController()
enlaceController = EnlaceController()
enlace_Router = Blueprint("enlaceRouter", __name__)

@enlace_Router.before_request
def validate_token():
    if request.method != "OPTIONS":
        token_data = tokenController.check_token(request.headers["Authorization"])
        g.userId = token_data.get("user_id")


# Fetch available states from Enlace API
@enlace_Router.route("/states", methods=["GET"])
def get_states():
    return enlaceController.get_states()

# Fetch courts for a given state
@enlace_Router.route("/courts", methods=["POST"])
def get_courts():
    return enlaceController.get_courts(request.json.get("estado"))

# Search expedient by number/year/etc.
@enlace_Router.route("/expedients", methods=["POST"])
def search_expedient():
    return enlaceController.search_expedient(request.json)

# Get historical data for an expedient
@enlace_Router.route("/expedients/history", methods=["POST"])
def get_expedient_history():
    return enlaceController.get_expedient_history(request.json)

# Match or suggest related expedients (assistant)
@enlace_Router.route("/assistant", methods=["POST"])
def match_expedients():
    return enlaceController.match_expedients(request.json)

# Create binder via Enlace API + store locally
@enlace_Router.route("/binders", methods=["POST"])
def create_binder():
    return enlaceController.create_binder(request.json)

# Rename binder via Enlace API + update locally
@enlace_Router.route("/binders/<binder_id>", methods=["PUT"])
def rename_binder(binder_id):
    return enlaceController.rename_binder(binder_id, request.json)

# Delete binder via Enlace API + delete locally
@enlace_Router.route("/binders/<binder_id>", methods=["DELETE"])
def delete_binder(binder_id):
    return enlaceController.delete_binder(binder_id, request.json)
