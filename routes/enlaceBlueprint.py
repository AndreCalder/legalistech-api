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


# Create binder via Enlace API + store in DB
@enlace_Router.route("/binders", methods=["POST"])
def create_binder():
    return enlaceController.create_binder(request.json)

# Fetch all binders belonging to the user
@enlace_Router.route("/binders", methods=["GET"])
def get_binders():
    return enlaceController.get_binders()

# List expedients inside a given binder
@enlace_Router.route("/binders/<binder_id>/expedients", methods=["GET"])
def get_expedients_by_binder(binder_id):
    return enlaceController.get_expedients_by_binder(binder_id)


# Rename binder via Enlace API + update in DB
@enlace_Router.route("/binders/<binder_id>", methods=["PUT"])
def rename_binder(binder_id):
    return enlaceController.rename_binder(binder_id, request.json)


# Delete binder via Enlace API + delete from DB
@enlace_Router.route("/binders/<binder_id>", methods=["DELETE"])
def delete_binder(binder_id):
    return enlaceController.delete_binder(binder_id, request.json)
