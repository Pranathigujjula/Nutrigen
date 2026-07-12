import sqlite3
import json
import os

DB_PATH = "nutrigen.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Create Users table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        profile_data TEXT -- JSON string of all profile fields
    )
    ''')
    
    # Create Feedback table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS feedback (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        meal_plan TEXT,
        rating INTEGER,
        comments TEXT,
        FOREIGN KEY(user_id) REFERENCES users(id)
    )
    ''')
    
    # Create Meal History table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS meal_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        plan_content TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(user_id) REFERENCES users(id)
    )
    ''')
    
    # Create Cache table for USDA data to avoid hitting API repeatedly
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS food_cache (
        query TEXT PRIMARY KEY,
        results TEXT -- JSON string of results
    )
    ''')
    
    conn.commit()
    conn.close()

def get_user(user_id: int):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()
    conn.close()
    if user:
        return dict(user)
    return None

def create_user(name: str, profile_data: dict):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO users (name, profile_data) VALUES (?, ?)",
            (name, json.dumps(profile_data))
        )
        user_id = cursor.lastrowid
        conn.commit()
        return user_id
    except sqlite3.IntegrityError:
        return None
    finally:
        conn.close()

def update_user_profile(user_id: int, profile_data: dict):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Preserve existing password
    cursor.execute("SELECT profile_data FROM users WHERE id = ?", (user_id,))
    row = cursor.fetchone()
    if row:
        try:
            existing_profile = json.loads(row['profile_data'])
            if 'password' in existing_profile:
                profile_data['password'] = existing_profile['password']
        except:
            pass

    cursor.execute(
        "UPDATE users SET profile_data = ? WHERE id = ?",
        (json.dumps(profile_data), user_id)
    )
    conn.commit()
    conn.close()

def save_feedback(user_id: int, meal_plan: str, rating: int, comments: str):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO feedback (user_id, meal_plan, rating, comments) VALUES (?, ?, ?, ?)",
        (user_id, meal_plan, rating, comments)
    )
    conn.commit()
    conn.close()

def save_meal_plan(user_id: int, plan_content: str):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO meal_history (user_id, plan_content) VALUES (?, ?)",
        (user_id, plan_content)
    )
    conn.commit()
    conn.close()

def get_user_history(user_id: int):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM meal_history WHERE user_id = ? ORDER BY created_at DESC", (user_id,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def login_user(name: str, password: str):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE name = ?", (name,))
    user = cursor.fetchone()
    conn.close()
    
    if user:
        profile = json.loads(user['profile_data'])
        if profile.get('password') == password:
            return dict(user)
    return None

# Initialize on import
init_db()
