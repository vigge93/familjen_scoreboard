import logging
import os
from logging.config import dictConfig

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from werkzeug.exceptions import HTTPException

from scoreboard.model.model import BaseModel

db = SQLAlchemy(engine_options={"pool_pre_ping": True}, model_class=BaseModel)


def create_app() -> Flask:
    app = Flask(__name__, instance_relative_config=True)

    app.config.from_mapping(
        SECRET_KEY=os.getenv("SECRET_KEY"),
        SQLALCHEMY_DATABASE_URI=os.getenv("SQLALCHEMY_DATABASE_URI"),
        SCOREBOARD_EMAIL_SENDER=os.getenv("SCOREBOARD_EMAIL_SENDER"),
        SCOREBOARD_SMTP_HOST=os.getenv("SCOREBOARD_SMTP_HOST"),
        SCOREBOARD_SMTP_PORT=os.getenv("SCOREBOARD_SMTP_PORT"),
        SCOREBOARD_SMTP_USERNAME=os.getenv("SCOREBOARD_SMTP_USERNAME"),
        SCOREBOARD_SMTP_PASSWORD=os.getenv("SCOREBOARD_SMTP_PASSWORD"),
        SCOREBOARD_ADMIN_USER_EMAIL=os.getenv("SCOREBOARD_ADMIN_USER_EMAIL"),
        SCOREBOARD_ADMIN_USER_NAME=os.getenv("SCOREBOARD_ADMIN_USER_NAME"),
        SCOREBOARD_ADMIN_USER_PASSWORD=os.getenv("SCOREBOARD_ADMIN_USER_PASSWORD"),
        SCOREBOARD_DEVELOPMENT=os.getenv("SCOREBOARD_DEVELOPMENT", False),
    )

    app.config.from_pyfile("config.py", silent=True)

    os.makedirs(app.instance_path, exist_ok=True)

    db.init_app(app)

    from . import init_data

    init_data.init_db(app, db)

    from . import auth

    app.register_blueprint(auth.bp)

    from . import main

    app.register_blueprint(main.bp)

    from . import admin

    app.register_blueprint(admin.bp)

    app.register_error_handler(HTTPException, error_page)

    @app.route("/healthz")
    def healthz() -> dict[str, int]:
        return {"status": 1}

    if (
        not app.config["TESTING"] and not app.config["SCOREBOARD_DEVELOPMENT"]
    ):  # pragma: no cover
        dictConfig(
            {
                "version": 1,
                "formatters": {
                    "default": {
                        "format": "[%(asctime)s] %(levelname)s in %(module)s: %(message)s",
                    },
                    "error": {
                        "format": "%(asctime)s-%(levelname)s-%(name)s-%(process)d::%(module)s|%(lineno)s:: %(message)s"
                    },
                },
                "handlers": {
                    "wsgi": {
                        "class": "logging.StreamHandler",
                        "stream": "ext://flask.logging.wsgi_errors_stream",
                        "formatter": "default",
                    },
                    "critical_mail_handler": {
                        "level": "ERROR",
                        "formatter": "error",
                        "class": "logging.handlers.SMTPHandler",
                        "mailhost": app.config["SCOREBOARD_SMTP_HOST"],
                        "fromaddr": app.config["SCOREBOARD_EMAIL_SENDER"],
                        "toaddrs": app.config["SCOREBOARD_ADMIN_USER_EMAIL"],
                        "subject": "Receipt helper: Application Error",
                        "credentials": (
                            app.config["SCOREBOARD_SMTP_USERNAME"],
                            app.config["SCOREBOARD_SMTP_PASSWORD"],
                        ),
                    },
                },
                "root": {
                    "level": int(os.getenv("LOGGING_LEVEL", logging.INFO)),
                    "handlers": ["wsgi", "critical_mail_handler"],
                },
            }
        )

        app.logger.info(f"Web app started!\t{__name__}")
    return app


def error_page(e):
    return {"status": e.code, "message": e.description}, e.code
