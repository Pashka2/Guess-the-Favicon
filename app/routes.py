from flask import Blueprint, render_template

main = Blueprint('main', __name__)

@main.route('/')
def index():
    return "<h1>Welcome to Guess the Favicon!</h1><p>The game is under construction.</p>"