from flask import Blueprint, request
from controllers.consultController import ConsultController

consultController = ConsultController()
consult_Router = Blueprint("consultRouter", __name__)


"""
{
    "query": "search term",
    "document": "Specific document to search in"
}
"""


@consult_Router.route("/", methods=["POST"])
def search():
    req = request.json
    query = req.get("query")
    document = req.get("document")
    return consultController.search(query, document)

@consult_Router.route("/<id>", methods=["GET"])
def get_by_id(id):
    return consultController.get_by_id(id)