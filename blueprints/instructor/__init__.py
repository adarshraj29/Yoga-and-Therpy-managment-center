"""
blueprints/instructor/__init__.py
"""
from flask import Blueprint

instructor_bp = Blueprint('instructor', __name__)

from blueprints.instructor import routes   # noqa: F401, E402
