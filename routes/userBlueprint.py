from flask import Blueprint, request, g
from controllers.userController import UserController
from controllers.token import TokenController

user_Router = Blueprint("usersBlueprint", __name__)
userController = UserController()
tokenController = TokenController()


@user_Router.before_request
def validate_token():
    if request.method in ["OPTIONS"] or (
        request.method == "POST" and request.path == "/users/"
    ):
        return
    token_data = tokenController.check_token(request.headers["Authorization"])

    if not token_data.get("isValid"):
        return {"message": "Invalid token"}, 401

    g.userId = token_data.get("user_id")


@user_Router.route("/", methods=["POST"])
def createUser():
    req = request.json
    email = req.get("email")
    password = req.get("password")
    return userController.create_user(email, password)


@user_Router.route("/getCurrentUser", methods=["GET"])
def getCurrentUser():
    return userController.get_user_byId(g.userId)


@user_Router.route("/getByName", methods=["GET"])
def getUser():
    username = request.args.to_dict().get("username")
    if username:
        user = userController.get_user(username)
        if user:
            return user, 200
        else:
            return {"message": "User not found"}, 204
    else:
        return {"message": "Invalid request"}, 400


@user_Router.route("/update/<id>", methods=["PUT"])
def updateUser(id):
    data = request.json
    data["user_id"] = {
        "$oid": id
    }
    return userController.update_user(data)
