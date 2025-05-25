from app import db
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin  # ✅ Import this

class Outlet(db.Model):
    __tablename__ = 'outlet'  # Explicitly set table name to match your schema
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    favicon_url = db.Column(db.String(256))
    bias = db.Column(db.Integer)
    establishment = db.Column(db.Integer)

class User(UserMixin, db.Model):  # ✅ Inherit from UserMixin
    __tablename__ = 'users'  # Matches your schema
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    points = db.Column(db.Integer, default=0)
    show_on_leaderboard = db.Column(db.Boolean, default=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class WrongGuess(db.Model):
    __tablename__ = 'wrong_guesses'

    outlet_id = db.Column(db.Integer, primary_key=True)
    guessed_name = db.Column(db.String, primary_key=True)
    guessed_bias = db.Column(db.Integer, primary_key=True)
    guessed_establishment = db.Column(db.Integer, primary_key=True)
    count = db.Column(db.Integer, default=1)


class UserOutletProgress(db.Model):
    __tablename__ = 'user_outlet_progress'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    outlet_id = db.Column(db.Integer, nullable=False)
    guessed_name_correct = db.Column(db.Boolean, default=False)
    guessed_bias_correct = db.Column(db.Boolean, default=False)
    guessed_establishment_correct = db.Column(db.Boolean, default=False)
    all_correct_on_first_try = db.Column(db.Boolean, default=False)

    __table_args__ = (
        db.UniqueConstraint('user_id', 'outlet_id', name='user_outlet_unique'),
    )

class Submission(db.Model):
    __tablename__ = 'submissions'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    url = db.Column(db.String, nullable=False)
    status = db.Column(db.String, default='pending')