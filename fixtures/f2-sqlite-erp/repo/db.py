import sqlite3
import time

DB_PATH = "erp.db"


def get_conn():
    conn = sqlite3.connect(DB_PATH, timeout=5)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=5000")
    conn.row_factory = sqlite3.Row
    return conn


def execute_with_retry(sql, params=(), retries=5):
    for attempt in range(retries):
        try:
            conn = get_conn()
            with conn:
                return conn.execute(sql, params)
        except sqlite3.OperationalError as e:
            if "database is locked" in str(e) and attempt < retries - 1:
                time.sleep(0.2 * (attempt + 1))
                continue
            raise
