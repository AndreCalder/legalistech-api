from flask import Blueprint, request
from controllers.token import TokenController
from controllers.authController import AuthController

auth_Router    = Blueprint("authBlueprint", __name__)
authController = AuthController()
tokenController= TokenController()

@auth_Router.route("/login", methods=["POST"])
def login():
    req   = request.json or {}
    email = req.get("email")
    pwd   = req.get("password")

    if not email or not pwd:
        return {"message": "Authentication required"}, 400

    return authController.login(email, pwd)


@auth_Router.route("/validatetoken", methods=["POST"])
def validateToken():
    token_data = tokenController.check_token(
        request.headers.get("Authorization", "")
    )

    if token_data.get("isValid"):
        return {
            "message":       "Success",
            "access_token":  token_data.get("access_token"),
            "refresh_token": token_data.get("refresh_token"),
            "email":         token_data.get("email"),
        }, 200

    return {"message": "Session terminated"}, 400
