from flask import Flask
from app.routes.escrow_routes import escrow_blueprint
from app.routes.user_info_route import user_info_blueprint


def create_app() -> Flask:
    """
    This function initializes a Flask app and adds the "telegram" blueprint to it.
    """
    app = Flask(__name__)
    app.register_blueprint(escrow_blueprint)
    app.register_blueprint(user_info_blueprint)

    return app
