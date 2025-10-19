"""
This module encapsulates all database access functionality
"""

import sqlite3
from results import Result

DbConnection = sqlite3.Connection


class DAL:
    """A namespace for all sqlite3 database operations"""

    @staticmethod
    def find_user_by_id(db_: DbConnection, user_id: int) -> Result.Type:
        """
        Finds a user by user_id in the database.
        Returns Result.Success(user_record) or Result.Error.
        """
        try:
            user = db_.execute(
                "SELECT * FROM users WHERE id = ?", (user_id,)
            ).fetchone()

            if user:
                return Result.Success(user)
            return Result.Error("User not found.")
        except sqlite3.Error as e:
            # database errors (e.g., table not found)
            print(f"Database error in find_user: {e}")
            return Result.Error(message="A database error occurred.")

    @staticmethod
    def find_user_by_username(db_: DbConnection, username: str) -> Result.Type:
        """
        Finds a user by username in the database.
        Returns Result.Success(user_record) or Result.Error.
        """
        try:
            user = db_.execute(
                "SELECT * FROM users WHERE username = ?", (username,)
            ).fetchone()

            if user:
                return Result.Success(user)
            return Result.Error("User not found.")
        except sqlite3.Error as e:
            # database errors (e.g., table not found)
            print(f"Database error in find_user: {e}")
            return Result.Error("A database error occurred.")

    @staticmethod
    def create_user(
        db_: DbConnection, username: str, hashed_password: str
    ) -> Result.Type:
        """
        Creates a new user in the database.
        Returns Result.Success() or Result.Error.
        """
        try:
            db_.execute(
                "INSERT INTO users (username, password) VALUES (?, ?)",
                (username, hashed_password),
            )
            db_.commit()
            return Result.Success()
        except sqlite3.IntegrityError:
            # error occurs if the username is not unique
            return Result.Error("This username is already taken.")
        except sqlite3.Error as e:
            print(f"Database error in create_user: {e}")
            return Result.Error("A database error occurred.")

    @staticmethod
    def update_password(
        db_: DbConnection, user_id: int, new_hashed_password: str
    ) -> Result.Type:
        """
        updates a user's password.
        returns result.success() or result.error with a message.
        """
        try:
            if not new_hashed_password:
                return Result.Error("No new password given")

            db_.execute(
                """
                UPDATE users 
                SET password = ?
                WHERE id = ?
                """,
                (
                    new_hashed_password,
                    user_id,
                ),
            )
            db_.commit()
            return Result.Success()
        except sqlite3.Error as e:
            print(f"database error in edit_note: {e}")
            return Result.Error("could not update note due to a database error.")

    @staticmethod
    def get_note_by_id(db_: DbConnection, note_id: int) -> Result.Type:
        """
        Retrieves a note by id
        Returns Result.Success(note) or Result.Error.
        """
        try:
            note = db_.execute(
                "SELECT content FROM notes WHERE id = ?", (note_id,)
            ).fetchone()
            return Result.Success(note)
        except sqlite3.Error as e:
            print(f"Database error in get_note_by_id: {e}")
            return Result.Error("Could not retrieve note due to a database error.")

    @staticmethod
    def get_notes_for_user(db_: DbConnection, user_id: int) -> Result.Type:
        """
        Retrieves all notes for a given user ID.
        Returns Result.Success(list_of_notes) or Result.Error.
        """
        try:
            notes = db_.execute(
                "SELECT content FROM notes WHERE user_id = ?", (user_id,)
            ).fetchall()
            return Result.Success(notes)
        except sqlite3.Error as e:
            print(f"Database error in get_notes_for_user: {e}")
            return Result.Error("Could not retrieve notes due to a database error.")

    @staticmethod
    def create_note_for_user(
        db_: DbConnection, user_id: int, content: str
    ) -> Result.Type:
        """
        Creates a new note for a given user.
        Returns Result.Success() or Result.Error.
        """
        try:
            if not content:
                return Result.Error("Note content cannot be empty.")

            db_.execute(
                "INSERT INTO notes (user_id, content) VALUES (?, ?)",
                (user_id, content),
            )
            db_.commit()
            return Result.Success()
        except sqlite3.Error as e:
            print(f"Database error in create_note_for_user: {e}")
            return Result.Error("Could not save note due to a database error.")

    @staticmethod
    def edit_note(db_: DbConnection, note_id: int, new_content: str) -> Result.Type:
        """
        updates a note by note_id
        returns result.success() or result.error.
        """
        try:
            if not new_content:
                return Result.Error("note content cannot be empty.")

            db_.execute(
                """
                UPDATE notes 
                SET content = ?
                WHERE id = ?
                """,
                (
                    new_content,
                    note_id,
                ),
            )
            db_.commit()
            return Result.Success()
        except sqlite3.Error as e:
            print(f"Database error in edit_note: {e}")
            return Result.Error("Could not update note due to a database error.")

    @staticmethod
    def delete_note(db_: DbConnection, note_id: int) -> Result.Type:
        """
        Delete a note by id
        Returns Result.Success() or Result.Error.
        """
        try:
            cursor = db_.execute(
                "DELETE FROM notes WHERE id = ?",
                (note_id,),
            )
            db_.commit()

            if cursor.rowcount == 0:
                # No note was found with that id
                return Result.Error("No note found with that id")
            return Result.Success()
        except sqlite3.Error as e:
            print(f"Database error in delete_note: {e}")
            return Result.Error("Could not delete note due to a database error.")
