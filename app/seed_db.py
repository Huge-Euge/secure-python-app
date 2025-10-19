"""
This module just exists to store the seed functions for the database for development.
"""

import json
from dal import DAL
from results import Result
from validators import validate_registration
from werkzeug.security import generate_password_hash


def seed_db(db_):
    """Seeds the database with 5 default users using the DAL, and the config file."""

    config = open("config.json", "r", encoding="utf-8")

    users = json.load(config)["seed_users"]

    for user in users:
        username = user["username"]
        password = user["password"]
        password_2 = password

        validate_result = validate_registration(username, password, password_2)

        if isinstance(validate_result, Result.Error):
            raise ValueError(
                "Failed to validate config seed inputs: " + validate_result.message
            )

        create_user_result = DAL.create_user(
            db_, username, generate_password_hash(password)
        )

        if (
            isinstance(create_user_result, Result.Error)
            and create_user_result.message != "This username is already taken."
        ):
            raise ValueError(
                "Failed to create user during seeding: " + create_user_result.message
            )

    for user in users:
        username = user["username"]
        existing_user_result = DAL.find_user_by_username(db_, username)

        if not isinstance(existing_user_result, Result.Success):
            raise ValueError(
                "Failed to find user after creation during seeding: "
                + existing_user_result.message
            )

        user_id = existing_user_result.value[0]

        has_notes = DAL.get_notes_for_user(db_, user_id)

        if isinstance(has_notes, Result.Success):
            # Don't bother seeding because the user has notes already
            continue

        content = f"This is a note for {username}."

        create_note_result = DAL.create_note_for_user(db_, user_id, content)

        if not isinstance(create_note_result, Result.Success):
            raise ValueError(
                "Failed to create note for user: " + create_note_result.message
            )
