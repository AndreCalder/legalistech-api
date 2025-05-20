from datetime import datetime
import os
import stripe
from flask import g, jsonify
from controllers.subController import Subscription_Controller
from controllers.userController import UserController
from mongoConnection import db

payment_intents = db["payment_intents"]
token_packs = db["token_packs"]

subController = Subscription_Controller()
userController = UserController()

endpoint_secret = os.getenv("STRIPE_ENDPOINT_SECRET")


class StripeController:
    def __init__(self):
        stripe.api_key = os.getenv("STRIPE_SECRET")

    def create_sub_payment_intent(self, request):
        try:
            data = request.get_json()

            price_id = data.get("priceId")

            user = userController.get_user_byId(g.userId)

            sub_data = subController.get_subscription(price_id)

            customer_id = user.get("customer_id")

            if user.get("customer_id") is None:
                customer = stripe.Customer.create(
                    email=user.get("email"),
                    name=user.get("username"),
                )

                updateData = {
                    "customer_id": customer.id,
                    "user_id": user["_id"],
                }
                customer_id = customer.id
                userController.update_user(updateData)

            subscription = stripe.Subscription.create(
                customer=customer_id,
                items=[{"price": price_id}],
                payment_behavior="default_incomplete",
                expand=["latest_invoice.payment_intent"],
            )

            subscription_id = subscription.id
            client_secret = subscription.latest_invoice.payment_intent.client_secret

            pi_data = {
                "id": subscription.latest_invoice.payment_intent.id,
                "validated": False,
                "tokens": sub_data.get("tokens"),
                "subscription_id": subscription_id,
                "user_id": g.userId,
            }

            payment_intents.insert_one(pi_data)

            return (
                jsonify(
                    {"clientSecret": client_secret, "subscription_id": subscription_id}
                ),
                200,
            )
        except Exception as e:
            return jsonify(error=str(e)), 400

    def create_payment_intent(self, data):
        try:
            product_id = data.get("product_id")

            if not product_id:
                return jsonify({"error": "Product ID is required"}), 400

            prices = stripe.Price.list(product=product_id, active=True, limit=1)

            if not prices.data:
                return jsonify({"error": "No active price found for product"}), 400

            price = prices.data[0]

            intent = stripe.PaymentIntent.create(
                amount=price.unit_amount,
                currency=price.currency,
                automatic_payment_methods={"enabled": True},
            )

            return jsonify({"client_secret": intent.client_secret})

        except Exception as e:
            return jsonify({"error": str(e)}), 500

    def validate_payment(self, payload):
        try:

            subscription_id = payload.get("subscriptionId")
            subscription = stripe.Subscription.retrieve(
                subscription_id, expand=["latest_invoice.payment_intent"]
            )
            latest_invoice = subscription.get("latest_invoice")
            payment_intent = (
                latest_invoice.get("payment_intent") if latest_invoice else None
            )

            if not payment_intent:
                return (
                    jsonify({"error": "No payment intent found for this subscription"}),
                    400,
                )

            if payment_intent["status"] == "succeeded":
                price_id = subscription["items"]["data"][0]["price"]["id"]
                sub_data = subController.get_subscription(price_id)

                pi = payment_intents.find_one({"id": payment_intent["id"]})
                tokens = sub_data.get("tokens")

                tokens = pi.get("tokens")

                if pi.get("validated") is False:
                    payment_intents.update_one(
                        {"id": payment_intent["id"]},
                        {"$set": {"validated": True}},
                    )
                    created_timestamp = payment_intent.get("created")
                    if created_timestamp is not None:
                        dt = datetime.fromtimestamp(created_timestamp)

                    updateData = {
                        "user_id": {"$oid": g.userId},
                        "monthly_tokens": tokens,
                        "sub_date": dt,
                    }
                    userController.update_user(updateData)

            return jsonify(
                {
                    "status": payment_intent["status"],
                    "amount": payment_intent["amount"],
                    "currency": payment_intent["currency"],
                    "id": payment_intent["id"],
                    "price_id": price_id,
                    "created": payment_intent["created"],
                    "subscription": sub_data,
                }
            )
        except Exception as e:
            return jsonify(error=str(e)), 400

    def handle_stripe_event(self, request):
        payload = request.data

        sig_header = request.headers.get("Stripe-Signature")

        try:
            event = stripe.Webhook.construct_event(payload, sig_header, endpoint_secret)
            if event["type"] == "invoice.paid":
                invoice = event["data"]["object"]

                if invoice.get("billing_reason") == "subscription_cycle":
                    print("Subscription cycle")

            return jsonify({"status": "success"}), 200
        except stripe.error.SignatureVerificationError:
            return jsonify({"error": "Invalid signature"}), 400
