# backend/app/controllers/userController.py

import json
import os
import datetime
from typing import Optional, Tuple, Dict, Any
from bson import ObjectId, json_util
from controllers.pinsController import generate_pin_for_user
from controllers.util.email_utils import send_pin_email
from mongoConnection import db
import bcrypt
import stripe

# Database collections
users = db["users"]
subscriptions = db["subscriptions"]
pins = db["pins"]

# Constants
BCRYPT_ROUNDS = 10
PIN_LENGTH = 4


class UserController:
    """Controller for user management operations including CRUD and subscription handling."""

    def get_user_byId(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve user by ID with subscription data.

        Args:
            user_id: User's MongoDB ObjectId as string

        Returns:
            User data with subscription info or None if not found
        """
        user = users.find_one({"_id": ObjectId(user_id)}, {"password": 0})

        if not user:
            return None

        subscription_id = user.get("subscription_id")
        if subscription_id:
            try:
                stripe.api_key = os.getenv("STRIPE_SECRET")
                subscription = stripe.Subscription.retrieve(user.get("subscription_id"))
                user["subscription_active"] = subscription["plan"]["active"]
            except Exception as e:
                print(f"Error fetching subscription data: {e}")
                user["subscription_active"] = False

        print(user)
        return json.loads(json_util.dumps(user))

    def get_user(self, email: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve user by email.

        Args:
            email: User's email address

        Returns:
            User data or None if not found
        """
        user = users.find_one({"email": email})
        return json.loads(json_util.dumps(user)) if user else None

    def create_user(self, email: str, password: str) -> Tuple[Dict[str, Any], int]:
        """
        Create a new user with email verification PIN.

        Args:
            email: User's email address
            password: User's password (will be hashed)

        Returns:
            Tuple of (response_data, status_code)
        """
        # Input validation
        if not email or not password:
            return {"message": "Email and password are required"}, 400

        if len(password) < 6:
            return {"message": "Password must be at least 6 characters long"}, 400

        user = self.get_user(email)
        if user:
            return {"message": "Este usuario ya fue registrado"}, 400

        salt = bcrypt.gensalt(BCRYPT_ROUNDS)
        hashedpass = bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")

        # insert user and grab the new ObjectId
        created_id = users.insert_one(
            {
                "email": email,
                "password": hashedpass,
                "verified": False,
                "created_at": datetime.datetime.now(datetime.timezone.utc),
            }
        ).inserted_id

        # Generate PIN and send via email
        pin_code = generate_pin_for_user(str(created_id))
        send_pin_email(email, pin_code, str(created_id))

        return {"userId": str(created_id)}, 200

    def update_user(self, data: Dict[str, Any]) -> Tuple[Dict[str, Any], int]:
        """
        Update user data.

        Args:
            data: Dictionary containing user_id and fields to update

        Returns:
            Tuple of (response_data, status_code)
        """
        try:
            user_id = ObjectId(data.get("user_id", {}).get("$oid"))
            if not user_id:
                return {"message": "Invalid user_id format"}, 400

            data.pop("user_id", None)

            user = users.find_one_and_update(
                {"_id": user_id},
                {"$set": data},
                upsert=True,
                return_document=True,
            )
            return {"_id": str(user["_id"])}, 200

        except ValueError as e:
            return {"message": f"Invalid ObjectId format: {str(e)}"}, 400
        except Exception as e:
            return {"message": f"Error updating user: {str(e)}"}, 500

    def delete_user(self, user_id: str) -> Tuple[Dict[str, Any], int]:
        """
        Delete a user by ID.

        Args:
            user_id: User's MongoDB ObjectId as string

        Returns:
            Tuple of (response_data, status_code)
        """
        try:
            result = users.delete_one({"_id": ObjectId(user_id)})
            if result.deleted_count == 0:
                return {"message": "User not found"}, 404
            return {"message": "User deleted successfully"}, 200
        except ValueError as e:
            return {"message": f"Invalid ObjectId format: {str(e)}"}, 400
        except Exception as e:
            return {"message": f"Error deleting user: {str(e)}"}, 500

    def verify_user_email(
        self, user_id: str, pin_code: str
    ) -> Tuple[Dict[str, Any], int]:
        """
        Verify user email with PIN code.

        Args:
            user_id: User's MongoDB ObjectId as string
            pin_code: PIN code for verification

        Returns:
            Tuple of (response_data, status_code)
        """
        try:
            from controllers.pinsController import verify_user_pin

            if verify_user_pin(user_id, pin_code):
                return {"message": "Email verified successfully"}, 200
            else:
                return {"message": "Invalid or expired PIN code"}, 400
        except Exception as e:
            return {"message": f"Error verifying email: {str(e)}"}, 500
