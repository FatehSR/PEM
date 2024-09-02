from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user, login_user, logout_user
from .models import User, Employee, Expense, Reminder  # Ensure you have a Reminder model
from . import db
from werkzeug.security import check_password_hash, generate_password_hash

views = Blueprint('views', __name__)

@views.route('/', methods=['GET', 'POST'])
def home():
    if current_user.is_authenticated:
        return redirect(url_for('views.welcome'))

    if request.method == 'POST':
        if 'login' in request.form:
            email = request.form.get('email')
            password = request.form.get('password')

            user = User.query.filter_by(email=email).first()
            if user and check_password_hash(user.password, password):
                login_user(user, remember=True)
                flash('Welcome back to our platform', category='success')
                return redirect(url_for('views.welcome'))
            else:
                flash('Invalid login credentials.', category='error')

        elif 'signup' in request.form:
            email = request.form.get('email')
            first_name = request.form.get('firstName')
            password1 = request.form.get('password1')
            password2 = request.form.get('password2')

            user = User.query.filter_by(email=email).first()
            if user:
                flash('Email already exists.', category='error')
            elif len(email) < 4:
                flash('Email must be greater than 3 characters.', category='error')
            elif len(first_name) < 2:
                flash('First name must be greater than 1 character.', category='error')
            elif password1 != password2:
                flash('Passwords don\'t match.', category='error')
            elif len(password1) < 7:
                flash('Password must be at least 7 characters.', category='error')
            else:
                new_user = User(
                    email=email,
                    first_name=first_name,
                    password=generate_password_hash(password1, method='pbkdf2:sha256'),
                    totp_key=None  # Set to None initially
                )
                db.session.add(new_user)
                db.session.commit()
                login_user(new_user, remember=True)
                flash('Welcome to our platform', category='success')
                return redirect(url_for('views.welcome'))

    return render_template("home.html", user=current_user)

@views.route('/welcome')
@login_required
def welcome():
    return render_template("welcome_back.html", user=current_user)

@views.route('/dashboard')
@login_required
def dashboard():
    return render_template("userDashboard.html", user=current_user)

@views.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    if request.method == 'POST':
        if 'update_password' in request.form:
            current_password = request.form.get('current_password')
            new_password = request.form.get('new_password')
            confirm_password = request.form.get('confirm_password')

            if not check_password_hash(current_user.password, current_password):
                flash('Current password is incorrect.', category='error')
            elif new_password != confirm_password:
                flash('New passwords do not match.', category='error')
            elif len(new_password) < 7:
                flash('New password must be at least 7 characters.', category='error')
            else:
                current_user.password = generate_password_hash(new_password, method='pbkdf2:sha256')
                db.session.commit()
                flash('Password updated successfully.', category='success')
                return redirect(url_for('views.settings'))

        elif 'update_profile' in request.form:
            name = request.form.get('name')
            email = request.form.get('email')
            phone = request.form.get('phone')

            if name:
                current_user.first_name = name
            if email:
                current_user.email = email
            if phone:
                current_user.phone_number = phone

            db.session.commit()
            flash('Profile updated successfully.', category='success')
            return redirect(url_for('views.settings'))

    return render_template("settings.html", user=current_user)

@views.route('/set-expense-reminder', methods=['GET', 'POST'])
@login_required
def set_expense_reminder():
    if request.method == 'POST':
        expense = request.form.get('expense')
        reminder_type = request.form.get('reminder_type')
        reminder_datetime = request.form.get('reminder_datetime')

        if expense and reminder_type and reminder_datetime:
            new_reminder = Reminder(
                expense=expense,
                reminder_type=reminder_type,
                reminder_datetime=reminder_datetime,
                user_id=current_user.id
            )
            db.session.add(new_reminder)
            db.session.commit()
            flash('Reminder set successfully.', category='success')
            return redirect(url_for('views.set_expense_reminder'))
        else:
            flash('Failed to set reminder. Please check your input.', category='error')

    # Fetch upcoming reminders for display
    reminders = Reminder.query.filter_by(user_id=current_user.id).all()
    return render_template("set_expense_reminder.html", user=current_user, reminders=reminders)

@views.route('/expense-report', methods=['GET', 'POST'])
@login_required
def expense_report():
    if request.method == 'POST':
        period = request.form.get('period')
        category = request.form.get('category')
        report_type = request.form.get('report_type')

        # Replace this with actual logic to fetch the report data
        report_entries = Expense.query.filter_by(
            user_id=current_user.id,
            category=category,
            # Add date filtering based on `period` here
        ).all()

        return render_template("expense_report.html", user=current_user, report_entries=report_entries)

    return render_template("expense_report.html", user=current_user)

@views.route('/categorize-expenses')
@login_required
def categorize_expenses():
    return render_template("categorize_expenses.html", user=current_user)

@views.route('/expense-management')
@login_required
def expense_management():
    return render_template("expense_management.html", user=current_user)

@views.route('/add-expense', methods=['POST'])
@login_required
def add_expense():
    expense_name = request.form.get('expense_name')
    amount = request.form.get('amount')
    date = request.form.get('date')
    category = request.form.get('category')

    if expense_name and amount and date and category:
        new_expense = Expense(
            name=expense_name,
            amount=amount,
            date=date,
            category=category,
            user_id=current_user.id
        )
        db.session.add(new_expense)
        db.session.commit()
        flash('Expense added successfully.', category='success')
    else:
        flash('Failed to add expense. Please check your input.', category='error')

    return redirect(url_for('views.expense_management'))

@views.route('/payroll-management', methods=['GET', 'POST'])
@login_required
def payroll_management():
    if request.method == 'POST':
        employee_id = request.form.get('employee_id')
        name = request.form.get('name')
        salary = request.form.get('salary')
        department = request.form.get('department')

        if employee_id:
            employee = Employee.query.get(employee_id)
            if employee:
                employee.name = name
                employee.salary = salary
                employee.department = department
                db.session.commit()
                flash('Employee updated successfully.', category='success')
        else:
            new_employee = Employee(
                id=employee_id,  # Ensure ID is provided or auto-generated
                name=name,
                position=department  # Assuming position is equivalent to department
            )
            db.session.add(new_employee)
            db.session.commit()
            flash('Employee added successfully.', category='success')

    employees = Employee.query.all()
    return render_template("payroll_management.html", user=current_user, employees=employees)

@views.route('/manage-employees')
@login_required
def manage_employees():
    employees = Employee.query.all()
    return render_template("manage_employees.html", user=current_user, employees=employees)

@views.route('/manage-attendance')
@login_required
def manage_attendance():
    # Assuming you have logic to fetch and display attendance data
    attendance_records = []  # Replace with actual query
    return render_template("manage_attendance.html", user=current_user, attendance_records=attendance_records)

@views.route('/manage-wagerates')
@login_required
def manage_wagerates():
    # Assuming you have logic to fetch and display wage rate data
    wage_rates = []  # Replace with actual query
    return render_template("manage_wagerates.html", user=current_user, wage_rates=wage_rates)

@views.route('/logout', methods=['POST'])
@login_required
def logout():
    logout_user()
    return redirect(url_for('views.home'))  # Redirect to home page after logout