import sqlite3
from contextlib import contextmanager
from pathlib import Path

from . import config


@contextmanager
def connect():
    """Open a connection, commit on success, roll back on error, always close."""
    conn = sqlite3.connect(config.DATABASE)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db():
    from . import auth
    schema = (Path(__file__).parent / "schema.sql").read_text()
    with connect() as conn:
        conn.executescript(schema)
        # Automatic safe migration for existing databases
        columns = [r["name"] for r in conn.execute("PRAGMA table_info(alerts)").fetchall()]
        if "resolved_at" not in columns:
            conn.execute("ALTER TABLE alerts ADD COLUMN resolved_at TEXT")
    auth.seed_default_users()


def query(sql, params=()):
    """Always pass values through `params`. Never build SQL with f-strings."""
    with connect() as conn:
        return conn.execute(sql, params).fetchall()
