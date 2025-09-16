from flask import Flask
from .extensions import db
from flask_migrate import Migrate
from config import Config
from .routes import bp

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Initialize extensions
    db.init_app(app)
    Migrate(app, db)

    # Register routes
    app.register_blueprint(bp)

    return app
