from datetime import datetime, timedelta, timezone

import jwt
import bcrypt
from os import environ
from mongoConnection import db
from bson import ObjectId
password_reset_tokens = db["password_reset_tokens"]
users = db["users"]

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

    def find_user_by_email(self, email):
        return users.find_one({"email": email})

    def create_password_reset_token(self, user_id, email):
        expiration_minutes = 30
        payload = {
            "user_id": str(user_id),
            "email": email,
        }
        token = self._create_token(payload, environ.get("RESET_TOKEN_SECRET"), expiration_minutes)

        # Guardar en MongoDB
        password_reset_tokens.insert_one({
            "token": token,
            "user_id": ObjectId(user_id),
            "used": False,
            "created_at": datetime.utcnow(),
            "expires_at": datetime.utcnow() + timedelta(minutes=expiration_minutes)
        })

        return token

    def verify_and_reset_password(self, token, new_password):
        try:
            payload = jwt.decode(token, environ.get("RESET_TOKEN_SECRET"), algorithms=["HS256"])
            user_id = payload["user_id"]

            record = password_reset_tokens.find_one({
                "token": token,
                "user_id": ObjectId(user_id),
                "used": False
            })

            if not record or record["expires_at"] < datetime.utcnow():
                return {"success": False, "message": "Token inválido o expirado."}

            # Obtener usuario y validar que la nueva contraseña sea distinta
            user = users.find_one({"_id": ObjectId(user_id)})
            if not user:
                return {"success": False, "message": "Usuario no encontrado."}

            current_hashed_password = user.get("password")
            if bcrypt.checkpw(new_password.encode("utf-8"), current_hashed_password.encode("utf-8")):
                return {
                    "success": False,
                    "message": "La nueva contraseña no puede ser igual a la actual."
                }

            # Hash seguro con bcrypt
            hashed_password = bcrypt.hashpw(new_password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
            users.update_one({"_id": ObjectId(user_id)}, {"$set": {"password": hashed_password}})

            # Marcar token como usado
            password_reset_tokens.update_one({"_id": record["_id"]}, {"$set": {"used": True}})

            return {"success": True, "message": "Contraseña actualizada exitosamente."}

        except jwt.ExpiredSignatureError:
            return {"success": False, "message": "El token ha expirado."}
        except jwt.DecodeError:
            return {"success": False, "message": "Token inválido."}
