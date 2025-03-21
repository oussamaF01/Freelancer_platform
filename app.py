from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = "your_secret_key_here"

# Database setup
def create_tables():
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()

    # Create users table with rating for freelancers
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            role TEXT NOT NULL,
            bank_name TEXT NOT NULL,
            account_number TEXT NOT NULL,
            iban TEXT NOT NULL,
            rating REAL DEFAULT 0 CHECK(rating BETWEEN 0 AND 5)  -- Rating between 0 and 5
        )
    ''')

    # Create jobs table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    ''')

    # Create notifications table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            message TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    ''')

    # Create messages table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sender_id INTEGER,
            receiver_id INTEGER,
            message TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (sender_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (receiver_id) REFERENCES users(id) ON DELETE CASCADE
        )
    ''')

    conn.commit()
    conn.close()


# Function to add the rating column if it's missing
def add_rating_column():
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()

    # Check if the column already exists to avoid duplicate addition
    cursor.execute("PRAGMA table_info(users)")
    columns = [column[1] for column in cursor.fetchall()]
    if 'rating' not in columns:
        cursor.execute('ALTER TABLE users ADD COLUMN rating REAL DEFAULT 0')
        conn.commit()

    conn.close()

@app.route("/")
def home():
    return render_template("home.html")


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        full_name = request.form["full_name"]
        email = request.form["email"]
        password = request.form["password"]
        confirm_password = request.form["confirm_password"]
        role = request.form["role"]
        bank_name = request.form["bank_name"]
        account_number = request.form["account_number"]
        iban = request.form["iban"]

        if password != confirm_password:
            flash("Passwords do not match. Please try again.", "danger")
            return redirect(url_for('signup'))

        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()

        cursor.execute('''INSERT INTO users (full_name, email, password, role, bank_name, account_number, iban)
                          VALUES (?, ?, ?, ?, ?, ?, ?)''',
                       (full_name, email, password, role, bank_name, account_number, iban))

        conn.commit()
        conn.close()

        flash("Account created successfully! You can now log in.", "success")
        return redirect(url_for('login'))

    return render_template("signup.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE email = ? AND password = ?', (email, password))
        user = cursor.fetchone()
        conn.close()

        if user:
            session['user_id'] = user[0]
            session['user_role'] = user[4]

            if user[4] == "client":
                return redirect(url_for('client_dashboard'))
            else:
                return redirect(url_for('freelancer_dashboard'))
        else:
            flash("Invalid email or password. Please try again.", "danger")
            return redirect(url_for('login'))

    return render_template("login.html")


@app.route("/dashboard")
def client_dashboard():
    if 'user_id' in session and session['user_role'] == "client":
        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM users WHERE id = ?', (session['user_id'],))
        user = cursor.fetchone()

        cursor.execute('SELECT id, full_name, email, role, rating FROM users WHERE role = "freelancer"')
        freelancers = cursor.fetchall()

        cursor.execute('SELECT * FROM jobs')
        jobs = cursor.fetchall()

        conn.close()

        return render_template("dashboard.html", user=user, freelancers=freelancers, jobs=jobs)
    else:
        return redirect(url_for('login'))


@app.route("/create_project", methods=["GET", "POST"])
def create_project():
    if 'user_id' in session and session['user_role'] == "client":
        if request.method == "POST":
            title = request.form["title"]
            description = request.form["description"]
            user_id = session['user_id']

            conn = sqlite3.connect('users.db')
            cursor = conn.cursor()

            cursor.execute('''INSERT INTO jobs (user_id, title, description)
                              VALUES (?, ?, ?)''',
                           (user_id, title, description))

            conn.commit()
            conn.close()

            flash("Project created successfully!", "success")
            return redirect(url_for('client_dashboard'))

        return render_template("create_project.html")
    else:
        return redirect(url_for('login'))


@app.route("/send_message", methods=["POST"])
def send_message():
    if 'user_id' in session:
        sender_id = session['user_id']
        receiver_id = request.form['receiver_id']
        message = request.form['message']

        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()
        cursor.execute('''INSERT INTO messages (sender_id, receiver_id, message)
                          VALUES (?, ?, ?)''', (sender_id, receiver_id, message))
        conn.commit()
        conn.close()

        return "Message sent successfully!", 200
    return "Unauthorized", 401


@app.route("/get_messages/<int:receiver_id>")
def get_messages(receiver_id):
    if 'user_id' in session:
        sender_id = session['user_id']

        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()
        cursor.execute('''SELECT * FROM messages
                          WHERE (sender_id = ? AND receiver_id = ?)
                          OR (sender_id = ? AND receiver_id = ?)
                          ORDER BY timestamp''', (sender_id, receiver_id, receiver_id, sender_id))
        messages = cursor.fetchall()
        conn.close()

        return render_template("messages.html", messages=messages)
    return "Unauthorized", 401


@app.route("/get_notifications")
@app.route("/get_notifications")
def get_notifications():
    if 'user_id' in session:
        # Static notifications (hardcoded)
        static_notifications = [
            {"id": 1, "message": "Welcome to the platform!", "timestamp": "2023-10-01 12:00:00"},
            {"id": 2, "message": "New job posted: Web Development", "timestamp": "2023-10-02 13:00:00"}
        ]

        # Fetch dynamic notifications from the database
        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM notifications WHERE user_id = ? ORDER BY id DESC', (session['user_id'],))
        dynamic_notifications = [
            {"id": row[0], "message": row[2], "timestamp": row[3]}
            for row in cursor.fetchall()
        ]
        conn.close()

        # Combine static and dynamic notifications
        notifications_list = static_notifications + dynamic_notifications

        return jsonify(notifications_list)  # Return JSON response
    return "Unauthorized", 401


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for('home'))


@app.route("/freelancer_dashboard")
def freelancer_dashboard():
    if 'user_id' in session and session['user_role'] == "freelancer":
        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM users WHERE id = ?', (session['user_id'],))
        user = cursor.fetchone()

        cursor.execute('SELECT * FROM jobs')
        jobs = cursor.fetchall()

        conn.close()

        return render_template("freelancer_dashboard.html", user=user, jobs=jobs)
    else:
        return redirect(url_for('login'))


@app.route("/rate_freelancer", methods=["POST"])
def rate_freelancer():
    if 'user_id' in session and session['user_role'] == "client":
        freelancer_id = request.form['freelancer_id']
        rating = float(request.form['rating'])

        if 0 <= rating <= 5:
            conn = sqlite3.connect('users.db')
            cursor = conn.cursor()
            cursor.execute("UPDATE users SET rating = ? WHERE id = ? AND role = 'freelancer'", (rating, freelancer_id))
            conn.commit()
            conn.close()
            flash("Rating updated successfully!", "success")
        else:
            flash("Invalid rating. Must be between 0 and 5.", "danger")

    return redirect(url_for('client_dashboard'))


if __name__ == "__main__":
    create_tables()
    add_rating_column()  # Ensure rating is added
    app.run(debug=True)