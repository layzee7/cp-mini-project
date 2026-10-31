# Library Management System

A web-based Library Management System developed as a college mini project using Python Flask, SQLite, HTML, CSS and JavaScript.

## Features

- Librarian login and logout
- Add, edit, delete and search books
- Register library members
- Issue books to members
- Return borrowed books
- View borrowing history
- Dashboard with library statistics

## Technologies Used

- **Frontend:** HTML, CSS, JavaScript
- **Backend:** Python, Flask
- **Database:** SQLite
- **Development Tool:** Visual Studio Code

## Project Structure

```text
library-management-system/
├── backend/
│   ├── app.py
│   ├── database.py
│   └── create_admin.py
├── frontend/
│   ├── index.html
│   ├── style.css
│   └── script.js
├── requirements.txt
├── README.md
└── .gitignore
```

## Installation and Setup

1. Download or clone this repository.
2. Open the project folder in VS Code.
3. Create a virtual environment:

   `python -m venv .venv`

4. Activate it on Windows Command Prompt:

   `.venv\Scripts\activate.bat`

5. Install dependencies:

   `pip install -r requirements.txt`

6. Create a librarian account:

   `python backend/create_admin.py`

7. Start the backend:

   `python backend/app.py`

8. Open `frontend/index.html` using VS Code Live Server.

## Login

Create your own librarian username and password using `create_admin.py`. There is no shared default login.

## Project Purpose

This project demonstrates CRUD operations, database connectivity, REST API development, frontend-backend integration and basic authentication.

## Author

College Mini Project