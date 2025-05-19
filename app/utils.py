# app/utils.py
import json
from flask import request

def get_guess_attempts():
    cookie = request.cookies.get('guess_attempts')
    if cookie:
        return json.loads(cookie)
    return {}

def save_guess_attempts(response, attempts_dict):
    response.set_cookie('guess_attempts', json.dumps(attempts_dict), max_age=60*60*24*30)  # 30 days