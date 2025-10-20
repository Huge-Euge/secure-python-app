"""
A module implementing form validation for the forms of the website
"""

import re
from returns.result import Result, Success, Failure
from results_extension import merge_results


def validate_registration(
    username: str, password: str, password_2: str
) -> Result[None, list[str]]:
    """
    Validates the user registration form.
    Returns a Failure([str]) on failure, or Success(None)
    """
    results = Success(None)

    username_validation = is_valid_username(username)
    results = merge_results(results, username_validation)

    password_validation = is_valid_password(password, password_2)
    results = merge_results(results, password_validation)

    return results


def is_valid_username(username: str) -> Result[None, list[str]]:
    """
    Check if a username contains only whitelisted characters.
    (a-z, A-Z, 0-9, underscore, hyphen)
    """
    results = Success(None)

    if not re.match(r"^[a-zA-Z0-9_-]{5,30}$", username):
        results = Failure(
            [
                """
            Username must be 5-30 characters long and contain only letters,
            numbers, underscores or hyphens.
            """
            ]
        )

    return results


def is_valid_password(password: str, password_2: str) -> Result[None, list[str]]:
    """
    Check if a password is valid.
    """
    results = Success(None)

    if not password or not password_2:
        results = merge_results(results, Failure(["Please enter your password twice."]))

    if len(password) < 8:
        results = merge_results(
            results, Failure(["Password must be at least 8 characters long."])
        )

    if password != password_2:
        results = merge_results(results, Failure(["Passwords do not match."]))

    return results


def validate_note(form) -> Result[None, list[str]]:
    """
    Validates an attempt to POST a note.
    Returns an Failure([str]), or Success(None)
    """

    content: str = form.get("note_content")

    results = Success(None)

    # The user has to input some text content
    if not content.strip():
        results = merge_results(results, Failure(["Note content cannot be empty."]))

    return results
