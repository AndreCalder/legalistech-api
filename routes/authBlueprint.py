from flask import Blueprint, request
from controllers.token import TokenController
from controllers.authController import AuthController

auth_Router = Blueprint("authBlueprint", __name__)
authController = AuthController()
tokenController = TokenController()


@auth_Router.route("/login", methods=["POST"])
def login():
    req = request.json or {}
    email = req.get("email")
    pwd = req.get("password")

    if not email or not pwd:
        return {"message": "Authentication required"}, 400

    return authController.login(email, pwd)


@auth_Router.route("/validatetoken", methods=["POST"])
def validateToken():
    token_data = tokenController.check_token(request.headers.get("Authorization", ""))

    if token_data.get("isValid"):
        return {
            "message": "Success",
            "access_token": token_data.get("access_token"),
            "refresh_token": token_data.get("refresh_token"),
            "email": token_data.get("email"),
        }, 200

    return {"message": "Session terminated"}, 400

# Solicitar token de recuperación (via email)
@auth_Router.route("/requestReset", methods=["POST"])
def request_password_reset():
    req = request.json or {}
    email = req.get("email")

    if not email:
        return {"message": "Email is required"}, 400

    user = tokenController.find_user_by_email(email)
    if not user:
        return {"message": "User not found"}, 404

    token = tokenController.create_password_reset_token(user["_id"], user["email"])
    # Puedes agregar aquí lógica para enviar el token por email

    return {"message": "Token de recuperación generado", "token": token}, 200


# Usar token y cambiar password
@auth_Router.route("/resetPassword", methods=["POST"])
def reset_password():
    req = request.json or {}
    token = req.get("token")
    new_password = req.get("new_password")

    if not token or not new_password:
        return {"message": "Token and new password required"}, 400

    return tokenController.verify_and_reset_password(token, new_password)