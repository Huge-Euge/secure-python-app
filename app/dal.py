"""
This module encapsulates all database access functionality
"""

import sqlite3
from typing import Tuple
from werkzeug.security import check_password_hash, generate_password_hash
from returns.result import Result, Success, Failure

DbConnection = sqlite3.Connection


class DAL:
    """A namespace for all sqlite3 database operations"""

    @staticmethod
    def find_user_by_id(db_: DbConnection, user_id: int) -> Result[Tuple, str]:
        """
        Finds a user by user_id in the database.
        Returns Success(user_record) or Failure.
        """
        try:
            user = db_.execute(
                "SELECT * FROM users WHERE id = ?", (user_id,)
            ).fetchone()

            if user:
                return Success(user)
            return Failure("User not found.")
        except sqlite3.Error as e:
            print(f"Database error in find_user: {e}")
            return Failure("A database error occurred.")

    @staticmethod
    def find_user_by_username(db_: DbConnection, username: str) -> Result[Tuple, str]:
        """
        Finds a user by username in the database.
        Returns Success(user_record) or Failure.
        """
        try:
            user = db_.execute(
                "SELECT * FROM users WHERE username = ?", (username,)
            ).fetchone()

            if user:
                return Success(user)
            return Failure("User not found.")
        except sqlite3.Error as e:
            print(f"Database error in find_user: {e}")
            return Failure("A database error occurred.")

    @staticmethod
    def create_user(
        db_: DbConnection, username: str, password: str
    ) -> Result[None, str]:
        """
        Creates a new user in the database.
        Returns Success(None) or Failure(str).
        """
        hashed_password = generate_password_hash(password)
        try:
            db_.execute(
                "INSERT INTO users (username, password) VALUES (?, ?)",
                (username, hashed_password),
            )
            db_.commit()
            return Success(None)
        except sqlite3.IntegrityError:
            # error occurs if the username is not unique
            return Failure("This username is already taken.")
        except sqlite3.Error as e:
            print(f"Database error in create_user: {e}")
            return Failure("A database error occurred.")

    @staticmethod
    def update_password(
        db_: DbConnection, user_id: int, old_password: str, new_password: str
    ) -> Result[None, str]:
        """
        updates a user's password.
        returns Success(None) or Failure(str)
        """
        try:
            if not new_password:
                return Failure("No new password given")

            user = db_.execute(
                "SELECT password FROM users WHERE id = ?", (user_id,)
            ).fetchone()

            if not user:
                return Failure("User not found.")

            if not check_password_hash(user[0], old_password):
                return Failure("Incorrect current password.")

            hashed_new_password = generate_password_hash(new_password)

            db_.execute(
                """
                UPDATE users 
                SET password = ?
                WHERE id = ?
                """,
                (
                    hashed_new_password,
                    user_id,
                ),
            )
            db_.commit()
            return Success(None)
        except sqlite3.Error as e:
            print(f"database error in update_password: {e}")
            return Failure("could not update password due to a database error.")

    @staticmethod
    def get_note_by_id(
        db_: DbConnection, note_id: int, user_id: int
    ) -> Result[Tuple, str]:
        """
        Retrieves a note by id
        Returns Success(note) or Failure.
        """
        try:
            note = db_.execute(
                "SELECT id, content FROM notes WHERE id = ? AND user_id = ?",
                (note_id, user_id),
            ).fetchone()

            if note:
                return Success(note)
            return Failure(
                "No note was found with the given id, created by the given user."
            )
        except sqlite3.Error as e:
            print(f"Database error in get_note_by_id: {e}")
            return Failure("Could not retrieve note due to a database error.")

    @staticmethod
    def get_notes_for_user(db_: DbConnection, user_id: int) -> Result[list[Tuple], str]:
        """
        Retrieves all notes for a given user ID.
        Returns Success(list_of_notes) or Failure.
        """
        try:
            notes = db_.execute(
                "SELECT id, content FROM notes WHERE user_id = ?", (user_id,)
            ).fetchall()
            # If this returns an empty list, that's fine.
            # Some users will have no notes when they open the /notes page
            return Success(notes)
        except sqlite3.Error as e:
            print(f"Database error in get_notes_for_user: {e}")
            return Failure("Could not retrieve notes due to a database error.")

    @staticmethod
    def create_note_for_user(
        db_: DbConnection, user_id: int, content: str
    ) -> Result[None, str]:
        """
        Creates a new note for a given user.
        Returns Success() or Failure.
        """
        try:
            if not content:
                return Failure("Note content cannot be empty.")

            db_.execute(
                "INSERT INTO notes (user_id, content) VALUES (?, ?)",
                (user_id, content),
            )
            db_.commit()
            return Success(None)
        except sqlite3.Error as e:
            print(f"Database error in create_note_for_user: {e}")
            return Failure("Could not save note due to a database error.")

    @staticmethod
    def edit_note(
        db_: DbConnection, note_id: int, user_id: int, new_content: str
    ) -> Result[None, str]:
        """
        updates a note by note_id
        returns result.success() or result.error.
        """
        try:
            if not new_content:
                return Failure("note content cannot be empty.")

            cursor = db_.execute(
                """
                UPDATE notes 
                SET content = ?
                WHERE id = ?
                AND user_id = ?
                """,
                (
                    new_content,
                    note_id,
                    user_id,
                ),
            )
            db_.commit()

            if cursor.rowcount == 0:
                # The user has not notes with that id.
                return Failure("You do not have a note with the given id.")
            return Success(None)
        except sqlite3.Error as e:
            print(f"Database error in edit_note: {e}")
            return Failure("Could not update note due to a database error.")

    @staticmethod
    def delete_note(db_: DbConnection, note_id: int, user_id: str) -> Result[None, str]:
        """
        Delete a note by id
        Returns Success() or Failure.
        """
        try:
            cursor = db_.execute(
                "DELETE FROM notes WHERE id = ? AND user_id = ?",
                (note_id, user_id),
            )
            db_.commit()

            if cursor.rowcount == 0:
                # No note was found with that id
                return Failure("You do not have a note with the given id.")
            return Success(None)
        except sqlite3.Error as e:
            print(f"Database error in delete_note: {e}")
            return Failure("Could not delete note due to a database error.")
