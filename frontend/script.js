
// ==========================================
// API CONFIGURATION
// ==========================================

// Flask backend address.
const API_URL = "http://127.0.0.1:5000/api";


// ==========================================
// GENERAL HELPER FUNCTIONS
// ==========================================

// Send a request to Flask and handle errors.
async function apiRequest(endpoint, options = {}) {
    const response = await fetch(API_URL + endpoint, {
        ...options,
        credentials: "include",
        headers: {
            "Content-Type": "application/json",
            ...options.headers
        }
    });

    const data = await response.json();

    if (!response.ok) {
        throw new Error(data.error || "Something went wrong");
    }

    return data;
}
async function login(username, password) {
    try {
        const result = await apiRequest("/auth/login", {
            method: "POST",
            body: JSON.stringify({ username, password })
        });

        document.getElementById("loginSection").classList.add("hidden");
        document.getElementById("appNav").classList.remove("hidden");
        document.getElementById("appMain").classList.remove("hidden");

        showMessage("Welcome, " + result.username + "!");
        loadDashboard();

    } catch (error) {
        showMessage(error.message);
    }
}


async function logout() {
    try {
        await apiRequest("/auth/logout", {
            method: "POST"
        });

        document.getElementById("loginSection").classList.remove("hidden");
        document.getElementById("appNav").classList.add("hidden");
        document.getElementById("appMain").classList.add("hidden");

        document.getElementById("loginForm").reset();

        showMessage("You have logged out.");

    } catch (error) {
        showMessage(error.message);
    }
}


async function checkLogin() {
    try {
        await apiRequest("/auth/me");

        document.getElementById("loginSection").classList.add("hidden");
        document.getElementById("appNav").classList.remove("hidden");
        document.getElementById("appMain").classList.remove("hidden");

        loadDashboard();

    } catch (error) {
        document.getElementById("loginSection").classList.remove("hidden");
        document.getElementById("appNav").classList.add("hidden");
        document.getElementById("appMain").classList.add("hidden");
    }
}


// Display a message to the user.
function showMessage(message) {

    const messageBox = document.getElementById("message");

    messageBox.textContent = message;
    messageBox.style.display = "block";

    setTimeout(() => {
        messageBox.style.display = "none";
    }, 3000);
}


// Escape text before inserting it into HTML.
function escapeHTML(value) {
    return String(value ?? "").replace(/[&<>"']/g, char => ({
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        '"': "&quot;",
        "'": "&#39;"
    })[char]);
}


// ==========================================
// NAVIGATION
// ==========================================

function showSection(sectionId) {

    document.querySelectorAll(".page").forEach(page => {
        page.classList.add("hidden");
    });

    document.getElementById(sectionId).classList.remove("hidden");

    // Load fresh data when opening a section.
    if (sectionId === "dashboard") loadDashboard();
    if (sectionId === "books") loadBooks();
    if (sectionId === "members") loadMembers();
    if (sectionId === "loans") loadLoans();
}


// ==========================================
// DASHBOARD
// ==========================================

async function loadDashboard() {

    try {

        const data = await apiRequest("/dashboard");

        document.getElementById("totalBooks").textContent =
            data.total_books;

        document.getElementById("availableBooks").textContent =
            data.available_books;

        document.getElementById("totalMembers").textContent =
            data.total_members;

        document.getElementById("activeLoans").textContent =
            data.active_loans;

        document.getElementById("overdueLoans").textContent =
            data.overdue_loans;

    } catch (error) {
        showMessage(error.message);
    }
}


// ==========================================
// BOOK MANAGEMENT
// ==========================================

// GET ALL BOOKS
async function loadBooks(search = "") {

    try {

        const data = await apiRequest(
            "/books?search=" + encodeURIComponent(search)
        );

        const container = document.getElementById("booksList");

        if (data.length === 0) {
            container.textContent = "No books found.";
            return;
        }

        let html = `
            <table>
                <tr>
                    <th>ID</th>
                    <th>Title</th>
                    <th>Author</th>
                    <th>ISBN</th>
                    <th>Availability</th>
                    <th>Actions</th>
                </tr>
        `;

        data.forEach(book => {

            html += `
                <tr>
                    <td>${book.id}</td>
                    <td>${escapeHTML(book.title)}</td>
                    <td>${escapeHTML(book.author)}</td>
                    <td>${escapeHTML(book.isbn || "-")}</td>
                    <td>
                        ${book.available ? "Available" : "Borrowed"}
                    </td>
                    <td>
                        <button class="edit-btn"
                            onclick="editBook(${book.id})">
                            Edit
                        </button>

                        <button class="delete-btn"
                            onclick="deleteBook(${book.id})">
                            Delete
                        </button>
                    </td>
                </tr>
            `;
        });

        html += "</table>";

        container.innerHTML = html;

    } catch (error) {
        showMessage(error.message);
    }
}


// ADD BOOK
document.getElementById("bookForm").addEventListener(
    "submit",
    async function(event) {

        event.preventDefault();

        const book = {
            title: document.getElementById("bookTitle").value,
            author: document.getElementById("bookAuthor").value,
            isbn: document.getElementById("bookIsbn").value
        };

        try {

            await apiRequest("/books", {
                method: "POST",
                body: JSON.stringify(book)
            });

            showMessage("Book added successfully!");

            this.reset();

            loadBooks();
            loadDashboard();

        } catch (error) {
            showMessage(error.message);
        }
    }
);


// EDIT BOOK
async function editBook(id) {

    try {

        const book = await apiRequest("/books/" + id);

        const title = prompt("Enter book title:", book.title);

        if (title === null) return;

        const author = prompt("Enter author:", book.author);

        if (author === null) return;

        const isbn = prompt("Enter ISBN:", book.isbn || "");

        if (isbn === null) return;

        await apiRequest("/books/" + id, {
            method: "PUT",
            body: JSON.stringify({
                title,
                author,
                isbn
            })
        });

        showMessage("Book updated successfully!");

        loadBooks();

    } catch (error) {
        showMessage(error.message);
    }
}


// DELETE BOOK
async function deleteBook(id) {

    if (!confirm("Are you sure you want to delete this book?")) {
        return;
    }

    try {

        await apiRequest("/books/" + id, {
            method: "DELETE"
        });

        showMessage("Book deleted successfully!");

        loadBooks();
        loadDashboard();

    } catch (error) {
        showMessage(error.message);
    }
}


// BOOK SEARCH
document.getElementById("bookSearch").addEventListener(
    "input",
    function() {
        loadBooks(this.value);
    }
);


// ==========================================
// MEMBER MANAGEMENT
// ==========================================

// GET MEMBERS
async function loadMembers() {

    try {

        const members = await apiRequest("/members");

        const container = document.getElementById("membersList");

        if (members.length === 0) {
            container.textContent = "No members registered.";
            return;
        }

        let html = `
            <table>
                <tr>
                    <th>ID</th>
                    <th>Name</th>
                    <th>Email</th>
                    <th>Phone</th>
                </tr>
        `;

        members.forEach(member => {

            html += `
                <tr>
                    <td>${member.id}</td>
                    <td>${escapeHTML(member.name)}</td>
                    <td>${escapeHTML(member.email)}</td>
                    <td>${escapeHTML(member.phone || "-")}</td>
                </tr>
            `;
        });

        html += "</table>";

        container.innerHTML = html;

    } catch (error) {
        showMessage(error.message);
    }
}


// REGISTER MEMBER
document.getElementById("memberForm").addEventListener(
    "submit",
    async function(event) {

        event.preventDefault();

        const member = {
            name: document.getElementById("memberName").value,
            email: document.getElementById("memberEmail").value,
            phone: document.getElementById("memberPhone").value
        };

        try {

            await apiRequest("/members", {
                method: "POST",
                body: JSON.stringify(member)
            });

            showMessage("Member registered successfully!");

            this.reset();

            loadMembers();
            loadDashboard();

        } catch (error) {
            showMessage(error.message);
        }
    }
);


// ==========================================
// BOOK BORROWING
// ==========================================

// ISSUE BOOK
document.getElementById("loanForm").addEventListener(
    "submit",
    async function(event) {

        event.preventDefault();

        const loan = {
            book_id: Number(
                document.getElementById("loanBookId").value
            ),

            member_id: Number(
                document.getElementById("loanMemberId").value
            ),

            due_date: document.getElementById("dueDate").value
        };

        try {

            await apiRequest("/loans", {
                method: "POST",
                body: JSON.stringify(loan)
            });

            showMessage("Book issued successfully!");

            this.reset();

            loadLoans();
            loadBooks();
            loadDashboard();

        } catch (error) {
            showMessage(error.message);
        }
    }
);


// ==========================================
// BORROWING HISTORY AND RETURNS
// ==========================================

async function loadLoans() {

    try {

        const loans = await apiRequest("/loans");

        const container = document.getElementById("loansList");

        if (loans.length === 0) {
            container.textContent = "No borrowing records found.";
            return;
        }

        let html = `
            <table>
                <tr>
                    <th>ID</th>
                    <th>Book</th>
                    <th>Member</th>
                    <th>Issue Date</th>
                    <th>Due Date</th>
                    <th>Return Date</th>
                    <th>Status</th>
                    <th>Action</th>
                </tr>
        `;

        loans.forEach(loan => {

            html += `
                <tr>
                    <td>${loan.id}</td>
                    <td>${escapeHTML(loan.book_title)}</td>
                    <td>${escapeHTML(loan.member_name)}</td>
                    <td>${escapeHTML(loan.issue_date)}</td>
                    <td>${escapeHTML(loan.due_date)}</td>
                    <td>${escapeHTML(loan.return_date || "-")}</td>
                    <td>${escapeHTML(loan.status)}</td>
                    <td>
                        ${
                            loan.return_date
                            ? "Completed"
                            : `<button class="return-btn"
                                onclick="returnLoan(${loan.id})">
                                Return
                              </button>`
                        }
                    </td>
                </tr>
            `;
        });

        html += "</table>";

        container.innerHTML = html;

    } catch (error) {
        showMessage(error.message);
    }
}


// RETURN BOOK
async function returnLoan(id) {

    if (!confirm("Confirm that this book has been returned?")) {
        return;
    }

    try {

        await apiRequest("/loans/" + id + "/return", {
            method: "PUT"
        });

        showMessage("Book returned successfully!");

        loadLoans();
        loadBooks();
        loadDashboard();

    } catch (error) {
        showMessage(error.message);
    }
}


// ==========================================
// APPLICATION STARTUP
// ==========================================

// Load dashboard when website opens.



document.getElementById("loginForm").addEventListener(
    "submit",
    async function(event) {
        event.preventDefault();

        const username = document.getElementById("loginUsername").value;
        const password = document.getElementById("loginPassword").value;

        await login(username, password);
    }
);
checkLogin();

document.getElementById("dueDate").min =
    new Date().toLocaleDateString("en-CA");