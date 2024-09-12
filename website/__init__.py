from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from os import path
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime

db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'  # Ensure this is the correct route for login

DB_NAME = "database.db"

def check_reminders():
    """Function to check if any reminders are due and unpaid."""
    from .models import Reminder  # Import here to avoid circular import issues
    now = datetime.now()
    due_reminders = Reminder.query.filter(Reminder.reminder_datetime <= now, Reminder.is_paid == False).all()
    for reminder in due_reminders:
        print(f"Reminder {reminder.id} is due for expense {reminder.expense_id}.")

def start_scheduler():
    """Start the APScheduler to check for reminders every minute."""
    scheduler = BackgroundScheduler()
    scheduler.add_job(check_reminders, 'interval', minutes=1)  # Runs every minute
    scheduler.start()

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'Womp Womp'
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DB_NAME}'
    db.init_app(app)

    # Import blueprints
    from .views import views
    from .auth import auth

    app.register_blueprint(views, url_prefix='/')
    app.register_blueprint(auth, url_prefix='/auth')

    # Import models after app context is set
    with app.app_context():
        from .models import User, Note, Employee, Reminder  # Import models here to avoid circular imports
        db.create_all()

    # Initialize LoginManager
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Start the scheduler
    start_scheduler()

    return app