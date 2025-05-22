import bcrypt
from controllers.token import TokenController
from controllers.userController import UserController

class AuthController:

    def __init__(self):
        self.token = TokenController()
        self.user  = UserController()

    def login(self, email: str, password: str):
        """
        Authenticate by email and password.
        """
        user = self.user.get_user(email)

        if not user:
            return {"message": "Email or password is incorrect"}, 400

        stored_hash = user.get("password")
        # bcrypt wants bytes
        is_match = bcrypt.checkpw(
            password.encode("utf-8"),
            stored_hash.encode("utf-8")
        )
        if not is_match:
            return {"message": "Email or password is incorrect"}, 400

        data = {
            "user_id": user.get("_id").get("$oid"),
            "email":   user.get("email"),
        }

        access_token  = self.token.create_access_token(data)
        refresh_token = self.token.create_refresh_token(data)

        return {
            "message":       "Success",
            "access_token":  access_token,
            "refresh_token": refresh_token,
        }, 200
