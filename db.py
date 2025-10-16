import sqlite3

def init_db():
    conn = sqlite3.connect("users.db")
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            cookie TEXT
        )
    """)
    conn.commit()
    conn.close()


def save_cookie(user_id: int, cookie: str):
    conn = sqlite3.connect("users.db")
    cur = conn.cursor()
    cur.execute("REPLACE INTO users (user_id, cookie) VALUES (?, ?)", (user_id, cookie))
    conn.commit()
    conn.close()


def get_cookie(user_id: int):
    conn = sqlite3.connect("users.db")
    cur = conn.cursor()
    cur.execute("SELECT cookie FROM users WHERE user_id = ?", (user_id,))
    row = cur.fetchone()
    conn.close()
    return row[0] if row else None
