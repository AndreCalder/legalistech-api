import json
from bson import json_util
from flask import jsonify
from mongoConnection import db

subscriptions = db["subscriptions"]


class Subscription_Controller:
    def get_subscriptions(self):
        subs = subscriptions.find()

        return jsonify(json.loads(json_util.dumps(subs)))

    def get_subscription(self, price_id):

        sub = subscriptions.find_one({"priceId": price_id}, {"_id": 0})

        if sub:
            return sub
        else:
            return {}
