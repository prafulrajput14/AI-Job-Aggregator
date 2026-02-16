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

def get_db_connection():
    if IS_POSTGRES and pg_pool:
        conn = pg_pool.getconn()
        conn.autocommit = False 
        return conn
    else:
        # Fallback to SQLite
        try:
            db_path = os.path.join(os.path.dirname(__file__), "data", DB_NAME)
            os.makedirs(os.path.dirname(db_path), exist_ok=True)
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            return conn
        except Exception as e:
            print(f"Database error: {e}")
            raise e

def release_connection(conn):
    if IS_POSTGRES and pg_pool:
        pg_pool.putconn(conn)
    else:
        conn.close()

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
        
        conn.commit()
        print("✅ Database initialized (Jobs & Users tables).")
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
def get_all_jobs(search_query=None, filter_type='All', location_filter=None):
    conn = get_db_connection()
    c = get_cursor(conn)
    
    query = "SELECT * FROM jobs WHERE 1=1"
    params = []

    if search_query:
        # EXPANSION LOGIC: Handle acronyms in DB retrieval too
        # If user searches "sde", we should also look for "software engineer"
        keyword_synonyms = {
            "sde": ["software", "developer", "engineer", "sde"],
            "swe": ["software", "engineer", "swe"],
            "frontend": ["front", "react", "angular", "vue", "web", "ui"],
            "backend": ["back", "node", "java", "python", "go", "api"],
            "fullstack": ["full", "stack", "software", "web"],
            "mern": ["mern", "node", "react", "mongo"],
        }
        
        search_terms = [search_query.lower().strip()]
        if search_terms[0] in keyword_synonyms:
            search_terms = list(set(search_terms + keyword_synonyms[search_terms[0]]))
            
        # Build dynamic OR clause for all terms across all fields
        # (lower(title) LIKE ? OR lower(company) LIKE ? ...)
        
        # This creates a block like: (lower(title) LIKE ? OR lower(company) LIKE ? ...)
        field_group = "(lower(title) LIKE ? OR lower(company) LIKE ? OR lower(skills) LIKE ? OR lower(description) LIKE ?)"
        
        # Combine blocks with OR: ((...) OR (...))
        query += " AND (" + " OR ".join([field_group] * len(search_terms)) + ")"
        
        for term in search_terms:
            t = f"%{term}%"
            params.extend([t, t, t, t])
        
    if location_filter:
        loc = location_filter.lower().strip()
        if "," in loc:
             loc = loc.split(",")[0].strip()

        # Handle Synonyms for Major Cities (Basic)
        # Replacing simple LIKE ? with specific logic
        # For cross-DB, standard SQL LIKE is safe.
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
    
    query += " ORDER BY id DESC LIMIT 50"
    
    # Normalize query for Postgres if needed
    if IS_POSTGRES:
        # We need to manually replace ? with %s correctly in order
        # Simple replace works because all ? are placeholders
        query = query.replace('?', '%s')
        # Also need to ensure ILIKE for case insensitivity in Postgres if desired, 
        # but we used lower() function which is standard.
    
    try:
        c.execute(query, tuple(params))
        jobs = c.fetchall()
        # Convert to dict
        return [dict(job) for job in jobs]
    except Exception as e:
        print(f"Error fetching jobs: {e}")
        return []
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
