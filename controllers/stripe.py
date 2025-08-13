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
                        "subscription_id": subscription_id,
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

    def cancel_subscription(self, subscription_id):
        try:
            stripe.Subscription.update(subscription_id, {"cancel_at_period_end": True})
            return jsonify({"status": "success"}), 200
        except Exception as e:
            return jsonify(error=str(e)), 400

    def handle_stripe_event(self, request):
        payload = request.data

        sig_header = request.headers.get("Stripe-Signature")

        try:
            event = stripe.Webhook.construct_event(payload, sig_header, endpoint_secret)
            if event["type"] == "invoice.paid":
                invoice = event["data"]["object"]
            elif event["type"] == "subscription.canceled":
                subscription = event["data"]["object"]
                self.cancel_subscription(subscription["id"])
            else:
                return jsonify({"status": "success"}), 200

            return jsonify({"status": "success"}), 200
        except Exception:
            return jsonify({"error": "Invalid signature"}), 400

    def get_payment_methods(self):
        try:
            user = userController.get_user_byId(g.userId)
            customer_id = user.get("customer_id")
            if not customer_id:
                return jsonify({"error": "No Stripe customer ID found for user"}), 404

            payment_methods = stripe.PaymentMethod.list(
                customer=customer_id,
                type="card"
            )
            return jsonify({"payment_methods": payment_methods.data}), 200
        except Exception as e:
            return jsonify({"error": str(e)}), 400

    def refund_payment(self, payment_intent_id):
        try:
            refund = stripe.Refund.create(payment_intent=payment_intent_id)
            # Optionally update your DB here
            return jsonify({"refund": refund}), 200
        except Exception as e:
            return jsonify({"error": str(e)}), 400

    def list_user_subscriptions(self):
        try:
            user = userController.get_user_byId(g.userId)
            customer_id = user.get("customer_id")
            if not customer_id:
                return jsonify({"error": "No Stripe customer ID found for user"}), 404
            subscriptions = stripe.Subscription.list(customer=customer_id)
            return jsonify({"subscriptions": subscriptions.data}), 200
        except Exception as e:
            return jsonify({"error": str(e)}), 400

    def list_user_payments(self):
        try:
            user = userController.get_user_byId(g.userId)
            customer_id = user.get("customer_id")
            if not customer_id:
                return jsonify({"error": "No Stripe customer ID found for user"}), 404
            payment_intents_list = stripe.PaymentIntent.list(customer=customer_id)
            return jsonify({"payment_intents": payment_intents_list.data}), 200
        except Exception as e:
            return jsonify({"error": str(e)}), 400

    def update_payment_method(self, payment_method_id):
        try:
            user = userController.get_user_byId(g.userId)
            customer_id = user.get("customer_id")
            if not customer_id:
                return jsonify({"error": "No Stripe customer ID found for user"}), 404
            # Attach the payment method to the customer
            payment_method = stripe.PaymentMethod.attach(
                payment_method_id,
                customer=customer_id,
            )
            # Set as default
            stripe.Customer.modify(
                customer_id,
                invoice_settings={"default_payment_method": payment_method_id},
            )
            return jsonify({"payment_method": payment_method}), 200
        except Exception as e:
            return jsonify({"error": str(e)}), 400

    def get_subscription_status(self, subscription_id):
        try:
            subscription = stripe.Subscription.retrieve(subscription_id)
            return jsonify({"status": subscription.status, "subscription": subscription}), 200
        except Exception as e:
            return jsonify({"error": str(e)}), 400

    def detach_payment_method(self, payment_method_id):
        try:
            payment_method = stripe.PaymentMethod.detach(payment_method_id)
            return jsonify({"payment_method": payment_method}), 200
        except Exception as e:
            return jsonify({"error": str(e)}), 400

    def change_subscription_plan(self, subscription_id, new_price_id):
        try:
            subscription = stripe.Subscription.retrieve(subscription_id)
            current_item_id = subscription['items']['data'][0]['id']
            updated_subscription = stripe.Subscription.modify(
                subscription_id,
                cancel_at_period_end=False,
                proration_behavior='create_prorations',
                items=[{
                    'id': current_item_id,
                    'price': new_price_id,
                }],
            )
            return jsonify({"subscription": updated_subscription}), 200
        except Exception as e:
            return jsonify({"error": str(e)}), 400
