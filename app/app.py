from flask import Flask, render_template, request, redirect, session
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import os

app = Flask(__name__)
app.secret_key = os.urandom(24)  # Secure session cookie


def get_db():
    return sqlite3.connect("database.db")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = generate_password_hash(request.form["password"])
        db = get_db()
        db.execute(
            "INSERT INTO users (username, password) VALUES (?, ?)", (username, password)
        )
        db.commit()
        return redirect("/login")
    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        db = get_db()
        user = db.execute(
            "SELECT * FROM users WHERE username = ?", (request.form["username"],)
        ).fetchone()
        if user and check_password_hash(user[2], request.form["password"]):
            session["user_id"] = user[0]
            return redirect("/notes")
    return render_template("login.html")


@app.route("/notes", methods=["GET", "POST"])
def notes():
    if "user_id" not in session:
        return redirect("/login")
    db = get_db()
    if request.method == "POST":
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
    with get_db() as db:
        db.execute(
            "CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, username TEXT, password TEXT)"
        )
        db.execute(
            "CREATE TABLE IF NOT EXISTS notes (id INTEGER PRIMARY KEY, user_id INTEGER, content TEXT)"
        )

    if os.path.exists("/.dockerenv"):
        host = "0.0.0.0"
    else:
        host = "127.0.0.1"

    app.run(host=host, port=5000, debug=True)
