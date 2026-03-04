import os
import sqlite3
import logging
from datetime import datetime, timedelta
from dotenv import load_dotenv
from functools import lru_cache

# Try importing psycopg2 for Postgres
try:
    import psycopg2
    import psycopg2.extras
    import psycopg2.pool
    PSYCOPG2_AVAILABLE = True
except ImportError:
    PSYCOPG2_AVAILABLE = False

load_dotenv()

DB_NAME = "jobs.db"
DATABASE_URL = os.getenv("DATABASE_URL")
IS_POSTGRES = bool(DATABASE_URL) and PSYCOPG2_AVAILABLE

pg_pool = None

if IS_POSTGRES:
    try:
        pg_pool = psycopg2.pool.SimpleConnectionPool(
            1, 20,
            DATABASE_URL
        )
        print("✅ PostgreSQL connection pool created.")
    except Exception as e:
        print(f"❌ Error creating PostgreSQL pool: {e}")
        IS_POSTGRES = False

import threading
# Fallback to local thread-safe SQLite connections to prevent lock errors
sqlite_local = threading.local()

def get_db_connection():
    if IS_POSTGRES and pg_pool:
        conn = pg_pool.getconn()
        conn.autocommit = False 
        return conn
    else:
        # Fallback to SQLite - Thread Safe
        try:
            if not hasattr(sqlite_local, "conn") or sqlite_local.conn is None:
                db_path = os.path.join(os.path.dirname(__file__), "data", DB_NAME)
                os.makedirs(os.path.dirname(db_path), exist_ok=True)
                # Increase timeout to 30 seconds to wait for locks instead of crashing instantly
                # Use check_same_thread=False for FastAPI background processes
                conn = sqlite3.connect(db_path, timeout=30.0, check_same_thread=False)
                conn.isolation_level = None  # Autocommit mode: Releases read-locks immediately after SELECT
                conn.row_factory = sqlite3.Row
                sqlite_local.conn = conn
            return sqlite_local.conn
        except Exception as e:
            print(f"Database error: {e}")
            raise e

def release_connection(conn):
    if IS_POSTGRES and pg_pool:
        pg_pool.putconn(conn)
    else:
        # For our thread-local SQLite, we leave it open for reuse by this thread
        pass

def get_cursor(conn):
    if IS_POSTGRES:
        return conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    else:
        return conn.cursor()

def normalize_query(query):
    """Convert ? placeholders to %s if using Postgres"""
    if IS_POSTGRES:
        return query.replace('?', '%s')
    return query

def init_db():
    conn = get_db_connection()
    c = conn.cursor()
    
    # Define schemas based on DB type
    if IS_POSTGRES:
        id_type = "SERIAL PRIMARY KEY"
        bool_type = "BOOLEAN"
    else:
        id_type = "INTEGER PRIMARY KEY AUTOINCREMENT"
        bool_type = "BOOLEAN" # SQLite accepts this as affinity

    try:
        # Jobs Table
        c.execute(f'''
            CREATE TABLE IF NOT EXISTS jobs (
                id {id_type},
                title TEXT NOT NULL,
                company TEXT NOT NULL,
                location TEXT,
                description TEXT,
                url TEXT UNIQUE,
                date_posted TEXT,
                skills TEXT,
                is_internship {bool_type},
                salary TEXT,
                site TEXT,
                job_type TEXT,
                currency TEXT,
                is_active {bool_type} DEFAULT {'TRUE' if IS_POSTGRES else '1'}
            )
        ''')

        # Users Table
        c.execute(f'''
            CREATE TABLE IF NOT EXISTS users (
                id {id_type},
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                full_name TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Saved Jobs Junction Table
        c.execute(f'''
            CREATE TABLE IF NOT EXISTS saved_jobs (
                user_id INTEGER,
                job_id INTEGER,
                saved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (user_id, job_id),
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
                FOREIGN KEY (job_id) REFERENCES jobs (id) ON DELETE CASCADE
            )
        ''')
        
        # Alert Subscriptions Table
        c.execute(f'''
            CREATE TABLE IF NOT EXISTS alert_subscriptions (
                id {id_type},
                user_id INTEGER NOT NULL,
                keyword TEXT NOT NULL,
                location TEXT,
                is_active {bool_type} DEFAULT {'TRUE' if IS_POSTGRES else '1'},
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
            )
        ''')
        
        # Password Resets Table
        c.execute(f'''
            CREATE TABLE IF NOT EXISTS password_resets (
                token TEXT PRIMARY KEY,
                user_id INTEGER NOT NULL,
                expires_at TIMESTAMP NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
            )
        ''')
        
        conn.commit()
        print("✅ Database initialized (Jobs, Users, Alerts, Resets).")
    except Exception as e:
        print(f"❌ Error initializing DB: {e}")
        conn.rollback()
    finally:
        release_connection(conn)

# --- JOB Functions ---

def add_job(job_data):
    conn = get_db_connection()
    c = get_cursor(conn)
    
    query = normalize_query('''
        INSERT INTO jobs (title, company, location, description, url, date_posted, skills, is_internship, salary, site, job_type, currency)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''')
    
    # Postgres uses ON CONFLICT, SQLite uses INSERT OR IGNORE logic via generic handling or explicit syntax
    # To keep it simple cross-db, we use try-except IntegrityError
    
    if IS_POSTGRES:
        # Use ON CONFLICT DO NOTHING for Postgres to avoid exception overhead
        query = query.replace('VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)', 
                              'VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) ON CONFLICT (url) DO NOTHING')
    
    try:
        c.execute(query, (
            job_data['title'],
            job_data['company'],
            job_data.get('location'),
            job_data.get('description'),
            job_data['url'],
            job_data.get('date_posted'),
            job_data.get('skills'),
            job_data.get('is_internship'),
            job_data.get('salary'),
            job_data.get('site'),
            job_data.get('job_type'),
            job_data.get('currency')
        ))
        conn.commit()
        # Invalidate cache when new data is added
        get_all_jobs.cache_clear()
    except Exception as e:
        # SQLite IntegrityError or other
        if "UNIQUE constraint failed" in str(e) or "duplicate key" in str(e):
            pass # Ignore duplicate
        else:
            print(f"Error adding job: {e}")
    finally:
        release_connection(conn)

@lru_cache(maxsize=128)
def get_all_jobs(search_query=None, filter_type='All', location_filter=None, sort_by='newest', date_posted_filter='any'):
    conn = get_db_connection()
    c = get_cursor(conn)
    
    query = "SELECT * FROM jobs WHERE 1=1"
    params = []

    if search_query:
        keyword_synonyms = {
            "sde": ["software", "developer", "engineer", "sde"],
            "swe": ["software", "engineer", "swe"],
            "frontend": ["front", "react", "angular", "vue", "web", "ui"],
            "backend": ["back", "node", "java", "python", "go", "api"],
            "fullstack": ["full", "stack", "software", "web"],
            "mern": ["mern", "node", "react", "mongo"],
        }
        
        # Map synonyms for the first word or whole phrase to help out
        search_query_lower = search_query.lower().strip()
        synonyms = keyword_synonyms.get(search_query_lower, [])
        if not synonyms and " " in search_query_lower:
            first_word = search_query_lower.split()[0]
            synonyms = keyword_synonyms.get(first_word, [])
            
        # Add the whole phrase and any synonyms to an OR group
        # If user types "software engineer", we want to match 'software' AND 'engineer',
        # OR any of the synonyms.
        
        terms = search_query_lower.split()
        
        # We will require every word in the search query to be present *somewhere*
        for word in terms:
            w = f"%{word}%"
            field_group = "(lower(title) LIKE ? OR lower(company) LIKE ? OR lower(skills) LIKE ? OR lower(description) LIKE ?)"
            query += f" AND {field_group}"
            params.extend([w, w, w, w])
        
    if location_filter:
        loc = location_filter.lower().strip()
        if "," in loc:
             loc = loc.split(",")[0].strip()
        query += " AND lower(location) LIKE ?"
        params.append(f"%{loc}%")

    if filter_type == 'Internship':
        query += " AND (is_internship = ? OR job_type LIKE ?)"
        params.extend([True if IS_POSTGRES else 1, '%intern%'])
    elif filter_type == 'Full-time':
        query += " AND (is_internship = ? AND (job_type IS NULL OR job_type LIKE ? OR job_type = ''))"
        params.extend([False if IS_POSTGRES else 0, '%full%'])
    elif filter_type == 'Contract':
        query += " AND job_type LIKE ?"
        params.append('%contract%')
    elif filter_type == 'Part-time':
        query += " AND job_type LIKE ?"
        params.append('%part%')

    # Date Posted Filter
    if date_posted_filter == 'past_24h':
        cutoff = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        query += " AND date_posted >= ?"
        params.append(cutoff)
    elif date_posted_filter == 'past_week':
        cutoff = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
        query += " AND date_posted >= ?"
        params.append(cutoff)

    # Sorting
    if sort_by == 'newest':
        # Fallback to ID representing chronological insertion if date strings are mixed
        query += " ORDER BY id DESC"
    elif sort_by == 'salary':
        # Since salary is unstructured text in standard Jobspy, this is a best-effort 
        # textual reverse sort (putting longer/higher prefixes first) 
        # We also order by id DESC as tie-breaker
        query += " ORDER BY salary DESC, id DESC"
    else:
        query += " ORDER BY id DESC"
        
    query += " LIMIT 50"
    
    if IS_POSTGRES:
        query = query.replace('?', '%s')
    
    try:
        c.execute(query, tuple(params))
        jobs = c.fetchall()
        return [dict(job) for job in jobs]
    except Exception as e:
        print(f"Error fetching jobs: {e}")
        return []
    finally:
        release_connection(conn)

def get_job_by_id(job_id):
    conn = get_db_connection()
    c = get_cursor(conn)
    query = normalize_query("SELECT * FROM jobs WHERE id = ?")
    
    try:
        c.execute(query, (job_id,))
        job = c.fetchone()
        return dict(job) if job else None
    except Exception as e:
        print(f"Error fetching job by id: {e}")
        return None
    finally:
        release_connection(conn)

def cleanup_old_jobs():
    conn = get_db_connection()
    c = get_cursor(conn)
    try:
        # 1. Calculate cutoff in Python to be DB-agnostic
        cutoff = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        query1 = "DELETE FROM jobs WHERE date_posted < ? AND length(date_posted) = 10"
        
        # 2. Relative dates
        query2 = "DELETE FROM jobs WHERE date_posted LIKE ? OR date_posted LIKE ?"
        
        q1 = normalize_query(query1)
        q2 = normalize_query(query2)
        
        c.execute(q1, (cutoff,))
        c.execute(q2, ('%month%', '%year%'))
        
        conn.commit()
        print("✅ Cleaned up old jobs.")
    except Exception as e:
        print(f"❌ Error cleaning up jobs: {e}")
    finally:
        release_connection(conn)

# --- USER Functions ---

def create_user(email, password_hash, full_name=None):
    conn = get_db_connection()
    c = get_cursor(conn)
    query = "INSERT INTO users (email, password_hash, full_name) VALUES (?, ?, ?)"
    query = normalize_query(query)
    try:
        c.execute(query, (email, password_hash, full_name))
        conn.commit()
        return True
    except Exception as e:
        if "unique" in str(e).lower():
            raise ValueError("Email already exists")
        print(f"Error checking user: {e}")
        raise e
    finally:
        release_connection(conn)

def get_user_by_email(email):
    conn = get_db_connection()
    c = get_cursor(conn)
    query = "SELECT * FROM users WHERE email = ?"
    query = normalize_query(query)
    try:
        c.execute(query, (email,))
        user = c.fetchone()
        return dict(user) if user else None
    except Exception as e:
        print(f"Error fetching user: {e}")
        return None
    finally:
        release_connection(conn)

def save_job(user_id, job_id):
    conn = get_db_connection()
    c = get_cursor(conn)
    query = "INSERT INTO saved_jobs (user_id, job_id) VALUES (?, ?)"
    
    if IS_POSTGRES:
        query = "INSERT INTO saved_jobs (user_id, job_id) VALUES (%s, %s) ON CONFLICT (user_id, job_id) DO NOTHING"
    else:
        query = "INSERT OR IGNORE INTO saved_jobs (user_id, job_id) VALUES (?, ?)"
        
    try:
        c.execute(query, (user_id, job_id))
        conn.commit()
        return True
    except Exception as e:
        print(f"Error saving job: {e}")
        return False
    finally:
        release_connection(conn)

def unsave_job(user_id, job_id):
    conn = get_db_connection()
    c = get_cursor(conn)
    query = "DELETE FROM saved_jobs WHERE user_id = ? AND job_id = ?"
    query = normalize_query(query)
    
    try:
        c.execute(query, (user_id, job_id))
        conn.commit()
        return True
    except Exception as e:
        print(f"Error unsaving job: {e}")
        return False
    finally:
        release_connection(conn)

def get_saved_jobs_for_user(user_id):
    conn = get_db_connection()
    c = get_cursor(conn)
    query = """
        SELECT jobs.* FROM jobs 
        JOIN saved_jobs ON jobs.id = saved_jobs.job_id 
        WHERE saved_jobs.user_id = ?
        ORDER BY saved_jobs.saved_at DESC
    """
    query = normalize_query(query)
    try:
        c.execute(query, (user_id,))
        jobs = c.fetchall()
        return [dict(job) for job in jobs]
    except Exception as e:
        print(f"Error fetching saved jobs: {e}")
        return []
    finally:
        release_connection(conn)

# --- ALERT SUBSCRIPTION Functions ---

def add_alert(user_id, keyword, location):
    conn = get_db_connection()
    c = get_cursor(conn)
    query = "INSERT INTO alert_subscriptions (user_id, keyword, location) VALUES (?, ?, ?)"
    query = normalize_query(query)
    try:
        c.execute(query, (user_id, keyword.strip(), location.strip() if location else ''))
        conn.commit()
        return True
    except Exception as e:
        print(f"Error adding alert: {e}")
        return False
    finally:
        release_connection(conn)

def remove_alert(alert_id, user_id):
    conn = get_db_connection()
    c = get_cursor(conn)
    query = "DELETE FROM alert_subscriptions WHERE id = ? AND user_id = ?"
    query = normalize_query(query)
    try:
        c.execute(query, (alert_id, user_id))
        conn.commit()
        return True
    except Exception as e:
        print(f"Error removing alert: {e}")
        return False
    finally:
        release_connection(conn)

def get_user_alerts(user_id):
    conn = get_db_connection()
    c = get_cursor(conn)
    query = "SELECT * FROM alert_subscriptions WHERE user_id = ? ORDER BY created_at DESC"
    query = normalize_query(query)
    try:
        c.execute(query, (user_id,))
        alerts = c.fetchall()
        return [dict(a) for a in alerts]
    except Exception as e:
        print(f"Error fetching alerts: {e}")
        return []
    finally:
        release_connection(conn)

def get_all_active_alerts():
    conn = get_db_connection()
    c = get_cursor(conn)
    query = "SELECT alert_subscriptions.*, users.email, users.full_name FROM alert_subscriptions JOIN users ON users.id = alert_subscriptions.user_id WHERE alert_subscriptions.is_active = ?"
    query = normalize_query(query)
    try:
        # 1 for SQLite True, True for Postgres
        active_val = True if IS_POSTGRES else 1
        c.execute(query, (active_val,))
        alerts = c.fetchall()
        return [dict(a) for a in alerts]
    except Exception as e:
        print(f"Error fetching all alerts: {e}")
        return []
    finally:
        release_connection(conn)

# --- PASSWORD RESET Functions ---

def create_password_reset_token(user_id, token, expires_at):
    conn = get_db_connection()
    c = get_cursor(conn)
    query = "INSERT OR REPLACE INTO password_resets (token, user_id, expires_at) VALUES (?, ?, ?)"
    query = normalize_query(query)
    try:
        c.execute(query, (token, user_id, expires_at))
        conn.commit()
        return True
    except Exception as e:
        print(f"Error creating reset token: {e}")
        return False
    finally:
        release_connection(conn)

def verify_reset_token(token):
    from datetime import datetime
    conn = get_db_connection()
    c = get_cursor(conn)
    query = "SELECT * FROM password_resets WHERE token = ?"
    query = normalize_query(query)
    try:
        c.execute(query, (token,))
        record = c.fetchone()
        if not record:
            return None
        
        # Check expiry
        if datetime.fromisoformat(record['expires_at']) < datetime.utcnow():
            return None
            
        return record['user_id']
    except Exception as e:
        print(f"Error verifying token: {e}")
        return None
    finally:
        release_connection(conn)

def update_user_password(user_id, hashed_password, token):
    conn = get_db_connection()
    c = get_cursor(conn)
    try:
        query1 = normalize_query("UPDATE users SET password_hash = ? WHERE id = ?")
        c.execute(query1, (hashed_password, user_id))
        
        query2 = normalize_query("DELETE FROM password_resets WHERE token = ?")
        c.execute(query2, (token,))
        
        conn.commit()
        return True
    except Exception as e:
        print(f"Error updating password: {e}")
        conn.rollback()
        return False
    finally:
        release_connection(conn)
