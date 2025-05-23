from datetime import datetime, timedelta, timezone

import jwt
from os import environ


class TokenController:

    def create_access_token(self, payload):
        return self._create_token(payload, environ.get("ACCESS_TOKEN_SECRET"), 180)

    def create_refresh_token(self, payload):
        return self._create_token(payload, environ.get("REFRESH_TOKEN_SECRET"), 180)

    def _create_token(self, payload: dict, secret_key: str, expiration: int):
        payload["iat"] = datetime.now(timezone.utc)
        payload["exp"] = datetime.now(timezone.utc) + timedelta(minutes=expiration)
        token = jwt.encode(payload, secret_key, algorithm="HS256")
        return token

    def check_token(self, token: str):
        token_data = jwt.decode(token, options={"verify_signature": False})
        if datetime.fromtimestamp(token_data.get("exp"), timezone.utc) > datetime.now(
            timezone.utc
        ):
            data = {
                "user_id": token_data.get("user_id"),
                "email": token_data.get("email"),
            }
            access_token = self.create_access_token(data)
            refresh_token = self.create_refresh_token(data)

            return {
                "isValid": True,
                "message": "Success",
                "access_token": access_token,
                "refresh_token": refresh_token,
                "email": token_data.get("email"),
                "user_id": token_data.get("user_id"),
                "roles": token_data.get("roles"),
            }
        return {"isValid": False}
