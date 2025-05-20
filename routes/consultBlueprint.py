from flask import Blueprint, request
from controllers.consultController import ConsultController

consultController = ConsultController()
consult_Router = Blueprint("consultRouter", __name__)


@consult_Router.route("/", methods=["POST"])
def search():
    req = request.json
    search = req.get("query")

    return consultController.search(search)
