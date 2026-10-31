import sqlite3

dataBase = None
dataBaseCursor = None

def setFeedBackDataBase():
    dataBase = sqlite3.connect("feedBack.db")
    dataBaseCursor = dataBase.cursor()
    create_table()

def create_table():
    dataBaseCursor.execute("""
            CREATE TABLE IF NOT EXISTS feedBack (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                street_name TEXT NOT NULL,
                level INTEGER NOT NULL,
                confidence INTEGER NOT NULL,
                proba INTEGER NOT NULL
            )
    """)
    dataBase.commit()

def insert(street_name: str, level: int, confidence: int, proba: int):
    dataBaseCursor.execute("""
        INSERT INTO feedBack (street_name, level, confidence, proba)
        VALUES (?, ?, ?, ?)
    """, (street_name, level, confidence, proba))

    dataBaseCursor.commit()

def find_all(self):
    dataBaseCursor.execute("SELECT * FROM streets")
    return dataBaseCursor.fetchall()