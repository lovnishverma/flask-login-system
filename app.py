
"""
Flask Login System with SQLite
Features:
- Signup (create new account)
- Login (check user credentials)
- Session (to remember login state)
- Cookies (to store last visit info)
- "Remember Me" option (stay logged in even after closing browser)
"""

from flask import Flask, render_template, request, redirect, url_for, session, make_response
import sqlite3
from datetime import timedelta

# Flask App Setup
app = Flask(__name__)

# Secret key is used to sign session data (must be kept secret in real apps!)
app.secret_key = "supersecretkey"

# Permanent sessions last for 7 days (used when "Remember Me" is checked)
app.permanent_session_lifetime = timedelta(days=7)


# Helper function to connect to SQLite database
def get_db_connection():
    # Connect to SQLite database (creates file users.db if it doesn’t exist)
    conn = sqlite3.connect("users.db")
    conn.row_factory = sqlite3.Row  # Makes rows behave like dictionaries
    return conn


# Initialize database with a "users" table
def init_db():
    conn = get_db_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT, -- Auto-increment ID
            username TEXT UNIQUE NOT NULL,        -- Unique username
            password TEXT NOT NULL                -- Password (plain text for demo, should use hashing!)
        )
    """)
    conn.commit()
    conn.close()

# Call database initialization at startup
init_db()


# Home Page (only logged-in users can see this)
@app.route("/")
def home():
    # Check if the user is logged in using session
    if "username" in session:
        username = session["username"]  # Get logged-in username from session

        # Get last visit message from cookie (if not found, show default message)
        last_visit = request.cookies.get("last_visit", "First time visiting!")

        return render_template("home.html", username=username, last_visit=last_visit)

    # If not logged in, redirect to login page
    return redirect(url_for("login"))


# Signup Page
@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":  # When user submits the form
        username = request.form["username"]
        password = request.form["password"]

        conn = get_db_connection()
        try:
            # Insert new user into database
            conn.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
            conn.commit()
            conn.close()

            # After signup, redirect to login page
            return redirect(url_for("login"))

        except sqlite3.IntegrityError:
            # This happens if the username already exists
            return "Username already exists! Try another."
    
    # If GET request, show signup form
    return render_template("signup.html")


# Login Page
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":  # When user submits login form
        username = request.form["username"]
        password = request.form["password"]

        # Checkbox value: will be "on" if user ticks "Remember Me"
        remember = request.form.get("remember")

        # Check if username & password exist in database
        conn = get_db_connection()
        user = conn.execute("SELECT * FROM users WHERE username=? AND password=?", 
                            (username, password)).fetchone()
        conn.close()

        if user:
            # ✅ User found → start session
            if remember == "on":
                # Session will survive browser close (7 days)
                session.permanent = True
            else:
                # Session ends when browser closes
                session.permanent = False

            # Store username inside session
            session["username"] = username

            # Create response with cookie
            resp = make_response(redirect(url_for("home")))

            # Save a cookie with "last visit" info
            # If "Remember Me" checked → cookie valid for 7 days
            # Else → cookie lasts only until browser closes
            resp.set_cookie("last_visit", "Welcome back, " + username, 
                            max_age=(7*24*60*60 if remember == "on" else None))

            return resp
        else:
            # If username or password is wrong
            return "Invalid username or password. Try again."

    # If GET request, show login form
    return render_template("login.html")


# Logout Page
@app.route("/logout")
def logout():
    # Remove username from session
    session.pop("username", None)

    # Also delete the "last_visit" cookie
    resp = make_response(redirect(url_for("login")))
    resp.set_cookie("last_visit", "", expires=0)
    return resp


# Run the App
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)