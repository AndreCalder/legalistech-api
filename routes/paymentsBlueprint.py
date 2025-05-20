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
