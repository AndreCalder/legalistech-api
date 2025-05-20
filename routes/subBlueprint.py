from flask import Blueprint
from controllers.subController import Subscription_Controller

sub_Router = Blueprint("subRouter", __name__)
subController = Subscription_Controller()


@sub_Router.route("/", methods=["GET"])
def search():
    return subController.get_subscriptions()
