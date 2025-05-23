from flask import Blueprint, render_template, redirect, url_for, make_response, flash, request, session
from sqlalchemy import text
from app import db 
from app.utils import get_guess_attempts, save_guess_attempts

#import json




MAX_ATTEMPTS = 5

#def get_guess_attempts():
 #   cookie = request.cookies.get('guess_attempts')
 #   if cookie:
 #       return json.loads(cookie)
 #   return {}

#def save_guess_attempts(response, attempts_dict):
#    response.set_cookie('guess_attempts', json.dumps(attempts_dict), max_age=60*60*24*30)  # 30 days

main = Blueprint('main', __name__)

@main.route('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for('auth.welcome'))  # Send to welcome screen if not logged in

    from app.models import Outlet
    outlets = Outlet.query.all()
    return render_template("index.html", outlets=outlets)


def log_wrong_guess(outlet_id, guessed_name, guessed_bias, guessed_establishment):
    stmt = text("""
        INSERT INTO wrong_guesses (outlet_id, guessed_name, guessed_bias, guessed_establishment, count)
        VALUES (:outlet_id, :guessed_name, :guessed_bias, :guessed_establishment, 1)
        ON CONFLICT (outlet_id, guessed_name, guessed_bias, guessed_establishment)
        DO UPDATE SET count = wrong_guesses.count + 1
        RETURNING count
    """)
    result = db.session.execute(stmt, {
        'outlet_id': outlet_id,
        'guessed_name': guessed_name,
        'guessed_bias': guessed_bias,
        'guessed_establishment': guessed_establishment
    })
    db.session.commit()
    return result.fetchone().count

@main.route('/guess/<int:outlet_id>', methods=['GET', 'POST'])
def guess(outlet_id):
    MAX_ATTEMPTS = 5
    guess_attempts = get_guess_attempts()
    remaining = guess_attempts.get(str(outlet_id), MAX_ATTEMPTS)

    if remaining <= 0:
        return "<h2>No attempts left. Submit an article to earn more!</h2>"

    message = None

    if request.method == 'POST':
        guessed_name = request.form['guessed_name']
        try:
            guessed_bias = int(request.form['guessed_bias'])
            guessed_establishment = int(request.form['guessed_establishment'])
        except ValueError:
            message = "Invalid input. Please enter numbers between 1 and 5."
            return render_template("guess.html", remaining_guesses=remaining, message=message, outlet_id=outlet_id)

        correct_outlet = db.session.execute(
            text("SELECT name, bias, establishment, favicon_url FROM outlets WHERE id = :id"),
            {"id": outlet_id}
        ).fetchone()

        if not correct_outlet:
            return "Outlet not found", 404

        if (
            guessed_name.lower() == correct_outlet.name.lower()
            and guessed_bias == correct_outlet.bias
            and guessed_establishment == correct_outlet.establishment
        ):
            message = "✅ Correct!"
        else:
            log_wrong_guess(outlet_id, guessed_name, guessed_bias, guessed_establishment)
            remaining -= 1
            guess_attempts[str(outlet_id)] = remaining
            message = f"❌ Wrong guess. Remaining attempts: {remaining}"

        resp = make_response(render_template(
            "guess.html",
            remaining_guesses=remaining,
            message=message,
            outlet_id=outlet_id,
            favicon_url=correct_outlet.favicon_url,
            outlet_name=correct_outlet.name
        ))
        save_guess_attempts(resp, guess_attempts)
        return resp

    # GET request - load favicon
    correct_outlet = db.session.execute(
        text("SELECT name, favicon_url FROM outlet WHERE id = :id"),
        {"id": outlet_id}
    ).fetchone()

    if not correct_outlet:
        return "Outlet not found", 404

    return render_template("guess.html",
        remaining_guesses=remaining,
        outlet_id=outlet_id,
        favicon_url=correct_outlet.favicon_url,
        outlet_name=correct_outlet.name
    )

@main.route("/favicons")
def favicons():
    from app.models import Outlet  # Make sure this import exists if needed
    outlets = Outlet.query.all()
    return render_template("favicons.html", outlets=outlets)


@main.route('/reset/<int:outlet_id>')
def reset_guesses(outlet_id):
    db.session.execute(
        text("DELETE FROM wrong_guesses WHERE outlet_id = :id"),
        {"id": outlet_id}
    )
    db.session.commit()
    return redirect(url_for('main.guess', outlet_id=outlet_id))

@main.route('/submit_article', methods=['POST'])
def submit_article():
    user_ip = request.remote_addr
    url = request.form['url']

    exists = db.session.execute(
        text("SELECT id FROM submissions WHERE url = :url"), {"url": url}
    ).fetchone()

    if exists:
        flash("URL already submitted.")
    else:
        db.session.execute(
            text("INSERT INTO submissions (user_id, url, status) VALUES (NULL, :url, 'pending')"),
            {"url": url}
        )
        db.session.commit()

        guess_attempts = get_guess_attempts()
        for k in guess_attempts:
            guess_attempts[k] += 1

        flash("Thanks! You've earned more attempts.")
        resp = make_response(redirect(request.referrer or url_for('main.favicons')))
        save_guess_attempts(resp, guess_attempts)
        return resp

    return redirect(request.referrer or url_for('main.favicons'))

    