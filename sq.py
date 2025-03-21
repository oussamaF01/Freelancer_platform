import sqlite3

def create_database():
    # Connect to the SQLite database (or create it if it doesn't exist)
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()

    # Create users table with a rating column
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            role TEXT NOT NULL,  -- 'client' or 'freelancer'
            bank_name TEXT NOT NULL,
            account_number TEXT NOT NULL UNIQUE,
            iban TEXT NOT NULL UNIQUE,
            rating REAL DEFAULT 3.0,  -- Default rating for freelancers
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Create jobs table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            status TEXT DEFAULT 'open',  -- 'open', 'in_progress', 'completed'
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    ''')

    # Create notifications table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            message TEXT NOT NULL,
            is_read BOOLEAN DEFAULT 0,  -- 0 = unread, 1 = read
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    ''')

    # Create messages table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sender_id INTEGER NOT NULL,
            receiver_id INTEGER NOT NULL,
            message TEXT NOT NULL,
            is_read BOOLEAN DEFAULT 0,  -- 0 = unread, 1 = read
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (sender_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (receiver_id) REFERENCES users(id) ON DELETE CASCADE
        )
    ''')

    # Check if the 'rating' column exists (for updating an existing database)
    cursor.execute("PRAGMA table_info(users)")
    columns = [col[1] for col in cursor.fetchall()]
    if "rating" not in columns:
        cursor.execute("ALTER TABLE users ADD COLUMN rating REAL DEFAULT 3.0")

    # Insert sample freelancers with a default rating
    freelancers = [
        ('John Doe', 'john@example.com', 'password123', 'freelancer', 'Bank A', '1234567890', 'IBAN123456789', 4.5),
        ('Jane Smith', 'jane@example.com', 'password456', 'freelancer', 'Bank B', '0987654321', 'IBAN987654321', 3.8),
        ('Alice Johnson', 'alice@example.com', 'password789', 'freelancer', 'Bank C', '5678901234', 'IBAN567890123', 5.0)
    ]
    cursor.executemany('''
        INSERT INTO users (full_name, email, password, role, bank_name, account_number, iban, rating)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', freelancers)

    # Insert sample clients (clients don't need a rating)
    clients = [
        ('Client One', 'client1@example.com', 'password123', 'client', 'Bank D', '1122334455', 'IBAN1122334455'),
        ('Client Two', 'client2@example.com', 'password456', 'client', 'Bank E', '5566778899', 'IBAN5566778899')
    ]
    cursor.executemany('''
        INSERT INTO users (full_name, email, password, role, bank_name, account_number, iban)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', clients)

    # Insert sample job offers
    jobs = [
        (1, 'Web Development Project', 'Build a website for a local business.'),
        (2, 'Mobile App Design', 'Create a mobile app for a new startup.'),
        (1, 'SEO Optimization', 'Optimize the website for search engines.')
    ]
    cursor.executemany('''
        INSERT INTO jobs (user_id, title, description)
        VALUES (?, ?, ?)
    ''', jobs)

    # Insert sample notifications for users
    notifications = [
        (1, 'You have a new job offer!'),
        (2, 'Your job has been approved!'),
        (3, 'New task assigned to you.')
    ]
    cursor.executemany('''
        INSERT INTO notifications (user_id, message)
        VALUES (?, ?)
    ''', notifications)

    # Insert sample messages
    messages = [
        (1, 2, 'Hello, I’m interested in your job posting.'),
        (2, 1, 'Great! Let’s discuss more details.'),
        (3, 1, 'I can help with the SEO optimization task.')
    ]
    cursor.executemany('''
        INSERT INTO messages (sender_id, receiver_id, message)
        VALUES (?, ?, ?)
    ''', messages)

    # Commit changes and close the connection
    conn.commit()
    conn.close()
    print("Database and tables created, with sample data inserted.")

if __name__ == "__main__":
    create_database()
