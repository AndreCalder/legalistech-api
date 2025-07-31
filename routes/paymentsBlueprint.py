from flask import Blueprint, request, g
from controllers.stripe import StripeController
from controllers.token import TokenController

payment_Router = Blueprint("paymentBlueprint", __name__)
stripeController = StripeController()
tokenController = TokenController()


@payment_Router.before_request
def validate_token():
    if request.headers.get("Stripe-Signature") is None and request.method != "OPTIONS":
        token_data = tokenController.check_token(request.headers["Authorization"])
        g.userId = token_data.get("user_id")


@payment_Router.route("/create-sub-payment-intent", methods=["POST"])
def create():
    return stripeController.create_sub_payment_intent(request)


@payment_Router.route("/create-payment-intent", methods=["POST"])
def create_pi():
    data = request.json
    return stripeController.create_payment_intent(data)


@payment_Router.route("/validate-payment", methods=["POST"])
def validate_payment():
    return stripeController.validate_payment(request.json)


# Conexión con Stripe
@payment_Router.route("/webhook", methods=["POST"])
def stripe_webhook():
    return stripeController.handle_stripe_event(request)

@payment_Router.route("/get-payment-methods", methods=["GET"])
def get_payment_methods():
    return stripeController.get_payment_methods()

@payment_Router.route("/refund-payment", methods=["POST"])
def refund_payment():
    data = request.json
    payment_intent_id = data.get("payment_intent_id")
    return stripeController.refund_payment(payment_intent_id)

@payment_Router.route("/list-user-subscriptions", methods=["GET"])
def list_user_subscriptions():
    return stripeController.list_user_subscriptions()

@payment_Router.route("/list-user-payments", methods=["GET"])
def list_user_payments():
    return stripeController.list_user_payments()

@payment_Router.route("/update-payment-method", methods=["POST"])
def update_payment_method():
    data = request.json
    payment_method_id = data.get("payment_method_id")
    return stripeController.update_payment_method(payment_method_id)

@payment_Router.route("/get-subscription-status", methods=["GET"])
def get_subscription_status():
    subscription_id = request.args.get("subscription_id")
    return stripeController.get_subscription_status(subscription_id)

@payment_Router.route("/detach-payment-method", methods=["POST"])
def detach_payment_method():
    data = request.json
    payment_method_id = data.get("payment_method_id")
    return stripeController.detach_payment_method(payment_method_id)

@payment_Router.route("/change-subscription-plan", methods=["POST"])
def change_subscription_plan():
    data = request.json
    subscription_id = data.get("subscription_id")
    new_price_id = data.get("new_price_id")
    return stripeController.change_subscription_plan(subscription_id, new_price_id)
