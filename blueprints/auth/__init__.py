"""
blueprints/auth/__init__.py
"""
from flask import Blueprint

auth_bp = Blueprint('auth', __name__)

from blueprints.auth import routes   # noqa: F401, E402
