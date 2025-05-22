import random
from datetime import datetime, timezone
from bson import ObjectId
from mongoConnection import db

# collections
users = db["users"]
pins = db["pins"]


def generate_pin_for_user(user_id: str) -> str:
    """
    Create & store a 4-digit PIN for the given user.
    Raises ValueError if user not found.
    Returns the PIN.
    """
    if not users.find_one({"_id": ObjectId(user_id)}):
        raise ValueError("User not found")

    pin_code = f"{random.randint(1000, 9999)}"
    pins.insert_one(
        {
            "user_id": ObjectId(user_id),
            "pin_code": pin_code,
            "created_at": datetime.now(timezone.utc),
            "PIN_used": False,
        }
    )
    return pin_code


def verify_user_pin(user_id: str, pin_code: str) -> bool:
    """
    Check for a non-used PIN matching user_id+pin_code.
    If found, mark it used and set confirmed_acc on the user.
    Returns True if successful, False otherwise.
    """
    pin_doc = pins.find_one(
        {"user_id": ObjectId(user_id), "pin_code": pin_code, "PIN_used": False}
    )
    if not pin_doc:
        return False

    pins.update_one({"_id": pin_doc["_id"]}, {"$set": {"PIN_used": True}})
    users.update_one({"_id": ObjectId(user_id)}, {"$set": {"confirmed_acc": True}})
    return True
