import sqlite3
from flask import g

def get_db():
    """Get a new connection to the database."""
    if "db" not in g:
        g.db = sqlite3.connect("files.db", detect_types=sqlite3.PARSE_DECLTYPES)
        g.db.row_factory = sqlite3.Row

    return g.db


def close_db(e=None):
    """Close the database connection."""
    db = g.pop("db", None)

    if db is not None:
        db.close()
