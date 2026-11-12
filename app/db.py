"""Database connection helpers (SQLite by default)."""
import os
import sqlite3
from flask import g, current_app


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(current_app.config["DATABASE"])
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


def close_db(_exc=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def ensure_schema():
    schema = os.path.join(os.path.dirname(__file__), "schema.sql")
    conn = sqlite3.connect(current_app.config["DATABASE"])
    with open(schema, encoding="utf-8") as f:
        conn.executescript(f.read())
    conn.close()


def init_app(app):
    app.teardown_appcontext(close_db)
