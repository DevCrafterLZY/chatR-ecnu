import logging
import os
from datetime import datetime
from logging.handlers import TimedRotatingFileHandler

from flask import Flask, Blueprint

from chatR.config.config import config


def create_app():
    app = Flask(__name__)
    app.secret_key = config.secret_key

    log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'log')
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    log_formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
    log_file_handler = TimedRotatingFileHandler(
        filename=os.path.join(log_dir, datetime.now().strftime('%Y-%m-%d') + '.log'), when='midnight', backupCount=7)
    log_file_handler.setFormatter(log_formatter)
    log_file_handler.setLevel(logging.DEBUG)
    app.logger.addHandler(log_file_handler)
    app.logger.setLevel(logging.DEBUG)

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

    @app.errorhandler(Exception)
    def handle_error(error):
        app.logger.error('ERROR: %s', error)

    return app
