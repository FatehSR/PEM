from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from flask_login import login_required, current_user, login_user, logout_user
from .models import User, Employee, Payroll, Expense, Reminder, Attendance, WageRate, Category, Report
from . import db
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime
from sqlalchemy import func, desc
from sqlalchemy.exc import IntegrityError

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
    # Fetch the most recent expenses (limit to 5 for brevity)
    recent_expenses = Expense.query.filter_by(user_id=current_user.id).order_by(Expense.date.desc()).limit(5).all()

    # Fetch employees with wage rates and attendance
    employees = Employee.query.all()

    recent_payrolls = []
    for employee in employees:
        # Fetch the most recent wage rate for each employee
        wage_rate = WageRate.query.filter_by(employee_id=employee.employee_id).order_by(WageRate.id.desc()).first()
        # Fetch the most recent attendance record for each employee
        attendance = Attendance.query.filter_by(employee_id=employee.employee_id).order_by(Attendance.date.desc()).first()

        # Debugging: Print employee details to check if they are fetched properly
        print(f"Employee: {employee.name}, Wage Rate: {wage_rate}, Attendance: {attendance}")

        # Loosen the condition for testing (remove attendance.status == 'Present' for now)
        if wage_rate and attendance:  # Removed attendance.status == 'Present' condition
            recent_payrolls.append({
                'employee_name': employee.name,
                'position': employee.position,
                'salary': wage_rate.wage_amount,
                'attendance_date': attendance.date
            })

    # Fetch urgent reminders that are due and not marked as paid
    urgent_reminders = Reminder.query.filter(
        Reminder.reminder_datetime <= datetime.now(),
        Reminder.is_paid == False,
        Reminder.user_id == current_user.id
    ).all()

    # Greeting message based on time of day
    current_hour = datetime.now().hour
    if current_hour < 12:
        greeting_message = "Good morning!"
    elif 12 <= current_hour < 18:
        greeting_message = "Good afternoon!"
    else:
        greeting_message = "Good evening!"

    return render_template('userdashboard.html', 
                           recent_expenses=recent_expenses, 
                           recent_payrolls=recent_payrolls, 
                           greeting_message=greeting_message,
                           urgent_reminders=urgent_reminders)

@views.route('/mark-expense-paid/<int:reminder_id>', methods=['POST'])
@login_required
def mark_expense_paid(reminder_id):
    try:
        # Fetch the reminder
        reminder = Reminder.query.get_or_404(reminder_id)

        # Ensure the reminder belongs to the current user
        if reminder.user_id != current_user.id:
            return jsonify({"error": "Unauthorized"}), 403

        # Mark the reminder as paid
        reminder.is_paid = True

        # Optionally mark the expense as paid, if you have added an is_paid field to Expense
        expense = reminder.expense
        expense.is_paid = True  # If you've added this field to Expense

        # Commit changes to the database
        db.session.commit()

        return jsonify({"success": "Expense marked as paid successfully!"}), 200
    except Exception as e:
        # Log the exception for debugging
        print(f"Error: {e}")
        return jsonify({"error": "Error marking expense as paid."}), 500
    
@views.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    if request.method == 'POST':
        # Handle password update
        if 'update_password' in request.form:
            current_password = request.form.get('current_password')
            new_password = request.form.get('new_password')
            confirm_password = request.form.get('confirm_password')

            # Validate current password
            if not check_password_hash(current_user.password, current_password):
                flash('Current password is incorrect.', category='error')
            # Validate new passwords match
            elif new_password != confirm_password:
                flash('New passwords do not match.', category='error')
            # Validate password length
            elif len(new_password) < 7:
                flash('New password must be at least 7 characters.', category='error')
            else:
                # Update password
                current_user.password = generate_password_hash(new_password, method='pbkdf2:sha256')
                db.session.commit()
                flash('Password updated successfully.', category='success')
                return redirect(url_for('views.settings'))

        # Handle profile update
        elif 'update_profile' in request.form:
            name = request.form.get('name')
            email = request.form.get('email')
            phone = request.form.get('phone')

            # Check for duplicate email if changed
            if email and email != current_user.email:
                email_exists = User.query.filter_by(email=email).first()
                if email_exists:
                    flash('Email is already in use by another user.', category='error')
                    return redirect(url_for('views.settings'))

            # Update profile fields if provided
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
        expense_category = request.form.get('expense')
        reminder_datetime_str = request.form.get('reminder_datetime')

        # Convert the reminder_datetime_str to a datetime object
        try:
            reminder_datetime = datetime.strptime(reminder_datetime_str, '%Y-%m-%dT%H:%M')
        except ValueError:
            flash('Invalid date/time format. Please try again.', category='error')
            return redirect(url_for('views.set_expense_reminder'))

        # Find the first matching expense for the given category and current user
        expense = Expense.query.filter_by(category=expense_category, user_id=current_user.id).first()

        # Ensure the expense and reminder datetime are present
        if expense and reminder_datetime:
            new_reminder = Reminder(
                expense=expense,
                reminder_datetime=reminder_datetime,
                user=current_user
            )
            db.session.add(new_reminder)
            db.session.commit()
            flash('Reminder set successfully.', category='success')
            return redirect(url_for('views.set_expense_reminder'))
        else:
            flash('Failed to set reminder. Please check your input.', category='error')

    # Group expenses by category and calculate the total for each
    expense_totals = {
        category: total_amount for category, total_amount in db.session.query(
            Expense.category,
            func.sum(Expense.amount).label('total_amount')
        ).filter_by(user_id=current_user.id).group_by(Expense.category).all()
    }

    # Fetch existing reminders
    reminders = Reminder.query.filter_by(user_id=current_user.id).all()

    return render_template(
        "set_expense_reminder.html", 
        user=current_user, 
        expense_totals=expense_totals, 
        reminders=reminders
    )

@views.route('/get_urgent_reminders', methods=['GET'])
@login_required
def get_urgent_reminders():
    urgent_reminders = Reminder.query.filter(
        Reminder.reminder_datetime <= datetime.now(),
        Reminder.is_paid == False,
        Reminder.user_id == current_user.id
    ).all()

    # Prepare data to send as JSON
    reminder_list = [{
        'id': reminder.id,
        'expense_name': reminder.expense.name,
        'amount': reminder.expense.amount,
        'reminder_datetime': reminder.reminder_datetime.strftime('%Y-%m-%d %H:%M:%S')
    } for reminder in urgent_reminders]

    return jsonify(reminder_list)

@views.route('/clear-expense-reminder-log', methods=['POST'])
@login_required
def clear_expense_reminder_log():
    action = request.form.get('action')
    if action == 'clear_log':
        Reminder.query.delete()
        db.session.commit()
        flash('Expense reminder log cleared successfully!', category='success')
    elif action == 'delete_selected':
        reminder_ids = request.form.getlist('reminder_ids')
        if reminder_ids:
            Reminder.query.filter(Reminder.id.in_(reminder_ids)).delete(synchronize_session=False)
            db.session.commit()
            flash('Selected reminder records deleted successfully!', category='success')
        else:
            flash('No records selected for deletion.', category='error')

    return redirect(url_for('views.set_expense_reminder'))

@views.route('/expense-report', methods=['GET', 'POST'])
@login_required
def expense_report():
    if request.method == 'POST':
        category = request.form.get('category')
        start_date = request.form.get('start_date')
        end_date = request.form.get('end_date')
        report_type = request.form.get('report_type')

        # Convert start and end dates from string to datetime
        try:
            start_date = datetime.strptime(start_date, '%Y-%m-%d')
            end_date = datetime.strptime(end_date, '%Y-%m-%d')
        except ValueError:
            flash('Invalid date format. Please use YYYY-MM-DD.', category='error')
            return redirect(url_for('views.expense_report'))

        # Filter expenses based on category, date range, and current user
        report_entries = db.session.query(
            Expense.category,
            func.sum(Expense.amount).label('total_amount')
        ).filter(
            Expense.user_id == current_user.id,
            Expense.category == category,
            Expense.date >= start_date,
            Expense.date <= end_date
        ).group_by(Expense.category).all()

        # Calculate the total amount from report_entries
        total_amount = report_entries[0].total_amount if report_entries else 0

        # Save the report to the database
        new_report = Report(
            user_id=current_user.id,
            category=category,
            start_date=start_date,
            end_date=end_date,
            report_type=report_type,
            total_amount=total_amount  # Save total amount
        )
        db.session.add(new_report)
        db.session.commit()

        # Render the report with summarized expenses
        return render_template(
            "expense_report.html",
            user=current_user,
            report_entries=report_entries,
            start_date=start_date,
            end_date=end_date,
            selected_category=category,
            report_type=report_type
        )

    # Fetch distinct categories from the expenses
    categories = [expense.category for expense in db.session.query(Expense.category).filter_by(user_id=current_user.id).distinct()]

    # Fetch saved reports from the database
    reports = Report.query.filter_by(user_id=current_user.id).all()

    return render_template('expense_report.html', categories=categories, reports=reports)

@views.route('/clear-expense-report-log', methods=['POST'])
@login_required
def clear_expense_report_log():
    action = request.form.get('action')

    if action == 'clear_log':
        # Clear all saved reports for the current user
        Report.query.filter_by(user_id=current_user.id).delete(synchronize_session=False)
        db.session.commit()
        flash('Expense report log cleared successfully!', category='success')

    elif action == 'delete_selected':
        report_ids = request.form.getlist('report_ids')
        if report_ids:
            # Delete the selected report entries
            Report.query.filter(Report.id.in_(report_ids), Report.user_id == current_user.id).delete(synchronize_session=False)
            db.session.commit()
            flash('Selected report records deleted successfully!', category='success')
        else:
            flash('No records selected for deletion.', category='error')

    return redirect(url_for('views.expense_report'))

@views.route('/expense-management')
@login_required
def expense_management():
    # Fetch categories for the current user
    categories = Category.query.filter_by(user_id=current_user.id).all()

    # Fetch expenses for the current user
    expenses = Expense.query.filter_by(user_id=current_user.id).all()

    # Render the expense management page with the user's categories and expenses
    return render_template("expense_management.html", 
                           user=current_user, 
                           categories=[cat.name for cat in categories], 
                           expenses=expenses)

@views.route('/add-expense', methods=['POST'])
@login_required
def add_expense():
    expense_name = request.form.get('expense_name')
    amount = request.form.get('amount')
    date_str = request.form.get('date')  # Get the date as a string
    category = request.form.get('category')

    # Convert the date string to a Python date object
    try:
        date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        flash('Invalid date format. Please select a valid date.', category='error')
        return redirect(url_for('views.expense_management'))

    if expense_name and amount and date_obj and category:
        new_expense = Expense(
            name=expense_name,
            amount=float(amount),  # Ensure the amount is stored as a float
            date=date_obj,          # Use the converted date object
            category=category,
            user_id=current_user.id
        )
        db.session.add(new_expense)
        db.session.commit()
        flash('Expense added successfully.', category='success')
    else:
        flash('Failed to add expense. Please check your input.', category='error')

    return redirect(url_for('views.expense_management'))

@views.route('/clear-expense-log', methods=['POST'])
@login_required
def clear_expense_log():
    action = request.form.get('action')
    if action == 'clear_log':
        Expense.query.delete()
        db.session.commit()
        flash('Expense log cleared successfully!', category='success')
    elif action == 'delete_selected':
        expense_ids = request.form.getlist('expense_ids')
        if expense_ids:
            Expense.query.filter(Expense.id.in_(expense_ids)).delete(synchronize_session=False)
            db.session.commit()
            flash('Selected expense records deleted successfully!', category='success')
        else:
            flash('No records selected for deletion.', category='error')

    return redirect(url_for('views.expense_management'))

@views.route('/add-category', methods=['POST'])
@login_required
def add_category():
    new_category_name = request.form.get('new_category')

    # Ensure the category name is not empty or whitespace
    if new_category_name and new_category_name.strip():
        # Strip extra whitespace and make the name consistent
        new_category_name = new_category_name.strip()

        # Check if the category already exists for this user
        existing_category = Category.query.filter_by(name=new_category_name, user_id=current_user.id).first()
        if existing_category:
            flash('This category already exists.', category='error')
        else:
            try:
                # Add the new category
                new_category = Category(name=new_category_name, user_id=current_user.id)
                db.session.add(new_category)
                db.session.commit()
                flash('Category added successfully!', category='success')
            except IntegrityError:
                # Rollback in case of a database error (e.g., uniqueness violation)
                db.session.rollback()
                flash('There was an error adding the category.', category='error')
    else:
        flash('Please enter a valid category name.', category='error')

    # Fetch updated list of categories after adding the new one
    categories = Category.query.filter_by(user_id=current_user.id).all()
    expenses = Expense.query.filter_by(user_id=current_user.id).all()

    return render_template("expense_management.html", user=current_user, categories=[cat.name for cat in categories], expenses=expenses)

@views.route('/open-report/<category>/<start_date>/<end_date>', methods=['GET', 'POST'])
@login_required
def open_report(category, start_date, end_date):
    try:
        start_date = datetime.strptime(start_date, '%Y-%m-%d')
        end_date = datetime.strptime(end_date, '%Y-%m-%d')
    except ValueError:
        flash('Invalid date format. Please use YYYY-MM-DD.', category='error')
        return redirect(url_for('views.expense_report'))

    # Fetch all categories from saved expenses
    categories = db.session.query(Expense.category).filter_by(user_id=current_user.id).distinct().all()
    categories = [c[0] for c in categories]  # Convert from list of tuples

    # Fetch expenses within the selected category and date range
    expenses = Expense.query.filter(
        Expense.user_id == current_user.id,
        Expense.category == category,
        Expense.date >= start_date,
        Expense.date <= end_date
    ).all()

    # Calculate total amount for the expenses
    total_amount = sum(expense.amount for expense in expenses)

    return render_template(
        "open_report.html",
        category=category,
        start_date=start_date,
        end_date=end_date,
        expenses=expenses,
        total_amount=total_amount,
        categories=categories  # Passing all categories to the template
    )

@views.route('/update-expenses', methods=['POST'])
@login_required
def update_expenses():
    # Extracting form data for start_date, end_date, and category
    start_date = request.form.get('start_date')
    end_date = request.form.get('end_date')
    category = request.form.get('category')

    # Handle missing date input and correct format errors
    try:
        if not start_date or not end_date:
            raise ValueError("Start date and end date are required.")
        start_date = datetime.strptime(start_date, '%Y-%m-%d')
        end_date = datetime.strptime(end_date, '%Y-%m-%d')
    except ValueError as e:
        flash(str(e), category='error')
        return redirect(url_for('views.open_report', start_date=start_date, end_date=end_date, category=category))

    # Iterate over the form data to update the expense details
    for expense_id in request.form:
        if expense_id.startswith('vendor_') or expense_id.startswith('client_') or expense_id.startswith('notes_'):
            # Extract the expense ID
            field, exp_id = expense_id.split('_')
            # Retrieve the expense from the database
            expense = Expense.query.get(exp_id)
            if expense and expense.user_id == current_user.id:
                # Update the corresponding fields based on the form input
                if field == 'vendor':
                    expense.vendor = request.form.get(expense_id)
                elif field == 'client':
                    expense.client = request.form.get(expense_id)
                elif field == 'notes':
                    expense.notes = request.form.get(expense_id)

    # Commit the changes to the database
    db.session.commit()
    flash('Expenses updated successfully!', category='success')

    # Redirect back to the report page with the correct start_date, end_date, and category
    return redirect(url_for('views.open_report', 
                            category=category, 
                            start_date=start_date.strftime('%Y-%m-%d'), 
                            end_date=end_date.strftime('%Y-%m-%d')))

@views.route('/payroll-management', methods=['GET', 'POST'])
@login_required
def payroll_management():
    if request.method == 'POST':
        employee_id = request.form.get('employee_id')
        name = request.form.get('name')
        position = request.form.get('position')

        # Validate input
        if not employee_id or not name or not position:
            flash('All fields are required!', category='error')
        elif Employee.query.filter_by(employee_id=employee_id).first():
            flash('Employee ID already exists!', category='error')
        else:
            # Create a new employee record
            new_employee = Employee(employee_id=employee_id, name=name, position=position)
            db.session.add(new_employee)
            db.session.commit()
            flash('Employee added successfully!', category='success')
            return redirect(url_for('views.payroll_management'))

    employees = Employee.query.all()  # Retrieve all employees for display
    return render_template('payroll_management.html', employees=employees, user=current_user)

@views.route('/delete_employee/<int:id>', methods=['POST'])
@login_required
def delete_employee(id):
    employee = Employee.query.get_or_404(id)
    db.session.delete(employee)
    db.session.commit()
    return jsonify({'message': 'Employee deleted successfully!'})

@views.route('/edit_employee/<int:id>', methods=['POST'])
@login_required
def edit_employee(id):
    employee = Employee.query.get_or_404(id)
    data = request.get_json()
    employee.name = data['name']
    employee.position = data['position']
    db.session.commit()
    return jsonify({'message': 'Employee details updated successfully!'})

@views.route('/manage-attendance', methods=['GET', 'POST'])
@login_required
def manage_attendance():
    if request.method == 'POST':
        date_str = request.form.get('date')
        employee_id = request.form.get('employee_id')
        status = request.form.get('status')

        # Validate input
        if not date_str or not employee_id or not status:
            flash('All fields are required!', category='error')
        else:
            # Convert the date string to a date object
            date = datetime.strptime(date_str, '%Y-%m-%d').date()
            
            employee = Employee.query.filter_by(employee_id=employee_id).first()
            if employee:
                # Create a new attendance record
                new_attendance = Attendance(date=date, employee_id=employee_id, status=status)
                db.session.add(new_attendance)
                db.session.commit()

                # Automatically update the wage rates log
                update_wage_rates(employee_id)

                flash('Attendance updated successfully!', category='success')
            else:
                flash('Employee ID is incorrect or does not exist.', category='error')

    # Retrieve attendance records for display
    attendance_records = Attendance.query.all()
    return render_template('manage_attendance.html', attendance_records=attendance_records, user=current_user)

@views.route('/clear-attendance-log', methods=['POST'])
@login_required
def clear_attendance_log():
    action = request.form.get('action')
    if action == 'clear_log':
        # Clear entire log
        Attendance.query.delete()
        db.session.commit()
        flash('Attendance log cleared successfully!', category='success')
    elif action == 'delete_selected':
        # Delete selected rows
        record_ids = request.form.getlist('record_ids')
        if record_ids:
            Attendance.query.filter(Attendance.id.in_(record_ids)).delete(synchronize_session=False)
            db.session.commit()
            flash('Selected attendance records deleted successfully!', category='success')
        else:
            flash('No records selected for deletion.', category='error')

    return redirect(url_for('views.manage_attendance'))

def update_wage_rates(employee_id):
    # Fetch the wage rate for the employee
    wage_rate = WageRate.query.filter_by(employee_id=employee_id).first()
    
    if wage_rate:
        # Fetch all the attendance records where the status is 'present'
        attendance_records = Attendance.query.filter_by(employee_id=employee_id, status='present').all()
        days_worked = len(attendance_records)

        # Calculate the total wage amount
        if wage_rate.wage_type == 'hourly':
            # Assume the working_hours were set during the initial wage rate setup
            total_wage_amount = wage_rate.wage_amount * wage_rate.working_hours * days_worked
        else:
            total_wage_amount = wage_rate.wage_amount * days_worked
        
        # Update the wage rate record with the new total wage amount and days worked
        wage_rate.days_worked = days_worked
        wage_rate.total_wage_amount = total_wage_amount
        db.session.commit()
    else:
        flash(f'No wage rate found for Employee ID: {employee_id}', category='error')

@views.route('/manage-wagerates', methods=['GET', 'POST'])
@login_required
def manage_wagerates():
    if request.method == 'POST':
        employee_id = request.form.get('employee_id')
        wage_type = request.form.get('wage_type')
        wage_amount = request.form.get('wage_amount')
        working_hours = request.form.get('working_hours')

        # Validate input
        if not employee_id or not wage_type or not wage_amount:
            flash('All fields need to be filled', category='error')
            return redirect(url_for('views.manage_wagerates'))

        employee = Employee.query.filter_by(employee_id=employee_id).first()
        if not employee:
            flash('Employee ID is incorrect or does not exist', category='error')
            return redirect(url_for('views.manage_wagerates'))

        # Calculate days worked based on attendance records
        attendance_records = Attendance.query.filter_by(employee_id=employee_id, status='present').all()
        days_worked = len(attendance_records)
        
        # Calculate total wage based on wage type
        if wage_type == 'hourly':
            if not working_hours:
                flash('Working hours must be provided for hourly wage type', category='error')
                return redirect(url_for('views.manage_wagerates'))
            total_wage_amount = float(wage_amount) * float(working_hours) * days_worked
        else:
            total_wage_amount = float(wage_amount) * days_worked

        # Save or update the wage rate information
        wage_rate = WageRate.query.filter_by(employee_id=employee_id).first()
        if wage_rate:
            wage_rate.wage_type = wage_type
            wage_rate.wage_amount = float(wage_amount)
            wage_rate.days_worked = days_worked
            wage_rate.total_wage_amount = total_wage_amount
            if wage_type == 'hourly':
                wage_rate.working_hours = float(working_hours)
            else:
                wage_rate.working_hours = None
        else:
            new_wage_rate = WageRate(
                employee_id=employee_id,
                wage_type=wage_type,
                wage_amount=float(wage_amount),
                days_worked=days_worked,
                total_wage_amount=total_wage_amount,
                working_hours=float(working_hours) if wage_type == 'hourly' else None
            )
            db.session.add(new_wage_rate)

        db.session.commit()
        flash('Wage rate updated successfully!', category='success')

    # Retrieve wage rates for display
    wages = WageRate.query.all()
    return render_template('manage_wagerates.html', wages=wages, user=current_user)

@views.route('/clear-wagerates-log', methods=['POST'])
@login_required
def clear_wagerates_log():
    action = request.form.get('action')
    if action == 'clear_log':
        # Clear entire log
        WageRate.query.delete()
        db.session.commit()
        flash('Wage rates log cleared successfully!', category='success')
    elif action == 'delete_selected':
        # Delete selected rows
        wage_ids = request.form.getlist('wage_ids')
        if wage_ids:
            WageRate.query.filter(WageRate.id.in_(wage_ids)).delete(synchronize_session=False)
            db.session.commit()
            flash('Selected wage rate records deleted successfully!', category='success')
        else:
            flash('No records selected for deletion.', category='error')

    return redirect(url_for('views.manage_wagerates'))

@views.route('/logout', methods=['POST'])
@login_required
def logout():
    logout_user()
    return redirect(url_for('views.home'))