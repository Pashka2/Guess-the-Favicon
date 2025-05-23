from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from config import Config

db = SQLAlchemy()
migrate = Migrate()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    migrate.init_app(app, db)

    from app.routes import main as main_blueprint
    from app.auth import auth as auth_blueprint  # ✅ Moved inside the function

    app.register_blueprint(main_blueprint)
    app.register_blueprint(auth_blueprint)

    return app
