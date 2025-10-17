from flask import Flask, render_template, request, redirect, session
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import os
import json

app = Flask(__name__)
app.secret_key = os.urandom(24)  # Secure session cookie


def get_db():
    return sqlite3.connect("database.db")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        # NOTE: there is no input validation here
        # NOTE: if there are multiple users with the same username, this breaks
        username = request.form["username"]
        # NOTE: IDK if this password is being sent unencrypted, also this is almost certainly wrong in some way
        password = generate_password_hash(request.form["password"])
        db = get_db()
        db.execute(
            "INSERT INTO users (username, password) VALUES (?, ?)", (username, password)
        )
        db.commit()
        return redirect("/login")
    return render_template("register.html")


# NOTE: there is no brute-force prevention here
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        db = get_db()
        # NOTE: there is no input validation here
        user = db.execute(
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
    db = get_db()
    if request.method == "POST":
        # NOTE: need to validate this input
        # NOTE: This is not behind any auth, well it checks if user_id is in session, but idk if an attacker could set that manually
        note = request.form["note"]
        db.execute(
            "INSERT INTO notes (user_id, content) VALUES (?, ?)",
            (session["user_id"], note),
        )
        db.commit()
    user_notes = db.execute(
        "SELECT content FROM notes WHERE user_id = ?", (session["user_id"],)
    ).fetchall()
    return render_template("notes.html", notes=user_notes)


@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")


if __name__ == "__main__":
    # NOTE: there are no backups on the db
    with get_db() as db:
        db.execute(
            "CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, username TEXT, password TEXT)"
        )
        db.execute(
            "CREATE TABLE IF NOT EXISTS notes (id INTEGER PRIMARY KEY, user_id INTEGER, content TEXT)"
        )

    with open("config.json", "r", encoding="utf-8") as f:
        config = json.load(f)
    host = config["server"]["host"]
    port = config["server"]["port"]

    # NOTE: change debug to false in final version, maybe switch to a config file
    app.run(host=host, port=port, debug=True, ssl_context=("cert.pem", "key.pem"))
