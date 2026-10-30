"""
utils/db.py — Database connection helper.
Uses Flask's application context (g) so one connection is
reused per request and cleanly closed at the end.
"""

import mysql.connector
from flask import current_app, g


def get_db():
    """Return a live MySQL connection for the current request."""
    if 'db' not in g:
        g.db = mysql.connector.connect(
            host     = current_app.config['MYSQL_HOST'],
            user     = current_app.config['MYSQL_USER'],
            password = current_app.config['MYSQL_PASSWORD'],
            database = current_app.config['MYSQL_DATABASE'],
            port     = current_app.config['MYSQL_PORT'],
            autocommit = False,
            charset    = 'utf8mb4',
            collation  = 'utf8mb4_unicode_ci'   # works with both MySQL and XAMPP's MariaDB
        )
    return g.db


def close_db(e=None):
    """Close the DB connection at the end of the request."""
    db = g.pop('db', None)
    if db is not None and db.is_connected():
        db.close()


def init_app(app):
    """Register the teardown hook with the Flask app."""
    app.teardown_appcontext(close_db)
