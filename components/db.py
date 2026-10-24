import sqlite3

from flask import g
from werkzeug.security import generate_password_hash

DB = "pharmacy.db"


def db():
    if "db" not in g:
        g.db = sqlite3.connect(DB)
        g.db.row_factory = sqlite3.Row
    return g.db


def register_db_handlers(app):
    @app.teardown_appcontext
    def close_db(e):
        d = g.pop("db", None)
        if d:
            d.close()


def init_db():
    c = sqlite3.connect(DB)
    c.executescript("""
    CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY, username TEXT UNIQUE, password TEXT);
    CREATE TABLE IF NOT EXISTS medicines(id INTEGER PRIMARY KEY, name TEXT, category TEXT,
        price REAL, stock INTEGER, expiry TEXT);
    CREATE TABLE IF NOT EXISTS sales(id INTEGER PRIMARY KEY, customer TEXT, total REAL, date TEXT);
    CREATE TABLE IF NOT EXISTS sale_items(id INTEGER PRIMARY KEY, sale_id INTEGER,
        medicine_id INTEGER, qty INTEGER, price REAL);""")
    if not c.execute("SELECT 1 FROM users").fetchone():
        c.execute("INSERT INTO users(username,password) VALUES(?,?)",
                  ("admin", generate_password_hash("admin123")))
    c.commit()
    c.close()
