"""
This module just exists to store the seed functions for the database for development.
"""

import json
import sqlite3
from werkzeug.security import generate_password_hash
from dal import Sqlite3DAL
from results import Result
from validators import validate_registration

DbConnection = sqlite3.Connection


def seed_db(db_):
    """Seeds the database with 5 default users using the DAL, and the config file."""

    config = open("config.json", "r", encoding="utf-8")

    users = json.load(config)["seed_users"]

    for user in users:
        validate_result = validate_registration(
            user.username, user.password, user.password
        )
        if isinstance(validate_result, Result.Error):
            raise ValueError("Failed to create user: " + validate_result.message)

    for user in users:
        username = user["username"]
        existing_user_result = Sqlite3DAL.find_user_by_username(db_, username)

        if isinstance(existing_user_result, Result.Success):
            print(f"User '{username}' already exists. Skipping.")
            continue

        # If user doesn't exist, create them using the DAL, and give them a note
        hashed_password = generate_password_hash(user["password"])
        create_result = Sqlite3DAL.create_user(db_, username, hashed_password)

        if not isinstance(create_result, Result.Success):
            raise ValueError("Failed to create user: " + create_result.message)

        user_id = Sqlite3DAL.find_user_by_username(db_, username)

        if not isinstance(user_id, Result.Success):
            raise ValueError("Failed to create user: " + user_id.message)
        content = f"This is a note for {username}."

        create_result = Sqlite3DAL.create_note_for_user(db_, user_id.value, content)

        if not isinstance(create_result, Result.Success):
            raise ValueError("Failed to create note for user: " + create_result.message)
