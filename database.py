import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "briefed.db")


def get_connection():
    return sqlite3.connect(DB_PATH)


def initialize_db():
    """Creates tables if they don't exist yet."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL,
            interests TEXT NOT NULL
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS articles_sent (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            url TEXT NOT NULL,
            sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)
    conn.commit()
    conn.close()


def get_user(user_id: int = 1) -> dict | None:
    """Retrieves user preferences by ID. Defaults to user 1."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, email, interests FROM users WHERE id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return {"id": row[0], "email": row[1], "interests": row[2]}
    return None


def create_user(email: str, interests: str) -> int:
    """Creates a new user and returns their ID."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO users (email, interests) VALUES (?, ?)",
        (email, interests)
    )
    conn.commit()
    user_id = cursor.lastrowid
    conn.close()
    return user_id


def update_interests(user_id: int, interests: str):
    """Updates a user's interests string."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE users SET interests = ? WHERE id = ?",
        (interests, user_id)
    )
    conn.commit()
    conn.close()


def filter_new_articles(user_id: int, articles: list[dict]) -> list[dict]:
    """Removes articles whose URLs have already been sent to this user."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT url FROM articles_sent WHERE user_id = ?",
        (user_id,)
    )
    sent_urls = {row[0] for row in cursor.fetchall()}
    conn.close()
    return [a for a in articles if a["url"] not in sent_urls]


def mark_articles_sent(user_id: int, articles: list[dict]):
    """Records articles as sent so they won't be repeated."""
    conn = get_connection()
    cursor = conn.cursor()
    for article in articles:
        cursor.execute(
            "INSERT INTO articles_sent (user_id, url) VALUES (?, ?)",
            (user_id, article["url"])
        )
    conn.commit()
    conn.close()


def ensure_default_user():
    """
    On Render's free tier the SQLite file is wiped on every cold start,
    so we re-seed user 1 from environment variables on every boot if
    they don't already exist. Configure these env vars in Render:

        BRIEFED_USER_EMAIL     — the inbox the briefing is sent to
        BRIEFED_USER_INTERESTS — comma-separated interest keywords
    """
    if get_user(1) is not None:
        return  # Already seeded.

    email = os.getenv("BRIEFED_USER_EMAIL")
    interests = os.getenv("BRIEFED_USER_INTERESTS")
    if not email or not interests:
        # Don't crash — just skip seeding. The /run endpoint will return
        # a clearer error when it can't find a user.
        print(
            "⚠️  database.py: BRIEFED_USER_EMAIL or BRIEFED_USER_INTERESTS "
            "not set; skipping default user seed."
        )
        return

    create_user(email=email, interests=interests)
    print(f"✅ database.py: seeded default user with email={email}")


# --- Auto-init on import ----------------------------------------------------
# Runs once when gunicorn imports any module that does `import database`.
# Safe to call repeatedly because both functions are idempotent (CREATE TABLE
# IF NOT EXISTS, and ensure_default_user checks before inserting).
initialize_db()
ensure_default_user()
# ---------------------------------------------------------------------------


# Quick test
if __name__ == "__main__":
    print("✅ Database initialized")
    user = get_user(1)
    print(f"✅ User 1: {user}")