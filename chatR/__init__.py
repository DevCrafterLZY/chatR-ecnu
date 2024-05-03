from flask import Flask, Blueprint

from chatR.config.config import config


def create_app():
    app = Flask(__name__)
    app.secret_key = config.secret_key

    from chatR.views.login import login_bp
    from chatR.views.register import register_bp
    from chatR.views.home.home_private import home_private_bp
    from chatR.views.home.home_public import home_public_bp
    from chatR.views.chat.chat_private import chat_private_bp
    from chatR.views.chat.chat_public import chat_public_bp
    app.register_blueprint(login_bp)
    app.register_blueprint(register_bp)
    app.register_blueprint(home_private_bp)
    app.register_blueprint(home_public_bp)
    app.register_blueprint(chat_private_bp)
    app.register_blueprint(chat_public_bp)

    return app
