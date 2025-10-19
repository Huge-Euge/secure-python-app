import sqlite3
import os
import json
from flask import Flask, render_template, flash, request, redirect, session
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from werkzeug.security import generate_password_hash, check_password_hash
from seed_db import seed_db

from results import ManyResults, Result
from validators import validate_registration
from dal import DAL

app = Flask(__name__)
app.secret_key = os.urandom(24)  # Secure session cookie

limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://",
)


def get_db():
    return sqlite3.connect("database.db")


@app.route("/register", methods=["GET", "POST"])
@limiter.limit("10 per hour")
def register():
    """
    Defines the /register endpoint where users can make accounts
    """
    if request.method == "POST":
        db_ = get_db()
        username = request.form["username"]
        password = request.form["password"]
        password_2 = request.form["password_2"]
        validation_result = validate_registration(username, password, password_2)
        # TODO: bring in the check if there's one already in the DB
        if not isinstance(validation_result, Result.Success):
            # NOTE: Should add some error messages to this here
            # handle rendering more
            return render_template("register.html")

        # The request.form is sent with HTTPS, so the password should be encrypted in transit
        username = request.form["username"]
        hashed_password = generate_password_hash(request.form["password"])

        DAL.create_user(db_, username, hashed_password)

        return redirect("/login")
    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
@limiter.limit("5 per 5 minutes")
def login():
    """
    Defines the /login endpoint where users can log in and get session tokens
    Note that there should ideally be some forgotten password functionality,
    but I think that's out of scope for this assignment.
    """
    if request.method == "POST":
        flash("You have to log in first.")
        db_ = get_db()
        user = DAL.find_user_by_username(db_, request.form["username"])

        if not isinstance(user, Result.Success):
            flash("Error, incorrect username or password.", "error")
        elif isinstance(user, Result.Success) and not check_password_hash(
            user.value[2], request.form["password"]
        ):
            flash("Error, incorrect username or password.", "error")
        else:
            session["user_id"] = user.value[0]
            return redirect("/notes")
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
        flash("You have to log in first.")
        return redirect("/login")
    db_ = get_db()
    if request.method == "POST":
        # NOTE: need to validate this input
        # NOTE: This is not behind any auth, well it checks if user_id is in session,
        # but idk if an attacker could set that manually
        note = request.form["note"]
        db_.execute(
            "INSERT INTO notes (user_id, content) VALUES (?, ?)",
            (session["user_id"], note),
        )
        db_.commit()
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
    with get_db() as db:
        db.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL
            )
            """
        )
        db.execute(
            """
            CREATE TABLE IF NOT EXISTS notes (
                id INTEGER PRIMARY KEY,
                user_id INTEGER,
                content TEXT NOT NULL
            )
            """
        )

        seed_db(db)

    with open("config.json", "r", encoding="utf-8") as f:
        config = json.load(f)
    host = config["server"]["host"]
    port = config["server"]["port"]
    debug = config["debug_bool"]

    # NOTE: change debug to false in final version
    app.run(host=host, port=port, debug=debug, ssl_context=("cert.pem", "key.pem"))
