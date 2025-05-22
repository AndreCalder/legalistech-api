from flask import Blueprint, request
from controllers.enlaceController import EnlaceController

enlaceController = EnlaceController()
enlace_Router = Blueprint("enlaceRouter", __name__)


@enlace_Router.route(("/estados"), methods=["GET"])
def get_states():
    return enlaceController.get_states()


@enlace_Router.route("/juzgados", methods=["POST"])
def get_courts():
    req = request.json
    state = req.get("estado")

    return enlaceController.get_courts(state)


@enlace_Router.route("/carpetas", methods=["GET"])
def get_files():
    req = request.json
    search = req.get("query")

    return enlaceController.get_files(search)
