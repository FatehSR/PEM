from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from os import path
import pyotp
import qrcode

db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'  # Ensure this is the correct route for login

DB_NAME = "database.db"

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'Womp Womp'
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DB_NAME}'
    db.init_app(app)

    # Register Blueprints
    from .views import views
    from .auth import auth  # Ensure you have an auth blueprint

    app.register_blueprint(views, url_prefix='/')
    app.register_blueprint(auth, url_prefix='/auth')  # Adjust URL prefix if needed

    # Import models
    from .models import User, Note, Employee

    # Create database tables
    with app.app_context():
        db.create_all()

    # Initialize LoginManager
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    return app