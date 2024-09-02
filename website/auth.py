from flask import Blueprint, render_template, request, flash, redirect, url_for
from .models import User
from werkzeug.security import check_password_hash, generate_password_hash
from . import db
from flask_login import login_user, login_required, logout_user, current_user
import pyotp

auth = Blueprint('auth', __name__)

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        user = User.query.filter_by(email=email).first()
        if user:
            if check_password_hash(user.password, password):
                login_user(user, remember=True)
                flash('Logged in successfully!', category='success')
                return redirect(url_for('views.dashboard'))
            else:
                flash('Incorrect password, try again.', category='error')
        else:
            flash('Email does not exist.', category='error')

    return render_template("login.html", user=current_user)

@auth.route('/logout', methods=['POST'])
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))

@auth.route('/signup', methods=['GET', 'POST'])
def sign_up():
    if request.method == 'POST':
        first_name = request.form['firstName']
        email = request.form['email']
        password1 = request.form['password1']
        password2 = request.form['password2']
        
        # Ensure passwords match
        if password1 != password2:
            flash("Passwords do not match", "danger")
            return redirect(url_for('auth.sign_up'))

        # Check if email already exists
        if User.query.filter_by(email=email).first():
            flash("Email already exists", "danger")
            return redirect(url_for('auth.sign_up'))

        # Create new user
        new_user = User(
            email=email,
            password=generate_password_hash(password1, method='pbkdf2:sha256'),
            first_name=first_name,
            totp_key=None  # Set to None or a default value if not provided
        )
        
        db.session.add(new_user)
        try:
            db.session.commit()
            flash("Account created successfully", "success")
            return redirect(url_for('auth.login'))
        except Exception as e:
            db.session.rollback()
            flash(f"An error occurred: {e}", "danger")
            return redirect(url_for('auth.sign_up'))
    
    return render_template('sign_up.html')

@auth.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email')
        user = User.query.filter_by(email=email).first()
        if user:
            # Here you would typically send an email with a password reset link
            flash('A password reset link has been sent to your email address.', category='info')
            # Redirect to login after showing the flash message
            return redirect(url_for('auth.login'))
        else:
            flash('Email does not exist.', category='error')

    return render_template('forgot_password.html')