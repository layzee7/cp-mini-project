
import os
import sqlite3
from datetime import date
from functools import wraps

from flask import Flask, jsonify, request, session
from flask_cors import CORS
from werkzeug.security import check_password_hash

from database import get_db_connection, initialize_db


# ==========================================
# FLASK CONFIGURATION
# ==========================================

app = Flask(__name__)

# Use an environment variable for deployment.
# A temporary random key is generated for local development
# if SECRET_KEY has not been configured.
app.secret_key = os.environ.get("SECRET_KEY") or os.urandom(32)

app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=False  # Local HTTP development only
)

# Change this origin if your Live Server uses localhost
# or a different port.
CORS(
    app,
    origins=["http://127.0.0.1:5500"],
    supports_credentials=True
)


# ==========================================
# LOGIN PROTECTION
# ==========================================

def login_required(function):
    @wraps(function)
    def wrapper(*args, **kwargs):
        if "librarian_id" not in session:
            return jsonify({"error": "Please log in first"}), 401

        return function(*args, **kwargs)

    return wrapper


# Convert database rows into dictionaries.
def row_to_dict(row):
    return dict(row)


# ==========================================
# HOME ROUTE
# ==========================================

@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "message": "Library Management API is running!"
    })


# ==========================================
# AUTHENTICATION
# ==========================================

@app.route("/api/auth/login", methods=["POST"])
def login():
    data = request.get_json(silent=True) or {}

    username = data.get("username", "")
    password = data.get("password", "")

    if not isinstance(username, str) or not isinstance(password, str):
        return jsonify({"error": "Invalid username or password"}), 400

    username = username.strip()

    if not username or not password:
        return jsonify({
            "error": "Username and password are required"
        }), 400

    connection = get_db_connection()

    try:
        librarian = connection.execute(
            "SELECT * FROM librarians WHERE username = ?",
            (username,)
        ).fetchone()
    finally:
        connection.close()

    if librarian is None:
        return jsonify({"error": "Invalid username or password"}), 401

    if not check_password_hash(librarian["password_hash"], password):
        return jsonify({"error": "Invalid username or password"}), 401

    session.clear()
    session["librarian_id"] = librarian["id"]
    session["username"] = librarian["username"]

    return jsonify({
        "message": "Login successful",
        "username": librarian["username"]
    })


@app.route("/api/auth/me", methods=["GET"])
def check_login():
    if "librarian_id" not in session:
        return jsonify({"error": "Not logged in"}), 401

    return jsonify({
        "logged_in": True,
        "username": session["username"]
    })


@app.route("/api/auth/logout", methods=["POST"])
def logout():
    session.clear()

    return jsonify({
        "message": "Logged out successfully"
    })


# ==========================================
# BOOK MANAGEMENT
# ==========================================

# GET ALL BOOKS / SEARCH BOOKS

@app.route("/api/books", methods=["GET"])
@login_required
def get_books():
    search = request.args.get("search", "").strip()

    connection = get_db_connection()

    try:
        if search:
            pattern = f"%{search}%"

            books = connection.execute(
                """
                SELECT * FROM books
                WHERE title LIKE ? OR author LIKE ?
                ORDER BY id
                """,
                (pattern, pattern)
            ).fetchall()
        else:
            books = connection.execute(
                "SELECT * FROM books ORDER BY id"
            ).fetchall()

        return jsonify([row_to_dict(book) for book in books])

    finally:
        connection.close()


# GET ONE BOOK

@app.route("/api/books/<int:book_id>", methods=["GET"])
@login_required
def get_book(book_id):
    connection = get_db_connection()

    try:
        book = connection.execute(
            "SELECT * FROM books WHERE id = ?",
            (book_id,)
        ).fetchone()

        if book is None:
            return jsonify({"error": "Book not found"}), 404

        return jsonify(row_to_dict(book))

    finally:
        connection.close()


# ADD BOOK

@app.route("/api/books", methods=["POST"])
@login_required
def add_book():
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({"error": "JSON object required"}), 400

    title = data.get("title")
    author = data.get("author")
    isbn = data.get("isbn")

    if not isinstance(title, str) or not title.strip():
        return jsonify({"error": "Valid title required"}), 400

    if not isinstance(author, str) or not author.strip():
        return jsonify({"error": "Valid author required"}), 400

    if isbn is not None and not isinstance(isbn, str):
        return jsonify({"error": "ISBN must be a string"}), 400

    isbn = isbn.strip() if isbn and isbn.strip() else None

    connection = get_db_connection()

    try:
        cursor = connection.execute(
            """
            INSERT INTO books (title, author, isbn)
            VALUES (?, ?, ?)
            """,
            (title.strip(), author.strip(), isbn)
        )

        connection.commit()

        return jsonify({
            "message": "Book added successfully",
            "id": cursor.lastrowid
        }), 201

    except sqlite3.IntegrityError:
        return jsonify({"error": "ISBN already exists"}), 409

    finally:
        connection.close()


# UPDATE BOOK

@app.route("/api/books/<int:book_id>", methods=["PUT"])
@login_required
def update_book(book_id):
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({"error": "JSON object required"}), 400

    title = data.get("title")
    author = data.get("author")
    isbn = data.get("isbn")

    if not isinstance(title, str) or not title.strip():
        return jsonify({"error": "Valid title required"}), 400

    if not isinstance(author, str) or not author.strip():
        return jsonify({"error": "Valid author required"}), 400

    if isbn is not None and not isinstance(isbn, str):
        return jsonify({"error": "ISBN must be a string"}), 400

    isbn = isbn.strip() if isbn and isbn.strip() else None

    connection = get_db_connection()

    try:
        cursor = connection.execute(
            """
            UPDATE books
            SET title = ?, author = ?, isbn = ?
            WHERE id = ?
            """,
            (title.strip(), author.strip(), isbn, book_id)
        )

        if cursor.rowcount == 0:
            return jsonify({"error": "Book not found"}), 404

        connection.commit()

        return jsonify({
            "message": "Book updated successfully"
        })

    except sqlite3.IntegrityError:
        return jsonify({"error": "ISBN already exists"}), 409

    finally:
        connection.close()


# DELETE BOOK

@app.route("/api/books/<int:book_id>", methods=["DELETE"])
@login_required
def delete_book(book_id):
    connection = get_db_connection()

    try:
        cursor = connection.execute(
            "DELETE FROM books WHERE id = ?",
            (book_id,)
        )

        if cursor.rowcount == 0:
            return jsonify({"error": "Book not found"}), 404

        connection.commit()

        return jsonify({
            "message": "Book deleted successfully"
        })

    except sqlite3.IntegrityError:
        return jsonify({
            "error": "Cannot delete a book with borrowing history"
        }), 409

    finally:
        connection.close()


# ==========================================
# MEMBER MANAGEMENT
# ==========================================

# GET ALL MEMBERS

@app.route("/api/members", methods=["GET"])
@login_required
def get_members():
    connection = get_db_connection()

    try:
        members = connection.execute(
            "SELECT * FROM members ORDER BY id"
        ).fetchall()

        return jsonify([row_to_dict(member) for member in members])

    finally:
        connection.close()


# GET ONE MEMBER

@app.route("/api/members/<int:member_id>", methods=["GET"])
@login_required
def get_member(member_id):
    connection = get_db_connection()

    try:
        member = connection.execute(
            "SELECT * FROM members WHERE id = ?",
            (member_id,)
        ).fetchone()

        if member is None:
            return jsonify({"error": "Member not found"}), 404

        return jsonify(row_to_dict(member))

    finally:
        connection.close()


# REGISTER MEMBER

@app.route("/api/members", methods=["POST"])
@login_required
def add_member():
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({"error": "JSON object required"}), 400

    name = data.get("name")
    email = data.get("email")
    phone = data.get("phone")

    if not isinstance(name, str) or not name.strip():
        return jsonify({"error": "Valid name required"}), 400

    if not isinstance(email, str) or "@" not in email:
        return jsonify({"error": "Valid email required"}), 400

    if phone is not None and not isinstance(phone, str):
        return jsonify({"error": "Phone must be a string"}), 400

    connection = get_db_connection()

    try:
        cursor = connection.execute(
            """
            INSERT INTO members (name, email, phone)
            VALUES (?, ?, ?)
            """,
            (
                name.strip(),
                email.strip().lower(),
                phone.strip() if phone else None
            )
        )

        connection.commit()

        return jsonify({
            "message": "Member registered successfully",
            "id": cursor.lastrowid
        }), 201

    except sqlite3.IntegrityError:
        return jsonify({"error": "Email already registered"}), 409

    finally:
        connection.close()


# ==========================================
# BOOK ISSUING
# ==========================================

@app.route("/api/loans", methods=["POST"])
@login_required
def issue_book():
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({"error": "JSON object required"}), 400

    book_id = data.get("book_id")
    member_id = data.get("member_id")
    due_date = data.get("due_date")

    # Validate book ID.
    if (
        isinstance(book_id, bool)
        or not isinstance(book_id, int)
        or book_id <= 0
    ):
        return jsonify({"error": "Valid book_id required"}), 400

    # Validate member ID.
    if (
        isinstance(member_id, bool)
        or not isinstance(member_id, int)
        or member_id <= 0
    ):
        return jsonify({"error": "Valid member_id required"}), 400

    # Validate due date.
    try:
        if not isinstance(due_date, str):
            raise ValueError

        due = date.fromisoformat(due_date)

        if due_date != due.isoformat():
            raise ValueError

    except (ValueError, TypeError):
        return jsonify({
            "error": "Due date must use YYYY-MM-DD format"
        }), 400

    if due < date.today():
        return jsonify({
            "error": "Due date cannot be in the past"
        }), 400

    connection = get_db_connection()

    try:
        # Start an atomic database transaction.
        connection.execute("BEGIN IMMEDIATE")

        book = connection.execute(
            "SELECT * FROM books WHERE id = ?",
            (book_id,)
        ).fetchone()

        member = connection.execute(
            "SELECT * FROM members WHERE id = ?",
            (member_id,)
        ).fetchone()

        if book is None:
            connection.rollback()
            return jsonify({"error": "Book not found"}), 404

        if member is None:
            connection.rollback()
            return jsonify({"error": "Member not found"}), 404

        if not book["available"]:
            connection.rollback()
            return jsonify({
                "error": "Book is currently unavailable"
            }), 409

        issue_date = date.today().isoformat()

        # Create borrowing record.
        cursor = connection.execute(
            """
            INSERT INTO loans
            (book_id, member_id, issue_date, due_date)
            VALUES (?, ?, ?, ?)
            """,
            (book_id, member_id, issue_date, due_date)
        )

        # Mark book unavailable.
        connection.execute(
            "UPDATE books SET available = 0 WHERE id = ?",
            (book_id,)
        )

        connection.commit()

        return jsonify({
            "message": "Book issued successfully",
            "loan_id": cursor.lastrowid,
            "book_id": book_id,
            "member_id": member_id,
            "issue_date": issue_date,
            "due_date": due_date
        }), 201

    except sqlite3.Error:
        connection.rollback()
        return jsonify({"error": "Could not issue book"}), 500

    finally:
        connection.close()


# ==========================================
# BOOK RETURNS
# ==========================================

@app.route("/api/loans/<int:loan_id>/return", methods=["PUT"])
@login_required
def return_book(loan_id):
    connection = get_db_connection()

    try:
        connection.execute("BEGIN IMMEDIATE")

        loan = connection.execute(
            """
            SELECT * FROM loans
            WHERE id = ? AND return_date IS NULL
            """,
            (loan_id,)
        ).fetchone()

        if loan is None:
            connection.rollback()
            return jsonify({
                "error": "Active loan not found or already returned"
            }), 404

        return_date = date.today().isoformat()

        # Update borrowing record.
        connection.execute(
            """
            UPDATE loans
            SET return_date = ?
            WHERE id = ?
            """,
            (return_date, loan_id)
        )

        # Make the book available again.
        connection.execute(
            """
            UPDATE books
            SET available = 1
            WHERE id = ?
            """,
            (loan["book_id"],)
        )

        connection.commit()

        return jsonify({
            "message": "Book returned successfully",
            "loan_id": loan_id,
            "return_date": return_date
        })

    except sqlite3.Error:
        connection.rollback()
        return jsonify({"error": "Could not return book"}), 500

    finally:
        connection.close()


# ==========================================
# BORROWING HISTORY
# ==========================================

@app.route("/api/loans", methods=["GET"])
@login_required
def get_loans():
    connection = get_db_connection()

    try:
        loans = connection.execute(
            """
            SELECT
                loans.id,
                books.title AS book_title,
                members.name AS member_name,
                loans.book_id,
                loans.member_id,
                loans.issue_date,
                loans.due_date,
                loans.return_date
            FROM loans
            JOIN books ON loans.book_id = books.id
            JOIN members ON loans.member_id = members.id
            ORDER BY loans.id DESC
            """
        ).fetchall()

        results = []

        for loan in loans:
            item = row_to_dict(loan)

            if loan["return_date"]:
                item["status"] = "Returned"
            elif loan["due_date"] < date.today().isoformat():
                item["status"] = "Overdue"
            else:
                item["status"] = "Borrowed"

            results.append(item)

        return jsonify(results)

    finally:
        connection.close()


# ==========================================
# DASHBOARD
# ==========================================

@app.route("/api/dashboard", methods=["GET"])
@login_required
def dashboard():
    connection = get_db_connection()

    try:
        total_books = connection.execute(
            "SELECT COUNT(*) FROM books"
        ).fetchone()[0]

        available_books = connection.execute(
            "SELECT COUNT(*) FROM books WHERE available = 1"
        ).fetchone()[0]

        total_members = connection.execute(
            "SELECT COUNT(*) FROM members"
        ).fetchone()[0]

        active_loans = connection.execute(
            "SELECT COUNT(*) FROM loans WHERE return_date IS NULL"
        ).fetchone()[0]

        overdue_loans = connection.execute(
            """
            SELECT COUNT(*) FROM loans
            WHERE return_date IS NULL AND due_date < ?
            """,
            (date.today().isoformat(),)
        ).fetchone()[0]

        return jsonify({
            "total_books": total_books,
            "available_books": available_books,
            "borrowed_books": total_books - available_books,
            "total_members": total_members,
            "active_loans": active_loans,
            "overdue_loans": overdue_loans
        })

    finally:
        connection.close()


# ==========================================
# RUN APPLICATION
# ==========================================

if __name__ == "__main__":
    initialize_db()
    app.run(debug=True, port=5000)
