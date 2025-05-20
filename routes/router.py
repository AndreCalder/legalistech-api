from flask import Blueprint
from routes.assistantBlueprint import assistant_Router
from routes.authBlueprint import auth_Router
from routes.userBlueprint import user_Router
from routes.consultBlueprint import consult_Router
from routes.paymentsBlueprint import payment_Router
from routes.subBlueprint import sub_Router
from routes.emailBlueprint import email_Router

router = Blueprint("router", __name__)

router.register_blueprint(auth_Router, url_prefix="/auth")
router.register_blueprint(user_Router, url_prefix="/users")
router.register_blueprint(assistant_Router, url_prefix="/assistant")
router.register_blueprint(consult_Router, url_prefix="/search")
router.register_blueprint(payment_Router, url_prefix="/payment")
router.register_blueprint(sub_Router, url_prefix="/sub")
router.register_blueprint(email_Router, url_prefix="/email")
