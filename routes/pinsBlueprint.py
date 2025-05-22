from flask import Blueprint, request
from controllers.pinsController import generate_pin_for_user, verify_user_pin

pins_bp = Blueprint("pins", __name__)

@pins_bp.route("/", methods=["POST"])
def create_pin():
    data    = request.get_json(force=True) or {}
    user_id = data.get("user_id")
    if not user_id:
        return {"error": "user_id is required"}, 400

    try:
        pin = generate_pin_for_user(user_id)
    except ValueError as e:
        return {"error": str(e)}, 404

    # TODO: integrate email sending here
    return {"message": "PIN generated", "pin_code": pin}, 201

@pins_bp.route("/verify", methods=["POST"])
def verify_pin():
    data     = request.get_json(force=True) or {}
    user_id  = data.get("user_id")
    pin_code = data.get("pin_code")
    if not user_id or not pin_code:
        return {"error": "user_id and pin_code are required"}, 400

    if not verify_user_pin(user_id, pin_code):
        return {"error": "Invalid or already used PIN"}, 400

    return {"message": "Account verified successfully"}, 200
