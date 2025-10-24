"""
This module just exists to store the seed functions for the database for development.
"""

import json
from returns.result import Failure
from validators import validate_registration
from dal import DAL


def init_db(db_):
    """Initializes the db tables"""
    db_.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
        """
    )
    db_.execute(
        """
        CREATE TABLE IF NOT EXISTS notes (
            id INTEGER PRIMARY KEY,
            user_id INTEGER,
            content TEXT NOT NULL
        )
        """
    )


def seed_db(db_):
    """Seeds the database with 5 default users using the DAL, and the config file."""

    with open("config.json", "r", encoding="utf-8") as f:
        config = json.load(f)

    users = config["seed_users"]

    for user in users:
        username = user["username"]
        password = user["password"]

        validate_result = validate_registration(username, password, password)

        if isinstance(validate_result, Failure):
            error_str: str = "Failed to validate config seed inputs:"

            for fail in validate_result.failure():
                error_str += "\n" + fail
            raise ValueError(error_str)

        create_user_result = DAL.create_user(db_, username, password)

        if (
            isinstance(create_user_result, Failure)
            and create_user_result.failure() != "This username is already taken."
        ):
            raise ValueError(
                "Failed to create user during seeding: " + create_user_result.failure()
            )

    for user in users:
        username = user["username"]
        existing_user_result = DAL.find_user_by_username(db_, username)

        if isinstance(existing_user_result, Failure):
            raise ValueError(
                "Failed to find user after creation during seeding: "
                + existing_user_result.failure()
            )

        user_id = existing_user_result.unwrap()[0]

        has_notes = DAL.get_notes_for_user(db_, user_id)

        if isinstance(has_notes, Failure):
            raise ValueError(
                "Failed to check whether user had notes during seeding: "
                + has_notes.failure()
            )

        if len(has_notes.unwrap()) >= 1:
            # Don't add any notes if the seed users already have some.
            continue

        content = f"This is a note for {username}."

        create_note_result = DAL.create_note_for_user(db_, user_id, content)

        if isinstance(create_note_result, Failure):
            raise ValueError(
                "Failed to create note for user: " + create_note_result.failure()
            )
