from flask import Blueprint
from routes.assistantBlueprint import assistant_Router
from routes.authBlueprint import auth_Router
from routes.userBlueprint import user_Router
from routes.consultBlueprint import consult_Router
from routes.paymentsBlueprint import payment_Router
from routes.subBlueprint import sub_Router
from routes.pinsBlueprint import pins_bp

router = Blueprint("router", __name__)

router.register_blueprint(auth_Router, url_prefix="/auth")  # Authentication routes
router.register_blueprint(user_Router, url_prefix="/users")  # User routes
router.register_blueprint(assistant_Router, url_prefix="/assistant")  # Chat routes
router.register_blueprint(consult_Router, url_prefix="/search")  # Smart search routes
router.register_blueprint(payment_Router, url_prefix="/payment")  # Payment routes
router.register_blueprint(sub_Router, url_prefix="/sub")  # Subscription routes
router.register_blueprint(pins_bp, url_prefix="/pins") # PIN Management Routes