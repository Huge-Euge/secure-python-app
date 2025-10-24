"""
The root of the secure-notes-app. Manages the web application's lifecycle.
"""

from datetime import timedelta
import os
import json
import sqlite3
from flask import Flask, render_template, flash, request, redirect, session, url_for, g
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from werkzeug.security import generate_password_hash, check_password_hash
from returns.result import Success, Failure

from validators import validate_registration, validate_note
from dal import DAL
from seed_db import seed_db, init_db

DbConnection = sqlite3.Connection

app = Flask(__name__)
# TOEX fully explain this
app.secret_key = os.urandom(24)  # Secure session cookie
# TOEX fully explain this
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

# TOEX: explain this in the document
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["500 per day", "100 per hour"],
    # TOEX: what is this?
    storage_uri="memory://",
)

# TOEX: explain this in the document
DUMMY_HASH = generate_password_hash(str(os.urandom(24)))


def get_db() -> DbConnection:
    """
    Gets the database connection for the current request, if it exists.
    If not, it creates it.
    """
    if "db" not in g:
        g.db = sqlite3.connect("database.db")
    return g.db


@app.teardown_appcontext
def close_db(e=None):
    """
    Automatically closes the database connection at the end of any request.
    """
    db = g.pop("db", None)
    if db is not None:
        db.close()


@app.route("/register", methods=["GET", "POST"])
def register():
    """
    Defines the /register endpoint where users can make accounts
    """
    # If the user is currently logged in, redirect them from the page.
    # There should be no case where the user can re-register an active account.
    if "user_id" in session:
        return redirect(url_for("index"))
    if request.method == "POST":
        db_ = get_db()
        username = request.form["username"]
        # The request.form is sent over HTTPS, so the password is secure in transit
        password = request.form["password"]
        password_2 = request.form["password_2"]

        print(username)
        print(password)
        print(password_2)

        validation_result = validate_registration(username, password, password_2)
        if isinstance(validation_result, Failure):
            for fail in validation_result.failure():
                print(fail)
                flash(fail, "error")
            return redirect(url_for("register"))

        creation_result = DAL.create_user(db_, username, password)
        if isinstance(creation_result, Success):
            flash("Account successfully registered!", "notification")
            return redirect(url_for("login"))
        # If creation_result is a failure because there was already a user with that username,
        # let them know.
        # If the error was something to do with the db, don't tell end users anything specific
        if creation_result.failure() == "This username is already taken.":
            flash(creation_result.failure(), "error")
        elif creation_result.failure() == "A database error occurred.":
            flash(creation_result.failure(), "error")
        print("Failure: " + creation_result.failure())
        return redirect(url_for("register"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    """
    Defines the /login endpoint where users can log in and get session tokens
    Note that there should ideally be some forgotten password functionality,
    but I think that's out of scope for this assignment.
    """

    # Redirect to index if already logged in.
    if "user_id" in session:
        return redirect(url_for("index"))
    if request.method == "POST":

        db_ = get_db()
        res_user = DAL.find_user_by_username(db_, request.form["username"])

        # Use a dummy hash for non-existant users to protect against
        # user enumeration attacks, this makes the process take the same
        # amount of time
        # Does it? Now that I am unwrapping and accessing the tuple of res_user
        # I think the if/else here takes different amounts of time
        user_hash = (
            res_user.unwrap()[2] if isinstance(res_user, Success) else DUMMY_HASH
        )

        if not check_password_hash(user_hash, request.form["password"]):
            flash("Error, incorrect username or password.", "error")
        else:
            session["user_id"] = res_user.unwrap()[0]
            return redirect(url_for("index"))
    # Handle GET requests
    return render_template("login.html")


@app.route("/logout", methods=["POST"])
def logout():
    """
    Defines the /logout endpoint that scrubs the session cookie and redirects to /
    """
    session.clear()
    flash("You have successfully logged out.", "notification")
    return redirect(url_for("index"))


@app.route("/notes", methods=["GET"])
def notes():
    """
    Defines the /notes endpoint where users can GET a collection of all of
    their notes.
    """
    # If the user is not logged in, they can't view this page
    if "user_id" not in session:
        flash("You must be logged in to view notes.", "error")
        return redirect(url_for("login"))
    user_id = session["user_id"]

    db_ = get_db()

    res_user_notes = DAL.get_notes_for_user(db_, user_id)
    # This doesn't appear when the user simply has no notes yet, only on db errors
    if isinstance(res_user_notes, Failure):
        flash(res_user_notes.failure(), "error")
        return redirect(url_for("index"))

    return render_template("notes.html", notes=res_user_notes.unwrap())


@app.route("/notes/new", methods=["GET", "POST"])
def new_note():
    """
    Defines the /notes/new endpoint where users can GET the page to create a new note
    or POST the note they just created.
    """

    if "user_id" not in session:
        flash("You must be logged in to create a note.", "error")
        return redirect(url_for("login"))
    user_id = session["user_id"]

    if request.method == "POST":
        content = request.form["note_content"]

        res_val_note = validate_note(content)
        if isinstance(res_val_note, Failure):
            flash(res_val_note.failure(), "error")
            return redirect(url_for("new_note"))

        db_ = get_db()
        res_create_note = DAL.create_note_for_user(db_, user_id, content)
        if isinstance(res_create_note, Failure):
            flash(res_create_note.failure(), "error")
            return redirect(url_for("new_note"))
        flash("Note successfully edited.", "notification")

        return redirect(url_for("notes"))

    # Handle GETs
    return render_template("single-note.html")


@app.route("/notes/edit/<int:note_id>", methods=["GET", "POST"])
def edit_note(note_id: int):
    """
    Defines the endpoint where users can GET an existing note to read and edit it,
    or POST the note they've just edited.
    """

    if "user_id" not in session:
        flash("You must be logged in to edit a note.", "error")
        return redirect(url_for("login"))
    user_id = session["user_id"]

    db_ = get_db()

    if request.method == "POST":
        # Logic for updating or creating a note
        content = request.form["note_content"].strip()

        # Validate it here
        res_val_note = validate_note(content)
        if isinstance(res_val_note, Failure):
            flash(res_val_note.failure(), "error")
            redirect(url_for("edit_note", note_id=note_id))

        # DB access
        res_edit_note = DAL.edit_note(db_, note_id, content)
        if isinstance(res_edit_note, Failure):
            flash(res_edit_note.failure(), "error")
            redirect(url_for("edit_note", note_id=note_id))
        flash("Note successfully edited.", "notification")
        return redirect(url_for("notes"))

    # Handle GET
    res_get_note = DAL.get_note_by_id(db_, note_id, user_id)
    if isinstance(res_get_note, Failure):
        flash(res_get_note.failure(), "error")
        redirect(url_for("notes"))

    return render_template("single-note.html", note=res_get_note.unwrap())


@app.route("/notes/delete/<int:note_id>", methods=["POST"])
def delete_note(note_id: int):
    """
    Defines the endpoint for deleting the note with the given note_id on POST
    """
    if "user_id" not in session:
        flash("You must be logged in to delete a note.", "error")
        return redirect(url_for("login"))
    user_id = session["user_id"]

    db_ = get_db()

    res_delete_note = DAL.delete_note(db_, note_id, user_id)
    if isinstance(res_delete_note, Failure):
        flash(res_delete_note.failure(), "error")

    return redirect(url_for("notes"))


@app.route("/", methods=["GET"])
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

    with app.app_context():
        with get_db() as db:
            init_db(db)
            # Only seed db values if the app is running in debug mode
            if debug:
                seed_db(db)

    app.run(host=host, port=port, debug=debug, ssl_context=("cert.pem", "key.pem"))
