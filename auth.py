import bcrypt
from db import get_connection

def check_user_exists(username):
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT 1 FROM users WHERE username = %s", (username,))
        return cur.fetchone() is not None
    finally:
        conn.close()

def create_user(username, password, role):
    conn = get_connection()
    try:
        cur = conn.cursor()
        hashed_pw = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
        cur.execute(
            "INSERT INTO users (username, hashed_password, role) VALUES (%s, %s, %s)",
            (username, hashed_pw, role)
        )
        conn.commit()
    finally:
        conn.close()

def login_user(username, password):
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT hashed_password, role FROM users WHERE username = %s", (username,))
        row = cur.fetchone()
        if row:
            stored_hash, role = row
            if bcrypt.checkpw(password.encode("utf-8"), stored_hash):
                return role
        return None
    finally:
        conn.close()