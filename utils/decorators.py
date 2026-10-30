"""
utils/decorators.py — Role-based access control decorators.
Apply these to any route that requires authentication or a specific role.

Usage:
    from utils.decorators import login_required, admin_required

    @app.route('/secret')
    @admin_required
    def secret():
        ...
"""

from functools import wraps
from flask import session, redirect, url_for, flash


def login_required(f):
    """Redirect to login if user is not authenticated."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated


def admin_required(f):
    """Allow only users with role='admin'."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in.', 'warning')
            return redirect(url_for('auth.login'))
        if session.get('role') != 'admin':
            flash('Admin access only.', 'danger')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated


def member_required(f):
    """Allow only users with role='member'."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in.', 'warning')
            return redirect(url_for('auth.login'))
        if session.get('role') != 'member':
            flash('Member access only.', 'danger')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated


def instructor_required(f):
    """Allow only users with role='instructor'."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in.', 'warning')
            return redirect(url_for('auth.login'))
        if session.get('role') != 'instructor':
            flash('Instructor access only.', 'danger')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated
