from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, current_user
from app.models import User
from app import db
from werkzeug.security import generate_password_hash, check_password_hash

auth = Blueprint('auth', __name__)

@auth.route('/welcome')
def welcome():
    return render_template('welcome.html')

@auth.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('Username already exists.')
            return redirect(url_for('auth.register'))

        user = User(username=username)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        login_user(user)  # ✅ Use flask_login to log in user
        return redirect(url_for('main.index'))

    return render_template('register.html')

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):
            login_user(user)  # ✅ Use flask_login to log in user
            return redirect(url_for('main.index'))
        else:
            flash('Invalid credentials.')
            return redirect(url_for('auth.login'))

    return render_template('login.html')

@auth.route('/logout')
def logout():
    logout_user()  # ✅ Use flask_login to log out user
    return redirect(url_for('auth.welcome'))