
from app import db


class Outlet(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    favicon_url = db.Column(db.String(256))