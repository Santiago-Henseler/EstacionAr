import os
import sqlite3

DATABASE = os.environ.get("FEEDBACK_DB", "feedBack.db")


def setFeedBackDataBase():
    with sqlite3.connect(DATABASE) as db:
        db.execute("""
            CREATE TABLE IF NOT EXISTS feedBack (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                street_name TEXT NOT NULL,
                a_init INTEGER NOT NULL,
                hora INTEGER NOT NULL,
                proba REAL NOT NULL
            )
        """)

def insert(street_name: str, aInit: int, hora: int, proba: int):
    with sqlite3.connect(DATABASE) as db:
        db.execute("""
            INSERT INTO feedBack (street_name, a_init, hora, proba)
            VALUES (?, ?, ?, ?)
        """, (street_name, aInit, hora, proba))


def averages():
    with sqlite3.connect(DATABASE) as db:
        cursor = db.execute("""
            SELECT street_name, a_init, hora, AVG(proba), COUNT(*)
            FROM feedBack
            GROUP BY street_name, a_init, hora
        """)
        result = cursor.fetchall()
        print("Averages:", result)
        return result

def find_all():
    with sqlite3.connect(DATABASE) as db:
        cursor = db.execute("SELECT * FROM feedBack").fetchall()