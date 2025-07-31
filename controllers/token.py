from datetime import datetime, timedelta, timezone
import jwt
import bcrypt
from os import environ
from mongoConnection import db
from bson import ObjectId
password_reset_tokens = db["password_reset_tokens"]
users = db["users"]
authSessions = db["authSessions"]


class TokenController:

    def create_access_token(self, payload):
        secret = environ.get("ACCESS_TOKEN_SECRET")
        if not secret:
            raise ValueError("ACCESS_TOKEN_SECRET environment variable is not set")
        return self._create_token(payload, "access", secret, 15)

    def create_refresh_token(self, payload):
        secret = environ.get("REFRESH_TOKEN_SECRET")
        if not secret:
            raise ValueError("REFRESH_TOKEN_SECRET environment variable is not set")
        return self._create_token(payload, "refresh", secret, 43200)

    def _create_token(
        self, payload: dict, token_type: str, secret_key: str, expiration: int
    ):
        payload = payload.copy()  # Avoid mutating the original payload
        payload["token_type"] = token_type  # Ensure token_type is set
        payload["iat"] = datetime.now(timezone.utc)
        payload["exp"] = datetime.now(timezone.utc) + timedelta(minutes=expiration)
        token = jwt.encode(payload, secret_key, algorithm="HS256")
        return token

    def check_token(self, token: str):
        try:
            # First, decode without verification to get the token type
            token_data = jwt.decode(token, options={"verify_signature": False})

            if token_data.get("token_type") == "access":
                secret_key = environ.get("ACCESS_TOKEN_SECRET")
            else:
                secret_key = environ.get("REFRESH_TOKEN_SECRET")

            # Verify the signature
            verified_token_data = jwt.decode(token, secret_key, algorithms=["HS256"])

            if datetime.fromtimestamp(
                verified_token_data.get("exp"), timezone.utc
            ) > datetime.now(timezone.utc):
                data = {
                    "user_id": verified_token_data.get("user_id"),
                    "email": verified_token_data.get("email"),
                }
                access_token = self.create_access_token(data)
                refresh_token = self.create_refresh_token(data)

                return {
                    "isValid": True,
                    "message": "Success",
                    "access_token": access_token,
                    "refresh_token": refresh_token,
                    "email": verified_token_data.get("email"),
                    "user_id": verified_token_data.get("user_id"),
                }
            else:
                return {"isValid": False, "message": "Token expired"}

        except jwt.InvalidSignatureError:
            return {"isValid": False, "message": "Invalid token signature"}
        except jwt.InvalidTokenError:
            return {"isValid": False, "message": "Invalid token"}
        except Exception as e:
            return {"isValid": False, "message": f"Token verification failed: {str(e)}"}
