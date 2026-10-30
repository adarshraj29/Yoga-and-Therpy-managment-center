"""
blueprints/admin/__init__.py
"""
from flask import Blueprint

admin_bp = Blueprint('admin', __name__)

from blueprints.admin import routes   # noqa: F401, E402
