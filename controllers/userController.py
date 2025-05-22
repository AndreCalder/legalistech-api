# backend/app/controllers/userController.py

import json
import os
import datetime
from bson import ObjectId, json_util
from controllers.pinsController import generate_pin_for_user
from mongoConnection import db
import bcrypt
import stripe

users = db["users"]
subscriptions = db["subscriptions"]
pins = db["pins"]


class UserController:

    def get_user_byId(self, user_id):
        user = users.find_one({"_id": ObjectId(user_id)}, {"password": 0})

        # Add subscription data to user
        customer_id = user.get("customer_id")
        if customer_id:
            stripe.api_key = os.getenv("STRIPE_SECRET")
            subs = stripe.Subscription.list(customer=customer_id)
            subscription = subs.data[0]
            user["subscription"] = subscription

            subPack = subscriptions.find_one({"priceId": subscription.plan.id})
            user["subPack"] = subPack

        return json.loads(json_util.dumps(user))

    def get_user(self, email):
        user = users.find_one({"email": email})
        return json.loads(json_util.dumps(user))

    def create_user(self, email, password):
        user = self.get_user(email)
        if user:
            return {"message": "Este usuario ya fue registrado"}, 400

        salt = bcrypt.gensalt(10)
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

        generate_pin_for_user(str(created_id))

        # TODO: send pin_code via email here

        return {"userId": str(created_id)}, 200

    def update_user(self, data):
        try:
            user_id = ObjectId(data.get("user_id").get("$oid"))
            data.pop("user_id", None)

            user = users.find_one_and_update(
                {"_id": user_id},
                {"$set": data},
                upsert=True,
                return_document=True,
            )
            return {"_id": str(user["_id"])}, 200

        except Exception as e:
            return {"message": str(e)}, 400
