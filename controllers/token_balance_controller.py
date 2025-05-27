import datetime
from bson import ObjectId
from flask import jsonify
from mongoConnection import db

users = db["users"]


class Token_Balance_Controller:

    def get_token_balance_raw(self, user_id):
        user = users.find_one({"_id": ObjectId(user_id)})
        monthly_tokens = user.get("monthly_tokens", 0)
        active_packs = [
            p
            for p in user.get("purchased_packs", [])
            if p["expires_at"] > datetime.datetime.now()
        ]
        purchased_tokens = sum([p["tokens_remaining"] for p in active_packs])
        return monthly_tokens + purchased_tokens, monthly_tokens, purchased_tokens

    def get_token_balance_byId(self, user_id):
        total, monthly, purchased = self.get_token_balance_raw(user_id)

        return jsonify(
            {
                "token_balance": total,
                "monthly_tokens": monthly,
                "purchased_tokens": purchased,
            }
        )

    def use_tokens(self, user_id, amount):
        user = users.find_one({"_id": ObjectId(user_id)})
        token_balance, _, _ = self.get_token_balance_raw(user_id)
        active_packs = [
            p
            for p in user.get("purchased_packs", [])
            if p["expires_at"] > datetime.now()
        ]
        if token_balance < amount:
            return {"message": "Insufficient tokens"}, 400

        if user["monthly_tokens"] >= amount:
            user["monthly_tokens"] -= amount
            amount = 0

        elif user["monthly_tokens"] < amount:
            amount -= user["monthly_tokens"]
            user["monthly_tokens"] = 0

        if amount > 0:
            for pack in active_packs:
                if pack["tokens_remaining"] >= amount:
                    pack["tokens_remaining"] -= amount
                    amount = 0
                    break
                else:
                    amount -= pack["tokens_remaining"]
                    pack["tokens_remaining"] = 0
                    pack["used_up"] = True

        users.find_one_and_update(
            {"_id": ObjectId(user_id)},
            {
                "$set": {
                    "monthly_tokens": user["monthly_tokens"],
                    "purchased_packs": active_packs,
                }
            },
            upsert=True,
        )
