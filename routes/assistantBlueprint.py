from flask import Blueprint, request, g
from controllers.assistantController import AssistantController
from controllers.token import TokenController

assistant_Router = Blueprint("assistantBlueprint", __name__)
assistantController = AssistantController()
tokenController = TokenController()


@assistant_Router.before_request
def validate_token():
    if request.method != "OPTIONS":
        token_data = tokenController.check_token(request.headers["Authorization"])
        g.userId = token_data.get("user_id")


@assistant_Router.route("/createsession", methods=["POST"])
def create_session():
    return assistantController.createSession(request)


@assistant_Router.route("/getsessions/", methods=["GET"])
def get_sessions():
    return assistantController.getUserSessions()


@assistant_Router.route("/getsession/<id>", methods=["GET"])
def get_session(id):
    return assistantController.getSession(id)


@assistant_Router.route("/updatesession/<id>", methods=["PUT"])
def update_session(id):
    body = request.json
    body["session_id"] = id
    return assistantController.updateSession(body)


@assistant_Router.route("/sendMsg/<id>", methods=["POST"])
def send_msg(id):
    return assistantController.chatSession(id, request)
