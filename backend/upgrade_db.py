import sqlite3
import os

DB_NAME = "jobs.db"
DB_PATH = os.path.join(os.path.dirname(__file__), "data", DB_NAME)

def upgrade_database():
    if not os.path.exists(DB_PATH):
        print("Database does not exist yet. Run init_db() instead.")
        return

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # List of new columns and their types
    new_columns = {
        "salary": "TEXT",
        "site": "TEXT",
        "job_type": "TEXT",
        "currency": "TEXT"
    }
    
    # Get existing columns
    c.execute("PRAGMA table_info(jobs)")
    existing_columns = [row[1] for row in c.fetchall()]
    
    for col, data_type in new_columns.items():
        if col not in existing_columns:
            print(f"Adding column: {col}")
            try:
                c.execute(f"ALTER TABLE jobs ADD COLUMN {col} {data_type}")
            except Exception as e:
                print(f"Error adding {col}: {e}")
        else:
            print(f"Column {col} already exists.")
            
    conn.commit()
    conn.close()
    print("Database upgrade complete.")

if __name__ == "__main__":
    upgrade_database()
