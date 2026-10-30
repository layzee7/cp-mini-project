from getpass import getpass
from werkzeug.security import generate_password_hash
from database import get_db_connection, initialize_db

initialize_db()

username = input("Enter librarian username: ").strip()
password = getpass("Enter librarian password: ")

if not username or not password:
    print("Username and password cannot be empty.")
else:
    connection = get_db_connection()

    try:
        password_hash = generate_password_hash(password)

        connection.execute(
            "INSERT INTO librarians (username, password_hash) VALUES (?, ?)",
            (username, password_hash)
        )

        connection.commit()
        print("Librarian account created successfully!")

    except Exception as error:
        print("Could not create account:", error)

    finally:
        connection.close()