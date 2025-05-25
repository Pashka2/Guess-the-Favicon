from flask import Blueprint, render_template, redirect, url_for, make_response, flash, request, session
from sqlalchemy import text
from app import db 
from flask_login import login_required, current_user
from app.utils import get_guess_attempts, save_guess_attempts
from app.models import User

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
    from flask_login import current_user
    if current_user.is_authenticated:
        from app.models import Outlet
        outlets = Outlet.query.all()
        return render_template("index.html", outlets=outlets, current_user=current_user)
    else:
        return redirect(url_for('auth.welcome'))


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
@login_required
def guess(outlet_id):
    user_id = current_user.id

    user_id = current_user.id
    MAX_ATTEMPTS = 5
    guess_attempts = get_guess_attempts()
    remaining = guess_attempts.get(str(outlet_id), MAX_ATTEMPTS)

    if remaining <= 0:
        return "<h2>No attempts left. Submit an article to earn more!</h2>"

    correct_outlet = db.session.execute(
        text("""
            SELECT id, name, bias, establishment, favicon_url 
            FROM outlet WHERE id = :id
        """), {"id": outlet_id}
    ).fetchone()

    if not correct_outlet:
        return "Outlet not found", 404

    # Load progress if any
    progress = db.session.execute(
        text("""
            SELECT * FROM user_outlet_progress 
            WHERE user_id = :user_id AND outlet_id = :outlet_id
        """), {"user_id": user_id, "outlet_id": outlet_id}
    ).fetchone()

    if not progress:
        db.session.execute(text("""
            INSERT INTO user_outlet_progress (user_id, outlet_id)
            VALUES (:user_id, :outlet_id)
        """), {"user_id": user_id, "outlet_id": outlet_id})
        db.session.commit()
        progress = db.session.execute(
            text("""
                SELECT * FROM user_outlet_progress 
                WHERE user_id = :user_id AND outlet_id = :outlet_id
            """), {"user_id": user_id, "outlet_id": outlet_id}
        ).fetchone()

    locked = {
        'name': progress.guessed_name_correct,
        'bias': progress.guessed_bias_correct,
        'establishment': progress.guessed_establishment_correct
    }

    checkmarks = {
        'name': False,
        'bias': False,
        'establishment': False
    }

    message = None

    if request.method == 'POST':
        guessed_name = request.form.get('guessed_name')
        guessed_bias = request.form.get('guessed_bias')
        guessed_establishment = request.form.get('guessed_establishment')

        points_awarded = 0
        update_fields = []

        if not locked['name'] and guessed_name:
            if guessed_name.strip().lower() == correct_outlet.name.strip().lower():
                points_awarded += 3
                update_fields.append("guessed_name_correct = TRUE")
                locked['name'] = True
                checkmarks['name'] = True

        if not locked['bias'] and guessed_bias:
            if int(guessed_bias) == correct_outlet.bias:
                points_awarded += 2
                update_fields.append("guessed_bias_correct = TRUE")
                locked['bias'] = True
                checkmarks['bias'] = True

        if not locked['establishment'] and guessed_establishment:
            if int(guessed_establishment) == correct_outlet.establishment:
                points_awarded += 2
                update_fields.append("guessed_establishment_correct = TRUE")
                locked['establishment'] = True
                checkmarks['establishment'] = True

        if (not progress.guessed_name_correct and not progress.guessed_bias_correct and
            not progress.guessed_establishment_correct and
            checkmarks['name'] and checkmarks['bias'] and checkmarks['establishment']):
            update_fields.append("all_correct_on_first_try = TRUE")
            points_awarded += 3

        if update_fields:
            db.session.execute(
                text(f"""
                    UPDATE user_outlet_progress
                    SET {', '.join(update_fields)}
                    WHERE user_id = :user_id AND outlet_id = :outlet_id
                """), {"user_id": user_id, "outlet_id": outlet_id})
            db.session.execute(
                text("UPDATE users SET points = points + :points WHERE id = :user_id"),
                {"points": points_awarded, "user_id": user_id}
            )
            db.session.commit()
            message = f"✅ You earned {points_awarded} points!"
        else:
            from app.routes import log_wrong_guess
            log_wrong_guess(outlet_id, guessed_name or '', int(guessed_bias or 0), int(guessed_establishment or 0))
            remaining -= 1
            guess_attempts[str(outlet_id)] = remaining
            message = f"❌ Incorrect. {remaining} guesses left."

        resp = make_response(render_template(
            "guess.html",
            remaining_guesses=remaining,
            message=message,
            outlet_id=outlet_id,
            favicon_url=correct_outlet.favicon_url,
            outlet_name=correct_outlet.name,
            locked=locked,
            checkmarks=checkmarks
        ))
        save_guess_attempts(resp, guess_attempts)
        return resp

    return render_template("guess.html",
        remaining_guesses=remaining,
        outlet_id=outlet_id,
        favicon_url=correct_outlet.favicon_url,
        outlet_name=correct_outlet.name,
        locked=locked,
        checkmarks=checkmarks
    )

@main.route('/reset/<int:outlet_id>')
@login_required
def reset_guesses(outlet_id):
    

    
    user_id = current_user.id

    # Decrease user points by 1 for resetting
    db.session.execute(
        text("UPDATE users SET points = GREATEST(points - 1, 0) WHERE id = :user_id"),
        {"user_id": user_id}
    )

    # Reset guesses in cookie
    guess_attempts = get_guess_attempts()
    guess_attempts[str(outlet_id)] = 5

    # Reset correctness flags for this outlet
    db.session.execute(
        text("""
            UPDATE user_outlet_progress
            SET guessed_name_correct = FALSE,
                guessed_bias_correct = FALSE,
                guessed_establishment_correct = FALSE,
                all_correct_on_first_try = FALSE
            WHERE user_id = :user_id AND outlet_id = :outlet_id
        """),
        {"user_id": user_id, "outlet_id": outlet_id}
    )

    db.session.commit()

    resp = make_response(redirect(url_for('main.guess', outlet_id=outlet_id)))
    save_guess_attempts(resp, guess_attempts)
    return resp


@main.route("/favicons")
@login_required
def favicons():
    from app.models import Outlet  # Make sure this import exists if needed
    outlets = Outlet.query.all()
    return render_template("favicons.html", outlets=outlets)




@main.route('/submit_article', methods=['POST'])
@login_required
def submit_article():
    

    
    user_id = current_user.id
    url = request.form['url'].strip()

    # Check if user has already submitted 5 URLs
    submission_count = db.session.execute(
        text("SELECT COUNT(*) FROM submissions WHERE user_id = :user_id"),
        {"user_id": user_id}
    ).scalar()

    if submission_count >= 5:
        flash("You’ve reached the limit of 5 article submissions.")
        return redirect(request.referrer or url_for('main.favicons'))

    # Check if this URL has already been submitted
    exists = db.session.execute(
        text("SELECT id FROM submissions WHERE url = :url"), {"url": url}
    ).fetchone()

    if exists:
        flash("This URL has already been submitted.")
        return redirect(request.referrer or url_for('main.favicons'))

    # Insert the new submission
    db.session.execute(
        text("INSERT INTO submissions (user_id, url, status) VALUES (:user_id, :url, 'pending')"),
        {"user_id": user_id, "url": url}
    )
    db.session.commit()

    # Add 1 guess back to each outlet the user has interacted with
    guess_attempts = get_guess_attempts()
    for k in guess_attempts:
        guess_attempts[k] += 1

    flash("Thanks! You’ve earned more guesses.")
    resp = make_response(redirect(request.referrer or url_for('main.favicons')))
    save_guess_attempts(resp, guess_attempts)
    return resp

@main.route('/leaderboard')
def leaderboard():
    users = db.session.execute(
        text("SELECT username, points FROM users WHERE show_on_leaderboard = TRUE ORDER BY points DESC")
    ).fetchall()
    return render_template("leaderboard.html", users=users)

@main.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    

    user = current_user

    if request.method == 'POST':
        show = 'show_leaderboard' in request.form
        db.session.execute(
            text("UPDATE users SET show_on_leaderboard = :show WHERE id = :user_id"),
            {"show": show, "user_id": user.id}
        )
        db.session.commit()
        flash("Leaderboard visibility updated.")
        return redirect(url_for('main.index'))

    return render_template("settings.html", current_show=user.show_on_leaderboard)
    