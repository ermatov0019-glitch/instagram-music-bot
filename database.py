import sqlite3
import os

# PostgreSQL uchun DATABASE_URL (Render-da o'rnatiladi)
DATABASE_URL = os.getenv("DATABASE_URL")

def get_connection():
    if DATABASE_URL:
        import psycopg2
        return psycopg2.connect(DATABASE_URL, sslmode='require')
    else:
        return sqlite3.connect("bot_database.db")

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    
    # User jadvali
    # user_id BIGINT bo'lishi kerak, chunki Telegram IDlari katta
    query = '''
        CREATE TABLE IF NOT EXISTS users (
            user_id BIGINT PRIMARY KEY,
            username TEXT,
            full_name TEXT,
            joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    '''
    cursor.execute(query)
    conn.commit()
    conn.close()

def add_user(user_id, username, full_name):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        if DATABASE_URL:
            # PostgreSQL sintaksisi
            cursor.execute('''
                INSERT INTO users (user_id, username, full_name) 
                VALUES (%s, %s, %s) 
                ON CONFLICT (user_id) DO NOTHING
            ''', (user_id, username, full_name))
        else:
            # SQLite sintaksisi
            cursor.execute('INSERT OR IGNORE INTO users (user_id, username, full_name) VALUES (?, ?, ?)', 
                           (user_id, username, full_name))
        conn.commit()
    except Exception as e:
        print(f"Database error: {e}")
    finally:
        conn.close()

def get_all_users():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT user_id FROM users')
    users = cursor.fetchall()
    conn.close()
    return [u[0] for u in users]

def get_user_count():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM users')
    count = cursor.fetchone()[0]
    conn.close()
    return count

# Initialize database
init_db()
