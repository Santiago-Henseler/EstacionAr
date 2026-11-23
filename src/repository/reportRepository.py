import os
import sqlite3
from datetime import datetime, UTC

DATABASE = os.environ.get("FEEDBACK_DB", "feedBack.db")

COLUMNS = ("id", "user_id", "type", "reason", "street_name", "level", "a_init", "hour", "description", "status", "created_at")


def setReportsDataBase():
    with sqlite3.connect(DATABASE) as db:
        db.execute("""
            CREATE TABLE IF NOT EXISTS reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                type TEXT NOT NULL,
                reason TEXT NOT NULL,
                street_name TEXT NOT NULL,
                level INTEGER NOT NULL,
                a_init INTEGER NOT NULL,
                hour INTEGER NOT NULL,
                description TEXT,
                status TEXT NOT NULL DEFAULT 'pendiente',
                created_at TEXT NOT NULL
            )
        """)
        db.execute("CREATE INDEX IF NOT EXISTS idx_reports_user_created ON reports (user_id, created_at)")
        db.execute("CREATE INDEX IF NOT EXISTS idx_reports_reason_created ON reports (reason, created_at)")


def _toRow(row) -> dict:
    report = dict(zip(COLUMNS, row))
    report["created_at"] = datetime.fromisoformat(report["created_at"])
    return report


def insertReport(user_id: int, reason: str, street_name: str, level: int, a_init: int, hour: int,
                 description: str | None = None, status: str = "pendiente",
                 created_at: datetime | None = None, type: str = "mala_indicacion") -> dict:
    created_at = (created_at or datetime.now(UTC)).astimezone(UTC)
    with sqlite3.connect(DATABASE) as db:
        cursor = db.execute("""
            INSERT INTO reports (user_id, type, reason, street_name, level, a_init, hour, description, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (user_id, type, reason, street_name, level, a_init, hour, description, status, created_at.isoformat()))
        row = db.execute(f"SELECT {', '.join(COLUMNS)} FROM reports WHERE id = ?", (cursor.lastrowid,)).fetchone()
    return _toRow(row)


def countReportsSince(user_id: int, since: datetime) -> int:
    with sqlite3.connect(DATABASE) as db:
        return db.execute(
            "SELECT COUNT(*) FROM reports WHERE user_id = ? AND created_at >= ?",
            (user_id, since.astimezone(UTC).isoformat()),
        ).fetchone()[0]


def findByUser(user_id: int) -> list[dict]:
    with sqlite3.connect(DATABASE) as db:
        rows = db.execute(
            f"SELECT {', '.join(COLUMNS)} FROM reports WHERE user_id = ? ORDER BY created_at DESC",
            (user_id,),
        ).fetchall()
    return [_toRow(r) for r in rows]


def noSpotReportsSince(since: datetime) -> list[tuple]:
    # (user_id, street_name, a_init, hour, created_at) de los "no había lugar" no rechazados
    with sqlite3.connect(DATABASE) as db:
        rows = db.execute("""
            SELECT user_id, street_name, a_init, hour, created_at
            FROM reports
            WHERE reason = 'no_habia_lugar' AND status != 'rechazado' AND created_at >= ?
        """, (since.astimezone(UTC).isoformat(),)).fetchall()
    return [(u, s, a, h, datetime.fromisoformat(c)) for u, s, a, h, c in rows]
