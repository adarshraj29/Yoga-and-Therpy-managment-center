"""
blueprints/member/__init__.py
"""
from flask import Blueprint

member_bp = Blueprint('member', __name__)

from blueprints.member import routes   # noqa: F401, E402
