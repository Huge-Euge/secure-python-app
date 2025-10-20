from datetime import timedelta
import os
import json
from flask import Flask, render_template, flash, request, redirect, session
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from werkzeug.security import generate_password_hash, check_password_hash
from returns.result import Result, Success, Failure

from validators import validate_registration
from dal import DAL
from seed_db import seed_db, init_db

app = Flask(__name__)
app.secret_key = os.urandom(24)  # Secure session cookie
app.config.update(
    # Limits Cookies to HTTPS traffic only
    SESSION_COOKIE_SECURE=True,
    # Prevent Session cookies from being accessed in JS
    SESSION_COOKIE_HTTPONLY=True,
    # Prevent sending cookies with all external requests
    SESSION_COOKIE_SAMESITE="Strict",
    # Make sessions expire after 1 hour
    PERMANENT_SESSION_LIFETIME=timedelta(hours=1),
)
# TODO: Confirm that I have solved cross-site-scripting
# TODO: Confirm that I have solved session fixation
# TODO: Implement Session expiry

limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://",
)

dummy_password = str(os.urandom(24))


@app.route("/register", methods=["GET", "POST"])
@limiter.limit("10 per hour")
def register():
    """
    Defines the /register endpoint where users can make accounts
    """
    # If the user is currently logged in, redirect them from the page.
    # There should be no case where the user can re-register with an account.
    if request.cookies.get("auth_token"):
        return redirect("/")
    if request.method == "POST":
        db_ = DAL.get_db()
        username = request.form["username"]
        # The request.form is sent with HTTPS, so the password should be secure in transit
        password = request.form["password"]
        password_2 = request.form["password_2"]
        validation_result = validate_registration(username, password, password_2)
        if isinstance(validation_result, Failure):
            for fail in validation_result.failure():
                flash(fail, "error")
            return render_template("register.html")

        creation_result = DAL.create_user(db_, username, password)
        if isinstance(creation_result, Success):
            flash("Account successfully registered!", "notification")
            return redirect("/login")
        # If creation_result is a failure because there was already a user with that username,
        # let them know.
        # If the error was something to do with the db, don't tell end users anything specific
        if creation_result.failure() == "This username is already taken.":
            flash(creation_result.failure(), "error")
        elif creation_result.failure() == "A database error occurred.":
            flash(creation_result.failure(), "error")

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
@limiter.limit("5 per 5 minutes")
def login():
    """
    Defines the /login endpoint where users can log in and get session tokens
    Note that there should ideally be some forgotten password functionality,
    but I think that's out of scope for this assignment.
    """
    # Redirect to index if already logged in.
    if request.cookies.get("auth_token"):
        return redirect("/")
    if request.method == "POST":

        db_ = DAL.get_db()
        res_user = DAL.find_user_by_username(db_, request.form["username"])

        # Create a dummy hash for non-existant users to protect against
        # user enumeration attacks
        dummy_hash = generate_password_hash(dummy_password)
        user_hash = (
            res_user.unwrap()[2] if isinstance(res_user, Success) else dummy_hash
        )

        if isinstance(res_user, Failure):
            flash("Error, incorrect username or password.", "error")
        elif isinstance(res_user, Success) and not check_password_hash(
            user_hash, request.form["password"]
        ):
            flash("Error, incorrect username or password.", "error")
        else:
            session["user_id"] = res_user.unwrap()[0]
            return redirect("/")
    return render_template("login.html")


@app.route("/notes", methods=["GET", "POST"])
def notes():
    """
    Defines the /notes endpoint where users can view a collection of all of
    their notes or find a note with a specific id
    """
    # NOTE: all this checks for is an id, which is just an integer, this can be guessed easily
    # NOTE: There is no session timeout here, there should be
    if "user_id" not in session:
        flash("You must log in before viewing notes.")
        return redirect("/login")
    db_ = DAL.get_db()
    if request.method == "POST":
        # NOTE: need to validate this input
        # NOTE: This is not behind any auth, well it checks if user_id is in session,
        # but idk if an attacker could set that manually
        note = request.form["note"]

        # TODO: move this into DAL methods
        db_.execute(
            "INSERT INTO notes (user_id, content) VALUES (?, ?)",
            (session["user_id"], note),
        )
        db_.commit()
    # TODO: check for URL params - note id

    # if request.method == "GET" and request.args:

    user_notes = db_.execute(
        "SELECT content FROM notes WHERE user_id = ?", (session["user_id"],)
    ).fetchall()
    return render_template("notes.html", notes=user_notes)


@app.route("/", methods=["GET"])
@limiter.limit("5 per 2 minutes")
def index():
    """
    Defines the index page for the website
    """
    return render_template("index.html")


if __name__ == "__main__":
    with open("config.json", "r", encoding="utf-8") as f:
        config = json.load(f)
    host = config["server"]["host"]
    port = config["server"]["port"]
    debug = config["debug_bool"]

    with DAL.get_db() as db:

        init_db(db)
        # Only seed db values if the app is running in debug mode
        if debug:
            seed_db(db)

    app.run(host=host, port=port, debug=debug, ssl_context=("cert.pem", "key.pem"))
