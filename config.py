# ============================================================
# config.py — Application Configuration
# Edit MYSQL_PASSWORD to match your MySQL root password.
# ============================================================

import os


class Config:
    # Flask secret key — change this for production
    SECRET_KEY = 'yoga_therapy_secret_key_mca_2024'

    # ---- MySQL Connection Settings ----
    MYSQL_HOST     = 'localhost'
    MYSQL_USER     = 'root'
    MYSQL_PASSWORD = os.environ.get('MYSQL_PASSWORD', '')   # <-- put your MySQL password between the last quotes
    MYSQL_DATABASE = 'yoga_therapy_db'
    MYSQL_PORT     = 3306

    # Run in debug mode (set False in production)
    DEBUG = True
