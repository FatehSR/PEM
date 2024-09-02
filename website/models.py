from . import db
from flask_login import UserMixin
from sqlalchemy.sql import func

class Note(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    data = db.Column(db.String(10000))
    date = db.Column(db.DateTime(timezone=True), default=func.now())
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    first_name = db.Column(db.String(150), nullable=False)
    totp_key = db.Column(db.String(100), nullable=True)  # Added this field
    notes = db.relationship('Note', backref='user', lazy=True)
    reminders = db.relationship('Reminder', backref='user_reminder', lazy=True)  # Changed backref name

    def __repr__(self):
        return f'<User {self.email}>'

class Employee(db.Model):
    id = db.Column(db.String(50), primary_key=True)  # Employee ID should be unique and text type
    name = db.Column(db.String(150), nullable=False)
    position = db.Column(db.String(150), nullable=False)

    def __repr__(self):
        return f'<Employee {self.name}>'

class Expense(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    date = db.Column(db.Date, nullable=False)
    category = db.Column(db.String(50), nullable=False)
    reminders = db.relationship('Reminder', backref='expense_reminder', lazy=True)  # Changed backref name

    def __repr__(self):
        return f'<Expense {self.name}>'

class Reminder(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    expense_id = db.Column(db.Integer, db.ForeignKey('expense.id'), nullable=False)
    reminder_type = db.Column(db.String(50), nullable=False)
    reminder_datetime = db.Column(db.DateTime, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    expense = db.relationship('Expense', backref='reminders_set', lazy=True)  # Changed backref name
    user = db.relationship('User', backref='reminders_set_user', lazy=True)  # Changed backref name

    def __repr__(self):
        return f'<Reminder {self.reminder_type} for Expense {self.expense_id}>'