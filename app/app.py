import sqlite3
import os
import json
from flask import Flask, render_template, request, redirect, session
from werkzeug.security import generate_password_hash, check_password_hash

from validators import validate_registration, Error

app = Flask(__name__)
app.secret_key = os.urandom(24)  # Secure session cookie


def get_db():
    return sqlite3.connect("database.db")


@app.route("/register", methods=["GET", "POST"])
def register():
    """
    Defines the /register endpoint where users can make accounts
    """
    if request.method == "POST":
        db_ = get_db()
        if validate_registration(request.form, db_) != True:
            # NOTE: Should add some error messages to this here
            return render_template("register.html")

        # The request.form is sent with HTTPS, so the password should be encrypted in transit
        username = request.form["username"]
        password = generate_password_hash(request.form["password"])
        db_.execute(
            "INSERT INTO users (username, password) VALUES (?, ?)",
            (username, password),
        )
        db_.commit()

        return redirect("/login")
    return render_template("register.html")


# NOTE: there is no brute-force prevention here
@app.route("/login", methods=["GET", "POST"])
def login():
    """
    Defines the /login endpoint where users can log in and get session tokens
    """
    if request.method == "POST":
        db_ = get_db()
        # NOTE: there is no input validation here
        user = db_.execute(
            "SELECT * FROM users WHERE username = ?", (request.form["username"],)
        ).fetchone()
        if user and check_password_hash(user[2], request.form["password"]):
            session["user_id"] = user[0]
            return redirect("/notes")
    return render_template("login.html")


@app.route("/notes", methods=["GET", "POST"])
def notes():
    # NOTE: all this checks for is an id, which is just an integer, this can be guessed easily
    # NOTE: There is no session timeout here, there should be
    if "user_id" not in session:
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
def index():
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

    with open("config.json", "r", encoding="utf-8") as f:
        config = json.load(f)
    host = config["server"]["host"]
    port = config["server"]["port"]

    # NOTE: change debug to false in final version, maybe switch to a config file
    app.run(host=host, port=port, debug=True, ssl_context=("cert.pem", "key.pem"))
