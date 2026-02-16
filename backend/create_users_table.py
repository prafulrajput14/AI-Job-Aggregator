import sqlite3
import os

DB_NAME = "jobs.db"

def add_users_table():
    db_path = os.path.join(os.path.dirname(__file__), "data", DB_NAME)
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    
    print("Creating users table...")
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            full_name TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()
    print("Users table created successfully.")

if __name__ == "__main__":
    add_users_table()
