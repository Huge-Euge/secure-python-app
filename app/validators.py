from typing import Union, NamedTuple


class Error(NamedTuple):
    """
    Error message wrapper for typed union
    """

    value: str


ValidationResult = Union[True, Error]


def validate_registration(form, db_):
    """
    Validates the user registration form.
    Returns an Error(str) failure, or True on success.
    """
    username = form.get("username")
    password = form.get("password")
    password_2 = form.get("password_2")

    # Check for empty fields
    if not username or not password or not password_2:
        return Error("Username and password are required.")

    # Enforce length constraints
    if len(username) < 5 or len(username) > 25:
        return Error("Username must be between 5 and 25 characters.")

    if len(password) < 8:
        return Error("Password must be at least 8 characters long.")

    if password != password_2:
        return Error("Passwords do not match.")

    # Check if the username is already taken
    user = db_.execute(
        "SELECT username FROM users WHERE username = ?", (username,)
    ).fetchone()

    if user:
        return "That username is already taken. Please choose another."

    # If all checks pass, return True
    return True
