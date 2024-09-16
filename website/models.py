from . import db
from flask_login import UserMixin
from sqlalchemy.sql import func
from flask_login import current_user
from datetime import datetime

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
    phone_number = db.Column(db.String(20), nullable=True)  # Add this line for phone number support
    totp_key = db.Column(db.String(100), nullable=True)
    reminders = db.relationship('Reminder', backref='user_reminder', lazy=True)
    expenses = db.relationship('Expense', backref='user', lazy=True)  # Relationship with Expense

    def __repr__(self):
        return f'<User {self.email}>'

class Employee(db.Model):
    id = db.Column(db.Integer, primary_key=True)  # Auto-incrementing primary key
    employee_id = db.Column(db.String(50), unique=True, nullable=False)  # Unique employee ID
    name = db.Column(db.String(150), nullable=False)
    position = db.Column(db.String(150), nullable=False)

    # Relationship to WageRate
    wage_rates = db.relationship('WageRate', backref='employee', lazy=True)

    def __repr__(self):
        return f'<Employee {self.name} ({self.employee_id})>'

class Expense(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    date = db.Column(db.Date, nullable=False)
    category = db.Column(db.String(50), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    vendor = db.Column(db.String(100), nullable=True)
    client = db.Column(db.String(100), nullable=True)
    notes = db.Column(db.Text, nullable=True)

    # Add the is_paid field
    is_paid = db.Column(db.Boolean, default=False)

    # Relationship with Reminder, providing a unique backref
    reminders = db.relationship('Reminder', backref='related_expense', lazy=True)

    def __repr__(self):
        return f'<Expense {self.name}>'

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def __repr__(self):
        return f'<Category {self.name}>'

class Attendance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)
    employee_id = db.Column(db.String(50), db.ForeignKey('employee.employee_id'), nullable=False)  # Referencing employee_id
    status = db.Column(db.String(50), nullable=False)

    def __repr__(self):
        return f'<Attendance {self.employee_id} - {self.date}>'
    
class WageRate(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employee.id'), nullable=False)  # Use Employee.id as foreign key
    wage_type = db.Column(db.String(50), nullable=False)
    wage_amount = db.Column(db.Float, nullable=False)
    working_hours = db.Column(db.Float, nullable=True)  # Optional field for hourly workers
    days_worked = db.Column(db.Integer, nullable=False)
    total_wage_amount = db.Column(db.Float, nullable=False)

    def __repr__(self):
        return f'<WageRate {self.employee_id} - {self.wage_type} - {self.total_wage_amount}>'
    
class Reminder(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    expense_id = db.Column(db.Integer, db.ForeignKey('expense.id'), nullable=False)
    reminder_datetime = db.Column(db.DateTime, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    is_paid = db.Column(db.Boolean, default=False)  # New field to track if the expense has been marked as paid

    # Relationships with unique backref names
    expense = db.relationship('Expense', backref='related_reminders', lazy=True)
    user = db.relationship('User', backref='reminder_set', lazy=True)

    def __repr__(self):
        return f'<Reminder {self.reminder_type} for Expense {self.expense_id}>'
    
class Report(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    category = db.Column(db.String(100))
    start_date = db.Column(db.Date)
    end_date = db.Column(db.Date)
    report_type = db.Column(db.String(50))
    total_amount = db.Column(db.Float)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Payroll(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    employee_name = db.Column(db.String(100), nullable=False)
    salary = db.Column(db.Float, nullable=False)
    department = db.Column(db.String(100), nullable=False)
    date = db.Column(db.Date, nullable=False, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def __repr__(self):
        return f'<Payroll {self.employee_name} - {self.salary}>'