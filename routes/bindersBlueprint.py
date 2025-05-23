from flask import Blueprint
from controllers.bindersController import BindersController

bindersController = BindersController()
binders_Router = Blueprint("bindersRouter", __name__)

# List locally stored binders for the current user
@binders_Router.route("/", methods=["GET"])
def list_binders():
    return bindersController.list_binders()
