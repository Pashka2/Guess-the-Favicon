# app/utils.py
import json
import zlib
import base64
from flask import request

def get_guess_attempts():
    cookie = request.cookies.get('guess_attempts')
    if cookie:
        try:
            decoded = base64.b64decode(cookie.encode())
            decompressed = zlib.decompress(decoded).decode()
            return json.loads(decompressed)
        except Exception:
            # In case of corrupt cookie, return fresh dict
            return {}
    return {}

def save_guess_attempts(response, attempts_dict):
    try:
        raw_json = json.dumps(attempts_dict).encode()
        compressed = zlib.compress(raw_json)
        encoded = base64.b64encode(compressed).decode()
        response.set_cookie('guess_attempts', encoded, max_age=60*60*24*30)  # 30 days
    except Exception:
        # Fail silently if compression fails
        pass