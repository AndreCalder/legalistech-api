import bcrypt
from controllers.token import TokenController
from controllers.userController import UserController


class AuthController:

    def __init__(self):
        self.token = TokenController()
        self.user = UserController()

    def login(self, username, password):
        user = self.user.get_user(username)

        if not user:
            return {"message": "Username or Password is Incorrect"}, 400

        userPass = user.get("password")
        password = password.encode("utf-8")
        hashed_pass = userPass.encode("utf-8")

        is_match = bcrypt.checkpw(password, hashed_pass)

        if not is_match:
            return {"message": "Username or Password is Incorrect"}, 400

        data = {
            "user_id": user.get("_id").get("$oid"),
            "username": user.get("username"),
        }

        access_token = self.token.create_access_token(data)
        refresh_token = self.token.create_refresh_token(data)
        return {
            "message": "Success",
            "access_token": access_token,
            "refresh_token": refresh_token,
        }, 200
