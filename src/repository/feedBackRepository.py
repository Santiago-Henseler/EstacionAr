import sqlite3

DATABASE = "feedBack.db"


def setFeedBackDataBase():
    with sqlite3.connect(DATABASE) as db:
        db.execute("""
            CREATE TABLE IF NOT EXISTS feedBack (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                street_name TEXT NOT NULL,
                level INTEGER NOT NULL,
                proba INTEGER NOT NULL
            )
        """)


def insert(street_name: str, level: int, proba: int):
    with sqlite3.connect(DATABASE) as db:
        db.execute("""
            INSERT INTO feedBack (street_name, level, proba)
            VALUES (?, ?, ?)
        """, (street_name, level, proba))


def find_all():
    with sqlite3.connect(DATABASE) as db:
        cursor = db.execute("SELECT * FROM feedBack")
        return cursor.fetchall()