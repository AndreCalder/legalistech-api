from flask import g, jsonify
from bson import ObjectId, json_util
from mongoConnection import db

binders = db["binders"]

class BindersController:

    # Return all binders for current user from local DB
    def list_binders(self):
        user_binders = binders.find({"user_id": ObjectId(g.userId)})
        return jsonify(json_util.loads(json_util.dumps(user_binders)))
