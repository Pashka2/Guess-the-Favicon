import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'guess-the-favicon-secret-key'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'postgresql+psycopg2://media_user:yourpassword@localhost/media_game'
    SQLALCHEMY_TRACK_MODIFICATIONS = False