import sqlite3
from contextlib import contextmanager
from typing import Dict, Any, List

DB_PATH = "aica.db"

def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute("""
        CREATE TABLE IF NOT EXISTS emails (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sender TEXT,
            subject TEXT,
            body TEXT,
            sent_date TEXT,
            sentiment TEXT,
            priority TEXT,
            priority_score REAL,
            extracted_json TEXT,
            ai_response TEXT,
            status TEXT DEFAULT 'pending'
        )
        """)
        conn.commit()

@contextmanager
def get_db():
    conn = sqlite3.connect(DB_PATH)
    try:
        yield conn
    finally:
        conn.close()

def insert_email(rec: Dict[str, Any]) -> int:
    with get_db() as conn:
        c = conn.cursor()
        c.execute("""
            INSERT INTO emails(sender, subject, body, sent_date, sentiment, priority, priority_score, extracted_json, ai_response, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (rec.get("sender"), rec.get("subject"), rec.get("body"), rec.get("sent_date"),
              rec.get("sentiment"), rec.get("priority"), rec.get("priority_score"),
              rec.get("extracted_json"), rec.get("ai_response"), rec.get("status","pending")))
        conn.commit()
        return c.lastrowid

def list_emails(order_by_priority=True) -> List[Dict[str, Any]]:
    with get_db() as conn:
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        if order_by_priority:
            c.execute("""
                SELECT * FROM emails ORDER BY priority = 'Urgent' DESC, priority_score DESC, datetime(sent_date) DESC
            """)
        else:
            c.execute("SELECT * FROM emails ORDER BY datetime(sent_date) DESC")
        rows = c.fetchall()
        return [dict(r) for r in rows]

def update_email_status(email_id: int, status: str):
    with get_db() as conn:
        c = conn.cursor()
        c.execute("UPDATE emails SET status = ? WHERE id = ?", (status, email_id))
        conn.commit()

def update_ai_response(email_id: int, ai_text: str):
    with get_db() as conn:
        c = conn.cursor()
        c.execute("UPDATE emails SET ai_response = ? WHERE id = ?", (ai_text, email_id))
        conn.commit()
