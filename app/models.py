from app import db
from werkzeug.security import generate_password_hash, check_password_hash

class Outlet(db.Model):
    __tablename__ = 'outlet'  # Explicitly set table name to match your schema
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    favicon_url = db.Column(db.String(256))
    bias = db.Column(db.Integer)
    establishment = db.Column(db.Integer)

class User(db.Model):
    __tablename__ = 'users'  # Matches your schema
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    points = db.Column(db.Integer, default=0)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
