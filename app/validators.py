"""
A module implementing form validation for the forms of the website
"""

import re
from results import ManyResults, Result, merge_many_results
from dal import Sqlite3DAL


def validate_registration(form, db_) -> ManyResults:
    """
    Validates the user registration form.
    Returns an Error(str) on failure, or True on success.
    """
    username = form.get("username")
    password = form.get("password")
    password_2 = form.get("password_2")
    results = Result.Success()

    username_validation = is_valid_username(username)
    results = merge_many_results(results, username_validation)

    password_validation = is_valid_password(password, password_2)
    results = merge_many_results(results, password_validation)

    # Check if the username is already taken
    user = Sqlite3DAL.find_user_by_username(db_, username)
    if isinstance(user, Result.Success):
        results = merge_many_results(
            results,
            [Result.Error("That username is already taken. Please choose another.")],
        )

    return results


def is_valid_username(username: str) -> ManyResults:
    """
    Check if a username contains only whitelisted characters.
    (a-z, A-Z, 0-9, underscore, hyphen)
    """
    results = Result.Success()

    if not username.strip():
        results = merge_many_results(
            results, [Result.Error("Username is required cannot contain whitespace.")]
        )

    # Enforce length constraints
    if len(username) < 5 or len(username) > 25:
        results = merge_many_results(
            results, [Result.Error("Username must be between 5 and 30 characters.")]
        )

    if not re.match(r"^[a-zA-Z0-9_-]{4,30}$", username):
        results = merge_many_results(
            results,
            [
                Result.Error(
                    """
            Username must be 5-30 characters long and contain only letters,
            numbers, underscores or hyphens.
            """
                )
            ],
        )

    return results


def is_valid_password(password: str, password_2: str) -> ManyResults:
    """
    Check if a password is valid.
    """
    results = Result.Success()

    if not password or not password_2:
        results = merge_many_results(
            results, [Result.Error("Please enter your password twice.")]
        )

    if len(password) < 8:
        results = merge_many_results(
            results, [Result.Error("Password must be at least 8 characters long.")]
        )

    if password != password_2:
        results = merge_many_results(results, [Result.Error("Passwords do not match.")])

    return results


def validate_note(form) -> Result.Type:
    """
    Validates an attempt to edit or create a note.
    Returns an Error(str) on failure, or True on success.
    """

    content: str = form.get("note_content")

    if not content.strip():
        return Result.Error("Note content cannot be empty.")

    return Result.Success()
