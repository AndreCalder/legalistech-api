from flask import Flask
from flask_cors import CORS
import os

from controllers.util.email_config import configure_mail, mail
from routes.router import router

app = Flask(__name__)
cors = CORS(app, resources={r"/*": {"origins": "*"}})

# ✅ Initialize mail before using
configure_mail(app)

@app.route("/_ah/warmup")
def warmup():
    return "", 200

app.register_blueprint(router)

if __name__ == "__main__":
    is_dev = os.environ.get("FLASK_ENV") == "development"
    app.run(host="127.0.0.1", port=8080, debug=is_dev)
