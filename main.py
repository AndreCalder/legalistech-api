from flask import Flask
from routes.router import router
from flask_cors import CORS
import os

app = Flask(__name__)
cors = CORS(app, resources={r"/*": {"origins": "*"}})


@app.route("/_ah/warmup")
def warmup():
    return "", 200


# Calling the router blueprint
app.register_blueprint(router)

if __name__ == "__main__":
    is_dev = os.environ.get("FLASK_ENV") == "development"
    app.run(host="127.0.0.1", port=8080, debug=is_dev)
